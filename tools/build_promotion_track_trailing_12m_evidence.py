"""Congela evidencia agregada para la lamina de compensation tracks.

La salida no conserva filas ni identificadores de empleados. El artefacto
publicable omite cualquier track actual con menos de 30 empleados.
"""

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
MAIN_QUERY = ROOT / "queries" / "audits" / "promotion_track_trailing_12m_20260918.sql"
FALLBACK_QUERY = ROOT / "queries" / "audits" / "promotion_track_unmatched_exit_nonnull_grade_20260918.sql"
ANALYSIS_PLAN = ROOT / "config" / "analysis-plans" / "20260918-promotion-track-trailing-12m-slide-v5.yaml"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.promotion-track-trailing-12m-evidence-20260918.json"
)

MIN_COHORT = 30
MIN_EXIT_ASSIGNMENT_COVERAGE_PERCENT = 99.5
EXPECTED_MAIN_COLUMNS = [
    "row_type",
    "track",
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
    "diagnostic_metric",
    "diagnostic_value",
]
EXPECTED_FALLBACK_COLUMNS = [
    "voluntary_event_count",
    "prior_active_track_count",
    "fallback_candidate_event_count",
    "fallback_unique_nonnull_grade_count",
    "fallback_conflicting_nonnull_grade_count",
    "fallback_with_null_copies_count",
    "fallback_valid_track_count",
    "unresolved_after_stable_nonnull_fallback_count",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def result_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def run_query(path: Path, max_rows: int) -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(path),
            "--max-rows",
            str(max_rows),
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


def build_evidence(main: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    require(main.get("columns") == EXPECTED_MAIN_COLUMNS, "La consulta principal devolvio columnas inesperadas.")
    require(main.get("truncated") is False, "La consulta principal fue truncada.")
    require(fallback.get("columns") == EXPECTED_FALLBACK_COLUMNS, "La auditoria de fallback devolvio columnas inesperadas.")
    require(fallback.get("truncated") is False, "La auditoria de fallback fue truncada.")
    require(len(fallback.get("rows", [])) == 1, "La auditoria de fallback debe devolver una sola fila.")

    rows = main.get("rows", [])
    track_rows = [row for row in rows if row.get("row_type") == "track"]
    diagnostic_rows = [row for row in rows if row.get("row_type") == "diagnostic"]
    require(track_rows and diagnostic_rows, "Faltan filas de track o diagnosticos.")
    diagnostics = {str(row["diagnostic_metric"]): str(row["diagnostic_value"]) for row in diagnostic_rows}

    expected_diagnostics = {
        "latest_snapshot_date": "2026-08-23",
        "baseline_snapshot_date": "2025-08-24",
        "latest_snapshot_exists": "1",
        "baseline_snapshot_exists": "1",
        "window_snapshot_count": "12",
        "review_snapshot_date": "2025-11-23",
        "current_missing_grade_count": "0",
        "current_invalid_grade_pattern_count": "0",
        "current_duplicate_employee_count": "0",
        "current_conflicting_grade_count": "0",
        "window_duplicate_employee_snapshot_count": "0",
        "window_conflicting_grade_count": "0",
        "annual_review_duplicate_employee_count": "0",
        "annual_review_conflicting_grade_count": "0",
        "annual_review_conflicting_promotion_flag_count": "0",
        "annual_review_invalid_promotion_flag_count": "0",
        "annual_review_missing_grade_count": "0",
        "annual_review_snapshot_unmatched_count": "0",
    }
    for key, expected in expected_diagnostics.items():
        require(diagnostics.get(key) == expected, f"No supera la validacion {key}: {diagnostics.get(key)!r}.")

    require(all(re.fullmatch(r"[A-Z]|Unknown", str(row["track"])) for row in track_rows), "Existe un track no normalizado.")
    current_total = int(diagnostics["current_population_count"])
    require(sum(as_int(row, "current_employee_count") for row in track_rows) == current_total, "La distribucion no reconcilia con la poblacion actual.")
    require(abs(sum(as_float(row, "current_distribution_percent") for row in track_rows) - 100.0) <= 0.001, "Los porcentajes de distribucion no suman 100%.")

    promotion_participants = sum(as_int(row, "promotion_participant_count") for row in track_rows)
    promoted = sum(as_int(row, "promoted_employee_count") for row in track_rows)
    require(promotion_participants == int(diagnostics["annual_review_scope_eligible_count"]), "Los participantes por track no reconcilian.")
    require(promoted == int(diagnostics["annual_review_promoted_employee_count"]), "Los promovidos por track no reconcilian.")

    fallback_row = fallback["rows"][0]
    event_count = as_int(fallback_row, "voluntary_event_count")
    assigned_exit_count = int(diagnostics["voluntary_event_track_total"])
    unassigned_exit_count = int(diagnostics["voluntary_event_unassigned_count"])
    assignment_coverage = 100.0 * assigned_exit_count / event_count
    require(event_count == int(diagnostics["voluntary_event_count"]), "El total de exits no reconcilia entre consultas.")
    require(as_int(fallback_row, "prior_active_track_count") == int(diagnostics["voluntary_event_prior_track_count"]), "El join temporal no reconcilia.")
    require(as_int(fallback_row, "fallback_valid_track_count") == int(diagnostics["voluntary_event_fallback_track_count"]), "El fallback no reconcilia.")
    require(as_int(fallback_row, "unresolved_after_stable_nonnull_fallback_count") == unassigned_exit_count, "Los exits no asignados no reconcilian.")
    require(as_int(fallback_row, "fallback_conflicting_nonnull_grade_count") == unassigned_exit_count, "Todo exit excluido debe corresponder a un conflicto real de grade.")
    require(assigned_exit_count + unassigned_exit_count == event_count, "La asignacion de exits no es exhaustiva.")
    require(assignment_coverage >= MIN_EXIT_ASSIGNMENT_COVERAGE_PERCENT, "La cobertura de track para exits es insuficiente.")
    require(sum(as_int(row, "voluntary_exit_count") for row in track_rows) == assigned_exit_count, "Los exits por track no reconcilian.")

    safe_rows: list[dict[str, Any]] = []
    suppressed_current_tracks = 0
    for row in track_rows:
        current_count = as_int(row, "current_employee_count")
        if current_count <= 0:
            continue
        if current_count < MIN_COHORT:
            suppressed_current_tracks += 1
            continue
        participants = as_int(row, "promotion_participant_count")
        promoted_count = as_int(row, "promoted_employee_count")
        average_headcount = as_float(row, "average_monthly_headcount")
        exits = as_int(row, "voluntary_exit_count")
        require(participants >= MIN_COHORT, f"El track {row['track']} no cumple n>=30 para promocion.")
        require(average_headcount >= MIN_COHORT, f"El track {row['track']} no cumple n>=30 para attrition.")
        require(exits >= MIN_COHORT, f"El track {row['track']} no cumple el minimo de exits para publicar attrition.")
        promotion_rate = as_float(row, "promotion_rate_percent")
        attrition_rate = as_float(row, "attrition_rate_percent")
        require(abs(promotion_rate - 100.0 * promoted_count / participants) <= 0.00011, f"La tasa de promocion de {row['track']} no reconcilia.")
        require(abs(attrition_rate - 100.0 * exits / average_headcount) <= 0.00011, f"La tasa de attrition de {row['track']} no reconcilia.")
        safe_rows.append(
            {
                "track": str(row["track"]),
                "current_employee_count": current_count,
                "current_distribution_percent": as_float(row, "current_distribution_percent"),
                "promotion_participant_count": participants,
                "promoted_employee_count": promoted_count,
                "promotion_rate_percent": promotion_rate,
                "average_monthly_headcount": average_headcount,
                "voluntary_exit_count": exits,
                "attrition_rate_percent": attrition_rate,
            }
        )

    safe_rows.sort(key=lambda row: (-int(row["current_employee_count"]), str(row["track"])))
    require(len(safe_rows) >= 2, "No hay suficientes tracks publicables.")
    require(suppressed_current_tracks >= 1, "Se esperaba al menos un track actual bajo el umbral de privacidad.")
    visible_distribution_coverage = 100.0 * sum(int(row["current_employee_count"]) for row in safe_rows) / current_total
    overall_promotion_rate = 100.0 * promoted / promotion_participants
    total_average_headcount = sum(as_float(row, "average_monthly_headcount") for row in track_rows)
    overall_attrition_rate = 100.0 * assigned_exit_count / total_average_headcount

    evidence = {
        "artifact_type": "promotion_track_trailing_12m_slide_evidence",
        "version": 1,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "purpose": "Actualizar la lamina 30 con compensation grades colapsados por letra y tasas agregadas de promocion y attrition.",
        "analysis_plan": {
            "path": str(ANALYSIS_PLAN.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_bytes(ANALYSIS_PLAN.read_bytes()),
        },
        "query_provenance": {
            "main": {
                "path": str(MAIN_QUERY.relative_to(ROOT)).replace("\\", "/"),
                "sql_sha256": sha256_bytes(MAIN_QUERY.read_bytes()),
                "result_sha256": result_hash(main),
            },
            "exit_fallback_audit": {
                "path": str(FALLBACK_QUERY.relative_to(ROOT)).replace("\\", "/"),
                "sql_sha256": sha256_bytes(FALLBACK_QUERY.read_bytes()),
                "result_sha256": result_hash(fallback),
            },
        },
        "definition": {
            "track": "Primera letra de compensation_grade/grade cuando el codigo inicia con letra A-Z seguida de digito; por ejemplo M10, M20 y M30 se colapsan a M.",
            "distribution": "Empleados Employee, Regular, activos y no RF360 en el snapshot 2026-08-23.",
            "promotion_rate": "promotion_yes_no='Yes' dividido entre participantes elegibles del ciclo AR25; track tomado del grade del ciclo.",
            "attrition_rate": "Exits strict VOLUNTARY en (2025-08-24, 2026-08-23] divididos entre el headcount mensual promedio del track en los doce snapshots.",
        },
        "window": {
            "snapshot_date": "2026-08-23",
            "start_exclusive": "2025-08-24",
            "end_inclusive": "2026-08-23",
            "monthly_snapshot_count": 12,
            "annual_review_cycle": "AR25",
            "annual_review_population_snapshot": diagnostics["review_snapshot_date"],
        },
        "totals": {
            "current_employee_count": current_total,
            "promotion_participant_count": promotion_participants,
            "promoted_employee_count": promoted,
            "overall_promotion_rate_percent": overall_promotion_rate,
            "average_monthly_headcount": total_average_headcount,
            "voluntary_event_count": event_count,
            "assigned_voluntary_exit_count": assigned_exit_count,
            "exit_track_assignment_coverage_percent": assignment_coverage,
            "overall_attrition_rate_percent": overall_attrition_rate,
        },
        "privacy": {
            "minimum_shared_cohort": MIN_COHORT,
            "displayed_track_count": len(safe_rows),
            "suppressed_current_track_count": suppressed_current_tracks,
            "suppressed_track_labels_and_counts_persisted": False,
            "visible_distribution_coverage_percent": visible_distribution_coverage,
            "employee_rows_or_identifiers_persisted": False,
        },
        "exit_track_assignment": {
            "minimum_accepted_coverage_percent": MIN_EXIT_ASSIGNMENT_COVERAGE_PERCENT,
            "coverage_percent": assignment_coverage,
            "method": "Ultimo snapshot activo previo dentro de 45 dias; fallback a un unico grade no nulo estable en las filas que registran el evento.",
            "ambiguous_events_are_unassigned": True,
            "unassigned_event_count": unassigned_exit_count,
        },
        "display_rows": safe_rows,
        "diagnostics": diagnostics,
        "outcome": "pass",
    }
    encoded = json.dumps(evidence, ensure_ascii=False).lower()
    for prohibited in ('"employee_id"', '"employee_key"', '"name"', '"email"', '"salary"', '"base_pay"'):
        require(prohibited not in encoded, f"La evidencia contiene el campo prohibido {prohibited}.")
    return evidence


def main() -> None:
    for path in (MAIN_QUERY, FALLBACK_QUERY, ANALYSIS_PLAN, HELPER):
        require(path.exists(), f"No existe el insumo requerido: {path}")
    evidence = build_evidence(run_query(MAIN_QUERY, 100), run_query(FALLBACK_QUERY, 10))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print(
        f"outcome={evidence['outcome']}; displayed_tracks={len(evidence['display_rows'])}; "
        f"assignment_coverage={evidence['exit_track_assignment']['coverage_percent']:.4f}%"
    )


if __name__ == "__main__":
    main()
