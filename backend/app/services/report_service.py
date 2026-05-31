import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.orm import ReportDB


def get_recent_reports(db: Session, limit: int = 50) -> List[dict]:
    """Fetch the most recent reports, newest first."""
    reports = (
        db.query(ReportDB)
        .order_by(ReportDB.id.desc())
        .limit(limit)
        .all()
    )
    return [_row_to_dict(r) for r in reports]


def get_report_by_id(db: Session, report_id: int) -> Optional[dict]:
    """Fetch a single report with full details."""
    report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
    if not report:
        return None
    return _row_to_dict(report)


def create_report(
    db: Session,
    report_type: str,
    status: str,
    summary: str = "",
    details: Any = None,
) -> dict:
    """Persist a new report to the database."""
    details_json = json.dumps(details) if details is not None else None
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    row = ReportDB(
        timestamp=timestamp,
        type=report_type,
        status=status,
        summary=summary,
        details=details_json,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def generate_master_summary(db: Session) -> dict:
    """Compute aggregate statistics across all stored reports."""
    all_reports = db.query(ReportDB).all()

    total = len(all_reports)
    passed = sum(1 for r in all_reports if r.status == "passed")
    failed = total - passed
    pass_rate = round((passed / total) * 100, 2) if total > 0 else 0.0

    # Breakdown by type
    by_type: Dict[str, Dict[str, int]] = {}
    for r in all_reports:
        bucket = by_type.setdefault(r.type, {"passed": 0, "failed": 0})
        bucket[r.status] = bucket.get(r.status, 0) + 1

    # Last 5 reports
    recent = (
        db.query(ReportDB)
        .order_by(ReportDB.id.desc())
        .limit(5)
        .all()
    )

    return {
        "total_runs": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "by_type": by_type,
        "recent": [_row_to_dict(r) for r in recent],
    }


def export_reports_csv(db: Session) -> str:
    """Generate a CSV string of all reports."""
    all_reports = db.query(ReportDB).order_by(ReportDB.id.desc()).all()

    lines = ["id,timestamp,type,status,summary"]
    for r in all_reports:
        # Escape commas / quotes in summary
        safe_summary = (r.summary or "").replace('"', '""')
        lines.append(f'{r.id},{r.timestamp},{r.type},{r.status},"{safe_summary}"')

    return "\n".join(lines)


def delete_report(db: Session, report_id: int) -> bool:
    """Delete a report by ID. Returns True if found and deleted."""
    report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
    if not report:
        return False
    db.delete(report)
    db.commit()
    return True


# ── helpers ──────────────────────────────────────────────────────────

def _row_to_dict(row: ReportDB) -> dict:
    """Convert an ORM row to a plain dict the frontend expects."""
    return {
        "id": row.id,
        "timestamp": row.timestamp,
        "type": row.type,
        "status": row.status,
        "summary": row.summary,
        "details": row.details,
    }
