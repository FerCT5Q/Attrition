"""Freeze aggregate-only evidence for the V8 promotion review slide.

The artifact describes the latest valid promotion recorded in the current
employment episode.  It never turns a missing event into a claim that somebody
was never promoted.  Employee IDs are used only inside aggregate SQL and are
not written to the JSON evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
METADATA_SQL = ROOT / "queries" / "audits" / "v8_time_since_last_promotion_metadata_preflight_20260923.sql"
REVIEW_SQL = ROOT / "queries" / "audits" / "v8_time_since_last_promotion_review_20260923.sql"
AUTHORIZATION = ROOT / "config" / "attrition_v8_internal_analysis_authorization_20260923.json"
OUTPUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v8.time-since-last-promotion-review-evidence-20260923.json"

DISPLAY_DATE = "2026-08-23"
BASELINE_DATE = "2025-08-24"
OUTCOME_CUTOFF = "2026-08-23"
MINIMUM_COHORT = 30

TIME_ORDER = (
    "0–<1 year",
    "1–<2 years",
    "2–<3 years",
    "3–<5 years",
    "5+ years",
    "No promotion recorded in current episode",
    "History predates observed promotion events",
)
ROLE_TIME_ORDER = ("<1 year", "1–<2 years", "2–<3 years", "3–<5 years", "5–<10 years", "10+ years", "Not recorded")
RELATION_ORDER = (
    "Role began with current employment episode",
    "Role began after current employment episode",
    "Start date not usable",
)
ALIGNMENT_ORDER = ("Within 3 months", "3–12 months apart", "More than 12 months apart", "Cannot compare")
FORBIDDEN_KEYS = {"employee_id", "emp_name", "name", "manager_employee_id", "manager_name", "term_date", "promotion_date"}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_rows(rows: list[dict[str, Any]]) -> str:
    return sha256_bytes(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def run_query(path: Path) -> tuple[list[dict[str, Any]], str]:
    command = [sys.executable, "-B", str(QUERY_HELPER), "--sql-file", str(path), "--max-rows", "100"]
    completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
    payload = json.loads(completed.stdout)
    if payload.get("truncated") is not False or not isinstance(payload.get("rows"), list):
        raise ValueError(f"Aggregate query did not return a complete row set: {path.name}")
    return payload["rows"], hash_rows(payload["rows"])


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def as_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer aggregate.") from exc


def as_float(value: Any, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a numeric aggregate.") from exc


def group_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    categories: dict[str, list[dict[str, Any]]] = {}
    metrics: dict[str, int] = {}
    for row in rows:
        kind = str(row.get("row_type"))
        if kind in {"diagnostic", "reconciliation"}:
            metric = str(row.get("metric"))
            if metric in metrics:
                raise ValueError(f"Duplicate V8 promotion metric {metric!r}.")
            metrics[metric] = as_int(row.get("metric_value"), metric)
            continue
        category = row.get("category")
        require(isinstance(category, str) and category, f"Missing category for {kind}.")
        categories.setdefault(kind, []).append(
            {
                "label": category,
                "employee_count": as_int(row.get("employee_count"), f"{kind}/{category} employee_count"),
                "voluntary_exits": None if row.get("voluntary_exits") is None else as_int(row.get("voluntary_exits"), f"{kind}/{category} voluntary_exits"),
                "annual_attrition_rate_percent": None if row.get("annual_attrition_rate_percent") is None else as_float(row.get("annual_attrition_rate_percent"), f"{kind}/{category} annual_attrition_rate_percent"),
            }
        )
    return categories, metrics


def rows_by_label(rows: list[dict[str, Any]], kind: str) -> dict[str, dict[str, Any]]:
    result = {row["label"]: row for row in rows if row["label"]}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate labels in {kind}.")
    return result


def ordered(rows: dict[str, dict[str, Any]], labels: tuple[str, ...], kind: str, *, allow_extra: bool = False) -> list[dict[str, Any]]:
    missing = [label for label in labels if label not in rows]
    if missing:
        raise ValueError(f"{kind} is missing expected labels: {missing!r}")
    if not allow_extra and set(rows) != set(labels):
        raise ValueError(f"{kind} contains unexpected labels: {sorted(set(rows) - set(labels))!r}")
    return [rows[label] for label in labels if label in rows]


def ensure_safe(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise ValueError(f"Forbidden sensitive key in frozen evidence: {key}")
            ensure_safe(child)
    elif isinstance(value, list):
        for child in value:
            ensure_safe(child)


def build_evidence(metadata_rows: list[dict[str, Any]], review_rows: list[dict[str, Any]], *, execution_date: str | None = None) -> dict[str, Any]:
    expected_metadata = {
        "employee_id": "bigint",
        "fis_mo_end_dt": "date",
        "worker_type": "character varying",
        "employee_type": "character varying",
        "active_status": "integer",
        "is_promo": "integer",
        "promotion_date": "date",
        "max_hire_rehire_date": "date",
        "time_in_role": "numeric",
        "time_in_job_profile_start_date": "date",
        "job_level_primary_position": "character varying",
        "level_grouped": "character varying",
        "term_date": "date",
        "term_type": "character varying",
    }
    observed_metadata = {str(row.get("column_name")): str(row.get("data_type")) for row in metadata_rows}
    require(expected_metadata.items() <= observed_metadata.items(), "Promotion-review metadata preflight is incomplete or has incompatible types.")

    categories, metrics = group_rows(review_rows)
    required_metrics = {
        "display_employee_count", "baseline_employee_count",
        "display_duplicate_employee_snapshot_count", "baseline_duplicate_employee_snapshot_count",
        "display_conflicting_employee_snapshot_count", "baseline_conflicting_employee_snapshot_count",
        "display_invalid_episode_start_count", "baseline_invalid_episode_start_count",
        "display_invalid_time_in_role_count", "baseline_invalid_time_in_role_count",
        "display_invalid_job_profile_start_count",
        "invalid_promo_flag_count", "promo_flag_without_date_count", "promotion_date_without_promo_flag_count",
        "promotion_date_after_event_snapshot_count", "future_promotion_date_count",
        "display_time_distribution_total", "baseline_time_distribution_total",
        "display_no_promo_total", "display_no_promo_level_total", "display_no_promo_role_total",
        "display_no_promo_relation_total", "display_no_promo_alignment_total",
        "baseline_classified_row_count", "baseline_classified_distinct_employee_count",
        "baseline_voluntary_exits_direct", "baseline_voluntary_exits_from_classified",
    }
    require(required_metrics <= set(metrics), "Promotion-review result is missing a required audit or reconciliation metric.")
    zero_metrics = (
        "display_duplicate_employee_snapshot_count", "baseline_duplicate_employee_snapshot_count",
        "display_conflicting_employee_snapshot_count", "baseline_conflicting_employee_snapshot_count",
        "display_invalid_episode_start_count", "baseline_invalid_episode_start_count",
        "display_invalid_time_in_role_count", "baseline_invalid_time_in_role_count",
        "display_invalid_job_profile_start_count", "invalid_promo_flag_count",
        "promo_flag_without_date_count", "promotion_date_without_promo_flag_count",
        "promotion_date_after_event_snapshot_count", "future_promotion_date_count",
    )
    failures = [name for name in zero_metrics if metrics[name] != 0]
    require(not failures, f"Promotion-review safeguards failed: {', '.join(failures)}")
    require(metrics["display_employee_count"] == 50043, "Current promotion-review denominator must reconcile to 50,043.")
    require(metrics["baseline_employee_count"] == 45003, "Annual promotion-review baseline must reconcile to 45,003.")
    require(metrics["display_time_distribution_total"] == metrics["display_employee_count"], "Current promotion bands do not reconcile to active Regular employees.")
    require(metrics["baseline_time_distribution_total"] == metrics["baseline_employee_count"], "Baseline promotion bands do not reconcile to the annual cohort.")
    require(metrics["baseline_classified_row_count"] == metrics["baseline_classified_distinct_employee_count"] == metrics["baseline_employee_count"], "Baseline promotion classification is not one row per employee.")
    require(metrics["baseline_voluntary_exits_direct"] == metrics["baseline_voluntary_exits_from_classified"] == 2484, "Promotion review does not reconcile to 2,484 strict voluntary exits.")

    display_time = ordered(rows_by_label(categories["display_time_since_promotion"], "display_time_since_promotion"), TIME_ORDER, "display_time_since_promotion")
    baseline_time = rows_by_label(categories["baseline_time_since_promotion"], "baseline_time_since_promotion")
    require(set(baseline_time) == set(TIME_ORDER), "Baseline promotion labels do not match current distribution labels.")
    for row in display_time:
        baseline = baseline_time[row["label"]]
        row["annual_baseline_employee_count"] = baseline["employee_count"]
        row["annual_voluntary_exits"] = baseline["voluntary_exits"]
        row["annual_attrition_rate_percent"] = baseline["annual_attrition_rate_percent"]
        row["publication_status"] = "internal_exploratory_small_cohort" if baseline["employee_count"] < MINIMUM_COHORT else "publishable"

    no_promo_count = next(row["employee_count"] for row in display_time if row["label"] == "No promotion recorded in current episode")
    for metric in ("display_no_promo_level_total", "display_no_promo_role_total", "display_no_promo_relation_total", "display_no_promo_alignment_total"):
        require(metrics[metric] == no_promo_count, f"{metric} does not reconcile to the no-promotion state.")

    current_level = rows_by_label(categories["display_no_promo_level"], "display_no_promo_level")
    baseline_level = rows_by_label(categories["baseline_no_promo_level"], "baseline_no_promo_level")
    require(set(current_level) == set(baseline_level), "No-promotion level panels have mismatched labels.")
    level_rows = []
    for label in sorted(current_level):
        current = dict(current_level[label])
        baseline = baseline_level[label]
        current["annual_baseline_employee_count"] = baseline["employee_count"]
        current["annual_voluntary_exits"] = baseline["voluntary_exits"]
        current["annual_attrition_rate_percent"] = baseline["annual_attrition_rate_percent"]
        current["publication_status"] = "internal_exploratory_small_cohort" if baseline["employee_count"] < MINIMUM_COHORT else "publishable"
        level_rows.append(current)

    current_role = rows_by_label(categories["display_no_promo_role_time"], "display_no_promo_role_time")
    baseline_role = rows_by_label(categories["baseline_no_promo_role_time"], "baseline_no_promo_role_time")
    require(set(baseline_role) == set(current_role), "No-promotion role panels have mismatched labels.")
    require(set(current_role) <= set(ROLE_TIME_ORDER), "No-promotion role panel contains an unsupported label.")
    role_rows = []
    for current in [current_role[label] for label in ROLE_TIME_ORDER if label in current_role]:
        baseline = baseline_role[current["label"]]
        row = dict(current)
        row["annual_baseline_employee_count"] = baseline["employee_count"]
        row["annual_voluntary_exits"] = baseline["voluntary_exits"]
        row["annual_attrition_rate_percent"] = baseline["annual_attrition_rate_percent"]
        row["publication_status"] = "internal_exploratory_small_cohort" if baseline["employee_count"] < MINIMUM_COHORT else "publishable"
        role_rows.append(row)

    relation_by_label = rows_by_label(categories["display_no_promo_role_start_relation"], "display_no_promo_role_start_relation")
    alignment_by_label = rows_by_label(categories["display_no_promo_role_tenure_alignment"], "display_no_promo_role_tenure_alignment")
    require(set(relation_by_label) <= set(RELATION_ORDER), "No-promotion role-start panel contains an unsupported label.")
    require(set(alignment_by_label) <= set(ALIGNMENT_ORDER), "No-promotion role-alignment panel contains an unsupported label.")
    relations = [relation_by_label[label] for label in RELATION_ORDER if label in relation_by_label]
    alignment = [alignment_by_label[label] for label in ALIGNMENT_ORDER if label in alignment_by_label]
    for group in (level_rows, role_rows, relations, alignment):
        require(all(row["employee_count"] >= MINIMUM_COHORT for row in group), "A displayed no-promotion context bucket is below n=30.")

    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    require(authorization.get("status") == "approved" and authorization.get("reporting_mode") == "internal_analysis", "V8 authorization is not approved for internal aggregate analysis.")
    evidence: dict[str, Any] = {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 8,
        "artifact_classification": "internal_analysis",
        "deliverable_mode": "internal_analysis",
        "variable": "Time since last promotion",
        "semantic_type": "derived_feature",
        "execution_date": execution_date or date.today().isoformat(),
        "display_snapshot_date": DISPLAY_DATE,
        "baseline_snapshot_date": BASELINE_DATE,
        "outcome_cutoff_date": OUTCOME_CUTOFF,
        "outcome_window": "(2025-08-24, 2026-08-23]",
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1",
        "grain": "Distinct active Regular employee at the named snapshot",
        "definition": {
            "latest_recorded_promotion": "Maximum distinct promotion_date where is_promo=1, the date is known by its event snapshot, and it is on or after max_hire_rehire_date for the employee's current episode.",
            "no_event_state": "No promotion recorded in current episode is an observed no-event state, not a claim of never having been promoted.",
            "role_context": "Stored time_in_role is shown separately from the tenure calculated from the later of time_in_job_profile_start_date and max_hire_rehire_date.",
            "annual_attrition": "Strict VOLUNTARY exits from the same 2025-08-24 baseline category in (2025-08-24, 2026-08-23].",
        },
        "display_distribution": display_time,
        "no_promotion_recorded_current_episode": {
            "employee_count": no_promo_count,
            "percent_of_display_population": 100.0 * no_promo_count / metrics["display_employee_count"],
            "level_grouped": level_rows,
            "time_in_role": role_rows,
            "role_start_vs_current_employment_episode": relations,
            "stored_time_in_role_vs_date_calculation": alignment,
        },
        "metrics": {
            "display_active_regular_employee_count": metrics["display_employee_count"],
            "baseline_active_regular_employee_count": metrics["baseline_employee_count"],
            "baseline_voluntary_exits": metrics["baseline_voluntary_exits_direct"],
            "baseline_invalid_job_profile_start_count": metrics["baseline_invalid_job_profile_start_count"],
            "pre_episode_promotion_events_excluded": metrics.get("pre_episode_event_excluded_count", 0),
            "minimum_cohort": MINIMUM_COHORT,
        },
        "validation": {
            "metadata_preflight": {"outcome": "pass", "acceptance_rule": "Required fields and compatible data types exist in hrda.post_hire_monthly_worker_dtls."},
            "event_integrity": {"outcome": "pass", "acceptance_rule": "No target duplicates/conflicts, invalid promotion flags, flag/date conflicts, future dates, or dates after their event snapshot."},
            "reconciliation": {"outcome": "pass", "acceptance_rule": "Current bands equal 50,043 employees; baseline bands equal 45,003; and strict voluntary exits reconcile to 2,484."},
            "role_context": {"outcome": "pass", "acceptance_rule": "Current no-event level, time-in-role, role-start and alignment groups each reconcile to the no-event denominator."},
            "privacy": {"outcome": "pass", "acceptance_rule": "Only aggregate counts/rates are frozen; no employee rows, IDs, names, individual dates, or exact compensation values are written."},
        },
        "authorization": {
            "path": str(AUTHORIZATION.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_bytes(AUTHORIZATION.read_bytes()),
            "authorization_id": authorization["authorization_id"],
        },
        "provenance": {
            "metadata_sql": str(METADATA_SQL.relative_to(ROOT)).replace("\\", "/"),
            "metadata_sql_sha256": sha256_bytes(METADATA_SQL.read_bytes()),
            "metadata_result_sha256": hash_rows(metadata_rows),
            "review_sql": str(REVIEW_SQL.relative_to(ROOT)).replace("\\", "/"),
            "review_sql_sha256": sha256_bytes(REVIEW_SQL.read_bytes()),
            "review_result_sha256": hash_rows(review_rows),
            "raw_aggregate_rows_persisted": False,
        },
        "privacy_checks": {
            "employee_rows_persisted": False,
            "employee_ids_persisted": False,
            "names_persisted": False,
            "individual_dates_persisted": False,
            "exact_compensation_values_persisted": False,
            "all_displayed_context_buckets_meet_minimum": True,
        },
        "score_v4_change": "none",
        "limitation": "The visual reports recorded events within observable history. It does not assert a promotion policy, causal relationship, or that people without a recorded event were never promoted. job-profile dates are unavailable for the historical baseline, so the role-start comparison is current-distribution context only.",
        "outcome": "pass",
    }
    ensure_safe(evidence)
    return evidence


def self_test() -> None:
    require(sha256_bytes(b"v8") == "147e82faca64a021f4af180c2acbeaa8be6a43478105110702869e353cda8c46", "SHA-256 self-test failed.")
    try:
        ensure_safe({"employee_id": 1})
    except ValueError:
        return
    raise AssertionError("Evidence privacy guard did not reject employee_id.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze V8 aggregate promotion-review evidence.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("self-test=pass")
    metadata_rows, _ = run_query(METADATA_SQL)
    review_rows, _ = run_query(REVIEW_SQL)
    evidence = build_evidence(metadata_rows, review_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(args.output)
    print(args.output)
    print(f"display_active_regular={evidence['metrics']['display_active_regular_employee_count']}")
    print(f"baseline_voluntary_exits={evidence['metrics']['baseline_voluntary_exits']}")


if __name__ == "__main__":
    main()
