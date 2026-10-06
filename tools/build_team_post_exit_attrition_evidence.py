"""Construye evidencia agregada para la cohorte reciente de salidas secuenciales."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "distribution"
AUDITS = ROOT / "queries" / "audits"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
CALENDAR_SQL = AUDITS / "team_post_exit_attrition_calendar_20260911.sql"
RECONCILIATION_SQL = AUDITS / "team_post_exit_attrition_event_source_reconciliation_20260910.sql"
TEMPLATE_SQL = AUDITS / "team_post_exit_attrition_static_snapshot_20260911.sql"
EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.team-post-exit-attrition-evidence-20260911.json"
GENERATED_SQL = OUT / "team-post-exit-attrition-static-cohort-20260911.sql"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_query(sql_path: Path) -> dict[str, object]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(sql_path),
            "--reporting-mode",
            "presentation",
            "--max-rows",
            "100",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"La consulta no devolvió JSON válido: {completed.stdout[:500]}") from exc
    if payload.get("truncated"):
        raise ValueError(f"La consulta {sql_path.name} superó el máximo de filas.")
    return payload


def metric_map(payload: dict[str, object]) -> dict[str, float]:
    rows = payload["rows"]
    assert isinstance(rows, list)
    return {
        str(row["metric"]): float(row["metric_value"])
        for row in rows
        if isinstance(row, dict) and row.get("metric") is not None
    }


def build_static_sql(cohort: dict[str, object]) -> None:
    values = {
        "2026-03-29": str(cohort["snapshot_date"]),
        "2026-02-22": str(cohort["p1"]),
        "2025-09-28": str(cohort["p6"]),
        "2026-04-26": str(cohort["f1"]),
        "2026-05-24": str(cohort["f2"]),
        "2026-06-28": str(cohort["f3"]),
        "2026-07-26": str(cohort["f4"]),
        "2026-08-23": str(cohort["f5"]),
        "2026-09-27": str(cohort["f6"]),
    }
    sql = TEMPLATE_SQL.read_text(encoding="utf-8")
    for old, new in values.items():
        token = f"DATE '{old}'"
        if token not in sql:
            raise ValueError(f"No se encontró el parámetro esperado {token} en la plantilla.")
        sql = sql.replace(token, f"DATE '{new}'", 1)
    GENERATED_SQL.write_text(sql, encoding="utf-8")


def cumulative_from_hazards(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    ordered = sorted(rows, key=lambda row: int(row["follow_month"]))
    survival = 1.0
    output: list[dict[str, object]] = []
    for row in ordered:
        hazard = float(row["standardized_hazard_percent"])
        survival *= 1.0 - hazard / 100.0
        output.append(
            {
                "follow_month": int(row["follow_month"]),
                "interval_hazard_percent": round(hazard, 6),
                "cumulative_incidence_percent": round(100.0 * (1.0 - survival), 4),
                "initial_roster_n": int(row["initial_roster_n"]),
                "at_risk_n": int(row["at_risk_n"]),
                "voluntary_events_in_interval": int(row["voluntary_events_in_interval"]),
                "censored_in_interval": int(row["censored_in_interval"]),
                "included_size_bands": int(row["included_bands"]),
            }
        )
    return output


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    calendar_payload = run_query(CALENDAR_SQL)
    calendar_rows = calendar_payload["rows"]
    assert isinstance(calendar_rows, list) and calendar_rows
    cohort = calendar_rows[-1]
    assert isinstance(cohort, dict)
    build_static_sql(cohort)
    reconciliation_payload = run_query(RECONCILIATION_SQL)
    series_payload = run_query(GENERATED_SQL)

    reconciliation = metric_map(reconciliation_payload)
    rows = series_payload["rows"]
    assert isinstance(rows, list)
    series_rows = [row for row in rows if isinstance(row, dict) and row.get("row_type") == "series"]
    audits = metric_map(series_payload)
    expected_keys = {
        (scope, group, month)
        for scope in ("all_teams", "teams_6_plus")
        for group in ("exposed", "reference_standardized")
        for month in range(1, 7)
    }
    observed_keys = {
        (str(row["scope"]), str(row["comparison_group"]), int(row["follow_month"]))
        for row in series_rows
    }
    calendar_dates = [date.fromisoformat(str(cohort[key])) for key in ("snapshot_date", "f1", "f2", "f3", "f4", "f5", "f6")]
    calendar_gaps = [(later - earlier).days for earlier, later in zip(calendar_dates, calendar_dates[1:])]
    errors: list[str] = []
    if observed_keys != expected_keys:
        errors.append(f"Se esperaban 24 puntos y se obtuvieron {len(observed_keys)}.")
    if reconciliation.get("voluntary_monthly_match_percent", 0.0) < 99.0:
        errors.append("La concordancia Voluntary mensual quedó por debajo de 99%.")
    if reconciliation.get("all_terminations_repeated_source_rows", -1.0) != 0.0:
        errors.append("all_terminations contiene filas duplicadas de evento.")
    if audits.get("index_team_episodes", 0.0) <= 0.0:
        errors.append("No hay episodios índice elegibles.")
    if audits.get("series_points", 0.0) != 24.0:
        errors.append("La consulta de cohorte no produjo los 24 puntos requeridos.")
    if not all(20 <= gap <= 45 for gap in calendar_gaps):
        errors.append("El seguimiento no tiene seis brechas mensuales válidas.")
    for row in series_rows:
        if int(row["at_risk_n"]) < 30:
            errors.append("Un punto visible tiene n en riesgo menor a 30.")
        hazard = float(row["standardized_hazard_percent"])
        if not 0.0 <= hazard <= 100.0:
            errors.append("Un hazard quedó fuera del rango 0–100.")

    grouped: dict[str, list[dict[str, object]]] = {}
    for row in series_rows:
        key = f"{row['scope']}::{row['comparison_group']}"
        grouped.setdefault(key, []).append(row)
    curves = {key: cumulative_from_hazards(value) for key, value in grouped.items()}
    output = {
        "artifact_classification": "presentation",
        "execution_date": datetime.now().astimezone().isoformat(timespec="seconds"),
        "outcome": "pass" if not errors else "fail",
        "variable": "More than 1 employee leaves in a year",
        "study": {
            "type": "cohorte descriptiva posterior a una salida inicial",
            "interpretation": "Asociación descriptiva; no causalidad, contagio probado, ranking de managers ni predicción individual.",
            "population": "Empleados Employee/Regular activos con manager en el cierre índice.",
            "index_event": "Una salida Voluntary reconciliada única en los seis intervalos cerrados previos; ocurre en el último intervalo antes de t.",
            "reference": "Equipos sin salida Voluntary reconciliada reciente, mismo cierre y banda de tamaño; estandarizados con la distribución expuesta.",
            "follow_up": "Seis cierres mensuales; se censura cambio de manager, salida no Voluntary o pérdida de observación.",
            "estimand": "Incidencia acumulada Kaplan–Meier a partir de hazards mensuales estandarizados.",
        },
        "cohort": {
            "index_snapshot": cohort["snapshot_date"],
            "lookback_start_exclusive": cohort["p6"],
            "index_interval_start_exclusive": cohort["p1"],
            "follow_up_end": cohort["f6"],
            "follow_up_snapshot_dates": [str(cohort[key]) for key in ("f1", "f2", "f3", "f4", "f5", "f6")],
            "follow_up_gaps_days": calendar_gaps,
        },
        "reconciliation_metrics": reconciliation,
        "query_audits": audits,
        "curves": curves,
        "validation": {
            "acceptance_rule": "24 puntos, n en riesgo >=30, hazards 0–100, seis cierres completos, episodio índice positivo y concordancia Voluntary >=99%.",
            "errors": errors,
        },
        "limitation": "La evidencia corresponde a la cohorte reciente completa; no estima estabilidad histórica y debe repetirse al haber un nuevo sexto cierre.",
        "provenance": {
            "calendar_sql": str(CALENDAR_SQL.relative_to(ROOT)).replace("\\", "/"),
            "reconciliation_sql": str(RECONCILIATION_SQL.relative_to(ROOT)).replace("\\", "/"),
            "static_template_sql": str(TEMPLATE_SQL.relative_to(ROOT)).replace("\\", "/"),
            "executed_static_sql": str(GENERATED_SQL.relative_to(ROOT)).replace("\\", "/"),
            "calendar_sql_sha256": sha256(CALENDAR_SQL),
            "reconciliation_sql_sha256": sha256(RECONCILIATION_SQL),
            "static_template_sql_sha256": sha256(TEMPLATE_SQL),
            "executed_static_sql_sha256": sha256(GENERATED_SQL),
            "calendar_result_sha256": hashlib.sha256(json.dumps(calendar_payload, sort_keys=True).encode()).hexdigest(),
            "reconciliation_result_sha256": hashlib.sha256(json.dumps(reconciliation_payload, sort_keys=True).encode()).hexdigest(),
            "static_result_sha256": hashlib.sha256(json.dumps(series_payload, sort_keys=True).encode()).hexdigest(),
        },
    }
    EVIDENCE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    if errors:
        raise SystemExit("Evidencia no publicable: " + " | ".join(errors))
    print(EVIDENCE)


if __name__ == "__main__":
    main()
