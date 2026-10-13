"""Compara C+Q, C+ciudad+Q y B+Q con resultados agregados."""
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
import engineering_model_c as c  # noqa: E402
import engineering_model_c_fast as fast  # noqa: E402
import engineering_model_c_qvoice as cq  # noqa: E402
import qvoice_horizon_calibration as horizon  # noqa: E402
import qvoice_model_data as qdata  # noqa: E402


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def loader_config(spec, out):
    config = read(ROOT / spec["loader_config"])
    config["run_id"] = spec["run_id"]
    config["output"] = out.relative_to(ROOT).as_posix()
    config["reporting_mode"] = "presentation"
    config["employee_level_rows_persisted"] = False
    config["individual_scores_published"] = False
    config["qvoice_alias_features"] = spec.get("qvoice_alias_features", [])
    if spec.get("source_c_config"):
        config["source_c_config"] = spec["source_c_config"]
    if spec.get("base_query"):
        config["base_query"] = spec["base_query"]
    config["skip_extra_hr_queries"] = bool(spec.get("skip_extra_hr_queries", False))
    if spec.get("disable_qvoice_comments", False):
        config.pop("qvoice_comments_contract", None)
    config.pop("skip_qvoice", None)
    return config


def copy_evidence(spec, out):
    source = ROOT / spec["evidence_source"] / "input-evidence"
    if not source.exists():
        raise RuntimeError(f"No existe la evidencia V11: {source}")
    shutil.copytree(source, out / "input-evidence", dirs_exist_ok=True)


def fit_city(frame, cutoff, base_model, c_config):
    train = c.train_before(frame, cutoff)
    features = list(base_model.features)
    if "work_city" in features:
        raise RuntimeError("work_city ya está en el modelo base.")
    features.append("work_city")
    design = c.Design.fit(train, features, c_config["interactions"])
    matrix = design.matrix(train)
    model = fast.fit_context(design, matrix, train.y_next.to_numpy(float), features, float(base_model.l2), c_config)
    del train, matrix
    return model


def q_spec(period_id, cq_config):
    path = ROOT / cq_config["output"] / "folds" / period_id / "selection.json"
    selection = read(path)
    return selection["winner"], path.relative_to(ROOT).as_posix()


def fit_q(frame, cutoff, base_model, spec):
    train = frame.loc[frame.y_next.notna() & (frame.label_end <= pd.Timestamp(cutoff))].copy()
    features = list(spec["features"])
    encoder = cq.qmodel.CategoryEncoder.fit(train, features)
    matrix = horizon.category_matrix(encoder, train)
    offset = cq.eta(base_model, train)
    beta, converged, iterations = cq.qmodel.fit_offset(matrix, train.y_next.to_numpy(float), offset, float(spec["l2"]))
    if not converged:
        raise RuntimeError(f"No convergió Q para {cutoff}.")
    del train, matrix, offset
    return encoder, beta, iterations


def correction(model, frame, fitted):
    encoder, beta = fitted[:2]
    return horizon.category_matrix(encoder, frame) @ beta


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


def summarize_evaluation(evaluation):
    global_metrics = evaluation["global"]
    metrics = evaluation["scenarios"]["30"]["metrics"]
    return {
        "log_loss": float(global_metrics["log_loss"]),
        "brier_score": float(global_metrics["brier_score"]),
        "pr_auc": float(global_metrics["pr_auc"]),
        "lift_at_10_percent": float(global_metrics["lift_at_10_percent"]),
        "capture_percent": float(metrics["capture_percent"]),
        "group_snapshot_mae_pp": float(metrics["group_snapshot_mae_pp"]),
        "group_mae_pp": float(metrics["group_mae_pp"]),
    }


def mean_rows(rows):
    keys = rows[0].keys()
    return {key: float(np.mean([row[key] for row in rows])) for key in keys}


def report(result):
    s = result["summary"]
    lines = [
        "# F + QVoice frente a C + QVoice y B + QVoice",
        "",
        "Comparación retrospectiva en modo `presentation`; no se guardaron filas, identificadores ni predicciones individuales.",
        "",
        "F+Q reutiliza la selección QVoice archivada de CQ por periodo y añade únicamente `work_city` al modelo C antes de la corrección Q. B+Q es la variante archivada `B_Q` de la ronda V11.",
        "",
        "## Promedio de agosto–diciembre de 2025 y enero–febrero de 2026",
        "",
        "Menor es mejor para pérdidas y error de grupo; mayor es mejor para PR-AUC, lift y captura.",
        "",
        "| Modelo | Log-loss ×1000 ↓ | Brier ×1000 ↓ | PR-AUC ↑ | Lift 10% ↑ | Captura 30% ↑ | Error grupo-mes ↓ |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label in ["C_plus_city_Q", "C_Q", "B_Q_archived"]:
        row = s[label]
        lines.append(f"| {row['label']} | {row['log_loss']*1000:.1f} | {row['brier_score']*1000:.1f} | {row['pr_auc']*100:.1f}% | {row['lift_at_10_percent']:.1f} | {row['capture_percent']:.1f}% | {row['group_snapshot_mae_pp']:.1f} pp |")
    lines += [
        "",
        "## Lectura",
        "",
        "La comparación F+Q frente a C+Q aísla el aporte de `work_city` manteniendo fija la selección QVoice de CQ. La comparación con B+Q usa el artefacto archivado `B_Q`; sus cifras se reportan como referencia externa de la misma ventana, no como un reajuste nuevo de B.",
        "",
    ]
    (ROOT / result["output"] / "informe.md").write_text("\n".join(lines), encoding="utf-8")


def run(config_path):
    spec = read(config_path)
    out = ROOT / spec["output"]
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"La salida ya existe y no se sobrescribirá: {out}")
    out.mkdir(parents=True)
    copy_evidence(spec, out)
    loader = loader_config(spec, out)
    c_config = read(ROOT / spec["c_config"])
    cq_config = read(ROOT / spec["cq_config"])
    qconfig = qdata.load_config(ROOT / loader["source_qvoice_config"])
    qmetadata = read(ROOT / loader["source_qvoice_metadata"])
    source_paths = [ROOT / spec["c_config"], ROOT / spec["cq_config"], ROOT / spec["loader_config"]]
    for key in ("source_c_config", "base_query"):
        if spec.get(key):
            source_paths.append(ROOT / spec[key])
    source_paths += [ROOT / cq_config["output"] / "folds" / p["id"] / "selection.json" for p in spec["periods"]]
    source_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths}
    write(out / "frozen-config.json", spec)
    write(out / "manifest.json", {"run_id": spec["run_id"], "status": "running", "reporting_mode": "presentation", "started_at": datetime.now(timezone.utc).isoformat(), "employee_level_rows_persisted": False, "individual_scores_published": False})

    started = time.perf_counter()
    print("Cargando frame V11 con QVoice en memoria.", flush=True)
    frame, qframe = data.load(loader, out)
    if qframe is None:
        raise RuntimeError("No se cargó QVoice.")
    bank = cq.catalog(cq_config)
    periods = []
    held = []
    for period in spec["periods"]:
        origin, base_model, base_reference = cq.model_before(bank, period["origin"])
        city = fit_city(frame, period["origin"], base_model, c_config)
        qwinner, selection_path = q_spec(period["id"], cq_config)
        q_c = fit_q(qframe, period["origin"], base_model, qwinner)
        q_city = fit_q(qframe, period["origin"], city, qwinner)
        test = test_frame(qframe, period, loader["knowledge_boundary"])
        pred = {
            "C": base_model.risk(test),
            "C_Q": cq.risk(base_model, test, correction(base_model, test, q_c)),
            "C_plus_city_Q": cq.risk(city, test, correction(city, test, q_city)),
        }
        evaluation, allocations = cq.evaluate(test, pred, cq_config)
        summaries = {name: summarize_evaluation(value) for name, value in evaluation.items()}
        periods.append({
            **period,
            "base_model_origin": str(origin.date()),
            "base_model_reference": base_reference,
            "q_selection": qwinner,
            "q_selection_source": selection_path,
            "training_snapshots": int(c.train_before(frame, period["origin"]).snapshot_date.nunique()),
            "evaluation_snapshots": int(test.snapshot_date.nunique()),
            "metrics": summaries,
            "models": {
                "C_Q": {"features": list(base_model.features), "l2": float(base_model.l2), "q_iterations": int(q_c[2]) if len(q_c) > 2 else None},
                "C_plus_city_Q": {"features": list(city.features), "l2": float(city.l2), "q_iterations": int(q_city[2]) if len(q_city) > 2 else None},
            },
        })
        held.append({"y": test.y_6m.to_numpy(float), "c": pred["C_Q"], "f": pred["C_plus_city_Q"], "ac": allocations["30"]["C_Q"], "af": allocations["30"]["C_plus_city_Q"]})
        del city, q_c, q_city, test, pred, evaluation, allocations
        gc.collect()
        print(f"{period['id']} terminado.", flush=True)

    # Referencia B+Q archivada en la misma ventana temporal.
    bq = read(ROOT / spec["bq_results"])["summary"]["QVoice"]["B_Q"]
    bq_summary = {
        "label": "B + QVoice (B_Q archivado)",
        "log_loss": float(bq["log_loss"]),
        "brier_score": float(bq["brier_score"]),
        "pr_auc": float(bq["pr_auc"]),
        "lift_at_10_percent": float(bq["lift_at_10_percent"]),
        "capture_percent": float(bq["capture_percent"]),
        "group_snapshot_mae_pp": float(bq["common_group_snapshot_mae_pp"]),
    }
    summary = {
        "C_plus_city_Q": {"label": "C + ciudad + QVoice", **mean_rows([p["metrics"]["C_plus_city_Q"] for p in periods])},
        "C_Q": {"label": "C + QVoice", **mean_rows([p["metrics"]["C_Q"] for p in periods])},
        "B_Q_archived": bq_summary,
    }
    deltas = {
        "FQ_minus_CQ": {key: summary["C_plus_city_Q"][key] - summary["C_Q"][key] for key in ["log_loss", "brier_score", "pr_auc", "lift_at_10_percent", "capture_percent", "group_snapshot_mae_pp"]},
    }
    result = {"run_id": spec["run_id"], "model_id": "FQ", "output": spec["output"], "reporting_mode": "presentation", "summary": summary, "deltas": deltas, "periods": periods, "source_hashes": source_hashes, "bq_source": spec["bq_results"], "employee_level_rows_persisted": False, "individual_scores_published": False, "elapsed_seconds": time.perf_counter() - started}
    write(out / "results.json", result)
    report(result)
    write(out / "manifest.json", {"run_id": spec["run_id"], "status": "completed_experimental", "reporting_mode": "presentation", "completed_at": datetime.now(timezone.utc).isoformat(), "source_hashes": source_hashes, "employee_level_rows_persisted": False, "individual_scores_published": False, "files": {p.relative_to(out).as_posix(): sha(p) for p in out.rglob("*") if p.is_file() and p.name != "manifest.json"}})
    print("F + QVoice completo; sólo se conservaron agregados.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/engineering_f_qvoice_comparison_20261013.json")
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(ROOT / args.config)
