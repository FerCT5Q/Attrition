"""Selección de variables por bloques para el hazard de Engineering (2026-10-01).

Carga el frame persona-mes en memoria (sin persistir filas ni IDs) bajo
``config/attrition_model_in_memory_training_authorization_20261001.json``,
lo colapsa a celdas exactas snapshot × variables y evalúa, con los mismos
cuatro folds rolling-origin del champion, una selección hacia delante por
bloques del hazard discreto ``cloglog``:

- base: nivel, antigüedad, mes calendario y tendencia;
- carrera: promoción en los últimos 12 meses;
- manager/equipo: cambios de manager, salidas voluntarias del equipo y
  reportes directos;
- geografía: región;
- compensación: banda de compa-ratio y familia de grado.

Regla de parsimonia: se elige la especificación con menos bloques cuyo
PR-AUC y lift@10% medios estén a menos de 2% relativo de la mejor. LightGBM
con todas las variables sirve como techo no lineal. Los grupos publicables
salen de un árbol poco profundo (profundidad <= 3) sobre el riesgo estimado
de la foto más reciente, con hojas de al menos 300 personas.

Sólo se escriben agregados: métricas, coeficientes y grupos >= 30 personas
(observado sólo con >= 30 salidas).
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import critical_tech_discrete_hazard_model as hz  # noqa: E402
import critical_tech_lightgbm_challenger as ch  # noqa: E402
import critical_tech_model_comparison_rolling as ro  # noqa: E402

ROOT = hz.ROOT
HELPER_DIR = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts"
FRAME_QUERY = ROOT / "queries" / "profiles" / "engineering_person_month_features_20261001.sql"
AUTHORIZATION = ROOT / "config" / "attrition_model_in_memory_training_authorization_20261001.json"
AUDITS = [
    ROOT / "queries" / "audits" / "engineering_candidate_feature_coverage_by_year_20261001.sql",
    ROOT / "queries" / "audits" / "engineering_candidate_feature_categories_20261001.sql",
    ROOT / "queries" / "audits" / "engineering_promotion_history_by_year_20261001.sql",
    ROOT / "queries" / "audits" / "engineering_event_flags_history_20261001.sql",
    ROOT / "queries" / "audits" / "manager_change_flag_vs_date_engineering_20261001.sql",
]
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "engineering" / "20261001" / "feature-block-selection-v1"
# Las ventanas de 12 meses sólo están completas desde 2021-07 (la tabla empieza en 2020-07).
MIN_SNAPSHOT = pd.Timestamp("2021-07-25")
SNAPSHOTS_PER_QUERY = 3

BASE = ["level_grouped", "company_tenure_band", "calendar_month"]
BLOCKS = {
    "carrera": ["promo_12m"],
    "manager_equipo": ["manager_changes_12m", "team_exits_12m", "direct_reports_band"],
    "geografia": ["region"],
    "compensacion": ["comp_ratio_band", "grade_family"],
}
ALL_FEATURES = BASE + [feature for block in BLOCKS.values() for feature in block]
OUTPUT_COLUMNS = ["snapshot_date"] + [f for f in ALL_FEATURES if f != "calendar_month"] + ["y_next", "y_6m"]
PARSIMONY_TOLERANCE = 0.02
TREE_DEPTH = 3
TREE_MIN_PEOPLE = 300
MIN_PEOPLE = 30
MIN_EVENTS = 30


def log(message: str) -> None:
    """Bitácora sin filas: sólo conteos y tiempos."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------- carga en memoria


def check_output_columns(columns: list[str]) -> None:
    sys.path.insert(0, str(HELPER_DIR))
    import run_readonly_query as helper

    leaked = sorted(set(columns) & helper.SENSITIVE_OUTPUT_COLUMNS)
    if leaked:
        raise RuntimeError(f"La consulta devolvería columnas restringidas: {leaked}")
    if columns != OUTPUT_COLUMNS:
        raise RuntimeError(f"Columnas inesperadas: {columns}")


def load_person_months(dates: list[pd.Timestamp]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Lee persona-mes por lotes y devuelve celdas exactas mensual y a seis meses."""
    sys.path.insert(0, str(HELPER_DIR))
    import run_readonly_query as helper

    template = FRAME_QUERY.read_text(encoding="utf-8")
    keys = ["snapshot_date"] + [f for f in ALL_FEATURES if f != "calendar_month"]
    monthly_parts, direct_parts = [], []
    totals = {"person_months": 0, "monthly_labeled": 0, "six_month_labeled": 0}
    connection = helper.connect()
    try:
        for offset in range(0, len(dates), SNAPSHOTS_PER_QUERY):
            chunk = dates[offset : offset + SNAPSHOTS_PER_QUERY]
            sql = helper.validate_readonly(hz.render_query(template, chunk[0], chunk[-1]))
            started = time.time()
            with connection.cursor() as cursor:
                cursor.execute(sql)
                columns = [d[0] for d in cursor.description]
                check_output_columns(columns)
                rows = cursor.fetchall()
            frame = pd.DataFrame(rows, columns=columns)
            del rows
            frame["snapshot_date"] = pd.to_datetime(frame["snapshot_date"])
            totals["person_months"] += len(frame)
            for target, parts, label in [("y_next", monthly_parts, "monthly_labeled"), ("y_6m", direct_parts, "six_month_labeled")]:
                labeled = frame.loc[frame[target].notna(), keys + [target]]
                totals[label] += len(labeled)
                if labeled.empty:
                    continue
                cells = labeled.groupby(keys, observed=True)[target].agg(["size", "sum"]).reset_index()
                parts.append(cells.rename(columns={"size": "exposure_count", "sum": "event_count"}))
            log(f"fotos {chunk[0].date()}..{chunk[-1].date()}: {len(frame)} persona-mes en {time.time() - started:.0f}s")
            del frame
    finally:
        connection.close()
    return finalize(pd.concat(monthly_parts)), finalize(pd.concat(direct_parts), six_month=True), totals


def finalize(cells: pd.DataFrame, six_month: bool = False) -> pd.DataFrame:
    cells = cells.copy()
    for column in ALL_FEATURES:
        if column != "calendar_month":
            cells[column] = cells[column].fillna("(unknown)").astype(str)
    cells["exposure_count"] = cells["exposure_count"].astype(int)
    cells["event_count"] = cells["event_count"].astype(int)
    cells["distinct_employee_count"] = cells["exposure_count"]
    cells["calendar_month"] = cells["snapshot_date"].dt.month.astype(str)
    cells["six_month_frame"] = six_month
    return cells.sort_values(["snapshot_date"] + [f for f in ALL_FEATURES if f != "calendar_month"]).reset_index(drop=True)


# ---------------------------------------------------------------- evaluación rolling


def fold_windows(direct: pd.DataFrame) -> list[dict]:
    dates = sorted(direct["snapshot_date"].unique())
    windows = []
    for start_text in ro.FOLD_STARTS:
        start = pd.Timestamp(start_text)
        test_dates = [pd.Timestamp(d) for d in dates if d >= start][: ro.FOLD_SNAPSHOTS]
        six_cutoff = test_dates[0] - pd.DateOffset(months=6)
        validation_dates = [pd.Timestamp(d) for d in dates if d <= six_cutoff][-6:]
        windows.append(
            {
                "test_dates": test_dates,
                "validation_dates": validation_dates,
                "validation_start": validation_dates[0],
                "start": test_dates[0],
            }
        )
    return windows


def evaluate_hazard(monthly: pd.DataFrame, direct: pd.DataFrame, features: list[str], windows: list[dict]) -> dict:
    folds = []
    for window in windows:
        validation = direct[direct["snapshot_date"].isin(window["validation_dates"])]
        inner = ro.before(monthly, window["validation_start"], inclusive=False)
        l2, _ = ro.choose_l2(lambda value: ro.fit_hazard(inner, features, value), hz.six_month_predictions, validation)
        model = ro.fit_hazard(ro.before(monthly, window["start"], inclusive=False), features, l2)
        test = direct[direct["snapshot_date"].isin(window["test_dates"])]
        predictions = hz.six_month_predictions(model, test)
        metric = hz.metrics(test, predictions)
        metric["l2"] = l2
        metric["mean_predicted_percent"] = round(100.0 * float(np.average(predictions, weights=test["exposure_count"])), 4)
        metric["converged"] = bool(model.converged)
        folds.append({"model": model, "test": test, "predictions": predictions, "metrics": metric})
    return {"features": features, "folds": folds, "summary": summary([f["metrics"] for f in folds])}


def evaluate_lightgbm(direct: pd.DataFrame, features: list[str], windows: list[dict]) -> dict:
    ch.CATEGORICAL = features
    folds = []
    for window in windows:
        validation = direct[direct["snapshot_date"].isin(window["validation_dates"])]
        inner_cutoff = window["validation_start"] - pd.DateOffset(months=6)
        inner = ro.before(direct, inner_cutoff, inclusive=True)
        final = ro.before(direct, window["start"] - pd.DateOffset(months=6), inclusive=True)
        test = direct[direct["snapshot_date"].isin(window["test_dates"])]
        categories = ch.categories_from(direct)
        params, rounds, _ = ch.select_lightgbm(inner, validation, categories)
        booster = ch.fit_lightgbm(final, categories, params, rounds)
        predictions = ch.lgb_predict(booster, test, categories)
        metric = hz.metrics(test, predictions)
        metric["params"] = {**params, "rounds": rounds}
        metric["mean_predicted_percent"] = round(100.0 * float(np.average(predictions, weights=test["exposure_count"])), 4)
        folds.append({"metrics": metric})
    return {"features": features, "folds": folds, "summary": summary([f["metrics"] for f in folds])}


def summary(metrics: list[dict]) -> dict:
    keys = ["pr_auc", "lift_at_10_percent", "lift_at_20_percent", "brier_score", "log_loss"]
    result = {key: round(float(np.mean([m[key] for m in metrics])), 8) for key in keys}
    result["by_fold"] = {key: [round(float(m[key]), 6) for m in metrics] for key in keys}
    result["calibration_ratio_by_fold"] = [
        round(m["mean_predicted_percent"] / m["observed_rate_percent"], 4) for m in metrics
    ]
    return result


def public_spec(spec: dict) -> dict:
    return {
        "blocks": spec["blocks"],
        "features": spec["features"],
        "parameters": spec["parameters"],
        "summary": spec["summary"],
        "folds": [{k: v for k, v in f["metrics"].items() if k != "calibration"} | {"calibration": f["metrics"]["calibration"]} for f in spec["folds"]],
    }


def forward_selection(monthly: pd.DataFrame, direct: pd.DataFrame, windows: list[dict]) -> tuple[list[dict], dict]:
    """Agrega en cada paso el bloque que más mejora; conserva todas las combinaciones evaluadas."""
    evaluated: dict[tuple, dict] = {}

    def run(blocks: tuple[str, ...]) -> dict:
        key = tuple(sorted(blocks))
        if key not in evaluated:
            features = BASE + [f for b in key for f in BLOCKS[b]]
            started = time.time()
            result = evaluate_hazard(monthly, direct, features, windows)
            result["blocks"] = list(key)
            result["parameters"] = int(len(result["folds"][-1]["model"].beta))
            evaluated[key] = result
            log(
                f"bloques {list(key) or ['base']}: PR-AUC {result['summary']['pr_auc']:.5f} "
                f"lift10 {result['summary']['lift_at_10_percent']:.4f} ({time.time() - started:.0f}s)"
            )
        return evaluated[key]

    def score(result: dict) -> float:
        return result["summary"]["pr_auc"] / base_pr + result["summary"]["lift_at_10_percent"] / base_lift

    base = run(())
    base_pr, base_lift = base["summary"]["pr_auc"], base["summary"]["lift_at_10_percent"]
    path = [base]
    current: tuple[str, ...] = ()
    remaining = list(BLOCKS)
    while remaining:
        candidates = [run(current + (block,)) for block in remaining]
        best = max(candidates, key=score)
        added = [b for b in best["blocks"] if b not in current][0]
        current = tuple(best["blocks"])
        remaining.remove(added)
        path.append(best)
    return path, evaluated


def parsimonious_choice(evaluated: dict) -> tuple[dict, dict]:
    results = list(evaluated.values())
    best_pr = max(r["summary"]["pr_auc"] for r in results)
    best_lift = max(r["summary"]["lift_at_10_percent"] for r in results)
    eligible = [
        r for r in results
        if r["summary"]["pr_auc"] >= (1 - PARSIMONY_TOLERANCE) * best_pr
        and r["summary"]["lift_at_10_percent"] >= (1 - PARSIMONY_TOLERANCE) * best_lift
    ]
    chosen = min(eligible, key=lambda r: (len(r["blocks"]), r["parameters"], -r["summary"]["pr_auc"]))
    rule = {
        "tolerance_relative": PARSIMONY_TOLERANCE,
        "best_pr_auc": best_pr,
        "best_lift_at_10_percent": best_lift,
        "eligible": [r["blocks"] for r in eligible],
        "chosen_blocks": chosen["blocks"],
    }
    return chosen, rule


def drop_one(monthly: pd.DataFrame, direct: pd.DataFrame, windows: list[dict], chosen: dict) -> list[dict]:
    """Quita una variable a la vez del modelo elegido (fuera de la base)."""
    rows = []
    for feature in [f for f in chosen["features"] if f not in BASE]:
        features = [f for f in chosen["features"] if f != feature]
        result = evaluate_hazard(monthly, direct, features, windows)
        rows.append({"dropped": feature, "summary": result["summary"]})
        log(f"sin {feature}: PR-AUC {result['summary']['pr_auc']:.5f} lift10 {result['summary']['lift_at_10_percent']:.4f}")
    return rows


# ---------------------------------------------------------------- interpretación


def coefficient_stability(chosen: dict) -> list[dict]:
    rows = {}
    for index, fold in enumerate(chosen["folds"]):
        model = fold["model"]
        for name, beta in zip(model.encoder.columns, model.beta):
            if name == "intercept" or name.startswith("calendar_month="):
                continue
            rows.setdefault(name, [None] * len(chosen["folds"]))[index] = float(beta)
    result = []
    for name, values in rows.items():
        present = [v for v in values if v is not None]
        signs = {np.sign(v) for v in present if abs(v) > 1e-9}
        result.append(
            {
                "term": name,
                "hazard_ratio_by_fold": [round(float(np.exp(v)), 4) if v is not None else None for v in values],
                "same_sign_all_folds": len(signs) <= 1 and len(present) == len(values),
            }
        )
    reference = chosen["folds"][-1]["model"].encoder.references
    return sorted(result, key=lambda r: -abs(np.log(r["hazard_ratio_by_fold"][-1] or 1.0))), reference


def subgroup_calibration(chosen: dict, keys: list[str]) -> list[dict]:
    """Estimado vs observado en el último fold por variable no protegida."""
    fold = chosen["folds"][-1]
    test = fold["test"].assign(_pred=fold["predictions"] * fold["test"]["exposure_count"])
    snapshots = test["snapshot_date"].nunique()
    rows = []
    for key in keys:
        grouped = test.groupby(key)[["exposure_count", "event_count", "_pred"]].sum()
        for value, row in grouped.iterrows():
            people = row["exposure_count"] / snapshots
            if people < MIN_PEOPLE or row["event_count"] < MIN_EVENTS:
                continue
            rows.append(
                {
                    "variable": key,
                    "category": value,
                    "people_per_snapshot": int(round(people)),
                    "predicted_percent": round(100.0 * row["_pred"] / row["exposure_count"], 3),
                    "observed_percent": round(100.0 * row["event_count"] / row["exposure_count"], 3),
                    "ratio": round(float(row["_pred"] / row["event_count"]), 3),
                }
            )
    return rows


def describe_path(tree, feature_names: list[str], node: int, path: list[str]) -> list[tuple[int, list[str]]]:
    left, right = tree.children_left[node], tree.children_right[node]
    if left == right:
        return [(node, path)]
    name = feature_names[tree.feature[node]]
    variable, value = name.split("=", 1)
    return describe_path(tree, feature_names, left, path + [f"{variable} ≠ {value}"]) + describe_path(
        tree, feature_names, right, path + [f"{variable} = {value}"]
    )


def tree_groups(
    monthly: pd.DataFrame,
    direct: pd.DataFrame,
    chosen: dict,
    l2: float,
    model=None,
    tree_features: list[str] | None = None,
) -> dict:
    """Árbol poco profundo sobre el riesgo estimado de la foto más reciente.

    ``model`` permite pasar un hazard ya ajustado (p. ej. recalibrado) y
    ``tree_features`` limita las variables que el árbol puede usar.
    """
    from sklearn.tree import DecisionTreeRegressor

    model = model or ro.fit_hazard(monthly, chosen["features"], l2)
    latest = monthly["snapshot_date"].max()
    current = monthly.loc[monthly["snapshot_date"] == latest].reset_index(drop=True)
    risk = hz.six_month_predictions(model, current)
    features = tree_features or [f for f in chosen["features"] if f != "calendar_month"]
    x = pd.get_dummies(current[features].astype(str), prefix_sep="=").astype(float)
    weights = current["exposure_count"].to_numpy(dtype=float)
    tree = DecisionTreeRegressor(
        max_depth=TREE_DEPTH,
        min_weight_fraction_leaf=TREE_MIN_PEOPLE / weights.sum(),
        random_state=0,
    ).fit(x, risk, sample_weight=weights)
    leaves = dict(describe_path(tree.tree_, list(x.columns), 0, []))
    current_leaf = tree.apply(x)

    # Observado: el último fold de prueba con el mismo árbol (grupos ≥30 salidas).
    test = chosen["folds"][-1]["test"]
    test_x = pd.get_dummies(test[features].astype(str), prefix_sep="=").reindex(columns=x.columns, fill_value=0).astype(float)
    test_leaf = tree.apply(test_x)
    test_frame = test.assign(_leaf=test_leaf, _pred=chosen["folds"][-1]["predictions"] * test["exposure_count"])
    observed = test_frame.groupby("_leaf")[["exposure_count", "event_count", "_pred"]].sum()
    test_snapshots = test["snapshot_date"].nunique()

    rows = []
    total = weights.sum()
    for leaf, rules in leaves.items():
        mask = current_leaf == leaf
        people = float(weights[mask].sum())
        if people < MIN_PEOPLE:
            continue
        item = {
            "rule": " y ".join(rules) if rules else "todos",
            "people": int(people),
            "people_share_percent": round(100.0 * people / total, 2),
            "predicted_6m_percent": round(100.0 * float(np.average(risk[mask], weights=weights[mask])), 3),
        }
        if leaf in observed.index:
            row = observed.loc[leaf]
            item["last_fold_people_per_snapshot"] = int(round(row["exposure_count"] / test_snapshots))
            item["last_fold_predicted_percent"] = round(100.0 * row["_pred"] / row["exposure_count"], 3)
            if row["event_count"] >= MIN_EVENTS:
                item["last_fold_events"] = int(row["event_count"])
                item["last_fold_observed_percent"] = round(100.0 * row["event_count"] / row["exposure_count"], 3)
        rows.append(item)
    rows.sort(key=lambda r: -r["predicted_6m_percent"])
    mean = float(np.average(risk, weights=weights))
    for row in rows:
        row["lift_vs_mean"] = round(row["predicted_6m_percent"] / (100.0 * mean), 3)
    return {
        "snapshot": str(latest.date()),
        "people": int(total),
        "mean_predicted_6m_percent": round(100.0 * mean, 3),
        "max_depth": TREE_DEPTH,
        "min_leaf_people": TREE_MIN_PEOPLE,
        "variance_explained_r2": round(float(tree.score(x, risk, sample_weight=weights)), 4),
        "groups": rows,
    }


def category_profile(direct: pd.DataFrame) -> list[dict]:
    """Distribución y tasa a seis meses por categoría (agregada, >= 30)."""
    snapshots = direct["snapshot_date"].nunique()
    rows = []
    for feature in [f for f in ALL_FEATURES if f != "calendar_month"]:
        grouped = direct.groupby(feature)[["exposure_count", "event_count"]].sum()
        for value, row in grouped.iterrows():
            people = row["exposure_count"] / snapshots
            if people < MIN_PEOPLE:
                continue
            rows.append(
                {
                    "variable": feature,
                    "category": value,
                    "people_per_snapshot": int(round(people)),
                    "six_month_rate_percent": round(100.0 * row["event_count"] / row["exposure_count"], 3)
                    if row["event_count"] >= MIN_EVENTS
                    else None,
                }
            )
    return rows


# ---------------------------------------------------------------- reporte


def fmt_summary(s: dict) -> str:
    return f"{s['pr_auc']:.4f} | {s['lift_at_10_percent']:.3f} | {s['lift_at_20_percent']:.3f} | {s['brier_score']:.5f}"


def build_report(result: dict) -> str:
    lines = [
        "# Selección de variables por bloques — Engineering",
        "",
        f"Creado: {result['created_at_utc']}. Frontera de conocimiento: {result['knowledge_boundary']}.",
        f"Fotos: {result['frame']['first_snapshot']} a {result['frame']['last_snapshot']}; "
        f"{result['frame']['monthly_exposures']:,} persona-mes con etiqueta mensual y "
        f"{result['frame']['six_month_exposures']:,} con etiqueta a seis meses.",
        "Entrenamiento en memoria (sin persistir filas ni IDs) bajo "
        f"`{result['authorization']['path']}`.",
        "",
        "## Camino de selección hacia delante (hazard `cloglog`, 4 folds)",
        "",
        "| Paso | Bloques | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for index, spec in enumerate(result["forward_path"]):
        lines.append(
            f"| {index} | {', '.join(spec['blocks']) or 'base'} | {spec['parameters']} | {fmt_summary(spec['summary'])} |"
        )
    lines += ["", "## Todas las combinaciones evaluadas", "", "| Bloques | PR-AUC | Lift@10% | Lift@20% | Brier |", "|---|---:|---:|---:|---:|"]
    for spec in sorted(result["evaluated"], key=lambda s: -s["summary"]["pr_auc"]):
        lines.append(f"| {', '.join(spec['blocks']) or 'base'} | {fmt_summary(spec['summary'])} |")
    rule = result["parsimony"]
    lines += [
        "",
        "## Regla de parsimonia",
        "",
        f"Mejor PR-AUC {rule['best_pr_auc']:.4f}; mejor lift@10% {rule['best_lift_at_10_percent']:.3f}; tolerancia 2% relativo.",
        f"Elegibles: {', '.join('[' + ', '.join(b or ['base']) + ']' for b in rule['eligible'])}.",
        f"**Elegido: {', '.join(rule['chosen_blocks']) or 'base'}.**",
        "",
        "## Techo no lineal (LightGBM, todas las variables)",
        "",
        f"PR-AUC | Lift@10% | Lift@20% | Brier: {fmt_summary(result['lightgbm_all']['summary'])}",
        "",
        "## Contribución de cada variable del elegido (quitar una)",
        "",
        "| Variable quitada | PR-AUC | Lift@10% | Lift@20% | Brier |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["drop_one"]:
        lines.append(f"| {row['dropped']} | {fmt_summary(row['summary'])} |")
    chosen = result["chosen"]
    lines += [
        "",
        "## Modelo elegido por fold",
        "",
        "| Fold | L2 | PR-AUC | Lift@10% | Brier | Estimado % | Observado % |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, fold in enumerate(chosen["folds"], start=1):
        lines.append(
            f"| {index} | {fold['l2']} | {fold['pr_auc']:.4f} | {fold['lift_at_10_percent']:.3f} | {fold['brier_score']:.5f} | "
            f"{fold['mean_predicted_percent']:.2f} | {fold['observed_rate_percent']:.2f} |"
        )
    lines += ["", "## Hazard ratios del elegido por fold", "", f"Referencias: {result['references']}", "", "| Término | HR por fold | Mismo signo |", "|---|---|---|"]
    for row in result["coefficients"]:
        hrs = ", ".join("—" if v is None else f"{v:.2f}" for v in row["hazard_ratio_by_fold"])
        lines.append(f"| {row['term']} | {hrs} | {'sí' if row['same_sign_all_folds'] else 'no'} |")
    groups = result["groups"]
    lines += [
        "",
        f"## Grupos (árbol profundidad ≤ {groups['max_depth']}, hojas ≥ {groups['min_leaf_people']} personas), foto {groups['snapshot']}",
        "",
        f"Riesgo medio estimado a seis meses: {groups['mean_predicted_6m_percent']:.2f}%. R² del árbol sobre el riesgo del modelo: {groups['variance_explained_r2']:.2f}.",
        "",
        "| Grupo | Personas | % población | Riesgo 6m % | Lift | Último fold: estimado % | observado % |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in groups["groups"]:
        observed = row.get("last_fold_observed_percent")
        lines.append(
            f"| {row['rule']} | {row['people']} | {row['people_share_percent']:.1f} | {row['predicted_6m_percent']:.2f} | "
            f"{row['lift_vs_mean']:.2f} | {row.get('last_fold_predicted_percent', float('nan')):.2f} | "
            f"{'—' if observed is None else f'{observed:.2f}'} |"
        )
    lines += ["", "## Calibración por subgrupo no protegido (último fold)", "", "| Variable | Categoría | Personas/foto | Estimado % | Observado % | Razón |", "|---|---|---:|---:|---:|---:|"]
    for row in result["subgroup_calibration"]:
        lines.append(
            f"| {row['variable']} | {row['category']} | {row['people_per_snapshot']} | {row['predicted_percent']:.2f} | "
            f"{row['observed_percent']:.2f} | {row['ratio']:.2f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-lightgbm", action="store_true")
    args = parser.parse_args()
    output_dir = (args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"La carpeta de salida ya tiene contenido: {output_dir}")
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    if authorization.get("status") != "approved":
        raise RuntimeError("La autorización de entrenamiento en memoria no está aprobada.")

    calendar = [d for d in hz.fetch_calendar() if d >= MIN_SNAPSHOT]
    monthly, direct, totals = load_person_months(calendar)
    log(f"celdas mensuales {len(monthly)}, a seis meses {len(direct)}")
    windows = fold_windows(direct)

    path, evaluated = forward_selection(monthly, direct, windows)
    chosen, rule = parsimonious_choice(evaluated)
    drops = drop_one(monthly, direct, windows, chosen)
    coefficients, references = coefficient_stability(chosen)
    lgb_all = None
    if not args.skip_lightgbm:
        started = time.time()
        lgb_all = evaluate_lightgbm(direct, [f for f in ALL_FEATURES], windows)
        log(f"LightGBM todas: PR-AUC {lgb_all['summary']['pr_auc']:.5f} lift10 {lgb_all['summary']['lift_at_10_percent']:.4f} ({time.time() - started:.0f}s)")
    groups = tree_groups(monthly, direct, chosen, chosen["folds"][-1]["metrics"]["l2"])
    calibration = subgroup_calibration(chosen, [f for f in chosen["features"] if f != "calendar_month"])

    import lightgbm
    import sklearn

    result = {
        "artifact": "engineering-feature-block-selection",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": hz.KNOWLEDGE_BOUNDARY.strftime("%Y-%m-%d"),
        "deliverable_classification": "presentation",
        "authorization": {"path": str(AUTHORIZATION.relative_to(ROOT)), "id": authorization["authorization_id"]},
        "frame": {
            "first_snapshot": str(monthly["snapshot_date"].min().date()),
            "last_snapshot": str(monthly["snapshot_date"].max().date()),
            "person_months_read": totals["person_months"],
            "monthly_exposures": int(monthly["exposure_count"].sum()),
            "monthly_events": int(monthly["event_count"].sum()),
            "six_month_exposures": int(direct["exposure_count"].sum()),
            "six_month_events": int(direct["event_count"].sum()),
            "monthly_cells": int(len(monthly)),
            "six_month_cells": int(len(direct)),
        },
        "design": {
            "base": BASE,
            "blocks": BLOCKS,
            "fold_starts": ro.FOLD_STARTS,
            "fold_snapshots": ro.FOLD_SNAPSHOTS,
            "l2_grid": ro.L2_GRID,
            "lightgbm_grid": ch.LGB_GRID,
            "selection": "hacia delante por bloques; puntaje = PR-AUC/base + lift@10/base, promedio de 4 folds",
            "parsimony": "menos bloques con PR-AUC y lift@10 medios >= 98% del mejor",
            "rsf": "no ejecutado: scikit-survival no está instalado; LightGBM cumple el papel de techo no lineal",
        },
        "forward_path": [public_spec(s) for s in path],
        "evaluated": [public_spec(s) for s in evaluated.values()],
        "parsimony": rule,
        "chosen": {"blocks": chosen["blocks"], "features": chosen["features"], "folds": [f["metrics"] for f in chosen["folds"]], "summary": chosen["summary"]},
        "drop_one": drops,
        "coefficients": coefficients,
        "references": references,
        "lightgbm_all": {"features": lgb_all["features"], "summary": lgb_all["summary"], "folds": [f["metrics"] for f in lgb_all["folds"]]} if lgb_all else None,
        "groups": groups,
        "subgroup_calibration": calibration,
        "category_profile": category_profile(direct),
        "versions": {"lightgbm": lightgbm.__version__, "sklearn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        "privacy": {
            "employee_level_rows_persisted": False,
            "employee_ids_selected": False,
            "aggregate_training_frame_persisted": False,
            "individual_scores_published": False,
            "minimum_group_people_per_snapshot": MIN_PEOPLE,
            "minimum_published_events": MIN_EVENTS,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "selection-results.json"
    report_path = output_dir / "selection-report.md"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    manifest = {
        "artifact": result["artifact"],
        "created_at_utc": result["created_at_utc"],
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "authorization": result["authorization"],
        "queries": {"calendar": str(hz.CALENDAR_QUERY.relative_to(ROOT)), "person_month_frame": str(FRAME_QUERY.relative_to(ROOT))},
        "query_sha256": {"calendar": hz.sha256_file(hz.CALENDAR_QUERY), "person_month_frame": hz.sha256_file(FRAME_QUERY)},
        "audits": {str(p.relative_to(ROOT)): hz.sha256_file(p) for p in AUDITS},
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": hz.sha256_file(result_path),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": hz.sha256_file(report_path),
        "employee_level_rows_persisted": False,
        "aggregate_training_frame_persisted": False,
    }
    (output_dir / "selection-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(build_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
