"""
Pipeline Auditor — Service Layer & Strategy Validation Engine

Implements connection management, query safety, the strategy validation pattern,
dynamic suggestions, execution logic, persistence, and reporting.
"""

from __future__ import annotations

import time
import json
import re
import io
import concurrent.futures
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import requests
from fastapi import HTTPException
from fastapi.responses import Response

def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively converts numpy types to standard python primitives for JSON serialization.
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(x) for x in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(x) for x in obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif pd.isna(obj):
        return None
    else:
        return obj


from app.models.orm import PipelineAuditDB
from app.models.pipeline_auditor import (
    ConnectionType,
    ExecutionStatus,
    ValidationType,
    AggregateFunction,
    Severity,
    ExportFormat,
    ValidationDescriptor,
    ValidationResult,
    AuditSummary,
    AiInsight,
    AiInsightsPayload,
    ExecutePipelineResponse,
    TestConnectionResponse,
    ConnectionMetadata,
    AuditHistoryItem,
    AuditDetailResponse,
    mask_secrets,
)
from app.services.report_service import create_report


# ══════════════════════════════════════════════════════════════════════
# 1. Query Safety Layer
# ══════════════════════════════════════════════════════════════════════

def validate_sql_safety(query: str) -> None:
    """
    Blocks destructive DDL and DML operations, ensuring the Pipeline Auditor
    remains strictly read-only.
    """
    if not query:
        return
        
    # Strip multi-line comments: /* ... */
    clean_query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
    # Strip single-line comments: -- ...
    clean_query = re.sub(r'--.*$', '', clean_query, flags=re.MULTILINE)
    
    clean_query = clean_query.strip()
    if not clean_query:
        return

    # Check start word: Only allow queries starting with SELECT or WITH
    tokens = re.findall(r'\b\w+\b', clean_query)
    if not tokens:
        raise ValueError("Invalid SQL: Query contains no commands.")
        
    first_word = tokens[0].upper()
    if first_word not in ("SELECT", "WITH"):
        raise ValueError(f"Unsafe SQL: Query must start with SELECT or WITH (got {first_word}).")
        
    # Block destructive keywords
    blocked_keywords = {"DROP", "DELETE", "TRUNCATE", "UPDATE", "ALTER", "CREATE", "INSERT", "REPLACE", "GRANT", "REVOKE"}
    all_words = set(w.upper() for w in re.findall(r'\b\w+\b', clean_query))
    found_blocked = blocked_keywords.intersection(all_words)
    if found_blocked:
        raise ValueError(f"Unsafe SQL: Destructive statement detected: {', '.join(found_blocked)}")


# ══════════════════════════════════════════════════════════════════════
# 2. Execution Safeguards (Timeouts)
# ══════════════════════════════════════════════════════════════════════

def run_with_timeout(func, timeout: int, *args, **kwargs):
    """
    Runs a synchronous callable in a separate thread with a specified timeout limit (seconds).
    Raises TimeoutError if execution exceeds the timeout limit.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Operation timed out after {timeout} seconds.")


# ══════════════════════════════════════════════════════════════════════
# 3. Connection Engine Builder & Data Fetchers
# ══════════════════════════════════════════════════════════════════════

def build_engine_from_config(config: Dict[str, Any]):
    """
    Creates a SQLAlchemy engine dynamically from target database parameters.
    """
    db_type = config.get("db_type", "sqlite").lower()
    db_name = config.get("db_name", "etl_test.db")
    
    if db_type == "postgres":
        db_type = "postgresql"
    elif db_type in ("sqlserver", "mssql"):
        db_type = "mssql+pyodbc"
        
    if db_type == "sqlite":
        return create_engine(f"sqlite:///{db_name}")
    else:
        host = config.get("host", "localhost")
        port = config.get("port", "5432")
        username = config.get("username", "")
        password = config.get("password", "")
        
        if username:
            if password:
                url = f"{db_type}://{username}:{password}@{host}:{port}/{db_name}"
            else:
                url = f"{db_type}://{username}@{host}:{port}/{db_name}"
        else:
            url = f"{db_type}://{host}:{port}/{db_name}"
            
        return create_engine(url)


def fetch_db_data(engine, query: str, row_limit: int, chunk_size: int, query_timeout: int) -> pd.DataFrame:
    """
    Executes database query using chunks and returns a DataFrame within execution limits.
    """
    validate_sql_safety(query)
    
    def execute_and_fetch():
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = []
            keys = list(result.keys())
            count = 0
            while True:
                if count >= row_limit:
                    break
                chunk = result.fetchmany(min(chunk_size, row_limit - count))
                if not chunk:
                    break
                rows.extend(chunk)
                count += len(chunk)
            return pd.DataFrame(rows, columns=keys)
            
    return run_with_timeout(execute_and_fetch, query_timeout)


def fetch_db_count(engine, query: str, query_timeout: int) -> int:
    """
    Attempts an optimized row count by wrapping the query in a SELECT COUNT(*).
    """
    validate_sql_safety(query)
    
    def execute_count():
        # Remove trailing semicolon
        q = query.strip().rstrip(';')
        wrapped = f"SELECT COUNT(*) FROM ({q}) AS subquery_for_count"
        with engine.connect() as conn:
            res = conn.execute(text(wrapped)).scalar()
            return int(res) if res is not None else 0
            
    try:
        return run_with_timeout(execute_count, query_timeout)
    except Exception:
        # Fallback to fetching minimal dataset if count query fails
        df = fetch_db_data(engine, query, row_limit=1000, chunk_size=1000, query_timeout=query_timeout)
        return len(df)


def fetch_api_data(config: Dict[str, Any], query_path: str, row_limit: int, query_timeout: int) -> pd.DataFrame:
    """
    Makes API request to retrieve JSON records and converts them to a DataFrame.
    """
    base_url = config.get("base_url", "").rstrip('/')
    path = query_path.lstrip('/')
    url = f"{base_url}/{path}" if path else base_url
    
    method = config.get("method", "GET").upper()
    headers = config.get("headers", {}) or {}
    auth_type = config.get("auth_type", "none").lower()
    token = config.get("token", "")
    
    req_headers = {k: v for k, v in headers.items()}
    if auth_type == "bearer" and token:
        req_headers["Authorization"] = f"Bearer {token}"
    elif auth_type == "api_key" and token:
        has_key = any(k.lower() in ("x-api-key", "apikey", "api-key") for k in req_headers)
        if not has_key:
            req_headers["X-API-Key"] = token
        else:
            for k in list(req_headers.keys()):
                if k.lower() in ("x-api-key", "apikey", "api-key"):
                    req_headers[k] = token
    elif auth_type == "basic" and token:
        req_headers["Authorization"] = f"Basic {token}"
        
    def execute_request():
        res = requests.request(method, url, headers=req_headers, timeout=query_timeout)
        res.raise_for_status()
        data = res.json()
        
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            for val in data.values():
                if isinstance(val, list):
                    records = val
                    break
            else:
                records = [data]
        else:
            raise ValueError(f"Unexpected API response type: {type(data)}")
            
        if len(records) > row_limit:
            records = records[:row_limit]
            
        return pd.DataFrame(records)
        
    return run_with_timeout(execute_request, query_timeout)


# ══════════════════════════════════════════════════════════════════════
# 4. Strategy Pattern Validation Engine
# ══════════════════════════════════════════════════════════════════════

class BaseValidationStrategy(ABC):
    """
    Abstract Base Class for all reconciliation validation strategies.
    Contains shared data retrieval utilities.
    """
    def __init__(self, descriptor: ValidationDescriptor):
        self.descriptor = descriptor
        
    @property
    def name(self) -> str:
        return self.descriptor.name
        
    @property
    def type(self) -> ValidationType:
        return self.descriptor.type

    @abstractmethod
    def execute(
        self,
        source_engine,
        target_engine,
        source_type: ConnectionType,
        target_type: ConnectionType,
        source_config: Dict[str, Any],
        target_config: Dict[str, Any],
        source_query: str,
        target_query: str,
        key_columns: List[str],
        row_limit: int,
        chunk_size: int,
        query_timeout: int,
    ) -> ValidationResult:
        pass

    def _get_source_query(self, global_query: str) -> str:
        return self.descriptor.source_sql if self.descriptor.source_sql else global_query

    def _get_target_query(self, global_query: str) -> str:
        return self.descriptor.target_sql if self.descriptor.target_sql else global_query

    def _fetch_source_df(self, source_engine, source_type, source_config, source_query, row_limit, chunk_size, query_timeout) -> pd.DataFrame:
        query = self._get_source_query(source_query)
        if source_type == ConnectionType.database:
            return fetch_db_data(source_engine, query, row_limit, chunk_size, query_timeout)
        else:
            return fetch_api_data(source_config, query, row_limit, query_timeout)

    def _fetch_target_df(self, target_engine, target_type, target_config, target_query, row_limit, chunk_size, query_timeout) -> pd.DataFrame:
        query = self._get_target_query(target_query)
        if target_type == ConnectionType.database:
            return fetch_db_data(target_engine, query, row_limit, chunk_size, query_timeout)
        else:
            return fetch_api_data(target_config, query, row_limit, query_timeout)


class RowCountStrategy(BaseValidationStrategy):
    """Compares absolute row counts between source and target systems."""
    def execute(self, source_engine, target_engine, source_type, target_type, source_config, target_config, source_query, target_query, key_columns, row_limit, chunk_size, query_timeout) -> ValidationResult:
        start_time = time.time()
        try:
            src_q = self._get_source_query(source_query)
            tgt_q = self._get_target_query(target_query)
            
            # Optimized database count
            if source_type == ConnectionType.database:
                src_count = fetch_db_count(source_engine, src_q, query_timeout)
            else:
                src_count = len(self._fetch_source_df(source_engine, source_type, source_config, src_q, row_limit, chunk_size, query_timeout))
                
            if target_type == ConnectionType.database:
                tgt_count = fetch_db_count(target_engine, tgt_q, query_timeout)
            else:
                tgt_count = len(self._fetch_target_df(target_engine, target_type, target_config, tgt_q, row_limit, chunk_size, query_timeout))
                
            status = "passed" if src_count == tgt_count else "failed"
            records_failed = abs(src_count - tgt_count)
            
            mismatch_details = None
            if src_count != tgt_count:
                mismatch_details = [{"message": f"Row count mismatch. Source: {src_count}, Target: {tgt_count}"}]
                
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status=status,
                records_checked=src_count,
                records_failed=records_failed,
                source_value=src_count,
                target_value=tgt_count,
                mismatch_details=mismatch_details,
                duration_ms=int((time.time() - start_time) * 1000)
            )
        except TimeoutError:
            raise
        except Exception as e:
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status="error",
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )


class ExactMatchStrategy(BaseValidationStrategy):
    """Performs cell-by-cell equality reconciliation on rows sharing keys."""
    def execute(self, source_engine, target_engine, source_type, target_type, source_config, target_config, source_query, target_query, key_columns, row_limit, chunk_size, query_timeout) -> ValidationResult:
        start_time = time.time()
        try:
            if not key_columns:
                raise ValueError("Exact Match Validation requires key_columns.")
                
            src_df = self._fetch_source_df(source_engine, source_type, source_config, source_query, row_limit, chunk_size, query_timeout)
            tgt_df = self._fetch_target_df(target_engine, target_type, target_config, target_query, row_limit, chunk_size, query_timeout)
            
            # Verify columns exist
            for k in key_columns:
                if k not in src_df.columns:
                    raise ValueError(f"Key column '{k}' not found in source dataset.")
                if k not in tgt_df.columns:
                    raise ValueError(f"Key column '{k}' not found in target dataset.")
                    
            # Drop key duplicates to prevent join blowup
            src_df = src_df.drop_duplicates(subset=key_columns)
            tgt_df = tgt_df.drop_duplicates(subset=key_columns)
            
            # Align on indexes
            src_df = src_df.set_index(key_columns)
            tgt_df = tgt_df.set_index(key_columns)
            common_idx = src_df.index.intersection(tgt_df.index)
            common_cols = [c for c in src_df.columns if c in tgt_df.columns]
            
            records_checked = len(common_idx)
            records_failed = 0
            mismatches = []
            
            if records_checked > 0:
                src_align = src_df.loc[common_idx, common_cols]
                tgt_align = tgt_df.loc[common_idx, common_cols]
                
                # Check element equality including NaN
                eq_mask = (src_align == tgt_align) | (src_align.isna() & tgt_align.isna())
                row_eq = eq_mask.all(axis=1)
                failed_idx = common_idx[~row_eq]
                records_failed = len(failed_idx)
                
                for idx in failed_idx[:100]:  # Limit details to top 100 rows
                    key_val = dict(zip(key_columns, idx)) if len(key_columns) > 1 else {key_columns[0]: idx}
                    diffs = {}
                    for col in common_cols:
                        v_src = src_align.loc[idx, col]
                        v_tgt = tgt_align.loc[idx, col]
                        is_eq = (v_src == v_tgt) or (pd.isna(v_src) and pd.isna(v_tgt))
                        if not is_eq:
                            diffs[col] = {
                                "source": None if pd.isna(v_src) else v_src,
                                "target": None if pd.isna(v_tgt) else v_tgt
                            }
                    mismatches.append({"key": key_val, "mismatched_columns": diffs})
                    
            status = "passed" if records_failed == 0 else "failed"
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status=status,
                records_checked=records_checked,
                records_failed=records_failed,
                source_value=records_checked - records_failed,
                target_value=records_checked,
                mismatch_details=mismatches if mismatches else None,
                duration_ms=int((time.time() - start_time) * 1000)
            )
        except TimeoutError:
            raise
        except Exception as e:
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status="error",
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )


class NullCheckStrategy(BaseValidationStrategy):
    """Verifies that designated columns in the target system do not contain unexpected NULL values."""
    def execute(self, source_engine, target_engine, source_type, target_type, source_config, target_config, source_query, target_query, key_columns, row_limit, chunk_size, query_timeout) -> ValidationResult:
        start_time = time.time()
        try:
            col_name = self.descriptor.column_name
            if not col_name:
                raise ValueError("Null Check Validation requires column_name.")
                
            tgt_df = self._fetch_target_df(target_engine, target_type, target_config, target_query, row_limit, chunk_size, query_timeout)
            
            if col_name not in tgt_df.columns:
                raise ValueError(f"Column '{col_name}' not found in target dataset.")
                
            records_checked = len(tgt_df)
            null_mask = tgt_df[col_name].isna()
            records_failed = int(null_mask.sum())
            
            mismatches = []
            if records_failed > 0:
                failed_rows = tgt_df[null_mask]
                for idx, row in failed_rows.head(100).iterrows():
                    key_val = {k: row[k] if k in tgt_df.columns else idx for k in key_columns} if key_columns else {"index": idx}
                    mismatches.append({"key": key_val, "column": col_name, "value": None})
                    
            status = "passed" if records_failed == 0 else "failed"
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status=status,
                records_checked=records_checked,
                records_failed=records_failed,
                source_value=records_checked - records_failed,
                target_value=records_failed,
                mismatch_details=mismatches if mismatches else None,
                duration_ms=int((time.time() - start_time) * 1000)
            )
        except TimeoutError:
            raise
        except Exception as e:
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status="error",
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )


class DuplicateCheckStrategy(BaseValidationStrategy):
    """Verifies uniqueness of keys or identifiers in the target system."""
    def execute(self, source_engine, target_engine, source_type, target_type, source_config, target_config, source_query, target_query, key_columns, row_limit, chunk_size, query_timeout) -> ValidationResult:
        start_time = time.time()
        try:
            cols = [self.descriptor.column_name] if self.descriptor.column_name else key_columns
            if not cols:
                raise ValueError("Duplicate Check Validation requires column_name or key_columns.")
                
            tgt_df = self._fetch_target_df(target_engine, target_type, target_config, target_query, row_limit, chunk_size, query_timeout)
            
            for col in cols:
                if col not in tgt_df.columns:
                    raise ValueError(f"Column '{col}' not found in target dataset.")
                    
            records_checked = len(tgt_df)
            counts = tgt_df.groupby(cols).size().reset_index(name="count")
            dups = counts[counts["count"] > 1]
            records_failed = int((dups["count"] - 1).sum())
            
            mismatches = []
            if len(dups) > 0:
                for _, row in dups.head(100).iterrows():
                    key_val = {col: row[col] for col in cols}
                    mismatches.append({"key": key_val, "occurrences": int(row["count"])})
                    
            status = "passed" if records_failed == 0 else "failed"
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status=status,
                records_checked=records_checked,
                records_failed=records_failed,
                source_value=records_checked - records_failed,
                target_value=records_failed,
                mismatch_details=mismatches if mismatches else None,
                duration_ms=int((time.time() - start_time) * 1000)
            )
        except TimeoutError:
            raise
        except Exception as e:
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status="error",
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )


class SchemaValidationStrategy(BaseValidationStrategy):
    """Compares structures, column names, and type mapping compatibility."""
    def execute(self, source_engine, target_engine, source_type, target_type, source_config, target_config, source_query, target_query, key_columns, row_limit, chunk_size, query_timeout) -> ValidationResult:
        start_time = time.time()
        try:
            # Sample 1 row to fetch schema structure quickly
            src_df = self._fetch_source_df(source_engine, source_type, source_config, source_query, row_limit=1, chunk_size=1, query_timeout=query_timeout)
            tgt_df = self._fetch_target_df(target_engine, target_type, target_config, target_query, row_limit=1, chunk_size=1, query_timeout=query_timeout)
            
            src_schema = {col: str(dtype) for col, dtype in src_df.dtypes.items()}
            tgt_schema = {col: str(dtype) for col, dtype in tgt_df.dtypes.items()}
            
            mismatches = []
            records_checked = len(src_schema)
            records_failed = 0
            
            # Missing columns
            for col, dtype in src_schema.items():
                if col not in tgt_schema:
                    mismatches.append({
                        "issue": "Missing Column",
                        "column": col,
                        "source_type": dtype,
                        "target_type": None,
                        "description": f"Column '{col}' is present in source but missing in target."
                    })
                    records_failed += 1
                else:
                    t_src = dtype.lower()
                    t_tgt = tgt_schema[col].lower()
                    
                    def normalize_type(t):
                        if "int" in t: return "integer"
                        if "float" in t or "double" in t or "decimal" in t: return "numeric"
                        if "str" in t or "object" in t or "char" in t or "text" in t: return "string"
                        if "bool" in t: return "boolean"
                        if "date" in t or "time" in t: return "datetime"
                        return t
                        
                    if normalize_type(t_src) != normalize_type(t_tgt):
                        mismatches.append({
                            "issue": "Type Mismatch",
                            "column": col,
                            "source_type": dtype,
                            "target_type": tgt_schema[col],
                            "description": f"Column '{col}' type mismatch. Source is {dtype}, Target is {tgt_schema[col]}."
                        })
                        records_failed += 1
                        
            # Extra columns
            for col, dtype in tgt_schema.items():
                if col not in src_schema:
                    mismatches.append({
                        "issue": "Extra Column",
                        "column": col,
                        "source_type": None,
                        "target_type": dtype,
                        "description": f"Column '{col}' exists in target but not in source."
                    })
                    records_failed += 1
                    
            status = "passed" if records_failed == 0 else "failed"
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status=status,
                records_checked=records_checked,
                records_failed=records_failed,
                source_value=len(src_schema),
                target_value=len(tgt_schema),
                mismatch_details=mismatches if mismatches else None,
                duration_ms=int((time.time() - start_time) * 1000)
            )
        except TimeoutError:
            raise
        except Exception as e:
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status="error",
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )


class AggregateValidationStrategy(BaseValidationStrategy):
    """Validates aggregate mathematical operations across matching columns."""
    def execute(self, source_engine, target_engine, source_type, target_type, source_config, target_config, source_query, target_query, key_columns, row_limit, chunk_size, query_timeout) -> ValidationResult:
        start_time = time.time()
        try:
            agg_col = self.descriptor.aggregate_column
            agg_fn = self.descriptor.aggregate_function
            if not agg_col or not agg_fn:
                raise ValueError("Aggregate Validation requires aggregate_column and aggregate_function.")
                
            agg_fn = agg_fn.upper()
            
            src_df = self._fetch_source_df(source_engine, source_type, source_config, source_query, row_limit, chunk_size, query_timeout)
            tgt_df = self._fetch_target_df(target_engine, target_type, target_config, target_query, row_limit, chunk_size, query_timeout)
            
            if agg_col not in src_df.columns:
                raise ValueError(f"Column '{agg_col}' not found in source dataset.")
            if agg_col not in tgt_df.columns:
                raise ValueError(f"Column '{agg_col}' not found in target dataset.")
                
            def compute_agg(df, col, fn):
                series = df[col]
                if fn in ("SUM", "AVG", "MIN", "MAX"):
                    series = pd.to_numeric(series, errors='coerce')
                
                if fn == "SUM":
                    return float(series.sum())
                elif fn == "COUNT":
                    return int(series.count())
                elif fn == "AVG":
                    return float(series.mean()) if not series.empty else 0.0
                elif fn == "MIN":
                    val = series.min()
                    return float(val) if pd.notna(val) else None
                elif fn == "MAX":
                    val = series.max()
                    return float(val) if pd.notna(val) else None
                else:
                    raise ValueError(f"Unsupported aggregate function: {fn}")
                    
            src_val = compute_agg(src_df, agg_col, agg_fn)
            tgt_val = compute_agg(tgt_df, agg_col, agg_fn)
            
            is_eq = False
            if src_val is None and tgt_val is None:
                is_eq = True
            elif src_val is not None and tgt_val is not None:
                if isinstance(src_val, float) or isinstance(tgt_val, float):
                    is_eq = abs(float(src_val) - float(tgt_val)) < 1e-5
                else:
                    is_eq = src_val == tgt_val
                    
            status = "passed" if is_eq else "failed"
            records_failed = 0 if is_eq else 1
            
            mismatch_details = None
            if not is_eq:
                mismatch_details = [{"message": f"Aggregate mismatch for {agg_fn}({agg_col}): Source={src_val}, Target={tgt_val}"}]
                
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status=status,
                records_checked=1,
                records_failed=records_failed,
                source_value=src_val,
                target_value=tgt_val,
                mismatch_details=mismatch_details,
                duration_ms=int((time.time() - start_time) * 1000)
            )
        except TimeoutError:
            raise
        except Exception as e:
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status="error",
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )


class MissingRecordsStrategy(BaseValidationStrategy):
    """Detects primary key combinations present in source but missing in target."""
    def execute(self, source_engine, target_engine, source_type, target_type, source_config, target_config, source_query, target_query, key_columns, row_limit, chunk_size, query_timeout) -> ValidationResult:
        start_time = time.time()
        try:
            if not key_columns:
                raise ValueError("Missing Records Validation requires key_columns.")
                
            src_df = self._fetch_source_df(source_engine, source_type, source_config, source_query, row_limit, chunk_size, query_timeout)
            tgt_df = self._fetch_target_df(target_engine, target_type, target_config, target_query, row_limit, chunk_size, query_timeout)
            
            for k in key_columns:
                if k not in src_df.columns:
                    raise ValueError(f"Key column '{k}' not found in source dataset.")
                if k not in tgt_df.columns:
                    raise ValueError(f"Key column '{k}' not found in target dataset.")
                    
            if len(key_columns) > 1:
                src_keys = set(tuple(x) for x in src_df[key_columns].values)
                tgt_keys = set(tuple(x) for x in tgt_df[key_columns].values)
            else:
                src_keys = set(src_df[key_columns[0]].values)
                tgt_keys = set(tgt_df[key_columns[0]].values)
                
            missing_keys = src_keys - tgt_keys
            records_checked = len(src_keys)
            records_failed = len(missing_keys)
            
            mismatches = []
            if records_failed > 0:
                for k in list(missing_keys)[:100]:
                    if len(key_columns) > 1:
                        mismatches.append(dict(zip(key_columns, k)))
                    else:
                        mismatches.append({key_columns[0]: k})
                        
            status = "passed" if records_failed == 0 else "failed"
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status=status,
                records_checked=records_checked,
                records_failed=records_failed,
                source_value=records_checked - records_failed,
                target_value=records_failed,
                mismatch_details=mismatches if mismatches else None,
                duration_ms=int((time.time() - start_time) * 1000)
            )
        except TimeoutError:
            raise
        except Exception as e:
            return ValidationResult(
                id=self.descriptor.id,
                name=self.descriptor.name,
                type=self.descriptor.type,
                severity=self.descriptor.severity,
                status="error",
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )


# ══════════════════════════════════════════════════════════════════════
# 5. Strategy Registry
# ══════════════════════════════════════════════════════════════════════

STRATEGY_REGISTRY: Dict[ValidationType, Type[BaseValidationStrategy]] = {
    ValidationType.row_count: RowCountStrategy,
    ValidationType.exact_match: ExactMatchStrategy,
    ValidationType.null_check: NullCheckStrategy,
    ValidationType.duplicate_check: DuplicateCheckStrategy,
    ValidationType.schema_validation: SchemaValidationStrategy,
    ValidationType.aggregate: AggregateValidationStrategy,
    ValidationType.missing_records: MissingRecordsStrategy,
}


# ══════════════════════════════════════════════════════════════════════
# 6. Connection Testing & Metadata Service
# ══════════════════════════════════════════════════════════════════════

def test_connection_service(type: ConnectionType, config: Dict[str, Any], query_timeout: int = 10) -> TestConnectionResponse:
    """
    Attempts to establish connection to source/target DB or API and extracts schema metadata.
    Raises ValueError on invalid credentials / parameters, ConnectionError on database/service unreachable.
    """
    start_time = time.time()
    
    if type == ConnectionType.database:
        db_type = config.get("db_type", "sqlite").lower()
        db_name = config.get("db_name", "")
        if not db_name:
            raise ValueError("Database name is required.")
        if db_type != "sqlite":
            if not config.get("host"):
                raise ValueError("Host parameter is required for non-sqlite databases.")
            if not config.get("port"):
                raise ValueError("Port parameter is required for non-sqlite databases.")
            
        try:
            engine = build_engine_from_config(config)
            
            def connect_and_ping():
                with engine.connect() as conn:
                    if db_type == "oracle":
                        conn.execute(text("SELECT 1 FROM DUAL"))
                    else:
                        conn.execute(text("SELECT 1"))
                        
            run_with_timeout(connect_and_ping, query_timeout)
        except Exception as e:
            err_msg = str(e)
            if "unable to open database file" in err_msg or "Connection refused" in err_msg or "Is the server running" in err_msg or "OperationalError" in err_msg or "Can't connect to" in err_msg:
                raise ConnectionError(f"Database unavailable: {err_msg}")
            elif "Access denied" in err_msg or "authentication failed" in err_msg or "password" in err_msg or "username" in err_msg or "invalid" in err_msg.lower():
                raise ValueError(f"Invalid connection parameters: {err_msg}")
            else:
                raise RuntimeError(f"Unexpected connection failure: {err_msg}")
            
        tables = []
        row_counts = {}
        columns = {}
        
        def extract_metadata():
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tbls = inspector.get_table_names()
            tables.extend(tbls[:10])  # limit metadata count for fast response
            for tbl in tables:
                cols = inspector.get_columns(tbl)
                columns[tbl] = [{"name": c["name"], "type": str(c["type"])} for c in cols]
                try:
                    with engine.connect() as conn:
                        res = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
                        row_counts[tbl] = int(res) if res is not None else 0
                except Exception:
                    row_counts[tbl] = 0
                    
        try:
            run_with_timeout(extract_metadata, 5)
        except Exception:
            pass
            
        latency = int((time.time() - start_time) * 1000)
        db_name = config.get("db_name", "etl_test.db")
        db_type = config.get("db_type", "sqlite")
        return TestConnectionResponse(
            status="success",
            message=f"Connected to {db_name} ({db_type.upper()}) — {len(tables)} tables found",
            latency_ms=latency,
            metadata=ConnectionMetadata(
                tables=tables,
                row_counts=row_counts,
                columns=columns
            )
        )
        
    elif type == ConnectionType.api:
        base_url = config.get("base_url", "").rstrip('/')
        if not base_url:
            raise ValueError("Base URL is required.")
            
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {}) or {}
        auth_type = config.get("auth_type", "none").lower()
        token = config.get("token", "")
        
        req_headers = {k: v for k, v in headers.items()}
        if auth_type == "bearer" and token:
            req_headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "api_key" and token:
            has_key = any(k.lower() in ("x-api-key", "apikey", "api-key") for k in req_headers)
            if not has_key:
                req_headers["X-API-Key"] = token
            else:
                for k in list(req_headers.keys()):
                    if k.lower() in ("x-api-key", "apikey", "api-key"):
                        req_headers[k] = token
        elif auth_type == "basic" and token:
            req_headers["Authorization"] = f"Basic {token}"
            
        def ping_api():
            res = requests.request(method, base_url, headers=req_headers, timeout=query_timeout)
            res.raise_for_status()
            return res
            
        try:
            res = run_with_timeout(ping_api, query_timeout)
        except Exception as e:
            err_msg = str(e)
            if "Connection refused" in err_msg or "Max retries exceeded" in err_msg or "Name or service not known" in err_msg or "Timeout" in err_msg:
                raise ConnectionError(f"API unavailable: {err_msg}")
            elif "401" in err_msg or "403" in err_msg or "Unauthorized" in err_msg or "Forbidden" in err_msg:
                raise ValueError(f"Invalid API credentials / parameters: {err_msg}")
            else:
                raise RuntimeError(f"Unexpected API connection failure: {err_msg}")
                
        latency = int((time.time() - start_time) * 1000)
        
        tables = []
        row_counts = {}
        columns = {}
        
        try:
            data = res.json()
            if isinstance(data, list):
                row_counts["response"] = len(data)
                if len(data) > 0 and isinstance(data[0], dict):
                    columns["response"] = [{"name": k, "type": type(v).__name__} for k, v in data[0].items()]
            elif isinstance(data, dict):
                for k, val in data.items():
                    if isinstance(val, list):
                        row_counts[k] = len(val)
                        if len(val) > 0 and isinstance(val[0], dict):
                            columns[k] = [{"name": c_k, "type": type(c_v).__name__} for c_k, c_v in val[0].items()]
                            break
                else:
                    row_counts["response"] = 1
                    columns["response"] = [{"name": k, "type": type(v).__name__} for k, v in data.items()]
        except Exception:
            pass
            
        return TestConnectionResponse(
            status="success",
            message=f"Connected to API base URL (HTTP {res.status_code})",
            latency_ms=latency,
            metadata=ConnectionMetadata(
                tables=list(columns.keys()),
                row_counts=row_counts,
                columns=columns
            )
        )
    else:
        raise ValueError(f"Unsupported connection type: {type}")


# ══════════════════════════════════════════════════════════════════════
# 7. Pipeline Schema Analysis Logic
# ══════════════════════════════════════════════════════════════════════

def analyze_pipeline_service(
    source_type: ConnectionType,
    source_config: Dict[str, Any],
    target_type: ConnectionType,
    target_config: Dict[str, Any],
    source_query: str,
    target_query: str,
    key_columns: List[str],
    query_timeout: int = 10,
) -> Dict[str, Any]:
    """
    Analyzes dataset schemas dynamically by fetching limited datasets,
    mapping data types, and returning dynamic reconciliation check recommendations.
    """
    analysis_logs = []
    
    # Run safety checks on queries
    if source_type == ConnectionType.database:
        validate_sql_safety(source_query)
    if target_type == ConnectionType.database:
        validate_sql_safety(target_query)
        
    analysis_logs.append("Query safety validation checks completed.")
    
    # 1. Fetch source sample
    analysis_logs.append(f"Connecting to source system ({source_type})...")
    src_engine = None
    if source_type == ConnectionType.database:
        src_engine = build_engine_from_config(source_config)
        src_df = fetch_db_data(src_engine, source_query, row_limit=10, chunk_size=10, query_timeout=query_timeout)
    else:
        src_df = fetch_api_data(source_config, source_query, row_limit=10, query_timeout=query_timeout)
    analysis_logs.append(f"Fetched source schema. Columns found: {len(src_df.columns)}")
    
    # 2. Fetch target sample
    analysis_logs.append(f"Connecting to target system ({target_type})...")
    tgt_engine = None
    if target_type == ConnectionType.database:
        tgt_engine = build_engine_from_config(target_config)
        tgt_df = fetch_db_data(tgt_engine, target_query, row_limit=10, chunk_size=10, query_timeout=query_timeout)
    else:
        tgt_df = fetch_api_data(target_config, target_query, row_limit=10, query_timeout=query_timeout)
    analysis_logs.append(f"Fetched target schema. Columns found: {len(tgt_df.columns)}")
    
    source_columns = [{"name": col, "type": str(dtype)} for col, dtype in src_df.dtypes.items()]
    target_columns = [{"name": col, "type": str(dtype)} for col, dtype in tgt_df.dtypes.items()]
    
    # 3. Generate dynamic checks
    src_cols_set = set(src_df.columns)
    tgt_cols_set = set(tgt_df.columns)
    common_cols = src_cols_set.intersection(tgt_cols_set)
    
    suggestions = []
    
    # Row Count Validation
    suggestions.append(ValidationDescriptor(
        id="RC_001",
        name="Row Count Validation",
        type=ValidationType.row_count,
        description="Verify source and target contain identical row counts.",
        severity=Severity.critical,
        enabled=True
    ))
    
    # Schema Validation
    suggestions.append(ValidationDescriptor(
        id="SV_001",
        name="Schema Validation",
        type=ValidationType.schema_validation,
        description="Verify source and target have matching column names and compatible types.",
        severity=Severity.high,
        enabled=True
    ))
    
    # Exact Match & Missing Records (only if key columns are present)
    if key_columns:
        suggestions.append(ValidationDescriptor(
            id="EM_001",
            name=f"Exact Match on {', '.join(key_columns)}",
            type=ValidationType.exact_match,
            description=f"Row-by-row data comparison matching on key columns: {', '.join(key_columns)}",
            severity=Severity.critical,
            enabled=True
        ))
        
        suggestions.append(ValidationDescriptor(
            id="MR_001",
            name="Missing Records Detection",
            type=ValidationType.missing_records,
            description="Find records present in source but missing in target based on key columns.",
            severity=Severity.critical,
            enabled=True
        ))
        
        for k in key_columns:
            suggestions.append(ValidationDescriptor(
                id=f"DC_{k}",
                name=f"Duplicate Check: {k}",
                type=ValidationType.duplicate_check,
                description=f"Verify no duplicate keys exist in target for '{k}'.",
                severity=Severity.critical,
                column_name=k,
                enabled=True
            ))
            
    # Null Checks for first 2 non-key columns
    non_key_cols = [c for c in common_cols if c not in key_columns]
    for col in non_key_cols[:2]:
        suggestions.append(ValidationDescriptor(
            id=f"NC_{col}",
            name=f"Null Check: {col}",
            type=ValidationType.null_check,
            description=f"Verify target column '{col}' does not contain NULLs.",
            severity=Severity.high,
            column_name=col,
            enabled=False
        ))
        
    # Aggregate Suggestion for numeric fields
    def is_numeric_type(t: str) -> bool:
        t_lower = t.lower()
        return any(x in t_lower for x in ("int", "float", "double", "decimal", "numeric", "real"))
        
    src_types = {col: str(dtype) for col, dtype in src_df.dtypes.items()}
    numeric_cols = [c for c in common_cols if is_numeric_type(src_types[c])]
    for col in numeric_cols[:2]:
        suggestions.append(ValidationDescriptor(
            id=f"AG_{col}_SUM",
            name=f"Aggregate: SUM({col})",
            type=ValidationType.aggregate,
            description=f"Compare sum of column '{col}' between source and target.",
            severity=Severity.medium,
            aggregate_function=AggregateFunction.SUM,
            aggregate_column=col,
            enabled=False
        ))
        
    analysis_logs.append(f"Generated {len(suggestions)} validation recommendations based on data inspection.")
    
    return {
        "status": "success",
        "suggestions": suggestions,
        "source_columns": source_columns,
        "target_columns": target_columns,
        "analysis_logs": analysis_logs
    }


# ══════════════════════════════════════════════════════════════════════
# 8. AI Insights Engine
# ══════════════════════════════════════════════════════════════════════

def generate_ai_insights_service(results: List[ValidationResult]) -> AiInsightsPayload:
    """
    Analyzes execution results dynamically to offer failure diagnosis and fix instructions.
    """
    failures = []
    failed_checks_count = sum(1 for r in results if r.status in ("failed", "error"))
    
    if failed_checks_count == 0:
        return AiInsightsPayload(
            summary="All validation checks passed successfully. Source and target datasets are reconciled.",
            failures=[]
        )
        
    summary = f"{failed_checks_count} validation checks failed or errored during pipeline execution."
    
    for r in results:
        if r.status in ("failed", "error"):
            cause = ""
            recommendation = ""
            
            if r.type == "row_count":
                diff = abs(int(r.source_value or 0) - int(r.target_value or 0))
                cause = f"Row count mismatch. Source has {r.source_value} rows while Target has {r.target_value} rows (difference of {diff} rows)."
                recommendation = "Verify transformation logic or filters that may have dropped records. Check source queries against target database."
            elif r.type == "exact_match":
                cause = f"Row-by-row cell mismatch detected on key columns for {r.records_failed} record(s)."
                recommendation = "Inspect mismatch_details array. Check field-mapping, character trimming, or float precision rounding."
            elif r.type == "null_check":
                cause = f"Target column '{r.id.split('_')[-1]}' contains {r.target_value} NULL values."
                recommendation = "Verify source field nullability, missing mappings, or database constraints in destination database."
            elif r.type == "duplicate_check":
                cause = f"Duplicate key values found in target dataset for check '{r.name}'."
                recommendation = "Check for missing distinct clauses or index boundaries. Ensure primary keys are enforced in target database."
            elif r.type == "schema_validation":
                cause = f"Schema mismatch detected: {r.records_failed} column schema differences exist."
                recommendation = "Run migration scripts or update DDL script to align schemas."
            elif r.type == "aggregate":
                cause = f"Aggregate value mismatch for '{r.name}': Source = {r.source_value}, Target = {r.target_value}."
                recommendation = "Check arithmetic rounding differences or delta rows excluded from computations."
            elif r.type == "missing_records":
                cause = f"Target database is missing {r.records_failed} key(s) that exist in the source."
                recommendation = "Run delta ingestion step to reload missing records. Check if ETL skipped them."
            else:
                cause = r.error_message or "Execution failed with an error."
                recommendation = "Check connection settings, queries, and schema configurations."
                
            failures.append(AiInsight(
                name=r.name,
                cause=cause,
                recommendation=recommendation
            ))
            
    return AiInsightsPayload(summary=summary, failures=failures)


# ══════════════════════════════════════════════════════════════════════
# 9. Audit Execution Orchestrator
# ══════════════════════════════════════════════════════════════════════

def execute_pipeline_audit_service(
    db: Session,
    pipeline_name: str,
    environment: Optional[str],
    pipeline_type: Optional[str],
    source_type: ConnectionType,
    source_config: Dict[str, Any],
    target_type: ConnectionType,
    target_config: Dict[str, Any],
    source_query: str,
    target_query: str,
    key_columns: List[str],
    validations: List[ValidationDescriptor],
    row_limit: int,
    chunk_size: int,
    query_timeout: int = 30,
    execution_timeout: int = 300,
) -> ExecutePipelineResponse:
    """
    Orchestrates the entire pipeline validation suite, tracking execution times,
    saving results to both history (PipelineAuditDB) and master reporting (ReportDB).
    """
    start_time_epoch = time.time()
    started_at_str = datetime.now(timezone.utc).isoformat()
    logs = []
    
    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [INFO] Starting Pipeline Audit: {pipeline_name}")
    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [INFO] Environment: {environment} | Type: {pipeline_type}")
    
    # Safety checks
    try:
        if source_type == ConnectionType.database:
            validate_sql_safety(source_query)
        if target_type == ConnectionType.database:
            validate_sql_safety(target_query)
        for v in validations:
            if v.source_sql:
                validate_sql_safety(v.source_sql)
            if v.target_sql:
                validate_sql_safety(v.target_sql)
    except ValueError as e:
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [ERROR] SQL Safety Validation failed: {str(e)}")
        completed_at_str = datetime.now(timezone.utc).isoformat()
        
        # Save failed run
        audit_record = PipelineAuditDB(
            pipeline_name=pipeline_name,
            environment=environment,
            pipeline_type=pipeline_type,
            source_type=source_type.value if hasattr(source_type, "value") else source_type,
            source_config=json.dumps(mask_secrets(source_config)),
            source_query=source_query,
            target_type=target_type.value if hasattr(target_type, "value") else target_type,
            target_config=json.dumps(mask_secrets(target_config)),
            target_query=target_query,
            matching_keys=json.dumps(key_columns),
            selected_validations=json.dumps([v.model_dump() for v in validations]),
            execution_status=ExecutionStatus.FAILED.value,
            execution_duration=0,
            total_checks=len(validations),
            passed_checks=0,
            failed_checks=len(validations),
            accuracy_percentage=0.0,
            ai_insights=json.dumps({"summary": "SQL safety violation blocked execution.", "failures": []}),
            results=json.dumps([]),
            execution_logs=json.dumps(logs),
            created_at=started_at_str,
            started_at=started_at_str,
            completed_at=completed_at_str
        )
        db.add(audit_record)
        db.commit()
        db.refresh(audit_record)
        
        # Dual persist to reports table
        create_report(
            db=db,
            report_type="ETL Reconciliation",
            status="failed",
            summary=f"SQL safety violation blocked execution for pipeline: {pipeline_name}",
            details={"audit_id": audit_record.id, "logs": logs}
        )
        
        return ExecutePipelineResponse(
            status="error",
            audit_id=audit_record.id,
            execution_status=ExecutionStatus.FAILED,
            summary=AuditSummary(total_checks=len(validations), passed_checks=0, failed_checks=len(validations), accuracy="0.0", duration_ms=0),
            results=[],
            ai_insights=AiInsightsPayload(summary="SQL safety violation blocked execution.", failures=[]),
            execution_logs=logs
        )

    # Database engines Setup
    source_engine = None
    target_engine = None
    try:
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [PROCESS] Connecting to systems...")
        if source_type == ConnectionType.database:
            source_engine = build_engine_from_config(source_config)
        if target_type == ConnectionType.database:
            target_engine = build_engine_from_config(target_config)
    except Exception as e:
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [ERROR] Database engine construction failed: {str(e)}")
        completed_at_str = datetime.now(timezone.utc).isoformat()
        
        audit_record = PipelineAuditDB(
            pipeline_name=pipeline_name,
            environment=environment,
            pipeline_type=pipeline_type,
            source_type=source_type.value if hasattr(source_type, "value") else source_type,
            source_config=json.dumps(mask_secrets(source_config)),
            source_query=source_query,
            target_type=target_type.value if hasattr(target_type, "value") else target_type,
            target_config=json.dumps(mask_secrets(target_config)),
            target_query=target_query,
            matching_keys=json.dumps(key_columns),
            selected_validations=json.dumps([v.model_dump() for v in validations]),
            execution_status=ExecutionStatus.FAILED.value,
            execution_duration=0,
            total_checks=len(validations),
            passed_checks=0,
            failed_checks=len(validations),
            accuracy_percentage=0.0,
            ai_insights=json.dumps({"summary": f"Failed to initialize engines: {str(e)}", "failures": []}),
            results=json.dumps([]),
            execution_logs=json.dumps(logs),
            created_at=started_at_str,
            started_at=started_at_str,
            completed_at=completed_at_str
        )
        db.add(audit_record)
        db.commit()
        db.refresh(audit_record)
        
        create_report(
            db=db,
            report_type="ETL Reconciliation",
            status="failed",
            summary=f"Failed to connect to source/target for pipeline: {pipeline_name}",
            details={"audit_id": audit_record.id, "logs": logs}
        )
        
        return ExecutePipelineResponse(
            status="error",
            audit_id=audit_record.id,
            execution_status=ExecutionStatus.FAILED,
            summary=AuditSummary(total_checks=len(validations), passed_checks=0, failed_checks=len(validations), accuracy="0.0", duration_ms=0),
            results=[],
            ai_insights=AiInsightsPayload(summary=f"Engine initialization error: {str(e)}", failures=[]),
            execution_logs=logs
        )

    results = []
    
    # Validation Loop
    for v in validations:
        # Check overall execution timeout
        elapsed = time.time() - start_time_epoch
        if elapsed > execution_timeout:
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [ERROR] Execution timeout reached after {execution_timeout} seconds.")
            # Set remaining validations to error
            results.append(ValidationResult(
                id=v.id,
                name=v.name,
                type=v.type.value,
                severity=v.severity.value,
                status="error",
                error_message="Execution timeout exceeded."
            ))
            continue
            
        if not v.enabled:
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [INFO] Skipping disabled validation: {v.name}")
            continue
            
        logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [PROCESS] Executing: {v.name} ({v.type.value})")
        
        strategy_class = STRATEGY_REGISTRY.get(v.type)
        if not strategy_class:
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [ERROR] Unknown validation strategy: {v.type}")
            results.append(ValidationResult(
                id=v.id,
                name=v.name,
                type=v.type.value,
                severity=v.severity.value,
                status="error",
                error_message=f"No strategy class registered for type '{v.type}'"
            ))
            continue
            
        # Instantiate strategy and run
        strategy_instance = strategy_class(v)
        
        # We catch exceptions inside strategies so that other tests can proceed
        try:
            res = strategy_instance.execute(
                source_engine=source_engine,
                target_engine=target_engine,
                source_type=source_type,
                target_type=target_type,
                source_config=source_config,
                target_config=target_config,
                source_query=source_query,
                target_query=target_query,
                key_columns=key_columns,
                row_limit=row_limit,
                chunk_size=chunk_size,
                query_timeout=query_timeout
            )
            # Sanitize numpy primitives from results attributes
            res.records_checked = int(res.records_checked) if res.records_checked is not None else 0
            res.records_failed = int(res.records_failed) if res.records_failed is not None else 0
            res.source_value = convert_numpy_types(res.source_value)
            res.target_value = convert_numpy_types(res.target_value)
            res.mismatch_details = convert_numpy_types(res.mismatch_details)
            
            results.append(res)
            
            # Print execution log line
            status_tag = "PASSED" if res.status == "passed" else "FAILED" if res.status == "failed" else "ERROR"
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [VALIDATION] {res.name} → {status_tag} (took {res.duration_ms}ms)")
        except TimeoutError as timeout_err:
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [TIMEOUT] {v.name} timed out after {query_timeout}s and execution was cancelled: {str(timeout_err)}")
            results.append(ValidationResult(
                id=v.id,
                name=v.name,
                type=v.type.value,
                severity=v.severity.value,
                status="error",
                error_message="Query execution timed out"
            ))
        except Exception as err:
            logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [ERROR] {v.name} failed: {str(err)}")
            results.append(ValidationResult(
                id=v.id,
                name=v.name,
                type=v.type.value,
                severity=v.severity.value,
                status="error",
                error_message=str(err)
            ))

    # Calculate Aggregates
    total_checks = len(results)
    passed_checks = sum(1 for r in results if r.status == "passed")
    failed_checks = sum(1 for r in results if r.status in ("failed", "error"))
    accuracy = round((passed_checks / total_checks) * 100, 2) if total_checks > 0 else 100.0
    
    execution_duration_ms = int((time.time() - start_time_epoch) * 1000)
    completed_at_str = datetime.now(timezone.utc).isoformat()
    
    # Final Execution Status
    if total_checks > 0 and failed_checks == 0:
        execution_status = ExecutionStatus.PASSED
    else:
        execution_status = ExecutionStatus.FAILED
        
    logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [RESULT] Audit Complete: {passed_checks}/{total_checks} checks passed ({accuracy}%) in {execution_duration_ms}ms")
    
    # 10. Generate AI Insights
    ai_insights = generate_ai_insights_service(results)
    
    # MASK configuration logs for security
    masked_source_config = mask_secrets(source_config)
    masked_target_config = mask_secrets(target_config)
    
    # Persist in pipeline_audits DB table
    audit_record = PipelineAuditDB(
        pipeline_name=pipeline_name,
        environment=environment,
        pipeline_type=pipeline_type,
        source_type=source_type.value if hasattr(source_type, "value") else source_type,
        source_config=json.dumps(masked_source_config),
        source_query=source_query,
        target_type=target_type.value if hasattr(target_type, "value") else target_type,
        target_config=json.dumps(masked_target_config),
        target_query=target_query,
        matching_keys=json.dumps(key_columns),
        selected_validations=json.dumps([v.model_dump() for v in validations]),
        execution_status=execution_status.value,
        execution_duration=execution_duration_ms,
        total_checks=total_checks,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        accuracy_percentage=float(accuracy),
        ai_insights=json.dumps(ai_insights.model_dump()),
        results=json.dumps([r.model_dump() for r in results]),
        execution_logs=json.dumps(logs),
        created_at=started_at_str,
        started_at=started_at_str,
        completed_at=completed_at_str
    )
    
    db.add(audit_record)
    db.commit()
    db.refresh(audit_record)
    
    # Persist report summary in global reports table
    create_report(
        db=db,
        report_type="ETL Reconciliation",
        status="passed" if execution_status == ExecutionStatus.PASSED else "failed",
        summary=f"Pipeline Auditor run for '{pipeline_name}' ({execution_status.value}): {passed_checks}/{total_checks} checks passed. Accuracy: {accuracy}%.",
        details={
            "audit_id": audit_record.id,
            "pipeline_name": pipeline_name,
            "environment": environment,
            "pipeline_type": pipeline_type,
            "passed_checks": passed_checks,
            "total_checks": total_checks,
            "accuracy_percentage": accuracy,
            "execution_duration_ms": execution_duration_ms,
            "results": [r.model_dump() for r in results[:10]],  # store a preview in details
            "logs": logs
        }
    )
    
    return ExecutePipelineResponse(
        status="success",
        audit_id=audit_record.id,
        execution_status=execution_status,
        summary=AuditSummary(
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            accuracy=str(accuracy),
            duration_ms=execution_duration_ms
        ),
        results=results,
        ai_insights=ai_insights,
        execution_logs=logs
    )


# ══════════════════════════════════════════════════════════════════════
# 10. Audit History & Detail Retrieval
# ══════════════════════════════════════════════════════════════════════

def get_audit_history_service(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    environment: Optional[str] = None,
    pipeline_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns paginated list of audit records matching optional filters.
    """
    query = db.query(PipelineAuditDB)
    
    if status:
        query = query.filter(PipelineAuditDB.execution_status == status)
    if environment:
        query = query.filter(PipelineAuditDB.environment == environment)
    if pipeline_type:
        query = query.filter(PipelineAuditDB.pipeline_type == pipeline_type)
        
    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(PipelineAuditDB.id.desc()).offset(offset).limit(page_size).all()
    
    history_items = []
    for row in items:
        history_items.append(AuditHistoryItem(
            id=row.id,
            pipeline_name=row.pipeline_name,
            environment=row.environment,
            pipeline_type=row.pipeline_type,
            source_type=row.source_type,
            target_type=row.target_type,
            execution_status=row.execution_status,
            total_checks=row.total_checks or 0,
            passed_checks=row.passed_checks or 0,
            failed_checks=row.failed_checks or 0,
            accuracy_percentage=row.accuracy_percentage or 0.0,
            execution_duration=row.execution_duration or 0,
            created_at=row.created_at,
            started_at=row.started_at,
            completed_at=row.completed_at
        ))
        
    import math
    pages = math.ceil(total / page_size) if total > 0 else 1
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "items": history_items
    }


def get_audit_detail_service(db: Session, audit_id: int) -> Optional[AuditDetailResponse]:
    """
    Fetches full audit execution detail by id. Parses stored JSON columns.
    """
    row = db.query(PipelineAuditDB).filter(PipelineAuditDB.id == audit_id).first()
    if not row:
        return None
        
    # Safely parse JSON strings from SQLite
    def safe_parse_json(text_data, default_val):
        if not text_data:
            return default_val
        try:
            return json.loads(text_data)
        except Exception:
            return default_val

    results_list = safe_parse_json(row.results, [])
    # Parse list of dicts to ValidationResult objects
    parsed_results = []
    for r in results_list:
        parsed_results.append(ValidationResult(**r))
        
    selected_validations_list = safe_parse_json(row.selected_validations, [])
    parsed_validations = []
    for v in selected_validations_list:
        parsed_validations.append(ValidationDescriptor(**v))
        
    ai_insights_data = safe_parse_json(row.ai_insights, {})
    ai_insights_payload = AiInsightsPayload(**ai_insights_data) if ai_insights_data else AiInsightsPayload()
    
    source_config_dict = safe_parse_json(row.source_config, {})
    target_config_dict = safe_parse_json(row.target_config, {})
    
    # Strip database credentials if not masked properly
    masked_source_config = mask_secrets(source_config_dict)
    masked_target_config = mask_secrets(target_config_dict)
    
    matching_keys_list = safe_parse_json(row.matching_keys, [])
    execution_logs_list = safe_parse_json(row.execution_logs, [])
    
    return AuditDetailResponse(
        id=row.id,
        pipeline_name=row.pipeline_name,
        environment=row.environment,
        pipeline_type=row.pipeline_type,
        source_type=row.source_type,
        target_type=row.target_type,
        source_config=masked_source_config,
        target_config=masked_target_config,
        source_query=row.source_query,
        target_query=row.target_query,
        matching_keys=matching_keys_list,
        selected_validations=parsed_validations,
        execution_status=row.execution_status,
        execution_duration=row.execution_duration or 0,
        total_checks=row.total_checks or 0,
        passed_checks=row.passed_checks or 0,
        failed_checks=row.failed_checks or 0,
        accuracy_percentage=row.accuracy_percentage or 0.0,
        results=parsed_results,
        ai_insights=ai_insights_payload,
        execution_logs=execution_logs_list,
        report_path=row.report_path,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at
    )


# ══════════════════════════════════════════════════════════════════════
# 11. Report Export Service
# ══════════════════════════════════════════════════════════════════════

def export_audit_to_format(db: Session, audit_id: int, format: ExportFormat) -> Response:
    """
    Renders an audit run summary and details into CSV, JSON, or Excel sheets.
    """
    row = db.query(PipelineAuditDB).filter(PipelineAuditDB.id == audit_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Audit execution {audit_id} not found")
        
    results_list = json.loads(row.results) if row.results else []
    
    # Build details DataFrame
    records = []
    for r in results_list:
        records.append({
            "Check ID": r.get("id"),
            "Check Name": r.get("name"),
            "Check Type": r.get("type"),
            "Severity": r.get("severity"),
            "Status": r.get("status"),
            "Records Checked": r.get("records_checked", 0),
            "Records Failed": r.get("records_failed", 0),
            "Source Value": r.get("source_value"),
            "Target Value": r.get("target_value"),
            "Error Message": r.get("error_message"),
            "Duration (ms)": r.get("duration_ms", 0)
        })
    df = pd.DataFrame(records)
    
    filename = f"pipeline_audit_{row.id}_{datetime.now().strftime('%Y%m%d')}"
    
    if format == ExportFormat.csv:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
        
    elif format == ExportFormat.json:
        # Full JSON details export
        detail_dict = {
            "id": row.id,
            "pipeline_name": row.pipeline_name,
            "environment": row.environment,
            "pipeline_type": row.pipeline_type,
            "source_type": row.source_type,
            "target_type": row.target_type,
            "execution_status": row.execution_status,
            "execution_duration_ms": row.execution_duration,
            "total_checks": row.total_checks,
            "passed_checks": row.passed_checks,
            "failed_checks": row.failed_checks,
            "accuracy_percentage": row.accuracy_percentage,
            "created_at": row.created_at,
            "started_at": row.started_at,
            "completed_at": row.completed_at,
            "results": results_list,
            "ai_insights": json.loads(row.ai_insights) if row.ai_insights else {},
            "execution_logs": json.loads(row.execution_logs) if row.execution_logs else []
        }
        json_content = json.dumps(detail_dict, indent=2)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}.json"}
        )
        
    elif format == ExportFormat.excel:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Audit Summary")
            
            # Additional tab for mismatch failures
            mismatches = []
            for r in results_list:
                details = r.get("mismatch_details")
                if details:
                    for det in details:
                        mismatches.append({
                            "Check ID": r.get("id"),
                            "Check Name": r.get("name"),
                            "Mismatch Detail": json.dumps(det)
                        })
            if mismatches:
                mismatch_df = pd.DataFrame(mismatches)
                mismatch_df.to_excel(writer, index=False, sheet_name="Mismatches")
                
        return Response(
            content=excel_buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
        
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
