"""Freeze presentation-safe evidence for the manager-level pay-spread distribution.

The slide keeps its historical title, ``Within team compensation range``, but
now describes a clearly bounded manager-level signal: count and share of
comparable direct-report groups whose FTE-adjusted base-pay spread is >=10%.
Only aggregate counts are written.  Manager, employee, country, grade,
currency, and compensation values remain in Redshift query memory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SQL = ROOT / "queries" / "audits" / "within_team_compensation_pay_spread_integrity_20260823.sql"
PROFILE_SQL = ROOT / "queries" / "profiles" / "within_team_compensation_pay_spread_distribution_20260823.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "within-team-compensation-pay-spread-evidence-20260910.json"
READONLY_QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
CUTOFF_DATE = "2026-08-23"
MINIMUM_COHORT = 30
PAY_SPREAD_THRESHOLD = 0.10

REQUIRED_AUDIT_METRICS = {
    "target_source_row_count",
    "target_unique_employee_count",
    "target_duplicate_employee_count",
    "target_duplicate_row_excess_count",
    "active_employee_duplicate_key_count",
    "active_employee_duplicate_row_excess_count",
    "reporter_without_manager_count",
    "reporter_with_unresolved_manager_count",
    "reporter_with_nonpositive_manager_flag_count",
    "manager_universe_count",
    "manager_member_report_count",
    "missing_country_member_count",
    "missing_grade_member_count",
    "missing_currency_member_count",
    "invalid_fte_annual_base_pay_member_count",
    "complete_member_count",
    "country_grade_currency_conflict_cell_count",
    "candidate_group_count",
    "singleton_group_count",
    "eligible_group_count",
    "flagged_eligible_group_count",
    "comparable_manager_count",
    "no_comparable_group_manager_count",
    "manager_reconciliation_difference",
}
REQUIRED_PROFILE_METRICS = {
    "manager_universe",
    "comparable_managers",
    "no_comparable_group_managers",
    "eligible_comparable_groups",
    "flagged_comparable_groups",
}
RATE_BANDS: tuple[tuple[str, str], ...] = (
    ("rate_0", "0%"),
    ("rate_gt0_lt25", ">0–<25%"),
    ("rate_25_lt50", "25–<50%"),
    ("rate_50_lt75", "50–<75%"),
    ("rate_75_lt100", "75–<100%"),
    ("rate_100", "100%"),
)
RATE_LABELS = dict(RATE_BANDS)
RATE_KEYS = tuple(key for key, _ in RATE_BANDS)
PROHIBITED_KEYS = {
    "employee_id", "employee_ids", "emp_name", "name", "employee_name", "email",
    "manager_employee_id", "manager_name", "manager_email", "country_values",
    "compensation_grade_values", "currency_values", "annual_base_pay", "fte_annual_base_pay",
    "raw_rows", "raw_query_rows", "query_rows", "source_rows", "salary", "salaries",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_json(value: object) -> str:
    return sha256_bytes(
        json.dumps(value, sort_keys=True, ensure_ascii=True, default=str, separators=(",", ":")).encode("utf-8")
    )


def numeric_int(value: object, label: str) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric.") from exc
    if not number.is_integer():
        raise ValueError(f"{label} must be an integer.")
    result = int(number)
    if result < 0:
        raise ValueError(f"{label} must not be negative.")
    return result


def ensure_no_sensitive_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in PROHIBITED_KEYS:
                raise ValueError(f"Frozen evidence attempted to persist a prohibited key: {key!r}.")
            ensure_no_sensitive_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            ensure_no_sensitive_keys(nested)


def check_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest.")


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
    """Run a saved read-only aggregate query without persisting its rows."""
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
        if set(row) != {"metric", "metric_value"}:
            raise ValueError("Pay-spread audit returned an unexpected aggregate schema.")
        key = str(row["metric"])
        if key in metrics:
            raise ValueError(f"Pay-spread audit duplicated {key!r}.")
        metrics[key] = numeric_int(row["metric_value"], f"audit:{key}")
    if set(metrics) != REQUIRED_AUDIT_METRICS:
        raise ValueError("Pay-spread audit metric contract mismatch.")
    return metrics


def parse_profile_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, int], dict[int, int], dict[str, int], int]:
    metrics: dict[str, int] = {}
    count_distribution: dict[int, int] = {}
    rate_distribution: dict[str, int] = {}
    no_comparable_state: int | None = None
    for row in rows:
        if set(row) != {"snapshot_date", "row_type", "bucket_key", "manager_count"}:
            raise ValueError("Pay-spread profile returned an unexpected aggregate schema.")
        if str(row["snapshot_date"]) != CUTOFF_DATE:
            raise ValueError("Pay-spread profile must use the 2026-08-23 cutoff.")
        row_type = str(row["row_type"])
        key = str(row["bucket_key"])
        count = numeric_int(row["manager_count"], f"profile:{row_type}:{key}")
        if row_type == "metric":
            if key not in REQUIRED_PROFILE_METRICS or key in metrics:
                raise ValueError("Pay-spread profile has an invalid metric row.")
            metrics[key] = count
        elif row_type == "count_distribution":
            try:
                flagged_group_count = int(key)
            except ValueError as exc:
                raise ValueError("Count-distribution bucket must be an integer.") from exc
            if flagged_group_count < 0 or flagged_group_count in count_distribution:
                raise ValueError("Pay-spread count distribution is invalid.")
            count_distribution[flagged_group_count] = count
        elif row_type == "rate_distribution":
            if key not in RATE_KEYS or key in rate_distribution:
                raise ValueError("Pay-spread rate distribution is invalid.")
            rate_distribution[key] = count
        elif row_type == "state":
            if key != "no_comparable_groups" or no_comparable_state is not None:
                raise ValueError("Pay-spread profile has an invalid state row.")
            no_comparable_state = count
        else:
            raise ValueError(f"Unsupported pay-spread profile row type {row_type!r}.")
    if set(metrics) != REQUIRED_PROFILE_METRICS:
        raise ValueError("Pay-spread profile is missing required metrics.")
    if not count_distribution or not rate_distribution or no_comparable_state is None:
        raise ValueError("Pay-spread profile is missing a distribution or state.")
    return metrics, count_distribution, rate_distribution, no_comparable_state


def validate_inputs(
    audit: dict[str, int],
    metrics: dict[str, int],
    count_distribution: dict[int, int],
    rate_distribution: dict[str, int],
    no_comparable_state: int,
) -> None:
    zero_required = {
        "target_duplicate_employee_count",
        "target_duplicate_row_excess_count",
        "active_employee_duplicate_key_count",
        "active_employee_duplicate_row_excess_count",
        "reporter_with_unresolved_manager_count",
        "reporter_with_nonpositive_manager_flag_count",
        "manager_reconciliation_difference",
    }
    failures = sorted(metric for metric in zero_required if audit[metric] != 0)
    if failures:
        raise ValueError(f"Pay-spread evidence rejected by safeguards: {', '.join(failures)}.")
    if audit["target_source_row_count"] != audit["target_unique_employee_count"]:
        raise ValueError("Active-regular snapshot rows do not reconcile to unique employees.")
    if audit["target_unique_employee_count"] < MINIMUM_COHORT:
        raise ValueError("Active-regular population is below the publication threshold.")
    if metrics["manager_universe"] != audit["manager_universe_count"]:
        raise ValueError("Manager universe does not reconcile to the audit.")
    if metrics["comparable_managers"] != audit["comparable_manager_count"]:
        raise ValueError("Comparable manager count does not reconcile to the audit.")
    if metrics["no_comparable_group_managers"] != audit["no_comparable_group_manager_count"]:
        raise ValueError("No-comparable state does not reconcile to the audit.")
    if no_comparable_state != metrics["no_comparable_group_managers"]:
        raise ValueError("No-comparable state row does not reconcile to the profile metric.")
    if metrics["comparable_managers"] + no_comparable_state != metrics["manager_universe"]:
        raise ValueError("Comparable and no-comparable managers do not reconcile to the manager universe.")
    if sum(count_distribution.values()) != metrics["comparable_managers"]:
        raise ValueError("Count distribution does not reconcile to comparable managers.")
    if sum(rate_distribution.values()) != metrics["comparable_managers"]:
        raise ValueError("Rate distribution does not reconcile to comparable managers.")
    if metrics["eligible_comparable_groups"] != audit["eligible_group_count"]:
        raise ValueError("Eligible group count does not reconcile to the audit.")
    if metrics["flagged_comparable_groups"] != audit["flagged_eligible_group_count"]:
        raise ValueError("Flagged group count does not reconcile to the audit.")
    if metrics["flagged_comparable_groups"] > metrics["eligible_comparable_groups"]:
        raise ValueError("Flagged group count exceeds eligible groups.")


def _count_label(lower: int, upper: int) -> str:
    if lower == upper:
        return f"{lower} flagged group" if lower == 1 else f"{lower} flagged groups"
    return f"{lower}–{upper} flagged groups"


def collapse_count_distribution(raw: dict[int, int]) -> list[dict[str, object]]:
    """Keep exact safe counts; combine adjacent sparse counts without persisting them."""
    ordered = sorted((key, value) for key, value in raw.items() if value > 0)
    if not ordered:
        raise ValueError("There are no comparable-manager count buckets to publish.")
    buckets: list[tuple[int, int, int]] = []
    lower: int | None = None
    upper: int | None = None
    total = 0
    for key, count in ordered:
        if lower is None:
            lower = key
        upper = key
        total += count
        if total >= MINIMUM_COHORT:
            buckets.append((lower, upper, total))
            lower = None
            upper = None
            total = 0
    if lower is not None and upper is not None:
        if not buckets:
            raise ValueError("Comparable-manager count distribution is below the publication threshold.")
        previous_lower, _, previous_total = buckets.pop()
        buckets.append((previous_lower, upper, previous_total + total))
    published = [
        {"key": f"count_{lower}_{upper}", "label": _count_label(lower, upper), "manager_count": total}
        for lower, upper, total in buckets
    ]
    if any(int(item["manager_count"]) < MINIMUM_COHORT for item in published):
        raise ValueError("A published count bucket is below the cohort threshold.")
    return published


def collapse_rate_distribution(raw: dict[str, int]) -> list[dict[str, object]]:
    """Combine adjacent sparse percentage bands while retaining an ordered range."""
    numeric_ranges = {
        "rate_0": (0.0, 0.0, "0%"),
        "rate_gt0_lt25": (0.0, 25.0, ">0–<25%"),
        "rate_25_lt50": (25.0, 50.0, "25–<50%"),
        "rate_50_lt75": (50.0, 75.0, "50–<75%"),
        "rate_75_lt100": (75.0, 100.0, "75–<100%"),
        "rate_100": (100.0, 100.0, "100%"),
    }
    active = [(key, raw.get(key, 0)) for key in RATE_KEYS if raw.get(key, 0) > 0]
    if not active:
        raise ValueError("There are no comparable-manager rate buckets to publish.")
    merged: list[tuple[int, int, int]] = []
    start: int | None = None
    end: int | None = None
    total = 0
    for index, (_, count) in enumerate(active):
        if start is None:
            start = index
        end = index
        total += count
        if total >= MINIMUM_COHORT:
            merged.append((start, end, total))
            start = None
            end = None
            total = 0
    if start is not None and end is not None:
        if not merged:
            raise ValueError("Comparable-manager rate distribution is below the publication threshold.")
        prior_start, _, prior_total = merged.pop()
        merged.append((prior_start, end, prior_total + total))
    published: list[dict[str, object]] = []
    for start_index, end_index, count in merged:
        start_key = active[start_index][0]
        end_key = active[end_index][0]
        lower, _, start_label = numeric_ranges[start_key]
        _, upper, end_label = numeric_ranges[end_key]
        if start_key == end_key:
            label = start_label
        elif lower == 0.0 and upper == 100.0:
            label = "0–100%"
        elif start_key == "rate_gt0_lt25":
            label = f">0–<{int(upper)}%"
        elif lower == 0.0:
            label = f"0–<{int(upper)}%"
        elif upper == 100.0:
            label = f"{int(lower)}–100%"
        else:
            label = f"{int(lower)}–<{int(upper)}%"
        published.append({"key": f"{start_key}_to_{end_key}", "label": label, "manager_count": count})
    if any(int(item["manager_count"]) < MINIMUM_COHORT for item in published):
        raise ValueError("A published rate bucket is below the cohort threshold.")
    return published


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
    audit = parse_audit_rows(audit_rows)
    metrics, count_raw, rate_raw, no_comparable = parse_profile_rows(profile_rows)
    validate_inputs(audit, metrics, count_raw, rate_raw, no_comparable)
    count_distribution = collapse_count_distribution(count_raw)
    rate_distribution = collapse_rate_distribution(rate_raw)
    no_comparable_rows = []
    if no_comparable:
        if no_comparable < MINIMUM_COHORT:
            raise ValueError("No-comparable manager state is below the publication threshold.")
        no_comparable_rows = [{"key": "no_comparable_groups", "label": "No comparable groups", "manager_count": no_comparable}]
    if sum(int(row["manager_count"]) for row in count_distribution) != metrics["comparable_managers"]:
        raise ValueError("Published count buckets do not reconcile to comparable managers.")
    if sum(int(row["manager_count"]) for row in rate_distribution) != metrics["comparable_managers"]:
        raise ValueError("Published rate buckets do not reconcile to comparable managers.")

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

    comparable = metrics["comparable_managers"]
    def with_percent(rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            {
                **row,
                "percent_of_comparable_managers": 100.0 * int(row["manager_count"]) / comparable,
            }
            for row in rows
        ]

    evidence: dict[str, object] = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "presentation",
        "variable": "Within team compensation range",
        "semantic_type": "derived_feature",
        "publication_status": "validated_descriptive_distribution",
        "execution_date": execution_date or date.today().isoformat(),
        "snapshot_date": CUTOFF_DATE,
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 at the 2026-08-23 monthly snapshot",
        "grain": "Direct-manager team at one monthly snapshot; manager is excluded from their own report group",
        "definition": {
            "team_membership": "Active regular direct reports sharing manager_employee_id in the cutoff snapshot; reg_non_intern_dir_reports > 0 corroborates the manager record.",
            "comparable_group": "Within one direct-manager team, direct reports sharing country, compensation_grade, and FTE annual-base-pay currency.",
            "eligibility": "At least two direct reports with nonblank country, compensation_grade, currency, and positive fte_annual_base_pay. Missing inputs and singleton groups do not form a comparable group.",
            "pay_spread": "max(fte_annual_base_pay) / min(fte_annual_base_pay) - 1, calculated only inside an eligible comparable group.",
            "flag_rule": "A comparable group is flagged when its FTE-adjusted base-pay spread is at least 10%.",
            "manager_metrics": "For each manager with one or more eligible groups: flagged-group count and flagged-group share of eligible comparable groups. Managers with no eligible group are kept in a separate No comparable groups state, not assigned zero.",
        },
        "distributions": {
            "flagged_group_count_per_team": with_percent(count_distribution),
            "flagged_group_share_per_team": with_percent(rate_distribution),
            "non_comparable_state": no_comparable_rows,
        },
        "metrics": {
            "active_regular_employee_count": audit["target_unique_employee_count"],
            "manager_universe_count": metrics["manager_universe"],
            "comparable_manager_count": comparable,
            "no_comparable_group_manager_count": no_comparable,
            "eligible_comparable_group_count": metrics["eligible_comparable_groups"],
            "flagged_comparable_group_count": metrics["flagged_comparable_groups"],
            "flagged_comparable_group_percent": 100.0 * metrics["flagged_comparable_groups"] / metrics["eligible_comparable_groups"] if metrics["eligible_comparable_groups"] else 0.0,
            "complete_member_count": audit["complete_member_count"],
            "excluded_missing_required_input_member_count": (
                audit["manager_member_report_count"] - audit["complete_member_count"]
            ),
            "singleton_group_count": audit["singleton_group_count"],
            "minimum_published_bucket_count": min(
                [int(row["manager_count"]) for row in count_distribution + rate_distribution + no_comparable_rows]
            ),
            "minimum_cohort": MINIMUM_COHORT,
            "pay_spread_threshold_percent": PAY_SPREAD_THRESHOLD * 100,
        },
        "validation": {
            "membership_integrity": {
                "outcome": "pass",
                "acceptance_rule": "No active-regular or active-manager snapshot duplicate keys; every assigned direct-report manager resolves uniquely and has reg_non_intern_dir_reports > 0.",
            },
            "reconciliation": {
                "outcome": "pass",
                "acceptance_rule": "Comparable-manager count and No comparable groups state reconcile to the direct-manager universe; both count and rate distributions reconcile to comparable managers; flagged groups do not exceed eligible groups.",
            },
            "privacy": {
                "outcome": "pass",
                "acceptance_rule": "Presentation evidence stores aggregate manager counts only; all displayed buckets meet n >= 30 and omit identifiers, country/grade/currency labels, and pay values.",
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
            "manager_rows_persisted": False,
            "exact_compensation_persisted": False,
            "country_grade_currency_labels_persisted": False,
            "all_displayed_buckets_meet_minimum": True,
            "minimum_cohort": MINIMUM_COHORT,
        },
        "score_v4_change": "none",
        "limitation": "This is a descriptive review signal, not a pay-equity finding. It does not model tenure, performance, job profile, labor-market differences within a country, or other legitimate compensation factors. The stored FTE annual-base-pay field is used as an operational normalization and does not establish authoritative compensation lineage.",
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
    audit = {metric: 0 for metric in REQUIRED_AUDIT_METRICS}
    audit.update({
        "target_source_row_count": 1000,
        "target_unique_employee_count": 1000,
        "reporter_without_manager_count": 1,
        "manager_universe_count": 250,
        "manager_member_report_count": 999,
        "complete_member_count": 960,
        "candidate_group_count": 400,
        "singleton_group_count": 120,
        "eligible_group_count": 320,
        "flagged_eligible_group_count": 100,
        "comparable_manager_count": 200,
        "no_comparable_group_manager_count": 50,
    })
    audit_rows = [{"metric": key, "metric_value": value} for key, value in sorted(audit.items())]
    profile_rows = [
        {"snapshot_date": CUTOFF_DATE, "row_type": "metric", "bucket_key": "manager_universe", "manager_count": 250},
        {"snapshot_date": CUTOFF_DATE, "row_type": "metric", "bucket_key": "comparable_managers", "manager_count": 200},
        {"snapshot_date": CUTOFF_DATE, "row_type": "metric", "bucket_key": "no_comparable_group_managers", "manager_count": 50},
        {"snapshot_date": CUTOFF_DATE, "row_type": "metric", "bucket_key": "eligible_comparable_groups", "manager_count": 320},
        {"snapshot_date": CUTOFF_DATE, "row_type": "metric", "bucket_key": "flagged_comparable_groups", "manager_count": 100},
        {"snapshot_date": CUTOFF_DATE, "row_type": "count_distribution", "bucket_key": "0", "manager_count": 100},
        {"snapshot_date": CUTOFF_DATE, "row_type": "count_distribution", "bucket_key": "1", "manager_count": 60},
        {"snapshot_date": CUTOFF_DATE, "row_type": "count_distribution", "bucket_key": "2", "manager_count": 20},
        {"snapshot_date": CUTOFF_DATE, "row_type": "count_distribution", "bucket_key": "3", "manager_count": 10},
        {"snapshot_date": CUTOFF_DATE, "row_type": "count_distribution", "bucket_key": "4", "manager_count": 10},
        {"snapshot_date": CUTOFF_DATE, "row_type": "rate_distribution", "bucket_key": "rate_0", "manager_count": 90},
        {"snapshot_date": CUTOFF_DATE, "row_type": "rate_distribution", "bucket_key": "rate_gt0_lt25", "manager_count": 20},
        {"snapshot_date": CUTOFF_DATE, "row_type": "rate_distribution", "bucket_key": "rate_25_lt50", "manager_count": 10},
        {"snapshot_date": CUTOFF_DATE, "row_type": "rate_distribution", "bucket_key": "rate_50_lt75", "manager_count": 30},
        {"snapshot_date": CUTOFF_DATE, "row_type": "rate_distribution", "bucket_key": "rate_75_lt100", "manager_count": 10},
        {"snapshot_date": CUTOFF_DATE, "row_type": "rate_distribution", "bucket_key": "rate_100", "manager_count": 40},
        {"snapshot_date": CUTOFF_DATE, "row_type": "state", "bucket_key": "no_comparable_groups", "manager_count": 50},
    ]
    return audit_rows, profile_rows


def expect_rejected(label: str, callback: Any) -> None:
    try:
        callback()
    except ValueError:
        return
    raise AssertionError(f"Expected rejection was not raised: {label}")


def self_test() -> None:
    audit_rows, profile_rows = synthetic_rows()
    baseline = build_evidence_from_rows(audit_rows, profile_rows, execution_date="2026-09-10")
    assert baseline["metrics"]["comparable_manager_count"] == 200
    assert baseline["distributions"]["flagged_group_count_per_team"][-1]["manager_count"] == 40

    duplicate_audit = deepcopy(audit_rows)
    next(row for row in duplicate_audit if row["metric"] == "target_duplicate_employee_count")["metric_value"] = 1
    expect_rejected("duplicate snapshot", lambda: build_evidence_from_rows(duplicate_audit, deepcopy(profile_rows)))

    mismatch_profile = deepcopy(profile_rows)
    next(row for row in mismatch_profile if row["row_type"] == "metric" and row["bucket_key"] == "comparable_managers")["manager_count"] = 201
    expect_rejected("unreconciled comparable manager count", lambda: build_evidence_from_rows(deepcopy(audit_rows), mismatch_profile))

    small_state_profile = deepcopy(profile_rows)
    next(row for row in small_state_profile if row["row_type"] == "state")["manager_count"] = 29
    next(row for row in small_state_profile if row["row_type"] == "metric" and row["bucket_key"] == "no_comparable_group_managers")["manager_count"] = 29
    next(row for row in small_state_profile if row["row_type"] == "metric" and row["bucket_key"] == "manager_universe")["manager_count"] = 229
    expect_rejected("small no-comparable state", lambda: build_evidence_from_rows(deepcopy(audit_rows), small_state_profile))

    expect_rejected("sensitive JSON key", lambda: ensure_no_sensitive_keys({"employee_id": "forbidden"}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze presentation-safe manager pay-spread evidence.")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="Presentation-safe JSON output path.")
    parser.add_argument("--self-test", action="store_true", help="Run offline fail-closed contract tests before querying Redshift.")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("self-test=pass")
        return
    evidence = build_and_write(args.output)
    metrics = evidence["metrics"]
    assert isinstance(metrics, dict)
    print(args.output)
    print(f"managers={metrics['manager_universe_count']}; comparable={metrics['comparable_manager_count']}")


if __name__ == "__main__":
    main()
