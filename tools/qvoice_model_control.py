"""Reproducir el modelo B histórico y conservar sólo métricas agregadas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import critical_tech_discrete_hazard_model as hz
import engineering_feature_block_selection as fs
import engineering_playbook_priority_model as pm
import engineering_playbook_tenure_confirmation as confirmation
from qvoice_model_data import ROOT, DEFAULT_CONFIG, load_config, sha256_file, utc_now, write_json


def load_control_frames(config: dict):
    authorization = json.loads((ROOT / config["authorization"]).read_text(encoding="utf-8"))
    if authorization.get("status") != "approved":
        raise ValueError("La autorización de procesamiento en memoria no está aprobada.")
    source = ROOT / config["control"]["source"]
    published = json.loads(source.read_text(encoding="utf-8"))
    if published["final_key"] != "b" or published["specs"]["b"]["features"] != config["control"]["features"]:
        raise ValueError("El contrato del control no coincide con el modelo B confirmado.")
    if published["knowledge_boundary"] != config["knowledge_boundary"]:
        raise ValueError("La frontera de conocimiento difiere de la reproducción acordada.")
    calendar = [d for d in hz.fetch_calendar() if d >= fs.MIN_SNAPSHOT]
    monthly, direct, totals = pm.load_person_months(calendar)
    return monthly, direct, totals, calendar, published


def reproduce(config: dict, output: Path, loaded=None) -> dict:
    if (output / "control-reproduction.json").exists():
        raise FileExistsError("La reproducción ya existe; utilice una nueva carpeta de ejecución.")
    monthly, direct, totals, calendar, published = loaded or load_control_frames(config)
    references = pm.modal_references(direct)
    runner = pm.Runner(monthly, direct, fs.fold_windows(direct), references)
    model = runner.run(config["control"]["features"], "tenure_playbook_band", tag="Reproducción del modelo B")
    actual = pm.public(model)
    expected = published["specs"]["b"]
    checks = []
    for key, value in (("person_months_read", totals["person_months"]), ("six_month_exposures", int(direct["exposure_count"].sum())), ("six_month_events", int(direct["event_count"].sum()))):
        checks.append({"check": key, "expected": published["frame"][key], "observed": value, "pass": value == published["frame"][key]})
    checks.append({"check": "parameters", "expected": expected["parameters"], "observed": actual["parameters"], "pass": actual["parameters"] == expected["parameters"]})
    tolerance = config["control"]["reproduction_relative_tolerance"]
    for fold, (observed, previous) in enumerate(zip(actual["folds"], expected["folds"]), 1):
        for key in ("exposures", "events", "snapshot_count"):
            checks.append({"check": f"fold_{fold}_{key}", "expected": previous[key], "observed": observed[key], "pass": observed[key] == previous[key]})
        for key in ("pr_auc", "lift_at_10_percent", "brier_score", "mean_predicted_percent"):
            difference = abs(observed[key] / previous[key] - 1)
            checks.append({"check": f"fold_{fold}_{key}", "expected": previous[key], "observed": observed[key], "relative_difference": difference, "pass": difference < tolerance})
    result = {
        "artifact": "qvoice-control-b-reproduction", "created_at": utc_now(), "reporting_mode": "presentation",
        "source": config["control"]["source"], "source_sha256": sha256_file(ROOT / config["control"]["source"]),
        "knowledge_boundary": config["knowledge_boundary"], "authorization": config["authorization"],
        "passed": all(c["pass"] for c in checks), "checks": checks, "model": actual,
        "frame": totals, "interaction_references": references,
        "queries": {str(p.relative_to(ROOT)): sha256_file(p) for p in (hz.CALENDAR_QUERY, pm.FRAME_QUERY)},
        "employee_level_rows_persisted": False,
        "note": "Reproduce el procedimiento histórico de B; la comparación QVoice usa selección L2 mediante Brier mensual y cortes explícitos de etiquetas.",
    }
    write_json(output / "control-reproduction.json", result)
    fs.log(f"Reproducción B: {'cumple' if result['passed'] else 'requiere revisión'}.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reproduce(load_config(args.config), args.output.resolve())
