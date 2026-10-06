"""Freeze aggregate-only evidence for entry paths to the current compensation grade.

The published matrix answers a narrow descriptive question: among employees in
each current grade, which share has a *recorded* promotion that aligns with the
last observed entry to that grade. It never labels a person as hired into a
grade. Employee keys, snapshots, event dates, and compensation values remain
inside the read-only query process and are not written to the JSON artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SQL = ROOT / "queries" / "audits" / "current_grade_entry_path_integrity_20260823.sql"
PROFILE_SQL = ROOT / "queries" / "profiles" / "current_grade_entry_path_20260823.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "current-grade-entry-path-evidence-20260910.json"
READONLY_QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
SNAPSHOT_DATE = "2026-08-23"
MINIMUM_COHORT = 30

CATEGORIES: tuple[tuple[str, str], ...] = (
    ("promotion_confirmed_into_current_grade", "Promotion confirmed into current grade"),
    ("observed_entry_without_registered_promotion", "Observed entry without registered promotion"),
    ("current_grade_entry_not_observable", "Current-grade entry not observable"),
)
CATEGORY_KEYS = tuple(key for key, _ in CATEGORIES)
CATEGORY_LABELS = dict(CATEGORIES)

REQUIRED_AUDIT_METRICS = {
    "target_source_row_count", "target_missing_employee_id_row_count", "target_unique_employee_count",
    "target_duplicate_employee_count", "target_duplicate_row_excess_count", "target_conflicting_grade_count",
    "target_conflicting_episode_count", "target_missing_compensation_grade_count",
    "target_missing_episode_start_count", "target_episode_start_future_count", "history_source_row_count",
    "history_duplicate_employee_snapshot_count", "history_duplicate_snapshot_row_excess_count",
    "history_conflicting_grade_snapshot_count", "history_missing_grade_snapshot_count",
    "history_conflicting_event_snapshot_count", "history_snapshot_gap_over_45_days_count",
    "invalid_promo_flag_count", "promo_flag_without_date_count", "promotion_date_without_promo_flag_count",
    "future_promotion_date_count", "promotion_date_after_event_snapshot_count",
    "candidate_event_before_current_episode_count", "observed_current_grade_entry_count",
    "employees_with_multiple_observed_entries_count", "older_observed_entries_not_selected_count",
    "selected_entries_after_gap_over_45_days_count", "entry_window_event_grade_mismatch_count",
    "valid_entry_promotion_pair_count", "employees_with_valid_entry_promotion_count",
    "promotion_confirmed_into_current_grade_count", "observed_entry_without_registered_promotion_count",
    "current_grade_entry_not_observable_count", "old_grade_comparable_snapshot_count",
    "old_grade_matches_previous_snapshot_count", "old_grade_mismatch_previous_snapshot_count",
    "old_grade_blank_with_previous_snapshot_count",
}
ZERO_REQUIRED_AUDIT_METRICS = {
    "target_missing_employee_id_row_count", "target_duplicate_employee_count", "target_duplicate_row_excess_count",
    "target_conflicting_grade_count", "target_conflicting_episode_count", "target_missing_compensation_grade_count",
    "target_missing_episode_start_count", "target_episode_start_future_count",
    "history_duplicate_employee_snapshot_count", "history_duplicate_snapshot_row_excess_count",
    "history_conflicting_grade_snapshot_count", "history_conflicting_event_snapshot_count",
    "invalid_promo_flag_count", "promo_flag_without_date_count", "promotion_date_without_promo_flag_count",
    "future_promotion_date_count", "promotion_date_after_event_snapshot_count",
    "entry_window_event_grade_mismatch_count", "selected_entries_after_gap_over_45_days_count",
}
REQUIRED_PROFILE_METRICS = {
    "denominator_active_regular", "observed_current_grade_entry_count",
    "promotion_confirmed_into_current_grade", "observed_entry_without_registered_promotion",
    "current_grade_entry_not_observable", "valid_entry_promotion_pair_count",
    "employees_with_valid_entry_promotion_count", "raw_current_grade_count",
}
PROHIBITED_KEYS = {
    "employee_id", "employee_ids", "emp_name", "name", "employee_name", "email",
    "manager_employee_id", "manager_name", "promotion_date", "entry_snapshot_date",
    "previous_snapshot_date", "max_hire_rehire_date", "compensation_grade_old", "raw_rows",
    "raw_query_rows", "query_rows", "source_rows", "individual_dates",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_json(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, ensure_ascii=True, default=str, separators=(",", ":")).encode("utf-8"))


def numeric_int(value: object, label: str) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric.") from exc
    if not numeric.is_integer():
        raise ValueError(f"{label} must be an integer.")
    return int(numeric)


def natural_sort_key(value: str) -> tuple[object, ...]:
    return tuple(int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", value))


def ensure_no_sensitive_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in PROHIBITED_KEYS:
                raise ValueError(f"Frozen current-grade-entry evidence attempted to persist a prohibited key: {key!r}.")
            ensure_no_sensitive_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            ensure_no_sensitive_keys(nested)


def load_readonly_helper() -> Any:
    if not READONLY_QUERY_HELPER.exists():
        raise FileNotFoundError(f"Read-only query helper not found: {READONLY_QUERY_HELPER}")
    spec = importlib.util.spec_from_file_location("attrition_readonly_query_helper", READONLY_QUERY_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the approved Redshift query helper.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute_aggregate_query(sql_path: Path) -> tuple[list[dict[str, Any]], str, str]:
    """Run saved aggregate SQL; raw results never leave this function."""
    sql = sql_path.read_text(encoding="utf-8")
    helper = load_readonly_helper()
    readonly_sql = helper.validate_readonly(sql)
    with helper.connect() as connection:
        connection.autocommit = True
        with connection.cursor(cursor_factory=helper.psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(readonly_sql)
            rows = [dict(row) for row in cursor.fetchall()]
    return rows, sha256_bytes(sql.encode("utf-8")), hash_json(rows)


def parse_audit_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    metrics: dict[str, int] = {}
    for row in rows:
        if set(row) != {"snapshot_date", "row_type", "metric", "metric_value"}:
            raise ValueError("The current-grade-entry audit returned an unexpected aggregate schema.")
        if str(row["snapshot_date"]) != SNAPSHOT_DATE or row["row_type"] != "metric":
            raise ValueError("Snapshot mismatch or unsupported row type in the current-grade-entry audit.")
        metric = str(row["metric"])
        if metric in metrics:
            raise ValueError(f"The current-grade-entry audit duplicated metric {metric!r}.")
        metrics[metric] = numeric_int(row["metric_value"], metric)
    missing, extra = sorted(REQUIRED_AUDIT_METRICS - set(metrics)), sorted(set(metrics) - REQUIRED_AUDIT_METRICS)
    if missing or extra:
        raise ValueError(f"Current-grade-entry audit metric contract mismatch; missing={missing}, extra={extra}.")
    return metrics


def parse_profile_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    metrics: dict[str, int] = {}
    grades: dict[str, dict[str, int]] = {}
    expected_columns = {"snapshot_date", "row_type", "compensation_grade", "category_key", "employee_count"}
    for row in rows:
        if set(row) != expected_columns or str(row["snapshot_date"]) != SNAPSHOT_DATE:
            raise ValueError("The current-grade-entry profile has an invalid aggregate row.")
        row_type, category = str(row["row_type"]), str(row["category_key"])
        count = numeric_int(row["employee_count"], f"{row_type}:{category}")
        if count < 0:
            raise ValueError("The current-grade-entry profile contains a negative count.")
        if row_type == "metric":
            if row["compensation_grade"] is not None or category not in REQUIRED_PROFILE_METRICS or category in metrics:
                raise ValueError("The current-grade-entry profile has an invalid metric row.")
            metrics[category] = count
        elif row_type == "grade_category":
            grade_value = row["compensation_grade"]
            if not isinstance(grade_value, str) or not grade_value.strip() or category not in CATEGORY_KEYS:
                raise ValueError("The current-grade-entry profile has an invalid grade-category row.")
            grade = grade_value.strip()
            category_counts = grades.setdefault(grade, {})
            if category in category_counts:
                raise ValueError(f"The current-grade-entry profile duplicated {grade!r}/{category!r}.")
            category_counts[category] = count
        else:
            raise ValueError(f"Unsupported current-grade-entry profile row type {row_type!r}.")
    if set(metrics) != REQUIRED_PROFILE_METRICS:
        raise ValueError("The current-grade-entry profile is missing a required metric.")
    if not grades or any(set(counts) != set(CATEGORY_KEYS) for counts in grades.values()):
        raise ValueError("Every grade must contain exactly the three entry-path states.")
    return metrics, grades


def rounded_percentages(counts: dict[str, int]) -> dict[str, float]:
    """Allocate tenth-percent remainders deterministically in category order."""
    total = sum(counts[key] for key in CATEGORY_KEYS)
    if total <= 0:
        raise ValueError("A displayed grade requires a positive total.")
    unrounded_tenths = [1000 * counts[key] / total for key in CATEGORY_KEYS]
    floors = [int(value) for value in unrounded_tenths]
    remainder = 1000 - sum(floors)
    order = sorted(range(len(CATEGORY_KEYS)), key=lambda index: (-(unrounded_tenths[index] - floors[index]), index))
    for index in order[:remainder]:
        floors[index] += 1
    values = {key: floors[index] / 10 for index, key in enumerate(CATEGORY_KEYS)}
    if round(sum(values.values()), 1) != 100.0:
        raise ValueError("Deterministic entry-path percentages do not sum to 100.0%.")
    return values


def validate_inputs(audit: dict[str, int], metrics: dict[str, int], grades: dict[str, dict[str, int]]) -> tuple[list[str], list[str]]:
    failures = [metric for metric in sorted(ZERO_REQUIRED_AUDIT_METRICS) if audit[metric] != 0]
    if failures:
        raise ValueError(f"Current-grade-entry publication rejected by nonzero safeguards: {', '.join(failures)}.")
    denominator = metrics["denominator_active_regular"]
    if denominator < MINIMUM_COHORT or audit["target_source_row_count"] != audit["target_unique_employee_count"] or denominator != audit["target_unique_employee_count"]:
        raise ValueError("Current-grade-entry denominator does not reconcile to the audited target population.")
    if audit["observed_current_grade_entry_count"] != metrics["observed_current_grade_entry_count"]:
        raise ValueError("Observed current-grade entries do not reconcile between audit and profile.")
    for key in ("promotion_confirmed_into_current_grade", "observed_entry_without_registered_promotion", "current_grade_entry_not_observable"):
        if audit[f"{key}_count"] != metrics[key]:
            raise ValueError(f"Current-grade-entry state {key!r} does not reconcile to the audit.")
    if metrics["promotion_confirmed_into_current_grade"] + metrics["observed_entry_without_registered_promotion"] != metrics["observed_current_grade_entry_count"]:
        raise ValueError("Observed entry states do not reconcile to observed current-grade entries.")
    if sum(metrics[key] for key in CATEGORY_KEYS) != denominator:
        raise ValueError("The three current-grade entry states do not reconcile to the denominator.")
    if metrics["valid_entry_promotion_pair_count"] != audit["valid_entry_promotion_pair_count"] or metrics["employees_with_valid_entry_promotion_count"] != audit["employees_with_valid_entry_promotion_count"]:
        raise ValueError("Valid promotion-event counts do not reconcile between audit and profile.")
    if audit["employees_with_valid_entry_promotion_count"] != metrics["promotion_confirmed_into_current_grade"]:
        raise ValueError("Confirmed entry promotions do not reconcile to their employee count.")
    if audit["old_grade_mismatch_previous_snapshot_count"] <= 0:
        raise ValueError("compensation_grade_old was not shown to disagree with the observed prior snapshot.")
    if audit["old_grade_matches_previous_snapshot_count"] + audit["old_grade_mismatch_previous_snapshot_count"] != audit["old_grade_comparable_snapshot_count"]:
        raise ValueError("compensation_grade_old reconciliation metrics are internally inconsistent.")
    if metrics["raw_current_grade_count"] != len(grades):
        raise ValueError("The profile grade domain does not reconcile to its metric.")
    totals = {key: sum(counts[key] for counts in grades.values()) for key in CATEGORY_KEYS}
    if totals != {key: metrics[key] for key in CATEGORY_KEYS}:
        raise ValueError("Grade-level entry-path totals do not reconcile to the three population states.")
    public_grades = sorted([grade for grade, counts in grades.items() if all(counts[key] >= MINIMUM_COHORT for key in CATEGORY_KEYS)], key=natural_sort_key)
    pooled_grades = sorted([grade for grade in grades if grade not in public_grades], key=natural_sort_key)
    if not public_grades or not pooled_grades:
        raise ValueError("Dynamic pooling must retain individual grades and a reconciled Other grades pool.")
    pooled_counts = {key: sum(grades[grade][key] for grade in pooled_grades) for key in CATEGORY_KEYS}
    if any(value < MINIMUM_COHORT for value in pooled_counts.values()) or any(value < MINIMUM_COHORT for grade in public_grades for value in grades[grade].values()):
        raise ValueError("A displayed current-grade-entry cell is below n=30.")
    return public_grades, pooled_grades


def check_sha256(value: str, label: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest.")


def build_evidence_from_rows(
    audit_rows: list[dict[str, Any]], profile_rows: list[dict[str, Any]], *,
    audit_sql_sha256: str | None = None, audit_result_sha256: str | None = None,
    profile_sql_sha256: str | None = None, profile_result_sha256: str | None = None,
    execution_date: str | None = None,
) -> dict[str, object]:
    audit = parse_audit_rows(audit_rows)
    metrics, grades = parse_profile_rows(profile_rows)
    public_grades, pooled_grades = validate_inputs(audit, metrics, grades)
    pooled_counts = {key: sum(grades[grade][key] for grade in pooled_grades) for key in CATEGORY_KEYS}
    matrix: list[dict[str, object]] = []
    for grade, scope, counts in [(grade, "individual", grades[grade]) for grade in public_grades] + [("Other grades", "pooled", pooled_counts)]:
        percents = rounded_percentages(counts)
        matrix.append({
            "grade": grade, "grade_scope": scope, "total_employee_count": sum(counts.values()),
            **{key: counts[key] for key in CATEGORY_KEYS},
            **{f"{key}_percent": percents[key] for key in CATEGORY_KEYS},
        })
    denominator = metrics["denominator_active_regular"]
    if sum(int(row["total_employee_count"]) for row in matrix) != denominator:
        raise ValueError("Published current-grade-entry matrix does not reconcile to the denominator.")
    for label, value in {
        "audit_sql_sha256": audit_sql_sha256 or sha256_bytes(AUDIT_SQL.read_bytes()),
        "audit_result_sha256": audit_result_sha256 or hash_json(audit_rows),
        "profile_sql_sha256": profile_sql_sha256 or sha256_bytes(PROFILE_SQL.read_bytes()),
        "profile_result_sha256": profile_result_sha256 or hash_json(profile_rows),
    }.items():
        check_sha256(value, label)
    evidence: dict[str, object] = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "internal_analysis",
        "variable": "Entry path to current compensation grade",
        "semantic_type": "derived_feature",
        "publication_status": "validated_descriptive_matrix",
        "execution_date": execution_date or date.today().isoformat(),
        "snapshot_date": SNAPSHOT_DATE,
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 at the 2026-08-23 monthly snapshot",
        "grain": "Distinct active regular employee at one monthly snapshot, grouped by current compensation_grade",
        "definition": {
            "classification": "The latest observed change into the current compensation grade is reconstructed from monthly snapshots inside the current employment episode.",
            "promotion_confirmation_rule": "A valid is_promo=1 event has a nonfuture date after the prior snapshot and on or before the entry snapshot; its event snapshot has the current compensation grade.",
            "observed_without_registered_promotion": "A change into the current grade is observed, but no event meets the promotion-confirmation rule.",
            "not_observable": "No previous complete snapshot demonstrates a change into the current grade; this state is not a direct-hire label.",
            "rejected_field": "compensation_grade_old is not used: the aggregate audit shows it does not reconcile to the observed prior snapshot.",
            "non_claims": "Neither observed entry without a registered promotion nor entry not observable means hired into grade, and this is not a causal attrition finding.",
        },
        "category_labels": CATEGORY_LABELS,
        "percentage_rounding": {"method": "largest remainder at 0.1 percentage point; category-order tie break", "each_row_sums_to_percent": 100.0},
        "matrix": matrix,
        "metrics": {
            "active_regular_employee_count": denominator,
            "observed_current_grade_entry_count": metrics["observed_current_grade_entry_count"],
            "promotion_confirmed_into_current_grade_count": metrics["promotion_confirmed_into_current_grade"],
            "observed_entry_without_registered_promotion_count": metrics["observed_entry_without_registered_promotion"],
            "current_grade_entry_not_observable_count": metrics["current_grade_entry_not_observable"],
            "valid_entry_promotion_pair_count": metrics["valid_entry_promotion_pair_count"],
            "employees_with_valid_entry_promotion_count": metrics["employees_with_valid_entry_promotion_count"],
            "raw_current_grade_count": len(grades), "individual_grade_count": len(public_grades),
            "pooled_other_grade_count": len(pooled_grades), "minimum_published_cell_count": min(int(row[key]) for row in matrix for key in CATEGORY_KEYS),
            "minimum_cohort": MINIMUM_COHORT,
            "employees_with_multiple_observed_entries_count": audit["employees_with_multiple_observed_entries_count"],
            "older_observed_entries_not_selected_count": audit["older_observed_entries_not_selected_count"],
            "history_missing_grade_snapshot_count": audit["history_missing_grade_snapshot_count"],
            "history_snapshot_gap_over_45_days_count": audit["history_snapshot_gap_over_45_days_count"],
            "old_grade_comparable_snapshot_count": audit["old_grade_comparable_snapshot_count"],
            "old_grade_matches_previous_snapshot_count": audit["old_grade_matches_previous_snapshot_count"],
            "old_grade_mismatch_previous_snapshot_count": audit["old_grade_mismatch_previous_snapshot_count"],
            "old_grade_blank_with_previous_snapshot_count": audit["old_grade_blank_with_previous_snapshot_count"],
        },
        "validation": {
            "integrity": {"outcome": "pass", "acceptance_rule": "Target and historical employee-snapshots are unique and conflict-free; target grade and episode are complete; promotion flags/dates are valid."},
            "entry_selection": {"outcome": "pass", "acceptance_rule": "When multiple entries to the same current grade are observed, only the latest one is selected; selection after a gap greater than 45 days is rejected."},
            "event_alignment": {"outcome": "pass", "acceptance_rule": "A confirming event is after the previous snapshot, on or before the entry snapshot, within the current episode, and recorded with the current grade."},
            "old_grade_rejected": {"outcome": "pass", "acceptance_rule": "The aggregate comparison records one or more compensation_grade_old mismatches to the prior observed snapshot; the field is excluded from the derivation."},
            "reconciliation": {"outcome": "pass", "acceptance_rule": "The three mutually exclusive states and all grade cells reconcile exactly to the active-regular denominator."},
            "pooling": {"outcome": "pass", "acceptance_rule": "An individual grade has n>=30 in each raw state; all other grades are reconciled once into Other grades."},
            "privacy": {"outcome": "pass", "acceptance_rule": "The internal-analysis artifact retains aggregate counts and rounded percentages only; every visible state cell is n>=30 and contains no identities, dates, employee rows, or exact compensation."},
        },
        "provenance": {
            "audit_sql": str(AUDIT_SQL.relative_to(ROOT)).replace("\\", "/"), "audit_sql_sha256": audit_sql_sha256 or sha256_bytes(AUDIT_SQL.read_bytes()),
            "audit_result_sha256": audit_result_sha256 or hash_json(audit_rows), "profile_sql": str(PROFILE_SQL.relative_to(ROOT)).replace("\\", "/"),
            "profile_sql_sha256": profile_sql_sha256 or sha256_bytes(PROFILE_SQL.read_bytes()), "profile_result_sha256": profile_result_sha256 or hash_json(profile_rows),
            "raw_aggregate_rows_persisted": False,
        },
        "privacy_checks": {"identifiers_persisted": False, "employee_rows_persisted": False, "individual_dates_persisted": False, "exact_compensation_persisted": False, "all_visible_cells_meet_minimum": True, "minimum_cohort": MINIMUM_COHORT},
        "score_v4_change": "none",
        "limitation": "This descriptive entry-path matrix does not identify direct hires, a promotion policy, employee intent, or a causal relationship with attrition.",
        "outcome": "pass",
    }
    ensure_no_sensitive_keys(evidence)
    return evidence


def build_and_write(output: Path = OUTPUT) -> dict[str, object]:
    audit_rows, audit_sql_hash, audit_result_hash = execute_aggregate_query(AUDIT_SQL)
    profile_rows, profile_sql_hash, profile_result_hash = execute_aggregate_query(PROFILE_SQL)
    evidence = build_evidence_from_rows(audit_rows, profile_rows, audit_sql_sha256=audit_sql_hash, audit_result_sha256=audit_result_hash, profile_sql_sha256=profile_sql_hash, profile_result_sha256=profile_result_hash)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(output)
    return evidence


def synthetic_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Small offline fixture with two individual grades and one Other pool."""
    audit = {metric: 0 for metric in REQUIRED_AUDIT_METRICS}
    audit.update({"target_source_row_count": 630, "target_unique_employee_count": 630, "history_source_row_count": 5000, "observed_current_grade_entry_count": 430, "employees_with_multiple_observed_entries_count": 4, "older_observed_entries_not_selected_count": 5, "valid_entry_promotion_pair_count": 220, "employees_with_valid_entry_promotion_count": 220, "promotion_confirmed_into_current_grade_count": 220, "observed_entry_without_registered_promotion_count": 210, "current_grade_entry_not_observable_count": 200, "old_grade_comparable_snapshot_count": 4100, "old_grade_matches_previous_snapshot_count": 3800, "old_grade_mismatch_previous_snapshot_count": 300, "old_grade_blank_with_previous_snapshot_count": 0})
    audit_rows = [{"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "metric": key, "metric_value": value} for key, value in sorted(audit.items())]
    grades = {"G10": [100, 80, 70], "G20": [90, 60, 80], "S1": [15, 40, 25], "S2": [15, 30, 25]}
    totals = [sum(values[index] for values in grades.values()) for index in range(3)]
    profile_rows: list[dict[str, Any]] = [{"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "denominator_active_regular", "employee_count": sum(totals)}, {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "observed_current_grade_entry_count", "employee_count": totals[0] + totals[1]}, {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "promotion_confirmed_into_current_grade", "employee_count": totals[0]}, {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "observed_entry_without_registered_promotion", "employee_count": totals[1]}, {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "current_grade_entry_not_observable", "employee_count": totals[2]}, {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "valid_entry_promotion_pair_count", "employee_count": totals[0]}, {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "employees_with_valid_entry_promotion_count", "employee_count": totals[0]}, {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "raw_current_grade_count", "employee_count": len(grades)}]
    for grade, counts in grades.items():
        profile_rows.extend({"snapshot_date": SNAPSHOT_DATE, "row_type": "grade_category", "compensation_grade": grade, "category_key": key, "employee_count": count} for key, count in zip(CATEGORY_KEYS, counts))
    return audit_rows, profile_rows


def self_test() -> None:
    audit_rows, profile_rows = synthetic_rows()
    evidence = build_evidence_from_rows(audit_rows, profile_rows, execution_date="2026-09-10")
    assert len(evidence["matrix"]) == 3
    assert all(round(sum(row[f"{key}_percent"] for key in CATEGORY_KEYS), 1) == 100.0 for row in evidence["matrix"])
    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    next(row for row in bad_audit if row["metric"] == "old_grade_mismatch_previous_snapshot_count")["metric_value"] = 0
    next(row for row in bad_audit if row["metric"] == "old_grade_matches_previous_snapshot_count")["metric_value"] = 4100
    try:
        build_evidence_from_rows(bad_audit, bad_profile)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected compensation_grade_old rejection")
    try:
        ensure_no_sensitive_keys({"employee_id": 1})
    except ValueError:
        pass
    else:
        raise AssertionError("Expected sensitive-key rejection")


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze aggregate internal evidence for entry paths to current compensation grade.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("self-test=pass")
    evidence = build_and_write(args.output)
    print(args.output)
    print(f"active_regular={evidence['metrics']['active_regular_employee_count']}")
    print(f"published_rows={len(evidence['matrix'])}")


if __name__ == "__main__":
    main()
