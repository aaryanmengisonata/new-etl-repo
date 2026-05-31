import time
import requests
import json
from sqlalchemy import text
from app.database import get_dynamic_engine
from app.models.integration_sentry import (
    SystemAnalysisRequest, SystemAnalysisResponse, IntegrationScenario,
    ReconciliationRequest, ReconciliationResult, SystemDefinition
)
from app.services.pipeline_auditor_service import (
    build_engine_from_config, validate_sql_safety, fetch_db_data, convert_numpy_types
)

def values_are_equal(v_a, v_b) -> bool:
    """
    Robust comparison of cell values, handling None/NULL representations,
    numeric float alignment, boolean variants, and JSON-serialized structures.
    """
    def normalize_value(val):
        if val is None:
            return None
        if isinstance(val, str):
            val_stripped = val.strip()
            if val_stripped.upper() in ("NONE", "NULL", ""):
                return None
            return val_stripped
        return val

    norm_a = normalize_value(v_a)
    norm_b = normalize_value(v_b)

    if norm_a is None and norm_b is None:
        return True
    if norm_a is None or norm_b is None:
        return False

    # Try numeric comparison
    try:
        is_bool_a = isinstance(norm_a, bool)
        is_bool_b = isinstance(norm_b, bool)
        
        if is_bool_a or is_bool_b:
            def to_bool(x):
                if isinstance(x, bool):
                    return x
                if isinstance(x, (int, float)):
                    return bool(x)
                if isinstance(x, str):
                    return x.lower() in ("true", "1", "yes", "t")
                return False
            return to_bool(norm_a) == to_bool(norm_b)
            
        float_a = float(norm_a)
        float_b = float(norm_b)
        return float_a == float_b
    except (ValueError, TypeError):
        pass

    # Try JSON parsing
    def try_json_load(x):
        if isinstance(x, str):
            cleaned = x.strip()
            if (cleaned.startswith('{') and cleaned.endswith('}')) or (cleaned.startswith('[') and cleaned.endswith(']')):
                try:
                    return json.loads(cleaned)
                except Exception:
                    pass
        return x

    json_a = try_json_load(norm_a)
    json_b = try_json_load(norm_b)
    if type(json_a) != type(norm_a) or type(json_b) != type(norm_b):
        if json_a == json_b:
            return True

    # Fallback to basic equality check, and then string representation comparison
    if norm_a == norm_b:
        return True

    return str(norm_a) == str(norm_b)


def _fetch_system_data(system: SystemDefinition, logs: list, row_limit: int = 10000, chunk_size: int = 2000, query_timeout: int = 30):
    """Fetch data dynamically from either a Database or an API."""
    timestamp = lambda: time.strftime('%H:%M:%S')
    
    if system.system_type == "database":
        logs.append(f"[{timestamp()}] [PROCESS] Connecting to Database (Env: {system.environment})...")
        
        if system.db_config:
            engine = build_engine_from_config(system.db_config)
            db_name = system.db_config.get("db_name", "")
            db_type = system.db_config.get("db_type", "sqlite").upper()
            logs.append(f"[{timestamp()}] [INFO] Connected to database: {db_name} ({db_type}).")
        else:
            engine = get_dynamic_engine()
            logs.append(f"[{timestamp()}] [INFO] Connected to default database.")
            
        validate_sql_safety(system.query)
        
        logs.append(f"[{timestamp()}] [PROCESS] Executing Query: {system.query[:100]}...")
        
        try:
            df = fetch_db_data(engine, system.query, row_limit=row_limit, chunk_size=chunk_size, query_timeout=query_timeout)
            columns = [{"name": col, "type": str(dtype)} for col, dtype in df.dtypes.items()]
            rows = convert_numpy_types(df.to_dict(orient="records"))
            logs.append(f"[{timestamp()}] [SUCCESS] Fetched {len(rows)} records from Database.")
            return rows, columns
        except Exception as e:
            logs.append(f"[{timestamp()}] [ERROR] Database fetch failed: {str(e)}")
            raise
            
    elif system.system_type == "api":
        logs.append(f"[{timestamp()}] [PROCESS] Connecting to API (Env: {system.environment})...")
        logs.append(f"[{timestamp()}] [PROCESS] Request: {system.method} {system.url}")
        
        headers = system.headers or {}
        kwargs = {"headers": headers, "timeout": query_timeout}
        
        if system.method.upper() in ["POST", "PUT", "PATCH"] and system.payload:
            try:
                kwargs["json"] = json.loads(system.payload)
            except:
                kwargs["data"] = system.payload
                
        try:
            response = requests.request(system.method, system.url, **kwargs)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, list):
                        data = val
                        break
                if isinstance(data, dict):
                    data = [data]
            
            if not isinstance(data, list):
                data = [data]
                
            if len(data) > row_limit:
                data = data[:row_limit]
                
            logs.append(f"[{timestamp()}] [SUCCESS] Fetched {len(data)} records from API.")
            
            columns = []
            if data and isinstance(data[0], dict):
                columns = [{"name": k, "type": type(v).__name__} for k, v in data[0].items()]
                
            return data, columns
        except Exception as e:
            logs.append(f"[{timestamp()}] [ERROR] API request failed: {str(e)}")
            raise
    else:
        raise ValueError(f"Unknown system type: {system.system_type}")

def analyze_systems(request: SystemAnalysisRequest) -> SystemAnalysisResponse:
    """Analyze two systems and suggest integration test scenarios."""
    logs = []
    schema_a = []
    schema_b = []
    
    try:
        data_a, cols_a = _fetch_system_data(request.system_a, logs, row_limit=5)
        schema_a = cols_a
    except Exception as e:
        logs.append(f"[WARNING] System A analysis failed: {str(e)}")
        
    try:
        data_b, cols_b = _fetch_system_data(request.system_b, logs, row_limit=5)
        schema_b = cols_b
    except Exception as e:
        logs.append(f"[WARNING] System B analysis failed: {str(e)}")
        
    scenarios = [
        IntegrationScenario(
            id="sync_check",
            name="Data Synchronization Check",
            description="Verify that records exist in both systems and row counts match.",
            type="data_sync"
        ),
        IntegrationScenario(
            id="bit_perfect",
            name="Bit-Perfect Data Reconciliation",
            description="Row-by-row comparison of all fields using a designated key column.",
            type="data_diff"
        )
    ]
    
    if request.system_a.system_type == "api" and request.system_b.system_type == "database":
         scenarios.append(IntegrationScenario(
            id="api_db_flow",
            name="End-to-End API to Database Flow",
            description="Validates that data ingested from the API was properly transformed and loaded into the DB.",
            type="data_flow"
        ))
        
    # Auto-generate steps listing linking sequence
    steps = []
    type_a = request.system_a.system_type.upper()
    type_b = request.system_b.system_type.upper()
    
    steps.append(f"1. Establish connection channels to System A ({type_a}) in environment: {request.system_a.environment}.")
    steps.append(f"2. Establish connection channels to System B ({type_b}) in environment: {request.system_b.environment}.")
    
    if request.system_a.system_type == "api":
        steps.append(f"3. Ingest raw JSON payload from Endpoint: {request.system_a.url}.")
    else:
        steps.append(f"3. Queries DB table using statement: '{request.system_a.query[:40]}...'.")
        
    if request.system_b.system_type == "api":
        steps.append(f"4. Queries target payload from Endpoint: {request.system_b.url}.")
    else:
        steps.append(f"4. Queries target DB table using statement: '{request.system_b.query[:40]}...'.")
        
    steps.append("5. Maps record matrices using matching key and audits cell equality to produce divergence metrics.")
    steps.append("6. Outputs AI Insights root cause reports and persists logs to telemetry database.")
    
    return SystemAnalysisResponse(
        suggested_scenarios=scenarios,
        system_a_schema=schema_a,
        system_b_schema=schema_b,
        cross_functional_steps=steps
    )

def execute_reconciliation(request: ReconciliationRequest) -> ReconciliationResult:
    """Execute the cross-system reconciliation."""
    logs = []
    timestamp = lambda: time.strftime('%H:%M:%S')
    start_time = time.time()
    
    logs.append(f"[{timestamp()}] [INFO] Starting Cross-System Integration Check...")
    logs.append(f"[{timestamp()}] [INFO] Scenario: {request.scenario_id}")
    
    try:
        # Fetch Data
        data_a, cols_a = _fetch_system_data(request.system_a, logs, row_limit=request.row_limit, chunk_size=request.chunk_size, query_timeout=request.query_timeout)
        data_b, cols_b = _fetch_system_data(request.system_b, logs, row_limit=request.row_limit, chunk_size=request.chunk_size, query_timeout=request.query_timeout)
        
        matches = 0
        mismatches = 0
        mismatch_details = []
        
        if request.scenario_id == "sync_check":
            logs.append(f"[{timestamp()}] [PROCESS] Comparing record counts...")
            if len(data_a) == len(data_b):
                matches = len(data_a)
            else:
                mismatches = abs(len(data_a) - len(data_b))
                mismatch_details.append({
                    "id": "COUNT_MISMATCH",
                    "field": "Row Count",
                    "source": str(len(data_a)),
                    "target": str(len(data_b)),
                    "risk": "High"
                })
        else:
            key_col = request.key_column or "id"
            logs.append(f"[{timestamp()}] [PROCESS] Performing row-by-row comparison using key: '{key_col}'...")
            
            b_dict = {str(row.get(key_col)): row for row in data_b if key_col in row}
            
            for row_a in data_a:
                key_val = str(row_a.get(key_col))
                if not key_val or key_val == "None":
                    continue
                    
                if key_val not in b_dict:
                    mismatches += 1
                    mismatch_details.append({
                        "id": key_val,
                        "field": "Record",
                        "source": "Present",
                        "target": "Missing",
                        "risk": "High"
                    })
                    continue
                    
                row_b = b_dict[key_val]
                row_mismatch = False
                
                # Compare fields
                for k, v_a in row_a.items():
                    if k == key_col: continue
                    v_b = row_b.get(k)
                    if not values_are_equal(v_a, v_b):
                        mismatches += 1
                        row_mismatch = True
                        mismatch_details.append({
                            "id": key_val,
                            "field": k,
                            "source": str(v_a)[:50],
                            "target": str(v_b)[:50],
                            "risk": "Medium"
                        })
                        if len(mismatch_details) > 100:
                            break
                            
                if not row_mismatch:
                    matches += 1
                    
                if len(mismatch_details) > 100:
                    logs.append(f"[{timestamp()}] [WARNING] Max mismatches (100) reached. Truncating diff report.")
                    break
                    
        total_checks = matches + mismatches
        accuracy = (matches / total_checks * 100) if total_checks > 0 else 100.0
        passed = accuracy == 100.0
        
        exec_time = time.time() - start_time
        logs.append(f"[{timestamp()}] [SUCCESS] Reconciliation complete in {exec_time:.2f}s. Accuracy: {accuracy:.1f}%")
        
        return ReconciliationResult(
            passed=passed,
            accuracy=accuracy,
            matches=matches,
            mismatches=mismatches,
            total_records_a=len(data_a),
            total_records_b=len(data_b),
            mismatch_details=mismatch_details,
            execution_logs=logs
        )
        
    except Exception as e:
        logs.append(f"[{timestamp()}] [ERROR] Reconciliation failed: {str(e)}")
        return ReconciliationResult(
            passed=False,
            accuracy=0.0,
            matches=0,
            mismatches=0,
            total_records_a=0,
            total_records_b=0,
            mismatch_details=[{"id": "ERR", "field": "System", "source": "Failed", "target": str(e), "risk": "Critical"}],
            execution_logs=logs
        )
