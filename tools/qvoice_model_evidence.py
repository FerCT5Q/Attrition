"""Evidencia actual por concepto de QVoice, con revisión entre variables."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from qvoice_model_data import (
    ROOT, DEFAULT_CONFIG, BANDS, WaveRows, availability_date, cell_value, component_result,
    components_for, favorable_band, load_config, primary_components, scan_wave, sha256_file, utc_now, write_json,
)
from qvoice_model_assessment import AUDIT_COLUMNS, assess_one, execute_local_audit, plan_path, audit_query_path
from qvoice_model_reconcile import reconcile_wave

JOIN_QUERY = ROOT / "queries/audits/qvoice_model_engineering_join_20261006.sql"
HEARTBEAT_RETROSPECTIVE_QUERY = ROOT / "queries/audits/qvoice_model_heartbeat_retrospective_join_20261006.sql"
STATUS_LABELS = {"valid": "Válida", "missing": "Sin respuesta", "sentinel_255": "Sin respuesta (255)", "question_absent": "Pregunta ausente", "invalid": "Inválida", "no_linked_row": "Sin registro enlazable", "duplicate": "Llave duplicada"}


def log(message: str) -> None:
    print(message, flush=True)


def compact_signature(candidate: dict, values: dict) -> dict:
    keys = components_for(candidate)
    heartbeat = candidate["id"] == "heartbeat"
    results = {key: component_result(values, key, heartbeat=heartbeat) for key in keys}
    primary = primary_components(candidate)
    valid_primary = [results[k][1] == "valid" for k in primary]
    full_complete = all(status == "valid" for _, status in results.values())
    result = {"primary_available": any(valid_primary), "primary_complete": all(valid_primary), "full_complete": full_complete,
              "states": {key: f"v{value}" if status == "valid" else status for key, (value, status) in results.items()},
              "comparable": 0, "mismatch": 0, "overlap_cohort_difference": 0,
              "alternate_comparable": 0, "alternate_disagreement": 0, "favorable_sum": 0}
    for key in keys:
        alternate = values.get(f"alternate_{key}_0")
        if alternate and values.get(key, (None, None))[1] == alternate[1] == "valid":
            result["alternate_comparable"] += 1
            result["alternate_disagreement"] += int(values[key][0] != alternate[0])
    if candidate["id"] == "mean33":
        numbers = [results[k][0] for k in keys]
        band = favorable_band(numbers, required_count=33)
        result["primary_available"] = band is not None
        result["states"] = {"mean33": band if band is not None else "missing"}
        if band is not None:
            result["favorable_sum"] = sum(numbers)
            score = float(np.mean(np.asarray(numbers, dtype=float))) * 100
            independent_band = BANDS[int(np.searchsorted([50, 70, 80, 90, 100], score, side="right"))]
            result["comparable"] = 1
            result["mismatch"] = int(independent_band != band)
            # La cohorte es siempre la original de 33, incluso si los 31 restantes son válidos.
            without_intent = [value for key, value in zip(keys, numbers) if key not in ("M14", "M16")]
            result["overlap_cohort_difference"] = int(len(without_intent) != 31 or favorable_band(without_intent, required_count=31) is None)
    elif candidate["id"] == "intent" and full_complete:
        q4, q12 = results["Q4"][0], results["Q12"][0]
        result["states"]["intent_both"] = f"v{int(q4 == 1 and q12 == 1)}"
        result["comparable"] = 1
        result["mismatch"] = int(int(q4 == 1 and q12 == 1) != q4 * q12)
    elif heartbeat:
        scale = [values.get(f"scale_Q{i}", (None, "question_absent"))[0] for i in range(1, 54)]
        valid = [v for v in scale if v in (1, 2, 3, 4, 5)]
        for key, (sign, status) in results.items():
            if status != "valid":
                continue
            item = values[f"scale_{key}"][0]
            difference = item - float(np.mean(valid))
            independent = 0 if math.isclose(difference, 0, abs_tol=1e-12) else 1 if difference > 0 else -1
            result["comparable"] += 1
            result["mismatch"] += int(sign != independent)
    return result


def group_wave(candidate: dict, wave: WaveRows) -> tuple[list[dict], dict[int, dict], dict]:
    groups: dict[str, int] = {}
    signatures: dict[int, dict] = {}
    records = []
    counts = Counter()
    heartbeat = candidate["id"] == "heartbeat"
    keys = [f"Q{i}" for i in range(1, 54)] if heartbeat else components_for(candidate)
    for employee_key, values in wave.rows.items():
        for key in keys:
            # El dominio de Heartbeat incluye las 53 entradas de su promedio,
            # aunque sólo se publiquen los signos de seis preguntas.
            _, status = values.get(f"scale_{key}", (None, "question_absent")) if heartbeat else component_result(values, key)
            counts[status] += 1
        signature = compact_signature(candidate, values)
        canonical = json.dumps(signature, sort_keys=True, ensure_ascii=True)
        if canonical not in groups:
            code = len(groups)
            groups[canonical] = code
            signatures[code] = signature
        records.append({"k": employee_key, "g": groups[canonical]})
    counts["status_reconciliation_difference"] = abs(sum(counts.values()) - len(wave.rows) * len(keys))
    return records, signatures, dict(counts)


def query_join(records: list[dict], wave: dict, config: dict, *, query_path: Path = JOIN_QUERY) -> tuple[list[dict], list[dict]]:
    """Las llaves sólo viajan al join autorizado; el cursor devuelve agregados."""
    sys.path.insert(0, str(ROOT / ".codex/skills/attrition-redshift-db/scripts"))
    import run_readonly_query as helper
    year = wave["year"]
    template = query_path.read_text(encoding="utf-8")
    totals = {}
    ledger = []
    with helper.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
        for offset in range(0, len(records), 10000):
            batch = records[offset:offset + 10000]
            sql = template.replace("__SOURCE_JSON__", json.dumps(batch, separators=(",", ":")))
            substitutions = {
                "__BASELINE_BEFORE__": f"{year}-01-01", "__KNOWLEDGE_BOUNDARY__": config["knowledge_boundary"],
                "__OUTCOME_START__": wave["descriptive_anchor"], "__OUTCOME_END__": f"{year + 1}-01-01" if year < 2026 else config["knowledge_boundary"],
            }
            for placeholder, value in substitutions.items():
                sql = sql.replace(placeholder, value)
            sql = helper.validate_readonly(sql)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    columns = [c[0] for c in cursor.description]
                    expected = ["scope", "group_code", "baseline_snapshot", "outcome_end", "eligible_count", "source_count", "matched_count", "event_count", "multi_match_count"]
                    if columns != expected:
                        raise ValueError("El join no respeta el contrato agregado.")
                    query_rows = cursor.fetchmany(4001)
                    if len(query_rows) > 4000:
                        raise ValueError("El join excede el límite agregado; se necesita un lote más acotado.")
            except helper.psycopg2.Error as error:
                # Diagnósticos SQL pueden incluir el payload de llaves; no propagarlos.
                raise RuntimeError(f"No se completó el enlace agregado ({type(error).__name__}).") from None
            for values in query_rows:
                row = dict(zip(columns, values))
                key = (row["scope"], int(row["group_code"]))
                if key not in totals:
                    totals[key] = {name: row[name] for name in ("scope", "group_code", "baseline_snapshot", "outcome_end", "eligible_count")}
                    totals[key].update({name: 0 for name in ("source_count", "matched_count", "event_count", "multi_match_count")})
                for name in ("source_count", "matched_count", "event_count", "multi_match_count"):
                    totals[key][name] += int(row[name])
            ledger.append({"template": str(query_path.relative_to(ROOT)), "template_sha256": sha256_file(query_path),
                           "runtime_statement_sha256": hashlib.sha256(sql.encode()).hexdigest(), "executed_at": utc_now(),
                           "batch_number": offset // 10000 + 1, "source_records": len(batch), "aggregate_rows": len(query_rows),
                           "runtime_sql_persisted": False})
            del sql, batch, query_rows
    return list(totals.values()), ledger


def public_group(feature: str, state: str, count: int, events: int, config: dict) -> dict:
    labels = {"v1": "Favorable", "v0": "No favorable", **STATUS_LABELS}
    if feature.startswith("heartbeat_"):
        labels = {"v1": "Por encima de su promedio", "v0": "Igual a su promedio", "v-1": "Por debajo de su promedio", **STATUS_LABELS}
    eligible = count >= config["privacy"]["minimum_people"]
    publish_rate = eligible and events >= config["privacy"]["minimum_events"]
    return {"feature": feature, "response": labels.get(state, state), "people": count if eligible else None,
            "events": events if publish_rate else None, "attrition_percent": 100 * events / count if publish_rate else None,
            "cohort_published": eligible, "rate_published": publish_rate,
            "suppression": None if publish_rate else "Cohorte menor de 30 o menos de 30 eventos; tasa no publicada."}


def summarize_wave(candidate: dict, wave_config: dict, wave: WaveRows, config: dict) -> tuple[dict, dict, list[dict]]:
    records, signatures, status_counts = group_wave(candidate, wave)
    joined, ledger = query_join(records, wave_config, config)
    retrospective = []
    if candidate["id"] == "heartbeat" and wave.year == 2026:
        retrospective, historical_ledger = query_join(records, wave_config, config, query_path=HEARTBEAT_RETROSPECTIVE_QUERY)
        ledger.extend(historical_ledger)
    del records
    output_scopes = {}
    source_counts = Counter()
    source_margins = Counter()
    for row in (r for r in joined if r["scope"] == "workforce"):
        signature = signatures[int(row["group_code"])]
        n = int(row["source_count"])
        for name in ("primary_available", "primary_complete", "full_complete", "favorable_sum"):
            source_counts[name] += n * int(signature[name])
        for feature, state in signature["states"].items():
            raw_feature = f"heartbeat_{feature}" if candidate["id"] == "heartbeat" else feature
            source_margins[(raw_feature, state)] += n
    for scope in ("Engineering", "workforce"):
        rows = [r for r in joined if r["scope"] == scope]
        if not rows:
            raise RuntimeError("No se obtuvieron grupos agregados para la wave.")
        eligible = int(rows[0]["eligible_count"])
        counts = Counter()
        margins = defaultdict(lambda: [0, 0])
        for row in rows:
            signature = signatures[int(row["group_code"])]
            n = int(row["matched_count"])
            counts["matched"] += n
            counts["source"] += int(row["source_count"])
            counts["multi_match"] += int(row["multi_match_count"])
            for name in ("primary_available", "primary_complete", "full_complete", "comparable", "mismatch", "overlap_cohort_difference", "alternate_comparable", "alternate_disagreement"):
                counts[name] += n * int(signature[name])
            for feature, state in signature["states"].items():
                name = f"heartbeat_{feature}" if candidate["id"] == "heartbeat" else feature
                margins[(name, state)][0] += n
                margins[(name, state)][1] += int(row["event_count"])
        if counts["source"] != len(wave.rows) or counts["matched"] > eligible:
            raise ValueError("Los conteos del enlace no se reconcilian con la población.")
        output_scopes[scope] = {
            "eligible_people": eligible, "linked_people": counts["matched"], "without_linked_row": eligible - counts["matched"],
            "source_not_in_population": counts["source"] - counts["matched"],
            "with_any_primary": counts["primary_available"], "complete_primary": counts["primary_complete"], "complete_full": counts["full_complete"],
            "coverage_percent": 100 * counts["primary_available"] / eligible if eligible else 0,
            "complete_primary_percent": 100 * counts["primary_complete"] / eligible if eligible else 0,
            "groups": [public_group(feature, state, n, e, config) for (feature, state), (n, e) in sorted(margins.items())],
            "baseline_snapshot": str(rows[0]["baseline_snapshot"]), "outcome_start": wave_config["descriptive_anchor"], "outcome_end": str(rows[0]["outcome_end"]),
            "window_type": "anual descriptiva" if wave.year < 2026 else "acumulado descriptivo de 2026",
        }
        if scope == "Engineering":
            audit_counts = counts
    if retrospective:
        historical_margins = defaultdict(lambda: [0, 0])
        for row in retrospective:
            if row["scope"] != "workforce":
                continue
            signature = signatures[int(row["group_code"])]
            for feature, state in signature["states"].items():
                historical_margins[(f"heartbeat_{feature}", state)][0] += int(row["matched_count"])
                historical_margins[(f"heartbeat_{feature}", state)][1] += int(row["event_count"])
        output_scopes["workforce_historical_reconciliation"] = {
            **output_scopes["workforce"],
            "groups": [public_group(feature, state, n, e, config) for (feature, state), (n, e) in sorted(historical_margins.items())],
            "window_type": "Conciliación retrospectiva; eventos sin límite de snapshot de registro, como en el playbook.",
            "predictive_use_allowed": False,
        }
    expected = [f"Q{i}" for i in range(1, 54)] if candidate["id"] == "heartbeat" else components_for(candidate)
    form = "scale_indices" if candidate["id"] == "heartbeat" else "binary_indices"
    missing = sum(not wave.mapping.get(key, {}).get(form) for key in expected)
    ambiguous = sum(len(wave.mapping.get(key, {}).get(form, [])) > 1 for key in expected)
    engineering = output_scopes["Engineering"]
    audit = {key: 0 for key in AUDIT_COLUMNS}
    audit.update({
        "survey_year": wave.year, "snapshot_date": engineering["baseline_snapshot"], "workbooks_checked": 1,
        "header_ambiguities": ambiguous, "missing_component_headers": missing,
        "unverified_availability_waves": int(availability_date(wave_config) is None),
        "unresolved_wording_waves": int(candidate["id"] == "career" and wave.year == 2024 and config["source_rules"]["career_cross_wave_equivalence"] != "verified"),
        "invalid_count": status_counts.get("invalid", 0), "valid_count": status_counts.get("valid", 0),
        "missing_count": status_counts.get("missing", 0) + status_counts.get("sentinel_255", 0), "absent_count": status_counts.get("question_absent", 0),
        "status_reconciliation_difference": status_counts["status_reconciliation_difference"],
        "comparable_count": audit_counts["comparable"], "recalculated_match_count": audit_counts["comparable"] - audit_counts["mismatch"], "mismatch_count": audit_counts["mismatch"],
        "eligible_count": engineering["eligible_people"], "matched_count": engineering["linked_people"], "unmatched_count": engineering["without_linked_row"],
        "duplicate_count": 0, "multi_match_count": audit_counts["multi_match"],
        "full_exceeds_primary_count": max(0, engineering["complete_full"] - engineering["complete_primary"]),
        "overlap_cohort_difference": audit_counts["overlap_cohort_difference"],
        "primary_complete_count": engineering["complete_primary"], "full_complete_count": engineering["complete_full"],
        "source_participants": len(wave.rows), "primary_available_count": engineering["with_any_primary"],
        "missing_key_rows": wave.source_quality["missing_key_rows"] + wave.source_quality["invalid_key_rows"],
        "source_duplicate_count": wave.source_quality["distinct_duplicate_keys"],
        "alternative_headers_checked": sum(bool(wave.mapping.get(k, {}).get("alternative_binary_indices")) for k in expected),
        "alternate_comparable_count": audit_counts["alternate_comparable"],
        "alternate_disagreement_count": audit_counts["alternate_disagreement"],
    })
    result = {"year": wave.year, "availability": wave_config["availability"], "source_quality": wave.source_quality,
              "raw_summary": {"participants": len(wave.rows), "complete_primary": source_counts["primary_complete"],
                              "mean_favorable_percent": 100 * source_counts["favorable_sum"] / (33 * source_counts["primary_complete"]) if candidate["id"] == "mean33" and source_counts["primary_complete"] else None,
                              "groups": [public_group(feature, state, n, 0, config) for (feature, state), n in sorted(source_margins.items())]},
              "component_states_raw": {STATUS_LABELS.get(k, k): v for k, v in status_counts.items()}, "scopes": output_scopes,
              "component_headers": {key: {"binary_present": bool(wave.mapping.get(key, {}).get("binary_indices")), "scale_present": bool(wave.mapping.get(key, {}).get("scale_indices"))} for key in expected}}
    if candidate["id"] == "heartbeat":
        result["heartbeat_itemset"] = {
            "expected_ordinal_headers": 53,
            "present_ordinal_headers": 53 - missing,
            "domain_scope": "Las 53 entradas ordinales del promedio personal; los seis signos se auditan por separado en la fórmula.",
            "expected_input_states": len(wave.rows) * 53,
            "observed_input_states": sum(value for key, value in status_counts.items() if key != "status_reconciliation_difference"),
        }
    result["historical_reconciliation"] = reconcile_wave(candidate, result, config)
    checked = result["historical_reconciliation"]["checks"]
    audit["reconciliation_tests"] = len(checked)
    audit["reconciliation_mismatch_count"] = sum(not check["pass"] for check in checked)
    return result, audit, ledger


def display_number(value: float) -> str:
    return f"{value:,.1f}".rstrip("0").rstrip(".") if value % 1 else f"{value:,.0f}"


def describe_evidence(candidate: dict, evidence: dict) -> str:
    annual_lag = evidence.get("temporal_assignment") == "annual_lag"
    history_text = (
        "2024–2026: extracción de los Excel anuales y enlace a la población previa de Engineering. Para el modelo, la wave Y se asigna sólo a snapshots Y+1 por la política aprobada; esto no certifica la publicación real."
        if annual_lag else
        "2024–2026: extracción de los Excel anuales y enlace a la población previa de Engineering. La publicación real de resultados sigue pendiente cuando así lo indica el registro de fechas."
    )
    lines = [f"# {candidate['name']}", "", "Clasificación: `presentation`. Asociación descriptiva; no estima el aporte incremental al modelo.", "",
             "## Flujo histórico", "", history_text, "",
             "| Año | Elegibles | Enlazados | Con señal primaria | Cobertura % | Completa primaria | Completa total |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for wave in evidence["waves"]:
        s = wave["scopes"]["Engineering"]
        lines.append(f"| {wave['year']} | {s['eligible_people']:,} | {s['linked_people']:,} | {s['with_any_primary']:,} | {display_number(s['coverage_percent'])} | {s['complete_primary']:,} | {s['complete_full']:,} |")
    lines += ["", "## Asociaciones por respuesta", "", "Numerador: personas con salida voluntaria en la ventana. Denominador: personas del grupo de respuesta enlazadas a Engineering en el baseline. Se publican tasas con al menos 30 personas y 30 eventos.", "",
              "| Año | Componente | Respuesta | Personas | Salidas | Attrition % |", "|---|---|---|---:|---:|---:|"]
    for wave in evidence["waves"]:
        for group in wave["scopes"]["Engineering"]["groups"]:
            if group["rate_published"]:
                lines.append(f"| {wave['year']} | {group['feature']} | {group['response']} | {group['people']:,} | {group['events']:,} | {display_number(group['attrition_percent'])} |")
    temporal_limit = ("- La asignación Y a Y+1 es un supuesto de negocio para este experimento; no demuestra la fecha operativa de publicación." if annual_lag else "- La ventana anual del playbook comienza en enero; no acredita que la respuesta ya se conociera ese día.")
    next_action = ("- Repetir la validación con la wave 2026 cuando existan snapshots y outcomes de 2027; resolver además las equivalencias pendientes." if annual_lag else "- Confirmar disponibilidad y equivalencias pendientes antes de evaluar incremento predictivo.")
    lines += ["", "## Límites y siguiente acción", "", temporal_limit,
              "- El acumulado de 2026 termina en la última foto conocida antes del 7 de septiembre; no es una tasa anual.",
              "- Un registro sin enlace no demuestra que la persona fuera invitada y no respondiera.",
              next_action, "",
              f"Consulta: `{JOIN_QUERY.relative_to(ROOT)}`. Ejecución: {evidence['created_at']}.",
              "Los criterios, preguntas, reglas, métricas, scores y acciones detalladas se conservan en el assessment v4 de este concepto."]
    return "\n".join(lines) + "\n"


def audit_one(candidate: dict, config: dict, source_rows: dict[int, WaveRows], root: Path, metadata: dict) -> dict:
    if (root / "evidence.json").exists():
        raise FileExistsError("La evidencia del concepto ya existe; use una nueva versión de ejecución.")
    evidence = {"candidate": candidate["id"], "variable": candidate["name"], "created_at": utc_now(), "reporting_mode": "presentation",
                "knowledge_boundary": config["knowledge_boundary"], "temporal_assignment": config.get("temporal_rules", {}).get("assignment"), "waves": [], "audit_rows": [], "redshift_executions": [],
                "source_hashes": {w["file"]: w["sha256"] for w in metadata["waves"]}, "employee_level_rows_persisted": False,
                "audit_scope": {"domain": "Respuestas raw de la wave", "formula_and_join": "Engineering elegible en la foto previa", "coverage": "Descriptiva, sin certificar disponibilidad temporal"}}
    evidence["execution_hashes"] = {
        "configuration": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        "analysis_plan": sha256_file(plan_path(candidate, config)),
        "parser": sha256_file(ROOT / "tools/qvoice_model_data.py"),
        "adapter": sha256_file(Path(__file__)),
        "reconciliation": sha256_file(ROOT / "tools/qvoice_model_reconcile.py"),
    }
    inputs = root / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / "tools/qvoice_model_data.py", Path(__file__), ROOT / "tools/qvoice_model_reconcile.py", ROOT / "tools/qvoice_model_assessment.py", plan_path(candidate, config), JOIN_QUERY):
        shutil.copy2(source, inputs / source.name)
    if candidate["id"] == "heartbeat":
        shutil.copy2(HEARTBEAT_RETROSPECTIVE_QUERY, inputs / HEARTBEAT_RETROSPECTIVE_QUERY.name)
    write_json(inputs / "experiment-config.json", config)
    evidence["extra_queries"] = {}
    plan = yaml.safe_load(plan_path(candidate, config).read_text(encoding="utf-8"))
    local_audit = str(audit_query_path(candidate, config).relative_to(ROOT)).replace("\\", "/")
    extra = set(story["sql_reference"] for story in plan["validation_story"]) - {local_audit}
    if extra:
        sys.path.insert(0, str(ROOT / ".codex/skills/attrition-redshift-db/scripts"))
        import run_readonly_query as helper
        with helper.connect() as connection:
            connection.set_session(readonly=True, autocommit=True)
            for reference in sorted(extra):
                path = ROOT / reference
                sql = helper.validate_readonly(path.read_text(encoding="utf-8"))
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    columns = [column[0] for column in cursor.description]
                    if set(columns) & helper.SENSITIVE_OUTPUT_COLUMNS:
                        raise ValueError("El seguimiento intenta devolver una columna restringida.")
                    rows = cursor.fetchmany(1001)
                    if len(rows) > 1000:
                        raise ValueError("El seguimiento excede el contrato agregado.")
                evidence["extra_queries"][reference] = [dict(zip(columns, row)) for row in rows]
                evidence["redshift_executions"].append({"template": reference, "template_sha256": sha256_file(path), "executed_at": utc_now(), "aggregate_rows": len(rows)})
                shutil.copy2(path, inputs / path.name)
    for wave in config["sources"]["waves"]:
        log(f"Auditando {candidate['id']}, wave {wave['year']}...")
        row, audit, ledger = summarize_wave(candidate, wave, source_rows[wave["year"]], config)
        evidence["waves"].append(row)
        evidence["audit_rows"].append(audit)
        evidence["redshift_executions"].extend(ledger)
    audit_rows, coverage = execute_local_audit(candidate, evidence["audit_rows"], config)
    evidence["audit_rows"] = audit_rows
    evidence["coverage_rows"] = coverage
    evidence["local_sql_execution"] = {"engine": "sqlite3 :memory:", "executed_at": utc_now(), "rows_are_aggregated_before_sql": True,
                                        "sql_path": local_audit}
    evidence["completed_at"] = utc_now()
    root.mkdir(parents=True, exist_ok=True)
    write_json(root / "evidence.json", evidence)
    (root / "evidence-report.md").write_text(describe_evidence(candidate, evidence), encoding="utf-8")
    for row in audit_rows:
        log(f"{row['survey_year']}: elegibles={row['eligible_count']}, enlazados={row['matched_count']}, con señal={row['primary_available_count']}, inválidos={row['invalid_count']}, diferencias de fórmula={row['mismatch_count']}.")
    return evidence


def interactive(config: dict, root: Path) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    preflight = root / "preflight"
    if not (preflight / "preflight-manifest.json").exists():
        raise ValueError("Complete primero el preflight conjunto y los planes explícitos.")
    metadata = json.loads((preflight / "source-metadata.json").read_text(encoding="utf-8"))
    loaded_parser_hash = sha256_file(ROOT / "tools/qvoice_model_data.py")
    requested = {k for candidate in config["candidates"] for k in components_for(candidate)}
    source_rows = {}
    for wave in config["sources"]["waves"]:
        meta = next(m for m in metadata["waves"] if m["year"] == wave["year"])
        if sha256_file(ROOT / wave["file"]) != meta["sha256"]:
            raise ValueError("Un archivo fuente cambió después del preflight.")
        log(f"Leyendo columnas estructuradas de {wave['year']} en memoria...")
        source_rows[wave["year"]] = scan_wave(wave, meta, requested)
    log("Fuentes en memoria. Comandos: audit <id>, prepare <id>, finalize <id>, status, quit. Cada concepto se finaliza antes del siguiente.")
    finalized = set()
    for c in config["candidates"]:
        pointer = root / "variables" / c["id"] / "assessment-reference.json"
        if pointer.is_file():
            reference = json.loads(pointer.read_text(encoding="utf-8"))
            path = ROOT / reference["path"] / "manifest.json"
            if not path.is_file() or sha256_file(path) != reference["manifest_sha256"]:
                raise ValueError("El assessment publicado cambió; revisar antes de reanudar.")
            finalized.add(c["id"])
    pending = {}
    while True:
        command = sys.stdin.readline()
        if not command:
            break
        parts = command.strip().split()
        if not parts:
            continue
        if parts[0] == "quit":
            break
        if parts[0] == "status":
            log("Finalizados: " + ", ".join(c["id"] for c in config["candidates"] if c["id"] in finalized))
            continue
        try:
            if len(parts) != 2 or parts[0] not in ("audit", "prepare", "finalize"):
                raise ValueError("Comando no válido.")
            candidate = next(c for c in config["candidates"] if c["id"] == parts[1])
            current = next((c for c in config["candidates"] if c["id"] not in finalized), None)
            if current is None or current["id"] != candidate["id"]:
                raise ValueError("Debe finalizar el concepto actual antes de avanzar.")
            destination = root / "variables" / candidate["id"]
            if sha256_file(ROOT / "tools/qvoice_model_data.py") != loaded_parser_hash:
                raise ValueError("Cambió el parser después de cargar la fuente; reinicie la carga antes de auditar.")
            # Relee adaptadores y renderer sin volver a materializar respuestas individuales.
            importlib.reload(importlib.import_module("qvoice_model_reconcile"))
            importlib.reload(importlib.import_module("qvoice_model_assessment"))
            runtime = importlib.reload(importlib.import_module("qvoice_model_evidence"))
            if parts[0] == "audit":
                frozen = json.loads((preflight / "preflight-manifest.json").read_text(encoding="utf-8"))
                if frozen["plan_sha256"][candidate["id"]] != sha256_file(runtime.plan_path(candidate, config)) or frozen["configuration_sha256"] != hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest():
                    raise ValueError("El plan o configuración cambió; congele el preflight antes de consultar.")
                version = 1
                current_destination = destination
                while (current_destination / "evidence.json").exists():
                    version += 1
                    current_destination = destination / "revisions" / f"v{version}"
                evidence = runtime.audit_one(candidate, config, source_rows, current_destination, metadata)
                pending[candidate["id"]] = (evidence, current_destination, version)
                write_json(destination / "latest-evidence.json", {"path": str(current_destination.relative_to(ROOT)), "version": version})
                log("Evidencia lista para revisión; no se ha iniciado el siguiente concepto.")
            else:
                current = pending.get(candidate["id"])
                if current is None:
                    pointer = json.loads((destination / "latest-evidence.json").read_text(encoding="utf-8"))
                    evidence_root = ROOT / pointer["path"]
                    current = (json.loads((evidence_root / "evidence.json").read_text(encoding="utf-8")), evidence_root, pointer["version"])
                evidence, evidence_root, version = current
                assessment = runtime.assess_one(candidate, evidence, evidence_root, preflight, config=config, version=version, prepare_only=parts[0] == "prepare")
                if parts[0] == "prepare":
                    log(f"Comando preparado: {assessment.relative_to(ROOT)}")
                    continue
                write_json(destination / "assessment-reference.json", {"path": str(assessment.relative_to(ROOT)), "manifest_sha256": sha256_file(assessment / "manifest.json"), "evidence_path": str(evidence_root.relative_to(ROOT))})
                finalized.add(candidate["id"])
                log(f"Finalizado {candidate['id']}: notebook, HTML, Excel y documentación v4.")
        except Exception as error:
            log(f"ERROR {type(error).__name__}: {error}")
    source_rows.clear()
    log("Memoria de respuestas descartada.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    interactive(load_config(args.config), args.run_root.resolve())
