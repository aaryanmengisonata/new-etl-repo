from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.report_service import create_report
from app.models.integration_sentry import (
    SystemAnalysisRequest, SystemAnalysisResponse,
    ReconciliationRequest, ReconciliationResult
)
from app.services.integration_sentry_service import (
    analyze_systems, execute_reconciliation
)

router = APIRouter(prefix="/api/integration-sentry", tags=["integration-sentry"])

@router.post("/analyze", response_model=SystemAnalysisResponse)
async def analyze_systems_endpoint(request: SystemAnalysisRequest):
    try:
        return analyze_systems(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", response_model=ReconciliationResult)
async def execute_reconciliation_endpoint(request: ReconciliationRequest, db_session: Session = Depends(get_db)):
    try:
        result = execute_reconciliation(request)
        
        # Save Report
        try:
            create_report(
                db_session,
                report_type="System Reconciliation",
                status="passed" if result.passed else "failed",
                summary=f"Integration Check: {request.scenario_id} — {'PASSED' if result.passed else 'FAILED'} (Accuracy: {result.accuracy:.1f}%)",
                details=result.model_dump(),
            )
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            # We don't fail the API call if saving report fails
            result.execution_logs.append(f"[WARNING] Failed to save execution report: {str(e)}")
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
