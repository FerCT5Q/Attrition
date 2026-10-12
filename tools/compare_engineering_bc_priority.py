"""Comparación retrospectiva de prioridades B/C; sólo agregados salen de RAM."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import time

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import engineering_model_c as base
import engineering_model_c_fast as fast

ROOT = base.ROOT
DEFAULT = ROOT / "config/engineering_bc_priority_comparison_20261008.json"


def restore_model(artifact):
    return base.Model(base.Design(**artifact["encoder"]), np.array(artifact["beta"]),
                      artifact["features"], artifact["l2"], artifact["iterations"])


def apply_rules(frame, artifact):
    leaf = np.full(len(frame), -1, dtype=int)
    for rule in artifact["rules"]:
        mask = np.ones(len(frame), dtype=bool)
        for condition in rule["conditions"]:
            feature, category = condition["condition"].split("=", 1)
            equal = frame[feature].astype(str).to_numpy() == category
            mask &= equal if condition["present"] else ~equal
        if np.any(leaf[mask] != -1):
            raise RuntimeError("Reglas de grupos superpuestas.")
        leaf[mask] = int(rule["node"])
    if np.any(leaf == -1):
        raise RuntimeError("Las reglas no cubren la población.")
    return leaf


def group_scores(leaf, artifact):
    lookup = {int(r["node"]): r["training_mean_risk"] for r in artifact["rules"]}
    return np.array([lookup[int(n)] for n in leaf])


def allocate(scores, fraction):
    """Misma probabilidad dentro de un empate; no se observan las etiquetas."""
    target = len(scores) * fraction
    cutoff = np.sort(scores)[::-1][max(0, int(np.ceil(target)) - 1)]
    above, tied = scores > cutoff, scores == cutoff
    probability = (target - above.sum()) / tied.sum()
    weights = above.astype(float) + tied * np.clip(probability, 0, 1)
    if not np.isclose(weights.sum(), target, atol=1e-7):
        raise RuntimeError("No se conservó la capacidad de intervención.")
    partial = bool(1e-10 < probability < 1 - 1e-10)
    lower = float(above.mean()) if partial else fraction
    upper = float((above | tied).mean()) if partial else fraction
    return weights, lower, upper


def policy(frame, scores, fraction):
    weights = np.zeros(len(frame))
    brackets = []
    dates = frame.snapshot_date.to_numpy()
    for date in np.unique(dates):
        idx = np.flatnonzero(dates == date)
        local, lower, upper = allocate(scores[idx], fraction)
        weights[idx] = local
        brackets.append({"snapshot": str(pd.Timestamp(date).date()), "people": len(idx),
                         "lower_whole_group_coverage_percent": 100 * lower,
                         "upper_whole_group_coverage_percent": 100 * upper})
    return weights, brackets


def context(frame):
    date_codes, dates = pd.factorize(frame.snapshot_date, sort=True)
    return {"frame": frame, "y": frame.y_6m.to_numpy(float), "date_codes": date_codes,
            "date_count": len(dates), "keys": frame.person_key.to_numpy()}


def describe(ctx, prediction, weights, leaves=None):
    y, dates, keys = ctx["y"], ctx["date_codes"], ctx["keys"]
    total = weights.sum()
    active = weights > 1e-12
    if total <= 0:
        raise RuntimeError("Selección vacía.")
    ndate = np.bincount(dates, weights=weights, minlength=ctx["date_count"])
    events = float(weights @ y)
    observed = events / total
    predicted = float(weights @ prediction / total)
    distinct_events = len(np.unique(keys[active & (y == 1)]))
    if np.min(ndate) < 30 or distinct_events < 30:
        return {"suppressed": True}, []
    result = {"coverage_percent": 100 * total / len(y), "effective_exposures": float(total),
              "mean_people_per_snapshot": float(total / ctx["date_count"]),
              "event_exposures": events, "distinct_people_with_event": distinct_events,
              "capture_percent": 100 * events / y.sum(),
              "observed_percent": 100 * observed, "predicted_percent": 100 * predicted,
              "lift": observed / y.mean(), "aggregate_error_pp": 100 * abs(predicted - observed)}
    if not np.isclose(result["capture_percent"], result["coverage_percent"] * result["lift"]):
        raise RuntimeError("Captura, cobertura y lift no concuerdan.")
    if leaves is None:
        return result, []
    group_error, monthly_error, public_exposure = 0., 0., 0.
    rows = []
    for node in np.unique(leaves[active]):
        mask = (leaves == node) & active
        w = weights[mask]
        size = w.sum()
        ny = float(w @ y[mask])
        npred = float(w @ prediction[mask])
        error = abs(npred - ny) / size * 100
        group_error += abs(npred - ny)
        local_dates = dates[mask]
        residual = np.bincount(local_dates, weights=w * (prediction[mask] - y[mask]), minlength=ctx["date_count"])
        monthly_error += abs(residual).sum()
        counts = np.bincount(local_dates, weights=w, minlength=ctx["date_count"])
        positive = counts[counts > 0]
        event_people = len(np.unique(keys[mask & (y == 1)]))
        safe = bool(len(positive) and positive.min() >= 30 and event_people >= 30)
        row = {"node": int(node), "observed_publishable": safe}
        if safe:
            public_exposure += size
            row.update({"effective_exposures": float(size), "mean_people_per_snapshot": float(size / ctx["date_count"]),
                        "selected_snapshots": int(len(positive)), "minimum_effective_people_selected_snapshot": float(positive.min()),
                        "distinct_people_with_event": event_people, "event_exposures": ny,
                        "observed_percent": 100 * ny / size, "predicted_percent": 100 * npred / size,
                        "error_pp": error})
        rows.append(row)
    public_errors = [r["error_pp"] for r in rows if r["observed_publishable"]]
    result.update({"group_mae_pp": 100 * group_error / total,
                   "group_snapshot_mae_pp": 100 * monthly_error / total,
                   "worst_publishable_group_error_pp": max(public_errors) if public_errors else None,
                   "publishable_group_exposure_percent": 100 * public_exposure / total,
                   "selected_group_count": len(rows)})
    return result, rows


def compare_metrics(actual, expected, tolerance, label):
    diffs = {key: abs(actual[key] - expected[key]) for key in
             ["exposures", "event_exposures", "pr_auc", "lift_at_10_percent", "log_loss",
              "brier_score", "predicted_percent", "observed_percent"]}
    if max(diffs.values()) > tolerance:
        raise RuntimeError(f"No se reproduce {label}; máxima diferencia agregada {max(diffs.values()):.3g}.")
    return {"outcome": "pass", "maximum_absolute_difference": max(diffs.values()), "differences": diffs}


def score_period(frame, predictions, artifacts, capacities):
    ctx = context(frame)
    leaves = {name: apply_rules(frame, artifacts[name]) for name in ["B", "C"]}
    scores = {name: group_scores(leaves[name], artifacts[name]) for name in leaves}
    output, allocations = {}, {}
    for fraction in capacities:
        key = str(int(round(100 * fraction)))
        output[key] = {}
        allocations[key] = {}
        for name in ["B", "C"]:
            w, brackets = policy(frame, scores[name], fraction)
            allocations[key][name] = w
            own, rows = describe(ctx, predictions[name], w, leaves[name])
            if own.get("suppressed"):
                raise RuntimeError("La selección no cumple mínimos de publicación.")
            other = "C" if name == "B" else "B"
            cross, _ = describe(ctx, predictions[other], w, leaves[name])
            individual, _ = policy(frame, predictions[name], fraction)
            individual_metrics, _ = describe(ctx, predictions[name], individual)
            low, _ = describe(ctx, predictions[name], 1 - w, leaves[name])
            output[key][name] = {"metrics": own, "selected_groups": rows,
                                  "same_selection_other_estimator": cross,
                                  "individual_ranking_diagnostic": individual_metrics,
                                  "outside_selection": low,
                                  "whole_group_brackets": brackets}
        output[key]["capture_difference_C_minus_B_pp"] = output[key]["C"]["metrics"]["capture_percent"] - output[key]["B"]["metrics"]["capture_percent"]
    base_key = str(int(round(100 * min(capacities))))
    for key in output:
        if key == base_key:
            continue
        for name in ["B", "C"]:
            incremental = allocations[key][name] - allocations[base_key][name]
            if incremental.min() < -1e-10:
                raise RuntimeError("La ampliación no conserva la prioridad anterior.")
            incremental_metrics, _ = describe(ctx, predictions[name], incremental, leaves[name])
            output[key][name]["increment_above_20_percent"] = incremental_metrics
    return output, allocations


def stability(frame, previous, current, capacities):
    result = {}
    for fraction in capacities:
        key = str(int(round(100 * fraction)))
        result[key] = {}
        for name in ["B", "C"]:
            old = group_scores(apply_rules(frame, previous[name]), previous[name])
            new = group_scores(apply_rules(frame, current[name]), current[name])
            wa, _ = policy(frame, old, fraction)
            wb, _ = policy(frame, new, fraction)
            result[key][name] = float(100 * np.minimum(wa, wb).sum() / wa.sum())
    return result


def capture_intervals(held, capacities, config):
    keys = np.concatenate([item["keys"] for item in held])
    codes, people = pd.factorize(keys, sort=False)
    sums = np.zeros((len(people), len(held), len(capacities) + 1))
    offset = 0
    for i, item in enumerate(held):
        local = codes[offset:offset + len(item["y"])]
        offset += len(local)
        sums[:, i, 0] = np.bincount(local, weights=item["y"], minlength=len(people))
        for j, fraction in enumerate(capacities, 1):
            key = str(int(round(100 * fraction)))
            delta = item["allocations"][key]["C"] - item["allocations"][key]["B"]
            sums[:, i, j] = np.bincount(local, weights=item["y"] * delta, minlength=len(people))
    flat = sums.reshape(len(people), -1)
    rng = np.random.default_rng(config["seed"])
    draws = []
    for _ in range(config["bootstrap_repetitions"]):
        weights = np.bincount(rng.integers(len(people), size=len(people)), minlength=len(people))
        totals = (weights @ flat).reshape(len(held), -1)
        draws.append(np.mean(100 * totals[:, 1:] / totals[:, :1], axis=0))
    draws = np.asarray(draws)
    totals = sums.sum(axis=0)
    point = np.mean(100 * totals[:, 1:] / totals[:, :1], axis=0)
    return {str(int(round(100 * f))): {"difference_C_minus_B_pp": float(point[j]),
                                     "ci95_pp": np.quantile(draws[:, j], [.025, .975]).tolist()}
            for j, f in enumerate(capacities)}


def summarize(folds, intervals, config):
    result = {}
    pref = config["preference_rule"]
    fields = ["capture_percent", "observed_percent", "predicted_percent", "lift", "aggregate_error_pp",
              "group_mae_pp", "group_snapshot_mae_pp", "worst_publishable_group_error_pp",
              "mean_people_per_snapshot", "publishable_group_exposure_percent", "selected_group_count"]
    for fraction in config["capacity_fractions"]:
        key = str(int(round(100 * fraction)))
        row = {name: {field: float(np.mean([fold["scenarios"][key][name]["metrics"][field] for fold in folds]))
                      for field in fields} for name in ["B", "C"]}
        row["capture_interval"] = intervals[key]
        gains = [fold["scenarios"][key]["capture_difference_C_minus_B_pp"] for fold in folds]
        row["capture_wins_C"] = int(sum(bool(g > 1e-8) for g in gains))
        row["capture_wins_B"] = int(sum(bool(g < -1e-8) for g in gains))
        row["capture_ties"] = int(sum(bool(abs(g) <= 1e-8) for g in gains))
        row["C_preference_checks"] = {
            "capture_gain": row["C"]["capture_percent"] > row["B"]["capture_percent"] + 1e-8,
            "temporal_capture": row["capture_wins_C"] >= pref["minimum_capture_winning_folds"],
            "capture_interval": intervals[key]["ci95_pp"][0] > 0,
            "selected_group_error": row["C"]["group_mae_pp"] <= row["B"]["group_mae_pp"] + pref["maximum_selected_group_mae_worsening_pp"],
            "group_snapshot_error": row["C"]["group_snapshot_mae_pp"] <= row["B"]["group_snapshot_mae_pp"] + pref["maximum_group_snapshot_mae_worsening_pp"]}
        row["C_preference_checks"] = {k: bool(v) for k, v in row["C_preference_checks"].items()}
        row["C_preferred_under_rule"] = bool(all(row["C_preference_checks"].values()))
        row["selected_group_error_wins_C"] = int(sum(bool(fold["scenarios"][key]["C"]["metrics"]["group_mae_pp"] < fold["scenarios"][key]["B"]["metrics"]["group_mae_pp"]) for fold in folds))
        row["individual_diagnostic"] = {name: float(np.mean([fold["scenarios"][key][name]["individual_ranking_diagnostic"]["capture_percent"] for fold in folds])) for name in ["B", "C"]}
        row["stability_overlap_percent"] = {name: float(np.mean([fold["stability_from_previous"][key][name] for fold in folds[1:]])) for name in ["B", "C"]}
        result[key] = row
    return result


def finalize_aggregates(config_path):
    """Normalizar escalares de NumPy usando sólo resultados agregados guardados."""
    config = base.read(config_path)
    out = ROOT / config["output"]
    raw = out / "calculation-results.json"
    if not raw.exists():
        shutil.copy2(out / "results.json", raw)
    result = base.read(raw)
    old = result["summary"]
    intervals = {key: s["capture_interval"] for key, s in old.items()}
    result["summary"] = summarize(result["folds"], intervals, config)
    for key, before in old.items():
        after = result["summary"][key]
        if before["B"] != after["B"] or before["C"] != after["C"] or before["C_preferred_under_rule"] != after["C_preferred_under_rule"]:
            raise RuntimeError("La normalización cambió valores numéricos o la decisión previa.")
    base.write(out / "results.json", result)
    base.write(out / "serialization-correction.json", {
        "description": "Normalización de contadores y booleanos NumPy que el serializador genérico exportó como strings. Se conservan todos los valores numéricos y la decisión. Se añade el conteo de periodos ganados en error por grupo.",
        "raw_results_sha256": base.sha(raw), "final_results_sha256": base.sha(out / "results.json"),
        "no_database_query": True, "no_model_refit": True,
        "source_path": str(Path(__file__).relative_to(ROOT)), "source_sha256": base.sha(Path(__file__))})
    target = out / "source-finalization" / "compare_engineering_bc_priority.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), target)
    print("Normalización de tipos completa; métricas y decisión conservadas.")


def run(config_path):
    started = time.perf_counter()
    config = base.read(config_path)
    source = ROOT / config["source_run"]
    out = ROOT / config["output"]
    if (out / "results.json").exists() or (out / "started.json").exists():
        raise RuntimeError("La ejecución ya existe; usar otra configuración.")
    base_config = base.read(source / "frozen-config.json")
    frozen = base.read(source / "frozen-sources.json")
    query = ROOT / base_config["query"]
    if base.sha(query) != frozen[base_config["query"].replace("/", "\\")]:
        raise RuntimeError("Cambió la consulta original.")
    source_manifest = base.read(source / "manifest.json")
    for path in [source / "results.json", *sorted((source / "folds").glob("*.json"))]:
        if base.sha(path) != source_manifest["files"][str(path.relative_to(source))]:
            raise RuntimeError("Cambió un artefacto de la evaluación original.")
    out.mkdir(parents=True, exist_ok=True)
    base.write(out / "frozen-config.json", config)
    # Importar utiliza el código local; congelar hashes y exigir igualdad con la copia de origen.
    paths = [config_path, Path(__file__), ROOT / "tools/engineering_model_c.py",
             ROOT / "tools/engineering_model_c_fast.py", ROOT / "tools/qvoice_model_validation.py",
             query, ROOT / config["authorization"], ROOT / "docs/plans/attrition-bc-priority-comparison-20261008.md"]
    for module in ["tools/engineering_model_c.py", "tools/engineering_model_c_fast.py"]:
        archived = source / "source" / module
        if archived.exists() and base.sha(archived) != base.sha(ROOT / module):
            raise RuntimeError("Cambió el motor respecto al experimento archivado.")
    base.write(out / "frozen-sources.json", {str(path.relative_to(ROOT)): base.sha(path) for path in paths})
    for path in paths:
        target = out / "source" / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    base.log("Cargando la misma población; sólo memoria, cuatro reconstrucciones B.")
    # La conexión ocurre antes del marcador: permite reintentar un bloqueo de red sin sobrescribir resultados.
    with base.db.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
    base.write(out / "started.json", {"started_at": datetime.now(timezone.utc).isoformat(), "status": "running"})
    frame = base.load_frame(base_config)
    load_seconds = time.perf_counter() - started
    base.log(f"Carga terminada en {load_seconds:.1f} s; reconstrucción y comparación de cuatro periodos.")
    population = frame.groupby("snapshot_date").agg(exposures=("person_key", "size"),
                 people=("person_key", "nunique"), monthly_labeled=("y_next", "count"), six_month_labeled=("y_6m", "count")).reset_index()
    original_population = pd.DataFrame(base.read(source / "population.json"))
    original_population["snapshot_date"] = pd.to_datetime(original_population.snapshot_date)
    if not population.equals(original_population):
        raise RuntimeError("Cambió la población o madurez de etiquetas respecto del experimento.")
    base.write(out / "population.json", population.to_dict("records"))
    original = base.read(source / "results.json")
    folds, held = [], []
    previous = None
    for row in original["folds"]:
        fold_start = time.perf_counter()
        i = row["fold"]
        train = base.train_before(frame, row["origin"])
        test = base.evaluation(frame, row["origin"], base_config["outer_snapshots"], base_config["knowledge_boundary"])
        c = restore_model(base.read(source / "folds" / f"fold-{i}-C-model.json"))
        design = base.Design.fit(train, base_config["base_features"], base_config["interactions"])
        x = design.matrix(train)
        b = fast.fit_context(design, x, train.y_next.to_numpy(float), base_config["base_features"], row["B_l2"], base_config)
        models = {"B": b, "C": c}
        predictions = {name: model.risk(test) for name, model in models.items()}
        reproduction = {name: compare_metrics(base.metrics(test, prediction), row[name],
                          config["reproduction_absolute_tolerance"], f"{name} periodo {i}") for name, prediction in predictions.items()}
        _, _, bga = base.make_groups(b, train, base_config)
        artifacts = {"B": bga, "C": row["group_definition"]}
        for name in ["B", "C"]:
            for rule in artifacts[name]["rules"]:
                rule["node"] = int(rule["node"])
            artifacts[name]["high_nodes"] = [int(n) for n in artifacts[name]["high_nodes"]]
            leaf = apply_rules(test, artifacts[name])
            reproduction[name + "_groups"] = compare_metrics(base.metrics(test, group_scores(leaf, artifacts[name])),
                    row["groups"]["ranking_of_frozen_groups"][name], config["reproduction_absolute_tolerance"], f"grupos {name} periodo {i}")
        scenarios, allocations = score_period(test, predictions, artifacts, config["capacity_fractions"])
        result = {"fold": i, "origin": row["origin"], "first_snapshot": row["first_snapshot"],
                  "last_snapshot": row["last_snapshot"], "latest_outcome": row["latest_outcome"],
                  "exposures": len(test), "reproduction": reproduction,
                  "group_definitions": artifacts, "scenarios": scenarios,
                  "stability_from_previous": stability(test.loc[test.snapshot_date == test.snapshot_date.min()], previous,
                        artifacts, config["capacity_fractions"]) if previous else None}
        result["elapsed_seconds"] = time.perf_counter() - fold_start
        folds.append(result)
        held.append({"keys": test.person_key.to_numpy(), "y": test.y_6m.to_numpy(float), "allocations": allocations})
        base.write(out / "folds" / f"fold-{i}.json", result)
        base.write(out / "reconstructed-models" / f"fold-{i}-B.json", b.artifact())
        previous = artifacts
        base.log(f"Periodo {i}/4 completo en {result['elapsed_seconds']:.1f} s; reproduce B, C y sus grupos.")
        del x, train, test
    base.log("Calculando incertidumbre pareada de captura y la extensión de febrero de 2026.")
    intervals = capture_intervals(held, config["capacity_fractions"], config)
    extension_frame = frame.loc[frame.snapshot_date == pd.Timestamp(config["extension_snapshot"])]
    if extension_frame.empty or extension_frame.y_6m.isna().any():
        raise RuntimeError("La foto adicional no tiene seguimiento maduro.")
    ep = {name: model.risk(extension_frame) for name, model in models.items()}
    extension_scenarios, _ = score_period(extension_frame, ep, artifacts, config["capacity_fractions"])
    extension = {"snapshot": config["extension_snapshot"], "followup_end": str(extension_frame.r6_end.max().date()),
                 "model_origin": original["folds"][-1]["origin"], "people": len(extension_frame),
                 "scenarios": extension_scenarios,
                 "interpretation": "Extensión retrospectiva de una foto; modelos y reglas congelados en agosto de 2025. No se suma como quinto periodo comparable ni es holdout virgen."}
    results = {"run_id": config["run_id"], "reporting_mode": config["reporting_mode"],
               "source_run": config["source_run"], "query": base_config["query"],
               "knowledge_boundary": base_config["knowledge_boundary"], "folds": folds,
               "summary": summarize(folds, intervals, config), "extension": extension,
               "bootstrap_repetitions": config["bootstrap_repetitions"], "b_reconstruction_fits": fast.STATS["executed_fits"],
               "c_refits": 0, "load_seconds": load_seconds, "elapsed_seconds": time.perf_counter() - started,
               "employee_level_rows_persisted": False, "individual_scores_published": False,
               "qvoice_included": False}
    base.write(out / "results.json", results)
    base.write(out / "analysis-checks.json", {"population_reproduced": True, "reproductions": [f["reproduction"] for f in folds],
               "capacity_checked_each_snapshot": True, "capture_equals_coverage_times_lift": True,
               "group_rules_cover_without_overlap": True, "mature_labels_only": True,
               "description": "Comprobaciones matemáticas y de reproducción integradas en el cálculo; no son una suite nueva de pruebas de software."})
    manifest = {"run_id": config["run_id"], "reporting_mode": "presentation", "status": "completed_analysis",
                "authorization": config["authorization"], "executed_at": datetime.now(timezone.utc).isoformat(),
                "employee_level_rows_persisted": False, "individual_scores_published": False, "salt_persisted": False,
                "original_models_promoted": False, "files": {str(p.relative_to(out)): base.sha(p) for p in out.rglob("*") if p.is_file() and p.name != "manifest.json"}}
    base.write(out / "manifest.json", manifest)
    base.write(out / "completed.json", {"status": "complete", "elapsed_seconds": results["elapsed_seconds"]})
    base.log(f"Comparación completada en {results['elapsed_seconds']:.1f} s; cuatro ajustes B y cero ajustes C.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT)
    parser.add_argument("--finalize-aggregates", action="store_true")
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.finalize_aggregates:
            finalize_aggregates(args.config.resolve())
        else:
            run(args.config.resolve())
