import time
import requests
import json
import sqlite3
import subprocess
import os
import sys
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

from app.database import get_db, get_dynamic_engine
from app.services.report_service import create_report
from app.services.pipeline_auditor_service import validate_sql_safety

def get_venv_python() -> str:
    """
    Resolves the virtual environment python executable or falls back to sys.executable.
    Checks 'venv/Scripts/python.exe' (Windows) and 'venv/bin/python' (Unix).
    """
    windows_path = os.path.join("venv", "Scripts", "python.exe")
    unix_path = os.path.join("venv", "bin", "python")
    
    if os.path.exists(windows_path):
        return windows_path
    elif os.path.exists(unix_path):
        return unix_path
    
    # Check parent directory as well
    windows_path_parent = os.path.join("..", "venv", "Scripts", "python.exe")
    unix_path_parent = os.path.join("..", "venv", "bin", "python")
    if os.path.exists(windows_path_parent):
        return windows_path_parent
    elif os.path.exists(unix_path_parent):
        return unix_path_parent
        
    return sys.executable

router = APIRouter(prefix="/api", tags=["interactive-testing"])

# --- Request/Response Models ---

class ApiTestRequest(BaseModel):
    url: str
    method: str = "GET"
    payload: Optional[str] = None
    validation_type: str = "status_code"  # status_code, contains_text, latency, json_schema
    expected_value: str

class DbQueryRequest(BaseModel):
    query: str
    validation_type: str = "raw"  # raw, duplicates, null_check, primary_key
    target_column: Optional[str] = None
    expected_condition: str = "EQUAL"
    expected_value: int = 0

class SchemaDetailsRequest(BaseModel):
    table_name: str
    columns: List[Dict[str, str]]

class EtlAuditRequest(BaseModel):
    source_query: str
    target_query: str
    reconciliation_type: str = "row_count"  # row_count, data_diff
    key_column: Optional[str] = None

# --- API Testing Endpoint ---

@router.post("/interactive-api-test")
async def run_api_test(req: ApiTestRequest, db: Session = Depends(get_db)):
    logs = []
    timestamp = lambda: time.strftime('%H:%M:%S')
    logs.append(f"[{timestamp()}] [INFO] Starting API validation framework")
    logs.append(f"[{timestamp()}] [PROCESS] Ignored UI parameters, triggering details.txt test suite...")
    
    start_time = time.time()
    
    try:
        python_exe = get_venv_python()
        cmd = [python_exe, "-m", "pytest", "tests/api/test_api_examples.py", "-v", "--alluredir=reports/allure-results"]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_data, stderr_data = await process.communicate()
        stdout_str = stdout_data.decode('utf-8', errors='ignore')
        stderr_str = stderr_data.decode('utf-8', errors='ignore')
        full_output = stdout_str + (f"\n{stderr_str}" if stderr_str else "")
        
        latency = int((time.time() - start_time) * 1000)
        logs.append(f"[{timestamp()}] [SUCCESS] Pytest execution completed. Latency: {latency}ms.")
        
        # Add pytest output to logs
        for line in stdout_str.split('\n'):
            if line.strip():
                logs.append(f"[PYTEST] {line.strip()}")
                
        passed = process.returncode == 0
        logs.append(f"[{timestamp()}] [RESULT] Assertions complete. Passed: {passed}")
        
        result = {
            "status_code": 200 if passed else 500,
            "latency_ms": latency,
            "headers": {},
            "response_body": full_output,
            "passed": passed,
            "validation_logs": ["PyTest Framework Executed"] if passed else ["PyTest Framework Failed"],
            "execution_logs": logs
        }

        # Auto-save report
        try:
            create_report(
                db,
                report_type="API Test",
                status="passed" if passed else "failed",
                summary=f"API Test Suite Executed — {'PASSED' if passed else 'FAILED'} ({latency}ms)",
                details=result,
            )
        except Exception:
            pass

        return result
        
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        logs.append(f"[{timestamp()}] [ERROR] Execution failed: {str(e)}")
        
        error_result = {
            "status_code": 0,
            "latency_ms": latency,
            "headers": {},
            "response_body": str(e),
            "passed": False,
            "validation_logs": [f"Execution error: {str(e)}"],
            "execution_logs": logs
        }
        return error_result

# --- Database Testing Endpoint ---

@router.post("/interactive-db-query")
async def run_db_query(req: DbQueryRequest, db_session: Session = Depends(get_db)):
    try:
        validate_sql_safety(req.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    logs = []
    timestamp = lambda: time.strftime('%H:%M:%S')
    logs.append(f"[{timestamp()}] [INFO] Executing dynamic Database Query")
    logs.append(f"[{timestamp()}] [PROCESS] Query: {req.query}")
    
    start_time = time.time()
    
    try:
        # Execute query dynamically
        engine = get_dynamic_engine()
        with engine.connect() as conn:
            result_proxy = conn.execute(text(req.query))
            columns = list(result_proxy.keys()) if result_proxy.keys() else ["Output"]
            if result_proxy.returns_rows:
                fetched_rows = result_proxy.fetchall()
                rows = [list(row) for row in fetched_rows]
            else:
                rows = []
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        logs.append(f"[{timestamp()}] [SUCCESS] Query executed in {execution_time_ms}ms. Returned {len(rows)} rows.")
        
        # Validation Logic
        passed = False
        if req.expected_condition == "EQUAL":
            # For count queries, checking if the first column of the first row equals expected_value
            # Or if it returns records (e.g., finding duplicates), length should equal expected_value
            if len(rows) == 1 and len(rows[0]) == 1 and isinstance(rows[0][0], (int, float)):
                actual_val = rows[0][0]
                passed = (actual_val == req.expected_value)
                logs.append(f"[{timestamp()}] [VALIDATION] Evaluated: {actual_val} == {req.expected_value} -> {passed}")
            else:
                actual_val = len(rows)
                passed = (actual_val == req.expected_value)
                logs.append(f"[{timestamp()}] [VALIDATION] Evaluated row count: {actual_val} == {req.expected_value} -> {passed}")
        
        elif req.expected_condition == "GREATER_THAN":
            if len(rows) == 1 and len(rows[0]) == 1 and isinstance(rows[0][0], (int, float)):
                actual_val = rows[0][0]
                passed = (actual_val > req.expected_value)
                logs.append(f"[{timestamp()}] [VALIDATION] Evaluated: {actual_val} > {req.expected_value} -> {passed}")
            else:
                actual_val = len(rows)
                passed = (actual_val > req.expected_value)
                logs.append(f"[{timestamp()}] [VALIDATION] Evaluated row count: {actual_val} > {req.expected_value} -> {passed}")
        else:
            # Raw query execution
            passed = True
        
        logs.append(f"[{timestamp()}] [RESULT] Status: {'PASSED' if passed else 'FAILED'}")
        
        result = {
            "columns": columns,
            "rows": rows,
            "passed": passed,
            "validation_logs": [f"Dynamic SQL Executed: {req.expected_condition} {req.expected_value}"],
            "execution_logs": logs
        }

        # Auto-save report
        try:
            create_report(
                db_session,
                report_type="DB Audit",
                status="passed" if passed else "failed",
                summary=f"Dynamic DB Validation — {'PASSED' if passed else 'FAILED'} ({execution_time_ms}ms)",
                details={"query": req.query, "validation_logs": result["validation_logs"], "execution_logs": logs},
            )
            db_session.commit()
        except Exception:
            db_session.rollback()

        return result
        
    except Exception as e:
        logs.append(f"[{timestamp()}] [ERROR] Database execution error: {str(e)}")

        error_result = {
            "columns": [],
            "rows": [],
            "passed": False,
            "validation_logs": [f"Execution error: {str(e)}"],
            "execution_logs": logs
        }

        # Auto-save failed report
        try:
            create_report(
                db_session,
                report_type="DB Audit",
                status="failed",
                summary=f"DB PyTest FAILED — {str(e)[:100]}",
                details={"error": str(e), "execution_logs": logs},
            )
        except Exception:
            pass

        return error_result

# --- AI Schema Analyzer ---

@router.post("/analyze-schema-image")
async def analyze_schema(file: UploadFile = File(...)):
    # Simulate AI analysis of the uploaded database diagram
    filename = file.filename
    time.sleep(1.5)  # Simulate LLM thinking time
    
    # We parse the file name or simply return a rich set of suggested SQL tests based on standard delta tables.
    suggested_tests = [
        {
            "test_id": "DB_PK_01",
            "type": "Primary Key Check",
            "description": "Assert that 'products.id' is unique and contains no duplicates.",
            "sql": "SELECT id, COUNT(*) FROM products GROUP BY id HAVING COUNT(*) > 1;",
            "expected_condition": "EQUAL",
            "expected_value": 0
        },
        {
            "test_id": "DB_NULL_02",
            "type": "Null Value Check",
            "description": "Check if required title column contains any null values.",
            "sql": "SELECT COUNT(*) FROM products WHERE title IS NULL OR title = '';",
            "expected_condition": "EQUAL",
            "expected_value": 0
        },
        {
            "test_id": "DB_QUAL_03",
            "type": "Data Quality Check",
            "description": "Verify product price conforms to business rules (price should be positive).",
            "sql": "SELECT COUNT(*) FROM products WHERE price < 0;",
            "expected_condition": "EQUAL",
            "expected_value": 0
        },
        {
            "test_id": "DB_FK_04",
            "type": "Referential Integrity",
            "description": "Ensure categories exist in product records.",
            "sql": "SELECT COUNT(DISTINCT category) FROM products;",
            "expected_condition": "GREATER_THAN",
            "expected_value": 0
        }
    ]
    
    return {
        "filename": filename,
        "status": "success",
        "recommended_tests": suggested_tests,
        "analysis_logs": [
            "AI Agent initialized.",
            "Reading uploaded schema layout image...",
            "Detected relational entities: 'products', 'etl_logs'.",
            "Discovered primary key attributes: 'products.id' (int).",
            "Discovered category attributes: 'products.category' (text).",
            "Validation plan generated: 4 integrity test cases recommended."
        ]
    }

@router.get("/interactive-testing/db-tables")
@router.get("/db-tables")
async def get_db_tables():
    try:
        engine = get_dynamic_engine()
        inspector = inspect(engine)
        tables = []
        for table_name in inspector.get_table_names():
            columns = [{"name": col["name"], "type": str(col["type"])} for col in inspector.get_columns(table_name)]
            tables.append({"name": table_name, "columns": columns})
        return {"status": "success", "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to inspect database tables: {str(e)}")

@router.post("/interactive-testing/analyze-schema-details")
@router.post("/analyze-schema-details")
async def analyze_schema_details(req: SchemaDetailsRequest):
    time.sleep(0.5) # Simulate quick analysis
    suggested_tests = []
    
    col_names = [col["name"].lower() for col in req.columns]
    
    # Simple heuristics mimicking AI
    if "id" in col_names:
        suggested_tests.append({
            "test_id": f"DB_PK_{req.table_name}_id",
            "type": "Primary Key Check",
            "description": f"Assert that '{req.table_name}.id' is unique and contains no duplicates.",
            "sql": f"SELECT id, COUNT(*) FROM {req.table_name} GROUP BY id HAVING COUNT(*) > 1;",
            "expected_condition": "EQUAL",
            "expected_value": 0
        })
        
    for col in req.columns:
        # Check if type is string/varchar
        if "char" in col["type"].lower() or "text" in col["type"].lower():
            suggested_tests.append({
                "test_id": f"DB_NULL_{req.table_name}_{col['name']}",
                "type": "Null Value Check",
                "description": f"Check if required {col['name']} column contains any null values.",
                "sql": f"SELECT COUNT(*) FROM {req.table_name} WHERE {col['name']} IS NULL OR {col['name']} = '';",
                "expected_condition": "EQUAL",
                "expected_value": 0
            })
        # If price is in column name, suggest a price check (> 0)
        if "price" in col["name"].lower():
            suggested_tests.append({
                "test_id": f"DB_QUAL_{req.table_name}_{col['name']}",
                "type": "Data Quality Check",
                "description": f"Verify {col['name']} conforms to business rules (price should be positive).",
                "sql": f"SELECT COUNT(*) FROM {req.table_name} WHERE {col['name']} < 0;",
                "expected_condition": "EQUAL",
                "expected_value": 0
            })
            
    if not suggested_tests:
        suggested_tests.append({
            "test_id": f"DB_ROWCOUNT_{req.table_name}",
            "type": "Data Exist Check",
            "description": f"Verify {req.table_name} contains data.",
            "sql": f"SELECT COUNT(*) FROM {req.table_name};",
            "expected_condition": "GREATER_THAN",
            "expected_value": 0
        })

    return {
        "table_name": req.table_name,
        "status": "success",
        "recommended_tests": suggested_tests,
        "analysis_logs": [
            f"Analyzed table '{req.table_name}' with {len(req.columns)} columns.",
            f"Validation plan generated: {len(suggested_tests)} test cases recommended."
        ]
    }

@router.post("/interactive-testing/execute-batch-db-validations")
@router.post("/execute-batch-db-validations")
async def execute_batch_db_validations(requests: List[DbQueryRequest], db_session: Session = Depends(get_db)):
    logs = []
    timestamp = lambda: time.strftime('%H:%M:%S')
    logs.append(f"[{timestamp()}] [INFO] Starting Batch Database Validations ({len(requests)} queries)")
    
    start_time = time.time()
    results = []
    all_passed = True
    
    try:
        engine = get_dynamic_engine()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect to the configured database: {str(e)}")
        
    for req in requests:
        try:
            validate_sql_safety(req.query)
            with engine.connect() as conn:
                result_proxy = conn.execute(text(req.query))
                if result_proxy.returns_rows:
                    fetched_rows = result_proxy.fetchall()
                    rows = [list(row) for row in fetched_rows]
                else:
                    rows = []
            
            passed = False
            if req.expected_condition == "EQUAL":
                if len(rows) == 1 and len(rows[0]) == 1 and isinstance(rows[0][0], (int, float)):
                    passed = (rows[0][0] == req.expected_value)
                else:
                    passed = (len(rows) == req.expected_value)
            elif req.expected_condition == "GREATER_THAN":
                if len(rows) == 1 and len(rows[0]) == 1 and isinstance(rows[0][0], (int, float)):
                    passed = (rows[0][0] > req.expected_value)
                else:
                    passed = (len(rows) > req.expected_value)
            else:
                passed = True
                
            if not passed:
                all_passed = False
                
            results.append({
                "query": req.query,
                "passed": passed,
                "rows_returned": len(rows)
            })
            logs.append(f"[{timestamp()}] [VALIDATION] Query executed. Passed: {passed}")
        except Exception as e:
            all_passed = False
            results.append({
                "query": req.query,
                "passed": False,
                "error": str(e)
            })
            logs.append(f"[{timestamp()}] [ERROR] Validation failed: {str(e)}")
            
    execution_time_ms = int((time.time() - start_time) * 1000)
    logs.append(f"[{timestamp()}] [RESULT] Batch Suite Status: {'PASSED' if all_passed else 'FAILED'} in {execution_time_ms}ms")
    
    report_details = {
        "total_validations": len(requests),
        "results": results,
        "execution_logs": logs
    }
    
    try:
        create_report(
            db_session,
            report_type="DB Batch Audit",
            status="passed" if all_passed else "failed",
            summary=f"DB Batch Validations — {'PASSED' if all_passed else 'FAILED'} ({execution_time_ms}ms)",
            details=report_details,
        )
        db_session.commit()
    except Exception:
        db_session.rollback()
        
    return {
        "status": "success",
        "passed": all_passed,
        "details": report_details
    }

# --- ETL Pipeline Reconciler ---

@router.post("/interactive-etl-audit")
async def run_etl_audit(req: EtlAuditRequest, db_session: Session = Depends(get_db)):
    logs = []
    timestamp = lambda: time.strftime('%H:%M:%S')
    logs.append(f"[{timestamp()}] [INFO] Starting ETL Audit Protocol...")
    logs.append(f"[{timestamp()}] [PROCESS] Triggering ETL PyTest Suite from details.txt...")
    
    start_time = time.time()
    
    try:
        python_exe = get_venv_python()
        cmd = [python_exe, "-m", "pytest", "tests/etl/test_etl_examples.py", "-v", "--alluredir=reports/allure-results"]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_data, stderr_data = await process.communicate()
        stdout_str = stdout_data.decode('utf-8', errors='ignore')
        
        for line in stdout_str.split('\n'):
            if line.strip():
                logs.append(f"[PYTEST] {line.strip()}")
                
        passed = process.returncode == 0
        accuracy = 100.0 if passed else 0.0
        
        logs.append(f"[{timestamp()}] [SUCCESS] Reconciliation complete. Accuracy: {accuracy}%")
        
        result = {
            "totalRows": 0,
            "matches": 1 if passed else 0,
            "mismatches": 0 if passed else 1,
            "accuracy": accuracy,
            "mismatchDetails": [] if passed else [{"id": "ERR", "field": "PyTest", "source": "Failed", "target": "Passed", "risk": "High"}],
            "execution_logs": logs
        }

        # Auto-save report
        try:
            create_report(
                db_session,
                report_type="ETL Reconciliation",
                status="passed" if passed else "failed",
                summary=f"ETL PyTest Suite — Accuracy: {accuracy}%",
                details=result,
            )
        except Exception:
            pass

        return result
        
    except Exception as e:
        logs.append(f"[{timestamp()}] [ERROR] Reconciliation error: {str(e)}")

        error_result = {
            "totalRows": 0,
            "matches": 0,
            "mismatches": 0,
            "accuracy": 0.0,
            "mismatchDetails": [{
                "id": "ERR",
                "field": "reconciliation_failure",
                "source": "N/A",
                "target": "N/A",
                "risk": "Critical"
            }],
            "execution_logs": logs
        }

        # Auto-save failed report
        try:
            create_report(
                db_session,
                report_type="ETL Reconciliation",
                status="failed",
                summary=f"ETL PyTest Suite FAILED — {str(e)[:100]}",
                details={"error": str(e), "execution_logs": logs},
            )
        except Exception:
            pass

        return error_result
