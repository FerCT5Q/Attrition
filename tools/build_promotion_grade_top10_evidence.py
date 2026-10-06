"""Congela evidencia agregada para el panel Top 10 de compensation grades."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "promotion_grade_top10_trailing_12m_20260918.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.promotion-grade-top10-trailing-12m-evidence-20260918.json"
)
MIN_COHORT = 30
EXPECTED_COLUMNS = [
    "row_type",
    "grade",
    "snapshot_date",
    "window_start_exclusive",
    "window_end_inclusive",
    "current_employee_count",
    "current_distribution_percent",
    "promotion_participant_count",
    "promoted_employee_count",
    "promotion_rate_percent",
    "average_monthly_headcount",
    "voluntary_exit_count",
    "attrition_rate_percent",
    "current_rank",
    "diagnostic_metric",
    "diagnostic_value",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def result_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def run_query() -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(QUERY),
            "--max-rows",
            "100",
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


def as_int(row: dict[str, Any], key: str) -> int:
    return int(row[key])


def as_float(row: dict[str, Any], key: str) -> float:
    return float(row[key])


def build_evidence(result: dict[str, Any]) -> dict[str, Any]:
    require(result.get("columns") == EXPECTED_COLUMNS, "La consulta de grades devolvio columnas inesperadas.")
    require(result.get("truncated") is False, "La consulta de grades fue truncada.")
    rows = result.get("rows", [])
    grade_rows = [row for row in rows if row.get("row_type") == "grade"]
    diagnostic_rows = [row for row in rows if row.get("row_type") == "diagnostic"]
    require(len(grade_rows) == 10, f"Se esperaban 10 grades y se obtuvieron {len(grade_rows)}.")
    require(diagnostic_rows, "Faltan diagnosticos de la consulta de grades.")

    diagnostics = {str(row["diagnostic_metric"]): str(row["diagnostic_value"]) for row in diagnostic_rows}
    expected = {
        "latest_snapshot_date": "2026-08-23",
        "baseline_snapshot_date": "2025-08-24",
        "window_snapshot_count": "12",
        "review_snapshot_date": "2025-11-23",
        "top10_grade_count": "10",
        "current_missing_grade_count": "0",
        "current_duplicate_employee_count": "0",
        "current_conflicting_grade_count": "0",
        "voluntary_event_count": "2604",
        "voluntary_event_assigned_count": "2603",
        "voluntary_event_unassigned_count": "1",
    }
    for key, value in expected.items():
        require(diagnostics.get(key) == value, f"No supera la validacion {key}: {diagnostics.get(key)!r}.")

    safe_rows: list[dict[str, Any]] = []
    for row in sorted(grade_rows, key=lambda item: int(item["current_rank"])):
        grade = str(row["grade"])
        rank = as_int(row, "current_rank")
        current_count = as_int(row, "current_employee_count")
        participants = as_int(row, "promotion_participant_count")
        promoted = as_int(row, "promoted_employee_count")
        average_headcount = as_float(row, "average_monthly_headcount")
        exits = as_int(row, "voluntary_exit_count")
        promotion_rate = as_float(row, "promotion_rate_percent")
        attrition_rate = as_float(row, "attrition_rate_percent")

        require(rank == len(safe_rows) + 1, "El ranking de grades no es contiguo.")
        require(re.fullmatch(r"[A-Z][0-9]+", grade) is not None, f"Grade no normalizado: {grade!r}.")
        require(current_count >= MIN_COHORT, f"El grade {grade} no cumple n>=30.")
        require(participants >= MIN_COHORT, f"El grade {grade} no cumple n>=30 para promotion.")
        require(average_headcount >= MIN_COHORT, f"El grade {grade} no cumple n>=30 para attrition.")
        require(exits >= MIN_COHORT, f"El grade {grade} no cumple n>=30 de exits para attrition.")
        require(abs(promotion_rate - 100.0 * promoted / participants) <= 0.00011, f"Promotion rate inconsistente en {grade}.")
        require(abs(attrition_rate - 100.0 * exits / average_headcount) <= 0.00011, f"Attrition inconsistente en {grade}.")

        safe_rows.append(
            {
                "grade": grade,
                "current_rank": rank,
                "current_employee_count": current_count,
                "current_distribution_percent": as_float(row, "current_distribution_percent"),
                "promotion_participant_count": participants,
                "promoted_employee_count": promoted,
                "promotion_rate_percent": promotion_rate,
                "average_monthly_headcount": average_headcount,
                "voluntary_exit_count": exits,
                "attrition_rate_percent": attrition_rate,
            }
        )

    require(len({row["grade"] for row in safe_rows}) == 10, "Hay grades duplicados en el Top 10.")
    require(all(safe_rows[i]["current_employee_count"] >= safe_rows[i + 1]["current_employee_count"] for i in range(9)), "El Top 10 no esta ordenado por empleados actuales.")
    require(sum(row["current_employee_count"] for row in safe_rows) > 0, "El Top 10 no tiene poblacion.")

    evidence = {
        "artifact_type": "promotion_grade_top10_trailing_12m_slide_evidence",
        "version": 1,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "purpose": "Agregar al slide de pay tracks un panel con los diez compensation grades exactos de mayor poblacion actual.",
        "query_provenance": {
            "path": str(QUERY.relative_to(ROOT)).replace("\\\\", "/"),
            "sql_sha256": sha256_bytes(QUERY.read_bytes()),
            "result_sha256": result_hash(result),
        },
        "definition": {
            "grade": "Compensation grade exacto, sin colapsar por letra.",
            "ranking": "Top 10 por empleados Employee, Regular, activos y no RF360 en el snapshot 2026-08-23.",
            "distribution": "Porcentaje de la poblacion actual completa representado por cada grade exacto.",
            "promotion_rate": "promotion_yes_no='Yes' dividido entre participantes elegibles del ciclo AR25, por grade del ciclo.",
            "attrition_rate": "Exits strict VOLUNTARY en (2025-08-24, 2026-08-23] divididos entre el headcount mensual promedio del grade en los doce snapshots.",
        },
        "window": {
            "snapshot_date": "2026-08-23",
            "start_exclusive": "2025-08-24",
            "end_inclusive": "2026-08-23",
            "monthly_snapshot_count": 12,
            "annual_review_cycle": "AR25",
            "annual_review_population_snapshot": diagnostics["review_snapshot_date"],
        },
        "top_grade_rows": safe_rows,
        "privacy": {
            "minimum_shared_cohort": MIN_COHORT,
            "displayed_grade_count": len(safe_rows),
            "employee_rows_or_identifiers_persisted": False,
            "exact_pay_values_persisted": False,
        },
        "diagnostics": diagnostics,
        "outcome": "pass",
    }
    encoded = json.dumps(evidence, ensure_ascii=False).lower()
    for prohibited in ('"employee_id"', '"employee_key"', '"name"', '"email"', '"salary"', '"base_pay"'):
        require(prohibited not in encoded, f"La evidencia contiene el campo prohibido {prohibited}.")
    return evidence


def main() -> None:
    for path in (QUERY, HELPER):
        require(path.exists(), f"No existe el insumo requerido: {path}.")
    evidence = build_evidence(run_query())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print(f"outcome={evidence['outcome']}; displayed_grades={len(evidence['top_grade_rows'])}")


if __name__ == "__main__":
    main()

