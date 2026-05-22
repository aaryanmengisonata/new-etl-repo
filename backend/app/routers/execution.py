from fastapi import APIRouter, HTTPException
from app.models.execution import ExecuteRequest, ExecuteResponse, GenerateQueryRequest, GenerateQueryResponse
from app.services.execution_service import run_execution, generate_ai_query

router = APIRouter(prefix="/api", tags=["execution"])

@router.post("/execute", response_model=ExecuteResponse)
async def execute_audit(request: ExecuteRequest):
    try:
        results = run_execution(request.dataset)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-query", response_model=GenerateQueryResponse)
async def generate_query(request: GenerateQueryRequest):
    try:
        results = generate_ai_query(request.prompt)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
