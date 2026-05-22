from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.test_case import TestCaseSummary
from app.services.test_case_service import (
    get_dataset_preview, 
    get_test_cases, 
    create_test_case, 
    update_test_case, 
    delete_test_case
)


router = APIRouter(prefix="/api", tags=["test-cases"])


@router.get("/test-cases", response_model=list[TestCaseSummary])
def list_test_cases(dataset: str = Query(default="bronze_silver"), db: Session = Depends(get_db)):
    try:
        return get_test_cases(dataset, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/test-cases")
def add_test_case(test_case: dict, dataset: str = Query(default="bronze_silver"), db: Session = Depends(get_db)):
    try:
        return create_test_case(dataset, test_case, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/test-cases/{test_id}")
def edit_test_case(test_id: str, test_case: dict, dataset: str = Query(default="bronze_silver"), db: Session = Depends(get_db)):
    try:
        return update_test_case(dataset, test_id, test_case, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/test-cases/{test_id}")
def remove_test_case(test_id: str, dataset: str = Query(default="bronze_silver"), db: Session = Depends(get_db)):
    try:
        success = delete_test_case(dataset, test_id, db)
        if not success:
            raise HTTPException(status_code=404, detail=f"Test case {test_id} not found")
        return {"status": "success", "message": f"Deleted {test_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dataset-preview")
def dataset_preview(
    dataset: str = Query(default="bronze_silver"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    try:
        return get_dataset_preview(dataset, db, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
