#!/usr/bin/env python3
"""
Generate a standalone HTML ETL metrics report for client sharing.

The output is a single self-contained HTML file that can be opened via
double-click (file://) without requiring a local server.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_TITLE = "ETL Validation Client Report"
STATUS_FAIL_SET = {"failed", "broken", "error"}
TESTCASE_PATTERN = re.compile(r"(TEST[_-]?\d+)", re.IGNORECASE)
FEATURE_CONFIG = {
    "CSV-Driven ETL Validation": {
        "slug": "bronze-to-silver",
        "title": "Bronze vs Silver Data Validation Checks",
        "source_label": "Bronze (Source)",
        "target_label": "Silver (Target)",
        "source_color": "bronze",
        "target_color": "silver",
    },
    "CSV-Driven Silver To Gold Validation": {
        "slug": "silver-to-gold",
        "title": "Silver vs Gold Data Validation Checks",
        "source_label": "Silver (Source)",
        "target_label": "Gold (Target)",
        "source_color": "silver",
        "target_color": "gold",
    },
}


def _safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _find_label_value(labels: List[Dict[str, Any]], key: str) -> Optional[str]:
    for label in labels:
        if str(label.get("name", "")) == key:
            raw = label.get("value")
            if raw is None:
                return None
            return str(raw)
    return None


def _normalize_record(record: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    target = record.get("target") if isinstance(record.get("target"), dict) else {}
    source_value = _as_float(source.get("value"))
    target_value = _as_float(target.get("value"))
    if source_value is None or target_value is None:
        return None

    test_case = str(record.get("testCase") or f"TEST_{index:02d}").strip() or f"TEST_{index:02d}"
    test_name = str(record.get("testName") or test_case).strip() or test_case
    status = str(record.get("status") or "unknown").strip().lower() or "unknown"

    return {
        "testCase": test_case,
        "testName": test_name,
        "status": status,
        "source": {
            "label": str(source.get("label") or "Bronze (Source)"),
            "table": str(source.get("table") or "N/A"),
            "lakehouse": str(source.get("lakehouse") or "N/A"),
            "validation": str(source.get("validation") or "N/A"),
            "value": source_value,
        },
        "target": {
            "label": str(target.get("label") or "Silver (Target)"),
            "table": str(target.get("table") or "N/A"),
            "lakehouse": str(target.get("lakehouse") or "N/A"),
            "validation": str(target.get("validation") or "N/A"),
            "value": target_value,
        },
    }


def _build_from_attachment(results_dir: Path) -> Optional[Dict[str, Any]]:
    attachment_path = results_dir / "etl-metrics-dashboard-attachment.json"
    payload = _safe_load_json(attachment_path)
    if not payload:
        return None

    records = payload.get("records")
    if not isinstance(records, list):
        return None

    normalized_records: List[Dict[str, Any]] = []
    for idx, item in enumerate(records, start=1):
        if not isinstance(item, dict):
            continue
        normalized = _normalize_record(item, idx)
        if normalized:
            normalized_records.append(normalized)

    if not normalized_records:
        return None

    return {
        "title": str(payload.get("title") or "Bronze vs Silver Data Validation Checks"),
        "xAxisTitle": str(payload.get("xAxisTitle") or "Test Cases"),
        "yAxisTitle": str(payload.get("yAxisTitle") or "Count"),
        "records": normalized_records,
        "sourceMode": "attachment",
    }


def _build_from_result_labels(results_dir: Path) -> Optional[Dict[str, Any]]:
    result_files = sorted(results_dir.glob("*-result.json"))
    sortable: List[Dict[str, Any]] = []

    for index, file_path in enumerate(result_files):
        data = _safe_load_json(file_path)
        if not data:
            continue

        labels = data.get("labels")
        if not isinstance(labels, list):
            continue

        source_count = _as_float(_find_label_value(labels, "Source_Count"))
        target_count = _as_float(_find_label_value(labels, "Target_Count"))
        if source_count is None or target_count is None:
            continue

        test_name = str(data.get("name") or "").strip()
        testcase_match = TESTCASE_PATTERN.search(test_name)
        test_case_id = testcase_match.group(1).upper().replace("-", "_") if testcase_match else None
        status = str(data.get("status") or "unknown").strip().lower() or "unknown"
        execution_start = data.get("start")
        if execution_start is None and isinstance(data.get("time"), dict):
            execution_start = data["time"].get("start")

        sortable.append(
            {
                "order": index,
                "start": execution_start if isinstance(execution_start, (int, float)) else None,
                "record": {
                    "testCase": test_case_id,
                    "testName": test_name or (test_case_id or ""),
                    "status": status,
                    "source": {
                        "label": "Bronze (Source)",
                        "table": _find_label_value(labels, "Table") or "N/A",
                        "lakehouse": _find_label_value(labels, "Source_Lakehouse") or "N/A",
                        "validation": _find_label_value(labels, "Validation") or "N/A",
                        "value": source_count,
                    },
                    "target": {
                        "label": "Silver (Target)",
                        "table": _find_label_value(labels, "Table") or "N/A",
                        "lakehouse": _find_label_value(labels, "Target_Lakehouse") or "N/A",
                        "validation": _find_label_value(labels, "Validation") or "N/A",
                        "value": target_count,
                    },
                },
            }
        )

    if not sortable:
        return None

    sortable.sort(key=lambda item: (item["start"] is None, item["start"] or 0, item["order"]))
    normalized_records: List[Dict[str, Any]] = []
    for idx, item in enumerate(sortable, start=1):
        normalized = _normalize_record(item["record"], idx)
        if normalized:
            normalized_records.append(normalized)

    if not normalized_records:
        return None

    return {
        "title": "Bronze vs Silver Data Validation Checks",
        "xAxisTitle": "Test Cases",
        "yAxisTitle": "Number of Lines (Count)",
        "records": normalized_records,
        "sourceMode": "labels",
    }


def _build_grouped_reports_from_result_labels(results_dir: Path) -> Dict[str, Dict[str, Any]]:
    result_files = sorted(results_dir.glob("*-result.json"))
    grouped_sortable: Dict[str, List[Dict[str, Any]]] = {}

    for index, file_path in enumerate(result_files):
        data = _safe_load_json(file_path)
        if not data:
            continue

        labels = data.get("labels")
        if not isinstance(labels, list):
            continue

        source_count = _as_float(_find_label_value(labels, "Source_Count"))
        target_count = _as_float(_find_label_value(labels, "Target_Count"))
        if source_count is None or target_count is None:
            continue

        feature_name = _find_label_value(labels, "feature") or "Fabric Validation"
        config = FEATURE_CONFIG.get(
            feature_name,
            {
                "slug": re.sub(r"[^a-z0-9]+", "-", feature_name.lower()).strip("-") or "fabric-validation",
                "title": feature_name,
                "source_label": "Source",
                "target_label": "Target",
            },
        )

        test_name = str(data.get("name") or "").strip()
        testcase_match = TESTCASE_PATTERN.search(test_name)
        test_case_id = testcase_match.group(1).upper().replace("-", "_") if testcase_match else None
        status = str(data.get("status") or "unknown").strip().lower() or "unknown"
        execution_start = data.get("start")
        if execution_start is None and isinstance(data.get("time"), dict):
            execution_start = data["time"].get("start")

        grouped_sortable.setdefault(config["slug"], []).append(
            {
                "order": index,
                "start": execution_start if isinstance(execution_start, (int, float)) else None,
                "config": config,
                "record": {
                    "testCase": test_case_id,
                    "testName": test_name or (test_case_id or ""),
                    "status": status,
                    "source": {
                        "label": config["source_label"],
                        "table": _find_label_value(labels, "Table") or "N/A",
                        "lakehouse": _find_label_value(labels, "Source_Lakehouse") or "N/A",
                        "validation": _find_label_value(labels, "Validation") or "N/A",
                        "value": source_count,
                    },
                    "target": {
                        "label": config["target_label"],
                        "table": _find_label_value(labels, "Table") or "N/A",
                        "lakehouse": _find_label_value(labels, "Target_Lakehouse") or "N/A",
                        "validation": _find_label_value(labels, "Validation") or "N/A",
                        "value": target_count,
                    },
                },
            }
        )

    report_payloads: Dict[str, Dict[str, Any]] = {}
    for slug, sortable in grouped_sortable.items():
        sortable.sort(key=lambda item: (item["start"] is None, item["start"] or 0, item["order"]))
        normalized_records: List[Dict[str, Any]] = []
        for idx, item in enumerate(sortable, start=1):
            normalized = _normalize_record(item["record"], idx)
            if normalized:
                normalized_records.append(normalized)

        if not normalized_records:
            continue

        config = sortable[0]["config"]
        report_payloads[slug] = {
            "title": config["title"],
            "records": normalized_records,
            "sourceMode": "labels",
            "sourceColor": config.get("source_color", "bronze"),
            "targetColor": config.get("target_color", "silver"),
        }

    return report_payloads


def _build_report_data(results_dir: Path, report_title: str) -> Dict[str, Any]:
    payload = _build_from_attachment(results_dir)
    if payload is None:
        payload = _build_from_result_labels(results_dir)

    records: List[Dict[str, Any]] = []
    data_source = "none"
    chart_title = "Bronze vs Silver Data Validation Checks"
    if payload:
        chart_title = payload.get("title", chart_title)
        records = payload.get("records", [])
        data_source = payload.get("sourceMode", "unknown")

    total = len(records)
    passed = sum(1 for row in records if row.get("status") == "passed")
    failed = sum(1 for row in records if str(row.get("status")) in STATUS_FAIL_SET)
    other = total - passed - failed

    return {
        "reportTitle": report_title,
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resultsDir": str(results_dir),
        "chartTitle": chart_title,
        "records": records,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "other": other,
        },
        "dataSource": data_source,
    }


def _build_report_data_from_payload(results_dir: Path, report_title: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    records = payload.get("records", [])
    total = len(records)
    passed = sum(1 for row in records if row.get("status") == "passed")
    failed = sum(1 for row in records if str(row.get("status")) in STATUS_FAIL_SET)
    other = total - passed - failed

    return {
        "reportTitle": report_title,
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resultsDir": str(results_dir),
        "chartTitle": payload.get("title", report_title),
        "records": records,
        "sourceColor": payload.get("sourceColor", "bronze"),
        "targetColor": payload.get("targetColor", "silver"),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "other": other,
        },
        "dataSource": payload.get("sourceMode", "labels"),
    }


def _render_multi_html(index_title: str, report_map: Dict[str, Dict[str, Any]]) -> str:
    serialized = json.dumps(report_map, ensure_ascii=True)
    ordered_keys = list(report_map.keys())
    default_key = ordered_keys[0] if ordered_keys else ""
    buttons_html = "\n".join(
        f'<button class="tab-btn{" active" if key == default_key else ""}" data-key="{key}">{report_map[key]["reportTitle"]}</button>'
        for key in ordered_keys
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{index_title}</title>
  <style>
    :root {{
      --bg: #eef3f8;
      --card: rgba(255, 255, 255, 0.84);
      --card-strong: #ffffff;
      --text: #13202c;
      --muted: #617181;
      --line: rgba(20, 32, 44, 0.09);
      --ok: #168a57;
      --bad: #cf3a35;
      --bronze: #b8742d;
      --silver: #7f8b98;
      --gold: #caa12a;
      --navy: #0f2741;
      --blue: #1b6fd8;
      --shadow: 0 18px 45px rgba(16, 37, 63, 0.09);
      --radius: 20px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(27, 111, 216, 0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(202, 161, 42, 0.12), transparent 24%),
        linear-gradient(180deg, #f8fbfe 0%, var(--bg) 100%);
      color: var(--text);
      overflow-x: hidden;
    }}
    .wrap {{ max-width: 1380px; margin: 0 auto; padding: clamp(16px, 2.4vw, 28px); }}
    .hero {{
      position: relative;
      overflow: hidden;
      background:
        linear-gradient(135deg, rgba(15, 39, 65, 0.96), rgba(23, 84, 152, 0.94));
      color: #ffffff;
      border-radius: 28px;
      padding: 28px 30px 24px;
      box-shadow: var(--shadow);
      margin-bottom: 20px;
    }}
    .hero:before {{
      content: "";
      position: absolute;
      inset: auto -8% -40% auto;
      width: 420px;
      height: 420px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255, 255, 255, 0.13), transparent 65%);
      pointer-events: none;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.6fr) minmax(280px, 1fr);
      gap: 18px;
      align-items: end;
      position: relative;
      z-index: 1;
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.09);
      border: 1px solid rgba(255, 255, 255, 0.14);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 14px;
    }}
    h1 {{
      margin: 0;
      font-size: 34px;
      line-height: 1.1;
      letter-spacing: -0.02em;
    }}
    .hero-meta {{
      margin-top: 12px;
      color: rgba(255, 255, 255, 0.78);
      font-size: 13px;
    }}
    .hero-aside {{
      display: flex;
      justify-content: flex-end;
      align-items: center;
      min-width: 0;
    }}
    .tabs {{
      display: inline-flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 18px;
      padding: 8px;
      backdrop-filter: blur(10px);
      max-width: 100%;
    }}
    .tab-btn {{
      border: 0;
      background: transparent;
      color: rgba(255, 255, 255, 0.76);
      padding: 12px 16px;
      border-radius: 12px;
      cursor: pointer;
      font-weight: 700;
      font-size: 13px;
      letter-spacing: 0.01em;
      transition: transform 140ms ease, background 140ms ease, color 140ms ease;
    }}
    .tab-btn:hover {{
      transform: translateY(-1px);
      background: rgba(255, 255, 255, 0.08);
      color: #ffffff;
    }}
    .tab-btn.active {{
      background: #ffffff;
      color: var(--navy);
      box-shadow: 0 8px 18px rgba(9, 25, 41, 0.18);
    }}
    .panel {{
      background: var(--card);
      backdrop-filter: blur(12px);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: var(--shadow);
      margin-bottom: 18px;
      min-width: 0;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(180px, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .stat {{
      position: relative;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px 16px 14px;
      background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(247,250,253,0.92));
      min-height: 110px;
    }}
    .stat:before {{
      content: "";
      position: absolute;
      inset: 0 auto auto 0;
      width: 100%;
      height: 4px;
      background: linear-gradient(90deg, rgba(15,39,65,0.14), rgba(15,39,65,0));
    }}
    .stat b {{
      display: block;
      font-size: 30px;
      line-height: 1;
      margin-top: 14px;
      letter-spacing: -0.03em;
    }}
    .stat span {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
    }}
    .ok b {{ color: var(--ok); }}
    .bad b {{ color: var(--bad); }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.9fr);
      gap: 18px;
      align-items: start;
    }}
    .panel-title {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 14px;
    }}
    .panel-title h2 {{
      margin: 0;
      font-size: 18px;
      letter-spacing: -0.01em;
    }}
    .panel-note {{
      color: var(--muted);
      font-size: 12px;
    }}
    .legend {{
      display: inline-flex;
      gap: 14px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
    }}
    .legend span {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
    }}
    .swatch {{
      width: 10px;
      height: 10px;
      border-radius: 999px;
      display: inline-block;
    }}
    .swatch.bronze {{ background: var(--bronze); }}
    .swatch.silver {{ background: var(--silver); }}
    .swatch.gold {{ background: var(--gold); }}
    .filters {{
      display: grid;
      grid-template-columns: 1.8fr 0.8fr;
      gap: 12px;
      margin-bottom: 14px;
    }}
    input, select {{
      width: 100%;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.95);
      color: var(--text);
      outline: none;
      font-size: 14px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
    }}
    input:focus, select:focus {{
      border-color: rgba(27,111,216,0.4);
      box-shadow: 0 0 0 4px rgba(27,111,216,0.12);
    }}
    .empty {{
      padding: 16px;
      border: 1px dashed var(--line);
      border-radius: 14px;
      color: var(--muted);
      background: rgba(255,255,255,0.6);
    }}
    .chart {{
      overflow-x: auto;
      padding-top: 8px;
      max-width: 100%;
      -webkit-overflow-scrolling: touch;
    }}
    .chart-grid {{
      display: flex;
      align-items: flex-end;
      gap: 16px;
      min-height: 320px;
      padding: 18px 10px 6px;
      width: max-content;
      min-width: 100%;
      background:
        linear-gradient(to top, rgba(15,39,65,0.04) 1px, transparent 1px) 0 100% / 100% 54px repeat-y;
      border-radius: 18px;
    }}
    .group {{
      min-width: 82px;
      background: rgba(255,255,255,0.55);
      border: 1px solid rgba(19,32,44,0.04);
      border-radius: 16px;
      padding: 10px 10px 8px;
    }}
    .bars {{
      display: flex;
      align-items: flex-end;
      justify-content: center;
      gap: 8px;
      height: 240px;
      border-bottom: 1px solid rgba(19,32,44,0.12);
      padding: 0 4px 8px;
    }}
    .bar {{
      width: 24px;
      border-radius: 10px 10px 4px 4px;
      position: relative;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.4), 0 10px 16px rgba(18,32,52,0.12);
      transition: transform 150ms ease, filter 150ms ease;
    }}
    .bar:hover {{
      transform: translateY(-3px);
      filter: saturate(1.08);
    }}
    .bar.bronze {{ background: linear-gradient(180deg, #d29756 0%, var(--bronze) 100%); }}
    .bar.silver {{ background: linear-gradient(180deg, #a8b1b9 0%, var(--silver) 100%); }}
    .bar.gold {{ background: linear-gradient(180deg, #e1c866 0%, var(--gold) 100%); }}
    .bar.bad {{ outline: 2px solid var(--bad); outline-offset: 1px; }}
    .bar:hover::after {{
      content: attr(data-tip);
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
      bottom: 100%;
      margin-bottom: 10px;
      white-space: nowrap;
      background: #0f1720;
      color: #fff;
      padding: 7px 9px;
      border-radius: 8px;
      font-size: 11px;
      z-index: 20;
      box-shadow: 0 10px 20px rgba(15, 23, 32, 0.22);
    }}
    .xlab {{
      font-size: 11px;
      text-align: center;
      margin-top: 8px;
      color: var(--muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-weight: 700;
    }}
    table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 13px;
      min-width: 900px;
    }}
    th, td {{
      padding: 12px 10px;
      border-bottom: 1px solid rgba(19,32,44,0.06);
      vertical-align: top;
      text-align: left;
    }}
    th {{
      background: rgba(245,248,252,0.96);
      color: #283746;
      font-weight: 600;
      position: sticky;
      top: 0;
      backdrop-filter: blur(10px);
      z-index: 1;
    }}
    tbody tr {{
      background: rgba(255,255,255,0.72);
    }}
    tbody tr:hover {{
      background: rgba(248,251,255,0.98);
    }}
    .status {{
      padding: 5px 9px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      display: inline-block;
      text-transform: uppercase;
    }}
    .s-passed {{ background: #ddf5e8; color: #1d7f49; }}
    .s-failed, .s-broken, .s-error {{ background: #fde3e3; color: #b43030; }}
    .s-other {{ background: #e9eef4; color: #4f5e6d; }}
    .table-wrap {{
      max-height: 620px;
      max-width: 100%;
      overflow: auto;
      -webkit-overflow-scrolling: touch;
      border: 1px solid rgba(19,32,44,0.05);
      border-radius: 18px;
      background: rgba(255,255,255,0.7);
    }}
    .name-cell {{
      min-width: 180px;
    }}
    .subtle {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
    }}
    @media (max-width: 1200px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .hero-grid {{ grid-template-columns: 1fr; }}
      .hero-aside {{ justify-content: flex-start; }}
    }}
    @media (max-width: 760px) {{
      .wrap {{ padding: 16px; }}
      h1 {{ font-size: 28px; }}
      .stats {{ grid-template-columns: repeat(2, minmax(140px, 1fr)); }}
      .filters {{ grid-template-columns: 1fr; }}
      .tabs {{ width: 100%; justify-content: stretch; }}
      .tab-btn {{ flex: 1 1 100%; text-align: center; }}
      .panel {{ padding: 16px; }}
      .group {{ min-width: 72px; }}
      .bars {{ height: 220px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div class="hero-grid">
        <div>
          <div class="eyebrow">Fabric Validation Dashboard</div>
          <h1 id="reportTitle">{index_title}</h1>
          <div class="hero-meta" id="reportMeta"></div>
        </div>
        <div class="hero-aside">
          <div class="tabs">
            {buttons_html}
          </div>
        </div>
      </div>
    </div>

    <div class="stats">
      <div class="stat"><span>Total Cases</span><b id="statTotal">0</b></div>
      <div class="stat ok"><span>Passed</span><b id="statPassed">0</b></div>
      <div class="stat bad"><span>Failed / Error</span><b id="statFailed">0</b></div>
      <div class="stat"><span>Other Status</span><b id="statOther">0</b></div>
    </div>

    <div class="layout">
      <div class="panel">
        <div class="panel-title">
          <div>
            <h2 id="chartTitle"></h2>
            <div class="panel-note">Interactive volume comparison across executed validation cases</div>
          </div>
          <div class="legend">
            <span><i class="swatch bronze"></i> Bronze</span>
            <span><i class="swatch silver"></i> Silver</span>
            <span><i class="swatch gold"></i> Gold</span>
          </div>
        </div>
        <div id="chartContainer" class="chart"></div>
      </div>

      <div class="panel">
        <div class="panel-title">
          <div>
            <h2>Validation Details</h2>
            <div class="panel-note">Filterable execution summary for client review and audit</div>
          </div>
        </div>
        <div class="filters">
          <input id="searchInput" placeholder="Search by test case, test name, table, or lakehouse">
          <select id="statusFilter">
            <option value="">All statuses</option>
            <option value="passed">passed</option>
            <option value="failed">failed</option>
            <option value="broken">broken</option>
            <option value="error">error</option>
            <option value="unknown">unknown</option>
          </select>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Test Case</th>
                <th>Status</th>
                <th>Table</th>
                <th>Source</th>
                <th>Target</th>
                <th>Validation</th>
                <th>Source Count</th>
                <th>Target Count</th>
                <th>Delta</th>
              </tr>
            </thead>
            <tbody id="rows"></tbody>
          </table>
        </div>
        <div id="emptyTable" class="empty" style="display:none; margin-top:10px;">
          No rows match your current filters.
        </div>
      </div>
    </div>
  </div>

  <script>
    (function () {{
      var REPORTS = {serialized};
      var activeKey = "{default_key}";

      function currentReport() {{
        return REPORTS[activeKey] || {{ records: [], summary: {{}} }};
      }}

      function setText(id, value) {{
        var node = document.getElementById(id);
        if (node) node.textContent = value;
      }}

      function statusClass(status) {{
        var s = String(status || "unknown").toLowerCase();
        if (s === "passed") return "s-passed";
        if (s === "failed" || s === "broken" || s === "error") return "s-failed";
        return "s-other";
      }}

      function toNumber(v) {{
        var n = Number(v);
        return isNaN(n) ? 0 : n;
      }}

      function formatValue(v) {{
        var n = toNumber(v);
        if (Math.abs(n - Math.round(n)) < 0.000001) {{
          return String(Math.round(n));
        }}
        return n.toFixed(2);
      }}

      function renderHeader() {{
        var report = currentReport();
        setText(
          "reportMeta",
          "Generated: " + (report.generatedAt || "") +
          " | Source: " + (report.resultsDir || "") +
          " | Data mode: " + (report.dataSource || "none")
        );

        var summary = report.summary || {{}};
        setText("statTotal", String(summary.total || 0));
        setText("statPassed", String(summary.passed || 0));
        setText("statFailed", String(summary.failed || 0));
        setText("statOther", String(summary.other || 0));
        setText("chartTitle", report.chartTitle || report.reportTitle || "ETL Validation");
      }}

      function renderChart(rows) {{
        var container = document.getElementById("chartContainer");
        if (!container) return;
        container.innerHTML = "";
        var report = currentReport();
        var sourceColor = report.sourceColor || "bronze";
        var targetColor = report.targetColor || "silver";

        if (!rows.length) {{
          container.innerHTML = '<div class="empty">No ETL metrics data available.</div>';
          return;
        }}

        var maxValue = 1;
        rows.forEach(function (r) {{
          maxValue = Math.max(maxValue, toNumber(r.source.value), toNumber(r.target.value));
        }});

        var grid = document.createElement("div");
        grid.className = "chart-grid";

        rows.forEach(function (r) {{
          var sourceVal = toNumber(r.source.value);
          var targetVal = toNumber(r.target.value);
          var isBad = ["failed", "broken", "error"].indexOf(String(r.status).toLowerCase()) >= 0;

          var group = document.createElement("div");
          group.className = "group";

          var bars = document.createElement("div");
          bars.className = "bars";

          var sourceBar = document.createElement("div");
          sourceBar.className = "bar " + sourceColor + (isBad ? " bad" : "");
          sourceBar.style.height = Math.max(2, Math.round((sourceVal / maxValue) * 210)) + "px";
          sourceBar.setAttribute("data-tip", "Source: " + formatValue(sourceVal));

          var targetBar = document.createElement("div");
          targetBar.className = "bar " + targetColor + (isBad ? " bad" : "");
          targetBar.style.height = Math.max(2, Math.round((targetVal / maxValue) * 210)) + "px";
          targetBar.setAttribute("data-tip", "Target: " + formatValue(targetVal));

          bars.appendChild(sourceBar);
          bars.appendChild(targetBar);

          var label = document.createElement("div");
          label.className = "xlab";
          label.textContent = r.testCase || "";
          label.title = r.testName || r.testCase || "";

          group.appendChild(bars);
          group.appendChild(label);
          grid.appendChild(group);
        }});

        container.appendChild(grid);
      }}

      function filterRows() {{
        var report = currentReport();
        var records = Array.isArray(report.records) ? report.records.slice() : [];
        var searchValue = (document.getElementById("searchInput").value || "").trim().toLowerCase();
        var statusValue = (document.getElementById("statusFilter").value || "").trim().toLowerCase();

        return records.filter(function (row) {{
          var rowStatus = String(row.status || "").toLowerCase();
          if (statusValue && rowStatus !== statusValue) {{
            return false;
          }}

          if (!searchValue) {{
            return true;
          }}

          var haystack = [
            row.testCase,
            row.testName,
            row.status,
            row.source && row.source.table,
            row.source && row.source.lakehouse,
            row.target && row.target.lakehouse,
            row.source && row.source.validation
          ].join(" ").toLowerCase();

          return haystack.indexOf(searchValue) >= 0;
        }});
      }}

      function renderTable(rows) {{
        var tbody = document.getElementById("rows");
        var empty = document.getElementById("emptyTable");
        tbody.innerHTML = "";

        if (!rows.length) {{
          empty.style.display = "block";
          return;
        }}
        empty.style.display = "none";

        rows.forEach(function (r) {{
          var delta = toNumber(r.target.value) - toNumber(r.source.value);
          var tr = document.createElement("tr");
          tr.innerHTML =
            "<td class='name-cell'>" + (r.testCase || "") + "<div class='subtle'>" + (r.testName || "") + "</div></td>" +
            "<td><span class='status " + statusClass(r.status) + "'>" + (r.status || "unknown") + "</span></td>" +
            "<td>" + (r.source.table || "N/A") + "</td>" +
            "<td>" + (r.source.lakehouse || "N/A") + "</td>" +
            "<td>" + (r.target.lakehouse || "N/A") + "</td>" +
            "<td>" + (r.source.validation || "N/A") + "</td>" +
            "<td>" + formatValue(r.source.value) + "</td>" +
            "<td>" + formatValue(r.target.value) + "</td>" +
            "<td>" + formatValue(delta) + "</td>";
          tbody.appendChild(tr);
        }});
      }}

      function refresh() {{
        renderHeader();
        var rows = filterRows();
        renderChart(rows);
        renderTable(rows);
      }}

      function selectTab(key) {{
        activeKey = key;
        var buttons = document.querySelectorAll(".tab-btn");
        buttons.forEach(function (btn) {{
          btn.classList.toggle("active", btn.getAttribute("data-key") === key);
        }});
        refresh();
      }}

      document.querySelectorAll(".tab-btn").forEach(function (btn) {{
        btn.addEventListener("click", function () {{
          selectTab(btn.getAttribute("data-key"));
        }});
      }});

      document.getElementById("searchInput").addEventListener("input", refresh);
      document.getElementById("statusFilter").addEventListener("change", refresh);
      refresh();
    }})();
  </script>
</body>
</html>
"""


def _render_html(report_data: Dict[str, Any]) -> str:
    serialized = json.dumps(report_data, ensure_ascii=True)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{report_data["reportTitle"]}</title>
  <style>
    :root {{
      --bg: #f2f4f8;
      --card: #ffffff;
      --text: #16202a;
      --muted: #5f6b76;
      --line: #d9e1ea;
      --ok: #1f8f52;
      --bad: #c43636;
      --bronze: #b9772c;
      --silver: #818b96;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      background: linear-gradient(180deg, #f9fafc 0%, var(--bg) 100%);
      color: var(--text);
      overflow-x: hidden;
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: clamp(16px, 2.2vw, 20px); }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 6px 18px rgba(9, 30, 66, 0.07);
      margin-bottom: 16px;
      min-width: 0;
    }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 10px;
      margin-top: 12px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 12px;
      background: #fbfcfe;
    }}
    .stat b {{ display: block; font-size: 22px; }}
    .stat span {{ color: var(--muted); font-size: 12px; }}
    .ok b {{ color: var(--ok); }}
    .bad b {{ color: var(--bad); }}
    .filters {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 10px;
      margin-top: 10px;
    }}
    input, select {{
      width: 100%;
      padding: 10px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
    }}
    .empty {{
      padding: 16px;
      border: 1px dashed var(--line);
      border-radius: 8px;
      color: var(--muted);
      background: #fcfdff;
    }}
    .chart {{
      overflow-x: auto;
      padding-top: 6px;
      max-width: 100%;
      -webkit-overflow-scrolling: touch;
    }}
    .chart-grid {{
      display: flex;
      align-items: flex-end;
      gap: 12px;
      min-height: 280px;
      padding: 12px 6px 0;
      width: max-content;
      min-width: 100%;
    }}
    .group {{ min-width: 70px; }}
    .bars {{
      display: flex;
      align-items: flex-end;
      gap: 5px;
      height: 220px;
      border-bottom: 1px solid #bcc8d3;
      padding-bottom: 4px;
    }}
    .bar {{
      width: 22px;
      border-radius: 4px 4px 0 0;
      position: relative;
    }}
    .bar.bronze {{ background: var(--bronze); }}
    .bar.silver {{ background: var(--silver); }}
    .bar.bad {{ outline: 2px solid var(--bad); }}
    .bar:hover::after {{
      content: attr(data-tip);
      position: absolute;
      left: -18px;
      bottom: 100%;
      margin-bottom: 6px;
      white-space: nowrap;
      background: #0f1720;
      color: #fff;
      padding: 4px 7px;
      border-radius: 6px;
      font-size: 11px;
      z-index: 20;
    }}
    .xlab {{
      font-size: 11px;
      text-align: center;
      margin-top: 5px;
      color: var(--muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      min-width: 900px;
    }}
    .table-wrap {{
      margin-top: 12px;
      max-width: 100%;
      max-height: 420px;
      overflow: auto;
      -webkit-overflow-scrolling: touch;
    }}
    th, td {{
      padding: 8px;
      border-bottom: 1px solid #ebf0f5;
      vertical-align: top;
      text-align: left;
    }}
    th {{
      background: #f7f9fc;
      color: #283746;
      font-weight: 600;
      position: sticky;
      top: 0;
    }}
    .status {{
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      display: inline-block;
      text-transform: uppercase;
    }}
    .s-passed {{ background: #ddf5e8; color: #1d7f49; }}
    .s-failed, .s-broken, .s-error {{ background: #fde3e3; color: #b43030; }}
    .s-other {{ background: #e9eef4; color: #4f5e6d; }}
    @media (max-width: 760px) {{
      .wrap {{ padding: 14px; }}
      .stats {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      .filters {{ grid-template-columns: 1fr; }}
      .panel {{ padding: 14px; }}
      .group {{ min-width: 64px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <h1 id="reportTitle"></h1>
      <div class="meta" id="reportMeta"></div>
      <div class="stats">
        <div class="stat"><b id="statTotal">0</b><span>Total Cases</span></div>
        <div class="stat ok"><b id="statPassed">0</b><span>Passed</span></div>
        <div class="stat bad"><b id="statFailed">0</b><span>Failed/Broken/Error</span></div>
        <div class="stat"><b id="statOther">0</b><span>Other Status</span></div>
      </div>
    </div>

    <div class="panel">
      <h2 id="chartTitle" style="margin:0 0 6px;font-size:18px;"></h2>
      <div id="chartContainer" class="chart"></div>
    </div>

    <div class="panel">
      <div class="filters">
        <input id="searchInput" placeholder="Search by test case, test name, table, or lakehouse">
        <select id="statusFilter">
          <option value="">All statuses</option>
          <option value="passed">passed</option>
          <option value="failed">failed</option>
          <option value="broken">broken</option>
          <option value="error">error</option>
          <option value="unknown">unknown</option>
        </select>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Test Case</th>
              <th>Status</th>
              <th>Table</th>
              <th>Source</th>
              <th>Target</th>
              <th>Validation</th>
              <th>Source Count</th>
              <th>Target Count</th>
              <th>Delta</th>
            </tr>
          </thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
      <div id="emptyTable" class="empty" style="display:none; margin-top:10px;">
        No rows match your current filters.
      </div>
    </div>
  </div>

  <script>
    (function () {{
      var DATA = {serialized};
      var records = Array.isArray(DATA.records) ? DATA.records.slice() : [];

      function setText(id, value) {{
        var node = document.getElementById(id);
        if (node) node.textContent = value;
      }}

      function statusClass(status) {{
        var s = String(status || "unknown").toLowerCase();
        if (s === "passed") return "s-passed";
        if (s === "failed" || s === "broken" || s === "error") return "s-failed";
        return "s-other";
      }}

      function toNumber(v) {{
        var n = Number(v);
        return isNaN(n) ? 0 : n;
      }}

      function formatValue(v) {{
        var n = toNumber(v);
        if (Math.abs(n - Math.round(n)) < 0.000001) {{
          return String(Math.round(n));
        }}
        return n.toFixed(2);
      }}

      function renderHeader() {{
        setText("reportTitle", DATA.reportTitle || "ETL Validation Client Report");
        setText(
          "reportMeta",
          "Generated: " + (DATA.generatedAt || "") +
          " | Source: " + (DATA.resultsDir || "") +
          " | Data mode: " + (DATA.dataSource || "none")
        );

        var summary = DATA.summary || {{}};
        setText("statTotal", String(summary.total || 0));
        setText("statPassed", String(summary.passed || 0));
        setText("statFailed", String(summary.failed || 0));
        setText("statOther", String(summary.other || 0));
        setText("chartTitle", DATA.chartTitle || "Bronze vs Silver Data Validation Checks");
      }}

      function renderChart(rows) {{
        var container = document.getElementById("chartContainer");
        if (!container) return;
        container.innerHTML = "";

        if (!rows.length) {{
          container.innerHTML = '<div class="empty">No ETL metrics data available.</div>';
          return;
        }}

        var maxValue = 1;
        rows.forEach(function (r) {{
          maxValue = Math.max(maxValue, toNumber(r.source.value), toNumber(r.target.value));
        }});

        var grid = document.createElement("div");
        grid.className = "chart-grid";

        rows.forEach(function (r) {{
          var sourceVal = toNumber(r.source.value);
          var targetVal = toNumber(r.target.value);
          var isBad = ["failed", "broken", "error"].indexOf(String(r.status).toLowerCase()) >= 0;

          var group = document.createElement("div");
          group.className = "group";

          var bars = document.createElement("div");
          bars.className = "bars";

          var sourceBar = document.createElement("div");
          sourceBar.className = "bar bronze" + (isBad ? " bad" : "");
          sourceBar.style.height = Math.max(2, Math.round((sourceVal / maxValue) * 210)) + "px";
          sourceBar.setAttribute("data-tip", "Source: " + formatValue(sourceVal));

          var targetBar = document.createElement("div");
          targetBar.className = "bar silver" + (isBad ? " bad" : "");
          targetBar.style.height = Math.max(2, Math.round((targetVal / maxValue) * 210)) + "px";
          targetBar.setAttribute("data-tip", "Target: " + formatValue(targetVal));

          bars.appendChild(sourceBar);
          bars.appendChild(targetBar);

          var label = document.createElement("div");
          label.className = "xlab";
          label.textContent = r.testCase || "";
          label.title = r.testName || r.testCase || "";

          group.appendChild(bars);
          group.appendChild(label);
          grid.appendChild(group);
        }});

        container.appendChild(grid);
      }}

      function filterRows() {{
        var searchValue = (document.getElementById("searchInput").value || "").trim().toLowerCase();
        var statusValue = (document.getElementById("statusFilter").value || "").trim().toLowerCase();

        return records.filter(function (row) {{
          var rowStatus = String(row.status || "").toLowerCase();
          if (statusValue && rowStatus !== statusValue) {{
            return false;
          }}

          if (!searchValue) {{
            return true;
          }}

          var haystack = [
            row.testCase,
            row.testName,
            row.status,
            row.source && row.source.table,
            row.source && row.source.lakehouse,
            row.target && row.target.lakehouse,
            row.source && row.source.validation
          ].join(" ").toLowerCase();

          return haystack.indexOf(searchValue) >= 0;
        }});
      }}

      function renderTable(rows) {{
        var tbody = document.getElementById("rows");
        var empty = document.getElementById("emptyTable");
        tbody.innerHTML = "";

        if (!rows.length) {{
          empty.style.display = "block";
          return;
        }}
        empty.style.display = "none";

        rows.forEach(function (r) {{
          var delta = toNumber(r.target.value) - toNumber(r.source.value);
          var tr = document.createElement("tr");
          tr.innerHTML =
            "<td>" + (r.testCase || "") + "<br><span style='color:#5f6b76'>" + (r.testName || "") + "</span></td>" +
            "<td><span class='status " + statusClass(r.status) + "'>" + (r.status || "unknown") + "</span></td>" +
            "<td>" + (r.source.table || "N/A") + "</td>" +
            "<td>" + (r.source.lakehouse || "N/A") + "</td>" +
            "<td>" + (r.target.lakehouse || "N/A") + "</td>" +
            "<td>" + (r.source.validation || "N/A") + "</td>" +
            "<td>" + formatValue(r.source.value) + "</td>" +
            "<td>" + formatValue(r.target.value) + "</td>" +
            "<td>" + formatValue(delta) + "</td>";
          tbody.appendChild(tr);
        }});
      }}

      function refresh() {{
        var rows = filterRows();
        renderChart(rows);
        renderTable(rows);
      }}

      renderHeader();
      refresh();
      document.getElementById("searchInput").addEventListener("input", refresh);
      document.getElementById("statusFilter").addEventListener("change", refresh);
    }})();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[1]
    default_results = repo_root / "reports" / "allure-results"
    default_output = repo_root / "reports" / "client-report" / "index.html"

    parser = argparse.ArgumentParser(description="Generate standalone client ETL HTML report")
    parser.add_argument("--results-dir", default=str(default_results), help="Path to allure-results folder")
    parser.add_argument("--output", default=str(default_output), help="Output HTML file path")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Top-level report title")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results_dir = Path(args.results_dir).resolve()
    output_path = Path(args.output).resolve()

    if not results_dir.exists():
        print(f"[ERROR] Results directory not found: {results_dir}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    grouped_payloads = _build_grouped_reports_from_result_labels(results_dir)

    if grouped_payloads:
        report_map: Dict[str, Dict[str, Any]] = {}
        for slug, payload in grouped_payloads.items():
            report_title = payload.get("title", slug)
            report_data = _build_report_data_from_payload(results_dir, report_title, payload)
            report_map[slug] = report_data
            print(f"[OK] Loaded report dataset: {report_title}")
            print(f"[INFO] Records included: {report_data['summary']['total']}")
            print(f"[INFO] Data source mode: {report_data['dataSource']}")

        output_path.write_text(
            _render_multi_html(args.title, report_map),
            encoding="utf-8",
        )
        print(f"[OK] Combined client report generated: {output_path}")
        return 0

    report_data = _build_report_data(results_dir, args.title)
    output_path.write_text(_render_html(report_data), encoding="utf-8")

    print(f"[OK] Standalone client report generated: {output_path}")
    print(f"[INFO] Records included: {report_data['summary']['total']}")
    print(f"[INFO] Data source mode: {report_data['dataSource']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
