"""Freeze presentation-safe aggregate evidence for Time since last promotion.

The published duration is calculated from the latest *recorded* valid promotion
event in the employee's current employment episode.  This script holds query
rows in memory only and writes neither identities nor individual event/start
dates.  It deliberately does not change the historical v4 assessment scores.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SQL = ROOT / "queries" / "audits" / "time_since_last_promotion_event_integrity_20260823.sql"
PROFILE_SQL = ROOT / "queries" / "profiles" / "time_since_last_promotion_distribution_20260823.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "time-since-last-promotion-distribution-evidence-20260910.json"
READONLY_QUERY_HELPER = (
    ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
)
CUTOFF_DATE = "2026-08-23"
MINIMUM_COHORT = 30

BANDS: tuple[tuple[str, str], ...] = (
    ("y0_to_lt1", "0–<1 year"),
    ("y1_to_lt2", "1–<2 years"),
    ("y2_to_lt3", "2–<3 years"),
    ("y3_to_lt5", "3–<5 years"),
    ("y5_plus", "5+ years"),
)
BAND_KEYS = tuple(key for key, _ in BANDS)
BAND_LABELS = dict(BANDS)
NON_TEMPORAL_STATES: tuple[tuple[str, str], ...] = (
    ("no_promotion_recorded_current_episode", "No promotion recorded in current episode"),
    ("history_predates_observed_promotion_events", "History predates observed promotion events"),
    ("episode_start_unknown", "Episode start unknown"),
)
STATE_KEYS = tuple(key for key, _ in NON_TEMPORAL_STATES)
STATE_LABELS = dict(NON_TEMPORAL_STATES)

REQUIRED_AUDIT_METRICS = {
    "candidate_event_before_current_episode_count",
    "employees_with_valid_event_count",
    "future_promotion_date_count",
    "history_conflicting_event_snapshot_count",
    "history_duplicate_employee_snapshot_count",
    "history_duplicate_snapshot_row_excess_count",
    "history_source_row_count",
    "identical_event_duplicate_pair_count",
    "identical_event_duplicate_row_excess_count",
    "invalid_promo_flag_count",
    "promo_flag_without_date_count",
    "promotion_date_after_event_snapshot_count",
    "promotion_date_without_promo_flag_count",
    "selected_latest_event_before_current_episode_count",
    "target_conflicting_event_snapshot_count",
    "target_duplicate_employee_count",
    "target_duplicate_row_excess_count",
    "target_episode_start_future_count",
    "target_episode_start_unknown_count",
    "target_source_row_count",
    "target_unique_employee_count",
    "transfer_date_coincident_with_valid_promotion_event_count",
    "transfer_flag_on_valid_promotion_event_count",
    "valid_event_pair_count",
}
ZERO_REQUIRED_AUDIT_METRICS = {
    "future_promotion_date_count",
    "history_conflicting_event_snapshot_count",
    "history_duplicate_employee_snapshot_count",
    "history_duplicate_snapshot_row_excess_count",
    "invalid_promo_flag_count",
    "promo_flag_without_date_count",
    "promotion_date_after_event_snapshot_count",
    "promotion_date_without_promo_flag_count",
    "selected_latest_event_before_current_episode_count",
    "target_conflicting_event_snapshot_count",
    "target_duplicate_employee_count",
    "target_duplicate_row_excess_count",
    "target_episode_start_future_count",
}
REQUIRED_PROFILE_METRICS = {
    "denominator_active_regular",
    "latest_recorded_promotion_event",
    "two_plus_years",
    "non_temporal_state_total",
}
PROHIBITED_KEYS = {
    "employee_id",
    "employee_ids",
    "emp_name",
    "name",
    "employee_name",
    "email",
    "manager_email",
    "manager_employee_id",
    "manager_name",
    "postal_code",
    "address",
    "home_address",
    "promotion_date",
    "max_hire_rehire_date",
    "raw_rows",
    "raw_query_rows",
    "query_rows",
    "source_rows",
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


def ensure_no_sensitive_keys(value: object) -> None:
    """Fail closed if a frozen artifact would contain restricted row data."""
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in PROHIBITED_KEYS:
                raise ValueError(f"Frozen evidence attempted to persist a prohibited key: {key!r}.")
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
    """Run one saved aggregate-only SQL statement and retain its rows in memory."""
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
        raise ValueError("The promotion-event audit returned no aggregate rows.")
    metrics: dict[str, int] = {}
    for row in rows:
        if set(row) != {"row_type", "metric", "metric_value"} or row["row_type"] != "metric":
            raise ValueError("The promotion-event audit returned an unexpected aggregate schema.")
        metric = str(row["metric"])
        if metric in metrics:
            raise ValueError(f"The promotion-event audit duplicated metric {metric!r}.")
        metrics[metric] = numeric_int(row["metric_value"], metric)
    missing = sorted(REQUIRED_AUDIT_METRICS - set(metrics))
    extra = sorted(set(metrics) - REQUIRED_AUDIT_METRICS)
    if missing or extra:
        raise ValueError(f"Promotion-event audit metric contract mismatch; missing={missing}, extra={extra}.")
    return metrics


def parse_profile_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, int], dict[str, int], str]:
    if not rows:
        raise ValueError("The promotion distribution profile returned no aggregate rows.")
    metrics: dict[str, int] = {}
    bands: dict[str, int] = {}
    states: dict[str, int] = {}
    history_start: str | None = None
    for row in rows:
        if set(row) != {"snapshot_date", "row_type", "bucket_key", "employee_count", "observed_history_start_date"}:
            raise ValueError("The promotion distribution profile returned an unexpected aggregate schema.")
        if str(row["snapshot_date"]) != CUTOFF_DATE:
            raise ValueError("Snapshot mismatch: promotion evidence must use 2026-08-23 only.")
        row_type = str(row["row_type"])
        key = str(row["bucket_key"])
        count = numeric_int(row["employee_count"], f"{row_type}:{key}")
        if count < 0:
            raise ValueError("The promotion distribution profile contains a negative count.")
        if row_type == "metric":
            if key not in REQUIRED_PROFILE_METRICS or key in metrics or row["observed_history_start_date"] is not None:
                raise ValueError("The promotion distribution profile has an invalid metric row.")
            metrics[key] = count
        elif row_type == "band":
            if key not in BAND_KEYS or key in bands or row["observed_history_start_date"] is not None:
                raise ValueError("The promotion distribution profile has an invalid time-band row.")
            bands[key] = count
        elif row_type == "state":
            if key not in STATE_KEYS or key in states or row["observed_history_start_date"] is not None:
                raise ValueError("The promotion distribution profile has an invalid non-temporal-state row.")
            states[key] = count
        elif row_type == "observability":
            if key != "observed_promotion_history_start" or count != 0 or history_start is not None:
                raise ValueError("The promotion distribution profile has an invalid observability row.")
            history_start = str(row["observed_history_start_date"])
            try:
                date.fromisoformat(history_start)
            except ValueError as exc:
                raise ValueError("The observed promotion-history start must use ISO YYYY-MM-DD.") from exc
        else:
            raise ValueError(f"The promotion distribution profile has unsupported row type {row_type!r}.")
    if set(metrics) != REQUIRED_PROFILE_METRICS:
        raise ValueError("The promotion distribution profile is missing a required metric.")
    if tuple(bands) != BAND_KEYS:
        raise ValueError("The promotion distribution profile is missing or reordering time bands.")
    required_states = set(STATE_KEYS[:2])
    if not required_states.issubset(states) or not set(states).issubset(STATE_KEYS):
        raise ValueError("The promotion distribution profile is missing a required non-temporal state.")
    if history_start is None:
        raise ValueError("The promotion distribution profile is missing its observed-history boundary.")
    return metrics, bands, states, history_start


def validate_inputs(audit: dict[str, int], metrics: dict[str, int], bands: dict[str, int], states: dict[str, int]) -> None:
    failed_safeguards = [metric for metric in sorted(ZERO_REQUIRED_AUDIT_METRICS) if audit[metric] != 0]
    if failed_safeguards:
        raise ValueError(f"Promotion distribution rejected by nonzero safeguards: {', '.join(failed_safeguards)}.")
    if audit["target_source_row_count"] != audit["target_unique_employee_count"]:
        raise ValueError("The target snapshot source rows do not reconcile to distinct employees.")
    if audit["target_unique_employee_count"] < MINIMUM_COHORT:
        raise ValueError("The active-regular snapshot is below the minimum publication cohort.")
    if metrics["denominator_active_regular"] != audit["target_unique_employee_count"]:
        raise ValueError("The profile denominator does not reconcile to the audited active-regular snapshot.")
    if metrics["latest_recorded_promotion_event"] != audit["employees_with_valid_event_count"]:
        raise ValueError("The latest-promotion count does not reconcile to the validated event audit.")
    if sum(bands.values()) != metrics["latest_recorded_promotion_event"]:
        raise ValueError("Time bands do not reconcile to employees with a latest recorded promotion event.")
    if sum(states.values()) != metrics["non_temporal_state_total"]:
        raise ValueError("Non-temporal states do not reconcile to their profile total.")
    if metrics["latest_recorded_promotion_event"] + metrics["non_temporal_state_total"] != metrics["denominator_active_regular"]:
        raise ValueError("Time bands plus non-temporal states do not reconcile to the full denominator.")
    calculated_two_plus = sum(bands[key] for key in ("y2_to_lt3", "y3_to_lt5", "y5_plus"))
    if calculated_two_plus != metrics["two_plus_years"]:
        raise ValueError("The 2+ years KPI does not equal the required three time bands.")
    if any(count < MINIMUM_COHORT for count in bands.values()):
        raise ValueError(f"A time band is below the presentation threshold n={MINIMUM_COHORT}.")
    if any(count < MINIMUM_COHORT for count in states.values()):
        raise ValueError(f"A non-temporal state is below the presentation threshold n={MINIMUM_COHORT}.")
    if audit["target_episode_start_unknown_count"] == 0 and "episode_start_unknown" in states:
        raise ValueError("Episode-start-unknown state appears despite zero audited unknown episode starts.")
    if audit["target_episode_start_unknown_count"] > 0:
        if states.get("episode_start_unknown") != audit["target_episode_start_unknown_count"]:
            raise ValueError("Episode-start-unknown state does not reconcile to the audit.")


def check_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
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
    """Create a validated, aggregate-only evidence payload from in-memory rows."""
    audit = parse_audit_rows(audit_rows)
    metrics, band_counts, state_counts, history_start = parse_profile_rows(profile_rows)
    validate_inputs(audit, metrics, band_counts, state_counts)

    denominator = metrics["denominator_active_regular"]
    distribution = [
        {
            "key": key,
            "label": BAND_LABELS[key],
            "employee_count": band_counts[key],
            "percent_of_active_regular": 100.0 * band_counts[key] / denominator,
        }
        for key in BAND_KEYS
    ]
    non_temporal_states = [
        {
            "key": key,
            "label": STATE_LABELS[key],
            "employee_count": state_counts[key],
            "percent_of_active_regular": 100.0 * state_counts[key] / denominator,
        }
        for key in STATE_KEYS
        if key in state_counts
    ]
    all_percentages = [float(row["percent_of_active_regular"]) for row in distribution + non_temporal_states]
    if not math.isclose(sum(all_percentages), 100.0, abs_tol=0.0000001):
        raise ValueError("Unrounded band and non-temporal-state percentages do not sum to 100%.")

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
        "deliverable_mode": "presentation",
        "variable": "Time since last promotion",
        "semantic_type": "derived_feature",
        "publication_status": "validated_descriptive_distribution",
        "execution_date": execution_date or date.today().isoformat(),
        "snapshot_date": CUTOFF_DATE,
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 at the 2026-08-23 monthly snapshot",
        "grain": "Distinct active regular employee at one monthly snapshot",
        "definition": {
            "latest_recorded_promotion_event": "Latest distinct promotion_date where is_promo=1, promotion_date is not future or after its event snapshot, and promotion_date is on or after max_hire_rehire_date for the active employee's current episode.",
            "duration": "Calendar-anniversary bands from the latest recorded valid promotion event to the 2026-08-23 cutoff.",
            "deduplication": "Identical employee + promotion_date events are counted once.",
            "rehire_policy": "Events dated before max_hire_rehire_date are excluded from the current episode.",
            "left_censoring": "When the current episode starts before observed promotion-event history and no valid event remains, the employee is retained as History predates observed promotion events, not assigned a duration.",
            "transfer_policy": "is_transferred and transfer_date are excluded from the formula; coincidence is retained only as aggregate audit context.",
        },
        "history_observability": {
            "observed_promotion_history_start_date": history_start,
            "interpretation": "Observed source-history boundary, not a claim that promotion history before that date is complete.",
        },
        "distribution": distribution,
        "non_temporal_states": non_temporal_states,
        "metrics": {
            "active_regular_employee_count": denominator,
            "latest_recorded_promotion_event_count": metrics["latest_recorded_promotion_event"],
            "non_temporal_state_count": metrics["non_temporal_state_total"],
            "two_plus_years_employee_count": metrics["two_plus_years"],
            "two_plus_years_percent_of_active_regular": 100.0 * metrics["two_plus_years"] / denominator,
            "current_episode_events_excluded_before_rehire_count": audit["candidate_event_before_current_episode_count"],
            "identical_event_duplicate_pairs_deduplicated": audit["identical_event_duplicate_pair_count"],
            "transfer_flag_on_valid_promotion_event_count": audit["transfer_flag_on_valid_promotion_event_count"],
            "transfer_date_coincident_with_valid_promotion_event_count": audit["transfer_date_coincident_with_valid_promotion_event_count"],
            "minimum_published_bucket_count": min(
                [row["employee_count"] for row in distribution + non_temporal_states]
            ),
            "minimum_cohort": MINIMUM_COHORT,
        },
        "validation": {
            "event_integrity": {
                "outcome": "pass",
                "acceptance_rule": "No target/history snapshot duplicates or event conflicts; flags are binary; event dates are populated, nonfuture, and not later than their snapshot; selected events are not before the current episode.",
            },
            "reconciliation": {
                "outcome": "pass",
                "acceptance_rule": "Time bands plus non-temporal states equal every active regular employee; unrounded shares equal 100%; and 2+ years equals 2–<3 + 3–<5 + 5+ years.",
            },
            "privacy": {
                "outcome": "pass",
                "acceptance_rule": "Presentation artifact contains aggregate counts only, no protected-category labels or individual fields, and every displayed bucket is at least n=30.",
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
            "protected_category_labels_persisted": False,
            "all_displayed_buckets_meet_minimum": True,
            "minimum_cohort": MINIMUM_COHORT,
        },
        "score_v4_change": "none",
        "limitation": "This descriptive chart reports latest recorded promotion events in observed history. It does not establish an approved promotion policy, classify employees with no recorded current-episode event as never promoted, or assert a causal relationship with attrition.",
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
    """Return a valid aggregate fixture for fail-closed contract tests."""
    audit_values = {metric: 0 for metric in REQUIRED_AUDIT_METRICS}
    audit_values.update(
        {
            "target_source_row_count": 1000,
            "target_unique_employee_count": 1000,
            "history_source_row_count": 24000,
            "valid_event_pair_count": 650,
            "employees_with_valid_event_count": 600,
            "candidate_event_before_current_episode_count": 11,
        }
    )
    audit_rows = [
        {"row_type": "metric", "metric": metric, "metric_value": value}
        for metric, value in sorted(audit_values.items())
    ]
    profile_rows: list[dict[str, Any]] = [
        {"snapshot_date": CUTOFF_DATE, "row_type": "metric", "bucket_key": "denominator_active_regular", "employee_count": 1000, "observed_history_start_date": None},
        {"snapshot_date": CUTOFF_DATE, "row_type": "metric", "bucket_key": "latest_recorded_promotion_event", "employee_count": 600, "observed_history_start_date": None},
        {"snapshot_date": CUTOFF_DATE, "row_type": "metric", "bucket_key": "two_plus_years", "employee_count": 350, "observed_history_start_date": None},
        {"snapshot_date": CUTOFF_DATE, "row_type": "metric", "bucket_key": "non_temporal_state_total", "employee_count": 400, "observed_history_start_date": None},
        {"snapshot_date": CUTOFF_DATE, "row_type": "observability", "bucket_key": "observed_promotion_history_start", "employee_count": 0, "observed_history_start_date": "2016-10-23"},
        {"snapshot_date": CUTOFF_DATE, "row_type": "band", "bucket_key": "y0_to_lt1", "employee_count": 120, "observed_history_start_date": None},
        {"snapshot_date": CUTOFF_DATE, "row_type": "band", "bucket_key": "y1_to_lt2", "employee_count": 130, "observed_history_start_date": None},
        {"snapshot_date": CUTOFF_DATE, "row_type": "band", "bucket_key": "y2_to_lt3", "employee_count": 140, "observed_history_start_date": None},
        {"snapshot_date": CUTOFF_DATE, "row_type": "band", "bucket_key": "y3_to_lt5", "employee_count": 100, "observed_history_start_date": None},
        {"snapshot_date": CUTOFF_DATE, "row_type": "band", "bucket_key": "y5_plus", "employee_count": 110, "observed_history_start_date": None},
        {"snapshot_date": CUTOFF_DATE, "row_type": "state", "bucket_key": "history_predates_observed_promotion_events", "employee_count": 100, "observed_history_start_date": None},
        {"snapshot_date": CUTOFF_DATE, "row_type": "state", "bucket_key": "no_promotion_recorded_current_episode", "employee_count": 300, "observed_history_start_date": None},
    ]
    return audit_rows, profile_rows


def replace_metric(rows: list[dict[str, Any]], metric: str, value: int) -> None:
    for row in rows:
        if row.get("metric") == metric:
            row["metric_value"] = value
            return
    raise AssertionError(f"Synthetic metric {metric!r} not found.")


def replace_profile_count(rows: list[dict[str, Any]], row_type: str, key: str, value: int) -> None:
    for row in rows:
        if row.get("row_type") == row_type and row.get("bucket_key") == key:
            row["employee_count"] = value
            return
    raise AssertionError(f"Synthetic profile row {row_type}/{key!r} not found.")


def expect_rejected(label: str, callback: Any) -> None:
    try:
        callback()
    except ValueError:
        return
    raise AssertionError(f"Expected rejection was not raised: {label}")


def self_test() -> None:
    """Exercise the required fail-closed integrity, privacy, and transfer controls."""
    audit_rows, profile_rows = synthetic_rows()
    baseline = build_evidence_from_rows(audit_rows, profile_rows, execution_date="2026-09-10")
    assert baseline["metrics"]["two_plus_years_employee_count"] == 350

    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    bad_profile[0]["snapshot_date"] = "2026-08-24"
    expect_rejected("wrong snapshot", lambda: build_evidence_from_rows(bad_audit, bad_profile))

    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    replace_metric(bad_audit, "history_conflicting_event_snapshot_count", 1)
    expect_rejected("flag/date conflict", lambda: build_evidence_from_rows(bad_audit, bad_profile))

    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    replace_metric(bad_audit, "future_promotion_date_count", 1)
    expect_rejected("future promotion date", lambda: build_evidence_from_rows(bad_audit, bad_profile))

    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    replace_metric(bad_audit, "selected_latest_event_before_current_episode_count", 1)
    expect_rejected("pre-rehire event selected", lambda: build_evidence_from_rows(bad_audit, bad_profile))

    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    replace_metric(bad_audit, "target_duplicate_employee_count", 1)
    replace_metric(bad_audit, "target_conflicting_event_snapshot_count", 1)
    expect_rejected("duplicate/conflicting target snapshot", lambda: build_evidence_from_rows(bad_audit, bad_profile))

    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    replace_profile_count(bad_profile, "metric", "denominator_active_regular", 1001)
    expect_rejected("unreconciled total", lambda: build_evidence_from_rows(bad_audit, bad_profile))

    expect_rejected("sensitive JSON key", lambda: ensure_no_sensitive_keys({"employee_id": "forbidden"}))

    bad_audit, bad_profile = deepcopy(audit_rows), deepcopy(profile_rows)
    replace_profile_count(bad_profile, "band", "y0_to_lt1", 29)
    replace_profile_count(bad_profile, "band", "y1_to_lt2", 221)
    expect_rejected("bucket below minimum cohort", lambda: build_evidence_from_rows(bad_audit, bad_profile))

    transfer_audit = deepcopy(audit_rows)
    replace_metric(transfer_audit, "transfer_flag_on_valid_promotion_event_count", 7)
    replace_metric(transfer_audit, "transfer_date_coincident_with_valid_promotion_event_count", 4)
    transfer_evidence = build_evidence_from_rows(transfer_audit, deepcopy(profile_rows), execution_date="2026-09-10")
    if transfer_evidence["distribution"] != baseline["distribution"] or transfer_evidence["non_temporal_states"] != baseline["non_temporal_states"]:
        raise AssertionError("Transfer diagnostics altered the promotion-duration result.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze aggregate presentation evidence for Time since last promotion.")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="Presentation-safe JSON output path.")
    parser.add_argument("--self-test", action="store_true", help="Run offline fail-closed contract tests before querying Redshift.")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("self-test=pass")
    evidence = build_and_write(args.output)
    print(args.output)
    print(f"active_regular={evidence['metrics']['active_regular_employee_count']}")
    print(f"two_plus_years={evidence['metrics']['two_plus_years_employee_count']}")


if __name__ == "__main__":
    main()
