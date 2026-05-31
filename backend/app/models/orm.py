from sqlalchemy import Column, Integer, String, Text, Boolean, Float
from app.database import Base


class TestCaseDB(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String, index=True)
    functionality = Column(String)
    sql_id = Column(String)
    expected_condition = Column(String)
    enabled = Column(String)
    description = Column(Text)
    source_file = Column(String)
    dataset = Column(String, index=True)


class ReportDB(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(String, nullable=False)
    type = Column(String, nullable=False)        # "API Test", "DB Audit", "ETL Reconciliation"
    status = Column(String, nullable=False)       # "passed" | "failed"
    summary = Column(Text, nullable=True)
    details = Column(Text, nullable=True)         # JSON-serialized execution payload


class PipelineAuditDB(Base):
    """
    Stores every pipeline audit execution for history, re-run, and reporting.

    SECURITY: source_config and target_config store MASKED connection
    metadata only. Raw passwords, API keys, and bearer tokens are NEVER
    persisted. The service layer strips secrets before writing.
    """
    __tablename__ = "pipeline_audits"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_name        = Column(String, nullable=False, index=True)

    # Audit metadata (for filtering / reporting)
    environment          = Column(String, nullable=True)            # DEV | QA | UAT | PROD
    pipeline_type        = Column(String, nullable=True)            # BronzeToSilver | SilverToGold | Custom

    # Source connection (MASKED — no raw secrets)
    source_type          = Column(String, nullable=False)           # "database" | "api"
    source_config        = Column(Text, nullable=True)              # JSON: masked connection metadata
    source_query         = Column(Text, nullable=True)

    # Target connection (MASKED — no raw secrets)
    target_type          = Column(String, nullable=False)           # "database" | "api"
    target_config        = Column(Text, nullable=True)              # JSON: masked connection metadata
    target_query         = Column(Text, nullable=True)

    # Matching / reconciliation keys (JSON array for composite key support)
    matching_keys        = Column(Text, nullable=True)              # JSON: ["customer_id", "order_id"]

    # Validations selected for this run
    selected_validations = Column(Text, nullable=True)              # JSON: list of validation descriptors

    # Execution lifecycle
    execution_status     = Column(String, nullable=False, default="PENDING")  # PENDING | RUNNING | PASSED | FAILED | CANCELLED
    execution_duration   = Column(Integer, nullable=True, default=0)          # milliseconds

    # Result aggregates
    total_checks         = Column(Integer, nullable=True, default=0)
    passed_checks        = Column(Integer, nullable=True, default=0)
    failed_checks        = Column(Integer, nullable=True, default=0)
    accuracy_percentage  = Column(Float, nullable=True, default=0.0)

    # AI-generated failure analysis
    ai_insights          = Column(Text, nullable=True)              # JSON: summary, failures, recommendations

    # Downloadable report file path (populated after export)
    report_path          = Column(String, nullable=True)

    # Detailed per-check results
    results              = Column(Text, nullable=True)              # JSON: per-validation detail rows
    execution_logs       = Column(Text, nullable=True)              # JSON: timestamped log lines

    # Timestamps
    created_at           = Column(String, nullable=False)           # ISO-8601 UTC — when the audit was created
    started_at           = Column(String, nullable=True)            # ISO-8601 UTC — when execution began
    completed_at         = Column(String, nullable=True)            # ISO-8601 UTC — when execution finished

