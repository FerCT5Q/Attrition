"""Challenger LightGBM frente al hazard discreto de Critical Tech.

SUPERADO por ``critical_tech_model_comparison_rolling.py`` (30-sep-2026): el
reajuste final de este script usa etiquetas a seis meses que caen dentro de la
ventana de holdout y no reproduce exactamente el baseline del 14-sep. Úsalo
sólo como referencia; la evidencia vigente es la comparación rolling-origin.

Reutiliza las consultas agregadas, ventanas, features y métricas de
``critical_tech_discrete_hazard_model.py``. LightGBM se entrena sobre las
mismas celdas agregadas a seis meses: cada celda se expande en dos filas
ponderadas (eventos con etiqueta 1 y no eventos con etiqueta 0). Así el
modelo optimiza la misma verosimilitud binomial que la logística agrupada sin
requerir filas employee-level.

En la misma ejecución se reajustan hazard ``cloglog``, logística y promedio
histórico para que los cuatro modelos se comparen sobre datos idénticos.

Dos alcances:
    v2: igual al baseline del 2026-09-14 (incluye ``Other Eng``); sirve para
        comprobar que el pipeline reproduce el reporte anterior.
    phase1: alcance vigente de fase 1, sin ``seg = 'Other Eng'``.

No se persisten filas employee-level ni el frame agregado de entrenamiento.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import critical_tech_discrete_hazard_model as hz  # noqa: E402

ROOT = hz.ROOT
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "critical-tech" / "20260930" / "ml-challenger-v1"
REFERENCE_RESULTS = (
    ROOT
    / "output"
    / "analysis"
    / "critical-tech"
    / "20260914"
    / "baseline-v2-calendar-brier"
    / "model-results.json"
)
CATEGORICAL = [
    "seg",
    "level_grouped",
    "company_tenure_band",
    "manager_change_12m",
    "calendar_month",
]
LGB_GRID = {
    "num_leaves": [4, 8, 16],
    "min_sum_hessian_in_leaf": [20.0, 100.0],
    "lambda_l2": [1.0, 10.0],
}
LEARNING_RATE = 0.05
MAX_ROUNDS = 2000
EARLY_STOPPING = 100
SEED = 20260930


def lgb_matrix(frame: pd.DataFrame, categories: dict[str, list[str]]) -> pd.DataFrame:
    data = {}
    for feature in CATEGORICAL:
        values = frame[feature].fillna("(unknown)").astype(str)
        data[feature] = pd.Categorical(values, categories=categories[feature])
    months = frame["snapshot_date"].dt.year * 12 + frame["snapshot_date"].dt.month
    data["time_index"] = months.astype(float).to_numpy()
    return pd.DataFrame(data, index=frame.index)


def expand_binomial(frame: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Expande cada celda en eventos y no eventos ponderados."""
    events = frame["event_count"].to_numpy(dtype=float)
    non_events = frame["exposure_count"].to_numpy(dtype=float) - events
    positives = frame.loc[events > 0]
    negatives = frame.loc[non_events > 0]
    expanded = pd.concat([positives, negatives], ignore_index=True)
    labels = np.concatenate([np.ones(len(positives)), np.zeros(len(negatives))])
    weights = np.concatenate([events[events > 0], non_events[non_events > 0]])
    return expanded, labels, weights


def fit_lightgbm(
    train: pd.DataFrame,
    categories: dict[str, list[str]],
    params: dict,
    rounds: int,
    validation: pd.DataFrame | None = None,
):
    import lightgbm as lgb

    expanded, labels, weights = expand_binomial(train)
    dataset = lgb.Dataset(
        lgb_matrix(expanded, categories),
        label=labels,
        weight=weights,
        categorical_feature=CATEGORICAL,
        free_raw_data=False,
    )
    full_params = {
        "objective": "binary",
        "learning_rate": LEARNING_RATE,
        "min_data_in_leaf": 1,
        "cat_smooth": 10.0,
        "max_cat_to_onehot": 16,
        "feature_fraction": 1.0,
        "bagging_fraction": 1.0,
        "verbosity": -1,
        "seed": SEED,
        "deterministic": True,
        "num_threads": 4,
        **params,
    }
    callbacks = []
    valid_sets = []
    if validation is not None:
        v_expanded, v_labels, v_weights = expand_binomial(validation)
        valid_sets = [
            lgb.Dataset(
                lgb_matrix(v_expanded, categories),
                label=v_labels,
                weight=v_weights,
                categorical_feature=CATEGORICAL,
                reference=dataset,
            )
        ]
        callbacks = [lgb.early_stopping(EARLY_STOPPING, verbose=False)]
    booster = lgb.train(
        full_params,
        dataset,
        num_boost_round=rounds,
        valid_sets=valid_sets,
        callbacks=callbacks,
    )
    return booster


def lgb_predict(booster, frame: pd.DataFrame, categories: dict[str, list[str]]) -> np.ndarray:
    values = booster.predict(lgb_matrix(frame, categories), num_iteration=booster.best_iteration or None)
    return np.clip(np.asarray(values, dtype=float), 1e-8, 1.0 - 1e-8)


def select_lightgbm(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    categories: dict[str, list[str]],
) -> tuple[dict, int, list[dict]]:
    candidates = []
    best = None
    keys = list(LGB_GRID)
    for combo in itertools.product(*(LGB_GRID[key] for key in keys)):
        params = dict(zip(keys, combo))
        booster = fit_lightgbm(train, categories, params, MAX_ROUNDS, validation)
        rounds = int(booster.best_iteration or MAX_ROUNDS)
        predictions = lgb_predict(booster, validation, categories)
        score = hz.brier_score(validation, predictions)
        candidates.append(
            {
                **params,
                "rounds": rounds,
                "validation_brier_score": round(float(score), 8),
                "validation_log_loss": round(hz.log_loss(validation, predictions), 8),
            }
        )
        if best is None or score < best[0]:
            best = (score, params, rounds)
    assert best is not None
    return best[1], best[2], candidates


def categories_from(*frames: pd.DataFrame) -> dict[str, list[str]]:
    combined = pd.concat([frame[CATEGORICAL] for frame in frames], ignore_index=True)
    return {
        feature: sorted(combined[feature].fillna("(unknown)").astype(str).unique().tolist())
        for feature in CATEGORICAL
    }


def gain_importance(booster) -> list[dict]:
    gains = booster.feature_importance(importance_type="gain")
    total = float(np.sum(gains)) or 1.0
    rows = [
        {"feature": name, "gain_share_percent": round(100.0 * float(gain) / total, 4)}
        for name, gain in zip(booster.feature_name(), gains)
    ]
    return sorted(rows, key=lambda item: item["gain_share_percent"], reverse=True)


def one_way_fit(frame: pd.DataFrame, predictions: dict[str, np.ndarray], feature: str) -> list[dict]:
    """Observado vs predicho por categoría de una sola variable (agregado)."""
    data = frame[[feature, "exposure_count", "event_count"]].copy()
    for name, values in predictions.items():
        data[f"pred_{name}"] = values * data["exposure_count"]
    grouped = data.groupby(feature, dropna=False).sum(numeric_only=True).reset_index()
    rows = []
    for _, row in grouped.iterrows():
        exposures = float(row["exposure_count"])
        events = float(row["event_count"])
        if exposures < 30 or events < 30:
            continue
        item = {
            "level": str(row[feature]),
            "exposures": int(exposures),
            "events": int(events),
            "observed_rate_percent": round(100.0 * events / exposures, 4),
        }
        for name in predictions:
            item[f"{name}_predicted_percent"] = round(100.0 * float(row[f"pred_{name}"]) / exposures, 4)
        rows.append(item)
    return rows


def monthly_by_calendar_month(frame: pd.DataFrame, predictions: np.ndarray) -> list[dict]:
    data = frame[["calendar_month", "exposure_count", "event_count"]].copy()
    data["predicted_events"] = predictions * data["exposure_count"]
    grouped = data.groupby("calendar_month").sum(numeric_only=True).reset_index()
    rows = []
    for _, row in grouped.iterrows():
        exposures = float(row["exposure_count"])
        events = float(row["event_count"])
        if exposures < 30 or events < 30:
            continue
        rows.append(
            {
                "calendar_month": int(row["calendar_month"]),
                "exposures": int(exposures),
                "events": int(events),
                "observed_rate_percent": round(100.0 * events / exposures, 4),
                "predicted_rate_percent": round(100.0 * float(row["predicted_events"]) / exposures, 4),
            }
        )
    return sorted(rows, key=lambda item: item["calendar_month"])


def run_scope(name: str, monthly: pd.DataFrame, direct: pd.DataFrame) -> dict:
    l2_grid = [0.0, 0.01, 0.1, 1.0, 10.0]
    train_monthly = hz.subset_dates(monthly, None, hz.TRAIN_END)
    train_direct = hz.subset_dates(direct, None, hz.TRAIN_END)
    validation_direct = hz.subset_dates(direct, hz.VALIDATION_START, hz.VALIDATION_END)
    final_train_monthly = hz.subset_dates(monthly, None, hz.VALIDATION_END)
    final_train_direct = hz.subset_dates(direct, None, hz.VALIDATION_END)
    holdout_monthly = hz.subset_dates(monthly, hz.HOLDOUT_START, hz.HOLDOUT_END)
    holdout_direct = hz.subset_dates(direct, hz.HOLDOUT_START, hz.HOLDOUT_END)

    champion_l2, _, champion_candidates = hz.selection_result(
        "cloglog", train_monthly, validation_direct, l2_grid
    )
    logistic_l2, _, logistic_candidates = hz.selection_result(
        "logit", train_direct, validation_direct, l2_grid
    )
    champion = hz.fit_irls(
        final_train_monthly, "cloglog", champion_l2, hz.DesignEncoder.fit(final_train_monthly)
    )
    logistic = hz.fit_irls(
        final_train_direct, "logit", logistic_l2, hz.DesignEncoder.fit(final_train_direct)
    )

    categories = categories_from(direct)
    lgb_params, lgb_rounds, lgb_candidates = select_lightgbm(
        train_direct, validation_direct, categories
    )
    # Reajuste final con train + validación y el número de rondas elegido.
    lgb_final = fit_lightgbm(final_train_direct, categories, lgb_params, lgb_rounds)

    train_rate = float(
        final_train_direct["event_count"].sum() / final_train_direct["exposure_count"].sum()
    )
    predictions = {
        "hazard": hz.six_month_predictions(champion, holdout_direct),
        "logistic": logistic.predict(holdout_direct),
        "lightgbm": lgb_predict(lgb_final, holdout_direct, categories),
        "historical": np.full(len(holdout_direct), train_rate, dtype=float),
    }
    return {
        "scope": name,
        "exposures": {
            "monthly": int(monthly["exposure_count"].sum()),
            "monthly_events": int(monthly["event_count"].sum()),
            "six_month": int(direct["exposure_count"].sum()),
            "six_month_events": int(direct["event_count"].sum()),
        },
        "selection": {
            "hazard_l2": champion_l2,
            "hazard_candidates": champion_candidates,
            "logistic_l2": logistic_l2,
            "logistic_candidates": logistic_candidates,
            "lightgbm_params": {**lgb_params, "rounds": lgb_rounds, "learning_rate": LEARNING_RATE},
            "lightgbm_candidates": lgb_candidates,
        },
        "final_holdout": {
            "hazard_monthly": hz.metrics(holdout_monthly, champion.predict(holdout_monthly)),
            **{f"{key}_six_month": hz.metrics(holdout_direct, values) for key, values in predictions.items()},
        },
        "one_way_fit": {
            feature: one_way_fit(holdout_direct, predictions, feature)
            for feature in ["company_tenure_band", "seg", "level_grouped", "calendar_month"]
        },
        "cohorts_segment_tenure": {
            key: hz.cohort_table(
                holdout_direct, predictions[key], ["seg", "company_tenure_band"], train_rate, limit=40
            )
            for key in ["hazard", "logistic", "lightgbm"]
        },
        "monthly_hazard_by_calendar_month": monthly_by_calendar_month(
            holdout_monthly, champion.predict(holdout_monthly)
        ),
        "hazard_reference_levels": champion.encoder.references,
        "hazard_trend_ratio_per_year": round(
            float(np.exp(champion.beta[1] * 12.0 / champion.encoder.time_scale)), 6
        ),
        "hazard_baseline_monthly_percent": round(100.0 * float(1.0 - np.exp(-np.exp(champion.beta[0]))), 6),
        "hazard_coefficients": hz.coefficient_summary(champion, final_train_monthly, limit=60),
        "hazard_parameter_count": int(len(champion.beta)),
        "lightgbm_gain_importance": gain_importance(lgb_final),
        "lightgbm_tree_count": int(lgb_final.num_trees()),
    }


def reproduction_check(scope_result: dict) -> dict:
    reference = json.loads(REFERENCE_RESULTS.read_text(encoding="utf-8"))["final_holdout"]
    pairs = {
        "hazard_six_month": "champion_six_month",
        "logistic_six_month": "direct_logistic_six_month",
        "historical_six_month": "historical_baseline_six_month",
    }
    rows = {}
    for ours, theirs in pairs.items():
        new = scope_result["final_holdout"][ours]
        old = reference[theirs]
        rows[ours] = {
            "brier_delta": round(new["brier_score"] - old["brier_score"], 10),
            "pr_auc_delta": round(new["pr_auc"] - old["pr_auc"], 10),
            "events_equal": new["events"] == old["events"],
            "exposures_equal": new["exposures"] == old["exposures"],
        }
    rows["reproduced"] = all(
        abs(item["brier_delta"]) < 1e-7 and item["events_equal"] and item["exposures_equal"]
        for key, item in rows.items()
        if isinstance(item, dict)
    )
    return rows


def self_test() -> None:
    rng = np.random.default_rng(7)
    rows = []
    for snapshot in pd.date_range("2022-01-26", "2026-02-26", freq="MS") + pd.Timedelta(days=25):
        for tenure, rate in [("<1 year", 0.02), ("1-3 years", 0.05), ("7+ years", 0.01)]:
            for seg in ["A", "B"]:
                n = 800
                events = int(rng.binomial(n, rate * (1.5 if seg == "B" else 1.0)))
                rows.append(
                    {
                        "snapshot_date": snapshot,
                        "seg": seg,
                        "level_grouped": "L",
                        "company_tenure_band": tenure,
                        "manager_change_12m": "no",
                        "exposure_count": n,
                        "distinct_employee_count": n,
                        "event_count": events,
                    }
                )
    frame = hz.prepare_frame(pd.DataFrame(rows), six_month=True)
    expanded, labels, weights = expand_binomial(frame)
    assert np.isclose(weights.sum(), frame["exposure_count"].sum())
    assert np.isclose(weights[labels == 1].sum(), frame["event_count"].sum())
    categories = categories_from(frame)
    booster = fit_lightgbm(frame, categories, {"num_leaves": 4, "min_sum_hessian_in_leaf": 20.0, "lambda_l2": 1.0}, 200)
    predictions = lgb_predict(booster, frame, categories)
    by_tenure = frame.assign(p=predictions).groupby("company_tenure_band")["p"].mean()
    assert by_tenure["1-3 years"] > by_tenure["<1 year"] > by_tenure["7+ years"]
    print(json.dumps({"self_test": "ok"}))


def build_report(result: dict) -> str:
    lines = [
        "# Challenger LightGBM frente al hazard discreto",
        "",
        f"Creado: {result['created_at_utc']}. Frontera de conocimiento: {result['knowledge_boundary']}.",
        "",
        "Mismas consultas, features, ventanas y holdout que el baseline v2. LightGBM se",
        "entrena sobre celdas agregadas ponderadas; no se persisten filas employee-level.",
        "",
        f"Reproducción del baseline v2: {'sí' if result['reproduction_check']['reproduced'] else 'no'}.",
        "",
    ]
    for scope in result["scopes"]:
        holdout = scope["final_holdout"]
        lines += [
            f"## Alcance `{scope['scope']}`",
            "",
            "| Modelo | Brier | Log loss | PR-AUC | Lift@10% | Lift@20% |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for key, label in [
            ("hazard_six_month", "Hazard cloglog (champion)"),
            ("logistic_six_month", "Logística directa 6m"),
            ("lightgbm_six_month", "LightGBM 6m"),
            ("historical_six_month", "Promedio histórico"),
        ]:
            m = holdout[key]
            lines.append(
                f"| {label} | {m['brier_score']:.6f} | {m['log_loss']:.5f} | "
                f"{m['pr_auc']:.4f} | {m['lift_at_10_percent']:.3f} | {m['lift_at_20_percent']:.3f} |"
            )
        lines += [
            "",
            f"Holdout: {holdout['hazard_six_month']['exposures']} exposiciones, "
            f"{holdout['hazard_six_month']['events']} eventos.",
            f"LightGBM elegido: {scope['selection']['lightgbm_params']}.",
            "",
        ]
    return "\n".join(lines) + "\n"


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
    output_dir.mkdir(parents=True, exist_ok=True)

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

    scopes = [run_scope("v2", monthly, direct)]
    scopes.append(
        run_scope(
            "phase1",
            monthly.loc[monthly["seg"] != "Other Eng"].reset_index(drop=True),
            direct.loc[direct["seg"] != "Other Eng"].reset_index(drop=True),
        )
    )
    import lightgbm

    result = {
        "artifact": "critical-tech-lightgbm-challenger",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": hz.KNOWLEDGE_BOUNDARY.strftime("%Y-%m-%d"),
        "deliverable_classification": "presentation",
        "features": CATEGORICAL + ["time_index"],
        "windows": {
            "train_end": str(hz.TRAIN_END.date()),
            "validation_start": str(hz.VALIDATION_START.date()),
            "validation_end": str(hz.VALIDATION_END.date()),
            "holdout_start": str(hz.HOLDOUT_START.date()),
            "holdout_end": str(hz.HOLDOUT_END.date()),
        },
        "selection_criterion": "Brier mínimo en validación temporal a seis meses; reajuste final con train + validación",
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
        "reproduction_check": reproduction_check(scopes[0]),
    }
    result_path = output_dir / "challenger-results.json"
    report_path = output_dir / "challenger-report.md"
    manifest_path = output_dir / "challenger-manifest.json"
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
    print(build_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
