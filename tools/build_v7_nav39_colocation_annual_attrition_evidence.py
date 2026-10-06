"""Persist aggregate annual attrition evidence for V7 co-location trend bars."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "v7_nav39_colocation_annual_attrition_20260917.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.nav39-colocation-annual-attrition-evidence-20260917.json"
MIN_EXPOSURE = 30
MIN_EXITS = 30


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(HELPER), "--sql-file", str(QUERY), "--max-rows", "1000", "--reporting-mode", "internal_analysis"],
        cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    )
    payload: dict[str, Any] = json.loads(completed.stdout)
    require(payload.get("truncated") is False, "La consulta co-location fue truncada.")
    rows = payload.get("rows")
    require(isinstance(rows, list) and rows, "La consulta co-location no devolvió filas.")
    category_rows = [row for row in rows if row.get("row_type") == "category"]
    coverage = {str(row["category"]): row for row in rows if row.get("row_type") == "coverage"}
    diagnostics = {str(row["metric"]): int(row["diagnostic_value"]) for row in rows if row.get("row_type") == "diagnostic"}
    require(diagnostics.get("duplicate_employee_snapshot_count") == 0, "Co-location contiene duplicados employee-snapshot.")
    require(diagnostics.get("conflicting_employee_snapshot_count") == 0, "Co-location contiene conflictos de fuente.")
    require({str(row["metric"]) for row in category_rows} == {"same_office_site", "same_office_site_and_city"}, "Cobertura co-location inesperada.")
    for year in map(str, range(2020, 2027)):
        require(year in coverage, f"Falta cobertura co-location para FY{year}.")
    for row in category_rows:
        exposure, exits = int(row["employee_snapshot_count"]), int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        require(exposure > 0 and 0 <= exits <= exposure and 0 <= rate <= 100, "Una tasa co-location no reconcilia.")
        year_coverage = coverage[str(row["category"])]
        row["complete_followup_fiscal_year"] = int(year_coverage["complete_followup_snapshots"]) == int(year_coverage["total_source_snapshots"])
        row["complete_followup_snapshots"] = int(year_coverage["complete_followup_snapshots"])
        row["total_source_snapshots"] = int(year_coverage["total_source_snapshots"])
        row["publication_status"] = "publishable" if exposure >= MIN_EXPOSURE and exits >= MIN_EXITS else "not_estimable_below_aggregate_threshold"
    evidence = {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 7,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "purpose": "Añadir attrition anual de empleados que comparten office_site, o office_site y city, con su manager en cada barra anual de co-location.",
        "outcome_contract": {
            "population": "active regular employee-manager pairs with comparable stored assigned-location fields at each snapshot",
            "grain": "employee_snapshot",
            "target": "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 12 months]",
            "history": "all snapshots whose 12-month follow-up is observable; fiscal-year completeness is reported separately",
            "minimum_employee_snapshot_exposure": MIN_EXPOSURE,
            "minimum_voluntary_exits": MIN_EXITS,
        },
        "definition": "Píldora por año = attrition anual de empleados que cumplen el proxy de co-location mostrado por esa barra; no es evidencia de presencia física.",
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": hashlib.sha256(QUERY.read_bytes()).hexdigest(),
        "diagnostics": diagnostics,
        "coverage": coverage,
        "rows": category_rows,
        "publication_rule": "FY con seguimiento incompleto mantiene una marca visible; FY sin snapshots con 12 meses de seguimiento se muestra Not estimable.",
        "outcome": "pass",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print(f"aggregate_categories={len(category_rows)}; outcome=pass")


if __name__ == "__main__":
    main()
