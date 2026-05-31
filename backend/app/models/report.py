from pydantic import BaseModel
from typing import Optional, List


class ReportCreate(BaseModel):
    type: str                          # e.g. "API Test", "DB Audit", "ETL Reconciliation"
    status: str                        # "passed" | "failed"
    summary: Optional[str] = None      # Human-readable one-liner
    details: Optional[str] = None      # JSON-serialized execution payload


class ReportResponse(BaseModel):
    id: int
    timestamp: str
    type: str
    status: str
    summary: Optional[str] = None
    details: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class ReportMasterSummary(BaseModel):
    total_runs: int
    passed: int
    failed: int
    pass_rate: float
    by_type: dict                      # { "API Test": { "passed": 3, "failed": 1 }, ... }
    recent: List[ReportResponse]       # Last 5 reports
