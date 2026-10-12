"""Comparación temporal QVoice: cortes de etiquetas, Brier mensual y bootstrap pareado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

import critical_tech_discrete_hazard_model as hz
import engineering_hazard_adjustment as adjustment
import engineering_playbook_priority_model as historical

INTERACTIONS = {"level_x_tenure": ("level_grouped", "tenure_playbook_band"), "tenure_x_manager_changes": ("tenure_playbook_band", "manager_changes_12m")}
DECISION_METRICS = ("pr_auc", "lift_at_10_percent", "brier_score", "calibration_error_pp", "top_quintile_calibration_error_pp")


def monthly_split(frame: pd.DataFrame, cutoff: Any, validation_intervals: int = 3, training_start: Any = "2024-01-01") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Sólo intervalos completamente observados; la igualdad de fecha está permitida."""
    cutoff = pd.Timestamp(cutoff)
    if "label_end" not in frame:
        raise ValueError("Falta la fecha efectiva final de la etiqueta mensual.")
    if (frame["label_end"].notna() & (frame["label_end"] <= frame["snapshot_date"])).any():
        raise ValueError("El intervalo mensual no puede finalizar antes de empezar.")
    eligible = frame.loc[(frame["snapshot_date"] >= pd.Timestamp(training_start)) & (frame["label_end"] <= cutoff)].copy()
    dates = sorted(eligible["snapshot_date"].unique())
    if len(dates) <= validation_intervals:
        raise ValueError("No hay historia anterior suficiente para ajuste interno y validación mensual.")
    validation_dates = dates[-validation_intervals:]
    inner_cutoff = pd.Timestamp(validation_dates[0])
    inner = eligible.loc[eligible["label_end"] <= inner_cutoff].copy()
    validation = eligible.loc[eligible["snapshot_date"].isin(validation_dates)].copy()
    if inner.empty or validation.empty or (inner["snapshot_date"] >= inner_cutoff).any():
        raise ValueError("La partición temporal interna no es válida.")
    return inner, validation, eligible


def period_frame(direct: pd.DataFrame, period: dict, knowledge_boundary: Any) -> pd.DataFrame:
    end = pd.to_datetime(direct["snapshot_date"]) + pd.DateOffset(months=6)
    return direct.loc[(direct["snapshot_date"] >= pd.Timestamp(period["start"])) &
                      (direct["snapshot_date"] <= pd.Timestamp(period["end"])) &
                      (end <= pd.Timestamp(knowledge_boundary))].copy()


def add_interactions(frame: pd.DataFrame, references: dict[str, str]) -> pd.DataFrame:
    result = frame.copy()
    result["calendar_month"] = result["snapshot_date"].dt.month.astype(str)
    for name, (left, right) in INTERACTIONS.items():
        a, b = result[left].astype(str), result[right].astype(str)
        result[name] = np.where((a != references[left]) & (b != references[right]), a + " | " + b, "ref")
    return result


@dataclass
class FrozenModel:
    fitted: hz.IRLSModel
    references: dict[str, str]

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        prepared = frame.copy()
        for column in prepared.select_dtypes(include="category").columns:
            prepared[column] = prepared[column].astype(object)
        return self.fitted.predict(add_interactions(prepared, self.references))


def fit_model(frame: pd.DataFrame, features: list[str], l2: float, penalty_scale: float = 8) -> FrozenModel:
    raw = sorted(({f for f in features if f not in INTERACTIONS and f != "calendar_month"}) |
                 {field for pair in INTERACTIONS.values() for field in pair})
    model_frame = frame.copy()
    for feature in raw:
        # QVoice se conserva como categorica para reducir memoria durante el join,
        # pero el encoder historico espera texto y agrega su propia categoria unknown.
        model_frame[feature] = model_frame[feature].astype(object).where(model_frame[feature].notna(), "(unknown)").astype(str)
    # Colapsar celdas antes de IRLS conserva exactamente el likelihood binomial.
    cells = model_frame.groupby(["snapshot_date"] + raw, observed=True, dropna=False)[["exposure_count", "event_count"]].sum().reset_index()
    cells = cells.loc[cells["exposure_count"] > 0].copy()
    references = {field: str(cells.groupby(field, observed=True)["exposure_count"].sum().idxmax()) for pair in INTERACTIONS.values() for field in pair}
    transformed = add_interactions(cells, references)
    encoder = adjustment.TrendEncoder.build(transformed, features, "none")
    scale = max(float(transformed["exposure_count"].mean()), 1)
    model = historical._ORIGINAL_FIT_IRLS(transformed, "cloglog", l2 * penalty_scale / scale, encoder)
    model.l2 = l2
    return FrozenModel(model, references)


def select_monthly_l2(inner: pd.DataFrame, validation: pd.DataFrame, features: list[str], grid: list[float], penalty_scale: float = 8) -> tuple[float, list[dict]]:
    trials = []
    for value in grid:
        try:
            model = fit_model(inner, features, value, penalty_scale)
            converged = model.fitted.converged
            loss = hz.brier_score(validation, model.predict(validation)) if converged else None
        except (RuntimeError, np.linalg.LinAlgError):
            converged, loss = False, None
        trials.append({"l2": value, "converged": bool(converged), "monthly_brier": loss})
    eligible = [trial for trial in trials if trial["converged"] and trial["monthly_brier"] is not None]
    if not eligible:
        raise ValueError("Ningún ajuste L2 convergió en la validación mensual.")
    # Desempate fijo por L2 menor, sin consultar el periodo de prueba.
    selected = min(eligible, key=lambda row: (row["monthly_brier"], row["l2"]))
    return float(selected["l2"]), trials


def fit_selected(final: pd.DataFrame, features: list[str], selected: float, grid: list[float], penalty_scale: float = 8) -> FrozenModel:
    for value in sorted(v for v in grid if v >= selected):
        try:
            model = fit_model(final, features, value, penalty_scale)
        except (RuntimeError, np.linalg.LinAlgError):
            continue
        if model.fitted.converged:
            return model
    raise ValueError("No converge el ajuste final con la rejilla L2 permitida.")


def _metric_order(p: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    order = np.argsort(-p, kind="stable")
    p_sorted = p[order]
    starts = np.r_[0, np.flatnonzero(p_sorted[1:] != p_sorted[:-1]) + 1]
    return order, starts, p_sorted[starts]


def _weighted_metrics_fixed_order(
    y: np.ndarray,
    p: np.ndarray,
    w: np.ndarray,
    order: np.ndarray,
    starts: np.ndarray,
    ordered_group_p: np.ndarray,
) -> dict:
    total = float(w.sum())
    events = float(np.sum(w * y))
    overall = events / total
    w_sorted, e_sorted = w[order], (w * y)[order]
    group_n, group_e = np.add.reduceat(w_sorted, starts), np.add.reduceat(e_sorted, starts)
    group_p = ordered_group_p
    keep = group_n > 0
    group_n, group_e, group_p = group_n[keep], group_e[keep], group_p[keep]
    cumulative_n, cumulative_e = np.cumsum(group_n), np.cumsum(group_e)
    average_precision = float(np.sum((group_e / events) * cumulative_e / cumulative_n)) if events else 0.0

    def top(fraction: float) -> tuple[float, float]:
        take = np.clip(total * fraction - (cumulative_n - group_n), 0, group_n)
        count = float(take.sum())
        actual = float(np.sum(take * group_e / group_n) / count)
        predicted = float(np.sum(take * group_p) / count)
        return actual, predicted

    rate10, _ = top(0.1)
    actual20, predicted20 = top(0.2)
    estimated = float(np.sum(p * w) / total)
    # y puede ser la proporción de una celda; ésta es pérdida binomial por persona.
    brier = float(np.sum(w * (y * (1 - p) ** 2 + (1 - y) * p ** 2)) / total)
    return {"exposures": total, "event_exposures": events, "pr_auc": average_precision,
            "lift_at_10_percent": rate10 / overall if overall else 0.0, "brier_score": brier,
            "observed_percent": 100 * overall, "predicted_percent": 100 * estimated,
            "calibration_error_pp": 100 * abs(estimated - overall),
            "top_quintile_observed_percent": 100 * actual20, "top_quintile_predicted_percent": 100 * predicted20,
            "top_quintile_calibration_error_pp": 100 * abs(predicted20 - actual20)}


def weighted_metrics(y: np.ndarray, predictions: np.ndarray, weights: np.ndarray | None = None) -> dict:
    """Métricas binomiales con empates agrupados; resultado independiente del orden."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(predictions, dtype=float)
    w = np.ones(len(y), dtype=float) if weights is None else np.asarray(weights, dtype=float)
    if y.shape != p.shape or w.shape != y.shape or not np.isfinite(y).all() or not np.isfinite(p).all() or not np.isfinite(w).all():
        raise ValueError("Métricas: formas incompatibles o valores no finitos.")
    if (w < 0).any() or ((y < 0) | (y > 1)).any() or ((p < 0) | (p > 1)).any() or w.sum() <= 0:
        raise ValueError("Métricas: pesos, respuesta o probabilidad fuera de dominio.")
    return _weighted_metrics_fixed_order(y, p, w, *_metric_order(p))


def frame_metrics(frame: pd.DataFrame, predictions: np.ndarray) -> dict:
    n = frame["exposure_count"].to_numpy(dtype=float)
    y = frame["event_count"].to_numpy(dtype=float) / n
    return weighted_metrics(y, predictions, n)


def component_gate(inner: pd.DataFrame, validation: pd.DataFrame, columns: list[str]) -> list[str]:
    reasons = []
    for name, frame in (("ajuste interno", inner), ("validación", validation)):
        for column in columns:
            if column not in frame or not frame[column].astype(str).isin(("v0", "v1", "v-1", *historical_values())).any():
                reasons.append(f"{column} no tiene respuestas utilizables en {name}.")
    return reasons


def historical_values() -> tuple[str, ...]:
    return ("<50", "50–69", "70–79", "80–89", "90–99", "100")


def bootstrap_paired(person_keys: np.ndarray, y: np.ndarray, prediction_sets: dict[str, np.ndarray], repetitions: int = 500, seed: int = 20261006, confidence_level: float = 0.95) -> dict:
    """Una multiplicidad por persona para todas sus observaciones y todos los modelos."""
    keys = np.asarray(person_keys)
    y = np.asarray(y, dtype=float)
    if len(keys) != len(y) or not prediction_sets or any(len(v) != len(y) for v in prediction_sets.values()):
        raise ValueError("Bootstrap: todas las predicciones deben corresponder a la misma cohorte.")
    if repetitions < 1:
        raise ValueError("El bootstrap necesita al menos una repetición.")
    unique, inverse = np.unique(keys, return_inverse=True)
    if len(unique) < 2:
        raise ValueError("Se necesitan varias personas para estimar incertidumbre.")
    names = list(prediction_sets)
    prepared = {name: np.asarray(prediction_sets[name], dtype=float) for name in names}
    if any(not np.isfinite(values).all() or ((values < 0) | (values > 1)).any() for values in prepared.values()):
        raise ValueError("Bootstrap: hay predicciones no finitas o fuera de dominio.")
    metric_orders = {name: _metric_order(values) for name, values in prepared.items()}
    pairs = [(name, reference) for index, name in enumerate(names) for reference in names[:index]]
    samples = {f"{name}__minus__{ref}": {metric: [] for metric in DECISION_METRICS} for name, ref in pairs}
    generator = np.random.default_rng(seed)
    for _ in range(repetitions):
        multiplicity = generator.multinomial(len(unique), np.full(len(unique), 1 / len(unique)))
        weights = multiplicity[inverse]
        metrics = {
            name: _weighted_metrics_fixed_order(y, prepared[name], weights, *metric_orders[name])
            for name in names
        }
        for name, reference in pairs:
            for metric in DECISION_METRICS:
                samples[f"{name}__minus__{reference}"][metric].append(metrics[name][metric] - metrics[reference][metric])
    alpha = (1 - confidence_level) / 2
    intervals = {pair: {metric: {"lower": float(np.quantile(values, alpha)), "upper": float(np.quantile(values, 1 - alpha))} for metric, values in columns.items()} for pair, columns in samples.items()}
    return {"unit": "persona; todas sus observaciones juntas", "people": len(unique), "repetitions": repetitions,
            "confidence_level": confidence_level, "seed": seed, "paired_differences": intervals,
            "scope": "Incertidumbre de evaluación condicional a los modelos ajustados; no vuelve a seleccionar L2 en cada réplica."}


def decision(periods: list[dict], minimum_periods: int = 2) -> dict:
    complete = [p for p in periods if p.get("main") and p.get("status") == "evaluated" and p.get("complete")]
    if len(complete) < minimum_periods:
        return {"status": "evidencia temporal insuficiente", "complete_main_periods": len(complete)}
    checks = {}
    for reference in ("control", "availability"):
        checks[f"ranking_vs_{reference}"] = all(p["response"]["pr_auc"] > p[reference]["pr_auc"] and p["response"]["lift_at_10_percent"] > p[reference]["lift_at_10_percent"] for p in complete)
        for metric in ("brier_score", "calibration_error_pp", "top_quintile_calibration_error_pp"):
            checks[f"{metric}_vs_{reference}"] = bool(np.mean([p["response"][metric] for p in complete]) <= np.mean([p[reference][metric] for p in complete]))
    return {"status": "prometedora" if all(checks.values()) else "sin mejora demostrada", "complete_main_periods": len(complete), "checks": checks}
