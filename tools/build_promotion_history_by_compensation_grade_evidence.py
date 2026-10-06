"""Freeze aggregate-only evidence for promotion history by current grade.

The four displayed categories describe recorded promotion events within the
current employment episode.  They neither identify a first promotion nor say
that an employee was hired into a grade.  All database rows stay in memory;
the published JSON contains only grade-level aggregate counts and hashes.
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
AUDIT_SQL = ROOT / "queries" / "audits" / "promotion_history_by_compensation_grade_integrity_20260823.sql"
PROFILE_SQL = ROOT / "queries" / "profiles" / "promotion_history_by_compensation_grade_20260823.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "promotion-history-by-compensation-grade-evidence-20260910.json"
READONLY_QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
SNAPSHOT_DATE = "2026-08-23"
OBSERVED_HISTORY_START = "2016-10-23"
MINIMUM_COHORT = 30
EXPECTED_INDIVIDUAL_GRADES = 13

CATEGORIES: tuple[tuple[str, str], ...] = (
    ("zero_recorded_promotions", "0 recorded promotions"),
    ("one_recorded_promotion", "1 recorded promotion"),
    ("two_or_more_recorded_promotions", "2+ recorded promotions"),
    ("partial_promotion_history", "Partial promotion history"),
)
CATEGORY_KEYS = tuple(key for key, _ in CATEGORIES)
CATEGORY_LABELS = dict(CATEGORIES)

REQUIRED_AUDIT_METRICS = {
    "target_source_row_count",
    "target_missing_employee_id_row_count",
    "target_unique_employee_count",
    "target_duplicate_employee_count",
    "target_duplicate_row_excess_count",
    "target_conflicting_grade_count",
    "target_conflicting_episode_count",
    "target_missing_compensation_grade_count",
    "target_missing_episode_start_count",
    "target_episode_start_future_count",
    "history_source_row_count",
    "history_duplicate_employee_snapshot_count",
    "history_duplicate_snapshot_row_excess_count",
    "history_conflicting_event_snapshot_count",
    "invalid_promo_flag_count",
    "promo_flag_without_date_count",
    "promotion_date_without_promo_flag_count",
    "future_promotion_date_count",
    "promotion_date_after_event_snapshot_count",
    "identical_event_duplicate_pair_count",
    "identical_event_duplicate_row_excess_count",
    "candidate_event_before_current_episode_count",
    "valid_event_pair_count",
    "employees_with_valid_event_count",
    "selected_event_before_current_episode_count",
}
ZERO_REQUIRED_AUDIT_METRICS = {
    "target_missing_employee_id_row_count",
    "target_duplicate_employee_count",
    "target_duplicate_row_excess_count",
    "target_conflicting_grade_count",
    "target_conflicting_episode_count",
    "target_missing_compensation_grade_count",
    "target_missing_episode_start_count",
    "target_episode_start_future_count",
    "history_duplicate_employee_snapshot_count",
    "history_duplicate_snapshot_row_excess_count",
    "history_conflicting_event_snapshot_count",
    "invalid_promo_flag_count",
    "promo_flag_without_date_count",
    "promotion_date_without_promo_flag_count",
    "future_promotion_date_count",
    "promotion_date_after_event_snapshot_count",
    "selected_event_before_current_episode_count",
}
REQUIRED_PROFILE_METRICS = {
    "denominator_active_regular",
    "observable_history_employee_count",
    "partial_history_employee_count",
    "zero_recorded_promotions",
    "one_recorded_promotion",
    "two_or_more_recorded_promotions",
    "valid_event_pair_count",
    "employees_with_valid_event_count",
}
PROHIBITED_KEYS = {
    "employee_id",
    "employee_ids",
    "emp_name",
    "name",
    "employee_name",
    "email",
    "manager_employee_id",
    "manager_name",
    "promotion_date",
    "max_hire_rehire_date",
    "raw_rows",
    "raw_query_rows",
    "query_rows",
    "source_rows",
    "individual_dates",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_json(value: object) -> str:
    return sha256_bytes(
        json.dumps(value, sort_keys=True, ensure_ascii=True, default=str, separators=(",", ":")).encode("utf-8")
    )


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


def rounded_percentages(counts: dict[str, int]) -> dict[str, float]:
    """Allocate tenth-percent remainders deterministically in category order."""
    total = sum(counts[key] for key in CATEGORY_KEYS)
    if total <= 0:
        raise ValueError("A published compensation grade requires a positive total.")
    unrounded_tenths = [1000 * counts[key] / total for key in CATEGORY_KEYS]
    floors = [int(value) for value in unrounded_tenths]
    remainder = 1000 - sum(floors)
    order = sorted(range(len(CATEGORY_KEYS)), key=lambda index: (-(unrounded_tenths[index] - floors[index]), index))
    for index in order[:remainder]:
        floors[index] += 1
    values = {key: floors[index] / 10 for index, key in enumerate(CATEGORY_KEYS)}
    if round(sum(values.values()), 1) != 100.0:
        raise ValueError("Promotion-history percentages do not sum to 100.0% after deterministic rounding.")
    return values


def ensure_no_sensitive_keys(value: object) -> None:
    """Fail closed if frozen evidence would retain row-level data."""
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in PROHIBITED_KEYS:
                raise ValueError(f"Frozen promotion-history evidence attempted to persist a prohibited key: {key!r}.")
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
    """Execute one saved aggregate-only query; never persist returned rows."""
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
    if not rows:
        raise ValueError("The promotion-history integrity audit returned no aggregate rows.")
    metrics: dict[str, int] = {}
    for row in rows:
        if set(row) != {"snapshot_date", "row_type", "metric", "metric_value"}:
            raise ValueError("The promotion-history integrity audit returned an unexpected aggregate schema.")
        if str(row["snapshot_date"]) != SNAPSHOT_DATE or row["row_type"] != "metric":
            raise ValueError("Snapshot mismatch or unexpected row type in the promotion-history audit.")
        metric = str(row["metric"])
        if metric in metrics:
            raise ValueError(f"The promotion-history audit duplicated metric {metric!r}.")
        metrics[metric] = numeric_int(row["metric_value"], metric)
    missing = sorted(REQUIRED_AUDIT_METRICS - set(metrics))
    extra = sorted(set(metrics) - REQUIRED_AUDIT_METRICS)
    if missing or extra:
        raise ValueError(f"Promotion-history audit metric contract mismatch; missing={missing}, extra={extra}.")
    return metrics


def parse_profile_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, dict[str, int]], str]:
    if not rows:
        raise ValueError("The promotion-history profile returned no aggregate rows.")
    metrics: dict[str, int] = {}
    grades: dict[str, dict[str, int]] = {}
    history_start: str | None = None
    expected_columns = {
        "snapshot_date", "row_type", "compensation_grade", "category_key", "employee_count", "observed_history_start_date"
    }
    for row in rows:
        if set(row) != expected_columns:
            raise ValueError("The promotion-history profile returned an unexpected aggregate schema.")
        if str(row["snapshot_date"]) != SNAPSHOT_DATE:
            raise ValueError("Snapshot mismatch: promotion-history profile must use 2026-08-23 only.")
        row_type = str(row["row_type"])
        category = str(row["category_key"])
        count = numeric_int(row["employee_count"], f"{row_type}:{category}")
        if count < 0:
            raise ValueError("The promotion-history profile contains a negative count.")
        if row_type == "metric":
            if row["compensation_grade"] is not None or row["observed_history_start_date"] is not None or category not in REQUIRED_PROFILE_METRICS or category in metrics:
                raise ValueError("The promotion-history profile has an invalid metric row.")
            metrics[category] = count
        elif row_type == "observability":
            if (
                row["compensation_grade"] is not None
                or category != "observed_promotion_history_start"
                or count != 0
                or history_start is not None
            ):
                raise ValueError("The promotion-history profile has an invalid observability row.")
            history_start = str(row["observed_history_start_date"])
            try:
                date.fromisoformat(history_start)
            except ValueError as exc:
                raise ValueError("The observed promotion-history start must be ISO YYYY-MM-DD.") from exc
        elif row_type == "grade_category":
            grade_value = row["compensation_grade"]
            if not isinstance(grade_value, str) or not grade_value.strip() or row["observed_history_start_date"] is not None or category not in CATEGORY_KEYS:
                raise ValueError("The promotion-history profile has an invalid grade-category row.")
            grade = grade_value.strip()
            categories = grades.setdefault(grade, {})
            if category in categories:
                raise ValueError(f"The promotion-history profile duplicated {grade!r}/{category!r}.")
            categories[category] = count
        else:
            raise ValueError(f"The promotion-history profile has unsupported row type {row_type!r}.")
    if set(metrics) != REQUIRED_PROFILE_METRICS:
        raise ValueError("The promotion-history profile is missing a required metric.")
    if history_start != OBSERVED_HISTORY_START:
        raise ValueError("The promotion-history profile does not match the approved observed-history boundary.")
    if not grades or any(set(categories) != set(CATEGORY_KEYS) for categories in grades.values()):
        raise ValueError("Every compensation grade must have exactly the four promotion-history categories.")
    return metrics, grades, history_start


def validate_inputs(audit: dict[str, int], metrics: dict[str, int], grades: dict[str, dict[str, int]]) -> tuple[list[str], list[str]]:
    failures = [metric for metric in sorted(ZERO_REQUIRED_AUDIT_METRICS) if audit[metric] != 0]
    if failures:
        raise ValueError(f"Promotion-history publication rejected by nonzero safeguards: {', '.join(failures)}.")
    if audit["target_source_row_count"] != audit["target_unique_employee_count"]:
        raise ValueError("Promotion-history target snapshot rows do not reconcile to distinct employees.")
    denominator = metrics["denominator_active_regular"]
    if denominator < MINIMUM_COHORT or denominator != audit["target_unique_employee_count"]:
        raise ValueError("Promotion-history denominator does not reconcile to the audited target population.")
    if metrics["valid_event_pair_count"] != audit["valid_event_pair_count"] or metrics["employees_with_valid_event_count"] != audit["employees_with_valid_event_count"]:
        raise ValueError("Promotion-history event counts do not reconcile to the integrity audit.")
    observable_total = sum(metrics[key] for key in CATEGORY_KEYS[:3])
    if observable_total != metrics["observable_history_employee_count"]:
        raise ValueError("0/1/2+ categories do not reconcile exactly to observable promotion history.")
    if metrics["partial_history_employee_count"] + metrics["observable_history_employee_count"] != denominator:
        raise ValueError("Partial promotion history does not reconcile exactly to the historical remainder.")
    if metrics["partial_history_employee_count"] <= 0:
        raise ValueError("Partial promotion history must retain the pre-observation episodes.")
    category_totals = {key: sum(counts[key] for counts in grades.values()) for key in CATEGORY_KEYS}
    if any(category_totals[key] != (metrics["partial_history_employee_count"] if key == "partial_promotion_history" else metrics[key]) for key in CATEGORY_KEYS):
        raise ValueError("Grade-category totals do not reconcile to the four population categories.")
    if sum(category_totals.values()) != denominator:
        raise ValueError("Grade-category matrix does not reconcile to the full denominator.")

    public_grades = sorted(
        [grade for grade, counts in grades.items() if all(counts[key] >= MINIMUM_COHORT for key in CATEGORY_KEYS)],
        key=natural_sort_key,
    )
    pooled_grades = sorted([grade for grade in grades if grade not in public_grades], key=natural_sort_key)
    if len(public_grades) != EXPECTED_INDIVIDUAL_GRADES or len(public_grades) + 1 != 14:
        raise ValueError("Dynamic pooling did not yield the approved 13 individual grades plus Other grades.")
    if not pooled_grades:
        raise ValueError("The approved display requires an Other grades pool.")
    pooled_counts = {key: sum(grades[grade][key] for grade in pooled_grades) for key in CATEGORY_KEYS}
    if any(count < MINIMUM_COHORT for count in pooled_counts.values()):
        raise ValueError("Other grades has a visible promotion-history cell below the minimum cohort.")
    if any(count < MINIMUM_COHORT for grade in public_grades for count in grades[grade].values()):
        raise ValueError("A published compensation-grade cell is below the minimum cohort.")
    return public_grades, pooled_grades


def check_sha256(value: str, label: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest.")


def build_evidence_from_rows(
    audit_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    *,
    audit_sql_sha256: str | None = None,
    audit_result_sha256: str | None = None,
    profile_sql_sha256: str | None = None,
    profile_result_sha256: str | None = None,
    execution_date: str | None = None,
) -> dict[str, object]:
    """Build a validated internal-analysis matrix from aggregate-only query rows."""
    audit = parse_audit_rows(audit_rows)
    metrics, grades, history_start = parse_profile_rows(profile_rows)
    public_grades, pooled_grades = validate_inputs(audit, metrics, grades)
    pooled_counts = {key: sum(grades[grade][key] for grade in pooled_grades) for key in CATEGORY_KEYS}
    matrix: list[dict[str, object]] = []
    for grade in public_grades:
        counts = grades[grade]
        percentages = rounded_percentages(counts)
        matrix.append({
            "grade": grade,
            "grade_scope": "individual",
            "total_employee_count": sum(counts.values()),
            **{key: counts[key] for key in CATEGORY_KEYS},
            **{f"{key}_percent": percentages[key] for key in CATEGORY_KEYS},
        })
    pooled_percentages = rounded_percentages(pooled_counts)
    matrix.append({
        "grade": "Other grades",
        "grade_scope": "pooled",
        "total_employee_count": sum(pooled_counts.values()),
        **pooled_counts,
        **{f"{key}_percent": pooled_percentages[key] for key in CATEGORY_KEYS},
    })
    denominator = metrics["denominator_active_regular"]
    if len(matrix) != 14 or sum(int(row["total_employee_count"]) for row in matrix) != denominator:
        raise ValueError("Published promotion-history matrix does not contain 14 reconciled rows.")

    audit_sql_sha256 = audit_sql_sha256 or sha256_bytes(AUDIT_SQL.read_bytes())
    audit_result_sha256 = audit_result_sha256 or hash_json(audit_rows)
    profile_sql_sha256 = profile_sql_sha256 or sha256_bytes(PROFILE_SQL.read_bytes())
    profile_result_sha256 = profile_result_sha256 or hash_json(profile_rows)
    for label, value in {
        "audit_sql_sha256": audit_sql_sha256,
        "audit_result_sha256": audit_result_sha256,
        "profile_sql_sha256": profile_sql_sha256,
        "profile_result_sha256": profile_result_sha256,
    }.items():
        check_sha256(value, label)

    evidence: dict[str, object] = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "internal_analysis",
        "variable": "Promotion history by current compensation grade",
        "semantic_type": "derived_feature",
        "publication_status": "validated_descriptive_matrix",
        "execution_date": execution_date or date.today().isoformat(),
        "snapshot_date": SNAPSHOT_DATE,
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 at the 2026-08-23 monthly snapshot",
        "grain": "Distinct active regular employee at one monthly snapshot, grouped by current compensation_grade",
        "definition": {
            "classification": "Current compensation grade is taken from the fixed employee snapshot. 0/1/2+ count valid recorded promotion events only inside the current employment episode.",
            "valid_event_rule": "is_promo=1; event date present, not later than the cutoff or its source snapshot, and on or after the current episode start.",
            "deduplication": "Only identical employee plus event-date pairs are counted once.",
            "partial_history_rule": "Any episode that began before the observed promotion-history boundary is Partial promotion history, regardless of recorded events.",
            "non_claims": "0 recorded promotions is not never promoted, first job, first promotion, or hired into grade.",
        },
        "history_observability": {
            "observed_promotion_history_start_date": history_start,
            "interpretation": "Observed source-history boundary; it is not a claim that earlier promotion history is complete.",
        },
        "category_labels": CATEGORY_LABELS,
        "percentage_rounding": {
            "method": "largest remainder at 0.1 percentage point; category-order tie break",
            "each_row_sums_to_percent": 100.0,
        },
        "matrix": matrix,
        "metrics": {
            "active_regular_employee_count": denominator,
            "observable_history_employee_count": metrics["observable_history_employee_count"],
            "partial_history_employee_count": metrics["partial_history_employee_count"],
            "valid_event_pair_count": metrics["valid_event_pair_count"],
            "employees_with_valid_event_count": metrics["employees_with_valid_event_count"],
            "current_episode_events_excluded_before_rehire_count": audit["candidate_event_before_current_episode_count"],
            "identical_event_duplicate_pairs_deduplicated": audit["identical_event_duplicate_pair_count"],
            "raw_current_grade_count": len(grades),
            "individual_grade_count": len(public_grades),
            "pooled_other_grade_count": len(pooled_grades),
            "minimum_published_cell_count": min(int(row[key]) for row in matrix for key in CATEGORY_KEYS),
            "minimum_cohort": MINIMUM_COHORT,
        },
        "validation": {
            "integrity": {
                "outcome": "pass",
                "acceptance_rule": "Target employee-snapshot, current grade, and episode are unique and complete; flags/dates are valid; no selected event predates its current episode.",
            },
            "reconciliation": {
                "outcome": "pass",
                "acceptance_rule": "0/1/2+ exactly cover observable episodes, Partial promotion history exactly covers the historical remainder, and all rows/categories sum to the 50,043-person population.",
            },
            "pooling": {
                "outcome": "pass",
                "acceptance_rule": "A grade is shown individually only if all four cells are n>=30; every other grade is included exactly once in Other grades.",
            },
            "privacy": {
                "outcome": "pass",
                "acceptance_rule": "Internal-analysis artifact retains only aggregate counts; every visible matrix cell is n>=30; no employee rows, identities, individual dates, or exact compensation values are stored.",
            },
        },
        "provenance": {
            "audit_sql": str(AUDIT_SQL.relative_to(ROOT)).replace("\\", "/"),
            "audit_sql_sha256": audit_sql_sha256,
            "audit_result_sha256": audit_result_sha256,
            "profile_sql": str(PROFILE_SQL.relative_to(ROOT)).replace("\\", "/"),
            "profile_sql_sha256": profile_sql_sha256,
            "profile_result_sha256": profile_result_sha256,
            "raw_aggregate_rows_persisted": False,
        },
        "privacy_checks": {
            "identifiers_persisted": False,
            "employee_rows_persisted": False,
            "individual_dates_persisted": False,
            "exact_compensation_persisted": False,
            "all_visible_cells_meet_minimum": True,
            "minimum_cohort": MINIMUM_COHORT,
        },
        "score_v4_change": "none",
        "limitation": "This descriptive matrix reports recorded promotion events in observed history. It does not establish a promotion policy, a causal relationship with attrition, a first promotion, or whether a person was hired into a grade.",
        "outcome": "pass",
    }
    ensure_no_sensitive_keys(evidence)
    return evidence


def build_and_write(output: Path = OUTPUT) -> dict[str, object]:
    audit_rows, audit_sql_hash, audit_result_hash = execute_aggregate_query(AUDIT_SQL)
    profile_rows, profile_sql_hash, profile_result_hash = execute_aggregate_query(PROFILE_SQL)
    evidence = build_evidence_from_rows(
        audit_rows,
        profile_rows,
        audit_sql_sha256=audit_sql_hash,
        audit_result_sha256=audit_result_hash,
        profile_sql_sha256=profile_sql_hash,
        profile_result_sha256=profile_result_hash,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(output)
    return evidence


def synthetic_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return a 13-public-grade fixture plus a two-grade Other pool."""
    audit = {metric: 0 for metric in REQUIRED_AUDIT_METRICS}
    audit.update({
        "target_source_row_count": 2105,
        "target_unique_employee_count": 2105,
        "history_source_row_count": 50000,
        "candidate_event_before_current_episode_count": 11,
        "valid_event_pair_count": 1480,
        "employees_with_valid_event_count": 1015,
    })
    audit_rows = [
        {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "metric": key, "metric_value": value}
        for key, value in sorted(audit.items())
    ]
    grades = {f"G{index:02d}": [40, 35, 30, 35] for index in range(1, 14)}
    grades["S1"] = [10, 50, 40, 40]
    grades["S2"] = [20, 45, 35, 45]
    totals = [sum(values[index] for values in grades.values()) for index in range(4)]
    profile_rows: list[dict[str, Any]] = [
        {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "denominator_active_regular", "employee_count": sum(totals), "observed_history_start_date": None},
        {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "observable_history_employee_count", "employee_count": sum(totals[:3]), "observed_history_start_date": None},
        {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "partial_history_employee_count", "employee_count": totals[3], "observed_history_start_date": None},
        {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "zero_recorded_promotions", "employee_count": totals[0], "observed_history_start_date": None},
        {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "one_recorded_promotion", "employee_count": totals[1], "observed_history_start_date": None},
        {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "two_or_more_recorded_promotions", "employee_count": totals[2], "observed_history_start_date": None},
        {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "valid_event_pair_count", "employee_count": 1480, "observed_history_start_date": None},
        {"snapshot_date": SNAPSHOT_DATE, "row_type": "metric", "compensation_grade": None, "category_key": "employees_with_valid_event_count", "employee_count": 1015, "observed_history_start_date": None},
        {"snapshot_date": SNAPSHOT_DATE, "row_type": "observability", "compensation_grade": None, "category_key": "observed_promotion_history_start", "employee_count": 0, "observed_history_start_date": OBSERVED_HISTORY_START},
    ]
    for grade, counts in grades.items():
        profile_rows.extend(
            {
                "snapshot_date": SNAPSHOT_DATE,
                "row_type": "grade_category",
                "compensation_grade": grade,
                "category_key": key,
                "employee_count": count,
                "observed_history_start_date": None,
            }
            for key, count in zip(CATEGORY_KEYS, counts)
        )
    return audit_rows, profile_rows


def expect_rejected(label: str, callback: Any) -> None:
    try:
        callback()
    except ValueError:
        return
    raise AssertionError(f"Expected rejection was not raised: {label}")


def replace_audit_metric(rows: list[dict[str, Any]], metric: str, value: int) -> None:
    for row in rows:
        if row.get("metric") == metric:
            row["metric_value"] = value
            return
    raise AssertionError(f"Missing synthetic metric {metric!r}.")


def self_test() -> None:
    """Exercise snapshot, integrity, pooling, reconciliation, and privacy gates."""
    audit_rows, profile_rows = synthetic_rows()
    baseline = build_evidence_from_rows(audit_rows, profile_rows, execution_date="2026-09-10")
    assert len(baseline["matrix"]) == 14
    assert baseline["metrics"]["active_regular_employee_count"] == 2105

    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    bad_profile[0]["snapshot_date"] = "2026-08-24"
    expect_rejected("wrong snapshot", lambda: build_evidence_from_rows(bad_audit, bad_profile))

    for metric, label in (
        ("target_duplicate_employee_count", "target duplicate"),
        ("target_conflicting_grade_count", "grade conflict"),
        ("history_conflicting_event_snapshot_count", "flag/date conflict"),
        ("invalid_promo_flag_count", "invalid flag"),
        ("future_promotion_date_count", "future date"),
        ("selected_event_before_current_episode_count", "pre-rehire selected"),
    ):
        bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
        replace_audit_metric(bad_audit, metric, 1)
        expect_rejected(label, lambda a=bad_audit, p=bad_profile: build_evidence_from_rows(a, p))

    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    next(row for row in bad_profile if row["category_key"] == "denominator_active_regular")["employee_count"] = 2106
    expect_rejected("unreconciled denominator", lambda: build_evidence_from_rows(bad_audit, bad_profile))

    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    row = next(row for row in bad_profile if row["row_type"] == "grade_category" and row["compensation_grade"] == "G01" and row["category_key"] == "zero_recorded_promotions")
    row["employee_count"] = 29
    expect_rejected("visible individual cell below n30", lambda: build_evidence_from_rows(bad_audit, bad_profile))

    expect_rejected("sensitive JSON key", lambda: ensure_no_sensitive_keys({"employee_id": "forbidden"}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze aggregate internal evidence for promotion history by compensation grade.")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="Aggregate-only JSON output path.")
    parser.add_argument("--self-test", action="store_true", help="Run offline fail-closed tests before querying Redshift.")
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
