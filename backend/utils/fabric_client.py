"""Microsoft Fabric Lakehouse Client for ETL Testing"""

import pyodbc
import struct
import configparser
from typing import Optional
from azure.identity import ClientSecretCredential, InteractiveBrowserCredential

try:
    from azure.identity import TokenCachePersistenceOptions
except ImportError:  # Older azure-identity versions may not expose persistent cache options.
    TokenCachePersistenceOptions = None


class FabricClient:
    _credential_cache = {}

    def __init__(self, layer="BRONZE"):
        self.config = configparser.ConfigParser()
        self.config.read("config/master.properties")
        self.layer = f"FABRIC_{layer.upper()}"
        self.connection = None
        self.connection_strategy = self.config.get(
            "FABRIC",
            "FABRIC_CONNECTION_STRATEGY",
            fallback="reuse",
        ).strip().lower()
        self.retry_attempts = 1

    @classmethod
    def _get_credential(cls, auth_method: str, tenant_id: str, client_id: str = "", client_secret: str = ""):
        """Reuse credentials so interactive auth is not triggered for every connection."""
        cache_key = (auth_method, tenant_id, client_id)
        if cache_key in cls._credential_cache:
            return cls._credential_cache[cache_key]

        if auth_method == "serviceprincipal":
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )
        else:
            credential_kwargs = {"tenant_id": tenant_id}
            if TokenCachePersistenceOptions is not None:
                credential_kwargs["cache_persistence_options"] = TokenCachePersistenceOptions(
                    name="fabric_etl_testing_cache",
                    allow_unencrypted_storage=True,
                )
            credential = InteractiveBrowserCredential(**credential_kwargs)

        cls._credential_cache[cache_key] = credential
        return credential

    def connect(self):
        """Connect to Microsoft Fabric Lakehouse SQL Endpoint"""

        # ---- Safety check: enforce correct ODBC driver ----
        required_driver = "ODBC Driver 18 for SQL Server"
        if required_driver not in pyodbc.drivers():
            raise RuntimeError(
                "ODBC Driver 18 for SQL Server is required for Microsoft Fabric"
            )

        # ---- Read SQL endpoint ----
        layer_name = self.layer.split("_")[1]
        sql_endpoint = self.config.get(self.layer, f"{layer_name}_SQL_ENDPOINT")

        # ---- Authentication ----
        auth_method = self.config.get(
            "FABRIC", "FABRIC_AUTH_METHOD", fallback="Interactive"
        ).strip().lower()
        tenant_id = self.config.get("FABRIC", "FABRIC_TENANT_ID")

        if auth_method == "serviceprincipal":
            client_id = self.config.get("FABRIC", "FABRIC_CLIENT_ID")
            client_secret = self.config.get("FABRIC", "FABRIC_CLIENT_SECRET")
            credential = self._get_credential(
                auth_method=auth_method,
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )
        else:
            # Interactive browser authentication (MFA supported)
            credential = self._get_credential(auth_method="interactive", tenant_id=tenant_id)

        # ---- Acquire access token ----
        token = credential.get_token(
            "https://database.windows.net/.default"
        ).token

        # ---- Convert token for pyodbc ----
        token_bytes = token.encode("utf-16-le")
        token_struct = struct.pack(
            f"<I{len(token_bytes)}s", len(token_bytes), token_bytes
        )

        # ---- ODBC Driver 18 connection string ----
        conn_str = (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server={sql_endpoint};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )

        # ---- Connect ----
        self.connection = pyodbc.connect(
            conn_str,
            attrs_before={1256: token_struct},
        )

        return self.connection

    def _ensure_connection(self):
        """Ensure an active connection exists."""
        if self.connection is None:
            return self.connect()
        return self.connection

    def _reconnect(self):
        """Force reconnection for stale/broken sessions."""
        self.close()
        return self.connect()

    @staticmethod
    def _is_transient_pyodbc_error(exc: pyodbc.Error) -> bool:
        """Best-effort detection for stale or transient Fabric/ODBC failures."""
        message = " ".join(str(arg) for arg in getattr(exc, "args", ()) if arg).lower()
        transient_markers = (
            "communication link failure",
            "connection is busy",
            "connection was not open",
            "connection is closed",
            "closed connection",
            "08s01",
            "08003",
            "08001",
            "hyt00",
            "hyt01",
            "timeout expired",
            "login timeout expired",
            "transport-level error",
            "network-related",
            "server has gone away",
            "semaphore timeout period has expired",
            "connection reset",
            "session",
        )
        return any(marker in message for marker in transient_markers)

    def _run_query_once(self, query: str):
        """Execute one query attempt and always close the cursor."""
        connection = self._ensure_connection()
        cursor: Optional[pyodbc.Cursor] = None
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            if cursor.description is None:
                return []

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            if cursor is not None:
                cursor.close()

    def execute_query(self, query):
        """Execute SQL query and return results."""
        if self.connection_strategy == "reconnect_per_query":
            self._reconnect()

        try:
            return self._run_query_once(query)
        except pyodbc.Error as exc:
            if self._is_transient_pyodbc_error(exc):
                self._reconnect()
                try:
                    print(
                        f"[FabricClient:{self.layer}] transient query error detected; "
                        "reconnecting and retrying once."
                    )
                    return self._run_query_once(query)
                except pyodbc.Error as retry_exc:
                    raise RuntimeError(
                        f"{self.layer} query failed after reconnect retry: "
                        f"{retry_exc.__class__.__name__}: {retry_exc}"
                    ) from retry_exc
            raise RuntimeError(
                f"{self.layer} query failed: {exc.__class__.__name__}: {exc}"
            ) from exc

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
