"""Prueba incremental de señales V11 sobre C; sólo agregados en disco."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import b_incremental_data as data  # noqa: E402
import engineering_b_incremental as inc  # noqa: E402
import engineering_model_c as c  # noqa: E402
import engineering_model_c_fast as fast  # noqa: E402


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def prepare_loader_config(spec, out):
    config = read(ROOT / spec["loader_config"])
    config["run_id"] = spec["run_id"]
    config["output"] = str(out.relative_to(ROOT).as_posix())
    config["reporting_mode"] = spec["reporting_mode"]
    config["employee_level_rows_persisted"] = False
    config["individual_scores_published"] = False
    # Estos challengers prueban señales RH sobre C; QVoice ya se evaluó en D/CQ.
    config["skip_qvoice"] = True
    return config


def copy_aggregated_evidence(loader_config, out):
    source = ROOT / read(ROOT / "config/engineering_c_signal_expansion_20261012.json")["loader_config"]
    source_config = read(source)
    source_dir = ROOT / source_config["output"] / "input-evidence"
    target_dir = out / "input-evidence"
    if not source_dir.exists():
        raise RuntimeError(f"No existe la evidencia V11 esperada: {source_dir}")
    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)


def test_frame(frame, period, knowledge):
    result = frame.loc[
        (frame.snapshot_date >= pd.Timestamp(period["origin"]))
        & (frame.snapshot_date <= pd.Timestamp(period["end"]))
        & frame.y_6m.notna()
        & (frame.r6_end <= pd.Timestamp(knowledge))
    ].copy()
    if result.snapshot_date.nunique() != period["snapshots"]:
        raise RuntimeError(f"El periodo {period['id']} no tiene los snapshots esperados.")
    return result


def c_features_for_period(spec, period):
    path = ROOT / spec["selection_dir"] / f"fold-{period['fold']}.json"
    selection = read(path)
    features = list(selection["C"]["features"])
    l2 = float(selection["C"]["l2"])
    return features, l2, path.relative_to(ROOT).as_posix()


def score(frame, prediction, config):
    evaluator = inc.Evaluation(frame, config)
    return evaluator.score(prediction, detailed=False)


def fit_variant(train, test, c_features, additions, l2, c_config):
    features = list(c_features)
    for feature in additions:
        if feature in features:
            raise RuntimeError(f"La señal {feature} ya está en C para este corte.")
        features.append(feature)
    design = c.Design.fit(train, features, c_config["interactions"])
    x = design.matrix(train)
    y = train.y_next.to_numpy(float)
    model = fast.fit_context(design, x, y, features, l2, c_config)
    prediction = model.risk(test)
    return model, prediction, features


def period_record(frame, period, spec, loader_config, c_config):
    train = c.train_before(frame, period["origin"])
    test = test_frame(frame, period, loader_config["knowledge_boundary"])
    c_features, l2, selection_path = c_features_for_period(spec, period)
    # Las interacciones de C se construyen dentro de Design.prepare(); no son
    # columnas almacenadas del frame temporal.
    required = {
        feature for feature in c_features
        if feature not in c_config["interactions"]
    }
    for variant in spec["variants"]:
        required.update(variant["additions"])
    absent = sorted(required - set(frame.columns))
    if absent:
        raise RuntimeError(f"Faltan señales en el frame de {period['id']}: {absent}")

    models = {}
    metrics = {}
    predictions = {}
    for label, additions in [("C", [])] + [(v["id"], v["additions"]) for v in spec["variants"]]:
        model, prediction, features = fit_variant(train, test, c_features, additions, l2, c_config)
        models[label] = {"features": features, "iterations": int(model.iterations), "l2": l2}
        predictions[label] = prediction
        metrics[label] = score(test, prediction, loader_config)
        log(f"{period['id']}: {label} listo; captura {metrics[label]['capture_percent']:.2f}%.")

    frame_for_weights = inc.Evaluation(test, loader_config)
    weights = {}
    for label, prediction in predictions.items():
        grouped = frame_for_weights.grouped(prediction)
        weights[label] = grouped.allocation(loader_config["primary_capacity_fraction"])[0].ravel()[grouped.cells]

    record = {
        "period": period,
        "selection_source": selection_path,
        "c_features": c_features,
        "c_l2": l2,
        "training_snapshots": int(train.snapshot_date.nunique()),
        "evaluation_snapshots": int(test.snapshot_date.nunique()),
        "metrics": metrics,
        "models": models,
        "_held": {
            "person_key": test.person_key.astype(str).to_numpy(),
            "y": test.y_6m.to_numpy(float),
            "predictions": predictions,
            "weights": weights,
        },
    }
    del train, test, predictions, weights, frame_for_weights
    gc.collect()
    return record


def bootstrap_intervals(records, variant, repetitions, seed):
    keys = np.concatenate([r["_held"]["person_key"] for r in records])
    inverse, unique = pd.factorize(keys, sort=False)
    counts = []
    events = []
    log_delta = []
    brier_delta = []
    capture_c = []
    capture_v = []
    start = 0
    for record in records:
        held = record["_held"]
        n = len(held["y"])
        codes = inverse[start:start + n]
        start += n
        y = held["y"]
        p_c = held["predictions"]["C"]
        p_v = held["predictions"][variant]
        p_c = np.clip(p_c, 1e-12, 1 - 1e-12)
        p_v = np.clip(p_v, 1e-12, 1 - 1e-12)
        ll_c = -y * np.log(p_c) - (1 - y) * np.log1p(-p_c)
        ll_v = -y * np.log(p_v) - (1 - y) * np.log1p(-p_v)
        br_c = (y - p_c) ** 2
        br_v = (y - p_v) ** 2
        binc = lambda values: np.bincount(codes, weights=values, minlength=len(unique))
        counts.append(binc(np.ones(n)))
        events.append(binc(y))
        log_delta.append(binc(ll_c - ll_v))
        brier_delta.append(binc(br_c - br_v))
        capture_c.append(binc(y * held["weights"]["C"]))
        capture_v.append(binc(y * held["weights"][variant]))
    arrays = [np.asarray(x) for x in [counts, events, log_delta, brier_delta, capture_c, capture_v]]
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(repetitions):
        w = rng.multinomial(len(unique), np.full(len(unique), 1 / len(unique)))
        n, e, ll, br, cap_c, cap_v = [a @ w for a in arrays]
        if np.any(n <= 0) or np.any(e <= 0):
            continue
        draws.append([
            float(np.mean(ll / n)),
            float(np.mean(br / n)),
            float(100 * (cap_v.sum() - cap_c.sum()) / e.sum()),
        ])
    values = np.asarray(draws)
    return {
        "variant": variant,
        "method": "Bootstrap pareado por persona; features y grupos fijos por periodo; igual peso por periodo.",
        "repetitions": int(len(values)),
        "log_loss_delta_C_minus_variant": np.quantile(values[:, 0], [0.025, 0.975]).tolist(),
        "brier_delta_C_minus_variant": np.quantile(values[:, 1], [0.025, 0.975]).tolist(),
        "capture_delta_variant_minus_C_pp": np.quantile(values[:, 2], [0.025, 0.975]).tolist(),
    }


def means(records):
    labels = ["C"] + [r["id"] for r in SPEC["variants"]]
    numeric = [
        "log_loss", "brier_score", "pr_auc", "lift_at_10_percent",
        "common_group_snapshot_mae_pp", "capture_percent", "priority_group_snapshot_mae_pp",
    ]
    result = {}
    for label in labels:
        rows = [r["metrics"][label] for r in records]
        result[label] = {"periods": [r["period"]["id"] for r in records]}
        for field in numeric:
            result[label][field] = float(np.mean([row[field] for row in rows]))
    return result


def build_report(result):
    model_id = result.get("model_id", "E")
    lines = [
        f"# Modelo {model_id}: señales V11 añadidas sobre C",
        "",
        "Ejecución experimental en modo `presentation`; no se guardaron filas, identificadores ni scores individuales.",
        "",
        "Se reutilizaron las features y L2 seleccionadas en cada fold de C. Las variantes añaden señales V11 y reajustan el hazard mensual con la misma penalización.",
        "",
        "## Promedio de los cuatro periodos",
        "",
        "Menor es mejor para pérdidas y error de grupo; mayor es mejor para PR-AUC, lift y captura.",
        "",
        "| Variante | Log-loss × 1000 | Brier × 1000 | PR-AUC (%) | Lift 10% | Captura 30% (%) | Error grupo (pp) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, row in result["summary"].items():
        lines.append(f"| {label} | {row['log_loss']*1000:.1f} | {row['brier_score']*1000:.1f} | {row['pr_auc']*100:.1f} | {row['lift_at_10_percent']:.1f} | {row['capture_percent']:.1f} | {row['common_group_snapshot_mae_pp']:.1f} |")
    lines += ["", "## Intervalos pareados frente a C", "", "Un intervalo de captura completamente positivo favorece a la variante; un intervalo de pérdidas completamente positivo en `C - variante` favorece a la variante.", "", "| Variante | IC95 log-loss C − variante | IC95 Brier C − variante | IC95 captura variante − C (pp) |", "|---|---:|---:|---:|"]
    for label, row in result["intervals"].items():
        lines.append(f"| {label} | [{row['log_loss_delta_C_minus_variant'][0]*1000:.2f}, {row['log_loss_delta_C_minus_variant'][1]*1000:.2f}] | [{row['brier_delta_C_minus_variant'][0]*1000:.2f}, {row['brier_delta_C_minus_variant'][1]*1000:.2f}] | [{row['capture_delta_variant_minus_C_pp'][0]:.2f}, {row['capture_delta_variant_minus_C_pp'][1]:.2f}] |")
    lines += ["", "## Lectura", "", "La comparación es incremental y retrospectiva. Una variante con señal positiva sobre C sigue siendo experimental: no se reoptimizaron los grupos, no se seleccionaron variables usando el periodo externo y la prueba no demuestra causalidad ni superioridad frente a C o CQ.", ""]
    (ROOT / result["output"] / "informe.md").write_text("\n".join(lines), encoding="utf-8")


def run(config_path):
    global SPEC
    SPEC = read(config_path)
    out = ROOT / SPEC["output"]
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"La salida ya existe y no se sobrescribirá: {out}")
    out.mkdir(parents=True)
    loader_config = prepare_loader_config(SPEC, out)
    c_config = read(ROOT / SPEC["c_config"])
    copy_aggregated_evidence(loader_config, out)
    write(out / "frozen-config.json", SPEC)
    write(out / "manifest.json", {"run_id": SPEC["run_id"], "status": "running", "reporting_mode": SPEC["reporting_mode"], "started_at": datetime.now(timezone.utc).isoformat(), "employee_level_rows_persisted": False, "individual_scores_published": False})
    source_paths = [ROOT / SPEC["c_config"], ROOT / SPEC["loader_config"]]
    source_paths += [ROOT / SPEC["selection_dir"] / f"fold-{p['fold']}.json" for p in SPEC["periods"]]
    source_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths}
    write(out / "source-hashes.json", source_hashes)

    log("Cargando el frame temporal en memoria con los contratos V11 ya aprobados.")
    frame, _ = data.load(loader_config, out)
    records = []
    started = time.perf_counter()
    for period in SPEC["periods"]:
        records.append(period_record(frame, period, SPEC, loader_config, c_config))
        gc.collect()
    summary = means(records)
    intervals = {v["id"]: bootstrap_intervals(records, v["id"], SPEC["bootstrap_repetitions"], SPEC["seed"]) for v in SPEC["variants"]}
    for r in records:
        r.pop("_held", None)
    result = {"model_id": SPEC.get("model_id", "E"), "run_id": SPEC["run_id"], "output": SPEC["output"], "reporting_mode": SPEC["reporting_mode"], "summary": summary, "intervals": intervals, "periods": records, "variants": SPEC["variants"], "source_hashes": source_hashes, "employee_level_rows_persisted": False, "individual_scores_published": False, "elapsed_seconds": time.perf_counter() - started}
    write(out / "results.json", result)
    build_report(result)
    write(out / "manifest.json", {"run_id": SPEC["run_id"], "status": "completed_experimental", "reporting_mode": SPEC["reporting_mode"], "completed_at": datetime.now(timezone.utc).isoformat(), "source_hashes": source_hashes, "employee_level_rows_persisted": False, "individual_scores_published": False, "files": {p.relative_to(out).as_posix(): sha(p) for p in out.rglob("*") if p.is_file() and p.name != "manifest.json"}})
    c.log(f"Modelo {SPEC.get('model_id', 'E')} completo; sólo se conservaron agregados.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/engineering_c_signal_expansion_20261012.json")
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(ROOT / args.config)


if __name__ == "__main__":
    main()
