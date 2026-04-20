"""Run CSV-driven ETL validations without pytest (Fabric notebook friendly)."""

from __future__ import annotations

import argparse
import contextlib
import sys
import types
from typing import Any, Dict, List

import pandas as pd


def _ensure_allure_stub() -> None:
    """Provide a minimal allure stub when allure is not installed."""
    try:
        import allure  # noqa: F401
        return
    except Exception:
        pass

    dummy = types.ModuleType("allure")
    dummy.epic = lambda *args, **kwargs: (lambda obj: obj)
    dummy.feature = lambda *args, **kwargs: (lambda obj: obj)
    dummy.step = lambda *args, **kwargs: contextlib.nullcontext()
    dummy.attach = lambda *args, **kwargs: None
    dummy.attachment_type = types.SimpleNamespace(TEXT="TEXT")
    dummy.dynamic = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        description=lambda *args, **kwargs: None,
        label=lambda *args, **kwargs: None,
    )
    sys.modules["allure"] = dummy


def run_validations(
    test_ids: List[str] | None = None,
    max_tests: int | None = None,
    fail_fast: bool = False,
) -> pd.DataFrame:
    """Execute enabled CSV test cases and return result rows."""
    _ensure_allure_stub()

    from test_csv_driven_etl_validation import TestCSVDrivenETLValidation

    TestCSVDrivenETLValidation.setup_class()
    runner = TestCSVDrivenETLValidation()
    test_cases = list(TestCSVDrivenETLValidation.test_cases)

    if test_ids:
        wanted = {item.strip() for item in test_ids if item.strip()}
        test_cases = [tc for tc in test_cases if str(tc.get("test_id", "")).strip() in wanted]

    if max_tests is not None and max_tests > 0:
        test_cases = test_cases[:max_tests]

    rows: List[Dict[str, Any]] = []
    try:
        for case in test_cases:
            test_id = str(case.get("test_id", "")).strip()
            test_name = str(case.get("test_name", "")).strip()
            validation_type = str(case.get("validation_type", "")).strip()
            table_name = str(case.get("table_name", "")).strip()
            try:
                result = runner._execute_validation(case)
            except Exception as exc:
                result = {"status": "ERROR", "message": str(exc)}

            row = {
                "test_id": test_id,
                "test_name": test_name,
                "validation_type": validation_type,
                "table_name": table_name,
                "status": result.get("status", "UNKNOWN"),
                "source_count": result.get("source_count"),
                "target_count": result.get("target_count"),
                "matched_count": result.get("matched_count"),
                "message": result.get("message", ""),
            }
            rows.append(row)

            if fail_fast and row["status"] != "PASSED":
                break
    finally:
        TestCSVDrivenETLValidation.source_client.close()
        TestCSVDrivenETLValidation.target_client.close()

    return pd.DataFrame(rows)


def _main() -> int:
    parser = argparse.ArgumentParser(description="Run ETL validations without pytest")
    parser.add_argument("--test-ids", default="", help="Comma-separated test IDs (e.g., TEST_01,TEST_02)")
    parser.add_argument("--max-tests", type=int, default=0, help="Run only first N tests")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first non-PASSED result")
    args = parser.parse_args()

    selected_ids = [item for item in args.test_ids.split(",") if item.strip()] if args.test_ids else None
    df = run_validations(
        test_ids=selected_ids,
        max_tests=args.max_tests if args.max_tests > 0 else None,
        fail_fast=args.fail_fast,
    )
    if df.empty:
        print("No tests selected.")
        return 1

    print(df.to_string(index=False))
    summary = df["status"].value_counts().to_dict()
    print(f"\nSummary: {summary}")
    return 0 if (df["status"] == "PASSED").all() else 2


if __name__ == "__main__":
    raise SystemExit(_main())
