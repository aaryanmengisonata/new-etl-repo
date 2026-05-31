"""
Pipeline Auditor — Pydantic Request / Response Models

All API contracts for the Pipeline Auditor module.

Design decisions:
 - ValidationType enum is the strategy-pattern dispatch key.
 - matching_keys is a JSON List[str] for composite key support.
 - Connection configs include a mask_secrets() utility — the service layer
   calls this before persisting to PipelineAuditDB.
 - ValidationResult carries severity + records_checked + records_failed
   for dashboard metrics.
 - row_limit / chunk_size protect against large-dataset memory blow-up.
"""

from __future__ import annotations

from copy import deepcopy
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════════════════════════════


class ConnectionType(str, Enum):
    database = "database"
    api = "api"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ValidationType(str, Enum):
    """Strategy-pattern key — each maps 1:1 to a validation strategy class."""
    row_count = "row_count"
    exact_match = "exact_match"
    null_check = "null_check"
    duplicate_check = "duplicate_check"
    schema_validation = "schema_validation"
    aggregate = "aggregate"
    missing_records = "missing_records"


class AggregateFunction(str, Enum):
    SUM = "SUM"
    COUNT = "COUNT"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ExportFormat(str, Enum):
    csv = "csv"
    json = "json"
    excel = "excel"


class PipelineTypeEnum(str, Enum):
    BronzeToSilver = "BronzeToSilver"
    SilverToGold = "SilverToGold"
    Custom = "Custom"


class EnvironmentEnum(str, Enum):
    DEV = "DEV"
    QA = "QA"
    UAT = "UAT"
    PROD = "PROD"


# ══════════════════════════════════════════════════════════════════════
# Connection Configs
# ══════════════════════════════════════════════════════════════════════

SECRET_FIELDS = {"password", "token", "api_key", "secret", "bearer_token"}


def mask_secrets(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a copy of the config dict with all secret fields masked.
    Used before persisting to PipelineAuditDB to prevent credential leaks.
    """
    masked = deepcopy(config)
    for key in list(masked.keys()):
        if key.lower() in SECRET_FIELDS:
            val = masked[key]
            if val and isinstance(val, str) and len(val) > 0:
                masked[key] = "••••••••"
            else:
                masked[key] = ""
    return masked


class DatabaseConnectionConfig(BaseModel):
    """Connection parameters for a relational database."""
    connection_name: str = ""
    db_type: str = "sqlite"           # sqlite | postgresql | mysql | mssql
    host: str = "localhost"
    port: str = "5432"
    db_name: str = "etl_test.db"
    username: str = ""
    password: str = ""


class ApiConnectionConfig(BaseModel):
    """Connection parameters for a REST API source/target."""
    base_url: str = ""
    method: str = "GET"
    auth_type: str = "none"           # none | bearer | api_key | basic
    headers: Dict[str, str] = Field(default_factory=dict)
    token: str = ""


# ══════════════════════════════════════════════════════════════════════
# 1. POST /api/pipeline-auditor/test-connection
# ══════════════════════════════════════════════════════════════════════


class TestConnectionRequest(BaseModel):
    type: ConnectionType
    config: Dict[str, Any]            # DatabaseConnectionConfig or ApiConnectionConfig dict


class ConnectionMetadata(BaseModel):
    """Metadata returned after a successful connection test."""
    tables: List[str] = Field(default_factory=list)
    row_counts: Dict[str, int] = Field(default_factory=dict)
    columns: Dict[str, List[Dict[str, str]]] = Field(default_factory=dict)  # table -> [{name, type}]


class TestConnectionResponse(BaseModel):
    status: str                       # "success" | "failed"
    message: str
    latency_ms: int = 0
    metadata: Optional[ConnectionMetadata] = None


# ══════════════════════════════════════════════════════════════════════
# 2. POST /api/pipeline-auditor/analyze
# ══════════════════════════════════════════════════════════════════════


class ValidationDescriptor(BaseModel):
    """
    A single validation check — used for both AI-generated suggestions
    and user-created custom validations.
    This is the unit that the strategy-pattern engine dispatches on.
    """
    id: str                                         # unique check ID (e.g. "RC_001")
    name: str                                       # human-readable name
    type: ValidationType                            # strategy dispatch key
    description: str = ""
    severity: Severity = Severity.medium
    enabled: bool = True

    # SQL (populated for DB-based checks)
    source_sql: Optional[str] = None
    target_sql: Optional[str] = None

    # Aggregate-specific
    aggregate_function: Optional[AggregateFunction] = None
    aggregate_column: Optional[str] = None

    # Metadata
    column_name: Optional[str] = None               # for null_check / duplicate_check


class AnalyzePipelineRequest(BaseModel):
    source_type: ConnectionType
    source_config: Dict[str, Any]
    target_type: ConnectionType
    target_config: Dict[str, Any]
    source_query: str
    target_query: str
    key_columns: List[str] = Field(default_factory=list)   # JSON array for composite keys
    pipeline_name: str = ""
    environment: Optional[str] = None
    pipeline_type: Optional[str] = None


class AnalyzePipelineResponse(BaseModel):
    status: str
    suggestions: List[ValidationDescriptor] = Field(default_factory=list)
    source_columns: List[Dict[str, str]] = Field(default_factory=list)   # [{name, type}]
    target_columns: List[Dict[str, str]] = Field(default_factory=list)
    analysis_logs: List[str] = Field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════
# 3. POST /api/pipeline-auditor/execute
# ══════════════════════════════════════════════════════════════════════


class ExecutePipelineRequest(BaseModel):
    pipeline_name: str
    environment: Optional[str] = None
    pipeline_type: Optional[str] = None

    source_type: ConnectionType
    source_config: Dict[str, Any]
    target_type: ConnectionType
    target_config: Dict[str, Any]
    source_query: str
    target_query: str
    key_columns: List[str] = Field(default_factory=list)
    validations: List[ValidationDescriptor]

    # Large dataset protection
    row_limit: int = Field(default=50000, ge=100, le=500000)
    chunk_size: int = Field(default=5000, ge=100, le=50000)

    # Timeouts
    query_timeout: int = Field(default=30, ge=0, le=3600)
    execution_timeout: int = Field(default=300, ge=1, le=18000)



class ValidationResult(BaseModel):
    """Result of a single validation check execution."""
    id: str
    name: str
    type: str                                       # ValidationType value
    severity: str                                   # Severity value (critical/high/medium/low)
    status: str                                     # "passed" | "failed" | "error"
    records_checked: int = 0
    records_failed: int = 0
    source_value: Optional[Any] = None
    target_value: Optional[Any] = None
    mismatch_details: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    duration_ms: int = 0


class AuditSummary(BaseModel):
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    accuracy: str = "0.0"
    duration_ms: int = 0


class AiInsight(BaseModel):
    """AI-generated analysis of a single failure."""
    name: str
    cause: str
    recommendation: str


class AiInsightsPayload(BaseModel):
    summary: str = ""
    failures: List[AiInsight] = Field(default_factory=list)


class ExecutePipelineResponse(BaseModel):
    status: str                                     # "success" | "error"
    audit_id: int = 0
    execution_status: ExecutionStatus = ExecutionStatus.PASSED
    summary: AuditSummary = Field(default_factory=AuditSummary)
    results: List[ValidationResult] = Field(default_factory=list)
    ai_insights: Optional[AiInsightsPayload] = None
    execution_logs: List[str] = Field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════
# 4. POST /api/pipeline-auditor/export
# ══════════════════════════════════════════════════════════════════════


class ExportReportRequest(BaseModel):
    audit_id: int
    format: ExportFormat


# ══════════════════════════════════════════════════════════════════════
# 5. GET /api/pipeline-auditor/history
#    GET /api/pipeline-auditor/history/{id}
# ══════════════════════════════════════════════════════════════════════


class AuditHistoryItem(BaseModel):
    id: int
    pipeline_name: str
    environment: Optional[str] = None
    pipeline_type: Optional[str] = None
    source_type: str
    target_type: str
    execution_status: str
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    accuracy_percentage: float = 0.0
    execution_duration: int = 0
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class AuditDetailResponse(BaseModel):
    """Full audit record including results, logs, and AI insights."""
    id: int
    pipeline_name: str
    environment: Optional[str] = None
    pipeline_type: Optional[str] = None
    source_type: str
    target_type: str
    source_config: Optional[Dict[str, Any]] = None   # MASKED — no secrets
    target_config: Optional[Dict[str, Any]] = None   # MASKED — no secrets
    source_query: Optional[str] = None
    target_query: Optional[str] = None
    matching_keys: Optional[List[str]] = None
    selected_validations: Optional[List[ValidationDescriptor]] = None
    execution_status: str
    execution_duration: int = 0
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    accuracy_percentage: float = 0.0
    results: Optional[List[ValidationResult]] = None
    ai_insights: Optional[AiInsightsPayload] = None
    execution_logs: Optional[List[str]] = None
    report_path: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════
# 6. DELETE /api/pipeline-auditor/history/{id}
#    (No special model needed — returns generic success dict)
# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# 7. Custom Validation Builder (used by frontend, sent in execute)
# ══════════════════════════════════════════════════════════════════════


class CustomValidationRequest(BaseModel):
    """User-defined custom validation to add alongside AI suggestions."""
    name: str
    type: ValidationType = ValidationType.row_count
    source_sql: Optional[str] = None
    target_sql: Optional[str] = None
    severity: Severity = Severity.medium
    description: str = ""
    aggregate_function: Optional[AggregateFunction] = None
    aggregate_column: Optional[str] = None
    column_name: Optional[str] = None
