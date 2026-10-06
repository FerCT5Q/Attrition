"""Freeze aggregate evidence for the V8 IOS trailing-12-month slide.

The input is the JSON returned by the guarded Redshift read-only helper.  It
contains aggregate group rows only; this script validates the temporal contract
and saves a compact evidence artifact without employee records or identifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "v8_ios_movement_reason_trailing_12m_attrition_20260923.sql"
METADATA_QUERY = ROOT / "queries" / "audits" / "v8_ios_movement_reason_trailing_12m_metadata_preflight_20260923.sql"
AUTHORIZATION = ROOT / "config" / "attrition_v8_internal_analysis_authorization_20260923.json"
DEFAULT_OUTPUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v8.ios-movement-reasons-trailing-12m-evidence-20260923.json"

GROUPS = (
    (0, "total", "All eligible IOS movements", "All IOS movements"),
    (1, "reorg_manager_change", "Transfer > Transfer > Reorg Department and/or Manager Change", "Reorg / manager change"),
    (2, "lateral_ios", "Transfer > Transfer > Lateral IOS", "Lateral IOS"),
    (3, "country_move", "Transfer > Transfer > Country-to-Country Location Change", "Country-to-country move"),
    (4, "promo_ios", "Promotion > Transfer > Promo IOS", "Promo IOS"),
    (5, "immigration_parking", "Transfer > Transfer > Immigration Parking", "Immigration parking"),
    (6, "downlevel_ios", "Demotion > Transfer > Downlevel IOS", "Downlevel IOS"),
)
REQUIRED_COLUMNS = {
    "display_order",
    "group_label",
    "current_active_regular_employees",
    "current_cohort_n",
    "current_workforce_share_percent",
    "baseline_active_regular_employees",
    "baseline_cohort_n",
    "annual_voluntary_exit_n",
    "annual_voluntary_attrition_percent",
    "publication_status",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def integer(value: Any) -> int:
    return int(float(value))


def decimal(value: Any) -> float:
    return float(value)


def load_source(path: str) -> tuple[dict[str, Any], bytes]:
    raw = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    return json.loads(raw), raw


def validate(source: dict[str, Any]) -> list[dict[str, Any]]:
    if source.get("truncated"):
        raise ValueError("The guarded query result is truncated.")
    if not REQUIRED_COLUMNS.issubset(set(source.get("columns", []))):
        raise ValueError("The guarded query result does not satisfy the IOS trailing-12-month contract.")
    raw_rows = source.get("rows")
    if not isinstance(raw_rows, list) or len(raw_rows) != len(GROUPS):
        raise ValueError("Expected exactly seven IOS reason aggregate rows.")

    expected = {order: (key, label, short) for order, key, label, short in GROUPS}
    result: list[dict[str, Any]] = []
    for raw in raw_rows:
        order = integer(raw["display_order"])
        if order not in expected:
            raise ValueError("Unexpected IOS display order.")
        key, label, short = expected[order]
        if str(raw["group_label"]) != label:
            raise ValueError("Unexpected IOS group label.")
        current_population = integer(raw["current_active_regular_employees"])
        current_count = integer(raw["current_cohort_n"])
        current_share = decimal(raw["current_workforce_share_percent"])
        baseline_population = integer(raw["baseline_active_regular_employees"])
        baseline_count = integer(raw["baseline_cohort_n"])
        exits = integer(raw["annual_voluntary_exit_n"])
        rate = decimal(raw["annual_voluntary_attrition_percent"])
        status = str(raw["publication_status"])
        if current_population != 50_043 or baseline_population != 45_003:
            raise ValueError("IOS active-Regular population does not match the V8 snapshots.")
        if not 0 <= current_count <= current_population or not 0 <= baseline_count <= baseline_population:
            raise ValueError("IOS cohort count is outside its active-Regular population.")
        if not 0 <= exits <= baseline_count:
            raise ValueError("IOS annual voluntary exits exceed the baseline cohort.")
        if abs(current_share - round(100.0 * current_count / current_population, 2)) > 0.000001:
            raise ValueError("IOS current workforce share does not reconcile.")
        if abs(rate - round(100.0 * exits / baseline_count, 2)) > 0.000001:
            raise ValueError("IOS annual voluntary attrition does not reconcile.")
        expected_status = "publish" if baseline_count >= 30 else "internal_analysis_exception"
        if status != expected_status:
            raise ValueError("IOS publication status does not match baseline cohort policy.")
        result.append(
            {
                "display_order": order,
                "group_key": key,
                "group_label": label,
                "short_label": short,
                "current_cohort_n": current_count,
                "current_workforce_share_percent": current_share,
                "baseline_cohort_n": baseline_count,
                "annual_voluntary_exit_n": exits,
                "annual_voluntary_attrition_percent": rate,
                "publication_status": status,
            }
        )
    result.sort(key=lambda row: int(row["display_order"]))
    if [row["group_key"] for row in result] != [group[1] for group in GROUPS]:
        raise ValueError("IOS groups are incomplete or duplicate.")
    total = result[0]
    if any(int(row["current_cohort_n"]) > int(total["current_cohort_n"]) for row in result[1:]):
        raise ValueError("An IOS reason exceeds the all-movements deduplicated total.")
    return result


def build(source: dict[str, Any], raw: bytes) -> dict[str, Any]:
    rows = validate(source)
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    if authorization.get("status") != "approved" or authorization.get("reporting_mode") != "internal_analysis":
        raise ValueError("The V8 internal-analysis authorization is not approved.")
    payload = {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 8,
        "artifact_classification": "internal_analysis",
        "deliverable_mode": "internal_analysis",
        "variable": "IOS movement reason in trailing 12 months",
        "semantic_type": "derived_feature",
        "execution_date": date.today().isoformat(),
        "current_snapshot_date": "2026-08-23",
        "baseline_snapshot_date": "2025-08-24",
        "outcome_cutoff_date": "2026-08-23",
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1",
        "grain": "Distinct active Regular employee per snapshot and IOS reason; all-movements total is deduplicated by employee.",
        "definition": {
            "current_distribution": "At least one IOS record with a known business_process_reason in (2025-08-23, 2026-08-23] for the active Regular employee at the current snapshot.",
            "annual_attrition": "The matching feature in (2024-08-24, 2025-08-24] for the active Regular baseline, followed for strict VOLUNTARY exits in (2025-08-24, 2026-08-23].",
            "overlap": "Reason rows can overlap and must not be added. All eligible IOS movements is deduplicated by employee.",
        },
        "metrics": {
            "current_active_regular_employee_count": 50_043,
            "baseline_active_regular_employee_count": 45_003,
            "current_all_ios_movement_count": rows[0]["current_cohort_n"],
            "baseline_all_ios_movement_count": rows[0]["baseline_cohort_n"],
            "baseline_all_ios_voluntary_exit_count": rows[0]["annual_voluntary_exit_n"],
            "minimum_standard_cohort": 30,
        },
        "rows": rows,
        "validation": {
            "outcome": "pass",
            "acceptance_rule": "Seven unique aggregate rows reconcile to the two active-Regular snapshots; every annual exit count is within its baseline cohort and every published rate equals exits divided by that cohort.",
            "reason_rows_overlap": True,
        },
        "provenance": {
            "metadata_sql": str(METADATA_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "metadata_sql_sha256": sha256_bytes(METADATA_QUERY.read_bytes()),
            "main_sql": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
            "main_sql_sha256": sha256_bytes(QUERY.read_bytes()),
            "aggregate_result_sha256": sha256_bytes(raw),
            "raw_aggregate_rows_persisted": False,
        },
        "authorization": {
            "path": str(AUTHORIZATION.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_bytes(AUTHORIZATION.read_bytes()),
            "authorization_id": authorization["authorization_id"],
        },
        "privacy_checks": {
            "employee_rows_persisted": False,
            "employee_ids_persisted": False,
            "names_persisted": False,
            "exact_compensation_values_persisted": False,
            "small_cell_exception_used": any(row["publication_status"] == "internal_analysis_exception" for row in rows),
        },
        "score_v4_change": "none",
        "limitation": "The source records IOS business-process reasons. It does not establish that an IOS movement caused attrition; the annual label follows the earlier baseline cohort and should not be read as a causal effect.",
        "outcome": "pass",
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze V8 IOS trailing-12-month aggregate evidence.")
    parser.add_argument("--input", default="-", help="Guarded read-only query JSON path, or - for stdin.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    source, raw = load_source(args.input)
    payload = build(source, raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
