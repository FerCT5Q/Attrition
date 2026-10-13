"""Efficient direct ablation: H = C minus transfer_12m, and H + QVoice."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import secrets
import shutil
import time

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import compare_engineering_bc_priority as prior
import engineering_model_c as base
import engineering_model_c_qvoice as cq
import qvoice_horizon_calibration as horizon
from qvoice_model_data import load_config


ROOT = base.ROOT
DEFAULT = ROOT / "config/engineering_model_h_without_transfers_20261013.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_spec(source: dict, period_id: str) -> dict:
    return next(row["selected"] for row in source["periods"] if row["id"] == period_id)


def load_frame_in_two_connections(config: dict, source_config: dict, salt: str) -> pd.DataFrame:
    """CQ's loader with one short-lived read-only connection per calendar year."""
    authorization = read(ROOT / config["authorization"])
    if authorization["status"] != "approved" or authorization["non_negotiable_controls"]["disk_cache_of_rows"]:
        raise RuntimeError("La autorización de memoria no está vigente.")
    for name in ["metadata", "region", "comp_ratio_band", "grade_family", "acquisition_recorded", "transfer_12m", "transfer_history"]:
        evidence = read(ROOT / config["source_c"] / "input-evidence" / f"{name}.json")
        if evidence["outcome"] != "pass" or sha(ROOT / evidence["query"]) != evidence["sql_sha256"]:
            raise RuntimeError("Cambió el contrato de entrada de C.")
    original = (ROOT / source_config["query"]).read_text(encoding="utf-8")
    template = (ROOT / config["query"]).read_text(encoding="utf-8")
    start = template.index("  CASE WHEN f.service_date IS NOT NULL AND f.service_date <= DATE '2024-01-01'")
    end = template.index("  COALESCE(f.level_grouped, '(unknown)') AS level_grouped,", start)
    if template[:start] + template[end:] != original:
        raise RuntimeError("La consulta cambió fuera de los indicadores de episodio.")
    expected = {"snapshot_date", "person_key", "label_end", "y_next", "y_6m", "company_tenure_band", "tenure_julia_band",
                "same_episode_2024", "same_episode_2025", "same_episode_2026"} | set(base.raw_features(source_config))
    parts = []
    for year in [2025, 2026]:
        tick = time.perf_counter()
        end_date = min(f"{year}-12-31", config["knowledge_boundary"])
        sql = base.db.validate_readonly(template.replace("__PERIOD_START__", f"{year}-01-01").replace("__PERIOD_END__", end_date).replace("__RUN_SALT__", salt))
        with base.db.connect() as conn:
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor() as cursor:
                cursor.execute(sql)
                columns = [column[0] for column in cursor.description]
                if set(columns) != expected or set(columns) & base.db.SENSITIVE_OUTPUT_COLUMNS:
                    raise RuntimeError("Columnas fuera del contrato autorizado.")
                while True:
                    rows = cursor.fetchmany(50000)
                    if not rows:
                        break
                    part = pd.DataFrame(rows, columns=columns).drop(columns=["company_tenure_band", "tenure_julia_band"])
                    for feature in base.raw_features(source_config):
                        part[feature] = part[feature].astype("category")
                    parts.append(part)
        base.log(f"Carga {year} en RAM: {time.perf_counter()-tick:.1f} s.")
    frame = pd.concat(parts, ignore_index=True)
    for field in ["snapshot_date", "label_end"]:
        frame[field] = pd.to_datetime(frame[field])
    for feature in base.raw_features(source_config):
        frame[feature] = frame[feature].astype("category")
    frame["calendar_month"] = frame.snapshot_date.dt.month.astype(str).astype("category")
    frame["r6_end"] = frame.snapshot_date + pd.DateOffset(months=6)
    if frame.duplicated(["person_key", "snapshot_date"]).any() or frame.loc[frame.label_end.isna(), "y_next"].notna().any():
        raise RuntimeError("Grano o etiquetas mensuales inválidos.")
    if frame.loc[frame.r6_end > pd.Timestamp(config["knowledge_boundary"]), "y_6m"].notna().any():
        raise RuntimeError("Existe etiqueta R6 inmadura.")
    if any(not frame[label].dropna().isin([0, 1]).all() for label in ["y_next", "y_6m"]):
        raise RuntimeError("Etiquetas no binarias.")
    if any(not frame[f"same_episode_{year}"].isin([0, 1]).all() for year in [2024, 2025, 2026]):
        raise RuntimeError("Indicador de episodio inválido.")
    return frame


def summarize(periods: list[dict], names: list[str], config: dict) -> dict:
    output = {}
    for name in names:
        entries = [period["evaluation"][name] for period in periods]
        global_metrics = {key: float(np.mean([e["global"][key] for e in entries]))
                          for key, value in entries[0]["global"].items()
                          if isinstance(value, (float, int, np.number))}
        scenarios = {}
        for fraction in config["capacity_fractions"]:
            cap = str(int(fraction * 100))
            metrics = [e["scenarios"][cap]["metrics"] for e in entries]
            scenarios[cap] = {key: float(np.mean([m[key] for m in metrics]))
                              for key, value in metrics[0].items()
                              if isinstance(value, (float, int, np.number))}
        output[name] = {"global": global_metrics, "scenarios": scenarios}
    return output


def paired_intervals(held: list[dict], config: dict) -> list[dict]:
    """500 person-cluster resamples shared by all compared estimators."""
    all_keys = np.concatenate([row["keys"] for row in held])
    codes, people = pd.factorize(all_keys, sort=False)
    pairs = [("H", "C"), ("HQ", "CQ")]
    metrics = ["capture20", "capture30", "capture40", "log_loss", "brier_score"]
    width = 2 + len(pairs) * len(metrics)
    cells = np.zeros((len(people), len(held), width))
    cursor = 0
    for period, row in enumerate(held):
        index = codes[cursor: cursor + len(row["y"])]
        cursor += len(index)
        cells[:, period, 0] = np.bincount(index, weights=row["y"], minlength=len(people))
        cells[:, period, 1] = np.bincount(index, minlength=len(people))
        losses = {name: horizon.binary_losses(row["y"], values) for name, values in row["predictions"].items()}
        for column, ((left, right), metric) in enumerate(itertools.product(pairs, metrics), 2):
            if metric.startswith("capture"):
                capacity = metric.replace("capture", "")
                values = row["y"] * (row["allocations"][capacity][left] - row["allocations"][capacity][right]) * 100
            else:
                values = losses[left][metric] - losses[right][metric]
            cells[:, period, column] = np.bincount(index, weights=values, minlength=len(people))
    denominators = [0 if metric.startswith("capture") else 1 for _, metric in itertools.product(pairs, metrics)]
    rng = np.random.default_rng(config["seed"])
    flat = cells.reshape(len(people), -1)
    samples = []
    for _ in range(config["bootstrap_repetitions"]):
        weights = np.bincount(rng.integers(len(people), size=len(people)), minlength=len(people))
        total = (weights @ flat).reshape(len(held), width)
        samples.append(np.mean(total[:, 2:] / total[:, denominators], axis=0))
    total = cells.sum(axis=0)
    point = np.mean(total[:, 2:] / total[:, denominators], axis=0)
    bounds = np.quantile(np.asarray(samples), [0.025, 0.975], axis=0)
    return [{"left": pair[0], "right": pair[1], "metric": metric, "difference": float(point[i]),
             "ci95": [float(x) for x in bounds[:, i]]}
            for i, (pair, metric) in enumerate(itertools.product(pairs, metrics))]


def report(config: dict, result: dict) -> str:
    summary = result["summary"]
    values = {}
    for name in ["B", "C", "H", "CQ", "HQ"]:
        global_metrics, cap = summary[name]["global"], summary[name]["scenarios"]["30"]
        values[name] = (f"| {name} | {global_metrics['log_loss']*1000:.1f} | {global_metrics['brier_score']*1000:.1f} | "
                        f"{global_metrics['pr_auc']*100:.1f}% | {cap['capture_percent']:.1f}% | {cap['group_snapshot_mae_pp']:.1f} pp |")
    interval = {(x["left"], x["right"], x["metric"]): x for x in result["intervals"]}
    h, hq = interval[("H", "C", "capture30")], interval[("HQ", "CQ", "capture30")]
    lines = [
        "# B, H = C sin Transfers y H + QVoice", "", "Modo: `presentation`.", "",
        "## Métricas retrospectivas", "",
        "| Modelo | Log-loss × 1,000 ↓ | Brier × 1,000 ↓ | PR-AUC ↑ | Captura al 30% ↑ | Error de grupo ↓ |",
        "|---|---:|---:|---:|---:|---:|", values["B"], values["C"], values["H"], values["CQ"], values["HQ"], "",
        "B se restaura desde el artefacto historico sin reajuste. En estos dos periodos presenta un intercambio frente a C: menor log-loss y error de grupo, pero menor captura y PR-AUC. Esta referencia corta no sustituye la seleccion historica B a C.",
        f"H menos C en captura al 30%: {h['difference']:.2f} pp, IC95 [{h['ci95'][0]:.2f}, {h['ci95'][1]:.2f}].",
        f"H + QVoice menos CQ en captura al 30%: {hq['difference']:.2f} pp, IC95 [{hq['ci95'][0]:.2f}, {hq['ci95'][1]:.2f}].", "",
        "## Método y límite", "",
        "Se retiró sólo `transfer_12m`, que representa una transferencia efectiva en los 12 meses anteriores a la foto. "
        "`transfer_history` nunca fue predictor de C. Se mantuvieron las variables restantes, la penalización, el origen "
        "de C (1-ago-2025), las personas, periodos, grupos y capacidades. H reajusta sus coeficientes; H + QVoice "
        "mantiene por periodo los bloques QVoice y L2 ya seleccionados por CQ y reajusta esa corrección sobre H.", "",
        "No se repitió la búsqueda de variables ni de combinaciones QVoice: es una ablación retrospectiva, no una selección "
        "de un nuevo modelo. C y CQ se reprodujeron antes de interpretar la comparación. Los intervalos usan 500 remuestreos "
        "pareados por persona."
    ]
    return "\n".join(lines) + "\n"


def run(config_path: Path) -> None:
    started = time.perf_counter()
    config = read(config_path)
    out = ROOT / config["output"]
    if out.exists():
        raise RuntimeError(f"No se sobrescribe una ejecución existente: {out}")
    out.mkdir(parents=True)
    write(out / "started.json", {"status": "running", "started_at": datetime.now(timezone.utc)})
    write(out / "frozen-config.json", config)
    files = [config_path, Path(__file__), ROOT / config["query"], ROOT / config["authorization"],
             ROOT / config["source_qvoice_config"], ROOT / config["source_c"] / "frozen-config.json",
             ROOT / config["source_c"] / "folds" / "fold-4-C-model.json", ROOT / config["source_b"],
             ROOT / config["source_cq"] / "results.json"]
    write(out / "frozen-sources.json", {str(path.relative_to(ROOT)): sha(path) for path in files})
    for path in files:
        target = out / "source" / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

    source_c_config = read(ROOT / config["source_c"] / "frozen-config.json")
    source_cq = read(ROOT / config["source_cq"] / "results.json")
    qconfig = load_config(ROOT / config["source_qvoice_config"])
    metadata = read(ROOT / config["source_qvoice"] / "preflight" / "source-metadata.json")
    salt = secrets.token_hex(32)
    base.log("Carga única 2025–2026; H elimina sólo transfer_12m al ajustar el hazard.")
    frame = load_frame_in_two_connections(config, source_c_config, salt)
    population = frame.groupby("snapshot_date").agg(exposures=("person_key", "size"), people=("person_key", "nunique"),
        monthly_labeled=("y_next", "count"), six_month_labeled=("y_6m", "count")).reset_index()
    expected_population = pd.DataFrame(read(ROOT / config["source_cq"] / "population.json"))
    expected_population["snapshot_date"] = pd.to_datetime(expected_population["snapshot_date"])
    if not population.equals(expected_population):
        raise RuntimeError("Población o madurez distinta de CQ.")
    write(out / "population.json", population.to_dict("records"))
    q_features = list(dict.fromkeys([f for block in qconfig["search"]["blocks"].values() for f in block] + qconfig["search"]["pca_items"]))
    timing: dict = {}
    frame = horizon.attach_selected(frame, qconfig, metadata, salt, q_features, timing)
    del salt
    for feature in q_features:
        frame["av_" + feature] = pd.Series(np.where(frame[feature].astype(str).isin(cq.VALID), "available", frame[feature].astype(str)), index=frame.index).astype("category")
    expected_wave = (frame.snapshot_date.dt.year - 1).astype(str).to_numpy()
    if not (frame.qvoice_wave.astype(str).to_numpy() == expected_wave).all():
        raise RuntimeError("QVoice no respeta la regla anual.")

    b_artifact = read(ROOT / config["source_b"])
    b_model = prior.restore_model(b_artifact)
    if b_model.features != source_c_config["base_features"]:
        raise RuntimeError("El artefacto B no coincide con la base hist?rica compatible de C.")
    c_artifact = read(ROOT / config["source_c"] / "folds" / "fold-4-C-model.json")
    c_model = prior.restore_model(c_artifact)
    h_features = [feature for feature in c_model.features if feature not in config["removed_predictors"]]
    if len(h_features) != len(c_model.features) - len(config["removed_predictors"]):
        raise RuntimeError("El predictor solicitado no pertenece a C.")
    train = base.train_before(frame, config["base_origin"])
    design = base.Design.fit(train, h_features, source_c_config["interactions"])
    h_model = base.fit_context(design, design.matrix(train), train.y_next.to_numpy(float), h_features, c_model.l2, source_c_config)
    write(out / "trained-model" / "model-h.json", {**h_model.artifact(), "name": "H = C − Transfers",
        "removed_predictors": config["removed_predictors"], "base_origin": config["base_origin"],
        "fit_maximum_label_end": str(train.label_end.max().date()), "status": "retrospective_ablation_not_selected"})

    monthly, direct = frame.loc[frame.y_next.notna()], frame.loc[frame.y_6m.notna()]
    periods, held, reproductions = [], [], []
    for period in config["periods"]:
        test = direct.loc[(direct.snapshot_date >= pd.Timestamp(period["origin"])) & (direct.snapshot_date <= pd.Timestamp(period["end"]))]
        if test.snapshot_date.nunique() != period["snapshots"]:
            raise RuntimeError(f"Periodo externo incompleto: {period['id']}")
        q_train = monthly.loc[monthly.label_end <= pd.Timestamp(period["origin"])]
        spec = selected_spec(source_cq, period["id"])
        original_fit, h_fit = cq.fit_corrections(q_train, c_model, spec), cq.fit_corrections(q_train, h_model, spec)
        original, without_transfer = cq.predictions(c_model, test, original_fit, spec), cq.predictions(h_model, test, h_fit, spec)
        pred = {"B": b_model.risk(test), "C": original["C"], "CQ": original["CQ"],
                "H": without_transfer["C"], "HQ": without_transfer["CQ"]}
        evaluation, allocations = cq.evaluate(test, pred, config)
        archived = next(row for row in source_cq["periods"] if row["id"] == period["id"])["evaluation"]
        check = {name: {"log_loss_difference": float(evaluation[name]["global"]["log_loss"] - archived[name]["global"]["log_loss"]),
                         "brier_difference": float(evaluation[name]["global"]["brier_score"] - archived[name]["global"]["brier_score"]),
                         "capture30_difference_pp": float(evaluation[name]["scenarios"]["30"]["metrics"]["capture_percent"] - archived[name]["scenarios"]["30"]["metrics"]["capture_percent"])}
                 for name in ["C", "CQ"]}
        if any(abs(v) > 1e-8 for item in check.values() for v in item.values()):
            raise RuntimeError(f"C/CQ no se reprodujeron en {period['id']}: {check}")
        record = {**period, "first_snapshot": str(test.snapshot_date.min().date()), "last_snapshot": str(test.snapshot_date.max().date()),
                  "latest_outcome": str(test.r6_end.max().date()), "exposures": int(len(test)), "people": int(test.person_key.nunique()),
                  "qvoice_spec_reused": spec, "evaluation": evaluation, "reproduction": check}
        write(out / "folds" / period["id"] / "evaluation.json", record)
        periods.append(record)
        held.append({"keys": test.person_key.to_numpy(), "y": test.y_6m.to_numpy(float), "predictions": pred, "allocations": allocations})
        reproductions.append({"period": period["id"], **check})
        base.log(f"{period['id']} completado; se reutilizó QVoice {spec['id']}.")

    result = {"run_id": config["run_id"], "reporting_mode": config["reporting_mode"], "method": config["method"],
              "transfer_definition": config["transfer_definition"], "removed_predictors": config["removed_predictors"],
              "periods": periods, "summary": summarize(periods, ["B", "C", "H", "CQ", "HQ"], config),
              "intervals": paired_intervals(held, config), "reproduction": reproductions,
              "B_artifact_reused_without_refit": config["source_b"],
              "base_hazard_refits": 1, "qvoice_correction_refits": 4, "employee_level_rows_persisted": False,
              "individual_scores_published": False, "elapsed_seconds": time.perf_counter() - started,
              "status": "retrospective_ablation_not_model_selection"}
    write(out / "results.json", result)
    (out / "informe.md").write_text(report(config, result), encoding="utf-8")
    write(out / "verification.json", {"population_matches_CQ": True, "archived_C_and_CQ_reproduced": True,
        "transfer_12m_absent_from_H": "transfer_12m" not in h_model.features,
        "archived_B_restored_on_same_population": True, "same_base_origin": config["base_origin"],
        "same_periods_and_groups": True, "bootstrap_repetitions": config["bootstrap_repetitions"],
        "employee_level_rows_persisted": False, "individual_scores_published": False})
    write(out / "completed.json", {"status": "completed_analysis", "seconds": result["elapsed_seconds"]})
    write(out / "manifest.json", {"run_id": config["run_id"], "status": "completed_analysis", "executed_at": datetime.now(timezone.utc),
        "authorization": config["authorization"], "employee_level_rows_persisted": False, "individual_scores_published": False,
        "salt_persisted": False, "files": {str(path.relative_to(out)): sha(path) for path in out.rglob("*") if path.is_file() and path.name != "manifest.json"}})
    base.log(f"H terminado en {result['elapsed_seconds']:.1f} s; 1 ajuste base y 4 correcciones QVoice.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(args.config.resolve())


if __name__ == "__main__":
    main()
