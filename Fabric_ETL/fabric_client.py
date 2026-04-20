"""Microsoft Fabric Lakehouse Client for ETL Testing"""

import os
import pyodbc
import struct
import configparser
from pathlib import Path
from azure.identity import ClientSecretCredential, InteractiveBrowserCredential

try:
    from azure.identity import TokenCachePersistenceOptions
except ImportError:  # Older azure-identity versions may not expose persistent cache options.
    TokenCachePersistenceOptions = None


class FabricClient:
    _credential_cache = {}

    def __init__(self, layer="BRONZE", config_path=None):
        self.config = configparser.ConfigParser()
        resolved_config_path = self._resolve_config_path(config_path)
        self.config.read(resolved_config_path)
        self.layer = f"FABRIC_{layer.upper()}"
        self.connection = None

    @staticmethod
    def _resolve_config_path(config_path=None):
        """Resolve config path for local runs and Fabric notebooks."""
        candidates = []
        if config_path:
            candidates.append(Path(config_path))

        env_config = os.getenv("ETL_CONFIG_PATH")
        if env_config:
            candidates.append(Path(env_config))

        cwd = Path.cwd()
        module_dir = Path(__file__).resolve().parent
        candidates.extend(
            [
                cwd / "master.properties",
                cwd / "config" / "master.properties",
                module_dir / "master.properties",
                module_dir / "config" / "master.properties",
            ]
        )

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        raise FileNotFoundError(
            "master.properties not found. Set ETL_CONFIG_PATH or place master.properties in project root."
        )

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

    @staticmethod
    def _get_notebook_token():
        """Get AAD token from Fabric notebook runtime."""
        scope = "https://database.windows.net/"
        try:
            import notebookutils  # type: ignore

            if hasattr(notebookutils, "credentials"):
                return notebookutils.credentials.getToken(scope)
        except Exception:
            pass

        try:
            from notebookutils import mssparkutils  # type: ignore

            return mssparkutils.credentials.getToken(scope)
        except Exception as exc:
            raise RuntimeError(
                "FABRIC_AUTH_METHOD=Notebook requires Fabric notebook runtime credentials APIs."
            ) from exc

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
        )
        auth_method = auth_method.strip().lower()

        if auth_method == "serviceprincipal":
            tenant_id = self.config.get("FABRIC", "FABRIC_TENANT_ID")
            client_id = self.config.get("FABRIC", "FABRIC_CLIENT_ID")
            client_secret = self.config.get("FABRIC", "FABRIC_CLIENT_SECRET")
            credential = self._get_credential(
                auth_method=auth_method,
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )
            token = credential.get_token(
                "https://database.windows.net/.default"
            ).token
        elif auth_method == "notebook":
            token = self._get_notebook_token()
        else:
            # Interactive browser authentication (MFA supported)
            tenant_id = self.config.get("FABRIC", "FABRIC_TENANT_ID")
            credential = self._get_credential(auth_method="interactive", tenant_id=tenant_id)
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

    def execute_query(self, query):
        """Execute SQL query and return results"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(query)

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
