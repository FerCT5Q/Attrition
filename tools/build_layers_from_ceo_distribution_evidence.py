"""Freeze privacy-safe aggregate evidence for slide 32.

The hierarchy is rebuilt inside one monthly snapshot.  The HR-approved CEO
reference is supplied only at execution through a secure environment variable
and bound as a database parameter; it is never written to SQL, JSON, logs, or
the rendered deck.  Raw aggregate depth rows are held only in memory so a
sub-threshold root or endpoint can be pooled before the frozen evidence is
written.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SQL = ROOT / "queries" / "audits" / "layers_from_ceo_snapshot_20260823_distribution.sql"
SNAPSHOT_DATE = "2026-08-23"
MINIMUM_COHORT = 30
MAXIMUM_CHAIN_LINKS = 25
DEFAULT_CEO_REFERENCE_ENV = "ATTRITION_APPROVED_CEO_EMPLOYEE_ID"
READONLY_QUERY_HELPER = (
    ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
)

REQUIRED_METRICS = {
    "active_source_row_count",
    "universe_node_count",
    "duplicate_source_node_count",
    "manager_conflict_node_count",
    "self_manager_node_count",
    "stored_level_conflict_node_count",
    "reconstructed_count",
    "unresolved_chain_count",
    "missing_manager_chain_count",
    "self_manager_chain_count",
    "cycle_chain_count",
    "depth_exceeded_chain_count",
    "manager_conflict_chain_count",
    "root_count",
    "approved_root_resolved_count",
    "nonmatching_approved_root_count",
    "maximum_observed_depth",
    "convergence_rate_percent",
    "root_reference_pass",
    "display_eligible_count",
    "display_reconstructed_count",
    "display_unresolved_chain_count",
    "display_approved_root_match_count",
    "stored_level_comparable_count",
    "stored_level_depth_plus_one_match_count",
    "stored_level_depth_plus_one_match_rate_percent",
    "maximum_chain_links",
}

INTEGER_METRICS = REQUIRED_METRICS - {
    "convergence_rate_percent",
    "stored_level_depth_plus_one_match_rate_percent",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_json(value: object) -> str:
    return sha256_bytes(
        json.dumps(value, sort_keys=True, ensure_ascii=True, default=str, separators=(",", ":")).encode("utf-8")
    )


def load_readonly_helper() -> Any:
    """Import the project-approved Redshift connection and SQL guard."""
    if not READONLY_QUERY_HELPER.exists():
        raise FileNotFoundError(f"Read-only query helper not found: {READONLY_QUERY_HELPER}")
    spec = importlib.util.spec_from_file_location("attrition_readonly_query_helper", READONLY_QUERY_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the approved read-only query helper.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def approved_ceo_reference(env_name: str) -> str:
    """Read, validate, and deliberately avoid returning a value to stdout."""
    value = os.getenv(env_name, "").strip()
    if not value:
        raise RuntimeError(
            f"Secure approved CEO reference is unavailable. Set {env_name} only in the execution environment."
        )
    if not value.isdecimal():
        raise RuntimeError("Secure approved CEO reference must be a numeric employee identifier.")
    return value


def execute_aggregate_query(approved_ceo_employee_id: str) -> tuple[list[dict[str, Any]], str, str]:
    """Execute saved aggregate-only SQL with an in-memory bound CEO reference."""
    sql = AUDIT_SQL.read_text(encoding="utf-8")
    helper = load_readonly_helper()
    readonly_sql = helper.validate_readonly(sql)
    with helper.connect() as connection:
        connection.autocommit = True
        with connection.cursor(cursor_factory=helper.psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(readonly_sql, {"approved_ceo_employee_id": approved_ceo_employee_id})
            rows = [dict(row) for row in cursor.fetchall()]
    return rows, sha256_bytes(sql.encode("utf-8")), hash_json(rows)


def numeric_int(value: object, metric: str) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Metric {metric!r} must be numeric.") from exc
    if not numeric.is_integer():
        raise ValueError(f"Metric {metric!r} must be an integer.")
    return int(numeric)


def parse_aggregate_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, float], list[tuple[int, int]]]:
    """Validate the flat aggregate contract without persisting its raw rows."""
    if not rows:
        raise ValueError("The hierarchy audit returned no aggregate rows.")
    metrics: dict[str, float] = {}
    raw_distribution: list[tuple[int, int]] = []
    for row in rows:
        if set(row) != {"snapshot_date", "row_type", "metric", "depth", "metric_value"}:
            raise ValueError("The hierarchy audit returned an unexpected aggregate schema.")
        if str(row["snapshot_date"]) != SNAPSHOT_DATE:
            raise ValueError("Snapshot mismatch: hierarchy evidence must use 2026-08-23 only.")
        row_type = str(row["row_type"])
        metric = str(row["metric"])
        if row_type == "metric":
            if row["depth"] is not None or metric in metrics:
                raise ValueError("Hierarchy metric rows must be unique and must not have a depth.")
            metrics[metric] = float(row["metric_value"])
        elif row_type == "depth_distribution":
            if metric != "display_employee_count" or row["depth"] is None:
                raise ValueError("Hierarchy depth rows use an invalid aggregate contract.")
            depth = numeric_int(row["depth"], "depth")
            employee_count = numeric_int(row["metric_value"], "depth employee_count")
            raw_distribution.append((depth, employee_count))
        else:
            raise ValueError(f"Unknown hierarchy audit row type: {row_type!r}.")
    missing = sorted(REQUIRED_METRICS - set(metrics))
    extra = sorted(set(metrics) - REQUIRED_METRICS)
    if missing or extra:
        raise ValueError(f"Hierarchy audit metric contract mismatch; missing={missing}, extra={extra}.")
    if not raw_distribution:
        raise ValueError("The hierarchy audit returned no display-population depth counts.")
    raw_distribution.sort()
    if len({depth for depth, _ in raw_distribution}) != len(raw_distribution):
        raise ValueError("The hierarchy audit returned duplicate depth buckets.")
    return metrics, raw_distribution


def pool_endpoint_depths(raw_distribution: list[tuple[int, int]]) -> list[dict[str, object]]:
    """Make ascending contiguous depth bands while preserving the n>=30 rule."""
    if not raw_distribution:
        raise ValueError("A depth distribution is required for privacy pooling.")
    depths = [depth for depth, _ in raw_distribution]
    if depths[0] < 0 or any(right != left + 1 for left, right in zip(depths, depths[1:])):
        raise ValueError("Depth buckets must be non-negative and contiguous before privacy pooling.")
    bands = [[depth, depth, count] for depth, count in raw_distribution]
    if any(count <= 0 for _, _, count in bands):
        raise ValueError("Raw depth buckets must have a positive aggregate count.")

    # At the hierarchy endpoints, grow only inward.  This is the normal path:
    # the CEO/root singleton and any rare deepest layer never appear alone.
    while len(bands) > 1 and bands[0][2] < MINIMUM_COHORT:
        bands[0][1] = bands[1][1]
        bands[0][2] += bands[1][2]
        del bands[1]
    while len(bands) > 1 and bands[-1][2] < MINIMUM_COHORT:
        bands[-2][1] = bands[-1][1]
        bands[-2][2] += bands[-1][2]
        del bands[-1]

    # An unexpected sparse interior level is still unsafe.  Coalesce it with
    # an adjacent band deterministically; the result remains contiguous and
    # is recorded as a protected aggregate rather than an individual layer.
    while len(bands) > 1:
        sparse_index = next((index for index, band in enumerate(bands) if band[2] < MINIMUM_COHORT), None)
        if sparse_index is None:
            break
        if sparse_index == 0:
            neighbor = 1
        elif sparse_index == len(bands) - 1:
            neighbor = sparse_index - 1
        else:
            left_count = bands[sparse_index - 1][2]
            right_count = bands[sparse_index + 1][2]
            neighbor = sparse_index - 1 if left_count <= right_count else sparse_index + 1
        first, second = sorted((sparse_index, neighbor))
        bands[first][1] = bands[second][1]
        bands[first][2] += bands[second][2]
        del bands[second]

    if any(count < MINIMUM_COHORT for _, _, count in bands):
        raise ValueError("No safe n>=30 display band can be formed from hierarchy depth counts.")

    def label(lower: int, upper: int) -> str:
        if lower == upper:
            return f"{lower} layer" if lower == 1 else f"{lower} layers"
        if lower == 0:
            return f"0–{upper} layers"
        if upper == depths[-1]:
            return f"{lower}+ layers"
        return f"{lower}–{upper} layers"

    return [
        {
            "label": label(lower, upper),
            "lower_depth": lower,
            "upper_depth": upper,
            "employee_count": count,
        }
        for lower, upper, count in bands
    ]


def validate_metrics(metrics: dict[str, float], raw_distribution: list[tuple[int, int]]) -> list[dict[str, object]]:
    """Fail closed on hierarchy, root, reconciliation, and privacy gaps."""
    integer = {metric: numeric_int(metrics[metric], metric) for metric in INTEGER_METRICS}
    if integer["maximum_chain_links"] != MAXIMUM_CHAIN_LINKS:
        raise ValueError("The audit did not enforce the 25-link traversal maximum.")
    if integer["universe_node_count"] < MINIMUM_COHORT:
        raise ValueError("The active hierarchy universe is below the minimum publication cohort.")
    if integer["active_source_row_count"] < integer["universe_node_count"]:
        raise ValueError("Active source rows do not reconcile to unique hierarchy nodes.")
    zero_required = (
        "manager_conflict_node_count",
        "self_manager_node_count",
        "unresolved_chain_count",
        "missing_manager_chain_count",
        "self_manager_chain_count",
        "cycle_chain_count",
        "depth_exceeded_chain_count",
        "manager_conflict_chain_count",
        "nonmatching_approved_root_count",
        "display_unresolved_chain_count",
    )
    failures = [metric for metric in zero_required if integer[metric] != 0]
    if failures:
        raise ValueError(f"Hierarchy publication rejected by nonzero safeguards: {', '.join(failures)}.")
    if integer["reconstructed_count"] != integer["universe_node_count"]:
        raise ValueError("Universe reconstruction does not reconcile to all active hierarchy nodes.")
    if integer["root_count"] != 1 or integer["root_reference_pass"] != 1:
        raise ValueError("The hierarchy does not converge to exactly one approved CEO root.")
    if integer["approved_root_resolved_count"] != integer["reconstructed_count"]:
        raise ValueError("At least one reconstructed active chain does not end at the approved root.")
    if not math.isclose(metrics["convergence_rate_percent"], 100.0, abs_tol=0.000001):
        raise ValueError("Hierarchy convergence is below 100%.")
    if integer["display_eligible_count"] < MINIMUM_COHORT:
        raise ValueError("The active-regular display population is below the minimum cohort.")
    if integer["display_reconstructed_count"] != integer["display_eligible_count"]:
        raise ValueError("Display-population reconstruction does not reconcile to its denominator.")
    if integer["display_approved_root_match_count"] != integer["display_eligible_count"]:
        raise ValueError("Display population does not fully converge to the approved root.")
    if sum(count for _, count in raw_distribution) != integer["display_eligible_count"]:
        raise ValueError("Raw depth totals do not reconcile to the active-regular denominator.")
    if max(depth for depth, _ in raw_distribution) > MAXIMUM_CHAIN_LINKS:
        raise ValueError("The audit emitted a depth beyond the permitted traversal maximum.")

    distribution = pool_endpoint_depths(raw_distribution)
    if sum(int(row["employee_count"]) for row in distribution) != integer["display_eligible_count"]:
        raise ValueError("Published depth bands do not reconcile to the active-regular denominator.")
    if any(int(row["employee_count"]) < MINIMUM_COHORT for row in distribution):
        raise ValueError("A published hierarchy depth band is below the privacy cohort minimum.")
    if any(int(row["lower_depth"]) == int(row["upper_depth"]) == 0 for row in distribution):
        raise ValueError("The CEO/root singleton must never be published as its own bar.")
    for row in distribution:
        row["percent_of_active_regular"] = round(
            100 * int(row["employee_count"]) / integer["display_eligible_count"], 8
        )
    return distribution


def ensure_no_sensitive_keys(value: object) -> None:
    """Reject accidental persistence of identities or a raw sub-threshold depth."""
    prohibited_exact = {
        "employee_id",
        "manager_employee_id",
        "root_employee_id",
        "terminal_root_employee_id",
        "name",
        "employee_name",
        "manager_name",
        "approved_ceo_employee_id",
    }
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in prohibited_exact:
                raise ValueError(f"Frozen evidence attempted to persist a restricted field: {key!r}.")
            ensure_no_sensitive_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            ensure_no_sensitive_keys(nested)


def build_evidence(approved_ceo_employee_id: str) -> dict[str, object]:
    """Run the audit, validate all publication gates, and return safe evidence."""
    raw_rows, sql_sha256, result_sha256 = execute_aggregate_query(approved_ceo_employee_id)
    metrics, raw_distribution = parse_aggregate_rows(raw_rows)
    distribution = validate_metrics(metrics, raw_distribution)
    integer_metrics = {metric: numeric_int(metrics[metric], metric) for metric in INTEGER_METRICS}
    evidence: dict[str, object] = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "internal_analysis",
        "variable": "Reconstructed manager layers to CEO",
        "semantic_type": "hierarchy",
        "execution_date": date.today().isoformat(),
        "snapshot_date": SNAPSHOT_DATE,
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 at the 2026-08-23 monthly snapshot",
        "node_universe": "All active workers at the same monthly snapshot, including active managers needed to traverse reporting links.",
        "grain": "Distinct active regular employee at one monthly snapshot",
        "definition": "Depth is the number of same-snapshot manager_employee_id links from an employee to the HR-approved CEO root. The CEO root is depth 0; a direct report is depth 1.",
        "traversal_rules": {
            "snapshot_isolation": "Managers are resolved only from the same 2026-08-23 snapshot; no manager is borrowed from another snapshot.",
            "maximum_links": MAXIMUM_CHAIN_LINKS,
            "failure_conditions": [
                "missing manager",
                "self-manager",
                "repeated node / cycle",
                "conflicting manager assignment",
                "traversal beyond 25 links",
            ],
        },
        "approved_root_check": {
            "reference": "HR-approved CEO reference bound in memory at execution time",
            "identifier_persisted": False,
            "root_count": integer_metrics["root_count"],
            "approved_root_resolved_count": integer_metrics["approved_root_resolved_count"],
            "convergence_rate_percent": metrics["convergence_rate_percent"],
            "outcome": "pass",
        },
        "stored_level_reconciliation": {
            "field": "worker_supervisory_organization_level_from_top",
            "purpose": "Separate reconciliation check only; it is not used as the chart value.",
            "comparable_active_regular_employees": integer_metrics["stored_level_comparable_count"],
            "depth_plus_one_match_count": integer_metrics["stored_level_depth_plus_one_match_count"],
            "depth_plus_one_match_rate_percent": metrics["stored_level_depth_plus_one_match_rate_percent"],
        },
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
        "provenance": {
            "audit_sql": str(AUDIT_SQL.relative_to(ROOT)).replace("\\", "/"),
            "audit_sql_sha256": sql_sha256,
            "aggregate_result_sha256": result_sha256,
            "raw_aggregate_rows_persisted": False,
        },
        "privacy_checks": {
            "identifiers_persisted": False,
            "employee_rows_persisted": False,
            "manager_rows_persisted": False,
            "names_persisted": False,
            "root_identifier_persisted": False,
            "all_displayed_buckets_meet_minimum": True,
            "root_singleton_displayed": False,
        },
        "acceptance_rule": "The fixed snapshot exists; all active same-snapshot chains reconstruct without manager conflicts, missing links, self-links, cycles, or paths beyond 25 links; every chain converges to exactly one HR-approved CEO root with 100% convergence; display depth counts reconcile exactly to active regular employees; and every published contiguous layer band has n >= 30 without exposing the CEO root singleton.",
        "outcome": "pass",
    }
    ensure_no_sensitive_keys(evidence)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Build frozen aggregate manager-layer evidence for slide 32.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--ceo-reference-env",
        default=DEFAULT_CEO_REFERENCE_ENV,
        help="Name of the secure execution-only environment variable holding the approved CEO identifier.",
    )
    args = parser.parse_args()
    reference = approved_ceo_reference(args.ceo_reference_env)
    evidence = build_evidence(reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metrics = evidence["metrics"]
    print(f"Wrote aggregate-only evidence: {args.output}")
    print(
        f"Snapshot {SNAPSHOT_DATE}; active regular employees={metrics['display_eligible_count']:,}; "
        f"published bands={metrics['published_bucket_count']}; approved-root check=pass"
    )


if __name__ == "__main__":
    main()
