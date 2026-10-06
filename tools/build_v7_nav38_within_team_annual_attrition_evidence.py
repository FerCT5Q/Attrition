"""Persist aggregate annual team-attrition evidence for the within-team-pay slide."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "v7_nav38_within_team_compensation_annual_attrition_20260917.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.nav38-within-team-annual-attrition-evidence-20260917.json"
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
    require(payload.get("truncated") is False, "La consulta de within-team fue truncada.")
    rows = payload.get("rows")
    require(isinstance(rows, list) and rows, "La consulta de within-team no devolvió filas.")
    categories = [row for row in rows if row.get("row_type") == "category"]
    diagnostics = {str(row["metric"]): int(row["diagnostic_value"]) for row in rows if row.get("row_type") == "diagnostic"}
    require(diagnostics.get("snapshot_count") == 24, "Within-team debe usar 24 snapshots completos.")
    require(diagnostics.get("duplicate_employee_snapshot_count") == 0, "Within-team tiene duplicados employee-snapshot.")
    require(diagnostics.get("conflicting_employee_snapshot_count") == 0, "Within-team tiene conflictos de definición.")
    require({str(row["metric"]) for row in categories} == {"within_team_review_count", "within_team_review_share", "within_team_no_comparable"}, "Cobertura within-team inesperada.")
    for row in categories:
        exposure, exits = int(row["employee_snapshot_count"]), int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        require(exposure > 0 and 0 <= exits <= exposure and 0 <= rate <= 100, "Una tasa within-team no reconcilia.")
        row["publication_status"] = "publishable" if exposure >= MIN_EXPOSURE and exits >= MIN_EXITS else "not_estimable_below_aggregate_threshold"
    evidence = {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 7,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "purpose": "Mostrar attrition voluntario anual de miembros de equipos cuyo manager pertenece a cada estado visible de revisión de compensación.",
        "outcome_contract": {
            "population": "active regular direct reports assigned to managers at the historical snapshot",
            "grain": "employee_snapshot",
            "target": "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 12 months]",
            "history": "latest 24 complete monthly 12-month follow-up snapshots",
            "minimum_employee_snapshot_exposure": MIN_EXPOSURE,
            "minimum_voluntary_exits": MIN_EXITS,
        },
        "definition": "El conteo del gráfico permanece en managers; la píldora reporta team-member attrition de los empleados asignados a managers de esa categoría. No se muestran IDs ni compensación exacta.",
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": hashlib.sha256(QUERY.read_bytes()).hexdigest(),
        "diagnostics": diagnostics,
        "rows": categories,
        "publication_rule": "Not estimable para menos de 30 exposiciones employee-snapshot o 30 salidas voluntarias.",
        "outcome": "pass",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print(f"aggregate_categories={len(categories)}; outcome=pass")


if __name__ == "__main__":
    main()
