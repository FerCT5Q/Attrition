"""Freeze aggregate annual-attrition evidence for V7 navigation slides 28–39.

The SQL owns the calculation: active employee category at a historical monthly
snapshot, followed by a strict VOLUNTARY termination in the next 12 months.
This wrapper persists only aggregate category metrics and source diagnostics.
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
QUERY = ROOT / "queries" / "audits" / "v7_nav28_39_annual_attrition_direct_20260917.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.nav28-39-direct-annual-attrition-evidence-20260917.json"
)

MIN_EXPOSURE = 30
MIN_EXITS = 30


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_query() -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(QUERY),
            "--max-rows",
            "1000",
            "--reporting-mode",
            "internal_analysis",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def build_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    expected_columns = [
        "row_type",
        "metric",
        "category",
        "first_snapshot_date",
        "last_snapshot_date",
        "distinct_employee_count",
        "employee_snapshot_count",
        "voluntary_exits",
        "annual_attrition_rate_percent",
        "diagnostic_value",
    ]
    require(payload.get("columns") == expected_columns, "La consulta directa devolvió columnas inesperadas.")
    require(payload.get("truncated") is False, "La evidencia directa fue truncada.")
    rows = payload.get("rows")
    require(isinstance(rows, list) and rows, "La evidencia directa no contiene filas.")

    diagnostic_rows = [row for row in rows if row.get("row_type") == "diagnostic"]
    category_rows = [row for row in rows if row.get("row_type") == "category"]
    require(len(diagnostic_rows) == 6 and category_rows, "Faltan diagnósticos o categorías en la evidencia directa.")
    diagnostics = {str(row["metric"]): int(row["diagnostic_value"]) for row in diagnostic_rows}
    require(diagnostics.get("snapshot_count") == 24, "La ventana anual debe tener exactamente 24 snapshots completos.")
    require(diagnostics.get("duplicate_employee_snapshot_count") == 0, "Existen duplicados employee-snapshot en la cohorte directa.")
    require(diagnostics.get("conflicting_employee_snapshot_count") == 0, "Existen conflictos de definición en la cohorte directa.")
    require(diagnostics.get("baseline_employee_snapshot_count", 0) > 0, "La cohorte directa está vacía.")
    require(diagnostics.get("baseline_voluntary_exit_count", 0) > 0, "La cohorte directa no tiene eventos voluntarios.")

    for row in category_rows:
        exposure = int(row["employee_snapshot_count"])
        exits = int(row["voluntary_exits"])
        rate = float(row["annual_attrition_rate_percent"])
        require(exposure > 0 and 0 <= exits <= exposure, "Una categoría anual directa no reconcilia.")
        require(0 <= rate <= 100, "Una tasa anual directa está fuera de rango.")
        row["publication_status"] = (
            "publishable"
            if exposure >= MIN_EXPOSURE and exits >= MIN_EXITS
            else "not_estimable_below_aggregate_threshold"
        )

    return {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 7,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "purpose": (
            "Añadir attrition voluntario anual a las categorías directas y de fecha acotada "
            "de los slides de navegación 28–39; no genera predicciones individuales."
        ),
        "outcome_contract": {
            "population": "worker_type='Employee' AND employee_type='Regular' AND active_status=1",
            "grain": "employee_snapshot",
            "target": "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 12 months]",
            "history": "latest 24 complete monthly 12-month follow-up snapshots",
            "minimum_employee_snapshot_exposure": MIN_EXPOSURE,
            "minimum_voluntary_exits": MIN_EXITS,
        },
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": hashlib.sha256(QUERY.read_bytes()).hexdigest(),
        "diagnostics": diagnostics,
        "rows": category_rows,
        "publication_rule": (
            "La tasa solo se muestra cuando el segmento tiene al menos 30 exposiciones "
            "employee-snapshot y 30 salidas voluntarias; en otro caso se usa Not estimable."
        ),
        "outcome": "pass",
    }


def main() -> None:
    require(QUERY.exists(), f"No existe la consulta: {QUERY}")
    require(HELPER.exists(), f"No existe el helper read-only: {HELPER}")
    evidence = build_evidence(run_query())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print(f"aggregate_categories={len(evidence['rows'])}; outcome={evidence['outcome']}")


if __name__ == "__main__":
    main()
