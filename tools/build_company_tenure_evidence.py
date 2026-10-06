"""Freeze aggregate-only descriptive evidence for the Company tenure slide.

The two published charts are intentionally field proxies, not a selection of a
governed Company tenure definition.  ``original_hire_date`` and
``max_hire_rehire_date`` are profiled separately at one fixed workforce
snapshot.  Raw aggregate rows remain in memory; the output retains only safe
counts, percentages, validation outcomes, and SQL/result hashes.
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
AUDIT_SQL = ROOT / "queries" / "audits" / "company_tenure_stored_date_integrity_20260823.sql"
PROFILE_SQL = ROOT / "queries" / "profiles" / "company_tenure_stored_date_distribution_20260823.sql"
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
CLOCKS = ("original_hire", "latest_hire_rehire")

REQUIRED_AUDIT_METRICS = {
    "population_source_row_count",
    "target_missing_employee_id_row_count",
    "target_source_row_count",
    "target_unique_employee_count",
    "target_duplicate_employee_count",
    "target_duplicate_row_excess_count",
    "target_conflicting_employee_count",
    "original_hire_null_count",
    "latest_hire_rehire_null_count",
    "original_hire_future_date_count",
    "latest_hire_rehire_future_date_count",
    "impossible_date_order_count",
    "original_hire_calculable_employee_count",
    "latest_hire_rehire_calculable_employee_count",
}

ZERO_REQUIRED_AUDIT_METRICS = {
    "target_missing_employee_id_row_count",
    "target_duplicate_employee_count",
    "target_duplicate_row_excess_count",
    "target_conflicting_employee_count",
    "original_hire_future_date_count",
    "latest_hire_rehire_future_date_count",
    "impossible_date_order_count",
}

PROHIBITED_KEYS = {
    "employee_id",
    "employee_ids",
    "emp_name",
    "name",
    "employee_name",
    "manager_employee_id",
    "manager_name",
    "email",
    "address",
    "home_address",
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


def ensure_no_sensitive_keys(value: object) -> None:
    """Reject row-level values, identity fields, and individual dates."""
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in PROHIBITED_KEYS:
                raise ValueError(f"Frozen Company tenure evidence attempted to persist a prohibited key: {key!r}.")
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
    """Run saved aggregate-only SQL and retain its rows only in memory."""
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
        raise ValueError("The Company tenure audit returned no aggregate rows.")
    metrics: dict[str, int] = {}
    for row in rows:
        if set(row) != {"snapshot_date", "row_type", "metric", "metric_value"}:
            raise ValueError("The Company tenure audit returned an unexpected aggregate schema.")
        if str(row["snapshot_date"]) != SNAPSHOT_DATE:
            raise ValueError("Snapshot mismatch: Company tenure evidence must use 2026-08-23 only.")
        if row["row_type"] != "metric":
            raise ValueError("The Company tenure audit returned a non-metric row.")
        metric = str(row["metric"])
        if metric in metrics:
            raise ValueError(f"The Company tenure audit duplicated metric {metric!r}.")
        metrics[metric] = numeric_int(row["metric_value"], metric)
    missing = sorted(REQUIRED_AUDIT_METRICS - set(metrics))
    extra = sorted(set(metrics) - REQUIRED_AUDIT_METRICS)
    if missing or extra:
        raise ValueError(f"Company tenure audit metric contract mismatch; missing={missing}, extra={extra}.")
    return metrics


def parse_profile_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    if not rows:
        raise ValueError("The Company tenure profile returned no aggregate rows.")
    metrics: dict[str, dict[str, int | None]] = {
        clock: {"calculable": None, "not_calculable": None} for clock in CLOCKS
    }
    bands: dict[str, dict[str, int]] = {clock: {} for clock in CLOCKS}
    for row in rows:
        if set(row) != {"snapshot_date", "clock", "row_type", "bucket_key", "employee_count"}:
            raise ValueError("The Company tenure profile returned an unexpected aggregate schema.")
        if str(row["snapshot_date"]) != SNAPSHOT_DATE:
            raise ValueError("Snapshot mismatch: Company tenure profile must use 2026-08-23 only.")
        clock = str(row["clock"])
        row_type = str(row["row_type"])
        bucket = str(row["bucket_key"])
        count = numeric_int(row["employee_count"], f"{clock}:{bucket}")
        if clock not in metrics or count < 0:
            raise ValueError("The Company tenure profile contains an invalid clock or negative count.")
        if row_type == "metric":
            if bucket not in metrics[clock] or metrics[clock][bucket] is not None:
                raise ValueError("The Company tenure profile has an invalid or duplicate coverage metric.")
            metrics[clock][bucket] = count
        elif row_type == "band":
            if bucket not in BAND_KEYS or bucket in bands[clock]:
                raise ValueError("The Company tenure profile has an invalid or duplicate anniversary band.")
            bands[clock][bucket] = count
        else:
            raise ValueError("The Company tenure profile has an invalid row type.")
    result: dict[str, dict[str, int]] = {}
    for clock in CLOCKS:
        if any(metrics[clock][key] is None for key in ("calculable", "not_calculable")):
            raise ValueError(f"The Company tenure profile is missing {clock} coverage metrics.")
        if tuple(bands[clock]) != BAND_KEYS:
            raise ValueError(f"The Company tenure profile is missing or reordering {clock} anniversary bands.")
        calculable = int(metrics[clock]["calculable"] or 0)
        if sum(bands[clock].values()) != calculable:
            raise ValueError(f"The Company tenure {clock} bands do not reconcile to their calculable denominator.")
        result[clock] = {
            "calculable": calculable,
            "not_calculable": int(metrics[clock]["not_calculable"] or 0),
            **bands[clock],
        }
    return result


def validate_inputs(audit: dict[str, int], profile: dict[str, dict[str, int]]) -> list[dict[str, object]]:
    failures = [metric for metric in sorted(ZERO_REQUIRED_AUDIT_METRICS) if audit[metric] != 0]
    if failures:
        raise ValueError(f"Company tenure publication rejected by nonzero safeguards: {', '.join(failures)}.")
    if audit["population_source_row_count"] != audit["target_source_row_count"]:
        raise ValueError("Company tenure population contains rows without an employee identifier.")
    if audit["target_source_row_count"] != audit["target_unique_employee_count"]:
        raise ValueError("Company tenure target source rows do not reconcile to unique employees.")
    if audit["target_unique_employee_count"] < MINIMUM_COHORT:
        raise ValueError("Company tenure active-regular population is below the minimum publication cohort.")

    audit_denominators = {
        "original_hire": audit["original_hire_calculable_employee_count"],
        "latest_hire_rehire": audit["latest_hire_rehire_calculable_employee_count"],
    }
    for clock in CLOCKS:
        if profile[clock]["calculable"] != audit_denominators[clock]:
            raise ValueError(f"The Company tenure {clock} profile denominator does not reconcile to the audit.")
        if profile[clock]["calculable"] + profile[clock]["not_calculable"] != audit["target_unique_employee_count"]:
            raise ValueError(f"The Company tenure {clock} coverage does not reconcile to the eligible population.")
        if profile[clock]["calculable"] < MINIMUM_COHORT:
            raise ValueError(f"The Company tenure {clock} calculable population is below the minimum publication cohort.")
        sparse = [key for key in BAND_KEYS if profile[clock][key] < MINIMUM_COHORT]
        if sparse:
            raise ValueError(f"The Company tenure {clock} contains a band below the minimum cohort: {', '.join(sparse)}.")

    distribution: list[dict[str, object]] = []
    for key in BAND_KEYS:
        original_count = profile["original_hire"][key]
        latest_count = profile["latest_hire_rehire"][key]
        distribution.append(
            {
                "label": BAND_LABELS[key],
                "source_band_key": key,
                "original_hire_employee_count": original_count,
                "latest_hire_rehire_employee_count": latest_count,
                "original_hire_percent_of_calculable": round(
                    100 * original_count / profile["original_hire"]["calculable"], 8
                ),
                "latest_hire_rehire_percent_of_calculable": round(
                    100 * latest_count / profile["latest_hire_rehire"]["calculable"], 8
                ),
            }
        )
    return distribution


def build_evidence_from_rows(
    audit_rows: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    *,
    audit_sql_sha256: str | None = None,
    audit_result_sha256: str | None = None,
    profile_sql_sha256: str | None = None,
    profile_result_sha256: str | None = None,
) -> dict[str, object]:
    """Build a validated aggregate-only evidence document from frozen rows."""
    audit = parse_audit_rows(audit_rows)
    profile = parse_profile_rows(profile_rows)
    distribution = validate_inputs(audit, profile)

    for clock, count_key, percent_key in (
        ("original_hire", "original_hire_employee_count", "original_hire_percent_of_calculable"),
        ("latest_hire_rehire", "latest_hire_rehire_employee_count", "latest_hire_rehire_percent_of_calculable"),
    ):
        if sum(int(row[count_key]) for row in distribution) != profile[clock]["calculable"]:
            raise ValueError(f"Company tenure {clock} display bands do not sum to the calculable denominator.")
        if not math.isclose(sum(float(row[percent_key]) for row in distribution), 100.0, abs_tol=0.000001):
            raise ValueError(f"Company tenure {clock} display percentages do not sum to 100%.")

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
        if not isinstance(value, str) or not all(character in "0123456789abcdef" for character in value) or len(value) != 64:
            raise ValueError(f"{label} must be a lowercase SHA-256 hex digest.")

    evidence: dict[str, object] = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "internal_analysis",
        "variable": "Company tenure",
        "semantic_type": "direct_field",
        "publication_status": "descriptive_stored_fields",
        "score_v4_change": "none",
        "execution_date": date.today().isoformat(),
        "snapshot_date": SNAPSHOT_DATE,
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 at the fixed 2026-08-23 monthly snapshot",
        "grain": "Distinct active regular employee at one monthly snapshot",
        "definitions": {
            "original_hire_date": "Proxy descriptivo: antigüedad por aniversario desde el valor almacenado original_hire_date.",
            "max_hire_rehire_date": "Proxy descriptivo: antigüedad por aniversario desde el valor almacenado max_hire_rehire_date.",
            "cross_field_policy": "No se aplica una fecha sobre la otra; cada gráfica describe directamente su propio campo almacenado.",
        },
        "coverage": {
            "eligible_employee_count": audit["target_unique_employee_count"],
            "original_hire_calculable_employee_count": profile["original_hire"]["calculable"],
            "original_hire_not_calculable_employee_count": profile["original_hire"]["not_calculable"],
            "latest_hire_rehire_calculable_employee_count": profile["latest_hire_rehire"]["calculable"],
            "latest_hire_rehire_not_calculable_employee_count": profile["latest_hire_rehire"]["not_calculable"],
        },
        "distribution": distribution,
        "metrics": {
            **audit,
            "published_band_count": len(distribution),
            "minimum_published_original_hire_band_count": min(int(row["original_hire_employee_count"]) for row in distribution),
            "minimum_published_latest_hire_rehire_band_count": min(int(row["latest_hire_rehire_employee_count"]) for row in distribution),
            "minimum_cohort": MINIMUM_COHORT,
        },
        "validations": {
            "employee_snapshot_grain": {"outcome": "pass", "rule": "No missing employee IDs, duplicate rows, or conflicting employee-snapshot fields."},
            "dates": {"outcome": "pass", "rule": "No future original-hire or latest-hire/rehire dates in the fixed snapshot."},
            "stored_date_order": {"outcome": "pass", "rule": "When both values are populated, original_hire_date is not later than max_hire_rehire_date."},
            "population_reconciliation": {"outcome": "pass", "rule": "Audit source rows, unique employees, each coverage pair, and profile denominators reconcile."},
            "distribution_reconciliation": {"outcome": "pass", "rule": "Each field's six bands sum exactly to its calculable denominator and 100%."},
            "privacy": {"outcome": "pass", "rule": "Each visible band in both distributions has n >= 30; no identities, employee rows, raw dates, or raw query rows are retained."},
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
            "raw_aggregate_rows_persisted": False,
            "all_displayed_bands_meet_minimum": True,
            "minimum_cohort": MINIMUM_COHORT,
        },
        "acceptance_rule": "El snapshot fijo 2026-08-23 de empleados regulares activos debe ser único y sin conflictos; no puede haber fechas futuras ni original_hire_date posterior a max_hire_rehire_date; ambos perfiles deben reconciliar cobertura y denominadores con la población auditada; cada banda compartida debe sumar su denominador y cumplir n >= 30. El resultado sólo describe los dos campos almacenados y no selecciona una definición HRIS de Company tenure.",
        "outcome": "pass",
    }
    ensure_no_sensitive_keys(evidence)
    return evidence


def build_evidence() -> dict[str, object]:
    """Execute both approved saved queries and freeze only their safe aggregates."""
    audit_rows, audit_sql_sha256, audit_result_sha256 = execute_aggregate_query(AUDIT_SQL)
    profile_rows, profile_sql_sha256, profile_result_sha256 = execute_aggregate_query(PROFILE_SQL)
    return build_evidence_from_rows(
        audit_rows,
        profile_rows,
        audit_sql_sha256=audit_sql_sha256,
        audit_result_sha256=audit_result_sha256,
        profile_sql_sha256=profile_sql_sha256,
        profile_result_sha256=profile_result_sha256,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build frozen aggregate-only evidence for Company tenure.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence = build_evidence()
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Publication blocked: {exc}") from exc
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    coverage = evidence["coverage"]
    assert isinstance(coverage, dict)
    print(f"Wrote aggregate-only evidence: {args.output}")
    print(
        f"Snapshot {SNAPSHOT_DATE}; active regular employees={coverage['eligible_employee_count']:,}; "
        f"original-hire calculable={coverage['original_hire_calculable_employee_count']:,}; "
        f"latest-hire/rehire calculable={coverage['latest_hire_rehire_calculable_employee_count']:,}"
    )


if __name__ == "__main__":
    main()
