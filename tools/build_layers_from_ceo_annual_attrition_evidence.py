"""Freeze aggregate annual attrition evidence for slide 32.

Each baseline employee is assigned one reconstructed manager-chain depth at
2025-08-24. The same baseline employees are checked for a strict VOLUNTARY
termination through 2026-08-23. No employee-level rows or identifiers are
returned or persisted.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SQL = ROOT / "queries" / "audits" / "layers_from_ceo_annual_attrition_20260921.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "layers-from-ceo-annual-attrition-evidence-20260921.json"
BASELINE_DATE = "2025-08-24"
OUTCOME_CUTOFF = "2026-08-23"
OUTCOME_WINDOW = "(2025-08-24, 2026-08-23]"
MINIMUM_COHORT = 30
MAXIMUM_CHAIN_LINKS = 25
READONLY_QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"

REQUIRED_METRICS = {
    "active_source_row_count", "universe_node_count", "duplicate_source_node_count",
    "manager_conflict_node_count", "self_manager_node_count", "stored_level_conflict_node_count",
    "reconstructed_count", "unresolved_chain_count", "missing_manager_chain_count",
    "self_manager_chain_count", "cycle_chain_count", "depth_exceeded_chain_count",
    "manager_conflict_chain_count", "root_count", "approved_root_resolved_count",
    "nonmatching_approved_root_count", "maximum_observed_depth", "convergence_rate_percent",
    "root_reference_pass", "display_eligible_count", "display_reconstructed_count",
    "display_unresolved_chain_count", "display_approved_root_match_count",
    "stored_level_comparable_count", "stored_level_depth_plus_one_match_count",
    "stored_level_depth_plus_one_match_rate_percent", "maximum_chain_links",
    "baseline_voluntary_exits", "voluntary_source_distinct_employee_count",
}
INTEGER_METRICS = REQUIRED_METRICS - {
    "convergence_rate_percent", "stored_level_depth_plus_one_match_rate_percent",
}


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_json(value: object) -> str:
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=True, default=str, separators=(",", ":")).encode("utf-8"))


def load_helper() -> Any:
    spec = importlib.util.spec_from_file_location("layers_annual_readonly_helper", READONLY_QUERY_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load the read-only helper: {READONLY_QUERY_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute_query() -> tuple[list[dict[str, Any]], str, str]:
    sql = AUDIT_SQL.read_text(encoding="utf-8")
    helper = load_helper()
    readonly_sql = helper.validate_readonly(sql)
    with helper.connect() as connection:
        connection.autocommit = True
        with connection.cursor(cursor_factory=helper.psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(readonly_sql)
            rows = [dict(row) for row in cursor.fetchall()]
    return rows, digest(sql.encode("utf-8")), hash_json(rows)


def integer(value: object, name: str) -> int:
    number = float(value)
    if not number.is_integer():
        raise ValueError(f"Metric {name!r} must be an integer.")
    return int(number)


def parse_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, float], list[dict[str, int | float]]]:
    expected = {
        "row_type", "metric", "depth", "metric_value", "employee_count",
        "voluntary_exits", "annual_attrition_rate_percent",
    }
    metrics: dict[str, float] = {}
    distribution: list[dict[str, int | float]] = []
    for row in rows:
        if set(row) != expected:
            raise ValueError(f"Unexpected aggregate schema: {sorted(row)}")
        if row["row_type"] == "metric":
            metric = str(row["metric"])
            if row["depth"] is not None or row["metric_value"] is None or metric in metrics:
                raise ValueError("Annual hierarchy metric rows are not unique and complete.")
            metrics[metric] = float(row["metric_value"])
        elif row["row_type"] == "depth_distribution":
            if row["metric"] != "display_employee_count" or row["depth"] is None:
                raise ValueError("Annual hierarchy depth row is invalid.")
            distribution.append({
                "depth": integer(row["depth"], "depth"),
                "employee_count": integer(row["employee_count"], "employee_count"),
                "voluntary_exits": integer(row["voluntary_exits"], "voluntary_exits"),
                "annual_attrition_rate_percent": float(row["annual_attrition_rate_percent"] or 0),
            })
        else:
            raise ValueError(f"Unknown aggregate row type: {row['row_type']!r}.")
    missing = sorted(REQUIRED_METRICS - set(metrics))
    extra = sorted(set(metrics) - REQUIRED_METRICS)
    if missing or extra:
        raise ValueError(f"Annual hierarchy metric contract mismatch; missing={missing}, extra={extra}.")
    distribution.sort(key=lambda row: int(row["depth"]))
    if not distribution or len({int(row["depth"]) for row in distribution}) != len(distribution):
        raise ValueError("Annual hierarchy depth distribution is empty or duplicated.")
    return metrics, distribution


def pool_depths(raw: list[dict[str, int | float]]) -> list[dict[str, object]]:
    depths = [int(row["depth"]) for row in raw]
    if depths[0] < 0 or any(right != left + 1 for left, right in zip(depths, depths[1:])):
        raise ValueError("Depth buckets must be non-negative and contiguous.")
    bands = [[int(row["depth"]), int(row["depth"]), int(row["employee_count"]), int(row["voluntary_exits"])] for row in raw]

    def merge(first: int, second: int) -> None:
        bands[first][1] = bands[second][1]
        bands[first][2] += bands[second][2]
        bands[first][3] += bands[second][3]
        del bands[second]

    while len(bands) > 1 and bands[0][2] < MINIMUM_COHORT:
        merge(0, 1)
    while len(bands) > 1 and bands[-1][2] < MINIMUM_COHORT:
        merge(len(bands) - 2, len(bands) - 1)
    while len(bands) > 1:
        sparse = next((index for index, band in enumerate(bands) if band[2] < MINIMUM_COHORT), None)
        if sparse is None:
            break
        if sparse == 0:
            neighbor = 1
        elif sparse == len(bands) - 1:
            neighbor = sparse - 1
        else:
            neighbor = sparse - 1 if bands[sparse - 1][2] <= bands[sparse + 1][2] else sparse + 1
        first, second = sorted((sparse, neighbor))
        merge(first, second)
    if any(band[2] < MINIMUM_COHORT for band in bands):
        raise ValueError("No safe n>=30 layer band can be formed.")

    def label(lower: int, upper: int) -> str:
        if lower == upper:
            return f"{lower} layer" if lower == 1 else f"{lower} layers"
        if lower == 0:
            return f"0–{upper} layers"
        if upper == depths[-1]:
            return f"{lower}+ layers"
        return f"{lower}–{upper} layers"

    total = sum(band[2] for band in bands)
    return [
        {
            "label": label(lower, upper),
            "lower_depth": lower,
            "upper_depth": upper,
            "employee_count": count,
            "voluntary_exits": exits,
            "annual_attrition_rate_percent": round(100.0 * exits / count, 4),
            "percent_of_baseline_population": round(100.0 * count / total, 8),
            "publication_status": "publishable" if count >= MINIMUM_COHORT else "not_estimable_below_30_baseline_employees",
        }
        for lower, upper, count, exits in bands
    ]


def validate(metrics: dict[str, float], raw: list[dict[str, int | float]]) -> list[dict[str, object]]:
    integer_metrics = {name: integer(metrics[name], name) for name in INTEGER_METRICS}
    if integer_metrics["maximum_chain_links"] != MAXIMUM_CHAIN_LINKS:
        raise ValueError("The annual audit did not enforce the 25-link traversal maximum.")
    if integer_metrics["universe_node_count"] < MINIMUM_COHORT:
        raise ValueError("The baseline hierarchy universe is below n=30.")
    forbidden_nonzero = (
        "manager_conflict_node_count", "self_manager_node_count", "unresolved_chain_count",
        "missing_manager_chain_count", "self_manager_chain_count", "cycle_chain_count",
        "depth_exceeded_chain_count", "manager_conflict_chain_count",
        "nonmatching_approved_root_count", "display_unresolved_chain_count",
    )
    failures = [name for name in forbidden_nonzero if integer_metrics[name] != 0]
    if failures:
        raise ValueError(f"Annual hierarchy safeguards failed: {', '.join(failures)}.")
    if integer_metrics["reconstructed_count"] != integer_metrics["universe_node_count"]:
        raise ValueError("The baseline hierarchy does not reconstruct all nodes.")
    if integer_metrics["root_count"] != 1 or integer_metrics["root_reference_pass"] != 1:
        raise ValueError("The baseline hierarchy does not converge to one approved CEO root.")
    if integer_metrics["approved_root_resolved_count"] != integer_metrics["reconstructed_count"]:
        raise ValueError("Not every baseline chain ends at the approved CEO root.")
    if not math.isclose(metrics["convergence_rate_percent"], 100.0, abs_tol=0.000001):
        raise ValueError("Baseline hierarchy convergence is below 100%.")
    if integer_metrics["display_eligible_count"] < MINIMUM_COHORT:
        raise ValueError("The active-regular baseline denominator is below n=30.")
    if integer_metrics["display_reconstructed_count"] != integer_metrics["display_eligible_count"]:
        raise ValueError("The active-regular baseline denominator does not reconcile.")
    if integer_metrics["display_approved_root_match_count"] != integer_metrics["display_eligible_count"]:
        raise ValueError("The active-regular baseline does not fully converge to the approved root.")
    if sum(int(row["employee_count"]) for row in raw) != integer_metrics["display_eligible_count"]:
        raise ValueError("Raw depth totals do not reconcile to the baseline denominator.")
    if any(int(row["voluntary_exits"]) > int(row["employee_count"]) for row in raw):
        raise ValueError("Voluntary exits exceed the baseline cohort in a depth bucket.")
    distribution = pool_depths(raw)
    if sum(int(row["employee_count"]) for row in distribution) != integer_metrics["display_eligible_count"]:
        raise ValueError("Published depth bands do not reconcile to the baseline denominator.")
    return distribution


def ensure_safe(value: object) -> None:
    restricted = {"employee_id", "manager_employee_id", "root_employee_id", "terminal_root_employee_id", "approved_ceo_employee_id", "name", "email"}
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in restricted:
                raise ValueError(f"Restricted field persisted: {key!r}.")
            ensure_safe(nested)
    elif isinstance(value, list):
        for nested in value:
            ensure_safe(nested)


def build_evidence() -> dict[str, object]:
    rows, sql_hash, result_hash = execute_query()
    metrics, raw = parse_rows(rows)
    distribution = validate(metrics, raw)
    integer_metrics = {name: integer(metrics[name], name) for name in INTEGER_METRICS}
    evidence: dict[str, object] = {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 1,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "presentation",
        "variable": "Reconstructed manager layers to CEO",
        "baseline_snapshot_date": BASELINE_DATE,
        "outcome_cutoff_date": OUTCOME_CUTOFF,
        "outcome_window": OUTCOME_WINDOW,
        "population": "worker_type='Employee' AND employee_type='Regular' AND active_status=1 at the baseline snapshot",
        "grain": "baseline employee snapshot",
        "definition": "Each baseline employee is assigned the number of same-snapshot manager links to the HR-approved CEO root; annual attrition is strict VOLUNTARY exits from that same baseline depth cohort divided by baseline employees in the cohort.",
        "target": "strict term_type='VOLUNTARY' with term_date in (2025-08-24, 2026-08-23]",
        "minimum_shared_cohort": MINIMUM_COHORT,
        "publication_rule": "Publish contiguous depth bands with at least 30 baseline employees; rate = voluntary exits from that same baseline band divided by baseline employees in the band.",
        "distribution": distribution,
        "metrics": {
            **integer_metrics,
            "convergence_rate_percent": metrics["convergence_rate_percent"],
            "stored_level_depth_plus_one_match_rate_percent": metrics["stored_level_depth_plus_one_match_rate_percent"],
            "published_bucket_count": len(distribution),
            "published_employee_count": sum(int(row["employee_count"]) for row in distribution),
            "minimum_published_bucket_count": min(int(row["employee_count"]) for row in distribution),
            "minimum_cohort": MINIMUM_COHORT,
        },
        "hierarchy_validation": {
            "approved_root_reference": "HR-approved CEO reference bound in memory at execution time",
            "identifier_persisted": False,
            "root_count": integer_metrics["root_count"],
            "convergence_rate_percent": metrics["convergence_rate_percent"],
            "stored_level_field": "worker_supervisory_organization_level_from_top",
            "stored_level_used_as_chart_value": False,
            "outcome": "pass",
        },
        "provenance": {
            "audit_sql": str(AUDIT_SQL.relative_to(ROOT)).replace("\\", "/"),
            "audit_sql_sha256": sql_hash,
            "aggregate_result_sha256": result_hash,
            "raw_aggregate_rows_persisted": False,
            "termination_source": "hrda.post_hire_monthly_worker_dtls; strict term_type='VOLUNTARY'",
        },
        "privacy_checks": {
            "identifiers_persisted": False,
            "employee_rows_persisted": False,
            "manager_rows_persisted": False,
            "root_identifier_persisted": False,
            "all_displayed_buckets_meet_minimum": True,
        },
        "outcome": "pass",
    }
    ensure_safe(evidence)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Build aggregate annual manager-layer attrition evidence for slide 32.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    evidence = build_evidence()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metrics = evidence["metrics"]
    print(f"Wrote aggregate-only evidence: {args.output}")
    print(f"Baseline {BASELINE_DATE}; employees={metrics['display_eligible_count']:,}; voluntary exits={metrics['baseline_voluntary_exits']:,}; bands={len(evidence['distribution'])}")


if __name__ == "__main__":
    main()
