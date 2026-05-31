import os
import pytest
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine

client = TestClient(app)

DB_SRC_PATH = "test_sentry_src_test.db"
DB_TGT_PATH = "test_sentry_tgt_test.db"

@pytest.fixture(scope="module", autouse=True)
def setup_sentry_databases():
    """Sets up local test SQLite databases for source and target, populate tables, and cleans up."""
    # Ensure backend tables exist
    Base.metadata.create_all(bind=engine)
    
    for path in (DB_SRC_PATH, DB_TGT_PATH):
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
                
    src_engine = create_engine(f"sqlite:///{DB_SRC_PATH}")
    tgt_engine = create_engine(f"sqlite:///{DB_TGT_PATH}")
    
    # Populate Source A (3 products)
    with src_engine.connect() as conn:
        conn.execute(text("CREATE TABLE source_products (id INTEGER PRIMARY KEY, title TEXT, price REAL)"))
        conn.execute(text("INSERT INTO source_products (id, title, price) VALUES (1, 'Phone', 500.0)"))
        conn.execute(text("INSERT INTO source_products (id, title, price) VALUES (2, 'Tablet', 300.0)"))
        conn.execute(text("INSERT INTO source_products (id, title, price) VALUES (3, 'Watch', 150.0)"))
        conn.commit()
        
    # Populate Target B (Row 1 matches, Row 2 price mismatch, Row 3 missing, Row 4 extra)
    with tgt_engine.connect() as conn:
        conn.execute(text("CREATE TABLE target_products (id INTEGER PRIMARY KEY, title TEXT, price REAL)"))
        conn.execute(text("INSERT INTO target_products (id, title, price) VALUES (1, 'Phone', 500.0)"))
        conn.execute(text("INSERT INTO target_products (id, title, price) VALUES (2, 'Tablet', 290.0)")) # Mismatch
        conn.execute(text("INSERT INTO target_products (id, title, price) VALUES (4, 'Charger', 25.0)")) # Extra
        conn.commit()
        
    yield
    
    for path in (DB_SRC_PATH, DB_TGT_PATH):
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

def test_sentry_analyze():
    """Test POST /api/integration-sentry/analyze endpoint."""
    payload = {
        "system_a": {
            "system_type": "database",
            "environment": "DEV",
            "query": "SELECT * FROM source_products",
            "db_config": {"db_type": "sqlite", "db_name": DB_SRC_PATH}
        },
        "system_b": {
            "system_type": "database",
            "environment": "QA",
            "query": "SELECT * FROM target_products",
            "db_config": {"db_type": "sqlite", "db_name": DB_TGT_PATH}
        }
    }
    response = client.post("/api/integration-sentry/analyze", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert len(res["suggested_scenarios"]) >= 2
    assert len(res["system_a_schema"]) == 3
    assert len(res["system_b_schema"]) == 3
    
    # Assert cross-functional steps generated
    assert len(res["cross_functional_steps"]) >= 5
    assert "source_products" in "".join(res["cross_functional_steps"])
    assert "target_products" in "".join(res["cross_functional_steps"])

def test_sentry_execute_sync():
    """Test POST /api/integration-sentry/execute with sync_check scenario."""
    payload = {
        "system_a": {
            "system_type": "database",
            "environment": "DEV",
            "query": "SELECT * FROM source_products",
            "db_config": {"db_type": "sqlite", "db_name": DB_SRC_PATH}
        },
        "system_b": {
            "system_type": "database",
            "environment": "QA",
            "query": "SELECT * FROM target_products",
            "db_config": {"db_type": "sqlite", "db_name": DB_TGT_PATH}
        },
        "scenario_id": "sync_check",
        "key_column": "id"
    }
    response = client.post("/api/integration-sentry/execute", json=payload)
    assert response.status_code == 200
    res = response.json()
    # Both systems have 3 rows -> len(data_a) == len(data_b) -> Passed!
    assert res["passed"] is True
    assert res["accuracy"] == 100.0
    assert res["total_records_a"] == 3
    assert res["total_records_b"] == 3

def test_sentry_execute_bit_perfect():
    """Test POST /api/integration-sentry/execute with bit_perfect scenario."""
    payload = {
        "system_a": {
            "system_type": "database",
            "environment": "DEV",
            "query": "SELECT * FROM source_products",
            "db_config": {"db_type": "sqlite", "db_name": DB_SRC_PATH}
        },
        "system_b": {
            "system_type": "database",
            "environment": "QA",
            "query": "SELECT * FROM target_products",
            "db_config": {"db_type": "sqlite", "db_name": DB_TGT_PATH}
        },
        "scenario_id": "bit_perfect",
        "key_column": "id"
    }
    response = client.post("/api/integration-sentry/execute", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["passed"] is False
    assert res["accuracy"] < 100.0
    
    # Check mismatch details
    # 1. ID 2 has price mismatch (300 vs 290)
    # 2. ID 3 is missing in target
    mismatches = {m["id"]: m for m in res["mismatch_details"]}
    assert "2" in mismatches
    assert mismatches["2"]["field"] == "price"
    assert mismatches["2"]["source"] == "500.0" or mismatches["2"]["source"] == "300.0"
    
    assert "3" in mismatches
    assert mismatches["3"]["field"] == "Record"
    assert mismatches["3"]["target"] == "Missing"
