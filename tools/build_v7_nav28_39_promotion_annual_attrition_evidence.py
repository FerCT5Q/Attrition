"""Persist aggregate annual attrition evidence for V7 promotion visuals."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "v7_nav28_39_annual_attrition_promotion_20260917.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.nav28-39-promotion-annual-attrition-evidence-20260917.json"
)
MIN_EXPOSURE = 30
MIN_EXITS = 30


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def query() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-B", str(HELPER), "--sql-file", str(QUERY), "--max-rows", "1000", "--reporting-mode", "internal_analysis"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def build(payload: dict[str, Any]) -> dict[str, Any]:
    require(payload.get("truncated") is False, "La consulta anual de promociones fue truncada.")
    rows = payload.get("rows")
    require(isinstance(rows, list) and rows, "La consulta anual de promociones no devolvió filas.")
    categories = [row for row in rows if row.get("row_type") == "category"]
    diagnostics = {str(row["metric"]): int(row["diagnostic_value"]) for row in rows if row.get("row_type") == "diagnostic"}
    require(categories, "Faltan categorías de promoción.")
    require(diagnostics.get("target_snapshot_count") == 24, "La ventana anual de promociones debe contener 24 snapshots completos.")
    require(diagnostics.get("target_duplicate_employee_snapshot_count") == 0, "Hay duplicados target employee-snapshot en promociones.")
    require(diagnostics.get("target_conflicting_employee_snapshot_count") == 0, "Hay conflictos de promoción o grade en la cohorte target.")
    expected_metrics = {"time_since_promotion", "promotion_history_by_grade", "current_grade_entry_path"}
    require({str(row["metric"]) for row in categories} == expected_metrics, "La cobertura de categorías de promoción no coincide con el contrato.")
    for row in categories:
        exposure = int(row["employee_snapshot_count"])
        exits = int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        require(exposure > 0 and 0 <= exits <= exposure and 0 <= rate <= 100, "Una categoría anual de promoción no reconcilia.")
        row["publication_status"] = "publishable" if exposure >= MIN_EXPOSURE and exits >= MIN_EXITS else "not_estimable_below_aggregate_threshold"

    return {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 7,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "purpose": "Asignar la categoría de promoción al snapshot histórico y calcular attrition voluntario en los 12 meses posteriores.",
        "outcome_contract": {
            "population": "worker_type='Employee' AND employee_type='Regular' AND active_status=1",
            "grain": "employee_snapshot",
            "target": "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 12 months]",
            "history": "latest 24 complete monthly 12-month follow-up snapshots",
            "minimum_employee_snapshot_exposure": MIN_EXPOSURE,
            "minimum_voluntary_exits": MIN_EXITS,
        },
        "definitions": {
            "time_since_promotion": "Última promoción válida registrada dentro del episodio actual al momento del snapshot; los episodios anteriores al inicio de la historia permanecen explícitamente censurados.",
            "promotion_history_by_grade": "Conteo de eventos de promoción válidos del episodio actual hasta el snapshot, separado de la historia parcial.",
            "current_grade_entry_path": "Último cambio observable al grade vigente hasta el snapshot, con confirmación de promoción solo dentro de la ventana de entrada observada.",
        },
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": hashlib.sha256(QUERY.read_bytes()).hexdigest(),
        "diagnostics": diagnostics,
        "rows": categories,
        "publication_rule": "Las celdas con menos de 30 exposiciones employee-snapshot o 30 salidas voluntarias se muestran como Not estimable.",
        "outcome": "pass",
    }


def main() -> None:
    require(QUERY.exists() and HELPER.exists(), "Falta la consulta o el helper read-only para promociones.")
    evidence = build(query())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print(f"aggregate_categories={len(evidence['rows'])}; outcome={evidence['outcome']}")


if __name__ == "__main__":
    main()
