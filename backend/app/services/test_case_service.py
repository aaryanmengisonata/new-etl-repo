from __future__ import annotations

import csv
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.orm import TestCaseDB

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATASET_FILE_MAP = {
    "bronze_silver": DATA_DIR / "etl_validation_bronze_to_silver_tests.csv",
    "silver_gold": DATA_DIR / "etl_validation_silver_to_gold_tests.csv",
}

def resolve_dataset_file(dataset: str) -> Path:
    dataset_key = (dataset or "bronze_silver").strip().lower()
    if dataset_key not in DATASET_FILE_MAP:
        raise ValueError(f"Unsupported dataset '{dataset}'.")
    return DATASET_FILE_MAP[dataset_key]

def import_csv_to_db_if_empty(db: Session):
    """Imports initial CSV data to PostgreSQL if the test_cases table is empty."""
    count = db.query(TestCaseDB).count()
    if count > 0:
        return  # DB already has data

    for dataset_key, csv_path in DATASET_FILE_MAP.items():
        if not csv_path.exists():
            continue
        
        with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for index, row in enumerate(reader, start=1):
                tc = TestCaseDB(
                    test_id=(row.get("test_id") or f"ROW_{index}").strip(),
                    functionality=(
                        row.get("validation_type")
                        or row.get("target_layer")
                        or row.get("source_layer")
                        or dataset_key.replace("_", " to ")
                    ).strip(),
                    sql_id=str(index),
                    expected_condition=(row.get("validation_type") or "EQUAL").strip(),
                    enabled=(row.get("enabled") or "TRUE").strip(),
                    description=(row.get("description") or row.get("test_name") or "").strip(),
                    source_file=str(csv_path),
                    dataset=dataset_key
                )
                db.add(tc)
    db.commit()


def get_test_cases(dataset: str, db: Session) -> list[TestCaseDB]:
    return db.query(TestCaseDB).filter(TestCaseDB.dataset == dataset).all()


def get_dataset_preview(dataset: str, db: Session, limit: int = 50) -> dict[str, object]:
    """Generates a dataset preview directly from the DB for the UI."""
    test_cases = db.query(TestCaseDB).filter(TestCaseDB.dataset == dataset).limit(limit).all()
    
    columns = ["test_id", "functionality", "sql_id", "expected_condition", "enabled", "description"]
    rows = []
    
    for tc in test_cases:
        rows.append([
            tc.test_id,
            tc.functionality,
            tc.sql_id,
            tc.expected_condition,
            tc.enabled,
            tc.description
        ])
        
    return {
        "dataset": dataset,
        "source_file": "PostgreSQL DB",
        "columns": columns,
        "rows": rows,
    }


def create_test_case(dataset: str, test_case: dict[str, str], db: Session) -> TestCaseDB:
    new_tc = TestCaseDB(
        test_id=test_case.get("test_id", ""),
        functionality=test_case.get("functionality", ""),
        sql_id=test_case.get("sql_id", ""),
        expected_condition=test_case.get("expected_condition", ""),
        enabled=test_case.get("enabled", ""),
        description=test_case.get("description", ""),
        source_file="PostgreSQL DB",
        dataset=dataset
    )
    db.add(new_tc)
    db.commit()
    db.refresh(new_tc)
    return new_tc

def update_test_case(dataset: str, test_id: str, updated_data: dict[str, str], db: Session) -> TestCaseDB:
    tc = db.query(TestCaseDB).filter(TestCaseDB.dataset == dataset, TestCaseDB.test_id == test_id).first()
    if not tc:
        raise ValueError(f"Test case with ID {test_id} not found.")
    
    for key, value in updated_data.items():
        if hasattr(tc, key) and key not in ["id", "dataset", "source_file"]:
            setattr(tc, key, value)
            
    db.commit()
    db.refresh(tc)
    return tc

def delete_test_case(dataset: str, test_id: str, db: Session) -> bool:
    tc = db.query(TestCaseDB).filter(TestCaseDB.dataset == dataset, TestCaseDB.test_id == test_id).first()
    if tc:
        db.delete(tc)
        db.commit()
        return True
    return False
