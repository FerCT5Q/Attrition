"""Ajuste del hazard elegido para Engineering: tendencia, recalibración e interacciones (2026-10-02).

Parte del elegido en ``feature-block-selection-v1`` (base + manager/equipo) y
evalúa, con los mismos cuatro folds rolling-origin y el mismo frame en
memoria (``config/attrition_model_in_memory_training_authorization_20261001.json``):

1. Tendencia: lineal (como el elegido), sin tendencia, o congelada en el
   último mes de entrenamiento; cada una con y sin recalibración del riesgo
   base sobre los 12 meses previos al corte (un desplazamiento del intercepto
   que iguala salidas estimadas y observadas en esa ventana).
2. Interacciones: con la mejor variante de calibración (menor Brier medio),
   agrega una a una las candidatas y conserva la que cumple la regla de
   promoción (gana >= 3 de 4 folds en PR-AUC y lift@10% sin empeorar el
   Brier medio); máximo tres.
3. Parsimonia contra el techo: compara con LightGBM (todas las variables,
   mismos folds) y marca si queda a menos de 2% relativo.

Sólo se escriben agregados: métricas, coeficientes y grupos >= 30 personas
(observado sólo con >= 30 salidas).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import critical_tech_discrete_hazard_model as hz  # noqa: E402
import critical_tech_model_comparison_rolling as ro  # noqa: E402
import engineering_feature_block_selection as fs  # noqa: E402

ROOT = hz.ROOT
SELECTION_RESULTS = ROOT / "output" / "analysis" / "engineering" / "20261001" / "feature-block-selection-v1" / "selection-results.json"
# v1 (2026-10-02) eligió L2 = 0 sin convergencia en folds 2-4; v2 sólo acepta ajustes convergidos.
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "engineering" / "20261001" / "hazard-adjustment-v2"
CHOSEN = fs.BASE + fs.BLOCKS["manager_equipo"]
WIDER = fs.BASE + fs.BLOCKS["carrera"] + fs.BLOCKS["geografia"] + fs.BLOCKS["manager_equipo"]
TREND_MODES = ["linear", "none", "frozen"]
RECALIBRATION_MONTHS = [0, 12]
# Pares candidatos: hipótesis de modificación del efecto de antigüedad y nivel.
INTERACTIONS = {
    "tenure_x_team_exits": ("company_tenure_band", "team_exits_12m"),
    "tenure_x_direct_reports": ("company_tenure_band", "direct_reports_band"),
    "tenure_x_manager_changes": ("company_tenure_band", "manager_changes_12m"),
    "level_x_team_exits": ("level_grouped", "team_exits_12m"),
    "level_x_tenure": ("level_grouped", "company_tenure_band"),
}
MAX_INTERACTIONS = 3
REFERENCE_NAME = "ref"


# ---------------------------------------------------------------- diseño


@dataclass
class TrendEncoder(hz.DesignEncoder):
    """``DesignEncoder`` con la tendencia lineal, sin ella o congelada."""

    mode: str = "linear"
    time_cap: float = 0.0

    @classmethod
    def build(cls, frame: pd.DataFrame, features: list[str], mode: str) -> "TrendEncoder":
        base = hz.DesignEncoder.fit(frame, features)
        encoder = cls(**vars(base), mode=mode)
        encoder.time_cap = float(base._time_index(frame["snapshot_date"]).max())
        if mode == "none":
            encoder.columns = [c for c in base.columns if c != "time_index"]
        return encoder

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        matrix = super().transform(frame)
        if self.mode == "none":
            return np.delete(matrix, 1, axis=1)
        if self.mode == "frozen":
            matrix[:, 1] = np.minimum(matrix[:, 1], self.time_cap)
        return matrix


def add_interactions(frame: pd.DataFrame, references: dict[str, str]) -> pd.DataFrame:
    """Interacción = combinación de dos categorías no referencia; el resto queda en ``ref``.

    Así la interacción sólo mide el exceso sobre los efectos principales y no
    duplica columnas de la base.
    """
    frame = frame.copy()
    for name, (left, right) in INTERACTIONS.items():
        a, b = frame[left].astype(str), frame[right].astype(str)
        frame[name] = np.where((a != references[left]) & (b != references[right]), a + " | " + b, REFERENCE_NAME)
    return frame


def modal_references(frame: pd.DataFrame) -> dict[str, str]:
    columns = {c for pair in INTERACTIONS.values() for c in pair}
    return {c: str(frame.groupby(c)["exposure_count"].sum().idxmax()) for c in sorted(columns)}


def recalibration_offset(model: hz.IRLSModel, recent: pd.DataFrame) -> float:
    """Desplazamiento del predictor lineal que iguala salidas estimadas y observadas."""
    eta = model.encoder.transform(recent) @ model.beta
    n = recent["exposure_count"].to_numpy(dtype=float)
    target = float(recent["event_count"].sum())
    delta = 0.0
    for _ in range(50):
        exponent = np.exp(np.clip(eta + delta, -30.0, 5.0))
        h = 1.0 - np.exp(-exponent)
        gap = float(np.sum(n * h)) - target
        slope = float(np.sum(n * exponent * np.exp(-exponent)))
        step = gap / max(slope, 1e-9)
        delta -= step
        if abs(step) < 1e-10:
            break
    return float(delta)


def fit_variant(train: pd.DataFrame, features: list[str], l2: float, trend: str, recalibration_months: int) -> hz.IRLSModel:
    model = hz.fit_irls(train, "cloglog", l2, TrendEncoder.build(train, features, trend))
    model.recalibration_offset = 0.0
    if recalibration_months:
        cutoff = train["snapshot_date"].max() - pd.DateOffset(months=recalibration_months)
        recent = train.loc[train["snapshot_date"] > cutoff]
        offset = recalibration_offset(model, recent)
        model.beta = model.beta.copy()
        model.beta[0] += offset
        model.recalibration_offset = offset
    return model


# ---------------------------------------------------------------- evaluación


def choose_converged_l2(fit, validation: pd.DataFrame) -> float:
    """L2 con menor Brier de validación entre los ajustes que convergen.

    Sin tendencia, L2 = 0 deja categorías sin salidas (p. ej. VP con < 3 años)
    con coeficientes que divergen; esos ajustes no son elegibles.
    """
    best = None
    for l2 in ro.L2_GRID:
        model = fit(l2)
        if not model.converged:
            continue
        score = hz.brier_score(validation, hz.six_month_predictions(model, validation))
        if best is None or score < best[0]:
            best = (score, l2)
    if best is None:
        raise RuntimeError("Ningún L2 de la rejilla convergió.")
    return best[1]


def fit_converged(train: pd.DataFrame, features: list[str], l2: float, trend: str, recalibration_months: int) -> hz.IRLSModel:
    """Ajusta con ``l2``; si no converge, sube al siguiente valor de la rejilla."""
    for value in [v for v in ro.L2_GRID if v >= l2]:
        model = fit_variant(train, features, value, trend, recalibration_months)
        if model.converged:
            return model
    raise RuntimeError("El ajuste no convergió con ningún L2 de la rejilla.")


def evaluate(monthly: pd.DataFrame, direct: pd.DataFrame, features: list[str], windows: list[dict], trend: str, recalibration_months: int) -> dict:
    folds = []
    for window in windows:
        validation = direct[direct["snapshot_date"].isin(window["validation_dates"])]
        inner = ro.before(monthly, window["validation_start"], inclusive=False)
        l2 = choose_converged_l2(lambda value: fit_variant(inner, features, value, trend, recalibration_months), validation)
        model = fit_converged(ro.before(monthly, window["start"], inclusive=False), features, l2, trend, recalibration_months)
        l2 = model.l2
        test = direct[direct["snapshot_date"].isin(window["test_dates"])]
        predictions = hz.six_month_predictions(model, test)
        metric = hz.metrics(test, predictions)
        metric["l2"] = l2
        metric["mean_predicted_percent"] = round(100.0 * float(np.average(predictions, weights=test["exposure_count"])), 4)
        metric["recalibration_offset"] = round(model.recalibration_offset, 6)
        metric["converged"] = bool(model.converged)
        folds.append({"model": model, "test": test, "predictions": predictions, "metrics": metric})
    result = {
        "features": features,
        "trend": trend,
        "recalibration_months": recalibration_months,
        "parameters": int(len(folds[-1]["model"].beta)),
        "folds": folds,
        "summary": fs.summary([f["metrics"] for f in folds]),
    }
    ratios = result["summary"]["calibration_ratio_by_fold"]
    result["summary"]["mean_abs_log_calibration_ratio"] = round(float(np.mean(np.abs(np.log(ratios)))), 6)
    return result


def label(spec: dict) -> str:
    extra = [f for f in spec["features"] if f in INTERACTIONS]
    recal = f"recal {spec['recalibration_months']}m" if spec["recalibration_months"] else "sin recal"
    wider = ", + carrera y geografía" if set(fs.BLOCKS["carrera"] + fs.BLOCKS["geografia"]) <= set(spec["features"]) else ""
    return f"{spec['trend']}, {recal}" + (f", {' + '.join(extra)}" if extra else "") + wider


def promotion(challenger: dict, incumbent: dict) -> dict:
    """Regla de promoción del champion: >= 3 de 4 folds en PR-AUC y lift@10 sin peor Brier medio."""
    c, i = challenger["summary"]["by_fold"], incumbent["summary"]["by_fold"]
    pr_wins = int(sum(a > b for a, b in zip(c["pr_auc"], i["pr_auc"])))
    lift_wins = int(sum(a > b for a, b in zip(c["lift_at_10_percent"], i["lift_at_10_percent"])))
    brier_ok = challenger["summary"]["brier_score"] <= incumbent["summary"]["brier_score"]
    return {"pr_auc_wins": pr_wins, "lift_wins": lift_wins, "brier_not_worse": bool(brier_ok), "promoted": pr_wins >= 3 and lift_wins >= 3 and brier_ok}


def interaction_search(monthly: pd.DataFrame, direct: pd.DataFrame, windows: list[dict], start: dict) -> tuple[dict, list[dict]]:
    current = start
    trail = []
    remaining = list(INTERACTIONS)
    while remaining and len([f for f in current["features"] if f in INTERACTIONS]) < MAX_INTERACTIONS:
        candidates = []
        for name in remaining:
            started = time.time()
            spec = evaluate(monthly, direct, current["features"] + [name], windows, current["trend"], current["recalibration_months"])
            rule = promotion(spec, current)
            fs.log(f"+{name}: PR-AUC {spec['summary']['pr_auc']:.5f} lift10 {spec['summary']['lift_at_10_percent']:.4f} {rule} ({time.time() - started:.0f}s)")
            trail.append({"step": len(trail), "added": name, "base": label(current), "summary": spec["summary"], "rule": rule, "parameters": spec["parameters"]})
            candidates.append((spec, rule, name))
        promoted = [c for c in candidates if c[1]["promoted"]]
        if not promoted:
            break
        best = max(promoted, key=lambda c: (c[0]["summary"]["pr_auc"] / current["summary"]["pr_auc"] + c[0]["summary"]["lift_at_10_percent"] / current["summary"]["lift_at_10_percent"]))
        current = best[0]
        remaining.remove(best[2])
        trail.append({"accepted": best[2], "now": label(current)})
    return current, trail


def ceiling_check(specs: list[dict], ceiling: dict) -> dict:
    best_pr = max([s["summary"]["pr_auc"] for s in specs] + [ceiling["pr_auc"]])
    best_lift = max([s["summary"]["lift_at_10_percent"] for s in specs] + [ceiling["lift_at_10_percent"]])
    rows = []
    for spec in specs:
        rows.append(
            {
                "spec": label(spec),
                "pr_auc_vs_best": round(spec["summary"]["pr_auc"] / best_pr, 4),
                "lift_vs_best": round(spec["summary"]["lift_at_10_percent"] / best_lift, 4),
                "within_tolerance": spec["summary"]["pr_auc"] >= (1 - fs.PARSIMONY_TOLERANCE) * best_pr
                and spec["summary"]["lift_at_10_percent"] >= (1 - fs.PARSIMONY_TOLERANCE) * best_lift,
            }
        )
    return {"best_pr_auc": best_pr, "best_lift_at_10_percent": best_lift, "tolerance_relative": fs.PARSIMONY_TOLERANCE, "rows": rows}


def public(spec: dict) -> dict:
    return {
        "label": label(spec),
        "features": spec["features"],
        "trend": spec["trend"],
        "recalibration_months": spec["recalibration_months"],
        "parameters": spec["parameters"],
        "summary": spec["summary"],
        "folds": [f["metrics"] for f in spec["folds"]],
    }


# ---------------------------------------------------------------- reporte


def fmt(s: dict) -> str:
    ratios = ", ".join(f"{r:.2f}" for r in s["calibration_ratio_by_fold"])
    return f"{s['pr_auc']:.4f} | {s['lift_at_10_percent']:.3f} | {s['lift_at_20_percent']:.3f} | {s['brier_score']:.5f} | {ratios}"


def build_report(result: dict) -> str:
    header = "| Especificación | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado por fold |"
    rule = "|---|---:|---:|---:|---:|---:|---|"
    lines = [
        "# Ajuste del hazard de Engineering: tendencia, recalibración e interacciones",
        "",
        f"Creado: {result['created_at_utc']}. Frontera de conocimiento: {result['knowledge_boundary']}.",
        f"Mismo frame y folds que `feature-block-selection-v1` ({result['frame']['six_month_exposures']:,} exposiciones a seis meses).",
        f"Entrenamiento en memoria bajo `{result['authorization']['path']}`; sin filas ni IDs persistidos.",
        "",
        "## 1. Tendencia y recalibración (base + manager/equipo)",
        "",
        header,
        rule,
    ]
    for spec in result["trend_variants"]:
        lines.append(f"| {spec['label']} | {spec['parameters']} | {fmt(spec['summary'])} |")
    lines += ["", f"Mejor calibración (menor Brier medio): **{result['calibration_choice']}**.", "", "## 2. Interacciones (regla de promoción)", "", "| Paso | Agregada | Sobre | PR-AUC | Lift@10% | Brier | Gana PR | Gana lift | Brier no peor | Promovida |", "|---:|---|---|---:|---:|---:|---:|---:|---|---|"]
    for row in result["interaction_trail"]:
        if "accepted" in row:
            lines.append(f"| | **aceptada: {row['accepted']}** | → {row['now']} | | | | | | | |")
            continue
        s, r = row["summary"], row["rule"]
        lines.append(
            f"| {row['step']} | {row['added']} | {row['base']} | {s['pr_auc']:.4f} | {s['lift_at_10_percent']:.3f} | {s['brier_score']:.5f} | "
            f"{r['pr_auc_wins']}/4 | {r['lift_wins']}/4 | {'sí' if r['brier_not_worse'] else 'no'} | {'sí' if r['promoted'] else 'no'} |"
        )
    lines += ["", "## 3. Finalistas", "", header, rule]
    for spec in result["finalists"]:
        lines.append(f"| {spec['label']} | {spec['parameters']} | {fmt(spec['summary'])} |")
    ceiling = result["ceiling"]
    lines += [
        "",
        f"Techo LightGBM (todas las variables, de `feature-block-selection-v1`): {fmt(ceiling['summary'])}",
        "",
        "## 4. Parsimonia contra el techo (2% relativo)",
        "",
        "| Especificación | PR-AUC / mejor | Lift@10% / mejor | Dentro de 2% |",
        "|---|---:|---:|---|",
    ]
    for row in result["ceiling_check"]["rows"]:
        lines.append(f"| {row['spec']} | {row['pr_auc_vs_best']:.3f} | {row['lift_vs_best']:.3f} | {'sí' if row['within_tolerance'] else 'no'} |")
    final = result["final"]
    lines += ["", f"**Modelo final: {final['label']}.** Promoción frente al elegido original: {result['final_vs_original']}.",
              "", "## 5. Modelo final por fold", "", "Todos los ajustes convergieron (L2 elegido sólo entre ajustes convergidos).", "",
        "| Fold | L2 | Recal. (log) | PR-AUC | Lift@10% | Brier | Estimado % | Observado % |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, fold in enumerate(final["folds"], start=1):
        lines.append(
            f"| {index} | {fold['l2']} | {fold['recalibration_offset']:.3f} | {fold['pr_auc']:.4f} | {fold['lift_at_10_percent']:.3f} | "
            f"{fold['brier_score']:.5f} | {fold['mean_predicted_percent']:.2f} | {fold['observed_rate_percent']:.2f} |"
        )
    lines += ["", "## 6. Hazard ratios del final por fold", "", f"Referencias: {result['references']}", "", "| Término | HR por fold | Mismo signo |", "|---|---|---|"]
    for row in result["coefficients"]:
        hrs = ", ".join("—" if v is None else f"{v:.2f}" for v in row["hazard_ratio_by_fold"])
        lines.append(f"| {row['term']} | {hrs} | {'sí' if row['same_sign_all_folds'] else 'no'} |")
    groups = result["groups"]
    lines += [
        "",
        f"## 7. Grupos (árbol profundidad ≤ {groups['max_depth']}, hojas ≥ {groups['min_leaf_people']} personas), foto {groups['snapshot']}",
        "",
        f"Riesgo medio estimado a seis meses: {groups['mean_predicted_6m_percent']:.2f}%. R² del árbol: {groups['variance_explained_r2']:.2f}.",
        "",
        "| Grupo | Personas | % población | Riesgo 6m % | Lift | Último fold: estimado % | observado % |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in groups["groups"]:
        observed = row.get("last_fold_observed_percent")
        lines.append(
            f"| {row['rule']} | {row['people']} | {row['people_share_percent']:.1f} | {row['predicted_6m_percent']:.2f} | {row['lift_vs_mean']:.2f} | "
            f"{row.get('last_fold_predicted_percent', float('nan')):.2f} | {'—' if observed is None else f'{observed:.2f}'} |"
        )
    lines += ["", "## 8. Calibración por subgrupo no protegido (último fold)", "", "| Variable | Categoría | Personas/foto | Estimado % | Observado % | Razón |", "|---|---|---:|---:|---:|---:|"]
    for row in result["subgroup_calibration"]:
        lines.append(f"| {row['variable']} | {row['category']} | {row['people_per_snapshot']} | {row['predicted_percent']:.2f} | {row['observed_percent']:.2f} | {row['ratio']:.2f} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output_dir = (args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"La carpeta de salida ya tiene contenido: {output_dir}")
    authorization = json.loads(fs.AUTHORIZATION.read_text(encoding="utf-8"))
    if authorization.get("status") != "approved":
        raise RuntimeError("La autorización de entrenamiento en memoria no está aprobada.")
    previous = json.loads(SELECTION_RESULTS.read_text(encoding="utf-8"))

    calendar = [d for d in hz.fetch_calendar() if d >= fs.MIN_SNAPSHOT]
    monthly, direct, totals = fs.load_person_months(calendar)
    if int(direct["exposure_count"].sum()) != previous["frame"]["six_month_exposures"]:
        fs.log("aviso: el frame no coincide con feature-block-selection-v1; el techo LightGBM no es comparable")
    references = modal_references(direct)
    monthly, direct = add_interactions(monthly, references), add_interactions(direct, references)
    windows = fs.fold_windows(direct)

    variants = []
    for trend in TREND_MODES:
        for months in RECALIBRATION_MONTHS:
            started = time.time()
            spec = evaluate(monthly, direct, CHOSEN, windows, trend, months)
            fs.log(f"{label(spec)}: PR-AUC {spec['summary']['pr_auc']:.5f} lift10 {spec['summary']['lift_at_10_percent']:.4f} brier {spec['summary']['brier_score']:.6f} ratios {spec['summary']['calibration_ratio_by_fold']} ({time.time() - started:.0f}s)")
            variants.append(spec)
    original = variants[0]
    calibrated = min(variants, key=lambda s: (s["summary"]["brier_score"], s["summary"]["mean_abs_log_calibration_ratio"]))

    with_interactions, trail = interaction_search(monthly, direct, windows, calibrated)
    wider = evaluate(monthly, direct, WIDER + [f for f in with_interactions["features"] if f in INTERACTIONS], windows, calibrated["trend"], calibrated["recalibration_months"])
    fs.log(f"amplio {label(wider)}: PR-AUC {wider['summary']['pr_auc']:.5f} lift10 {wider['summary']['lift_at_10_percent']:.4f}")
    finalists = [original, calibrated] + ([with_interactions] if with_interactions is not calibrated else []) + [wider]
    ceiling = previous["lightgbm_all"]
    check = ceiling_check(finalists, ceiling["summary"])

    # Final: el más simple dentro de 2% del mejor hazard (no se exige al techo si ninguno llega).
    best_pr = max(s["summary"]["pr_auc"] for s in finalists)
    best_lift = max(s["summary"]["lift_at_10_percent"] for s in finalists)
    eligible = [
        s for s in finalists[1:]
        if s["summary"]["pr_auc"] >= (1 - fs.PARSIMONY_TOLERANCE) * best_pr and s["summary"]["lift_at_10_percent"] >= (1 - fs.PARSIMONY_TOLERANCE) * best_lift
    ] or finalists[1:]
    final = min(eligible, key=lambda s: (s["parameters"], s["summary"]["brier_score"]))

    coefficients, model_references = fs.coefficient_stability(final)
    full_l2 = final["folds"][-1]["metrics"]["l2"]
    full_model = fit_converged(monthly, final["features"], full_l2, final["trend"], final["recalibration_months"])
    tree_features = [f for f in final["features"] if f != "calendar_month" and f not in INTERACTIONS]
    groups = fs.tree_groups(monthly, direct, final, full_l2, model=full_model, tree_features=tree_features)
    calibration = fs.subgroup_calibration(final, tree_features)

    result = {
        "artifact": "engineering-hazard-adjustment",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": hz.KNOWLEDGE_BOUNDARY.strftime("%Y-%m-%d"),
        "deliverable_classification": "presentation",
        "authorization": {"path": str(fs.AUTHORIZATION.relative_to(ROOT)), "id": authorization["authorization_id"]},
        "frame": {
            "first_snapshot": str(monthly["snapshot_date"].min().date()),
            "last_snapshot": str(monthly["snapshot_date"].max().date()),
            "person_months_read": totals["person_months"],
            "monthly_exposures": int(monthly["exposure_count"].sum()),
            "six_month_exposures": int(direct["exposure_count"].sum()),
            "six_month_events": int(direct["event_count"].sum()),
        },
        "design": {
            "starting_features": CHOSEN,
            "trend_modes": {"linear": "tendencia lineal extrapolada", "none": "sin tendencia", "frozen": "tendencia congelada en el último mes de entrenamiento"},
            "recalibration": "desplazamiento del intercepto que iguala salidas estimadas y observadas en los 12 meses previos al corte",
            "calibration_choice_rule": "menor Brier medio en 4 folds",
            "interactions": {k: list(v) for k, v in INTERACTIONS.items()},
            "interaction_references": references,
            "interaction_rule": "gana >= 3 de 4 folds en PR-AUC y lift@10% sin peor Brier medio; máximo tres",
            "final_rule": "menos parámetros dentro de 2% del mejor hazard en PR-AUC y lift@10%; se informa la distancia al techo LightGBM",
            "fold_starts": ro.FOLD_STARTS,
            "l2_grid": ro.L2_GRID,
        },
        "trend_variants": [public(s) for s in variants],
        "calibration_choice": label(calibrated),
        "interaction_trail": trail,
        "finalists": [public(s) for s in finalists],
        "ceiling": {"source": str(SELECTION_RESULTS.relative_to(ROOT)), "features": ceiling["features"], "summary": ceiling["summary"]},
        "ceiling_check": check,
        "final": public(final),
        "final_vs_original": promotion(final, original),
        "full_model_recalibration_offset": round(full_model.recalibration_offset, 6),
        "coefficients": coefficients,
        "references": model_references,
        "groups": groups,
        "subgroup_calibration": calibration,
        "privacy": {
            "employee_level_rows_persisted": False,
            "employee_ids_selected": False,
            "aggregate_training_frame_persisted": False,
            "individual_scores_published": False,
            "minimum_group_people_per_snapshot": fs.MIN_PEOPLE,
            "minimum_published_events": fs.MIN_EVENTS,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "adjustment-results.json"
    report_path = output_dir / "adjustment-report.md"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    manifest = {
        "artifact": result["artifact"],
        "created_at_utc": result["created_at_utc"],
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "authorization": result["authorization"],
        "queries": {"calendar": str(hz.CALENDAR_QUERY.relative_to(ROOT)), "person_month_frame": str(fs.FRAME_QUERY.relative_to(ROOT))},
        "query_sha256": {"calendar": hz.sha256_file(hz.CALENDAR_QUERY), "person_month_frame": hz.sha256_file(fs.FRAME_QUERY)},
        "ceiling_source": str(SELECTION_RESULTS.relative_to(ROOT)),
        "ceiling_source_sha256": hz.sha256_file(SELECTION_RESULTS),
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": hz.sha256_file(result_path),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": hz.sha256_file(report_path),
        "employee_level_rows_persisted": False,
        "aggregate_training_frame_persisted": False,
    }
    (output_dir / "adjustment-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(build_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
