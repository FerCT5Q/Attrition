"""Ajusta y valida el modelo agregado de attrition voluntario para Critical Tech.

El script consulta únicamente celdas agregadas. employee_id se mantiene dentro
de Redshift para deduplicar y contar; nunca se devuelve ni se persiste. El
frame agregado se conserva sólo en memoria durante la ejecución y el output
contiene métricas, coeficientes filtrados y cohortes publicables.

Modelo champion:
    hazard discreto mensual con enlace complementary log-log y penalización L2.

Benchmark:
    regresión logística agrupada directamente a seis meses.

La implementación usa IRLS con NumPy para no depender de paquetes estadísticos
adicionales en el entorno del proyecto.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import timezone, datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
HELPER = (
    ROOT
    / ".codex"
    / "skills"
    / "attrition-redshift-db"
    / "scripts"
    / "run_readonly_query.py"
)
CALENDAR_QUERY = ROOT / "queries" / "profiles" / "critical_tech_model_calendar_20260907.sql"
MONTHLY_QUERY = ROOT / "queries" / "profiles" / "critical_tech_model_frame_20260907.sql"
SIX_MONTH_QUERY = (
    ROOT / "queries" / "profiles" / "critical_tech_six_month_model_frame_20260907.sql"
)
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "critical-tech" / "20260907" / "model"
KNOWLEDGE_BOUNDARY = pd.Timestamp("2026-09-07")
MIN_MODEL_DATE = pd.Timestamp("2020-07-26")
TRAIN_END = pd.Timestamp("2024-12-29")
VALIDATION_START = pd.Timestamp("2025-01-26")
VALIDATION_END = pd.Timestamp("2025-07-27")
HOLDOUT_START = pd.Timestamp("2025-08-24")
HOLDOUT_END = pd.Timestamp("2026-02-22")
FEATURES = [
    "seg",
    "level_grouped",
    "company_tenure_band",
    "manager_change_12m",
    "calendar_month",
]
EXPECTED_MONTHLY_COLUMNS = {
    "snapshot_date",
    "seg",
    "level_grouped",
    "company_tenure_band",
    "manager_change_12m",
    "exposure_count",
    "distinct_employee_count",
    "event_count",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run_readonly_query(path: Path, max_rows: int = 1000) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(path),
            "--max-rows",
            str(max_rows),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Falló la consulta read-only {path}: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Respuesta no JSON del helper para {path}") from exc
    if payload.get("truncated"):
        raise RuntimeError(f"Resultado truncado para {path}; se requiere dividir el periodo.")
    return payload


def render_query(template: str, start: pd.Timestamp, end: pd.Timestamp) -> str:
    start_text = start.strftime("%Y-%m-%d")
    end_text = end.strftime("%Y-%m-%d")
    return template.replace("__PERIOD_START__", start_text).replace("__PERIOD_END__", end_text)


def fetch_calendar() -> list[pd.Timestamp]:
    payload = run_readonly_query(CALENDAR_QUERY, max_rows=100)
    if set(payload.get("columns", [])) != {"snapshot_date", "next_snapshot_date"}:
        raise RuntimeError("El calendario devolvió columnas inesperadas.")
    values = [
        pd.Timestamp(row["snapshot_date"])
        for row in payload.get("rows", [])
        if pd.Timestamp(row["snapshot_date"]) >= MIN_MODEL_DATE
    ]
    if not values:
        raise RuntimeError("No hay snapshots Critical Tech en la ventana del modelo.")
    return values


def fetch_frame(
    template_path: Path,
    dates: list[pd.Timestamp],
    expected_columns: set[str],
    max_dates_per_query: int = 2,
) -> tuple[pd.DataFrame, str]:
    """Consulta periodos pequeños y concatena sólo celdas agregadas en memoria."""
    template = template_path.read_text(encoding="utf-8")
    all_rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="critical-tech-model-", dir=ROOT / ".tmp") as temp_dir:
        temp_root = Path(temp_dir)
        for offset in range(0, len(dates), max_dates_per_query):
            chunk = dates[offset : offset + max_dates_per_query]
            rendered = render_query(template, chunk[0], chunk[-1])
            temp_query = temp_root / f"frame_{offset:04d}.sql"
            temp_query.write_text(rendered, encoding="utf-8")
            payload = run_readonly_query(temp_query, max_rows=1000)
            columns = set(payload.get("columns", []))
            if columns != expected_columns:
                raise RuntimeError(
                    f"Columnas inesperadas en {template_path.name}: "
                    f"{sorted(columns)}"
                )
            all_rows.extend(payload.get("rows", []))

    frame_hash = sha256_json(all_rows)
    frame = pd.DataFrame(all_rows)
    if frame.empty:
        raise RuntimeError(f"El frame quedó vacío: {template_path}")
    return frame, frame_hash


def prepare_frame(frame: pd.DataFrame, six_month: bool = False) -> pd.DataFrame:
    result = frame.copy()
    result["snapshot_date"] = pd.to_datetime(result["snapshot_date"])
    for column in [
        "seg",
        "level_grouped",
        "company_tenure_band",
        "manager_change_12m",
    ]:
        result[column] = result[column].fillna("(unknown)").astype(str)
    for column in ["exposure_count", "distinct_employee_count", "event_count"]:
        result[column] = pd.to_numeric(result[column], errors="raise").astype(int)
    if (result["exposure_count"] <= 0).any():
        raise RuntimeError("El frame contiene exposiciones no positivas.")
    if (result["event_count"] < 0).any() or (
        result["event_count"] > result["exposure_count"]
    ).any():
        raise RuntimeError("El target agregado está fuera de [0, exposure].")
    if (result["distinct_employee_count"] > result["exposure_count"]).any():
        raise RuntimeError("El conteo distinto supera las exposiciones.")
    result["calendar_month"] = result["snapshot_date"].dt.month.astype(str)
    result["target_rate"] = result["event_count"] / result["exposure_count"]
    result["six_month_frame"] = bool(six_month)
    return result.sort_values(
        ["snapshot_date", "seg", "level_grouped", "company_tenure_band", "manager_change_12m"]
    ).reset_index(drop=True)


def subset_dates(frame: pd.DataFrame, start: pd.Timestamp | None, end: pd.Timestamp | None) -> pd.DataFrame:
    mask = pd.Series(True, index=frame.index)
    if start is not None:
        mask &= frame["snapshot_date"] >= start
    if end is not None:
        mask &= frame["snapshot_date"] <= end
    selected = frame.loc[mask].copy()
    if selected.empty:
        raise RuntimeError(f"No hay datos en la ventana {start} a {end}.")
    return selected


@dataclass
class DesignEncoder:
    features: list[str]
    references: dict[str, str]
    categories: dict[str, list[str]]
    time_origin: pd.Timestamp
    time_scale: float
    columns: list[str]

    @classmethod
    def fit(cls, frame: pd.DataFrame, features: list[str] | None = None) -> "DesignEncoder":
        selected = features or FEATURES
        references: dict[str, str] = {}
        categories: dict[str, list[str]] = {}
        for feature in selected:
            if feature == "calendar_month":
                values = frame[feature].astype(str)
            else:
                values = frame[feature].fillna("(unknown)").astype(str)
            weighted = (
                frame.assign(_value=values)
                .groupby("_value", dropna=False)["exposure_count"]
                .sum()
                .sort_values(ascending=False)
            )
            if weighted.empty:
                raise RuntimeError(f"No hay categorías para {feature}.")
            references[feature] = str(weighted.index[0])
            categories[feature] = sorted(str(value) for value in weighted.index)

        months = frame["snapshot_date"].dt.year * 12 + frame["snapshot_date"].dt.month
        origin = frame["snapshot_date"].min()
        weighted_mean = float(np.average(months.astype(float), weights=frame["exposure_count"]))
        weighted_var = float(
            np.average((months.astype(float) - weighted_mean) ** 2, weights=frame["exposure_count"])
        )
        scale = math.sqrt(weighted_var) if weighted_var > 1e-8 else 1.0

        columns = ["intercept", "time_index"]
        for feature in selected:
            for value in categories[feature]:
                if value != references[feature]:
                    columns.append(f"{feature}={value}")
        return cls(selected, references, categories, origin, scale, columns)

    def _time_index(self, dates: pd.Series) -> np.ndarray:
        months = dates.dt.year.to_numpy() * 12 + dates.dt.month.to_numpy()
        origin_month = self.time_origin.year * 12 + self.time_origin.month
        return (months - origin_month) / self.time_scale

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        matrix = [np.ones(len(frame), dtype=float), self._time_index(frame["snapshot_date"])]
        for feature in self.features:
            values = frame[feature].fillna("(unknown)").astype(str)
            reference = self.references[feature]
            for category in self.categories[feature]:
                if category == reference:
                    continue
                matrix.append((values == category).astype(float).to_numpy())
        return np.column_stack(matrix)


@dataclass
class IRLSModel:
    link: str
    l2: float
    beta: np.ndarray
    encoder: DesignEncoder
    iterations: int
    converged: bool

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        eta = self.encoder.transform(frame) @ self.beta
        if self.link == "cloglog":
            exponent = np.exp(np.clip(eta, -30.0, 5.0))
            values = 1.0 - np.exp(-exponent)
        elif self.link == "logit":
            values = 1.0 / (1.0 + np.exp(-np.clip(eta, -30.0, 30.0)))
        else:
            raise ValueError(f"Link no soportado: {self.link}")
        return np.clip(values, 1e-8, 1.0 - 1e-8)


def fit_irls(
    frame: pd.DataFrame,
    link: str,
    l2: float,
    encoder: DesignEncoder | None = None,
    max_iter: int = 150,
) -> IRLSModel:
    encoder = encoder or DesignEncoder.fit(frame)
    x = encoder.transform(frame)
    n = frame["exposure_count"].to_numpy(dtype=float)
    successes = frame["event_count"].to_numpy(dtype=float)
    y = successes / n
    weighted_rate = float(successes.sum() / n.sum())
    weighted_rate = min(max(weighted_rate, 1e-6), 1.0 - 1e-6)
    if link == "cloglog":
        intercept = math.log(-math.log(1.0 - weighted_rate))
    elif link == "logit":
        intercept = math.log(weighted_rate / (1.0 - weighted_rate))
    else:
        raise ValueError(f"Link no soportado: {link}")
    beta = np.zeros(x.shape[1], dtype=float)
    beta[0] = intercept
    penalty = np.eye(x.shape[1], dtype=float)
    penalty[0, 0] = 0.0
    penalty *= float(l2) * max(float(np.mean(n)), 1.0)
    converged = False

    for iteration in range(1, max_iter + 1):
        eta = x @ beta
        if link == "cloglog":
            exponent = np.exp(np.clip(eta, -30.0, 5.0))
            p = 1.0 - np.exp(-exponent)
            derivative = exponent * np.exp(-exponent)
        else:
            p = 1.0 / (1.0 + np.exp(-np.clip(eta, -30.0, 30.0)))
            derivative = p * (1.0 - p)
        p = np.clip(p, 1e-8, 1.0 - 1e-8)
        variance = np.maximum(p * (1.0 - p), 1e-8)
        derivative = np.maximum(derivative, 1e-10)
        weights = n * (derivative**2) / variance
        working = eta + (y - p) / derivative
        normal = x.T @ (weights[:, None] * x) + penalty
        rhs = x.T @ (weights * working)
        try:
            next_beta = np.linalg.solve(normal, rhs)
        except np.linalg.LinAlgError:
            next_beta = np.linalg.lstsq(normal, rhs, rcond=None)[0]
        delta = float(np.max(np.abs(next_beta - beta)))
        beta = next_beta
        if not np.isfinite(beta).all():
            raise RuntimeError(f"IRLS produjo coeficientes no finitos en iteración {iteration}.")
        if delta < 1e-7:
            converged = True
            break
    return IRLSModel(link, l2, beta, encoder, iteration, converged)


def brier_score(frame: pd.DataFrame, predictions: np.ndarray) -> float:
    n = frame["exposure_count"].to_numpy(dtype=float)
    events = frame["event_count"].to_numpy(dtype=float)
    non_events = n - events
    p = np.clip(predictions, 1e-8, 1.0 - 1e-8)
    return float(
        np.sum(events * (1.0 - p) ** 2 + non_events * p**2) / np.sum(n)
    )


def log_loss(frame: pd.DataFrame, predictions: np.ndarray) -> float:
    n = frame["exposure_count"].to_numpy(dtype=float)
    events = frame["event_count"].to_numpy(dtype=float)
    non_events = n - events
    p = np.clip(predictions, 1e-8, 1.0 - 1e-8)
    return float(
        (-np.sum(events * np.log(p) + non_events * np.log(1.0 - p))) / np.sum(n)
    )


def pr_auc(frame: pd.DataFrame, predictions: np.ndarray) -> float:
    events = frame["event_count"].to_numpy(dtype=float)
    n = frame["exposure_count"].to_numpy(dtype=float)
    order = np.argsort(-predictions, kind="mergesort")
    events = events[order]
    n = n[order]
    cumulative_events = np.cumsum(events)
    cumulative_exposure = np.cumsum(n)
    total_events = float(events.sum())
    if total_events <= 0:
        return 0.0
    recall = cumulative_events / total_events
    precision = cumulative_events / np.maximum(cumulative_exposure, 1.0)
    previous_recall = np.concatenate(([0.0], recall[:-1]))
    return float(np.sum((recall - previous_recall) * precision))


def lift_at_fraction(
    frame: pd.DataFrame, predictions: np.ndarray, fraction: float
) -> float | None:
    events = frame["event_count"].to_numpy(dtype=float)
    n = frame["exposure_count"].to_numpy(dtype=float)
    total_n = float(n.sum())
    total_events = float(events.sum())
    if total_n <= 0 or total_events <= 0:
        return None
    order = np.argsort(-predictions, kind="mergesort")
    target_n = total_n * fraction
    selected_n = 0.0
    selected_events = 0.0
    for index in order:
        take = min(float(n[index]), target_n - selected_n)
        if take <= 0:
            break
        selected_n += take
        selected_events += float(events[index]) * take / float(n[index])
        if selected_n >= target_n:
            break
    selected_rate = selected_events / max(selected_n, 1.0)
    overall_rate = total_events / total_n
    return float(selected_rate / overall_rate) if overall_rate > 0 else None


def calibration_bins(
    frame: pd.DataFrame, predictions: np.ndarray, bin_count: int = 5
) -> list[dict]:
    order = np.argsort(predictions, kind="mergesort")
    n = frame["exposure_count"].to_numpy(dtype=float)[order]
    events = frame["event_count"].to_numpy(dtype=float)[order]
    ordered_predictions = predictions[order]
    cumulative = np.cumsum(n)
    total_n = float(n.sum())
    rows: list[dict] = []
    start = 0
    for bin_number in range(bin_count):
        target = total_n * (bin_number + 1) / bin_count
        stop = int(np.searchsorted(cumulative, target, side="left")) + 1
        stop = min(max(stop, start + 1), len(order))
        bin_n = float(n[start:stop].sum())
        bin_events = float(events[start:stop].sum())
        if bin_n >= 30:
            rows.append(
                {
                    "bin": bin_number + 1,
                    "exposures": int(bin_n),
                    "events": int(bin_events) if bin_events >= 30 else None,
                    "observed_rate_percent": round(100.0 * bin_events / bin_n, 4)
                    if bin_events >= 30
                    else None,
                    "mean_predicted_percent": round(
                        100.0
                        * float(np.average(ordered_predictions[start:stop], weights=n[start:stop])),
                        4,
                    ),
                    "published": bool(bin_events >= 30),
                }
            )
        start = stop
        if start >= len(order):
            break
    return rows


def metrics(frame: pd.DataFrame, predictions: np.ndarray) -> dict:
    n = int(frame["exposure_count"].sum())
    events = int(frame["event_count"].sum())
    lift10 = lift_at_fraction(frame, predictions, 0.10)
    lift20 = lift_at_fraction(frame, predictions, 0.20)
    return {
        "rows": int(len(frame)),
        "snapshot_count": int(frame["snapshot_date"].nunique()),
        "exposures": n,
        "events": events,
        "observed_rate_percent": round(100.0 * events / n, 4) if n else None,
        "brier_score": round(brier_score(frame, predictions), 8),
        "log_loss": round(log_loss(frame, predictions), 8),
        "pr_auc": round(pr_auc(frame, predictions), 8),
        "lift_at_10_percent": round(lift10, 8) if lift10 is not None else None,
        "lift_at_20_percent": round(lift20, 8) if lift20 is not None else None,
        "calibration": calibration_bins(frame, predictions),
    }


def six_month_predictions(model: IRLSModel, frame: pd.DataFrame) -> np.ndarray:
    pieces = []
    for month_ahead in range(6):
        part = frame.copy()
        part["snapshot_date"] = part["snapshot_date"] + pd.DateOffset(months=month_ahead)
        # El calendario futuro es conocido al momento del snapshot; las demás
        # covariables se congelan para no imputar cambios futuros no observables.
        part["calendar_month"] = part["snapshot_date"].dt.month.astype(str)
        pieces.append(model.predict(part))
    hazards = np.column_stack(pieces)
    return np.clip(1.0 - np.prod(1.0 - hazards, axis=1), 1e-8, 1.0 - 1e-8)


def cohort_table(
    frame: pd.DataFrame,
    predictions: np.ndarray,
    keys: list[str],
    overall_rate: float,
    limit: int = 20,
) -> list[dict]:
    data = frame[keys + ["exposure_count", "event_count"]].copy()
    data["_prediction"] = predictions
    data["_predicted_events"] = data["exposure_count"] * data["_prediction"]
    grouped = (
        data.groupby(keys, dropna=False)
        .agg(
            exposure_count=("exposure_count", "sum"),
            event_count=("event_count", "sum"),
            predicted_events=("_predicted_events", "sum"),
        )
        .reset_index()
    )
    grouped["observed_rate_percent"] = 100.0 * grouped["event_count"] / grouped["exposure_count"]
    grouped["predicted_rate_percent"] = (
        100.0 * grouped["predicted_events"] / grouped["exposure_count"]
    )
    grouped["lift_vs_overall"] = grouped["observed_rate_percent"] / (100.0 * overall_rate)
    public = grouped[
        (grouped["exposure_count"] >= 30) & (grouped["event_count"] >= 30)
    ].sort_values(["lift_vs_overall", "event_count"], ascending=[False, False])
    rows: list[dict] = []
    for _, row in public.head(limit).iterrows():
        item = {key: str(row[key]) for key in keys}
        item.update(
            {
                "employee_snapshot_exposures": int(row["exposure_count"]),
                "voluntary_events": int(row["event_count"]),
                "observed_rate_percent": round(float(row["observed_rate_percent"]), 4),
                "predicted_rate_percent": round(float(row["predicted_rate_percent"]), 4),
                "lift_vs_overall": round(float(row["lift_vs_overall"]), 4),
            }
        )
        rows.append(item)
    return rows


def coefficient_summary(model: IRLSModel, train: pd.DataFrame, limit: int = 15) -> list[dict]:
    exposure_by_value: dict[tuple[str, str], int] = {}
    events_by_value: dict[tuple[str, str], int] = {}
    for feature in model.encoder.features:
        values = train[feature].fillna("(unknown)").astype(str)
        for value, part in train.assign(_value=values).groupby("_value"):
            exposure_by_value[(feature, str(value))] = int(part["exposure_count"].sum())
            events_by_value[(feature, str(value))] = int(part["event_count"].sum())

    candidates = []
    for index, label in enumerate(model.encoder.columns):
        if index < 2:
            continue
        feature, value = label.split("=", 1)
        exposure = exposure_by_value.get((feature, value), 0)
        events = events_by_value.get((feature, value), 0)
        if exposure < 100 or events < 30:
            continue
        candidates.append(
            {
                "feature": feature,
                "level": value,
                "reference_level": model.encoder.references[feature],
                "coefficient": round(float(model.beta[index]), 6),
                "relative_hazard_scale": round(float(math.exp(np.clip(model.beta[index], -5, 5))), 6),
                "training_exposures": exposure,
                "training_events": events,
            }
        )
    candidates.sort(key=lambda item: item["coefficient"], reverse=True)
    return candidates[:limit]


def selection_result(
    link: str,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    candidate_l2: Iterable[float],
) -> tuple[float, IRLSModel, list[dict]]:
    candidates = []
    best: tuple[float, float, IRLSModel] | None = None
    for l2 in candidate_l2:
        encoder = DesignEncoder.fit(train)
        model = fit_irls(train, link=link, l2=float(l2), encoder=encoder)
        predictions = (
            six_month_predictions(model, validation)
            if link == "cloglog"
            else model.predict(validation)
        )
        score = brier_score(validation, predictions)
        candidates.append(
            {
                "l2": float(l2),
                "validation_brier_score": round(float(score), 8),
                "iterations": model.iterations,
                "converged": model.converged,
            }
        )
        if best is None or score < best[1]:
            best = (float(l2), float(score), model)
    if best is None:
        raise RuntimeError("No se pudo seleccionar una penalización.")
    return best[0], best[2], candidates


def self_test() -> None:
    dates = pd.date_range("2020-01-26", periods=18, freq="MS")
    rows = []
    for index, snapshot in enumerate(dates):
        for manager in ["no", "yes"]:
            exposures = 900
            events = 8 + (index // 6) + (12 if manager == "yes" else 0)
            rows.append(
                {
                    "snapshot_date": snapshot,
                    "seg": "A",
                    "level_grouped": "L7",
                    "company_tenure_band": "1-3 years",
                    "manager_change_12m": manager,
                    "exposure_count": exposures,
                    "distinct_employee_count": exposures,
                    "event_count": events,
                }
            )
    frame = prepare_frame(pd.DataFrame(rows))
    model = fit_irls(frame, "cloglog", 0.1)
    assert model.converged
    assert np.isfinite(model.beta).all()
    assert np.all((model.predict(frame) > 0) & (model.predict(frame) < 1))

    brier_frame = pd.DataFrame(
        {
            "exposure_count": [100],
            "event_count": [20],
            "target_rate": [0.20],
        }
    )
    assert np.isclose(brier_score(brier_frame, np.array([0.20])), 0.16)

    class CalendarProbe:
        def predict(self, probe_frame: pd.DataFrame) -> np.ndarray:
            return np.where(
                probe_frame["calendar_month"].astype(str).to_numpy() == "2",
                0.20,
                0.10,
            )

    calendar_probe_frame = pd.DataFrame(
        {
            "snapshot_date": [pd.Timestamp("2020-01-26")],
            "calendar_month": ["1"],
        }
    )
    expected_six_month_risk = 1.0 - (1.0 - 0.20) * (1.0 - 0.10) ** 5
    assert np.isclose(
        six_month_predictions(CalendarProbe(), calendar_probe_frame)[0],
        expected_six_month_risk,
    )
    print("self-test: pass")


def build_report(results: dict) -> str:
    champion = results["final_holdout"]["champion_six_month"]
    benchmark = results["final_holdout"]["direct_logistic_six_month"]
    monthly = results["final_holdout"]["champion_monthly"]
    better = (
        champion["brier_score"] <= benchmark["brier_score"]
        and champion["pr_auc"] >= benchmark["pr_auc"]
        and champion["lift_at_10_percent"] >= benchmark["lift_at_10_percent"]
    )
    lines = [
        "# Modelo de attrition voluntario de Critical Tech",
        "",
        f"Fecha de conocimiento: **{results['knowledge_boundary']}**.",
        "",
        "## Resultado ejecutivo",
        "",
        "Se ajustó un modelo pooled de supervivencia discreta mensual con enlace "
        "cloglog, usando sólo información disponible en el snapshot. La salida "
        "publicada es de cohortes y métricas agregadas; no se generaron scores "
        "individuales.",
        "",
        f"En el holdout final de seis meses, el champion obtuvo Brier "
        f"**{champion['brier_score']:.6f}**, PR-AUC **{champion['pr_auc']:.6f}** "
        f"y lift@10% **{champion['lift_at_10_percent']:.4f}**.",
        f"El benchmark logístico obtuvo Brier **{benchmark['brier_score']:.6f}** "
        f"y PR-AUC **{benchmark['pr_auc']:.6f}**.",
        "",
        (
            "El candidato cloglog pasa el gate de Brier, PR-AUC y lift de esta "
            "ejecución; todavía requiere estabilidad temporal y fairness antes "
            "de una promoción operativa."
            if better
            else "La evidencia no justifica declarar superior al candidato "
            "cloglog; se conservan hazard y logística como referencias hasta "
            "completar estabilidad temporal y fairness."
        ),
        "",
        "## Diseño",
        "",
        "- Target mensual: evento Voluntary entre el snapshot y el siguiente snapshot real.",
        "- Target de evaluación: al menos un evento Voluntary en los seis meses posteriores.",
        "- Champion: hazard discreto pooled con enlace complementary log-log y L2.",
        "- Benchmark: regresión logística agrupada directa a seis meses.",
        "- Validación: train temporal hasta 2024-12-29; selección en 2025-01-26–2025-07-27; holdout final 2025-08-24–2026-02-22.",
        "- Unidad consultada: celdas agregadas por snapshot, no filas employee-level.",
        "- Publicación: sólo grupos con al menos 30 exposiciones y 30 eventos.",
        "",
        "## Resultado mensual",
        "",
        f"El hazard mensual en el holdout obtuvo Brier **{monthly['brier_score']:.6f}**, "
        f"PR-AUC **{monthly['pr_auc']:.6f}** y lift@10% "
        f"**{monthly['lift_at_10_percent']:.4f}**.",
        "",
        "## Cohortes observadas en el holdout",
        "",
        "Estas filas son asociaciones agregadas para priorizar diagnóstico. "
        "No son una lista de personas ni demuestran causalidad.",
        "",
        "| Segmento | Tenure | Exposiciones | Eventos | Tasa observada | Tasa predicha | Lift |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in results["cohorts"]["segment_tenure"]:
        lines.append(
            f"| {row['seg']} | {row['company_tenure_band']} | "
            f"{row['employee_snapshot_exposures']} | {row['voluntary_events']} | "
            f"{row['observed_rate_percent']:.4f}% | {row['predicted_rate_percent']:.4f}% | "
            f"{row['lift_vs_overall']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Señales y acciones",
            "",
            "El coeficiente positivo es una señal ajustada, no una causa. Para "
            "cada cohorte se debe validar la palanca con HRBP y después medir "
            "un piloto o diseño cuasi-experimental.",
            "",
            "| Señal | Nivel | Escala relativa del hazard | Acción candidata |",
            "|---|---|---:|---|",
        ]
    )
    for item in results["coefficients"][:10]:
        action = "Revisar carrera, movilidad y claridad de scope."
        if item["feature"] == "manager_change_12m":
            action = "Revisar handoff, prioridades y enablement después del cambio."
        elif item["feature"] == "company_tenure_band":
            action = "Revisar trayectoria, onboarding o movilidad según la etapa."
        lines.append(
            f"| {item['feature']} | {item['level']} vs {item['reference_level']} | "
            f"{item['relative_hazard_scale']:.4f} | {action} |"
        )
    lines.extend(
        [
            "",
            "## Limitaciones y siguientes pasos",
            "",
            "- Voluntary Exception se excluyó del target primario hasta recibir una decisión de negocio; debe ejecutarse una sensibilidad antes de usarlo operativamente.",
            "- La membership histórica usa el catálogo vigente; el crosswalk de critical_tech_archive sigue bloqueado.",
            "- El champion v1 usa señales core. Promotion y transfer permanecen en el screen y en análisis de sensibilidad, no como drivers confirmados.",
            "- Un driver predictivo no demuestra que modificarlo reduzca attrition.",
            "- No se publican filas employee-level, IDs, nombres, categorías protegidas ni compensación exacta.",
            "",
            "Fuentes SQL:",
            "- queries/profiles/critical_tech_model_calendar_20260907.sql",
            "- queries/profiles/critical_tech_model_frame_20260907.sql",
            "- queries/profiles/critical_tech_six_month_model_frame_20260907.sql",
            "- queries/audits/critical_tech_core_model_cardinality_20260907.sql",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    output_dir = (ROOT / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    calendar = fetch_calendar()
    monthly_raw, monthly_frame_hash = fetch_frame(
        MONTHLY_QUERY, calendar, EXPECTED_MONTHLY_COLUMNS
    )
    direct_dates = [value for value in calendar if value <= HOLDOUT_END]
    direct_raw, direct_frame_hash = fetch_frame(
        SIX_MONTH_QUERY, direct_dates, EXPECTED_MONTHLY_COLUMNS
    )
    monthly = prepare_frame(monthly_raw)
    direct = prepare_frame(direct_raw, six_month=True)

    train_monthly = subset_dates(monthly, None, TRAIN_END)
    validation_direct = subset_dates(direct, VALIDATION_START, VALIDATION_END)
    train_direct = subset_dates(direct, None, TRAIN_END)
    holdout_monthly = subset_dates(monthly, HOLDOUT_START, HOLDOUT_END)
    holdout_direct = subset_dates(direct, HOLDOUT_START, HOLDOUT_END)

    l2_grid = [0.0, 0.01, 0.1, 1.0, 10.0]
    champion_l2, _, champion_selection = selection_result(
        "cloglog", train_monthly, validation_direct, l2_grid
    )
    logistic_l2, _, logistic_selection = selection_result(
        "logit", train_direct, validation_direct, l2_grid
    )

    final_train_monthly = subset_dates(monthly, None, VALIDATION_END)
    final_train_direct = subset_dates(direct, None, VALIDATION_END)
    champion_encoder = DesignEncoder.fit(final_train_monthly)
    champion = fit_irls(
        final_train_monthly,
        link="cloglog",
        l2=champion_l2,
        encoder=champion_encoder,
    )
    logistic_encoder = DesignEncoder.fit(final_train_direct)
    logistic = fit_irls(
        final_train_direct,
        link="logit",
        l2=logistic_l2,
        encoder=logistic_encoder,
    )

    champion_monthly_pred = champion.predict(holdout_monthly)
    champion_six_pred = six_month_predictions(champion, holdout_direct)
    logistic_six_pred = logistic.predict(holdout_direct)
    train_rate = float(
        final_train_direct["event_count"].sum() / final_train_direct["exposure_count"].sum()
    )
    baseline_six_pred = np.full(len(holdout_direct), train_rate, dtype=float)

    result = {
        "artifact": "critical-tech-discrete-hazard-model",
        "model_id": "critical-tech-voluntary-attrition-discrete-hazard",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": KNOWLEDGE_BOUNDARY.strftime("%Y-%m-%d"),
        "population": {
            "worker_type": "Employee",
            "employee_type": "Regular",
            "active_status": 1,
            "critical_tech_membership": "job_family normalizado contra hrda.critical_tech",
        },
        "privacy": {
            "employee_level_rows_persisted": False,
            "aggregate_training_frame_persisted": False,
            "individual_scores_published": False,
            "minimum_shared_exposures": 30,
            "minimum_shared_events": 30,
        },
        "target": {
            "primary": "Voluntary entre snapshot y siguiente snapshot real",
            "six_month": "Al menos un Voluntary posterior y hasta seis meses",
            "voluntary_exception": "excluded_pending_business_confirmation",
            "involuntary": "excluded",
        },
        "features": FEATURES,
        "windows": {
            "model_first_snapshot": str(monthly["snapshot_date"].min().date()),
            "model_last_snapshot": str(monthly["snapshot_date"].max().date()),
            "train_end": str(TRAIN_END.date()),
            "validation_start": str(VALIDATION_START.date()),
            "validation_end": str(VALIDATION_END.date()),
            "holdout_start": str(HOLDOUT_START.date()),
            "holdout_end": str(HOLDOUT_END.date()),
        },
        "query_results": {
            "monthly_snapshot_count": int(monthly["snapshot_date"].nunique()),
            "monthly_exposures": int(monthly["exposure_count"].sum()),
            "monthly_events": int(monthly["event_count"].sum()),
            "six_month_snapshot_count": int(direct["snapshot_date"].nunique()),
            "six_month_exposures": int(direct["exposure_count"].sum()),
            "six_month_events": int(direct["event_count"].sum()),
            "monthly_frame_sha256": monthly_frame_hash,
            "six_month_frame_sha256": direct_frame_hash,
        },
        "selection": {
            "criterion": "Brier mínimo en validación temporal a seis meses",
            "champion_link": "cloglog",
            "champion_l2": champion_l2,
            "champion_candidates": champion_selection,
            "logistic_l2": logistic_l2,
            "logistic_candidates": logistic_selection,
        },
        "final_holdout": {
            "champion_monthly": metrics(holdout_monthly, champion_monthly_pred),
            "champion_six_month": metrics(holdout_direct, champion_six_pred),
            "direct_logistic_six_month": metrics(holdout_direct, logistic_six_pred),
            "historical_baseline_six_month": metrics(holdout_direct, baseline_six_pred),
        },
        "coefficients": coefficient_summary(champion, final_train_monthly),
        "cohorts": {
            "segment_tenure": cohort_table(
                holdout_direct,
                champion_six_pred,
                ["seg", "company_tenure_band"],
                train_rate,
            ),
            "segment_level": cohort_table(
                holdout_direct,
                champion_six_pred,
                ["seg", "level_grouped"],
                train_rate,
            ),
        },
        "implementation_note": (
            "El frame agregado se procesó en memoria por periodos de máximo dos "
            "snapshots. No se guardaron filas employee-level ni el frame de "
            "entrenamiento."
        ),
    }
    result_path = output_dir / "model-results.json"
    report_path = output_dir / "model-report.md"
    manifest_path = output_dir / "model-manifest.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    manifest = {
        "artifact": result["artifact"],
        "created_at_utc": result["created_at_utc"],
        "knowledge_boundary": result["knowledge_boundary"],
        "queries": {
            "calendar": str(CALENDAR_QUERY.relative_to(ROOT)),
            "monthly_frame": str(MONTHLY_QUERY.relative_to(ROOT)),
            "six_month_frame": str(SIX_MONTH_QUERY.relative_to(ROOT)),
        },
        "query_sha256": {
            "calendar": sha256_file(CALENDAR_QUERY),
            "monthly_frame": sha256_file(MONTHLY_QUERY),
            "six_month_frame": sha256_file(SIX_MONTH_QUERY),
        },
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": sha256_file(result_path),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": sha256_file(report_path),
        "employee_level_rows_persisted": False,
        "aggregate_training_frame_persisted": False,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "manifest": str(manifest_path.relative_to(ROOT)),
                "champion_l2": champion_l2,
                "logistic_l2": logistic_l2,
                "holdout_champion_brier": result["final_holdout"]["champion_six_month"][
                    "brier_score"
                ],
                "holdout_logistic_brier": result["final_holdout"]["direct_logistic_six_month"][
                    "brier_score"
                ],
                "published_segment_tenure_cohorts": len(result["cohorts"]["segment_tenure"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
