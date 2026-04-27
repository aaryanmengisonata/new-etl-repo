import pytest
import json
import re
from pathlib import Path
from utils.api_client import APIClient
from utils.db_client import DatabaseClient

@pytest.fixture(scope="session")
def api_client():
    """Session-scoped API client fixture"""
    return APIClient()

@pytest.fixture(scope="session")
def db_client():
    """Session-scoped database client fixture"""
    return DatabaseClient()

@pytest.fixture(scope="module")
def sample_product():
    """Sample product data for testing"""
    return {
        "id": 1,
        "title": "Test Product",
        "price": 29.99,
        "description": "Test product description",
        "category": "electronics",
        "image": "https://example.com/image.jpg",
        "rating": {
            "rate": 4.5,
            "count": 100
        }
    }

@pytest.fixture(scope="module")
def product_schema():
    """Product JSON schema fixture"""
    with open('schemas/product_schema.json', 'r') as f:
        return json.load(f)

@pytest.fixture(scope="module")
def user_schema():
    """User JSON schema fixture"""
    with open('schemas/user_schema.json', 'r') as f:
        return json.load(f)

@pytest.fixture(scope="function")
def test_data_cleanup():
    """Fixture for test data cleanup"""
    yield
    # Cleanup code here if needed
    pass


def _safe_get_allure_results_dir(config):
    """Return --alluredir path when allure-pytest is enabled."""
    option_candidates = ("--alluredir", "alluredir", "allure_report_dir")
    for candidate in option_candidates:
        try:
            value = config.getoption(candidate)
        except Exception:
            value = None
        if value:
            return Path(value)
    return None


def _find_label(labels, key):
    for label in labels or []:
        if label.get("name") == key:
            return label.get("value")
    return None


def _is_fabric_result(result_data):
    labels = result_data.get("labels", [])
    parent_suite = _find_label(labels, "parentSuite") or ""
    suite = _find_label(labels, "suite") or ""
    package = _find_label(labels, "package") or ""

    fabric_scopes = (
        str(parent_suite).startswith("tests.fabric"),
        str(package).startswith("tests.fabric"),
        "fabric" in str(suite).lower(),
    )
    if any(fabric_scopes):
        return True

    return any(
        str(label.get("name", "")).lower() == "tag" and str(label.get("value", "")).lower() == "fabric"
        for label in labels
    )


def _build_dashboard_payload(result_files):
    sortable_records = []
    for index, result_file in enumerate(result_files):
        try:
            result_data = json.loads(result_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not _is_fabric_result(result_data):
            continue

        labels = result_data.get("labels", [])
        source_count = _find_label(labels, "Source_Count")
        target_count = _find_label(labels, "Target_Count")
        if source_count is None or target_count is None:
            continue

        try:
            source_value = int(float(source_count))
            target_value = int(float(target_count))
        except Exception:
            continue

        table_name = _find_label(labels, "Table") or "N/A"
        validation = _find_label(labels, "Validation") or "N/A"
        source_lakehouse = _find_label(labels, "Source_Lakehouse") or "N/A"
        target_lakehouse = _find_label(labels, "Target_Lakehouse") or "N/A"
        test_name = str(result_data.get("name") or "")
        testcase_match = re.search(r"(TEST[_-]?\d+)", test_name, flags=re.IGNORECASE)
        execution_start = result_data.get("start")
        if execution_start is None:
            execution_start = (result_data.get("time") or {}).get("start")

        sortable_records.append(
            {
                "index": index,
                "executionStart": execution_start,
                "testCaseId": testcase_match.group(1).upper().replace("-", "_") if testcase_match else None,
                "testName": test_name,
                "status": result_data.get("status", "unknown"),
                "source": {
                    "label": "Bronze (Source)",
                    "table": table_name,
                    "lakehouse": source_lakehouse,
                    "validation": validation,
                    "value": source_value,
                },
                "target": {
                    "label": "Silver (Target)",
                    "table": table_name,
                    "lakehouse": target_lakehouse,
                    "validation": validation,
                    "value": target_value,
                },
            }
        )

    if not sortable_records:
        return None

    sortable_records.sort(
        key=lambda item: (
            item["executionStart"] is None,
            item["executionStart"] if item["executionStart"] is not None else 0,
            item["index"],
        )
    )

    records = []
    for position, item in enumerate(sortable_records, start=1):
        records.append(
            {
                "testCase": item["testCaseId"] or f"TEST_{position:02d}",
                "testName": item["testName"],
                "status": item["status"],
                "source": item["source"],
                "target": item["target"],
            }
        )

    return {
        "title": "Bronze vs Silver Data Validation Checks",
        "xAxisTitle": "Test Cases",
        "yAxisTitle": "Number of Lines (Count)",
        "records": records,
    }


def _attach_dashboard_payload(result_files, dashboard_filename):
    """Reference dashboard JSON in one Allure result file so generate/serve can load it."""
    for result_file in result_files:
        try:
            result_data = json.loads(result_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        steps = result_data.get("steps")
        if isinstance(steps, list) and steps:
            step = steps[0]
            attachments = step.setdefault("attachments", [])
            if not any(
                att.get("source") == dashboard_filename or att.get("name") == "ETL Metrics Dashboard Data"
                for att in attachments
            ):
                attachments.append(
                    {
                        "name": "ETL Metrics Dashboard Data",
                        "source": dashboard_filename,
                        "type": "application/json",
                    }
                )
            result_file.write_text(json.dumps(result_data), encoding="utf-8")
            return

        attachments = result_data.setdefault("attachments", [])
        if not any(
            att.get("source") == dashboard_filename or att.get("name") == "ETL Metrics Dashboard Data"
            for att in attachments
        ):
            attachments.append(
                {
                    "name": "ETL Metrics Dashboard Data",
                    "source": dashboard_filename,
                    "type": "application/json",
                }
            )
        result_file.write_text(json.dumps(result_data), encoding="utf-8")
        return


def _extract_allure_attachment_sources(payload):
    sources = set()

    def _visit(node):
        if isinstance(node, dict):
            source = node.get("source")
            if isinstance(source, str) and source:
                sources.add(source)
            for value in node.values():
                _visit(value)
        elif isinstance(node, list):
            for item in node:
                _visit(item)

    _visit(payload)
    return sources


def _extract_collected_csv_test_ids(items):
    test_ids = set()
    for item in items:
        callspec = getattr(item, "callspec", None)
        if not callspec:
            continue
        params = getattr(callspec, "params", {}) or {}
        test_case = params.get("test_case")
        if not isinstance(test_case, dict):
            continue
        test_id = str(test_case.get("test_id", "")).strip()
        if test_id:
            test_ids.add(test_id)
    return test_ids


def _result_matches_collected_test_ids(result_data, collected_test_ids):
    if not collected_test_ids:
        return False

    result_name = str(result_data.get("name", "")).strip()
    if any(result_name.startswith(f"{test_id}:") for test_id in collected_test_ids):
        return True

    parameters = result_data.get("parameters", [])
    for parameter in parameters:
        parameter_value = str(parameter.get("value", ""))
        for test_id in collected_test_ids:
            if f"'test_id': '{test_id}'" in parameter_value or f'"test_id": "{test_id}"' in parameter_value:
                return True

    return False


def _remove_stale_allure_results(results_dir, collected_test_ids):
    if not results_dir or not results_dir.exists() or not collected_test_ids:
        return

    for result_file in results_dir.glob("*-result.json"):
        try:
            result_data = json.loads(result_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not _result_matches_collected_test_ids(result_data, collected_test_ids):
            continue

        for attachment_source in _extract_allure_attachment_sources(result_data):
            attachment_path = results_dir / attachment_source
            if attachment_path.exists():
                try:
                    attachment_path.unlink()
                except Exception:
                    pass

        try:
            result_file.unlink()
        except Exception:
            pass


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    del session
    results_dir = _safe_get_allure_results_dir(config)
    if not results_dir:
        fallback = Path("reports/allure-results")
        if fallback.exists():
            results_dir = fallback

    collected_test_ids = _extract_collected_csv_test_ids(items)
    _remove_stale_allure_results(results_dir, collected_test_ids)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Create ETL dashboard JSON in allure-results and expose it as an attachment."""
    del exitstatus
    results_dir = _safe_get_allure_results_dir(session.config)
    if not results_dir:
        fallback = Path("reports/allure-results")
        if fallback.exists():
            results_dir = fallback
    if not results_dir or not results_dir.exists():
        return

    result_files = sorted(results_dir.glob("*-result.json"))
    if not result_files:
        return

    custom_input_path = results_dir / "etl-metrics-dashboard-input.json"
    payload = None
    if custom_input_path.exists():
        try:
            payload = json.loads(custom_input_path.read_text(encoding="utf-8"))
        except Exception:
            payload = None

    if payload is None:
        payload = _build_dashboard_payload(result_files)
    if not payload:
        return

    if isinstance(payload.get("records"), list):
        for pos, record in enumerate(payload["records"], start=1):
            if not record.get("testCase"):
                record["testCase"] = f"TEST_{pos:02d}"
            if not record.get("status"):
                record["status"] = "unknown"

    dashboard_filename = "etl-metrics-dashboard-attachment.json"
    dashboard_path = results_dir / dashboard_filename
    dashboard_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _attach_dashboard_payload(result_files, dashboard_filename)
