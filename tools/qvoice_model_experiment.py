"""Ejecutar comparaciones QVoice predefinidas y escribir únicamente resultados agregados."""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import critical_tech_discrete_hazard_model as hz
import engineering_playbook_priority_model as historical
from qvoice_model_data import ROOT, DEFAULT_CONFIG, availability_date, components_for, favorable_band, load_config, scan_wave, sha256_file, utc_now, write_json, component_result
from qvoice_model_validation import monthly_split, period_frame, component_gate, select_monthly_l2, fit_selected, frame_metrics, bootstrap_paired, decision

DEFAULT_MODEL_QUERY = ROOT / "queries/profiles/engineering_qvoice_person_month_20261006.sql"


def model_query_path(config: dict) -> Path:
    configured = config.get("paths", {}).get("model_query")
    return ROOT / configured if configured else DEFAULT_MODEL_QUERY


def variant_specs(config: dict) -> list[dict]:
    variants = []
    for candidate in config["candidates"]:
        for variant in candidate["variants"]:
            representation = variant["representation"]
            if representation == "favorable_both":
                columns = ["qv_intent_both"]
            elif representation == "favorable_bands":
                columns = ["qv_mean33"]
            elif representation == "relative_to_personal_mean":
                columns = [f"qv_heartbeat_{key}" for key in variant["components"]]
            else:
                columns = [f"qv_{key}" for key in variant["components"]]
            variants.append({"id": variant["id"], "candidate": candidate["id"], "columns": columns})
    by_id = {v["id"]: v for v in variants}
    by_id["mean31"] = {"columns": ["qv_mean31"]}
    for combination in config["combinations"]:
        columns = list(dict.fromkeys(column for block in combination["blocks"] for column in by_id[block]["columns"]))
        variants.append({"id": combination["id"], "candidate": "combination", "columns": columns})
    return variants


def write_model_sql(config: dict) -> Path:
    """Derivar la consulta del control y conservar su linaje; no almacena el salt."""
    original = historical.FRAME_QUERY.read_text(encoding="utf-8")
    boundary = pd.Timestamp(config["knowledge_boundary"]).strftime("%Y-%m-%d")
    if original.count("DATE '2026-09-07' AS knowledge_boundary") != 1:
        raise ValueError("Cambió la frontera de la consulta del control; revisar el adaptador.")
    original = original.replace("DATE '2026-09-07' AS knowledge_boundary", f"DATE '{boundary}' AS knowledge_boundary")
    projection = "\nSELECT\n  f.snapshot_date,"
    if original.count(projection) != 1:
        raise ValueError("Cambió el contrato de la consulta del control; revisar el adaptador.")
    extra = ["  MD5(CAST(f.employee_id AS VARCHAR) || '__RUN_SALT__') AS person_key,", "  f.next_snapshot_date AS label_end,"]
    for wave in config["sources"]["waves"]:
        anchor = wave["descriptive_anchor"]
        extra.append(f"""  CASE WHEN f.service_date IS NOT NULL AND f.service_date <= DATE '{anchor}'
       AND NOT EXISTS (
         SELECT 1 FROM hrda.post_hire_monthly_worker_dtls episode
         WHERE episode.employee_id = f.employee_id
           AND CAST(episode.term_date AS DATE) >= DATE '{anchor}'
           AND CAST(episode.term_date AS DATE) <= f.snapshot_date
           AND CAST(episode.fis_mo_end_dt AS DATE) <= f.snapshot_date
       ) THEN 1 ELSE 0 END AS same_episode_{wave['year']},""")
    sql = original.replace(projection, projection + "\n" + "\n".join(extra))
    # Las etiquetas del experimento deben existir en snapshots observados al límite global.
    needle = "    AND CAST(term_date AS DATE) <= (SELECT knowledge_boundary FROM params)"
    sql = sql.replace(needle, needle + "\n    AND CAST(fis_mo_end_dt AS DATE) <= (SELECT knowledge_boundary FROM params)")
    sql = ("/* QVoice: sólo memoria, autorización 20261001. La llave MD5 usa salt aleatorio\n"
           "   por consulta y se descarta. No se guarda SQL expandido ni predicciones por persona.\n"
           "   Los indicadores same_episode impiden transportar respuestas entre contrataciones. */\n" + sql)
    path = model_query_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sql, encoding="utf-8")
    return path


def output_columns(config: dict) -> list[str]:
    return ["snapshot_date", "person_key", "label_end"] + [f"same_episode_{w['year']}" for w in config["sources"]["waves"]] + historical.OUTPUT_COLUMNS[1:]


def read_model_frame(config: dict, salt: str) -> pd.DataFrame:
    authorization = json.loads((ROOT / config["authorization"]).read_text(encoding="utf-8"))
    if authorization.get("status") != "approved" or len(salt) != 64 or any(c not in "0123456789abcdef" for c in salt):
        raise ValueError("La autorización o el identificador efímero de ejecución no es válido.")
    path = write_model_sql(config)
    sys.path.insert(0, str(ROOT / ".codex/skills/attrition-redshift-db/scripts"))
    import run_readonly_query as helper
    template = path.read_text(encoding="utf-8")
    sql = hz.render_query(template, pd.Timestamp(config["validation"]["training_start"]), pd.Timestamp(config["knowledge_boundary"]))
    sql = helper.validate_readonly(sql.replace("__RUN_SALT__", salt))
    columns = output_columns(config)
    parts = []
    with helper.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql)
            except helper.psycopg2.Error as error:
                raise RuntimeError(f"No se completó el frame autorizado ({type(error).__name__}).") from None
            actual_columns = [c[0] for c in cursor.description]
            if actual_columns != columns or set(actual_columns) & helper.SENSITIVE_OUTPUT_COLUMNS:
                raise ValueError("La consulta del experimento no respeta el contrato de columnas.")
            while True:
                rows = cursor.fetchmany(50000)
                if not rows:
                    break
                parts.append(pd.DataFrame(rows, columns=columns))
    frame = pd.concat(parts, ignore_index=True)
    frame["snapshot_date"] = pd.to_datetime(frame["snapshot_date"])
    frame["label_end"] = pd.to_datetime(frame["label_end"])
    if frame.duplicated(["person_key", "snapshot_date"]).any():
        raise ValueError("El frame contiene más de una fila por persona y snapshot.")
    for column in historical.FRAME_FEATURES:
        frame[column] = frame[column].fillna("(unknown)").astype(str)
    return frame


def wave_feature_values(values: dict, wave: dict, config: dict) -> dict[str, str]:
    features = {}
    for candidate in config["candidates"]:
        for key in components_for(candidate):
            value, status = component_result(values, key, heartbeat=candidate["id"] == "heartbeat")
            name = f"qv_heartbeat_{key}" if candidate["id"] == "heartbeat" else f"qv_{key}"
            features[name] = f"v{value}" if status == "valid" else status
    career_policy = config["source_rules"].get("career_cross_wave_equivalence", "pending")
    if wave["year"] == 2024 and career_policy not in ("verified", "exploratory_transport"):
        features["qv_career"] = "wording_unverified"
    q4, q12 = values.get("Q4", (None, "question_absent")), values.get("Q12", (None, "question_absent"))
    features["qv_intent_both"] = f"v{int(q4[0] == 1 and q12[0] == 1)}" if q4[1] == q12[1] == "valid" else "missing"
    numbers = [values.get(f"M{i:02d}", (None, "question_absent"))[0] for i in range(1, 34)]
    band = favorable_band(numbers, required_count=33)
    features["qv_mean33"] = band if band is not None else "missing"
    # M14 y M16 corresponden a los textos exactos Q12 y Q4 en la whitelist inmutable.
    remaining = [v for i, v in enumerate(numbers, 1) if i not in (14, 16)]
    features["qv_mean31"] = favorable_band(remaining, required_count=31) if band is not None else "missing"
    return features


def attach_qvoice(frame: pd.DataFrame, config: dict, metadata: dict, salt: str) -> pd.DataFrame:
    columns = list(dict.fromkeys(column for variant in variant_specs(config) for column in variant["columns"]))
    result = frame.copy()
    for column in columns:
        result[column] = "no_available_wave"
    result["qvoice_wave"] = "ninguna"
    available = [(availability_date(wave), wave) for wave in config["sources"]["waves"]]
    available = sorted([(known, wave) for known, wave in available if known is not None], key=lambda item: item[0])
    dates = [d for d, _ in available]
    if len(dates) != len(set(dates)):
        raise ValueError("Hay dos waves disponibles en la misma fecha sin orden de reemplazo.")
    requested = {key for candidate in config["candidates"] for key in components_for(candidate)}
    for index, (known, wave) in enumerate(available):
        expiration = known + pd.DateOffset(months=config["temporal_rules"]["maximum_age_months"])
        if index + 1 < len(available):
            expiration = min(expiration, available[index + 1][0])
        mask = (result["snapshot_date"] >= known) & (result["snapshot_date"] < expiration)
        if not mask.any():
            continue
        meta = next(m for m in metadata["waves"] if m["year"] == wave["year"])
        if sha256_file(ROOT / wave["file"]) != meta["sha256"]:
            raise ValueError("La fuente QVoice cambió después del preflight; se necesita una nueva ejecución.")
        source = scan_wave(wave, meta, requested)
        lookup = {hashlib.md5((str(key) + salt).encode()).hexdigest(): wave_feature_values(values, wave, config) for key, values in source.rows.items()}
        indices = result.index[mask]
        selected = result.loc[indices, "person_key"].map(lookup)
        same_episode = result.loc[indices, f"same_episode_{wave['year']}"] == 1
        for column in columns:
            mapped = selected.map(lambda value: value.get(column, "question_absent") if isinstance(value, dict) else "no_linked_row")
            mapped.loc[~same_episode] = "different_employment_episode"
            result.loc[indices, column] = mapped
        result.loc[indices, "qvoice_wave"] = str(wave["year"])
        del source, lookup, selected
    for column in columns:
        valid = result[column].isin(("v0", "v1", "v-1", "<50", "50–69", "70–79", "80–89", "90–99", "100"))
        result[f"av_{column}"] = np.where(valid, "available", result[column])
        result[column] = result[column].astype("category")
        result[f"av_{column}"] = result[f"av_{column}"].astype("category")
    return result


def modeling_frames(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    output = []
    for label in ("y_next", "y_6m"):
        subset = frame.loc[frame[label].notna()].copy()
        subset["exposure_count"] = 1
        subset["event_count"] = subset[label].astype(int)
        output.append(subset)
    return tuple(output)


def run_variant(config: dict, variant: dict, monthly: pd.DataFrame, direct: pd.DataFrame, periods: list[dict], control_cache: dict) -> dict:
    base = config["control"]["features"]
    rows = []
    for period in periods:
        test = period_frame(direct, period, config["knowledge_boundary"])
        item = {"period": period["id"], "main": period.get("main", True), "complete": len(test["snapshot_date"].unique()) == period.get("expected_snapshots", len(test["snapshot_date"].unique()))}
        if test.empty or not item["complete"]:
            rows.append({**item, "status": "not_evaluable", "reasons": ["No hay un periodo completo con seguimiento a seis meses."]})
            continue
        try:
            inner, validation, final = monthly_split(monthly, period["start"], config["validation"]["inner_validation_intervals"], config["validation"]["training_start"])
        except ValueError as error:
            rows.append({**item, "status": "not_evaluable", "reasons": [str(error)]})
            continue
        reasons = component_gate(inner, validation, variant["columns"]) + component_gate(test, test, variant["columns"])
        if reasons:
            rows.append({**item, "status": "not_evaluable", "reasons": list(dict.fromkeys(reasons))})
            continue
        event_people = test.loc[test["event_count"] > 0, "person_key"].nunique()
        if test.groupby("snapshot_date")["person_key"].nunique().min() < config["privacy"]["minimum_people"] or event_people < config["privacy"]["minimum_events"]:
            rows.append({**item, "status": "not_evaluable", "reasons": ["La cohorte general no cumple los mínimos de personas y eventos para publicar métricas."]})
            continue
        item.update({"status": "evaluated", "first_snapshot": str(test["snapshot_date"].min().date()), "last_snapshot": str(test["snapshot_date"].max().date()),
                     "snapshot_count": int(test["snapshot_date"].nunique()), "people": int(test["person_key"].nunique()),
                     "monthly_validation_dates": [str(pd.Timestamp(d).date()) for d in sorted(validation["snapshot_date"].unique())],
                     "fit_cutoff": period["start"], "maximum_inner_label_end": str(inner["label_end"].max().date()), "maximum_fit_label_end": str(final["label_end"].max().date()),
                     "maximum_test_label_end": str((test["snapshot_date"] + pd.DateOffset(months=6)).max().date())})
        predictions = {}
        trials = {}
        try:
            for name, features in (("control", base), ("availability", base + [f"av_{c}" for c in variant["columns"]]), ("response", base + variant["columns"])):
                cache_key = (period["id"], tuple(features))
                if cache_key not in control_cache:
                    l2, tuning = select_monthly_l2(inner, validation, features, config["validation"]["l2_grid"], config["control"]["penalty_cell_scale"])
                    fitted = fit_selected(final, features, l2, config["validation"]["l2_grid"], config["control"]["penalty_cell_scale"])
                    prediction = hz.six_month_predictions(fitted, test)
                    control_cache[cache_key] = (prediction, tuning, fitted.fitted.l2, len(fitted.fitted.beta))
                predictions[name], trials[name], final_l2, parameter_count = control_cache[cache_key]
                item[name] = {**frame_metrics(test, predictions[name]), "l2": final_l2, "parameters": parameter_count}
            if any(len(predictions[name]) != len(test) for name in predictions):
                raise ValueError("Los modelos no comparten exactamente las mismas filas de evaluación.")
        except ValueError as error:
            rows.append({**item, "status": "not_evaluable", "reasons": [str(error)]})
            continue
        item["l2_trials"] = trials
        item["cohort_equality_verified"] = True
        item["uncertainty"] = bootstrap_paired(test["person_key"].to_numpy(), test["event_count"].to_numpy(), predictions, config["validation"]["bootstrap_repetitions"], config["validation"]["bootstrap_seed"], config["validation"]["confidence_level"])
        valid_mask = test[[f"av_{c}" for c in variant["columns"]]].eq("available").all(axis=1)
        response_cohort = test.loc[valid_mask]
        event_people = response_cohort.loc[response_cohort["event_count"] == 1, "person_key"].nunique()
        min_snapshot_people = response_cohort.groupby("snapshot_date")["person_key"].nunique().min() if len(response_cohort) else 0
        published = bool(min_snapshot_people >= config["privacy"]["minimum_people"] and event_people >= config["privacy"]["minimum_events"])
        item["response_available_cohort"] = {"published": published,
            "coverage_percent": 100 * float(valid_mask.mean()),
            "metrics": {name: frame_metrics(response_cohort, values[valid_mask]) for name, values in predictions.items()} if published else None}
        item["usable_wave_count"] = int(test.loc[valid_mask, "qvoice_wave"].nunique())
        rows.append(item)
    return {**variant, "periods": rows, "decision": decision(rows, config["decision"]["minimum_complete_main_periods"])}


def compare(config: dict, root: Path) -> dict:
    destination = root / "comparison-results.json"
    if destination.exists():
        raise FileExistsError("El resultado comparativo ya existe; use una nueva ejecución.")
    periods = [{**p, "main": True} for p in config["validation"]["main_periods"]]
    supplementary_start = config["validation"].get("supplementary_start")
    if supplementary_start:
        last_supplementary = pd.Timestamp(config["knowledge_boundary"]) - pd.DateOffset(months=6)
        periods.append({"id": "supplementary_2026", "main": False, "start": supplementary_start, "end": str(last_supplementary.date())})
    variants = variant_specs(config)
    metadata_path = root / "preflight/source-metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {"waves": []}
    for variant in variants:
        notes = []
        if "qv_career" in variant["columns"] and config["source_rules"]["career_cross_wave_equivalence"] != "verified":
            if config["source_rules"]["career_cross_wave_equivalence"] == "exploratory_transport":
                notes.append("Career goals transporta de forma exploratoria la redacción 2024 a la versión posterior; esta sensibilidad no puede promover la variable por sí sola.")
            else:
                notes.append("La equivalencia del texto de Career goals de 2024 sigue pendiente; no se mezcla con las versiones posteriores.")
        for column in ("qv_Q6", "qv_Q9"):
            if column in variant["columns"]:
                absent = [str(wave["year"]) for wave in metadata["waves"] if not wave["mapping"].get(column[3:], {}).get("binary_indices")]
                if absent:
                    notes.append(f"{column[3:]} no existe en la fuente binaria de {', '.join(absent)}; el conjunto completo necesita historia propia.")
        if any(column.startswith("qv_heartbeat_") for column in variant["columns"]):
            incomplete = []
            for wave in metadata["waves"]:
                present = sum(bool(wave["mapping"].get(f"Q{i}", {}).get("scale_indices")) for i in range(1, 54))
                if present != 53:
                    incomplete.append(f"{wave['year']}: {present} de 53")
            if incomplete:
                notes.append("No se puede reconstruir el promedio ordinal exacto: " + "; ".join(incomplete) + ".")
        variant["eligibility_notes"] = notes
    boundary = pd.Timestamp(config["knowledge_boundary"])
    assigned = [w for w in config["sources"]["waves"] if availability_date(w) is not None]
    available = [w for w in assigned if availability_date(w) <= boundary]
    control_path = root / "control/control-reproduction.json"
    control_passed = False
    if control_path.is_file():
        control = json.loads(control_path.read_text(encoding="utf-8"))
        control_passed = bool(control["passed"] and control["source_sha256"] == sha256_file(ROOT / config["control"]["source"])
                              and control["knowledge_boundary"] == config["knowledge_boundary"]
                              and control["model"]["features"] == config["control"]["features"]
                              and all(sha256_file(ROOT / path) == digest for path, digest in control["queries"].items()))
    write_model_sql(config)
    if not available or not control_passed:
        reason = "No hay waves con fecha verificable de disponibilidad de resultados." if not available else "La reproducción del control B no ha pasado."
        results = [{**v, "periods": [{"period": p["id"], "main": p["main"], "complete": False, "status": "not_evaluable", "reasons": [reason]} for p in periods],
                    "decision": {"status": "evidencia temporal insuficiente", "complete_main_periods": 0}} for v in variants]
    else:
        salt = secrets.token_hex(32)
        frame = read_model_frame(config, salt)
        frame = attach_qvoice(frame, config, metadata, salt)
        monthly, direct = modeling_frames(frame)
        del frame, salt
        cache = {}
        results = []
        for index, variant in enumerate(variants, 1):
            print(f"[{index:02d}/{len(variants):02d}] Ajustando {variant['id']}...", flush=True)
            results.append(run_variant(config, variant, monthly, direct, periods, cache))
            print(f"[{index:02d}/{len(variants):02d}] {variant['id']}: {results[-1]['decision']['status']}.", flush=True)
        del cache, monthly, direct
    result = {"experiment": config["experiment_id"], "created_at": utc_now(), "reporting_mode": "presentation",
              "knowledge_boundary": config["knowledge_boundary"], "control_reproduced": bool(control_passed),
              "available_wave_count": len(available), "assigned_wave_count": len(assigned), "variants": results, "authorization": config["authorization"],
              "employee_level_rows_persisted": False, "individual_scores_published": False,
              "model_query": str(model_query_path(config).relative_to(ROOT)), "model_query_sha256": sha256_file(model_query_path(config))}
    write_json(destination, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    result = compare(load_config(args.config), args.run_root.resolve())
    print(f"Comparación registrada: {len(result['variants'])} variantes, {result['available_wave_count']} waves con disponibilidad acreditada.")
