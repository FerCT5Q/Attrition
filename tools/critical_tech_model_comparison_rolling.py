"""Comparación rolling-origin de hazard, logística y LightGBM en Critical Tech.

Corrige la limitación del holdout único (``critical_tech_lightgbm_challenger``):
el reajuste final de aquel diseño usaba filas a seis meses cuyo outcome caía
dentro del holdout. Aquí cada fold sólo entrena con etiquetas conocidas antes
del inicio de su ventana de prueba:

- hazard mensual: snapshots ``< T`` (la salida al siguiente snapshot ya ocurrió);
- logística y LightGBM a seis meses: snapshots ``<= T - 6 meses``;
- hiperparámetros elegidos por Brier en una validación interna de seis
  snapshots previa a ``T - 6 meses``, con la misma regla de etiquetas conocidas.

Modelos: hazard ``cloglog`` aditivo (champion), hazard con interacciones
preespecificadas segmento×antigüedad y segmento×nivel (tomadas del screen de
cohortes del 2026-09-07), logística directa, LightGBM y promedio histórico.

Sólo se consultan y conservan agregados; no se persisten filas employee-level
ni el frame agregado de entrenamiento.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import critical_tech_discrete_hazard_model as hz  # noqa: E402
import critical_tech_lightgbm_challenger as ch  # noqa: E402

ROOT = hz.ROOT
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "critical-tech" / "20260930" / "model-comparison-rolling-v1"
FOLD_STARTS = ["2024-02-01", "2024-08-01", "2025-02-01", "2025-08-01"]
FOLD_SNAPSHOTS = 6
L2_GRID = [0.0, 0.01, 0.1, 1.0, 10.0]
ADDITIVE = hz.FEATURES
INTERACTION = hz.FEATURES + ["seg_x_tenure", "seg_x_level"]
MODEL_KEYS = ["hazard", "hazard_interactions", "logistic", "lightgbm", "historical"]


def add_interactions(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["seg_x_tenure"] = result["seg"] + " | " + result["company_tenure_band"]
    result["seg_x_level"] = result["seg"] + " | " + result["level_grouped"]
    return result


def before(frame: pd.DataFrame, cutoff: pd.Timestamp, inclusive: bool) -> pd.DataFrame:
    mask = frame["snapshot_date"] <= cutoff if inclusive else frame["snapshot_date"] < cutoff
    selected = frame.loc[mask]
    if selected.empty:
        raise RuntimeError(f"Sin datos antes de {cutoff}.")
    return selected


def fit_hazard(train: pd.DataFrame, features: list[str], l2: float) -> hz.IRLSModel:
    return hz.fit_irls(train, "cloglog", l2, hz.DesignEncoder.fit(train, features))


def fit_logistic(train: pd.DataFrame, l2: float) -> hz.IRLSModel:
    return hz.fit_irls(train, "logit", l2, hz.DesignEncoder.fit(train))


def choose_l2(fit, predict, validation: pd.DataFrame) -> tuple[float, list[dict]]:
    rows = []
    best = None
    for l2 in L2_GRID:
        model = fit(l2)
        score = hz.brier_score(validation, predict(model, validation))
        rows.append({"l2": l2, "validation_brier_score": round(float(score), 8)})
        if best is None or score < best[0]:
            best = (score, l2)
    return best[1], rows


def run_fold(
    monthly: pd.DataFrame, direct: pd.DataFrame, test_dates: list[pd.Timestamp]
) -> tuple[dict, dict]:
    start = test_dates[0]
    six_cutoff = start - pd.DateOffset(months=6)
    direct_dates = sorted(direct["snapshot_date"].unique())
    validation_dates = [d for d in direct_dates if d <= six_cutoff][-6:]
    validation_start = pd.Timestamp(validation_dates[0])
    inner_six_cutoff = validation_start - pd.DateOffset(months=6)

    validation = direct[direct["snapshot_date"].isin(validation_dates)]
    inner_monthly = before(monthly, validation_start, inclusive=False)
    inner_direct = before(direct, inner_six_cutoff, inclusive=True)
    final_monthly = before(monthly, start, inclusive=False)
    final_direct = before(direct, six_cutoff, inclusive=True)
    test = direct[direct["snapshot_date"].isin(test_dates)]

    selection = {}
    hazard_l2, selection["hazard"] = choose_l2(
        lambda l2: fit_hazard(inner_monthly, ADDITIVE, l2), hz.six_month_predictions, validation
    )
    inter_l2, selection["hazard_interactions"] = choose_l2(
        lambda l2: fit_hazard(inner_monthly, INTERACTION, l2), hz.six_month_predictions, validation
    )
    logistic_l2, selection["logistic"] = choose_l2(
        lambda l2: fit_logistic(inner_direct, l2), lambda m, f: m.predict(f), validation
    )
    categories = ch.categories_from(direct)
    lgb_params, lgb_rounds, lgb_candidates = ch.select_lightgbm(inner_direct, validation, categories)
    selection["lightgbm"] = lgb_candidates

    hazard = fit_hazard(final_monthly, ADDITIVE, hazard_l2)
    hazard_inter = fit_hazard(final_monthly, INTERACTION, inter_l2)
    logistic = fit_logistic(final_direct, logistic_l2)
    booster = ch.fit_lightgbm(final_direct, categories, lgb_params, lgb_rounds)
    train_rate = float(final_direct["event_count"].sum() / final_direct["exposure_count"].sum())

    predictions = {
        "hazard": hz.six_month_predictions(hazard, test),
        "hazard_interactions": hz.six_month_predictions(hazard_inter, test),
        "logistic": logistic.predict(test),
        "lightgbm": ch.lgb_predict(booster, test, categories),
        "historical": np.full(len(test), train_rate, dtype=float),
    }
    fold = {
        "test_start": str(start.date()),
        "test_end": str(test_dates[-1].date()),
        "test_snapshots": len(test_dates),
        "validation_start": str(validation_start.date()),
        "validation_end": str(pd.Timestamp(validation_dates[-1]).date()),
        "monthly_train_last_snapshot": str(final_monthly["snapshot_date"].max().date()),
        "six_month_train_last_snapshot": str(final_direct["snapshot_date"].max().date()),
        "chosen": {
            "hazard_l2": hazard_l2,
            "hazard_interactions_l2": inter_l2,
            "logistic_l2": logistic_l2,
            "lightgbm": {**lgb_params, "rounds": lgb_rounds},
        },
        "selection": selection,
        "metrics": {key: hz.metrics(test, values) for key, values in predictions.items()},
    }
    models = {
        "hazard": hazard,
        "hazard_interactions": hazard_inter,
        "booster": booster,
        "categories": categories,
        "final_monthly": final_monthly,
        "test": test,
        "predictions": predictions,
        "train_rate": train_rate,
    }
    return fold, models


def summarize(folds: list[dict]) -> dict:
    summary = {}
    for key in MODEL_KEYS:
        values = [fold["metrics"][key] for fold in folds]
        summary[key] = {
            metric: {
                "mean": round(float(np.mean([v[metric] for v in values])), 8),
                "by_fold": [round(float(v[metric]), 8) for v in values],
            }
            for metric in ["brier_score", "log_loss", "pr_auc", "lift_at_10_percent", "lift_at_20_percent"]
        }
    wins = {}
    for key in ["hazard_interactions", "logistic", "lightgbm"]:
        wins[key] = {
            "pr_auc_folds_won_vs_hazard": sum(
                f["metrics"][key]["pr_auc"] > f["metrics"]["hazard"]["pr_auc"] for f in folds
            ),
            "lift10_folds_won_vs_hazard": sum(
                f["metrics"][key]["lift_at_10_percent"] > f["metrics"]["hazard"]["lift_at_10_percent"]
                for f in folds
            ),
            "brier_folds_not_worse_vs_hazard": sum(
                f["metrics"][key]["brier_score"] <= f["metrics"]["hazard"]["brier_score"] for f in folds
            ),
            "fold_count": len(folds),
        }
    summary["wins_vs_hazard"] = wins
    return summary


def worked_example(model: hz.IRLSModel, start: pd.Timestamp) -> list[dict]:
    """Riesgo a seis meses para perfiles de ejemplo, calculado con el modelo final."""
    references = model.encoder.references
    profiles = [
        ("referencia", {}),
        ("antigüedad 3-7 años", {"company_tenure_band": "3-7 years"}),
        ("antigüedad 1-3 años", {"company_tenure_band": "1-3 years"}),
        ("3-7 años + cambio de manager", {"company_tenure_band": "3-7 years", "manager_change_12m": "yes"}),
    ]
    rows = []
    for label, overrides in profiles:
        if any(feature not in model.encoder.features for feature in overrides):
            continue
        values = {feature: references[feature] for feature in model.encoder.features if feature != "calendar_month"}
        values.update(overrides)
        if any(value not in model.encoder.categories[feature] for feature, value in values.items()):
            continue
        frame = pd.DataFrame([{**values, "snapshot_date": start}])
        frame["calendar_month"] = frame["snapshot_date"].dt.month.astype(str)
        monthly = []
        for ahead in range(6):
            part = frame.copy()
            part["snapshot_date"] = part["snapshot_date"] + pd.DateOffset(months=ahead)
            part["calendar_month"] = part["snapshot_date"].dt.month.astype(str)
            monthly.append(float(model.predict(part)[0]))
        rows.append(
            {
                "profile": label,
                "levels": values,
                "first_month": str(start.date()),
                "monthly_hazard_percent": [round(100.0 * h, 4) for h in monthly],
                "six_month_risk_percent": round(100.0 * (1.0 - float(np.prod([1.0 - h for h in monthly]))), 4),
            }
        )
    return rows


def run_scope(name: str, monthly: pd.DataFrame, direct: pd.DataFrame) -> dict:
    monthly = add_interactions(monthly)
    direct = add_interactions(direct)
    dates = sorted(direct["snapshot_date"].unique())
    folds = []
    last_models = None
    for index, raw_start in enumerate(FOLD_STARTS):
        start = pd.Timestamp(raw_start)
        test_dates = [pd.Timestamp(d) for d in dates if d >= start]
        is_last = index == len(FOLD_STARTS) - 1
        test_dates = test_dates if is_last else test_dates[:FOLD_SNAPSHOTS]
        fold, models = run_fold(monthly, direct, test_dates)
        folds.append(fold)
        print(f"{name} fold {fold['test_start']}: listo", file=sys.stderr, flush=True)
        last_models = models
    assert last_models is not None
    hazard = last_models["hazard"]
    test = last_models["test"]
    predictions = last_models["predictions"]
    return {
        "scope": name,
        "exposures": {
            "monthly": int(monthly["exposure_count"].sum()),
            "monthly_events": int(monthly["event_count"].sum()),
            "six_month": int(direct["exposure_count"].sum()),
            "six_month_events": int(direct["event_count"].sum()),
        },
        "folds": folds,
        "summary": summarize(folds),
        "last_fold": {
            "one_way_fit": {
                feature: ch.one_way_fit(test, predictions, feature)
                for feature in ["company_tenure_band", "seg", "level_grouped", "manager_change_12m"] if feature in test
            },
            "cohorts_segment_tenure": {
                key: hz.cohort_table(test, predictions[key], ["seg", "company_tenure_band"], last_models["train_rate"], limit=40)
                for key in ["hazard", "hazard_interactions", "logistic", "lightgbm"]
            },
            "cohorts_segment_level": {
                key: hz.cohort_table(test, predictions[key], ["seg", "level_grouped"], last_models["train_rate"], limit=40)
                for key in ["hazard", "hazard_interactions", "logistic", "lightgbm"]
            },
            "hazard_coefficients": hz.coefficient_summary(hazard, last_models["final_monthly"], limit=80),
            "hazard_reference_levels": hazard.encoder.references,
            "hazard_parameter_count": int(len(hazard.beta)),
            "hazard_interactions_parameter_count": int(len(last_models["hazard_interactions"].beta)),
            "hazard_trend_ratio_per_year": round(float(np.exp(hazard.beta[1] * 12.0 / hazard.encoder.time_scale)), 6),
            "hazard_worked_example": worked_example(hazard, pd.Timestamp(folds[-1]["test_start"])),
            "lightgbm_gain_importance": ch.gain_importance(last_models["booster"]),
            "lightgbm_tree_count": int(last_models["booster"].num_trees()),
        },
    }


def build_report(result: dict) -> str:
    labels = {
        "hazard": "Hazard cloglog aditivo",
        "hazard_interactions": "Hazard + interacciones",
        "logistic": "Logística directa 6m",
        "lightgbm": "LightGBM 6m",
        "historical": "Promedio histórico",
    }
    lines = [
        "# Comparación rolling-origin de modelos de attrition",
        "",
        f"Creado: {result['created_at_utc']}. Frontera de conocimiento: {result['knowledge_boundary']}.",
        "",
        "Cuatro folds temporales; cada fold entrena sólo con etiquetas conocidas antes de su",
        "ventana de prueba. Sin filas employee-level persistidas.",
        "",
    ]
    for scope in result["scopes"]:
        lines += [f"## Alcance `{scope['scope']}`", ""]
        header = "| Modelo | " + " | ".join(f["test_start"] for f in scope["folds"]) + " | Media |"
        for metric, title in [("pr_auc", "PR-AUC"), ("lift_at_10_percent", "Lift@10%"), ("brier_score", "Brier")]:
            lines += [f"### {title}", "", header, "|---|" + "---:|" * (len(scope["folds"]) + 1)]
            for key in MODEL_KEYS:
                item = scope["summary"][key][metric]
                lines.append(
                    f"| {labels[key]} | " + " | ".join(f"{v:.5f}" for v in item["by_fold"]) + f" | {item['mean']:.5f} |"
                )
            lines.append("")
        lines += ["### Folds ganados frente al hazard aditivo", ""]
        for key, wins in scope["summary"]["wins_vs_hazard"].items():
            lines.append(
                f"- {labels[key]}: PR-AUC {wins['pr_auc_folds_won_vs_hazard']}/{wins['fold_count']}, "
                f"lift@10% {wins['lift10_folds_won_vs_hazard']}/{wins['fold_count']}, "
                f"Brier no peor {wins['brier_folds_not_worse_vs_hazard']}/{wins['fold_count']}."
            )
        lines.append("")
        lines += ["### Eventos por fold", ""]
        for fold in scope["folds"]:
            m = fold["metrics"]["hazard"]
            lines.append(
                f"- {fold['test_start']} a {fold['test_end']}: {m['exposures']} exposiciones, {m['events']} eventos."
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def self_test() -> None:
    rng = np.random.default_rng(11)
    rows = []
    for snapshot in pd.date_range("2021-01-01", "2026-02-01", freq="MS") + pd.Timedelta(days=22):
        for tenure, rate in [("<1 year", 0.02), ("1-3 years", 0.05), ("7+ years", 0.01)]:
            for seg in ["A", "B"]:
                n = 600
                bump = 2.0 if (seg == "B" and tenure == "1-3 years") else 1.0
                rows.append(
                    {
                        "snapshot_date": snapshot,
                        "seg": seg,
                        "level_grouped": "L",
                        "company_tenure_band": tenure,
                        "manager_change_12m": "no",
                        "exposure_count": n,
                        "distinct_employee_count": n,
                        "event_count": int(rng.binomial(n, rate * bump)),
                    }
                )
    direct = hz.prepare_frame(pd.DataFrame(rows), six_month=True)
    monthly = direct.copy()
    monthly["event_count"] = (monthly["event_count"] / 6).round().astype(int)
    monthly["six_month_frame"] = False
    scope = run_scope("synthetic", monthly, direct)
    assert len(scope["folds"]) == len(FOLD_STARTS)
    for fold in scope["folds"]:
        assert fold["six_month_train_last_snapshot"] <= str(
            (pd.Timestamp(fold["test_start"]) - pd.DateOffset(months=6)).date()
        )
        assert fold["monthly_train_last_snapshot"] < fold["test_start"]
    print(json.dumps({"self_test": "ok"}))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    output_dir = args.output_dir if args.output_dir.is_absolute() else (ROOT / args.output_dir)
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"La carpeta de salida ya tiene contenido: {output_dir}")

    original_query = hz.run_readonly_query

    def logged_query(path: Path, max_rows: int = 1000) -> dict:
        payload = original_query(path, max_rows)
        print(f"consulta {path.name}: {len(payload.get('rows', []))} celdas", file=sys.stderr, flush=True)
        return payload

    hz.run_readonly_query = logged_query
    calendar = hz.fetch_calendar()
    monthly_raw, monthly_hash = hz.fetch_frame(hz.MONTHLY_QUERY, calendar, hz.EXPECTED_MONTHLY_COLUMNS)
    direct_dates = [value for value in calendar if value <= hz.HOLDOUT_END]
    direct_raw, direct_hash = hz.fetch_frame(hz.SIX_MONTH_QUERY, direct_dates, hz.EXPECTED_MONTHLY_COLUMNS)
    monthly = hz.prepare_frame(monthly_raw)
    direct = hz.prepare_frame(direct_raw, six_month=True)

    scopes = [
        run_scope(
            "phase1",
            monthly.loc[monthly["seg"] != "Other Eng"].reset_index(drop=True),
            direct.loc[direct["seg"] != "Other Eng"].reset_index(drop=True),
        ),
        run_scope("v2", monthly, direct),
    ]
    import lightgbm

    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "artifact": "critical-tech-model-comparison-rolling",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": hz.KNOWLEDGE_BOUNDARY.strftime("%Y-%m-%d"),
        "deliverable_classification": "presentation",
        "design": {
            "fold_starts": FOLD_STARTS,
            "fold_snapshots": FOLD_SNAPSHOTS,
            "last_fold": "todas las fotos desde el inicio hasta el último snapshot con seis meses de seguimiento",
            "monthly_train_rule": "snapshot < inicio de prueba",
            "six_month_train_rule": "snapshot <= inicio de prueba - 6 meses",
            "selection": "Brier mínimo en seis snapshots de validación interna, con la misma regla de etiquetas conocidas",
            "interaction_terms": ["seg_x_tenure", "seg_x_level"],
            "interaction_source": "output/analysis/critical-tech/20260907/cohort-screen-report.md",
            "l2_grid": L2_GRID,
            "lightgbm_grid": ch.LGB_GRID,
        },
        "lightgbm_version": lightgbm.__version__,
        "frame_sha256": {"monthly": monthly_hash, "six_month": direct_hash},
        "privacy": {
            "employee_level_rows_persisted": False,
            "aggregate_training_frame_persisted": False,
            "individual_scores_published": False,
            "minimum_published_exposures": 30,
            "minimum_published_events": 30,
        },
        "scopes": scopes,
    }
    result_path = output_dir / "comparison-results.json"
    report_path = output_dir / "comparison-report.md"
    manifest_path = output_dir / "comparison-manifest.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    manifest = {
        "artifact": result["artifact"],
        "created_at_utc": result["created_at_utc"],
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "queries": {
            "calendar": str(hz.CALENDAR_QUERY.relative_to(ROOT)),
            "monthly_frame": str(hz.MONTHLY_QUERY.relative_to(ROOT)),
            "six_month_frame": str(hz.SIX_MONTH_QUERY.relative_to(ROOT)),
        },
        "query_sha256": {
            "calendar": hz.sha256_file(hz.CALENDAR_QUERY),
            "monthly_frame": hz.sha256_file(hz.MONTHLY_QUERY),
            "six_month_frame": hz.sha256_file(hz.SIX_MONTH_QUERY),
        },
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": hz.sha256_file(result_path),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": hz.sha256_file(report_path),
        "employee_level_rows_persisted": False,
        "aggregate_training_frame_persisted": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(build_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
