import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.config import DbConnectionConfig
from app.services.config_service import load_db_config

client = TestClient(app)

def test_config_db_endpoints():
    # 1. GET current database config
    response = client.get("/api/config/db")
    assert response.status_code == 200
    cfg = response.json()
    assert "engine" in cfg
    assert "db_name" in cfg

    # Save original config
    original_cfg = dict(cfg)

    # 2. POST updated database config
    test_payload = {
        "engine": "sqlite",
        "host": "localhost",
        "port": "5432",
        "db_name": "etl_test.db",
        "username": "",
        "password": ""
    }
    post_response = client.post("/api/config/db", json=test_payload)
    assert post_response.status_code == 200
    post_json = post_response.json()
    assert post_json["message"] == "Database configuration saved successfully"
    assert post_json["config"]["db_name"] == "etl_test.db"

    # Restore original config
    client.post("/api/config/db", json=original_cfg)

def test_db_tables_endpoint():
    # Test getting tables list from the configured database
    response = client.get("/api/interactive-testing/db-tables")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "tables" in data
    assert isinstance(data["tables"], list)

    # Alias path
    response_alias = client.get("/api/db-tables")
    assert response_alias.status_code == 200

def test_analyze_schema_details_endpoint():
    payload = {
        "table_name": "products",
        "columns": [
            {"name": "id", "type": "INTEGER"},
            {"name": "title", "type": "VARCHAR(255)"},
            {"name": "price", "type": "FLOAT"}
        ]
    }
    response = client.post("/api/interactive-testing/analyze-schema-details", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["table_name"] == "products"
    
    recommended = data["recommended_tests"]
    types = [test["type"] for test in recommended]
    assert "Primary Key Check" in types
    assert "Null Value Check" in types
    assert "Data Quality Check" in types

def test_execute_batch_db_validations():
    payload = [
        {
            "query": "SELECT COUNT(*) FROM products",
            "validation_type": "raw",
            "expected_condition": "GREATER_THAN",
            "expected_value": 0
        },
        {
            "query": "SELECT id, COUNT(*) FROM products GROUP BY id HAVING COUNT(*) > 1",
            "validation_type": "duplicates",
            "expected_condition": "EQUAL",
            "expected_value": 0
        }
    ]
    response = client.post("/api/interactive-testing/execute-batch-db-validations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "passed" in data
    assert "details" in data
    assert len(data["details"]["results"]) == 2


def test_unsafe_sql_execution():
    # 1. Unsafe query on /interactive-db-query should raise 400 Bad Request
    destructive_payload = {
        "query": "DROP TABLE products",
        "validation_type": "raw",
        "expected_condition": "EQUAL",
        "expected_value": 0
    }
    response = client.post("/api/interactive-db-query", json=destructive_payload)
    assert response.status_code == 400
    assert "Unsafe SQL" in response.json()["detail"]

    # 2. Safe query on /interactive-db-query should succeed (200)
    safe_payload = {
        "query": "SELECT COUNT(*) FROM products",
        "validation_type": "raw",
        "expected_condition": "GREATER_THAN",
        "expected_value": 0
    }
    response = client.post("/api/interactive-db-query", json=safe_payload)
    assert response.status_code == 200
    assert response.json()["passed"] is True


def test_unsafe_sql_batch_execution():
    # Destructive query in batch should not crash the batch validation, but mark the specific validation as failed.
    payload = [
        {
            "query": "SELECT COUNT(*) FROM products",
            "validation_type": "raw",
            "expected_condition": "GREATER_THAN",
            "expected_value": 0
        },
        {
            "query": "DROP TABLE products",
            "validation_type": "raw",
            "expected_condition": "EQUAL",
            "expected_value": 0
        }
    ]
    response = client.post("/api/interactive-testing/execute-batch-db-validations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["passed"] is False  # batch overall failed because of the destructive query
    results = data["details"]["results"]
    assert len(results) == 2
    assert results[0]["passed"] is True
    assert results[1]["passed"] is False
    assert "Unsafe SQL" in results[1]["error"]

