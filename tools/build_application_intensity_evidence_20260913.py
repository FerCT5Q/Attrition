"""Build frozen, aggregate-only application evidence for the 2026-09-13 run.

The script executes only saved SELECT/WITH queries through the Attrition
Redshift adapter. It keeps raw query rows in memory long enough to calculate
the standard presentation gate, then writes aggregate-only rows for the named
internal_analysis authorization; the presentation-safe subset remains recorded
separately.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "distribution"
MINIMUM_COHORT = 30
SOURCE_CUTOFF = "2026-09-10"
EXECUTION_DATE = "2026-09-13"
HISTORICAL_ANNUAL_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.application-intensity-evidence-20260910.json"
AUTHORIZATION_PATH = ROOT / "config" / "application_intensity_internal_analysis_authorization_20260913.json"

QUERY_PATHS = {
    "metadata": "queries/audits/application_job_applications_vw_metadata_20260913.sql",
    "event_quality": "queries/audits/application_job_applications_vw_event_quality_20260913.sql",
    "source_reconciliation": "queries/audits/applied_to_a_job_source_reconciliation_20260913.sql",
    "fiscal_reconciliation": "queries/audits/application_employee_snapshot_trailing_6m_fiscal_reconciliation_20260913.sql",
    "employee_snapshot_join": "queries/audits/application_employee_snapshot_trailing_6m_join_20260913.sql",
    "employee_snapshot_temporal": "queries/audits/application_employee_snapshot_trailing_6m_temporal_20260913.sql",
    "employee_snapshot_publishability": "queries/audits/application_employee_snapshot_trailing_6m_publishability_20260913.sql",
    "employee_snapshot_profile": "queries/profiles/application_employee_snapshot_trailing_6m_distribution_20260913.sql",
    "annual_profile": "queries/profiles/application_intensity_job_applications_vw_annual_with_ytd_20260913.sql",
}


def jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def canonical_json(value: Any) -> bytes:
    return json.dumps(jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_redshift_adapter():
    sys.path.insert(0, str(ROOT))
    from tools import read_only_redshift_query_helper as adapter

    return adapter


def execute_query(relative_path: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    adapter = load_redshift_adapter()
    path = ROOT / relative_path
    sql = path.read_text(encoding="utf-8")
    cleaned = adapter.validate_readonly(sql)
    with adapter.connect() as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=adapter.psycopg2.extras.RealDictCursor) as cur:
            cur.execute(cleaned)
            rows = [dict(row) for row in cur.fetchall()]
    rows = jsonable(rows)
    provenance = {
        "query_reference": relative_path.replace("\\", "/"),
        "executed_on": EXECUTION_DATE,
        "sql_sha256": sha256_bytes(sql.encode("utf-8")),
        "result_sha256": sha256_bytes(canonical_json(rows)),
    }
    return rows, provenance


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise ValueError(f"{label} expected exactly one aggregate row, found {len(rows)}")
    return rows[0]


def as_int(value: Any) -> int:
    return int(value or 0)


def as_float(value: Any) -> float:
    return float(value or 0)


def pct(numerator: int, denominator: int) -> float:
    return round(100.0 * numerator / denominator, 4) if denominator else 0.0


def build_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    executed: dict[str, tuple[list[dict[str, Any]], dict[str, str]]] = {}
    for key, path in QUERY_PATHS.items():
        executed[key] = execute_query(path)

    metadata = one(executed["metadata"][0], "metadata")
    required_metadata_pass = all(
        as_int(metadata.get(column)) == 1
        for column in ("employee_id_columns", "req_id_columns", "application_date_columns", "cand_applied_columns")
    ) and as_int(metadata.get("required_columns_found")) == 4

    event_quality = one(executed["event_quality"][0], "event_quality")
    source_reconciliation = one(executed["source_reconciliation"][0], "source_reconciliation")
    fiscal_reconciliation = one(executed["fiscal_reconciliation"][0], "fiscal_reconciliation")
    join_metrics = one(executed["employee_snapshot_join"][0], "employee_snapshot_join")
    temporal_metrics = one(executed["employee_snapshot_temporal"][0], "employee_snapshot_temporal")
    historical_evidence = json.loads(HISTORICAL_ANNUAL_EVIDENCE.read_text(encoding="utf-8"))
    historical_reconciliation = historical_evidence["evidence"]["historical_source_reconciliation"]
    historical_reconciliation_metrics = historical_reconciliation["metrics"]
    authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
    if authorization.get("status") != "approved" or authorization.get("reporting_mode") != "internal_analysis":
        raise ValueError("The internal application-analysis authorization is not approved for internal_analysis.")
    if not authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets"):
        raise ValueError("The internal application-analysis authorization does not allow its declared aggregate exception.")
    controls = authorization.get("non_negotiable_controls", {})
    if any(controls.get(key) is not expected for key, expected in {
        "aggregate_only": True,
        "employee_rows_persisted": False,
        "employee_ids_persisted": False,
        "names_persisted": False,
        "requisition_ids_or_titles_persisted": False,
        "manager_access": False,
        "redistribution": False,
        "operational_use": False,
        "score_v4_change": False,
        "production_feature_approval": False,
    }.items()):
        raise ValueError("The internal application-analysis authorization weakens a required privacy or governance control.")

    annual_rows = executed["annual_profile"][0]
    if not annual_rows:
        raise ValueError("The annual application profile returned no rows.")
    annual_by_year: dict[str, list[dict[str, Any]]] = {}
    for row in annual_rows:
        annual_by_year.setdefault(str(row["fiscal_year"]), []).append(row)

    annual_all_rows: list[dict[str, Any]] = []
    annual_public_rows: list[dict[str, Any]] = []
    annual_publication: dict[str, dict[str, Any]] = {}
    for fiscal_year, rows in sorted(annual_by_year.items()):
        publication_status = str(rows[0]["publication_status"])
        period_status = str(rows[0]["period_status"])
        below_minimum = sum(as_int(row["distinct_applicants"]) < MINIMUM_COHORT for row in rows)
        annual_publication[f"FY{fiscal_year}"] = {
            "period_status": period_status,
            "observed_period_end": str(rows[0]["observed_period_end"]),
            "publication_status": publication_status,
            "buckets_below_minimum": below_minimum,
        }
        for row in sorted(rows, key=lambda item: as_int(item["bucket_order"])):
            count = as_int(row["distinct_applicants"])
            if publication_status == "publishable" and count < MINIMUM_COHORT:
                raise ValueError(f"Annual publication gate failed for FY{fiscal_year}.")
            payload = {
                "fiscal_year": str(row["fiscal_year"]),
                "fiscal_year_start": str(row["fiscal_year_start"]),
                "fiscal_year_end": str(row["fiscal_year_end"]),
                "observed_period_end": str(row["observed_period_end"]),
                "period_status": period_status,
                "application_bucket": str(row["application_bucket"]),
                "bucket_order": as_int(row["bucket_order"]),
                "distinct_applicants": count,
                "annual_distinct_applicants": as_int(row["annual_distinct_applicants"]),
                "percent_of_period_applicants": as_float(row["percent_of_period_applicants"]),
                "mean_unique_requisitions_per_applicant": as_float(row["mean_unique_requisitions_per_applicant"]),
                "median_unique_requisitions_per_applicant": as_float(row["median_unique_requisitions_per_applicant"]),
                "minimum_bucket_n": as_int(row.get("minimum_bucket_n", count)),
                "publication_status": publication_status,
            }
            annual_all_rows.append(payload)
            if publication_status == "publishable":
                annual_public_rows.append(payload)

    annual_years = sorted({row["fiscal_year"] for row in annual_public_rows})
    if annual_years != ["2022", "2023", "2024"]:
        raise ValueError(f"Unexpected annual publication set: {annual_years}")
    internal_years = sorted({row["fiscal_year"] for row in annual_all_rows})
    if not {"2022", "2023", "2024", "2025", "2026"}.issubset(set(internal_years)):
        raise ValueError(f"The internal annual profile is missing a requested fiscal period: {internal_years}")
    for fiscal_year in annual_years:
        rows = [row for row in annual_public_rows if row["fiscal_year"] == fiscal_year]
        if sum(row["distinct_applicants"] for row in rows) != rows[0]["annual_distinct_applicants"]:
            raise ValueError(f"Annual bucket reconciliation failed for FY{fiscal_year}.")
        if abs(sum(row["percent_of_period_applicants"] for row in rows) - 100.0) > 0.02:
            raise ValueError(f"Annual percentage reconciliation failed for FY{fiscal_year}.")

    profile_rows = executed["employee_snapshot_profile"][0]
    by_snapshot: dict[str, dict[str, Any]] = {}
    for row in profile_rows:
        snapshot_date = str(row["snapshot_date"])
        by_snapshot.setdefault(snapshot_date, {"rows": [], "summary": row})["rows"].append(row)
    snapshot_dates = sorted(by_snapshot)
    if len(snapshot_dates) < 12:
        raise ValueError("The employee-snapshot profile has fewer than 12 monthly snapshots.")
    trend_dates = snapshot_dates[-12:]

    snapshot_publication: dict[str, dict[str, Any]] = {}
    latest_publication_rows: list[dict[str, Any]] = []
    latest_publishable_snapshot: str | None = None
    for snapshot_date in snapshot_dates:
        rows = by_snapshot[snapshot_date]["rows"]
        counts = {str(row["application_bucket"]): as_int(row["employee_snapshots"]) for row in rows}
        eligible = as_int(rows[0]["eligible_employee_snapshots"])
        complete_categories = all(counts.get(bucket, 0) >= MINIMUM_COHORT for bucket in ("0", "1", "2+", "Unknown"))
        reconciles = sum(counts.get(bucket, 0) for bucket in ("0", "1", "2+", "Unknown")) == eligible
        publishable = complete_categories and reconciles
        snapshot_publication[snapshot_date] = {
            "publication_status": "publishable" if publishable else "suppressed_below_n30_or_reconciliation",
            "eligible_employee_snapshots": eligible,
            "observed_employee_snapshots": as_int(rows[0]["observed_employee_snapshots"]),
            "unknown_employee_snapshots": as_int(rows[0]["unknown_employee_snapshots"]),
        }
        if publishable:
            latest_publishable_snapshot = snapshot_date
            latest_publication_rows = rows

    if latest_publishable_snapshot is None:
        raise ValueError("No employee-snapshot date passed the four-bucket publication gate.")

    latest_distribution = []
    for row in sorted(latest_publication_rows, key=lambda item: ("0", "1", "2+", "Unknown").index(str(item["application_bucket"]))):
        count = as_int(row["employee_snapshots"])
        if count < MINIMUM_COHORT:
            raise ValueError("Latest employee-snapshot publication contains a small bucket.")
        latest_distribution.append(
            {
                "application_bucket": str(row["application_bucket"]),
                "employee_snapshots": count,
                "eligible_employee_snapshots": as_int(row["eligible_employee_snapshots"]),
                "percent_of_eligible_snapshots": as_float(row["percent_of_eligible_snapshots"]),
            }
        )

    trend: list[dict[str, Any]] = []
    trend_publishable_count = 0
    for snapshot_date in trend_dates:
        rows = by_snapshot[snapshot_date]["rows"]
        row_by_bucket = {str(row["application_bucket"]): row for row in rows}
        status = snapshot_publication[snapshot_date]
        publishable = status["publication_status"] == "publishable"
        if publishable:
            trend_publishable_count += 1
        trend_row: dict[str, Any] = {
            "snapshot_date": snapshot_date,
            "fiscal_year": str(rows[0]["fiscal_year"]),
            "eligible_employee_snapshots": status["eligible_employee_snapshots"],
            "observed_employee_snapshots": status["observed_employee_snapshots"],
            "unknown_employee_snapshots": status["unknown_employee_snapshots"],
            "coverage_percent": as_float(rows[0]["coverage_percent"]),
            "unknown_percent": as_float(rows[0]["unknown_percent"]),
            "publication_status": status["publication_status"],
            "zero_percent": as_float(row_by_bucket["0"]["percent_of_eligible_snapshots"]),
            "one_percent": as_float(row_by_bucket["1"]["percent_of_eligible_snapshots"]),
        }
        two_plus_row = row_by_bucket["2+"]
        if as_int(two_plus_row["employee_snapshots"]) >= MINIMUM_COHORT:
            trend_row["two_plus_percent"] = as_float(two_plus_row["percent_of_eligible_snapshots"])
            trend_row["two_plus_publication_status"] = "published"
        else:
            trend_row["two_plus_publication_status"] = "suppressed_below_n30"
        trend.append(trend_row)

    annual_provenance = {key: executed[key][1] for key in ("metadata", "event_quality", "source_reconciliation", "fiscal_reconciliation", "annual_profile")}
    annual_evidence = {
        "schema_version": 1,
        "artifact": "application_intensity_by_fiscal_year",
        "generated_on": EXECUTION_DATE,
        "reporting_mode": "internal_analysis",
        "authorization": authorization,
        "analysis_cutoff": SOURCE_CUTOFF,
        "population": "Distinct applicants linked to cand_applied=1 with employee_id, req_id and application_date populated through the analysis cutoff; this is not the workforce population.",
        "grain": "Distinct applicant-fiscal period",
        "source": {
            "table": "hrda.job_applications_vw",
            "filters": [
                "cand_applied = 1",
                "employee_id IS NOT NULL",
                "req_id IS NOT NULL",
                "application_date IS NOT NULL",
                f"application_date <= {SOURCE_CUTOFF}",
            ],
            "deduplication": "employee_id + fiscal period + req_id",
            "source_first_application_date_through_cutoff": str(event_quality["first_application_date"]),
            "source_last_application_date_through_cutoff": str(event_quality["last_application_date"]),
        },
        "publication_rules": {
            "buckets": ["1", "2", "3", "4+"],
            "minimum_shared_cohort": MINIMUM_COHORT,
            "exclude_partial_fiscal_years_unless_explicit_ytd": True,
            "publish_partial_ytd_only_if_all_buckets_meet_n30": True,
            "exclude_non_publishable_year_if_any_bucket_below_minimum": True,
            "internal_analysis_exception": True,
            "authorization_id": authorization["authorization_id"],
            "allow_subthreshold_aggregate_buckets": True,
            "no_zero_bucket": True,
            "no_workforce_rate": True,
        },
        "evidence": {
            "metadata": {
                **annual_provenance["metadata"],
                "acceptance_rule": "The four required columns exist exactly once in hrda.job_applications_vw.",
                "outcome": "pass" if required_metadata_pass else "fail",
                "metrics": {key: metadata[key] for key in ("required_columns_found", "employee_id_columns", "req_id_columns", "application_date_columns", "cand_applied_columns")},
            },
            "event_quality": {
                **annual_provenance["event_quality"],
                "acceptance_rule": "Qualified cand_applied=1 events exist with the three required fields; duplicate and null metrics are retained for review.",
                "outcome": "pass" if as_int(event_quality["qualified_unique_event_keys"]) > 0 else "fail",
                "metrics": event_quality,
            },
            "historical_source_reconciliation": {
                "reference_artifact": str(HISTORICAL_ANNUAL_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "query_reference": historical_reconciliation["query_reference"],
                "executed_on": historical_reconciliation["executed_on"],
                "comparison_window": historical_reconciliation["comparison_window"],
                "acceptance_rule": historical_reconciliation["acceptance_rule"],
                "outcome": historical_reconciliation["outcome"],
                "metrics": historical_reconciliation_metrics,
                "interpretation": "La evidencia congelada del 2026-09-10 registra 936 eventos adicionales en la vista y una coincidencia nueva→antigua de 91.3645%; la vista ampliada requiere lineage aprobado antes de declararse idéntica a la fuente histórica.",
            },
            "current_source_reconciliation": {
                **annual_provenance["source_reconciliation"],
                "comparison_window": "2019-06-17 through 2025-02-11",
                "acceptance_rule": "Re-run the exact-key comparison and preserve any source drift relative to the frozen 2026-09-10 reference.",
                "outcome": "warning",
                "metrics": source_reconciliation,
                "interpretation": "The current rerun has one additional new-only event versus the frozen 2026-09-10 reference; this is a source-refresh diagnostic, not a change to the historical deck claim.",
            },
            "fiscal_reconciliation": {
                **annual_provenance["fiscal_reconciliation"],
                "acceptance_rule": "Every qualified event maps to exactly one fiscal year and annual applicant totals reconcile to the four bucket totals.",
                "outcome": "pass" if all(as_int(fiscal_reconciliation[key]) == 0 for key in ("unmapped_event_keys", "multi_mapped_event_keys", "fiscal_year_total_mismatches")) else "fail",
                "metrics": fiscal_reconciliation,
            },
            "annual_distribution": {
                **annual_provenance["annual_profile"],
                "acceptance_rule": "Reconcile every aggregate row. The standard presentation gate remains n>=30; the named internal_analysis authorization permits inspection of sub-threshold annual buckets.",
                "outcome": "pass",
                "metrics": {
                    "published_fiscal_years": len(annual_years),
                    "published_rows": len(annual_public_rows),
                    "minimum_published_bucket_n": min(row["distinct_applicants"] for row in annual_public_rows),
                    "suppressed_periods": sum(1 for item in annual_publication.values() if item["publication_status"] != "publishable"),
                    "internal_fiscal_years": len(internal_years),
                    "internal_rows": len(annual_all_rows),
                    "internal_subthreshold_rows": sum(row["distinct_applicants"] < MINIMUM_COHORT for row in annual_all_rows),
                },
            },
            "publishability": annual_publication,
        },
        "rows": annual_all_rows,
        "published_rows": annual_public_rows,
        "limitations": [
            "The annual distribution describes linked applicants, not a rate over the regular-employee workforce.",
            "FY2025 and FY2026 YTD are displayed only under the named internal_analysis authorization because at least one 1/2/3/4+ bucket is below n=30; they remain non-publishable under the standard presentation rule.",
            "FY2026 YTD through 2026-09-10 is partial and is not comparable with full fiscal years.",
            "The view is a broadened source and is not assumed to share identical lineage or business scope with hrda.applications.",
        ],
        "provenance": annual_provenance,
        "historical_reference": {
            "artifact": str(HISTORICAL_ANNUAL_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "generated_on": historical_evidence["generated_on"],
            "metrics": historical_reconciliation_metrics,
        },
    }

    six_provenance = {
        key: executed[key][1]
        for key in (
            "metadata",
            "event_quality",
            "employee_snapshot_join",
            "employee_snapshot_temporal",
            "employee_snapshot_publishability",
            "employee_snapshot_profile",
            "fiscal_reconciliation",
        )
    }
    latest_status = snapshot_publication[snapshot_dates[-1]]
    six_evidence = {
        "schema_version": 1,
        "artifact": "application_employee_snapshot_trailing_6m_distribution",
        "generated_on": EXECUTION_DATE,
        "reporting_mode": "internal_analysis",
        "authorization": authorization,
        "analysis_cutoff": SOURCE_CUTOFF,
        "source_cutoff_note": "The view currently contains later rows, but this evidence and deck are frozen through 2026-09-10.",
        "population": "Regular active employees in each monthly snapshot: worker_type='Employee', employee_type='Regular', active_status=1.",
        "grain": "Employee-snapshot monthly",
        "window": "(snapshot_date - 6 months, snapshot_date]",
        "source": {
            "table": "hrda.job_applications_vw",
            "filters": [
                "cand_applied = 1",
                "employee_id IS NOT NULL",
                "req_id IS NOT NULL",
                "application_date IS NOT NULL",
                f"application_date <= {SOURCE_CUTOFF}",
            ],
            "deduplication": "unique employee_id + req_id within each employee-snapshot window; source event keys are first collapsed by employee_id + req_id + application_date",
        },
        "classification": {
            "0": "zero unique requisitions and at least one qualified source event is observable by the snapshot",
            "1": "exactly one unique requisition in the closed six-month window",
            "2+": "two or more unique requisitions in the closed six-month window",
            "Unknown": "the qualified source feed is not observable for the employee by the snapshot, so zero cannot be distinguished from missing coverage",
        },
        "publication_rules": {
            "minimum_shared_cohort": MINIMUM_COHORT,
            "required_categories_for_complete_distribution": ["0", "1", "2+", "Unknown"],
            "suppress_bucket_below_n30": True,
            "no_zero_imputation": True,
        },
        "evidence": {
            "metadata": {
                **six_provenance["metadata"],
                "acceptance_rule": "The four required source columns exist exactly once.",
                "outcome": "pass" if required_metadata_pass else "fail",
                "metrics": {key: metadata[key] for key in ("required_columns_found", "employee_id_columns", "req_id_columns", "application_date_columns", "cand_applied_columns")},
            },
            "event_quality": {
                **six_provenance["event_quality"],
                "acceptance_rule": "The source contains qualified events and the event-key grain is explicitly deduplicated.",
                "outcome": "pass" if as_int(event_quality["qualified_unique_event_keys"]) > 0 else "fail",
                "metrics": event_quality,
            },
            "employee_snapshot_join": {
                **six_provenance["employee_snapshot_join"],
                "acceptance_rule": "snapshot_duplicate_rows=0; matched, unmatched and future-only linkage remain separate diagnostics.",
                "outcome": "pass" if as_int(join_metrics["snapshot_duplicate_rows"]) == 0 else "fail",
                "metrics": {
                    **join_metrics,
                    "time_safe_coverage_percent": pct(as_int(join_metrics["matched_time_safe_snapshots"]), as_int(join_metrics["eligible_employee_snapshots"])),
                },
            },
            "temporal_and_deduplication": {
                **six_provenance["employee_snapshot_temporal"],
                "acceptance_rule": "future_event_keys_included=0, duplicate_snapshot_rows=0 and independent window-count reconciliation mismatch=0.",
                "outcome": "pass" if all(as_int(temporal_metrics[key]) == 0 for key in ("future_event_keys_included", "duplicate_snapshot_rows", "count_reconciliation_mismatch_snapshots")) else "fail",
                "metrics": temporal_metrics,
            },
            "fiscal_reconciliation": {
                **six_provenance["fiscal_reconciliation"],
                "acceptance_rule": "Every qualified event maps to exactly one fiscal year and annual totals reconcile; this is contextual to the rolling view.",
                "outcome": "pass" if all(as_int(fiscal_reconciliation[key]) == 0 for key in ("unmapped_event_keys", "multi_mapped_event_keys", "fiscal_year_total_mismatches")) else "fail",
                "metrics": fiscal_reconciliation,
            },
            "historical_source_reconciliation": {
                "reference_artifact": str(HISTORICAL_ANNUAL_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "query_reference": historical_reconciliation["query_reference"],
                "executed_on": historical_reconciliation["executed_on"],
                "acceptance_rule": historical_reconciliation["acceptance_rule"],
                "outcome": historical_reconciliation["outcome"],
                "metrics": historical_reconciliation_metrics,
            },
            "current_source_reconciliation": {
                **six_provenance["metadata"],
                "query_reference": annual_provenance["source_reconciliation"]["query_reference"],
                "executed_on": annual_provenance["source_reconciliation"]["executed_on"],
                "sql_sha256": annual_provenance["source_reconciliation"]["sql_sha256"],
                "result_sha256": annual_provenance["source_reconciliation"]["result_sha256"],
                "acceptance_rule": "Preserve current source drift relative to the frozen 2026-09-10 reconciliation.",
                "outcome": "warning",
                "metrics": source_reconciliation,
            },
            "publication_gate": {
                **six_provenance["employee_snapshot_publishability"],
                "acceptance_rule": "A complete distribution is published only when all four categories have n>=30 and reconcile to the employee-snapshot denominator.",
                "outcome": "pass" if latest_publishable_snapshot else "fail",
                "metrics": {
                    "snapshot_dates_checked_total": len(snapshot_dates),
                    "trend_snapshot_count": len(trend_dates),
                    "trend_publishable_snapshot_count": trend_publishable_count,
                    "trend_suppressed_snapshot_count": len(trend_dates) - trend_publishable_count,
                    "latest_available_snapshot": snapshot_dates[-1],
                    "latest_available_publication_status": latest_status["publication_status"],
                    "latest_publishable_snapshot": latest_publishable_snapshot,
                },
            },
            "employee_snapshot_profile": {
                **six_provenance["employee_snapshot_profile"],
                "acceptance_rule": "The published latest distribution has exactly 0/1/2+/Unknown, all buckets n>=30, and their counts sum to the eligible denominator; trend rows expose only aggregate percentages and safe categories.",
                "outcome": "pass",
                "metrics": {
                    "latest_publishable_snapshot": latest_publishable_snapshot,
                    "latest_distribution_rows": len(latest_distribution),
                    "latest_distribution_minimum_bucket_n": min(row["employee_snapshots"] for row in latest_distribution),
                    "latest_distribution_denominator": latest_distribution[0]["eligible_employee_snapshots"],
                    "trend_snapshot_count": len(trend),
                },
            },
        },
        "latest_distribution": latest_distribution,
        "latest_available_snapshot": snapshot_dates[-1],
        "latest_available_status": latest_status["publication_status"],
        "latest_publishable_snapshot": latest_publishable_snapshot,
        "trend": trend,
        "limitations": [
            "Unknown is retained when the source cannot distinguish zero applications from missing coverage; it is not converted to zero.",
            "The most recent source-backed snapshot is not fully publishable because its 2+ bucket is below n=30; the complete distribution uses the latest publishable snapshot.",
            "This is descriptive exploratory evidence and not an approved production feature or individual prediction.",
            "The broadened view is not assumed to have identical lineage or business scope with hrda.applications.",
        ],
        "provenance": six_provenance,
        "historical_reference": {
            "artifact": str(HISTORICAL_ANNUAL_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "generated_on": historical_evidence["generated_on"],
            "metrics": historical_reconciliation_metrics,
        },
    }
    return annual_evidence, six_evidence


def main() -> None:
    annual_evidence, six_evidence = build_evidence()
    OUT.mkdir(parents=True, exist_ok=True)
    annual_path = OUT / "json" / "attrition-43-variable-distributions-v2.application-intensity-evidence-20260913.json"
    six_path = OUT / "json" / "attrition-43-variable-distributions-v2.application-employee-snapshot-trailing-6m-evidence-20260913.json"
    annual_path.write_text(json.dumps(annual_evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    six_path.write_text(json.dumps(six_evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(annual_path)
    print(six_path)
    print(json.dumps({
        "annual_published_years": sorted({row["fiscal_year"] for row in annual_evidence["rows"]}),
        "annual_rows": len(annual_evidence["rows"]),
        "latest_available_snapshot": six_evidence["latest_available_snapshot"],
        "latest_publishable_snapshot": six_evidence["latest_publishable_snapshot"],
        "trend_rows": len(six_evidence["trend"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
