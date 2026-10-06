"""Freeze aggregate-only evidence for slide 26 career-tenure distributions.

The deck may publish this evidence only after an HRIS authority confirms that
``time_in_job_profile_start_date`` is the current-job-profile start and that
``job_level_primary_position`` is the current detailed-level construct.  The
confirmation is intentionally external to this script: a Tableau caption, a
field name, a historic assessment, or an annual-review field is not accepted.

Raw query rows are kept in memory only.  The resulting JSON retains aggregate
metrics, pooled counts, hashes, and the lineage attestation needed to review a
safe internal-analysis chart.
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
AUDIT_SQL = ROOT / "queries" / "audits" / "role_level_tenure_transition_audit_20260823.sql"
PROFILE_SQL = ROOT / "queries" / "profiles" / "role_level_tenure_distribution_20260823.sql"
SNAPSHOT_DATE = "2026-08-23"
MINIMUM_COHORT = 30
READONLY_QUERY_HELPER = (
    ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
)

BANDS: tuple[tuple[str, str], ...] = (
    ("lt_1", "<1 year"),
    ("y1_to_lt2", "1–<2 years"),
    ("y2_to_lt3", "2–<3 years"),
    ("y3_to_lt5", "3–<5 years"),
    ("y5_to_lt10", "5–<10 years"),
    ("y10_plus", "10+ years"),
)
BAND_KEYS = tuple(key for key, _ in BANDS)
BAND_LABELS = dict(BANDS)

REQUIRED_AUDIT_METRICS = {
    "target_source_row_count",
    "target_unique_employee_count",
    "target_duplicate_employee_count",
    "target_duplicate_row_excess_count",
    "target_conflicting_employee_count",
    "role_start_future_date_count",
    "level_start_future_date_count",
    "rehire_date_future_count",
    "rehire_flag_without_date_count",
    "role_calculable_employee_count",
    "level_calculable_employee_count",
    "role_rehire_adjustment_count",
    "level_rehire_adjustment_count",
    "time_in_role_support_populated_count",
    "history_duplicate_employee_snapshot_count",
    "history_conflicting_employee_snapshot_count",
    "comparable_transition_snapshot_count",
    "detailed_level_transition_count",
    "detailed_level_transition_with_date_reset_count",
    "unexplained_detailed_level_transition_count",
    "unexplained_detailed_level_reset_count",
    "job_profile_start_reset_count",
    "job_profile_reset_with_proxy_change_count",
    "job_profile_reset_without_proxy_change_count",
    "job_proxy_change_without_profile_reset_count",
    "promotion_level_transition_intersection_count",
    "demotion_level_transition_intersection_count",
    "transfer_level_transition_intersection_count",
    "rehire_level_transition_intersection_count",
}

BASE_ZERO_REQUIRED_AUDIT_METRICS = {
    "target_duplicate_employee_count",
    "target_duplicate_row_excess_count",
    "target_conflicting_employee_count",
    "role_start_future_date_count",
    "level_start_future_date_count",
    "rehire_date_future_count",
    "rehire_flag_without_date_count",
    "history_duplicate_employee_snapshot_count",
    "history_conflicting_employee_snapshot_count",
}

STRICT_CONSTRUCT_ZERO_REQUIRED_AUDIT_METRICS = {
    "unexplained_detailed_level_transition_count",
    "unexplained_detailed_level_reset_count",
}

PROHIBITED_KEYS = {
    "employee_id",
    "employee_ids",
    "manager_employee_id",
    "name",
    "employee_name",
    "manager_name",
    "email",
    "job_title",
    "job_code",
    "time_in_job_profile_start_date",
    "levelentrydate",
    "max_hire_rehire_date",
    "raw_rows",
    "raw_query_rows",
    "query_rows",
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
    """Reject any attempt to persist row-level or raw HR values."""
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
    """Execute one saved aggregate-only SQL file without writing its rows."""
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
    """Validate the saved audit's flat aggregate contract."""
    if not rows:
        raise ValueError("The role/level transition audit returned no aggregate rows.")
    metrics: dict[str, int] = {}
    for row in rows:
        if set(row) != {"snapshot_date", "row_type", "metric", "metric_value"}:
            raise ValueError("The role/level transition audit returned an unexpected aggregate schema.")
        if str(row["snapshot_date"]) != SNAPSHOT_DATE:
            raise ValueError("Snapshot mismatch: role/level evidence must use 2026-08-23 only.")
        if row["row_type"] != "metric":
            raise ValueError("The role/level transition audit returned a non-metric row.")
        metric = str(row["metric"])
        if metric in metrics:
            raise ValueError(f"The role/level transition audit duplicated metric {metric!r}.")
        metrics[metric] = numeric_int(row["metric_value"], metric)
    missing = sorted(REQUIRED_AUDIT_METRICS - set(metrics))
    extra = sorted(set(metrics) - REQUIRED_AUDIT_METRICS)
    if missing or extra:
        raise ValueError(f"Role/level audit metric contract mismatch; missing={missing}, extra={extra}.")
    return metrics


def parse_profile_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Validate the two-clock aggregate distribution contract."""
    if not rows:
        raise ValueError("The role/level distribution profile returned no aggregate rows.")
    result = {"role": {"calculable": None, "not_calculable": None}, "level": {"calculable": None, "not_calculable": None}}
    bands = {"role": {}, "level": {}}
    for row in rows:
        if set(row) != {"snapshot_date", "clock", "row_type", "bucket_key", "employee_count"}:
            raise ValueError("The role/level distribution profile returned an unexpected aggregate schema.")
        if str(row["snapshot_date"]) != SNAPSHOT_DATE:
            raise ValueError("Snapshot mismatch: the distribution profile must use 2026-08-23 only.")
        clock = str(row["clock"])
        row_type = str(row["row_type"])
        bucket = str(row["bucket_key"])
        count = numeric_int(row["employee_count"], f"{clock}:{bucket}")
        if clock not in result or count < 0:
            raise ValueError("The distribution profile has an invalid clock or negative count.")
        if row_type == "metric":
            if bucket not in {"calculable", "not_calculable"} or result[clock][bucket] is not None:
                raise ValueError("The distribution profile has an invalid or duplicate metric bucket.")
            result[clock][bucket] = count
        elif row_type == "band":
            if bucket not in BAND_KEYS or bucket in bands[clock]:
                raise ValueError("The distribution profile has an invalid or duplicate tenure band.")
            bands[clock][bucket] = count
        else:
            raise ValueError("The distribution profile has an invalid row type.")
    for clock in ("role", "level"):
        if any(result[clock][name] is None for name in ("calculable", "not_calculable")):
            raise ValueError(f"The distribution profile is missing {clock} coverage metrics.")
        if tuple(bands[clock]) != BAND_KEYS:
            raise ValueError(f"The distribution profile is missing or reordering {clock} tenure bands.")
        if sum(bands[clock].values()) != result[clock]["calculable"]:
            raise ValueError(f"The {clock} bands do not reconcile to its calculable denominator.")
    return {
        "role": {**{key: int(value) for key, value in result["role"].items()}, **bands["role"]},
        "level": {**{key: int(value) for key, value in result["level"].items()}, **bands["level"]},
    }


def normalize_authoritative_lineage(lineage: object) -> dict[str, str]:
    """Require a source-owner confirmation, not a field-name inference."""
    if not isinstance(lineage, dict):
        raise ValueError("Authoritative lineage confirmation must be a JSON object.")
    ensure_no_sensitive_keys(lineage)
    required = {
        "artifact_type",
        "authority",
        "confirmation_date",
        "source_reference",
        "time_in_job_profile_start_date_confirmed_construct",
        "job_level_primary_position_confirmed_construct",
        "approved",
    }
    missing = sorted(required - set(lineage))
    if missing:
        raise ValueError(f"Authoritative lineage confirmation is missing fields: {missing}.")
    if lineage.get("artifact_type") != "authoritative_lineage_confirmation" or lineage.get("approved") is not True:
        raise ValueError("Authoritative lineage confirmation is not approved.")
    if lineage.get("time_in_job_profile_start_date_confirmed_construct") != "current_job_profile_start":
        raise ValueError("Authoritative lineage does not confirm the current job-profile start construct.")
    if lineage.get("job_level_primary_position_confirmed_construct") != "current_detailed_level":
        raise ValueError("Authoritative lineage does not confirm the current detailed-level construct.")
    normalized = {
        key: str(lineage[key]).strip()
        for key in ("authority", "confirmation_date", "source_reference")
    }
    if not all(normalized.values()):
        raise ValueError("Authoritative lineage confirmation contains a blank authority, date, or reference.")
    try:
        date.fromisoformat(normalized["confirmation_date"])
    except ValueError as exc:
        raise ValueError("Authoritative lineage confirmation_date must use ISO YYYY-MM-DD.") from exc
    return {
        **normalized,
        "time_in_job_profile_start_date_confirmed_construct": "current_job_profile_start",
        "job_level_primary_position_confirmed_construct": "current_detailed_level",
        "lineage_sha256": hash_json(lineage),
    }


def pool_shared_bands(raw: dict[str, dict[str, int]]) -> list[dict[str, object]]:
    """Pool adjacent bands identically until both charts satisfy n >= 30."""
    groups = [[index, index] for index in range(len(BAND_KEYS))]

    def counts(group: list[int]) -> tuple[int, int]:
        lower, upper = group
        keys = BAND_KEYS[lower:upper + 1]
        return (
            sum(raw["role"][key] for key in keys),
            sum(raw["level"][key] for key in keys),
        )

    if raw["role"]["calculable"] < MINIMUM_COHORT or raw["level"]["calculable"] < MINIMUM_COHORT:
        raise ValueError("Each calculable clock population must meet the minimum cohort before publication.")

    while len(groups) > 1:
        sparse_index = next(
            (index for index, group in enumerate(groups) if min(counts(group)) < MINIMUM_COHORT),
            None,
        )
        if sparse_index is None:
            break
        if sparse_index == 0:
            neighbor = 1
        elif sparse_index == len(groups) - 1:
            neighbor = sparse_index - 1
        else:
            left_minimum = min(counts(groups[sparse_index - 1]))
            right_minimum = min(counts(groups[sparse_index + 1]))
            neighbor = sparse_index - 1 if left_minimum <= right_minimum else sparse_index + 1
        first, second = sorted((sparse_index, neighbor))
        groups[first][1] = groups[second][1]
        del groups[second]

    published: list[dict[str, object]] = []
    for lower, upper in groups:
        source_keys = list(BAND_KEYS[lower:upper + 1])
        role_count, level_count = counts([lower, upper])
        if min(role_count, level_count) < MINIMUM_COHORT:
            raise ValueError("No privacy-safe shared tenure bands can be formed.")
        label = BAND_LABELS[source_keys[0]] if len(source_keys) == 1 else (
            f"{BAND_LABELS[source_keys[0]].replace(' year', '').replace(' years', '')}–{BAND_LABELS[source_keys[-1]]}"
        )
        # Preserve readable boundary labels when pooling two or more source bins.
        if len(source_keys) > 1:
            first_label = BAND_LABELS[source_keys[0]]
            last_label = BAND_LABELS[source_keys[-1]]
            label = f"{first_label} to {last_label}"
        published.append(
            {
                "label": label,
                "source_band_keys": source_keys,
                "role_employee_count": role_count,
                "level_employee_count": level_count,
            }
        )
    return published


def validate_inputs(
    audit: dict[str, int],
    profile: dict[str, dict[str, int]],
    *,
    require_construct_validation: bool,
) -> list[dict[str, object]]:
    """Apply data-integrity, construct-transition, reconciliation, and privacy gates."""
    required_zero_metrics = set(BASE_ZERO_REQUIRED_AUDIT_METRICS)
    if require_construct_validation:
        required_zero_metrics.update(STRICT_CONSTRUCT_ZERO_REQUIRED_AUDIT_METRICS)
    failures = [metric for metric in sorted(required_zero_metrics) if audit[metric] != 0]
    if failures:
        raise ValueError(f"Role/level publication rejected by nonzero safeguards: {', '.join(failures)}.")
    if audit["target_source_row_count"] != audit["target_unique_employee_count"]:
        raise ValueError("Target source rows do not reconcile to unique active-regular employees.")
    if audit["target_unique_employee_count"] < MINIMUM_COHORT:
        raise ValueError("The active-regular population is below the minimum publication cohort.")
    if audit["comparable_transition_snapshot_count"] <= 0:
        raise ValueError("No comparable historical detailed-level transitions were available for validation.")
    for clock, metric_name in (("role", "role_calculable_employee_count"), ("level", "level_calculable_employee_count")):
        if profile[clock]["calculable"] != audit[metric_name]:
            raise ValueError(f"The {clock} profile denominator does not reconcile to the transition audit.")
        if profile[clock]["calculable"] + profile[clock]["not_calculable"] != audit["target_unique_employee_count"]:
            raise ValueError(f"The {clock} profile coverage does not reconcile to the active-regular population.")
    return pool_shared_bands(profile)


def build_evidence_from_rows(
    lineage: object | None,
    audit_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    *,
    audit_sql_sha256: str | None = None,
    audit_result_sha256: str | None = None,
    profile_sql_sha256: str | None = None,
    profile_result_sha256: str | None = None,
    exploratory: bool = False,
) -> dict[str, object]:
    """Build testable frozen evidence from in-memory aggregate rows only."""
    if exploratory:
        lineage_summary = {
            "status": "not_confirmed",
            "authority": "Not supplied",
            "confirmation_date": "",
            "source_reference": "No authoritative HRIS lineage confirmation was supplied; this is a descriptive stored-field analysis.",
            "time_in_job_profile_start_date_confirmed_construct": "not_confirmed",
            "job_level_primary_position_confirmed_construct": "not_confirmed",
            "lineage_sha256": hash_json({"status": "not_confirmed", "source": "not_supplied"}),
        }
    else:
        lineage_summary = {"status": "confirmed", **normalize_authoritative_lineage(lineage)}
    audit = parse_audit_rows(audit_rows)
    profile = parse_profile_rows(profile_rows)
    distribution = validate_inputs(audit, profile, require_construct_validation=not exploratory)
    role_denominator = profile["role"]["calculable"]
    level_denominator = profile["level"]["calculable"]
    for row in distribution:
        row["role_percent_of_calculable"] = round(100 * int(row["role_employee_count"]) / role_denominator, 8)
        row["level_percent_of_calculable"] = round(100 * int(row["level_employee_count"]) / level_denominator, 8)
    if not math.isclose(sum(float(row["role_percent_of_calculable"]) for row in distribution), 100.0, abs_tol=0.000001):
        raise ValueError("Role distribution percentages do not sum to 100%.")
    if not math.isclose(sum(float(row["level_percent_of_calculable"]) for row in distribution), 100.0, abs_tol=0.000001):
        raise ValueError("Level distribution percentages do not sum to 100%.")

    audit_sql_sha256 = audit_sql_sha256 or sha256_bytes(AUDIT_SQL.read_bytes())
    profile_sql_sha256 = profile_sql_sha256 or sha256_bytes(PROFILE_SQL.read_bytes())
    audit_result_sha256 = audit_result_sha256 or hash_json(audit_rows)
    profile_result_sha256 = profile_result_sha256 or hash_json(profile_rows)
    for label, value in {
        "audit_sql_sha256": audit_sql_sha256,
        "audit_result_sha256": audit_result_sha256,
        "profile_sql_sha256": profile_sql_sha256,
        "profile_result_sha256": profile_result_sha256,
    }.items():
        if not isinstance(value, str) or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError(f"{label} must be a lowercase SHA-256 hex digest.")

    evidence: dict[str, object] = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "internal_analysis",
        "variable": "Time in current job profile vs. current detailed level",
        "semantic_type": "derived_feature",
        "publication_status": "exploratory" if exploratory else "validated",
        "execution_date": date.today().isoformat(),
        "snapshot_date": SNAPSHOT_DATE,
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 at the 2026-08-23 monthly snapshot",
        "grain": "Distinct active regular employee at one monthly snapshot",
        "definitions": {
            "time_in_current_job_profile": "Anniversary-based tenure from the later of time_in_job_profile_start_date and max_hire_rehire_date." if not exploratory else "Descriptive date-field proxy from the later of time_in_job_profile_start_date and max_hire_rehire_date; HRIS construct lineage is not confirmed.",
            "time_at_current_detailed_level": "Anniversary-based tenure from the later of levelentrydate and max_hire_rehire_date; job_level_primary_position is required to identify the current detailed-level construct." if not exploratory else "Descriptive date-field proxy from the later of levelentrydate and max_hire_rehire_date, displayed with populated job_level_primary_position; HRIS construct lineage is not confirmed.",
            "time_in_role": "Supporting audit field only; it does not define either published clock.",
        },
        "reset_policy": {
            "job_profile_change": "Resets the job-profile clock only.",
            "detailed_level_change": "Resets the detailed-level clock only.",
            "rehire": "Both clocks use the later stored start date and max_hire_rehire_date.",
            "promotion_demotion": "Validation context only; flags do not automatically reset a clock.",
            "manager_location_cost_center_transfer_job_family": "Do not reset either clock unless the selected construct changes.",
        },
        "authoritative_lineage": lineage_summary,
        "coverage": {
            "eligible_employee_count": audit["target_unique_employee_count"],
            "role_calculable_employee_count": role_denominator,
            "role_not_calculable_employee_count": profile["role"]["not_calculable"],
            "level_calculable_employee_count": level_denominator,
            "level_not_calculable_employee_count": profile["level"]["not_calculable"],
        },
        "distribution": distribution,
        "metrics": {
            **audit,
            "published_band_count": len(distribution),
            "minimum_published_role_band_count": min(int(row["role_employee_count"]) for row in distribution),
            "minimum_published_level_band_count": min(int(row["level_employee_count"]) for row in distribution),
            "minimum_cohort": MINIMUM_COHORT,
        },
        "validations": {
            "employee_snapshot_grain": {"outcome": "pass", "rule": "No duplicate or conflicting employee-snapshot rows."},
            "dates_and_rehire": {"outcome": "pass", "rule": "No future dates or unresolved rehire conflicts; later-date adjustment applied."},
            "detailed_level_transition": {"outcome": "warning" if exploratory else "pass", "rule": "Transition mismatch is reported as a caveat in exploratory mode; validated publication requires no unexplained detailed-level transition or date reset."},
            "distribution_reconciliation": {"outcome": "pass", "rule": "Both distributions sum exactly to their calculable denominators and 100%."},
            "privacy": {"outcome": "pass", "rule": "Every published shared band has n >= 30 in both clocks."},
            "authoritative_lineage": {"outcome": "not_confirmed" if exploratory else "pass", "rule": "Exploratory mode does not assert field semantics." if exploratory else "HRIS authority confirmed both selected constructs."},
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
            "raw_dates_persisted": False,
            "job_code_or_title_persisted": False,
            "all_displayed_bands_meet_minimum": True,
            "minimum_cohort": MINIMUM_COHORT,
        },
        "acceptance_rule": "Exploratory publication: the active-regular snapshot and history are unique and conflict-free; no future dates or unresolved rehire conflicts exist; each stored-date distribution reconciles to its calculable denominator; every shared visible band has n >= 30; and unresolved construct and transition evidence is displayed as a caveat rather than treated as confirmed semantics." if exploratory else "The HRIS authority confirms both source constructs; the 2026-08-23 active-regular employee snapshot and comparable history are unique and conflict-free; no future dates or unresolved rehire conflicts exist; detailed-level transitions reconcile to levelentrydate without unexplained resets; each clock reconciles to its calculable denominator; and every shared visible band has n >= 30.",
        "exploratory_caveat": "Stored-field distributions only. Do not interpret the chart as proof that either field is the governed current job-profile or current detailed-level clock." if exploratory else None,
        "outcome": "pass",
    }
    ensure_no_sensitive_keys(evidence)
    return evidence


def load_lineage_file(path: Path) -> object:
    if not path.exists():
        raise FileNotFoundError(
            "Authoritative lineage confirmation is required before publishing slide 26: "
            f"{path}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def build_evidence(lineage_path: Path | None, *, exploratory: bool = False) -> dict[str, object]:
    """Execute both saved queries and freeze safe evidence only after all gates pass."""
    if lineage_path is None and not exploratory:
        raise FileNotFoundError("Authoritative lineage confirmation is required before validated publication.")
    lineage = load_lineage_file(lineage_path) if lineage_path is not None else None
    audit_rows, audit_sql_sha256, audit_result_sha256 = execute_aggregate_query(AUDIT_SQL)
    profile_rows, profile_sql_sha256, profile_result_sha256 = execute_aggregate_query(PROFILE_SQL)
    return build_evidence_from_rows(
        lineage,
        audit_rows,
        profile_rows,
        audit_sql_sha256=audit_sql_sha256,
        audit_result_sha256=audit_result_sha256,
        profile_sql_sha256=profile_sql_sha256,
        profile_result_sha256=profile_result_sha256,
        exploratory=exploratory,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build frozen aggregate evidence for the role/level tenure slide.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--authoritative-lineage",
        type=Path,
        help="Approved HRIS lineage confirmation JSON; Tableau or historic assessments are not accepted.",
    )
    parser.add_argument(
        "--exploratory",
        action="store_true",
        help="Publish a clearly caveated internal stored-field distribution without asserting authoritative construct lineage.",
    )
    args = parser.parse_args()
    try:
        evidence = build_evidence(args.authoritative_lineage, exploratory=args.exploratory)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Publication blocked: {exc}") from exc
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    coverage = evidence["coverage"]
    assert isinstance(coverage, dict)
    print(f"Wrote aggregate-only evidence: {args.output}")
    print(
        f"Snapshot {SNAPSHOT_DATE}; status={evidence['publication_status']}; active regular employees={coverage['eligible_employee_count']:,}; "
        f"role calculable={coverage['role_calculable_employee_count']:,}; "
        f"level calculable={coverage['level_calculable_employee_count']:,}"
    )


if __name__ == "__main__":
    main()
