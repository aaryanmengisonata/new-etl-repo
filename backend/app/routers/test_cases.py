from fastapi import APIRouter, HTTPException, Query

from app.models.test_case import TestCaseSummary
from app.services.test_case_service import get_dataset_preview, get_test_cases


router = APIRouter(prefix="/api", tags=["test-cases"])


@router.get("/test-cases", response_model=list[TestCaseSummary])
def list_test_cases(dataset: str = Query(default="bronze_silver")):
    try:
        return get_test_cases(dataset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/dataset-preview")
def dataset_preview(
    dataset: str = Query(default="bronze_silver"),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return get_dataset_preview(dataset, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
