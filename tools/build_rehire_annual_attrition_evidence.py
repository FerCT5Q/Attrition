"""Freeze aggregate annual rehire-attrition evidence for V7 slide 16.

The script is intentionally a small wrapper around the guarded Redshift
reader.  It persists only aggregate fiscal-year results, never employee rows.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "rehire_annual_voluntary_attrition_by_fiscal_year_20260917.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.rehire-annual-attrition-evidence-20260917.json"
EXPECTED_YEARS = ("2020", "2021", "2023", "2024", "2025", "2026")
ALLOWED_STATUSES = {
    "not_comparable_source_era",
    "publishable",
    "publishable_mature_partial_year",
    "not_estimable_incomplete_followup",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_rows(rows: list[dict[str, Any]]) -> None:
    if [str(row.get("fiscal_year")) for row in rows] != list(EXPECTED_YEARS):
        raise ValueError("La consulta de rehire debe devolver exactamente los seis años del visual, en orden.")
    for row in rows:
        status = str(row.get("publication_status"))
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Estado de publicación inesperado para rehire: {status!r}.")
        if int(row.get("employee_snapshot_count") or 0) < 0 or int(row.get("distinct_employee_count") or 0) < 0:
            raise ValueError("La evidencia de rehire contiene un denominador negativo.")
        if status.startswith("publishable"):
            if int(row["employee_snapshot_count"]) < 30 or int(row["distinct_employee_count"]) < 30:
                raise ValueError("Una tasa publicada de rehire no cumple el mínimo de cohorte.")
            if row.get("attrition_rate_percent") is None:
                raise ValueError("Una tasa publicada de rehire no tiene porcentaje de attrition.")
        elif row.get("attrition_rate_percent") is not None:
            raise ValueError("Una tasa no publicable de rehire no debe conservar porcentaje de attrition.")

    status_by_year = {str(row["fiscal_year"]): str(row["publication_status"]) for row in rows}
    if status_by_year["2020"] != "not_comparable_source_era" or status_by_year["2021"] != "not_comparable_source_era":
        raise ValueError("Los años previos al corte de fuente deben permanecer no comparables.")
    if status_by_year["2026"] != "not_estimable_incomplete_followup":
        raise ValueError("FY2026 debe permanecer no estimable sin seguimiento anual completo.")


def build_evidence(rows: list[dict[str, Any]], columns: list[str] | None) -> dict[str, Any]:
    validate_rows(rows)
    return {
        "artifact_type": "aggregate_rehire_annual_attrition_evidence",
        "version": 7,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "artifact_classification": "internal_analysis",
        "purpose": "Etiquetar la attrition voluntaria a 12 meses debajo de cada barra anual de Rehire (1) en la lámina 16.",
        "definition": {
            "concept": "Stored is_rehire flag",
            "display_group": "Rehire (1)",
            "population": "Active Regular Employees at each monthly snapshot",
            "grain": "Deduplicated employee-snapshot exposure, grouped by fiscal year",
            "outcome": "Strict VOLUNTARY termination in (snapshot_date, snapshot_date + 12 months]",
            "minimum_cohort": 30,
        },
        "source_era_rule": "FY2020 and FY2021 are labeled not comparable because the slide documents a source-definition break beginning 2022-10-23.",
        "partial_year_rule": "FY2025 rate is published from mature monthly snapshots only and is marked with an asterisk in the visual.",
        "not_estimable_rule": "FY2026 has no complete 12-month follow-up in the retained source window and renders as Not estimable.",
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": digest(QUERY),
        "columns": columns,
        "row_count": len(rows),
        "rows": rows,
        "acceptance_rule": "Publish only years with >=30 employee-snapshot exposures and >=30 distinct employees; preserve source-era and incomplete-follow-up limitations instead of imputing a rate.",
        "outcome": "pass",
    }


def main() -> None:
    if not QUERY.exists() or not HELPER.exists():
        raise FileNotFoundError("No existe la consulta o el helper read-only requerido para rehire.")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(QUERY),
            "--max-rows",
            "20",
            "--reporting-mode",
            "internal_analysis",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    payload = json.loads(result.stdout)
    rows = payload.get("rows")
    if not isinstance(rows, list) or payload.get("truncated"):
        raise ValueError("La consulta de rehire debe devolver todos los agregados sin truncamiento.")
    evidence = build_evidence(rows, payload.get("columns"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
