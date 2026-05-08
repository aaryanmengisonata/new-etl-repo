from __future__ import annotations

import csv
from pathlib import Path


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


def get_test_cases(dataset: str) -> list[dict[str, str]]:
    csv_path = resolve_dataset_file(dataset)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            {
                "test_id": (row.get("test_id") or f"ROW_{index}").strip(),
                "functionality": (
                    row.get("validation_type")
                    or row.get("target_layer")
                    or row.get("source_layer")
                    or dataset.replace("_", " to ")
                ).strip(),
                "sql_id": str(index),
                "expected_condition": (row.get("validation_type") or "EQUAL").strip(),
                "enabled": (row.get("enabled") or "TRUE").strip(),
                "description": (row.get("description") or row.get("test_name") or "").strip(),
                "source_file": str(csv_path),
                "dataset": dataset,
            }
            for index, row in enumerate(reader, start=1)
        ]


def get_dataset_preview(dataset: str, limit: int = 50) -> dict[str, object]:
    csv_path = resolve_dataset_file(dataset)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = reader.fieldnames or []
        rows = []
        for index, row in enumerate(reader):
            if index >= limit:
                break
            rows.append([str(row.get(column, "")) for column in columns])

    return {
        "dataset": dataset,
        "source_file": str(csv_path),
        "columns": columns,
        "rows": rows,
    }
