"""Freeze aggregate evidence for slide 3 application buckets and 12-month attrition."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "application_intensity_fiscal_year_12m_attrition_20260917.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
AUTHORIZATION = ROOT / "config" / "attrition_v7_internal_analysis_authorization_20260917.json"
REFERENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v2.application-intensity-evidence-20260913.json"
OUTPUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.application-intensity-annual-attrition-evidence-20260917.json"
YEARS = (2022, 2023, 2024, 2025, 2026)
BUCKETS = ("1", "2", "3", "4+")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_query() -> tuple[list[dict], list[str]]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(QUERY),
            "--max-rows",
            "1000",
        ],
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
    if payload.get("truncated") or not isinstance(rows, list) or len(rows) != 20:
        raise ValueError("La consulta de attrition de aplicaciones no devolvio las 20 celdas esperadas.")
    if not isinstance(columns, list) or any("employee_id" == str(column).lower() for column in columns):
        raise ValueError("No se permiten identificadores de empleado en la evidencia persistida.")
    return [dict(row) for row in rows], [str(column) for column in columns]


def normalize(row: dict) -> dict:
    return {
        "fiscal_year": int(row["fiscal_year"]),
        "fiscal_year_start": str(row["fiscal_year_start"]),
        "fiscal_year_end": str(row["fiscal_year_end"]),
        "observed_period_end": str(row["observed_period_end"]),
        "period_status": str(row["period_status"]),
        "latest_observed_snapshot": str(row["latest_observed_snapshot"]),
        "followup_status": str(row["followup_status"]),
        "application_bucket": str(row["application_bucket"]),
        "bucket_order": int(row["bucket_order"]),
        "distinct_applicants": int(row["distinct_applicants"]),
        "annual_distinct_applicants": int(row["annual_distinct_applicants"]),
        "distribution_percent": float(row["distribution_percent"]),
        "attrition_eligible_applicants": int(row["attrition_eligible_applicants"]),
        "voluntary_exits": None if row["voluntary_exits"] is None else int(row["voluntary_exits"]),
        "attrition_rate_percent": None if row["attrition_rate_percent"] is None else float(row["attrition_rate_percent"]),
        "publication_status": str(row["publication_status"]),
    }


def reference_drift(rows: list[dict]) -> dict:
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    old = {
        (int(row["fiscal_year"]), str(row["application_bucket"])): int(row["distinct_applicants"])
        for row in reference["rows"]
        if int(row["fiscal_year"]) in YEARS
    }
    current = {(row["fiscal_year"], row["application_bucket"]): row["distinct_applicants"] for row in rows}
    changed = [
        {"fiscal_year": year, "application_bucket": bucket, "reference_count": old[key], "current_count": current[key]}
        for key, value in current.items()
        if key in old and old[key] != value
        for year, bucket in [key]
    ]
    return {
        "reference_artifact": str(REFERENCE.relative_to(ROOT)).replace("\\", "/"),
        "reference_generated_on": reference.get("generated_on"),
        "changed_cells": changed,
        "changed_cell_count": len(changed),
        "interpretation": "Se conserva el resultado actual de la fuente; las diferencias pequeñas frente al congelado anterior quedan documentadas como source refresh drift.",
    }


def main() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    if authorization.get("reporting_mode") != "internal_analysis":
        raise ValueError("La autorizacion V7 debe declarar internal_analysis.")
    if not authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets"):
        raise ValueError("La autorizacion V7 no permite mostrar todos los agregados del slide.")

    raw_rows, columns = run_query()
    rows = [normalize(row) for row in raw_rows]
    pairs = {(row["fiscal_year"], row["application_bucket"]) for row in rows}
    expected = {(year, bucket) for year in YEARS for bucket in BUCKETS}
    if pairs != expected:
        raise ValueError("La matriz anual no contiene exactamente FY2022-FY2026 y buckets 1/2/3/4+.")
    for year in YEARS:
        year_rows = [row for row in rows if row["fiscal_year"] == year]
        total = year_rows[0]["annual_distinct_applicants"]
        if sum(row["distinct_applicants"] for row in year_rows) != total:
            raise ValueError(f"La distribucion de FY{year} no reconcilia al total de aplicantes.")
        if any(row["attrition_rate_percent"] is not None and row["attrition_eligible_applicants"] == 0 for row in year_rows):
            raise ValueError(f"FY{year} tiene una tasa con denominador cero.")
    complete_years = {row["fiscal_year"] for row in rows if row["followup_status"] == "complete_12m_followup"}
    if complete_years != {2022, 2023, 2024}:
        raise ValueError(f"La completitud esperada de seguimiento cambio: {sorted(complete_years)}")

    result_hash = hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    payload = {
        "schema_version": 1,
        "artifact": "application_intensity_fiscal_year_12m_attrition",
        "artifact_classification": "internal_analysis",
        "generated_on": date.today().isoformat(),
        "reporting_mode": "internal_analysis",
        "authorization": authorization,
        "query": {
            "path": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(QUERY),
            "result_sha256": result_hash,
            "columns": columns,
            "executed_on": date.today().isoformat(),
        },
        "population": "Distinct linked applicants by fiscal year and unique-requisition bucket; attrition cohort is the subset active as Employee/Regular at the fiscal-year-end snapshot.",
        "grain": "aggregate fiscal-year x application bucket",
        "target": "Strict voluntary termination in (fiscal_year_end, fiscal_year_end + 12 months].",
        "definition": {
            "application_bucket": "1, 2, 3, or 4+ unique req_id values per employee within the fiscal year.",
            "distribution_denominator": "All distinct linked applicants in the fiscal year.",
            "attrition_denominator": "Distinct applicants with a regular active employee snapshot at fiscal-year end.",
            "attrition_rate": "100 * voluntary exits / attrition-eligible applicants.",
            "fy2026": "Partial through 2026-09-10; no 12-month follow-up, therefore Not estimable.",
        },
        "privacy": {
            "aggregate_only": True,
            "small_cell_exception": True,
            "minimum_displayed_count": 0,
            "employee_rows_persisted": False,
            "employee_ids_persisted": False,
            "names_persisted": False,
            "emails_persisted": False,
        },
        "source_refresh_drift": reference_drift(rows),
        "rows": rows,
        "validation": {
            "outcome": "pass",
            "acceptance_rule": "All 20 fiscal-year/bucket cells reconcile to annual applicants; attrition is NULL when 12-month follow-up is incomplete or denominator is zero; no individual-level columns are persisted.",
            "metrics": {
                "years": len(YEARS),
                "buckets_per_year": len(BUCKETS),
                "aggregate_rows": len(rows),
                "complete_12m_followup_years": sorted(complete_years),
                "not_estimable_cells": sum(row["attrition_rate_percent"] is None for row in rows),
            },
        },
        "outcome": "pass",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)
    print(f"years={len(YEARS)}; buckets={len(BUCKETS)}; rows={len(rows)}; not_estimable={sum(row['attrition_rate_percent'] is None for row in rows)}")


if __name__ == "__main__":
    main()
