from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.report import ReportCreate
from app.services.report_service import (
    get_recent_reports,
    get_report_by_id,
    create_report,
    generate_master_summary,
    export_reports_csv,
    delete_report,
)

router = APIRouter(tags=["reports"])


# ── Public (no /api prefix — matches existing frontend call) ─────────

@router.get("/recent-reports")
def list_recent_reports(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return recent reports ordered newest-first."""
    return get_recent_reports(db, limit)


# ── Prefixed under /api ──────────────────────────────────────────────

@router.get("/api/reports/summary")
def master_summary(db: Session = Depends(get_db)):
    """Aggregated statistics across all stored reports."""
    return generate_master_summary(db)


@router.get("/api/reports/export/csv")
def export_csv(db: Session = Depends(get_db)):
    """Download all reports as a CSV file."""
    csv_content = export_reports_csv(db)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reports_export.csv"},
    )


@router.get("/api/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Fetch a single report by ID."""
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return report


@router.post("/api/reports")
def save_report(payload: ReportCreate, db: Session = Depends(get_db)):
    """Create a new report record."""
    return create_report(
        db,
        report_type=payload.type,
        status=payload.status,
        summary=payload.summary or "",
        details=payload.details,
    )


@router.delete("/api/reports/{report_id}")
def remove_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a report by ID."""
    success = delete_report(db, report_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return {"status": "success", "message": f"Deleted report {report_id}"}
