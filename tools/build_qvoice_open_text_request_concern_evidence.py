"""Build aggregate-only QVoice evidence for remote/hybrid and onsite-policy comments.

The raw QVoice workbooks are streamed in memory. Participant identifiers and
comment text are used only while this process runs. The persisted JSON contains
aggregate counts, shares, validation diagnostics, and aggregate attrition only.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from openpyxl import load_workbook

from build_qvoice_comment_evidence import (
    QVOICE_ROOT,
    WAVES,
    _find_column,
    _iter_selected_rows,
    _norm_header,
    _norm_text,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
WINDOW_AUDIT = ROOT / "queries" / "audits" / "qvoice_open_text_request_concern_attrition_window_audit_20260918.sql"
RUNTIME_SQL_TEMPLATE = ROOT / "queries" / "audits" / "qvoice_open_text_no_comment_attrition_runtime_template_20260921.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "qvoice-open-text-request-concern-evidence-20260922.json"
MINIMUM_COHORT = 30
RUNTIME_BATCH_SIZE = 12_000


# A request needs both a remote/hybrid topic and an explicit ask, preference,
# or flexibility action in the same sentence-like clause. This avoids treating
# a simple positive/neutral mention as a request.
REMOTE_OR_HYBRID_TARGETS = (
    "remote work", "remote-working", "working remotely", "work remotely",
    "work from home", "working from home", "wfh", "telework", "telecommute",
    "trabajo remoto", "trabajo a distancia", "trabajar desde casa",
    "trabajo desde casa", "teletrabajo", "modalidad remota", "modalidad remoto",
    "hybrid work", "hybrid-working", "hybrid", "trabajo híbrido", "trabajo hibrido",
    "modelo híbrido", "modelo hibrido", "esquema híbrido", "esquema hibrido",
    "modalidad híbrida", "modalidad hibrida", "híbrido", "hibrido",
)
REQUEST_ACTIONS = (
    "more", "increase", "allow", "allowing", "offer", "provide", "keep", "continue",
    "maintain", "flexibility", "flexible", "option", "options", "prefer", "preference",
    "would like", "wish", "request", "need", "want", "support", "enable", "permit",
    "return to", "back to", "less restrictive", "expand", "extend", "preserve",
    "más", "mas", "aumentar", "permitir", "ofrecer", "mantener", "continuar",
    "flexibilidad", "flexible", "opción", "opcion", "preferir", "quisiera", "solicito",
    "necesito", "quiero", "apoyar", "habilitar", "conservar", "ampliar", "extender",
)

# An onsite concern needs an office/onsite topic plus a policy, enforcement,
# requirement, exception, flexibility, or commute burden in the same clause.
# "home office" is stripped before testing this family of patterns.
ONSITE_TARGETS = (
    "rto", "return to office", "return to the office", "return back to office",
    "back to office", "go back to office", "in office", "in-office", "in the office",
    "onsite", "on-site", "office days", "days in office", "office attendance",
    "presencial", "trabajo presencial", "volver a la oficina", "regreso a la oficina",
    "regresar a la oficina", "ir a la oficina", "días de oficina", "dias de oficina",
    "asistir a la oficina", "presencialidad",
)
ONSITE_CONCERN_ACTIONS = (
    "mandatory", "mandated", "require", "required", "requirement", "must", "forced", "force",
    "policy", "policies", "enforce", "enforcement", "compliance", "comply", "exception",
    "exceptions", "waiver", "waivers", "flexibility", "flexible", "inflexible", "not flexible",
    "days per week", "day per week", "reduce", "less", "fewer", "avoid", "stop", "remove",
    "eliminate", "burden", "difficult", "difficulty", "problem", "issue", "challenge",
    "commute", "commuting", "parking", "traffic", "travel time", "travel", "drive", "driving",
    "cost", "expense", "childcare", "work life balance", "work-life balance",
    "obligatorio", "obligatoria", "requerido", "requerida", "requisito", "debe", "forzado",
    "forzada", "política", "politica", "cumplimiento", "cumplir", "excepción", "excepcion",
    "excepciones", "flexibilidad", "flexible", "inflexible", "días por semana", "dias por semana",
    "reducir", "menos", "evitar", "eliminar", "carga", "difícil", "dificil", "problema",
    "traslado", "estacionamiento", "tráfico", "trafico", "tiempo de viaje", "costo", "coste",
)

SUBTHEMES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "remote_hybrid_flexibility_request",
        "Request for remote or hybrid flexibility",
        REQUEST_ACTIONS,
    ),
    (
        "required_onsite_days",
        "Required days in the office",
        (
            "mandatory", "mandated", "require", "required", "requirement", "must", "forced",
            "days per week", "day per week", "obligatorio", "obligatoria", "requerido", "requerida",
            "requisito", "debe", "forzado", "forzada", "días por semana", "dias por semana",
        ),
    ),
    (
        "policy_enforcement_compliance_exceptions",
        "Policy enforcement, compliance, or exceptions",
        (
            "policy", "policies", "enforce", "enforcement", "compliance", "comply", "exception",
            "exceptions", "waiver", "waivers", "política", "politica", "cumplimiento", "cumplir",
            "excepción", "excepcion", "excepciones",
        ),
    ),
    (
        "commute_parking_travel_time",
        "Commute, parking, or travel time",
        (
            "commute", "commuting", "parking", "traffic", "travel time", "travel", "drive", "driving",
            "traslado", "estacionamiento", "tráfico", "trafico", "tiempo de viaje",
        ),
    ),
    (
        "office_space_or_facilities",
        "Office space or facilities",
        (
            "office space", "workspace", "work space", "desk", "desks", "seating", "seat",
            "facility", "facilities", "cafeteria", "temperature", "restroom", "office building",
            "espacio de oficina", "espacio de trabajo", "escritorio", "asiento", "instalaciones",
            "cafetería", "cafeteria", "temperatura", "baño", "bano", "edificio",
        ),
    ),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_employee_id(value: object) -> int | None:
    normalized = _norm_text(value)
    if not normalized:
        return None
    if re.fullmatch(r"\d+", normalized):
        return int(normalized)
    if re.fullmatch(r"\d+\.0+", normalized):
        return int(float(normalized))
    return None


def has_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(r"(?<!\w)" + re.escape(pattern.casefold()) + r"(?!\w)", text) for pattern in patterns)


def clauses(text: str) -> list[str]:
    return [clause.strip() for clause in re.split(r"[.!?;\n]+", text) if clause.strip()]


def onsite_text(clause: str) -> str:
    return re.sub(r"(?<!\w)home\s+office(?!\w)", " ", clause)


def is_remote_hybrid_request(text: str) -> bool:
    return any(
        has_any(clause, REMOTE_OR_HYBRID_TARGETS) and has_any(clause, REQUEST_ACTIONS)
        for clause in clauses(text)
    )


def is_onsite_policy_concern(text: str) -> bool:
    return any(
        has_any(onsite_text(clause), ONSITE_TARGETS) and has_any(onsite_text(clause), ONSITE_CONCERN_ACTIONS)
        for clause in clauses(text)
    )


def is_onsite_subtheme(text: str, patterns: Iterable[str]) -> bool:
    return any(
        has_any(onsite_text(clause), ONSITE_TARGETS) and has_any(onsite_text(clause), patterns)
        for clause in clauses(text)
    )


def headers_for(path: Path) -> list[str]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        worksheet = workbook["Raw data"]
        return [_norm_header(value) for value in next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True))]
    finally:
        workbook.close()


def selected_columns(config: dict[str, object], headers: list[str]) -> tuple[str, dict[str, str]]:
    key_column = _find_column(headers, [str(config["key_column"])])
    require(key_column is not None, f"No se encontró la llave de {config['wave']}.")
    prompt_columns: dict[str, str] = {}
    for role, candidates in dict(config["prompt_candidates"]).items():
        if not candidates:
            continue
        column = _find_column(headers, list(candidates))
        require(column is not None, f"No se encontró el prompt {role} de {config['wave']}.")
        prompt_columns[role] = column
    expected_roles = {"doing_well", "can_improve"}
    if str(config["wave"]) in {"Jan-2025", "Jan-2026"}:
        expected_roles.add("processes_to_improve")
    require(set(prompt_columns) == expected_roles, f"Los prompts seleccionados de {config['wave']} no coinciden con el contrato.")
    return key_column, prompt_columns


def scan_wave(config: dict[str, object]) -> tuple[dict[str, set[int]], set[int], dict[str, Any]]:
    path = QVOICE_ROOT / str(config["file"])
    key_column, prompt_columns = selected_columns(config, headers_for(path))
    required_columns = {key_column, *prompt_columns.values()}
    all_keys: Counter[int] = Counter()
    commenter_keys: set[int] = set()
    request_or_concern: set[int] = set()
    subtheme_keys: dict[str, set[int]] = {key: set() for key, _, _ in SUBTHEMES}
    source_rows = 0
    comments_without_usable_key = 0
    invalid_key_rows = 0
    nonempty_by_prompt: Counter[str] = Counter()

    for header_map, row in _iter_selected_rows(path, "Raw data", required_columns):
        source_rows += 1
        employee_id = parse_employee_id(row.get(header_map[key_column]))
        raw_key = _norm_text(row.get(header_map[key_column]))
        if raw_key and employee_id is None:
            invalid_key_rows += 1
        if employee_id is not None:
            all_keys[employee_id] += 1

        comments = {
            role: _norm_text(row.get(header_map[column]))
            for role, column in prompt_columns.items()
        }
        nonempty_roles = [role for role, value in comments.items() if value]
        if not nonempty_roles:
            continue
        for role in nonempty_roles:
            nonempty_by_prompt[role] += 1
        if employee_id is None:
            comments_without_usable_key += 1
            continue

        commenter_keys.add(employee_id)
        text = ". ".join(comments[role] for role in nonempty_roles)
        remote_request = is_remote_hybrid_request(text)
        onsite_concern = is_onsite_policy_concern(text)
        if remote_request or onsite_concern:
            request_or_concern.add(employee_id)
        if remote_request:
            subtheme_keys["remote_hybrid_flexibility_request"].add(employee_id)
        for key, _, patterns in SUBTHEMES[1:]:
            if is_onsite_subtheme(text, patterns):
                subtheme_keys[key].add(employee_id)

    duplicate_participant_keys = sum(1 for count in all_keys.values() if count > 1)
    duplicate_participant_rows = sum(count - 1 for count in all_keys.values() if count > 1)
    require(comments_without_usable_key == 0, f"{config['wave']} contiene comentarios sin llave usable.")
    require(duplicate_participant_rows == 0, f"{config['wave']} contiene llaves de participantes duplicadas.")
    require(commenter_keys, f"{config['wave']} no contiene comentarios abiertos con llave usable.")

    other_commenters = commenter_keys - request_or_concern
    no_comment_keys = set(all_keys) - commenter_keys
    require(request_or_concern.isdisjoint(other_commenters), f"Los grupos de {config['wave']} se traslapan.")
    require(request_or_concern | other_commenters == commenter_keys, f"Los grupos de {config['wave']} no reconcilian.")
    require(no_comment_keys.isdisjoint(commenter_keys), f"Los no-comentaristas de {config['wave']} se traslapan con comentaristas.")
    require(len(no_comment_keys) + len(commenter_keys) == len(all_keys), f"{config['wave']} no reconcilia participantes con y sin comentario.")
    require(len(request_or_concern) >= MINIMUM_COHORT, f"El grupo request/concern de {config['wave']} es menor que n=30.")
    require(len(other_commenters) >= MINIMUM_COHORT, f"El grupo all-other de {config['wave']} es menor que n=30.")
    require(len(no_comment_keys) >= MINIMUM_COHORT, f"El grupo no-comment de {config['wave']} es menor que n=30.")

    groups = {
        "requested_remote_hybrid_or_raised_onsite_policy_concern": request_or_concern,
        "all_other_open_text_commenters": other_commenters,
    }
    subtheme_counts = {key: len(values) for key, values in subtheme_keys.items()}
    quality = {
        "wave": str(config["wave"]),
        "source_file": str(config["file"]),
        "source_rows": source_rows,
        "selected_open_text_prompt_roles": list(prompt_columns),
        "selected_open_text_prompt_count": len(prompt_columns),
        "nonempty_rows_by_prompt": dict(nonempty_by_prompt),
        "commenter_count": len(commenter_keys),
        "distinct_usable_participant_keys": len(all_keys),
        "no_comment_participant_count": len(no_comment_keys),
        "invalid_key_rows": invalid_key_rows,
        "comments_without_usable_key": comments_without_usable_key,
        "duplicate_participant_keys": duplicate_participant_keys,
        "duplicate_participant_rows": duplicate_participant_rows,
        "group_counts": {key: len(values) for key, values in groups.items()},
        "subtheme_counts": subtheme_counts,
        "groups_reconcile_to_all_commenters": True,
        "participants_reconcile_to_commenters_and_no_comment": True,
    }
    return groups, no_comment_keys, quality


def json_query(*, sql: str | None = None, sql_file: Path | None = None, max_rows: int = 100) -> dict[str, Any]:
    require((sql is None) != (sql_file is None), "Specify exactly one SQL source.")
    command = [
        str(PYTHON if PYTHON.exists() else sys.executable),
        str(HELPER),
        "--max-rows", str(max_rows),
        "--reporting-mode", "internal_analysis",
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
            require(not payload.get("truncated"), "La consulta agregada se truncó.")
            return payload
        last_error = result.stderr[-1600:] or result.stdout[-1600:]
        if attempt < 3 and ("Connection timed out" in last_error or "connection to server" in last_error):
            time.sleep(3)
            continue
        break
    raise RuntimeError(last_error)


def windows() -> dict[str, dict[str, Any]]:
    payload = json_query(sql_file=WINDOW_AUDIT, max_rows=20)
    rows = payload.get("rows")
    require(isinstance(rows, list) and len(rows) == 4, "La auditoría de ventanas debe devolver cuatro waves.")
    expected_waves = {str(config["wave"]) for config in WAVES}
    result = {str(row["wave"]): dict(row) for row in rows}
    require(set(result) == expected_waves, "Las waves de la auditoría no coinciden con QVoice.")
    for wave, row in result.items():
        require(int(row["baseline_distinct_employee_count"]) >= MINIMUM_COHORT, f"{wave} no cumple n>=30 en baseline.")
        require(int(row["duplicate_baseline_employee_count"]) == 0, f"{wave} tiene duplicados en baseline.")
        require(int(row["followup_or_cutoff_available"]) == 1, f"{wave} no tiene la ventana requerida.")
        if wave == "Jan-2026":
            require(str(row["outcome_type"]) == "ytd_partial", "Jan-2026 debe ser YTD parcial.")
            require(str(row["baseline_snapshot"]) == "2025-12-28", "El baseline Jan-2026 es inesperado.")
            require(str(row["outcome_start"]) == "2026-01-07", "El lanzamiento Jan-2026 es inesperado.")
            require(str(row["outcome_end"])[:10] == "2026-08-23", "El corte Jan-2026 debe ser 23 Aug 2026.")
            require(int(row["august_snapshot_exists"]) == 1, "No existe el snapshot de agosto requerido.")
        else:
            require(str(row["outcome_type"]) == "annual_12m", f"{wave} debe usar 12 meses.")
    return result


def runtime_sql(records: list[dict[str, int]], window: dict[str, Any]) -> str:
    source_json = json.dumps(records, separators=(",", ":")).replace("'", "''")
    return f"""WITH source AS (
  SELECT
    elem.employee_id::BIGINT AS employee_id,
    elem.group_code::INTEGER AS group_code
  FROM (SELECT JSON_PARSE('{source_json}') AS payload) AS src,
       src.payload AS elem
), baseline AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE '{str(window['baseline_snapshot'])[:10]}'
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
    AND CAST(term_date AS DATE) > DATE '{str(window['outcome_start'])[:10]}'
    AND CAST(term_date AS DATE) <= DATE '{str(window['outcome_end'])[:10]}'
  GROUP BY 1
)
SELECT
  s.group_code,
  COUNT(*) AS source_participant_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_employee_count,
  SUM(CASE WHEN b.employee_id IS NULL THEN 1 ELSE 0 END) AS unmatched_employee_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL AND e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count
FROM source AS s
LEFT JOIN baseline AS b
  ON b.employee_id = s.employee_id
LEFT JOIN voluntary_events AS e
  ON e.employee_id = b.employee_id
GROUP BY 1
ORDER BY 1"""


def group_attrition(groups: dict[str, set[int]], window: dict[str, Any], wave: str) -> dict[str, dict[str, int | float]]:
    labels = list(groups)
    totals = {
        code: {
            "source_participant_count": 0,
            "matched_employee_count": 0,
            "unmatched_employee_count": 0,
            "voluntary_exit_count": 0,
        }
        for code in range(len(labels))
    }
    records = [
        {"employee_id": employee_id, "group_code": code}
        for code, label in enumerate(labels)
        for employee_id in sorted(groups[label])
    ]
    for start in range(0, len(records), RUNTIME_BATCH_SIZE):
        payload = json_query(sql=runtime_sql(records[start:start + RUNTIME_BATCH_SIZE], window), max_rows=10)
        rows = payload.get("rows")
        require(isinstance(rows, list), f"{wave} no devolvió agregados de attrition.")
        for row in rows:
            code = int(row["group_code"])
            for metric in totals[code]:
                totals[code][metric] += int(row.get(metric) or 0)

    result: dict[str, dict[str, int | float]] = {}
    for code, label in enumerate(labels):
        metric = totals[code]
        source = int(metric["source_participant_count"])
        matched = int(metric["matched_employee_count"])
        exits = int(metric["voluntary_exit_count"])
        require(source == len(groups[label]), f"{wave}:{label} no reconcilia a la fuente QVoice.")
        require(matched >= MINIMUM_COHORT and 0 <= exits <= matched, f"{wave}:{label} no es publicable.")
        require(int(metric["unmatched_employee_count"]) == source - matched, f"{wave}:{label} no reconcilia el join temporal.")
        result[label] = {
            **metric,
            "voluntary_attrition_rate_percent": round(100.0 * exits / matched, 4),
        }
    return result


def label_for(window: dict[str, Any]) -> str:
    if str(window["outcome_type"]) == "annual_12m":
        return "12-month voluntary attrition after the survey"
    return "YTD voluntary attrition through Aug 2026 (partial year)"


def main() -> None:
    require(RUNTIME_SQL_TEMPLATE.exists(), "Falta la plantilla SQL del join QVoice de attrition.")
    require(WINDOW_AUDIT.exists(), "Falta la auditoría de ventanas QVoice.")
    print("Validando ventanas agregadas de atrición…", flush=True)
    window_by_wave = windows()
    wave_rows: list[dict[str, Any]] = []
    latest_subthemes: list[dict[str, Any]] = []

    for config in WAVES:
        wave = str(config["wave"])
        print(f"Procesando comentarios {wave}…", flush=True)
        groups, no_comment_keys, quality = scan_wave(config)
        print(f"Calculando atrición agregada {wave}…", flush=True)
        attrition = group_attrition(groups, window_by_wave[wave], wave)
        no_comment_attrition = group_attrition(
            {"no_open_text_comment": no_comment_keys},
            window_by_wave[wave],
            wave,
        )["no_open_text_comment"]
        commenter_count = int(quality["commenter_count"])
        group_counts = quality["group_counts"]
        group_rows = []
        for group_key in groups:
            count = int(group_counts[group_key])
            rates = attrition[group_key]
            group_rows.append({
                "group": group_key,
                "commenter_count": count,
                "share_of_open_text_commenters_percent": round(100.0 * count / commenter_count, 4),
                "source_commenter_count": int(rates["source_participant_count"]),
                **{key: value for key, value in rates.items() if key != "source_participant_count"},
            })
        require(sum(int(row["commenter_count"]) for row in group_rows) == commenter_count, f"{wave} no reconcilia grupos.")
        require(abs(sum(float(row["share_of_open_text_commenters_percent"]) for row in group_rows) - 100.0) < 0.001, f"{wave} no reconcilia porcentajes.")
        no_comment_row = {
            "group": "no_open_text_comment",
            "label": "No comment submitted",
            "participant_count": len(no_comment_keys),
            **no_comment_attrition,
        }
        survey_participant_count = int(quality["distinct_usable_participant_keys"])
        composition_groups = [
            {
                "group": str(row["group"]),
                "participant_count": int(row["commenter_count"]),
                "share_of_survey_participants_percent": round(
                    100.0 * int(row["commenter_count"]) / survey_participant_count,
                    4,
                ),
            }
            for row in group_rows
        ] + [
            {
                "group": "no_open_text_comment",
                "participant_count": int(no_comment_row["participant_count"]),
                "share_of_survey_participants_percent": round(
                    100.0 * int(no_comment_row["participant_count"]) / survey_participant_count,
                    4,
                ),
            }
        ]
        require(
            sum(int(row["participant_count"]) for row in composition_groups) == survey_participant_count,
            f"{wave} no reconcilia los tres grupos de participaci\u00f3n.",
        )
        require(
            abs(sum(float(row["share_of_survey_participants_percent"]) for row in composition_groups) - 100.0) < 0.001,
            f"{wave} no reconcilia la composici\u00f3n a 100%.",
        )

        if wave == "Jan-2026":
            request_concern_count = int(group_counts["requested_remote_hybrid_or_raised_onsite_policy_concern"])
            for key, label, _ in SUBTHEMES:
                count = int(quality["subtheme_counts"][key])
                if count >= MINIMUM_COHORT:
                    latest_subthemes.append({
                        "subtheme": key,
                        "label": label,
                        "commenter_count": count,
                        "share_of_request_or_concern_group_percent": round(100.0 * count / request_concern_count, 4),
                    })

        wave_rows.append({
            "wave": wave,
            "survey_label": "2025 QVoice survey (fielded Jan 2026)" if wave == "Jan-2026" else wave,
            "survey_participant_count": survey_participant_count,
            "open_text_commenter_count": commenter_count,
            "groups": group_rows,
            "no_comment": no_comment_row,
            "composition": {
                "denominator": "Distinct QVoice participants with a usable key in the Raw data worksheet for the wave.",
                "groups": composition_groups,
                "groups_are_mutually_exclusive_and_exhaustive": True,
            },
            "attrition_window": {
                "baseline_snapshot": str(window_by_wave[wave]["baseline_snapshot"])[:10],
                "outcome_start": str(window_by_wave[wave]["outcome_start"])[:10],
                "outcome_end": str(window_by_wave[wave]["outcome_end"])[:10],
                "outcome_type": str(window_by_wave[wave]["outcome_type"]),
                "label": label_for(window_by_wave[wave]),
            },
            "source_quality": quality,
        })

    latest_subthemes.sort(key=lambda row: (-int(row["commenter_count"]), str(row["label"])))
    require(len(latest_subthemes) >= 3, "No hay suficientes subtemas publicables para el resumen Jan-2026.")
    latest_subthemes = latest_subthemes[:5]
    require(all(int(row["commenter_count"]) >= MINIMUM_COHORT for row in latest_subthemes), "Un subtema visible es menor que n=30.")

    evidence = {
        "artifact": "internal_analysis",
        "evidence_type": "aggregate-only QVoice open-text remote/hybrid requests and onsite-policy concerns",
        "generated_on": date.today().isoformat(),
        "outcome": "pass",
        "minimum_shared_cohort": MINIMUM_COHORT,
        "population": "QVoice survey participants with a usable key in the Raw data worksheet; comment groups are participant-wave cases and no-comment is the complementary participant group with no selected open-text response.",
        "classification_rule": {
            "requested_remote_hybrid_or_raised_onsite_policy_concern": "A participant has either (a) a remote/hybrid topic plus an explicit request, preference, or flexibility action in the same sentence-like clause, or (b) an office/onsite topic plus a policy, enforcement, requirement, exception, flexibility, or commute burden in the same clause.",
            "all_other_open_text_commenters": "Every other participant with at least one selected open-text comment, including neutral/positive topic mentions and people who did not mention the topic.",
            "compliance_boundary": "Compliance qualifies only where it appears in the same office/onsite clause; generic compliance is excluded.",
            "home_office_boundary": "The phrase home office is treated as a remote-work phrase and is excluded from the office/onsite detector.",
        },
        "subtheme_rule": "Jan-2026 subthemes are non-exclusive. Each requires its topic and qualifier in the same sentence-like clause; only n >= 30 subthemes are rendered.",
        "outcome_contract": {
            "historical": "For Mar-2023, Jan-2024, and Jan-2025, strict VOLUNTARY termination in the 12 months after the survey wave began.",
            "jan_2026": "For the 2025 QVoice survey fielded Jan 2026, strict VOLUNTARY termination from 07 Jan 2026 through the 23 Aug 2026 snapshot. This is YTD partial-year and is not annualized.",
            "population": "worker_type='Employee'; employee_type='Regular'; active_status=1 at the wave-specific pre-survey baseline snapshot.",
            "grain": "Distinct survey participant in each QVoice wave and displayed group after a time-safe employee-date join; no-comment excludes participants with any selected open-text response.",
        },
        "waves": wave_rows,
        "latest_survey_subthemes": latest_subthemes,
        "validation": {
            "outcome": "pass",
            "all_selected_prompts_present": True,
            "prompt_contract": {
                "Mar-2023": ["doing_well", "can_improve"],
                "Jan-2024": ["doing_well", "can_improve"],
                "Jan-2025": ["doing_well", "can_improve", "processes_to_improve"],
                "Jan-2026": ["doing_well", "can_improve", "processes_to_improve"],
            },
            "all_visible_groups_reconcile_to_open_text_commenters": True,
            "all_visible_no_comment_cohorts_reconcile_to_survey_participants": True,
            "all_three_group_compositions_reconcile_to_survey_participants": True,
            "all_visible_group_and_subtheme_cohorts_n_at_least": MINIMUM_COHORT,
            "all_attrition_rates_reconcile_to_exits_and_matched_cohort": True,
            "historical_followup_is_12_months": True,
            "jan_2026_cutoff": "2026-08-23",
            "jan_2026_ytd_is_partial_and_not_annualized": True,
            "runtime_join_sql_persisted": False,
            "runtime_join_sql_template_persisted": True,
        },
        "privacy": {
            "employee_identifiers_persisted": False,
            "employee_rows_persisted": False,
            "raw_comment_text_persisted": False,
            "runtime_join_sql_persisted": False,
            "runtime_join_sql_template_persisted": True,
        },
        "provenance": {
            "window_audit": str(WINDOW_AUDIT.relative_to(ROOT)).replace("\\", "/"),
            "window_audit_sha256": sha256_path(WINDOW_AUDIT),
            "runtime_join_sql_template": str(RUNTIME_SQL_TEMPLATE.relative_to(ROOT)).replace("\\", "/"),
            "runtime_join_sql_template_sha256": sha256_path(RUNTIME_SQL_TEMPLATE),
            "raw_workbooks": [str(config["file"]) for config in WAVES],
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "waves": [row["wave"] for row in wave_rows], "outcome": "pass"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
