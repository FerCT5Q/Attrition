"""Freeze aggregate-only evidence for slide 3 rolling-August attrition."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
METADATA_QUERY = ROOT / "queries" / "audits" / "application_trailing_12m_august_attrition_metadata_20260918.sql"
MAIN_QUERY = ROOT / "queries" / "audits" / "application_trailing_12m_august_attrition_20260918.sql"
AUTHORIZATION = ROOT / "config" / "application_intensity_internal_analysis_authorization_20260913.json"
OUTPUT = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.application-trailing-12m-august-attrition-evidence-20260918.json"
)
YEARS = (2022, 2023, 2024, 2025, 2026)
VISIBLE_YEARS = (2025, 2026)
BUCKETS = ("1", "2", "3", "4+")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_query(query_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    completed = subprocess.run(
        [sys.executable, "-B", str(HELPER), "--sql-file", str(query_path), "--max-rows", "100"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    payload = json.loads(completed.stdout)
    rows = payload.get("rows")
    columns = payload.get("columns")
    if payload.get("truncated") or not isinstance(rows, list) or not isinstance(columns, list):
        raise ValueError(f"{query_path.name} no devolvio un resultado agregado completo.")
    if any("employee_id" == str(column).lower() for column in columns):
        raise ValueError("No se permiten identificadores de empleado en la evidencia persistida.")
    return [dict(row) for row in rows], [str(column) for column in columns]


def normalize_main_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "cutoff_year": int(row["cutoff_year"]),
        "august_cutoff_date": str(row["august_cutoff_date"]),
        "window_start_date": str(row["window_start_date"]).split(" ", 1)[0],
        "application_bucket": str(row["application_bucket"]),
        "bucket_order": int(row["bucket_order"]),
        "distinct_applicant_count": int(row["distinct_applicant_count"]),
        "total_distinct_applicants": int(row["total_distinct_applicants"]),
        "voluntary_exit_count": int(row["voluntary_exit_count"]),
        "trailing_12m_voluntary_attrition_percent": (
            None
            if row["trailing_12m_voluntary_attrition_percent"] is None
            else float(row["trailing_12m_voluntary_attrition_percent"])
        ),
    }


def validate_authorization(authorization: dict[str, Any]) -> None:
    scope = authorization.get("scope", {})
    rolling_scope = scope.get("trailing_12m_august_application_attrition", {})
    if authorization.get("reporting_mode") != "internal_analysis":
        raise ValueError("La autorizacion debe declarar internal_analysis.")
    if not authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets"):
        raise ValueError("La autorizacion no permite buckets agregados por debajo de n=30.")
    if rolling_scope.get("artifact") != "application_intensity_trailing_12m_august_attrition":
        raise ValueError("La autorizacion no incluye el artefacto rolling-August solicitado.")
    if not rolling_scope.get("subthreshold_aggregate_buckets_authorized"):
        raise ValueError("La autorizacion rolling-August no permite los buckets agregados pequenos.")


def validate_metadata(rows: list[dict[str, Any]]) -> None:
    by_table = {str(row["table_name"]): row for row in rows}
    expected = {
        "job_applications_vw": {
            "required_columns_found": 4,
            "employee_id_columns": 1,
            "req_id_columns": 1,
            "application_date_columns": 1,
            "cand_applied_columns": 1,
        },
        "post_hire_monthly_worker_dtls": {
            "required_columns_found": 3,
            "employee_id_columns": 1,
            "term_date_columns": 1,
            "term_type_columns": 1,
        },
    }
    if set(by_table) != set(expected):
        raise ValueError("La metadata no devolvio exactamente las dos fuentes requeridas.")
    for table, requirements in expected.items():
        for column, expected_value in requirements.items():
            if int(by_table[table][column]) != expected_value:
                raise ValueError(f"La metadata de {table}.{column} no cumple la regla de aceptacion.")


def validate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected_pairs = {(year, bucket) for year in YEARS for bucket in BUCKETS}
    pairs = {(row["cutoff_year"], row["application_bucket"]) for row in rows}
    if len(rows) != len(expected_pairs) or pairs != expected_pairs:
        raise ValueError("La matriz debe contener cinco cortes de agosto por cuatro buckets.")

    metrics_by_year: list[dict[str, Any]] = []
    for year in YEARS:
        year_rows = [row for row in rows if row["cutoff_year"] == year]
        totals = {row["total_distinct_applicants"] for row in year_rows}
        cutoff_dates = {row["august_cutoff_date"] for row in year_rows}
        if len(totals) != 1 or len(cutoff_dates) != 1:
            raise ValueError(f"El corte o total de {year} no es consistente entre buckets.")
        total = totals.pop()
        if sum(row["distinct_applicant_count"] for row in year_rows) != total:
            raise ValueError(f"Los buckets de {year} no reconcilian a los aplicantes distintos.")
        for row in year_rows:
            denominator = row["distinct_applicant_count"]
            exits = row["voluntary_exit_count"]
            rate = row["trailing_12m_voluntary_attrition_percent"]
            if denominator < 0 or exits < 0 or exits > denominator:
                raise ValueError(f"El numerador o denominador de {year}/{row['application_bucket']} es invalido.")
            expected_rate = None if denominator == 0 else round(100 * exits / denominator, 2)
            if rate != expected_rate:
                raise ValueError(f"La tasa de {year}/{row['application_bucket']} no reconcilia a sus agregados.")
        repeat_count = sum(row["distinct_applicant_count"] for row in year_rows if row["application_bucket"] != "1")
        metrics_by_year.append(
            {
                "cutoff_year": year,
                "august_cutoff_date": next(iter(cutoff_dates)),
                "total_distinct_applicants": total,
                "repeat_applicant_count": repeat_count,
                "repeat_applicant_percent": round(100 * repeat_count / total, 2),
            }
        )

    subthreshold = [
        {
            "cutoff_year": row["cutoff_year"],
            "application_bucket": row["application_bucket"],
            "distinct_applicant_count": row["distinct_applicant_count"],
        }
        for row in rows
        if row["distinct_applicant_count"] < 30
    ]
    return {
        "cutoffs": metrics_by_year,
        "subthreshold_aggregate_buckets": subthreshold,
        "subthreshold_aggregate_bucket_count": len(subthreshold),
    }


def main() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    validate_authorization(authorization)
    metadata_rows, metadata_columns = run_query(METADATA_QUERY)
    validate_metadata(metadata_rows)
    raw_rows, main_columns = run_query(MAIN_QUERY)
    rows = [normalize_main_row(row) for row in raw_rows]
    validation_metrics = validate_rows(rows)

    payload = {
        "schema_version": 1,
        "artifact": "application_intensity_trailing_12m_august_attrition",
        "artifact_classification": "internal_analysis",
        "reporting_mode": "internal_analysis",
        "generated_on": date.today().isoformat(),
        "authorization": authorization,
        "semantic_type": "derived_feature",
        "definition": {
            "population": "Distinct linked applicants with cand_applied=1, employee_id, req_id and application_date in the 12 months ending at the August cutoff.",
            "application_bucket": "1, 2, 3, or 4+ unique requisitions per applicant in that same trailing window.",
            "outcome": "Strict VOLUNTARY termination after the first qualifying application and on or before the August cutoff.",
            "rate": "100 * voluntary_exit_count / distinct_applicant_count.",
            "time_interpretation": "Observed trailing-12-month attrition ending at the August cutoff; it is not prospective follow-up after a fiscal-year endpoint.",
        },
        "grain": "aggregate August cutoff x application bucket",
        "visible_slide_cutoffs": list(VISIBLE_YEARS),
        "evidence_only_cutoffs": [year for year in YEARS if year not in VISIBLE_YEARS],
        "provenance": {
            "metadata_query": {
                "path": str(METADATA_QUERY.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(METADATA_QUERY),
                "result_sha256": canonical_hash(metadata_rows),
                "columns": metadata_columns,
                "executed_on": date.today().isoformat(),
            },
            "main_query": {
                "path": str(MAIN_QUERY.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(MAIN_QUERY),
                "result_sha256": canonical_hash(rows),
                "columns": main_columns,
                "executed_on": date.today().isoformat(),
            },
        },
        "privacy": {
            "aggregate_only": True,
            "employee_rows_persisted": False,
            "employee_ids_persisted": False,
            "names_persisted": False,
            "requisition_ids_or_titles_persisted": False,
            "small_cell_exception": True,
            "minimum_displayed_count": 0,
        },
        "metadata_rows": metadata_rows,
        "rows": rows,
        "validation": {
            "outcome": "pass",
            "acceptance_rule": "Exactly five August cutoffs (2022-2026) x four buckets are returned; bucket denominators reconcile to each cutoff total; voluntary exits are within their bucket denominator; every displayed rate reconciles to its aggregate numerator and denominator; only aggregate columns are persisted.",
            "metrics": {
                "years": len(YEARS),
                "buckets_per_year": len(BUCKETS),
                "aggregate_rows": len(rows),
                "visible_slide_cutoffs": list(VISIBLE_YEARS),
                **validation_metrics,
            },
        },
        "outcome": "pass",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)
    print(f"years={len(YEARS)}; rows={len(rows)}; visible_cutoffs={','.join(map(str, VISIBLE_YEARS))}")


if __name__ == "__main__":
    main()
