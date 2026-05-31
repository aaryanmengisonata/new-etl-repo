import os
import pytest
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient

from app.main import app
from app.services.pipeline_auditor_service import validate_sql_safety
from app.database import Base, engine

client = TestClient(app)

DB_SRC_PATH = "test_audit_src_test.db"
DB_TGT_PATH = "test_audit_tgt_test.db"


@pytest.fixture(scope="module", autouse=True)
def setup_test_databases():
    """
    Sets up local test SQLite databases for source and target,
    inserts mock records with mismatching data, and cleans up afterwards.
    """
    # Create all backend tables in the application database (e.g. etl_test_api.db)
    Base.metadata.create_all(bind=engine)

    # Cleanup any leftovers
    for path in (DB_SRC_PATH, DB_TGT_PATH):

        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    src_engine = create_engine(f"sqlite:///{DB_SRC_PATH}")
    tgt_engine = create_engine(f"sqlite:///{DB_TGT_PATH}")

    # Populate Source
    with src_engine.connect() as conn:
        conn.execute(text("CREATE TABLE products (id INTEGER PRIMARY KEY, title TEXT, price REAL, category TEXT)"))
        conn.execute(text("INSERT INTO products (id, title, price, category) VALUES (1, 'Laptop', 1000.0, 'Electronics')"))
        conn.execute(text("INSERT INTO products (id, title, price, category) VALUES (2, 'Smartphone', 500.0, 'Electronics')"))
        # Row 3
        conn.execute(text("INSERT INTO products (id, title, price, category) VALUES (3, 'Shoes', 80.0, 'Footwear')"))
        conn.commit()

    # Populate Target (with modifications to trigger check failures)
    #  - Row 1: Identical
    #  - Row 2: Price mismatch (490.0 instead of 500.0)
    #  - Row 3: Category is NULL (to test Null check)
    #  - Row 4: Duplicate of Row 1 (to test Duplicate check)
    #  - Source row 3 is omitted in target to test missing record detection
    with tgt_engine.connect() as conn:
        conn.execute(text("CREATE TABLE products_silver (id INTEGER, title TEXT, price REAL, category TEXT)"))
        conn.execute(text("INSERT INTO products_silver (id, title, price, category) VALUES (1, 'Laptop', 1000.0, 'Electronics')"))
        conn.execute(text("INSERT INTO products_silver (id, title, price, category) VALUES (2, 'Smartphone', 490.0, 'Electronics')"))
        conn.execute(text("INSERT INTO products_silver (id, title, price, category) VALUES (1, 'Laptop', 1000.0, 'Electronics')"))  # Duplicate
        conn.execute(text("INSERT INTO products_silver (id, title, price, category) VALUES (4, 'Tablet', 300.0, NULL)"))  # Null category
        conn.commit()

    yield

    # Teardown database files
    for path in (DB_SRC_PATH, DB_TGT_PATH):
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════
# 1. SQL Safety Layer Tests
# ══════════════════════════════════════════════════════════════════════

def test_sql_safety_valid():
    """Verify safe SQL statements are allowed."""
    validate_sql_safety("SELECT * FROM products")
    validate_sql_safety("  WITH cte AS (SELECT id FROM products) SELECT * FROM cte; -- trailing comment ")
    validate_sql_safety("/* multi-line comment */ SELECT SUM(price) FROM products WHERE id = 1")


def test_sql_safety_invalid():
    """Verify destructive SQL statements are blocked."""
    with pytest.raises(ValueError, match="Unsafe SQL"):
        validate_sql_safety("DROP TABLE products")

    with pytest.raises(ValueError, match="Unsafe SQL"):
        validate_sql_safety("DELETE FROM products WHERE id = 1")

    with pytest.raises(ValueError, match="Unsafe SQL"):
        validate_sql_safety("UPDATE products SET price = 0")

    with pytest.raises(ValueError, match="Unsafe SQL"):
        validate_sql_safety("CREATE TABLE temp_table (id INT)")

    with pytest.raises(ValueError, match="Unsafe SQL"):
        validate_sql_safety("ALTER TABLE products ADD COLUMN age INT")

    with pytest.raises(ValueError, match="Unsafe SQL"):
        validate_sql_safety("TRUNCATE TABLE products")

    with pytest.raises(ValueError, match="Unsafe SQL: Query must start with SELECT or WITH"):
        validate_sql_safety("INSERT INTO products VALUES (4, 'Key', 1.0, 'Cat')")


# ══════════════════════════════════════════════════════════════════════
# 2. Connection Testing Endpoints
# ══════════════════════════════════════════════════════════════════════

def test_api_test_connection():
    """Test POST /api/pipeline-auditor/test-connection"""
    payload = {
        "type": "database",
        "config": {
            "db_type": "sqlite",
            "db_name": DB_SRC_PATH
        }
    }
    response = client.post("/api/pipeline-auditor/test-connection", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert "products" in res["metadata"]["tables"]


# ══════════════════════════════════════════════════════════════════════
# 3. Pipeline Schema Analysis Endpoint
# ══════════════════════════════════════════════════════════════════════

def test_api_analyze_pipeline():
    """Test POST /api/pipeline-auditor/analyze"""
    payload = {
        "source_type": "database",
        "source_config": {"db_type": "sqlite", "db_name": DB_SRC_PATH},
        "target_type": "database",
        "target_config": {"db_type": "sqlite", "db_name": DB_TGT_PATH},
        "source_query": "SELECT * FROM products",
        "target_query": "SELECT * FROM products_silver",
        "key_columns": ["id"],
        "pipeline_name": "Test Bronze to Silver"
    }
    response = client.post("/api/pipeline-auditor/analyze", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    assert len(res["suggestions"]) >= 4
    
    # Assert specific suggestions were made dynamically
    sug_ids = [s["id"] for s in res["suggestions"]]
    assert "RC_001" in sug_ids  # Row Count
    assert "SV_001" in sug_ids  # Schema Validation
    assert "EM_001" in sug_ids  # Exact Match
    assert "MR_001" in sug_ids  # Missing Records


# ══════════════════════════════════════════════════════════════════════
# 4. Pipeline Audit Execution Endpoint
# ══════════════════════════════════════════════════════════════════════

def test_api_execute_audit():
    """Test POST /api/pipeline-auditor/execute and verify validation strategies."""
    payload = {
        "pipeline_name": "Test Exec Suite",
        "environment": "DEV",
        "pipeline_type": "BronzeToSilver",
        "source_type": "database",
        "source_config": {"db_type": "sqlite", "db_name": DB_SRC_PATH, "password": "RAW_PASSWORD_TEST"},
        "target_type": "database",
        "target_config": {"db_type": "sqlite", "db_name": DB_TGT_PATH},
        "source_query": "SELECT * FROM products",
        "target_query": "SELECT * FROM products_silver",
        "key_columns": ["id"],
        "validations": [
            {
                "id": "RC_001",
                "name": "Row Count Check",
                "type": "row_count",
                "severity": "critical",
                "enabled": True
            },
            {
                "id": "SV_001",
                "name": "Schema Check",
                "type": "schema_validation",
                "severity": "high",
                "enabled": True
            },
            {
                "id": "EM_001",
                "name": "Exact Match Check",
                "type": "exact_match",
                "severity": "critical",
                "enabled": True
            },
            {
                "id": "DC_id",
                "name": "Duplicate Key Check",
                "type": "duplicate_check",
                "column_name": "id",
                "severity": "high",
                "enabled": True
            },
            {
                "id": "NC_category",
                "name": "Null Check Category",
                "type": "null_check",
                "column_name": "category",
                "severity": "high",
                "enabled": True
            },
            {
                "id": "AG_price_SUM",
                "name": "Price Aggregate Check",
                "type": "aggregate",
                "aggregate_function": "SUM",
                "aggregate_column": "price",
                "severity": "medium",
                "enabled": True
            },
            {
                "id": "MR_001",
                "name": "Missing Records Check",
                "type": "missing_records",
                "severity": "critical",
                "enabled": True
            }
        ],
        "row_limit": 1000,
        "chunk_size": 100
    }
    response = client.post("/api/pipeline-auditor/execute", json=payload)
    if response.status_code != 200:
        print("ERROR BODY:", response.text)
    assert response.status_code == 200
    res = response.json()
    
    assert res["status"] == "success"
    assert res["audit_id"] > 0
    assert "summary" in res
    
    results = {r["id"]: r for r in res["results"]}
    
    # 1. Row count validation (Source=3, Target=4 -> difference 1 -> FAILED)
    assert results["RC_001"]["status"] == "failed"
    assert results["RC_001"]["records_checked"] == 3
    assert results["RC_001"]["records_failed"] == 1
    
    # 2. Schema check (Columns match -> PASSED)
    assert results["SV_001"]["status"] == "passed"
    
    # 3. Exact Match (Row 1 identical, Row 2 price mismatch 500 vs 490 -> FAILED)
    assert results["EM_001"]["status"] == "failed"
    assert results["EM_001"]["records_failed"] > 0
    
    # 4. Duplicate Check (id 1 exists twice in target -> FAILED)
    assert results["DC_id"]["status"] == "failed"
    assert results["DC_id"]["records_failed"] == 1
    
    # 5. Null Check (Row 4 category is NULL -> FAILED)
    assert results["NC_category"]["status"] == "failed"
    assert results["NC_category"]["records_failed"] == 1
    
    # 6. Aggregate Check (Source SUM = 1580, Target SUM = 2790 -> FAILED)
    assert results["AG_price_SUM"]["status"] == "failed"
    
    # 7. Missing records (Source ID 3 omitted in Target -> FAILED)
    assert results["MR_001"]["status"] == "failed"
    assert results["MR_001"]["records_failed"] == 1

    # Verify AI Insights populated
    assert res["ai_insights"] is not None
    assert len(res["ai_insights"]["failures"]) >= 5

    # Verify connection logs masked RAW_PASSWORD_TEST
    logs_str = "".join(res["execution_logs"])
    assert "RAW_PASSWORD_TEST" not in logs_str


# ══════════════════════════════════════════════════════════════════════
# 5. History & Paginated Fetch Endpoints
# ══════════════════════════════════════════════════════════════════════

def test_api_history_and_detail():
    """Test GET /api/pipeline-auditor/history and GET /api/pipeline-auditor/history/{id}"""
    # Retrieve paginated history
    history_response = client.get("/api/pipeline-auditor/history?page=1&page_size=10&environment=DEV")
    assert history_response.status_code == 200
    history = history_response.json()
    assert "items" in history
    assert len(history["items"]) >= 1
    
    audit_id = history["items"][0]["id"]
    
    # Retrieve detail
    detail_response = client.get(f"/api/pipeline-auditor/history/{audit_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == audit_id
    # Assert password masked
    assert detail["source_config"]["password"] == "••••••••"


# ══════════════════════════════════════════════════════════════════════
# 6. Report Export Endpoint
# ══════════════════════════════════════════════════════════════════════

def test_api_export_reports():
    """Test POST /api/pipeline-auditor/export as CSV, JSON, and Excel"""
    # Fetch latest audit ID
    history = client.get("/api/pipeline-auditor/history").json()
    audit_id = history["items"][0]["id"]
    
    # Test CSV export
    csv_resp = client.post("/api/pipeline-auditor/export", json={"audit_id": audit_id, "format": "csv"})
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert b"Check ID,Check Name,Check Type" in csv_resp.content

    # Test JSON export
    json_resp = client.post("/api/pipeline-auditor/export", json={"audit_id": audit_id, "format": "json"})
    assert json_resp.status_code == 200
    assert json_resp.headers["content-type"] == "application/json"
    assert json_resp.json()["id"] == audit_id

    # Test Excel export
    excel_resp = client.post("/api/pipeline-auditor/export", json={"audit_id": audit_id, "format": "excel"})
    assert excel_resp.status_code == 200
    assert excel_resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(excel_resp.content) > 1000  # valid binary bytes
