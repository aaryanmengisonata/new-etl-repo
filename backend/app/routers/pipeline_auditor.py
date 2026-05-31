"""
Pipeline Auditor — FastAPI Router

Exposes endpoints for testing connections, generating AI audit suggestions,
running reconciliation tests, fetching paginated run history, and exporting report files.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import PipelineAuditDB
from app.models.pipeline_auditor import (
    TestConnectionRequest,
    TestConnectionResponse,
    AnalyzePipelineRequest,
    AnalyzePipelineResponse,
    ExecutePipelineRequest,
    ExecutePipelineResponse,
    ExportReportRequest,
    AuditDetailResponse,
)
from app.services.pipeline_auditor_service import (
    test_connection_service,
    analyze_pipeline_service,
    execute_pipeline_audit_service,
    get_audit_history_service,
    get_audit_detail_service,
    export_audit_to_format,
    validate_sql_safety,
)

router = APIRouter(prefix="/api/pipeline-auditor", tags=["pipeline-auditor"])


@router.post("/test-connection", response_model=TestConnectionResponse)
def test_connection(payload: TestConnectionRequest):
    """
    Validates connection parameters for a database or API, returning discovered metadata.
    """
    try:
        return test_connection_service(type=payload.type, config=payload.config)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except ConnectionError as conn_err:
        raise HTTPException(status_code=503, detail=str(conn_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test connection: {str(e)}")


@router.post("/analyze", response_model=AnalyzePipelineResponse)
def analyze_pipeline(payload: AnalyzePipelineRequest):
    """
    Inspects source/target structures dynamically and returns suggested reconciliation tests.
    """
    try:
        # Enforce SQL safety at the entrypoint
        if payload.source_type == "database":
            validate_sql_safety(payload.source_query)
        if payload.target_type == "database":
            validate_sql_safety(payload.target_query)
            
        result = analyze_pipeline_service(
            source_type=payload.source_type,
            source_config=payload.source_config,
            target_type=payload.target_type,
            target_config=payload.target_config,
            source_query=payload.source_query,
            target_query=payload.target_query,
            key_columns=payload.key_columns
        )
        return AnalyzePipelineResponse(**result)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze pipeline schema: {str(e)}")


@router.post("/execute", response_model=ExecutePipelineResponse)
def execute_pipeline(payload: ExecutePipelineRequest, db: Session = Depends(get_db)):
    """
    Executes the suite of reconciliation validation checks.
    """
    try:
        # Enforce SQL safety on the main queries
        if payload.source_type == "database":
            validate_sql_safety(payload.source_query)
        if payload.target_type == "database":
            validate_sql_safety(payload.target_query)
            
        # Enforce SQL safety on custom SQL validation inputs
        for v in payload.validations:
            if v.source_sql:
                validate_sql_safety(v.source_sql)
            if v.target_sql:
                validate_sql_safety(v.target_sql)
                
        return execute_pipeline_audit_service(
            db=db,
            pipeline_name=payload.pipeline_name,
            environment=payload.environment,
            pipeline_type=payload.pipeline_type,
            source_type=payload.source_type,
            source_config=payload.source_config,
            target_type=payload.target_type,
            target_config=payload.target_config,
            source_query=payload.source_query,
            target_query=payload.target_query,
            key_columns=payload.key_columns,
            validations=payload.validations,
            row_limit=payload.row_limit,
            chunk_size=payload.chunk_size,
            query_timeout=payload.query_timeout,
            execution_timeout=payload.execution_timeout
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute pipeline audit: {str(e)}")


@router.get("/history")
def get_audit_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    environment: Optional[str] = Query(default=None),
    pipeline_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Retrieves a paginated list of previous pipeline audit runs.
    """
    try:
        return get_audit_history_service(
            db=db,
            page=page,
            page_size=page_size,
            status=status,
            environment=environment,
            pipeline_type=pipeline_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit history: {str(e)}")


@router.get("/history/{audit_id}", response_model=AuditDetailResponse)
def get_audit_detail(audit_id: int, db: Session = Depends(get_db)):
    """
    Fetches the detailed results and execution logs of a specific audit run.
    """
    try:
        detail = get_audit_detail_service(db=db, audit_id=audit_id)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Audit run #{audit_id} not found")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit run details: {str(e)}")


@router.post("/export")
def export_audit_report(payload: ExportReportRequest, db: Session = Depends(get_db)):
    """
    Exports a completed pipeline audit execution report as CSV, JSON, or Excel.
    """
    try:
        return export_audit_to_format(db=db, audit_id=payload.audit_id, format=payload.format)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")


@router.delete("/history/{audit_id}")
def delete_audit_run(audit_id: int, db: Session = Depends(get_db)):
    """
    Deletes an audit execution log from database history.
    """
    try:
        row = db.query(PipelineAuditDB).filter(PipelineAuditDB.id == audit_id).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Audit run #{audit_id} not found")
        db.delete(row)
        db.commit()
        return {"status": "success", "message": f"Deleted audit #{audit_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete audit run: {str(e)}")
