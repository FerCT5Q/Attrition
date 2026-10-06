"""Build aggregate-only QVoice wave attrition evidence for slide 20.

The four QVoice raw files are read only in memory to obtain the participant
keys for each wave.  Keys are passed only to the guarded Redshift helper in
ephemeral runtime SQL and are never printed or persisted.  The JSON output
contains aggregate cohort metrics only.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

from build_qvoice_comment_evidence import QVOICE_ROOT, WAVES as COMMENT_WAVES, _iter_selected_rows, _norm_text


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
WINDOW_AUDIT = ROOT / "queries" / "audits" / "qvoice_wave_annual_attrition_window_audit_20260918.sql"
YTD_EVIDENCE = ROOT / "output" / "distribution" / "json" / "qvoice-2026-ytd-attrition-evidence-20260917.json"
OUTPUT = ROOT / "output" / "distribution" / "json" / "qvoice-wave-annual-attrition-evidence-20260918.json"
MINIMUM_COHORT = 30
RUNTIME_BATCH_SIZE = 12_000


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_employee_id(value: object) -> int | None:
    text = _norm_text(value)
    if not text:
        return None
    if re.fullmatch(r"\d+", text):
        return int(text)
    if re.fullmatch(r"\d+\.0+", text):
        return int(float(text))
    return None


def json_query(*, sql: str | None = None, sql_file: Path | None = None, max_rows: int = 100) -> dict[str, Any]:
    require((sql is None) != (sql_file is None), "Specify exactly one SQL source.")
    command = [
        str(PYTHON if PYTHON.exists() else sys.executable),
        str(HELPER),
        "--max-rows",
        str(max_rows),
        "--reporting-mode",
        "internal_analysis",
    ]
    if sql_file is not None:
        command.extend(["--sql-file", str(sql_file)])
    last_error = ""
    for attempt in range(1, 4):
        result = subprocess.run(
            command,
            cwd=ROOT,
            input=sql,
            text=True,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode == 0:
            payload = json.loads(result.stdout)
            if payload.get("truncated"):
                raise ValueError("La consulta agregada se truncó.")
            return payload
        last_error = result.stderr[-1600:] or result.stdout[-1600:]
        if attempt < 3 and ("Connection timed out" in last_error or "connection to server" in last_error):
            time.sleep(3)
            continue
        break
    raise RuntimeError(last_error)


def raw_wave_participants(config: dict[str, object]) -> tuple[set[int], dict[str, int]]:
    """Read one raw wave and return unique numeric keys without persisting them."""
    key_column = str(config["key_column"])
    source_rows = missing_key_rows = invalid_key_rows = duplicate_key_rows = 0
    employee_ids: set[int] = set()
    path = QVOICE_ROOT / str(config["file"])

    for header_map, row in _iter_selected_rows(path, "Raw data", {key_column}):
        source_rows += 1
        raw_value = row.get(header_map[key_column])
        employee_id = parse_employee_id(raw_value)
        if employee_id is None:
            if _norm_text(raw_value):
                invalid_key_rows += 1
            else:
                missing_key_rows += 1
            continue
        if employee_id in employee_ids:
            duplicate_key_rows += 1
        employee_ids.add(employee_id)

    require(employee_ids, f"{config['wave']} no contiene participantes con llave numérica.")
    # Some raw extracts contain non-participant rows without a usable employee
    # key. They cannot enter a time-safe workforce join, so record them as a
    # coverage limitation instead of silently treating them as employees.
    require(duplicate_key_rows == 0, f"{config['wave']} contiene participantes duplicados.")
    return employee_ids, {
        "source_rows": source_rows,
        "distinct_usable_participant_count": len(employee_ids),
        "missing_key_rows": missing_key_rows,
        "invalid_key_rows": invalid_key_rows,
        "unjoinable_source_rows": missing_key_rows + invalid_key_rows,
        "duplicate_key_rows": duplicate_key_rows,
    }


def window_rows() -> dict[str, dict[str, Any]]:
    payload = json_query(sql_file=WINDOW_AUDIT, max_rows=20)
    rows = payload.get("rows")
    require(isinstance(rows, list) and len(rows) == 4, "La auditoría de ventanas QVoice debe devolver cuatro waves.")
    result = {str(row["wave"]): dict(row) for row in rows}
    require(set(result) == {str(config["wave"]) for config in COMMENT_WAVES}, "Las ventanas no coinciden con las cuatro waves QVoice.")
    for wave, row in result.items():
        baseline = int(row["baseline_distinct_employee_count"])
        require(baseline >= MINIMUM_COHORT, f"{wave} no cumple el mínimo de cohorte de workforce.")
        require(int(row["duplicate_baseline_employee_count"]) == 0, f"{wave} tiene duplicados en el snapshot de baseline.")
        require(int(row["followup_complete"]) == 1, f"{wave} no tiene follow-up suficiente para el contrato declarado.")
        if row["outcome_type"] == "annual_12m":
            require(str(row["outcome_start"]) > str(row["baseline_snapshot"]), f"{wave} debe iniciar después del baseline.")
            require(str(row["outcome_end"])[:10] > str(row["outcome_start"]), f"{wave} tiene una ventana anual inválida.")
        else:
            require(wave == "Jan-2026", "Sólo Jan-2026 puede usar el contrato YTD.")
            require(str(row["baseline_snapshot"]) == "2025-12-28", "El baseline YTD 2026 es inesperado.")
            require(str(row["outcome_start"]) == "2026-01-07", "El inicio YTD 2026 es inesperado.")
            require(str(row["outcome_end"])[:10] == "2026-09-27", "El corte YTD 2026 es inesperado.")
    return result


def build_runtime_sql(employee_ids: list[int], baseline_snapshot: str, outcome_start: str, outcome_end: str) -> str:
    """Return ephemeral aggregate-only SQL; its embedded IDs must never be saved."""
    source_json = json.dumps(employee_ids, separators=(",", ":")).replace("'", "''")
    return f"""WITH source AS (
  SELECT elem::BIGINT AS employee_id
  FROM (SELECT JSON_PARSE('{source_json}') AS payload) AS src,
       src.payload AS elem
), baseline AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE '{baseline_snapshot}'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
  GROUP BY 1
), voluntary_events AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND CAST(term_date AS DATE) > DATE '{outcome_start}'
    AND CAST(term_date AS DATE) <= DATE '{outcome_end}'
  GROUP BY 1
)
SELECT
  COUNT(*) AS source_participant_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_employee_count,
  SUM(CASE WHEN b.employee_id IS NULL THEN 1 ELSE 0 END) AS unmatched_employee_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL AND e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count
FROM source AS s
LEFT JOIN baseline AS b
  ON b.employee_id = s.employee_id
LEFT JOIN voluntary_events AS e
  ON e.employee_id = b.employee_id"""


def runtime_attrition(employee_ids: set[int], window: dict[str, Any], wave: str) -> dict[str, int | float]:
    totals = {
        "source_participant_count": 0,
        "matched_employee_count": 0,
        "unmatched_employee_count": 0,
        "voluntary_exit_count": 0,
    }
    ordered_ids = sorted(employee_ids)
    baseline_snapshot = str(window["baseline_snapshot"])
    outcome_start = str(window["outcome_start"])
    outcome_end = str(window["outcome_end"])[:10]
    for start in range(0, len(ordered_ids), RUNTIME_BATCH_SIZE):
        batch = ordered_ids[start : start + RUNTIME_BATCH_SIZE]
        payload = json_query(sql=build_runtime_sql(batch, baseline_snapshot, outcome_start, outcome_end), max_rows=10)
        rows = payload.get("rows")
        require(isinstance(rows, list) and len(rows) == 1, f"{wave} no devolvió un agregado único para una partición.")
        row = rows[0]
        for key in totals:
            totals[key] += int(row.get(key) or 0)
        print(f"  {wave}: participantes {start + 1:,}-{min(start + RUNTIME_BATCH_SIZE, len(ordered_ids)):,}", flush=True)

    require(totals["source_participant_count"] == len(employee_ids), f"{wave} no reconcilia el total de participantes.")
    require(totals["matched_employee_count"] >= MINIMUM_COHORT, f"{wave} no cumple n>=30 tras el join temporal.")
    require(totals["unmatched_employee_count"] == totals["source_participant_count"] - totals["matched_employee_count"], f"{wave} no reconcilia los no matched.")
    require(0 <= totals["voluntary_exit_count"] <= totals["matched_employee_count"], f"{wave} tiene salidas fuera de rango.")
    totals["voluntary_attrition_rate_percent"] = round(
        100.0 * totals["voluntary_exit_count"] / totals["matched_employee_count"], 4
    )
    return totals


def label_for(window: dict[str, Any], rate: float) -> str:
    if window["outcome_type"] == "annual_12m":
        return f"Annual attrition · {rate:.1f}%"
    return f"YTD attrition · {rate:.1f}%"


def reused_jan_2026_ytd() -> tuple[dict[str, int | float], dict[str, int]]:
    """Reuse the already validated exact Jan-07 YTD participant contract."""
    evidence = json.loads(YTD_EVIDENCE.read_text(encoding="utf-8"))
    require(evidence.get("artifact") == "internal_analysis" and evidence.get("outcome") == "pass", "La evidencia YTD 2026 no es válida.")
    contract = evidence.get("outcome_contract", {})
    require(contract.get("survey_launch_date") == "2026-01-07" and contract.get("baseline_snapshot") == "2025-12-28", "El contrato YTD 2026 no coincide.")
    participation = evidence.get("slides", {}).get("22", {})
    responded = participation.get("Responded")
    no_answer = participation.get("QVoice row / no answer")
    require(isinstance(responded, dict) and isinstance(no_answer, dict), "Faltan cohortes de participación YTD 2026.")
    source = int(responded["source_employee_count"]) + int(no_answer["source_employee_count"])
    matched = int(responded["matched_employee_count"]) + int(no_answer["matched_employee_count"])
    exits = int(responded["voluntary_exit_count"]) + int(no_answer["voluntary_exit_count"])
    quality_source = evidence.get("validation", {}).get("participation_source", {})
    require(source == 42_203 and matched >= MINIMUM_COHORT and 0 <= exits <= matched, "La cohorte participante YTD 2026 no reconcilia.")
    return (
        {
            "source_participant_count": source,
            "matched_employee_count": matched,
            "unmatched_employee_count": source - matched,
            "voluntary_exit_count": exits,
            "voluntary_attrition_rate_percent": round(100.0 * exits / matched, 4),
        },
        {
            "source_rows": int(quality_source["raw_rows"]),
            "distinct_usable_participant_count": int(quality_source["raw_distinct_usable_keys"]),
            "missing_key_rows": int(quality_source["raw_missing_key_rows"]),
            "invalid_key_rows": int(quality_source["raw_invalid_key_rows"]),
            "unjoinable_source_rows": int(quality_source["raw_missing_key_rows"]) + int(quality_source["raw_invalid_key_rows"]),
            "duplicate_key_rows": int(quality_source["raw_duplicate_key_rows"]),
        },
    )


def main() -> None:
    require(WINDOW_AUDIT.exists() and YTD_EVIDENCE.exists(), "Falta evidencia de ventanas o YTD de QVoice.")
    windows = window_rows()
    published: list[dict[str, Any]] = []
    raw_quality: dict[str, dict[str, int]] = {}

    for config in COMMENT_WAVES:
        wave = str(config["wave"])
        if wave == "Jan-2026":
            print("Reutilizando la cohorte participante Jan-2026 YTD ya validada…", flush=True)
            metrics, quality = reused_jan_2026_ytd()
        else:
            print(f"Procesando participantes {wave}…", flush=True)
            employee_ids, quality = raw_wave_participants(config)
            metrics = runtime_attrition(employee_ids, windows[wave], wave)
        raw_quality[wave] = quality
        published.append(
            {
                "wave": wave,
                "outcome_type": windows[wave]["outcome_type"],
                "baseline_snapshot": str(windows[wave]["baseline_snapshot"]),
                "outcome_start": str(windows[wave]["outcome_start"]),
                "outcome_end": str(windows[wave]["outcome_end"])[:10],
                "label": label_for(windows[wave], float(metrics["voluntary_attrition_rate_percent"])),
                **metrics,
            }
        )

    historic = [row for row in published if row["outcome_type"] == "annual_12m"]
    ytd = [row for row in published if row["outcome_type"] == "ytd"]
    require(len(historic) == 3 and len(ytd) == 1 and ytd[0]["wave"] == "Jan-2026", "El contrato anual/YTD no es el esperado.")
    evidence = {
        "artifact": "internal_analysis",
        "evidence_type": "aggregate-only QVoice wave participant voluntary attrition",
        "generated_on": date.today().isoformat(),
        "outcome": "pass",
        "minimum_shared_cohort": MINIMUM_COHORT,
        "outcome_contract": {
            "historical": "Annual voluntary attrition: distinct QVoice raw-wave participants who matched to active Regular employees at the latest monthly snapshot before the wave month; strict VOLUNTARY exits in (wave-month start, wave-month start + 12 months].",
            "2026": "Voluntary attrition YTD: the same pre-wave cohort through the latest available snapshot; not annualized.",
            "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 at each pre-wave baseline snapshot.",
            "grain": "Distinct participant in a QVoice raw wave after a time-safe employee-date join.",
        },
        "waves": published,
        "window_audit": [windows[str(config["wave"])] for config in COMMENT_WAVES],
        "validation": {
            "outcome": "pass",
            "raw_wave_key_quality": raw_quality,
            "unjoinable_raw_rows_recorded_not_imputed": True,
            "all_usable_participant_keys_unique": True,
            "all_historical_waves_have_complete_12_month_followup": True,
            "jan_2026_is_ytd_not_annualized": True,
            "all_published_cohorts_n_at_least": MINIMUM_COHORT,
            "runtime_join_sql_persisted": False,
            "reason_runtime_join_sql_not_persisted": "It contains in-memory employee identifiers and returns aggregate counts only.",
        },
        "privacy": {
            "employee_identifiers_persisted": False,
            "employee_rows_persisted": False,
            "raw_comment_text_persisted": False,
            "runtime_join_sql_persisted": False,
        },
        "provenance": {
            "window_audit": str(WINDOW_AUDIT.relative_to(ROOT)).replace("\\", "/"),
            "window_audit_sha256": sha256_path(WINDOW_AUDIT),
            "jan_2026_ytd_evidence": str(YTD_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "jan_2026_ytd_evidence_sha256": sha256_path(YTD_EVIDENCE),
            "raw_workbooks": [str(config["file"]) for config in COMMENT_WAVES],
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "waves": [row["wave"] for row in published], "outcome": "pass"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
