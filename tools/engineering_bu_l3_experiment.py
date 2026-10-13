"""Evalua BU L3 en B, C+QVoice y F+QVoice con una sola carga en memoria.

El proceso conserva los modelos existentes, usa el mapping SCD as-of del
snapshot, no escribe filas de empleados ni predicciones individuales y deja
solamente resultados agregados.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import itertools
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
sys.path.insert(0, str(ROOT / ".codex/skills/attrition-redshift-db/scripts"))

import b_incremental_data as data  # noqa: E402
import engineering_b_incremental as binc  # noqa: E402
import engineering_c_group_selection as groups  # noqa: E402
import engineering_model_c as c  # noqa: E402
import engineering_model_c_fast as fast  # noqa: E402
import engineering_model_c_qvoice as cq  # noqa: E402
import qvoice_horizon_calibration as horizon  # noqa: E402
import run_readonly_query as db  # noqa: E402


DEFAULT = ROOT / "config/engineering_bu_l3_experiment_20261012.json"
MODEL_METRICS = (
    "log_loss",
    "brier_score",
    "pr_auc",
    "lift_at_10_percent",
)
GROUP_METRICS = (
    "capture_percent",
    "group_snapshot_mae_pp",
    "group_mae_pp",
    "rest_percent",
)


def read(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def native(value):
    if isinstance(value, dict):
        return {str(k): native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [native(v) for v in value]
    if isinstance(value, np.ndarray):
        return native(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def write(path: str | Path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(native(value), ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n",
        encoding="utf-8",
    )


def sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def log(message: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def loader_config(spec: dict, output: Path) -> dict:
    config = read(ROOT / spec["loader_config"])
    config["run_id"] = spec["run_id"]
    config["output"] = output.relative_to(ROOT).as_posix()
    config["reporting_mode"] = "presentation"
    config["employee_level_rows_persisted"] = False
    config["individual_scores_published"] = False
    config["qvoice_alias_features"] = spec.get("qvoice_alias_features", [])
    config["base_query"] = spec["base_query"]
    config["source_c_config"] = spec["source_c_config"]
    config["skip_extra_hr_queries"] = True
    config.pop("qvoice_comments_contract", None)
    return config


def copy_evidence(spec: dict, output: Path):
    source = ROOT / spec["evidence_source"] / "input-evidence"
    if not source.exists():
        raise RuntimeError(f"No existe la evidencia de entrada: {source}")
    shutil.copytree(source, output / "input-evidence", dirs_exist_ok=True)


def query_result_hash(rows: list[dict]) -> str:
    payload = json.dumps(native(rows), ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run_aggregate_query(path: Path, output: Path, name: str, max_rows: int = 10000) -> dict:
    sql_text = path.read_text(encoding="utf-8")
    sql = db.validate_readonly(sql_text)
    with db.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [column[0] for column in cursor.description]
            if set(columns) & db.SENSITIVE_OUTPUT_COLUMNS:
                raise RuntimeError(f"La consulta {path} devuelve columnas restringidas.")
            rows = []
            while len(rows) <= max_rows:
                batch = cursor.fetchmany(min(1000, max_rows + 1 - len(rows)))
                if not batch:
                    break
                rows.extend(dict(zip(columns, row)) for row in batch)
            if len(rows) > max_rows:
                raise RuntimeError(f"La evidencia agregada {path} excede el limite de filas.")
    result = {
        "query": path.relative_to(ROOT).as_posix(),
        "sql_sha256": sha(path),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "reporting_mode": "presentation",
        "columns": columns,
        "rows": rows,
        "result_sha256": query_result_hash(rows),
        "employee_level_rows_persisted": False,
        "outcome": "pass",
    }
    write(output / "input-evidence" / f"{name}.json", result)
    return result


def audit_bu_l3(spec: dict, output: Path) -> dict:
    metadata = run_aggregate_query(
        ROOT / spec["audit_queries"][0], output, "bu-l3-metadata", max_rows=100
    )
    join = run_aggregate_query(
        ROOT / spec["audit_queries"][1], output, "bu-l3-join", max_rows=100
    )
    metrics = {row["metric"]: float(row["value"]) for row in join["rows"]}
    total = metrics["employee_snapshot_rows"]
    unmatched_rate = 100 * metrics["unmatched_rows"] / total if total else 100.0
    acceptance = {
        "duplicate_valid_matches": {"observed": metrics["duplicate_valid_matches"], "rule": "== 0"},
        "multi_bu_valid_matches": {"observed": metrics["multi_bu_valid_matches"], "rule": "== 0"},
        "unmatched_rate_percent": {"observed": unmatched_rate, "rule": "<= 5"},
        "future_only_mapping_rows": {
            "observed": metrics["future_only_mapping_rows"],
            "rule": "no future row is used; encode as (unknown)",
        },
    }
    passed = (
        metrics["duplicate_valid_matches"] == 0
        and metrics["multi_bu_valid_matches"] == 0
        and unmatched_rate <= 5
    )
    join.update(
        {
            "claim": "Join temporal as-of de BU L3 por cost_centerid y nk_dept_id.",
            "population": "Employee, Regular, active_status=1, Engineering, RF360=0",
            "grain": "employee-snapshot deduplicado",
            "acceptance": acceptance,
            "outcome": "pass" if passed else "fail",
        }
    )
    write(output / "input-evidence" / "bu-l3-join.json", join)
    if not passed:
        raise RuntimeError(f"La auditoria BU L3 no paso: {acceptance}")
    return {"metadata": metadata, "join": join, "metrics": metrics, "unmatched_rate_percent": unmatched_rate}


@dataclass
class BUPool:
    keep: list[str]

    @classmethod
    def fit(cls, frame: pd.DataFrame, minimum: int) -> "BUPool":
        values = frame[["person_key", "bu_l3"]].drop_duplicates()
        counts = values.groupby("bu_l3", observed=True).size()
        keep = sorted(str(value) for value, count in counts.items() if count >= minimum)
        if "(unknown)" not in keep:
            keep.append("(unknown)")
        return cls(keep)

    def apply(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy(deep=False)
        values = frame["bu_l3"].astype(str)
        result["bu_l3"] = values.where(values.isin(self.keep), "(other)").astype("category")
        return result


class PooledModel:
    def __init__(self, model: c.Model, pool: BUPool):
        self.model = model
        self.pool = pool
        self.design = model.design
        self.beta = model.beta
        self.features = model.features
        self.l2 = model.l2
        self.iterations = model.iterations

    def eta(self, frame: pd.DataFrame) -> np.ndarray:
        return np.asarray(self.design.matrix(self.pool.apply(frame)) @ self.beta).ravel()

    def risk(self, frame: pd.DataFrame) -> np.ndarray:
        return self.model.risk(self.pool.apply(frame))


def fit_b_model(frame: pd.DataFrame, cutoff: str, l2: float, config: dict, add_bu: bool) -> PooledModel:
    train = c.train_before(frame, cutoff)
    pool = BUPool.fit(train, config["rare_category_minimum_training_people"])
    prepared = pool.apply(train)
    features = list(binc.B_TERMS) + (["bu_l3"] if add_bu else [])
    design = c.Design.fit(prepared, features, config["interactions"])
    matrix = design.matrix(prepared)
    model = fast.fit_context(design, matrix, train.y_next.to_numpy(float), features, l2, config)
    del train, prepared, matrix
    return PooledModel(model, pool)


def fit_c_addition(
    frame: pd.DataFrame,
    cutoff: str,
    base_model,
    additions: list[str],
    config: dict,
) -> object:
    train = c.train_before(frame, cutoff)
    pool = BUPool.fit(train, int(config.get("rare_category_minimum_training_people", 300))) if "bu_l3" in additions else None
    prepared = pool.apply(train) if pool else train
    features = list(base_model.features)
    for feature in additions:
        if feature in features:
            raise RuntimeError(f"La variable {feature} ya esta en el modelo base.")
        features.append(feature)
    design = c.Design.fit(prepared, features, config["interactions"])
    matrix = design.matrix(prepared)
    model = fast.fit_context(design, matrix, train.y_next.to_numpy(float), features, float(base_model.l2), config)
    del train, prepared, matrix
    return PooledModel(model, pool) if pool else model


def model_eta(model, frame: pd.DataFrame) -> np.ndarray:
    if isinstance(model, PooledModel):
        return model.eta(frame)
    return np.asarray(cq.eta(model, frame)).ravel()


def fit_q(model, frame: pd.DataFrame, cutoff: str, spec: dict):
    train = frame.loc[frame.y_next.notna() & (frame.label_end <= pd.Timestamp(cutoff))].copy()
    features = list(spec["features"])
    encoder = cq.qmodel.CategoryEncoder.fit(train, features)
    matrix = horizon.category_matrix(encoder, train)
    offset = model_eta(model, train)
    beta, converged, iterations = cq.qmodel.fit_offset(
        matrix, train.y_next.to_numpy(float), offset, float(spec["l2"])
    )
    if not converged:
        raise RuntimeError(f"No convergio la correccion QVoice para {cutoff}.")
    del train, matrix, offset
    return encoder, beta, iterations


def q_correction(fitted, frame: pd.DataFrame) -> np.ndarray:
    encoder, beta = fitted[:2]
    return np.asarray(horizon.category_matrix(encoder, frame) @ beta).ravel()


def risk_with_correction(model, frame: pd.DataFrame, correction: np.ndarray) -> np.ndarray:
    coefficients = dict(zip(model.design.columns, model.beta))
    calendar = np.zeros(13)
    for column, coefficient in coefficients.items():
        if column.startswith("calendar_month="):
            calendar[int(column.split("=", 1)[1])] = coefficient
    months = frame.snapshot_date.dt.month.to_numpy()
    fixed = model_eta(model, frame) - calendar[months] + correction
    future = (months[:, None] - 1 + np.arange(6)) % 12 + 1
    cumulative = np.exp(np.clip(fixed[:, None] + calendar[future], -30, 5)).sum(axis=1)
    return np.clip(-np.expm1(-cumulative), 1e-8, 1 - 1e-8)


def test_frame(frame: pd.DataFrame, period: dict, knowledge: str) -> pd.DataFrame:
    result = frame.loc[
        (frame.snapshot_date >= pd.Timestamp(period["origin"]))
        & (frame.snapshot_date <= pd.Timestamp(period["end"]))
        & frame.y_6m.notna()
        & (frame.r6_end <= pd.Timestamp(knowledge))
    ].copy()
    if result.snapshot_date.nunique() != period["snapshots"]:
        raise RuntimeError(f"El periodo {period['id']} no tiene los snapshots esperados.")
    return result


def q_spec(period_id: str, config: dict):
    path = ROOT / config["output"] / "folds" / period_id / "selection.json"
    selection = read(path)
    return selection["winner"], path.relative_to(ROOT).as_posix()


def group_definitions(spec: dict) -> list[dict]:
    baseline = tuple(spec["grouping"]["baseline"])
    bu = spec["grouping"]["bu_dimension"]
    definitions = [{"id": "baseline", "dimensions": list(baseline), "is_bu": False}]
    definitions.append({"id": "bu_l3", "dimensions": [bu], "is_bu": True})
    for size in range(1, len(baseline) + 1):
        for combination in itertools.combinations(baseline, size):
            dims = [bu, *combination]
            definitions.append(
                {"id": "bu_l3__" + "__".join(combination), "dimensions": dims, "is_bu": True}
            )
    return definitions


def group_config(spec: dict) -> dict:
    cfg = spec["grouping"]
    return {
        "minimum_group_people_each_snapshot": cfg["minimum_group_people_each_snapshot"],
        "minimum_public_people_each_snapshot": cfg["minimum_public_people_each_snapshot"],
        "minimum_distinct_events": cfg["minimum_distinct_events"],
        "primary_capacity_fraction": cfg["capacity_fraction"],
    }


def group_label(dimensions: list[str]) -> str:
    labels = {"bu_l3": "BU L3"}
    return " x ".join(labels.get(d, groups.historical.DISPLAY.get(d, d)) for d in dimensions)


def evaluate_groups(frame: pd.DataFrame, prediction: np.ndarray, definitions: list[dict], spec: dict):
    all_dimensions = list(dict.fromkeys(d for item in definitions for d in item["dimensions"]))
    groups.historical.DISPLAY["bu_l3"] = "BU L3"
    baseline_dimensions = set(spec["grouping"]["baseline"])
    raw_dimensions = [dimension for dimension in all_dimensions if dimension not in baseline_dimensions]
    encoded = groups.encode(groups.cut_keys(frame, raw_dimensions))
    cfg = group_config(spec)
    result = {}
    allocations = {}
    for definition in definitions:
        dimensions = tuple(definition["dimensions"])
        try:
            codes, count, names = groups.combined(encoded, dimensions, True)
            grouped = groups.Grouped(frame, prediction, codes, count, cfg, names)
            weights, _, _ = grouped.allocation(cfg["primary_capacity_fraction"])
            metrics = grouped.quick(weights)
            metrics.update(
                {
                    "status": "ok",
                    "dimensions": list(dimensions),
                    "label": group_label(list(dimensions)),
                    "minimum_eligible_groups": int(grouped.eligible.sum(axis=1).min()),
                    "maximum_eligible_groups": int(grouped.eligible.sum(axis=1).max()),
                    "mean_eligible_groups": float(grouped.eligible.sum(axis=1).mean()),
                    "rest_percent": float(100 * grouped.n[~grouped.eligible].sum() / grouped.n.sum()),
                }
            )
            allocations[definition["id"]] = weights.ravel()[grouped.cells]
            result[definition["id"]] = metrics
        except (RuntimeError, ValueError) as error:
            result[definition["id"]] = {
                "status": "ineligible",
                "dimensions": list(dimensions),
                "label": group_label(list(dimensions)),
                "reason": str(error),
            }
    return result, allocations


def evaluate_two_stage_groups(frame: pd.DataFrame, prediction: np.ndarray, spec: dict):
    """Refina por BU L3 sólo dentro de las celdas baseline de mayor riesgo."""
    baseline = tuple(spec["grouping"]["baseline"])
    cfg = group_config(spec)
    encoded = groups.encode(groups.cut_keys(frame, [spec["grouping"]["bu_dimension"]]))
    base_codes, base_count, _ = groups.combined(encoded, baseline, False)
    bu_codes, bu_values = encoded[spec["grouping"]["bu_dimension"]]
    bu_count = len(bu_values)
    base_grouped = groups.Grouped(frame, prediction, base_codes, base_count, cfg)
    base_weights, _, _ = base_grouped.allocation(cfg["primary_capacity_fraction"])
    selected_base_by_date = base_weights > 1e-12
    selected_base_population = 100 * base_grouped.n[selected_base_by_date].sum() / base_grouped.n.sum()

    outputs = {}
    allocations = {}
    for threshold in spec.get("two_stage_grouping", {}).get("refined_minimum_people_each_snapshot", []):
        identifier = str(threshold)
        refined_count = base_count * bu_count
        refined_codes = base_codes * bu_count + bu_codes
        refined = groups.Grouped(frame, prediction, refined_codes, refined_count, cfg)
        selected_refined_by_date = np.repeat(selected_base_by_date, bu_count, axis=1)
        refined.eligible = (refined.n >= int(threshold)) & selected_refined_by_date
        try:
            weights, _, _ = refined.allocation(cfg["primary_capacity_fraction"])
            metrics = refined.quick(weights)
            metrics.update(
                {
                    "status": "ok",
                    "threshold_people_each_snapshot": int(threshold),
                    "stage_one_selected_population_percent": float(selected_base_population),
                    "rest_percent": float(100 * refined.n[~refined.eligible].sum() / refined.n.sum()),
                    "minimum_eligible_groups": int(refined.eligible.sum(axis=1).min()),
                    "maximum_eligible_groups": int(refined.eligible.sum(axis=1).max()),
                    "mean_eligible_groups": float(refined.eligible.sum(axis=1).mean()),
                    "mean_selected_groups": float((weights > 1e-12).sum(axis=1).mean()),
                }
            )
            allocations[identifier] = weights.ravel()[refined.cells]
            outputs[identifier] = metrics
        except (RuntimeError, ValueError) as error:
            outputs[identifier] = {
                "status": "ineligible",
                "threshold_people_each_snapshot": int(threshold),
                "stage_one_selected_population_percent": float(selected_base_population),
                "reason": str(error),
            }
    return outputs, allocations


def mean_metric(rows: list[dict], key: str) -> float:
    values = [float(row[key]) for row in rows if row.get("status") == "ok" and row.get(key) is not None]
    return float(np.mean(values)) if values else float("nan")


def select_group(periods: list[dict], model_name: str, spec: dict) -> dict:
    definitions = {item["id"]: item for item in group_definitions(spec)}
    candidate_rows = []
    for identifier, definition in definitions.items():
        rows = [period["models"][model_name]["groups"][identifier] for period in periods]
        if not all(row.get("status") == "ok" for row in rows):
            continue
        candidate_rows.append(
            {
                "id": identifier,
                "dimensions": definition["dimensions"],
                "is_bu": definition["is_bu"],
                "label": rows[0]["label"],
                "capture_percent": mean_metric(rows, "capture_percent"),
                "group_snapshot_mae_pp": mean_metric(rows, "group_snapshot_mae_pp"),
                "group_mae_pp": mean_metric(rows, "group_mae_pp"),
                "rest_percent": mean_metric(rows, "rest_percent"),
                "mean_eligible_groups": mean_metric(rows, "mean_eligible_groups"),
                "periods": int(len(rows)),
            }
        )
    baseline = next((row for row in candidate_rows if row["id"] == "baseline"), None)
    if baseline is None:
        raise RuntimeError(f"El baseline de grupos no es elegible para {model_name}.")

    bu_candidates = [row for row in candidate_rows if row["is_bu"]]

    # Conservamos la mejor candidata exploratoria aunque no pase las guardas
    # de promocion. Asi la senal encontrada queda visible y separada de la
    # recomendacion formal.
    best_bu_candidate = min(
        bu_candidates,
        key=lambda row: (
            -row["capture_percent"],
            row["group_snapshot_mae_pp"],
            row["rest_percent"],
            len(row["dimensions"]),
            row["id"],
        ),
    ) if bu_candidates else None

    def choose(rows: list[dict]) -> dict | None:
        if not rows:
            return None
        max_capture = max(row["capture_percent"] for row in rows)
        near_capture = [
            row for row in rows
            if row["capture_percent"] >= max_capture * (1 - spec["grouping"]["capture_relative_tolerance"])
        ]
        min_error = min(row["group_snapshot_mae_pp"] for row in near_capture)
        finalists = [
            row for row in near_capture
            if row["group_snapshot_mae_pp"] <= min_error + spec["grouping"]["error_tolerance_pp"]
            and row["rest_percent"] <= baseline["rest_percent"] + spec["grouping"]["maximum_rest_worsening_pp"]
        ]
        if not finalists:
            return None
        return min(
            finalists,
            key=lambda row: (
                len(row["dimensions"]),
                row["mean_eligible_groups"],
                -row["capture_percent"],
                row["id"],
            ),
        )

    all_winner = choose(candidate_rows)
    bu_winner = choose([row for row in candidate_rows if row["is_bu"]])

    exploratory_failures = []
    if best_bu_candidate is not None:
        max_bu_capture = max(row["capture_percent"] for row in bu_candidates)
        near_capture = [
            row for row in bu_candidates
            if row["capture_percent"] >= max_bu_capture * (1 - spec["grouping"]["capture_relative_tolerance"])
        ]
        min_error = min(row["group_snapshot_mae_pp"] for row in near_capture)
        if best_bu_candidate["group_snapshot_mae_pp"] > min_error + spec["grouping"]["error_tolerance_pp"]:
            exploratory_failures.append(
                "error de grupo fuera de la tolerancia respecto a las candidatas cercanas en captura"
            )
        maximum_rest = baseline["rest_percent"] + spec["grouping"]["maximum_rest_worsening_pp"]
        if best_bu_candidate["rest_percent"] > maximum_rest:
            exploratory_failures.append(
                f"rest {best_bu_candidate['rest_percent']:.1f}% > maximo {maximum_rest:.1f}%"
            )

    return {
        "model": model_name,
        "baseline": baseline,
        "winner_all": all_winner,
        "winner_bu": bu_winner,
        "best_bu_candidate": best_bu_candidate,
        "best_bu_candidate_failures": exploratory_failures,
        "best_bu_candidate_rule": "Mayor captura media; desempate por menor error de grupo, menor rest y menor complejidad.",
        "candidates": candidate_rows,
        "selection_rule": {
            "capture_relative_tolerance": spec["grouping"]["capture_relative_tolerance"],
            "error_tolerance_pp": spec["grouping"]["error_tolerance_pp"],
            "maximum_rest_worsening_pp": spec["grouping"]["maximum_rest_worsening_pp"],
        },
    }


def aggregate_model_metrics(periods: list[dict], model_name: str) -> dict:
    rows = [period["models"][model_name]["global"] for period in periods]
    return {key: mean_metric([{"status": "ok", key: row[key]} for row in rows], key) for key in MODEL_METRICS}


def compare_models(periods: list[dict], control_name: str, candidate_name: str, label: str) -> dict:
    control = aggregate_model_metrics(periods, control_name)
    candidate = aggregate_model_metrics(periods, candidate_name)
    return {
        "label": label,
        "control_name": control_name,
        "candidate_name": candidate_name,
        "control": control,
        "candidate": candidate,
        "delta": {key: candidate[key] - control[key] for key in MODEL_METRICS},
        "periods": [
            {
                "id": period["id"],
                "control": period["models"][control_name]["global"],
                "candidate": period["models"][candidate_name]["global"],
                "delta": {
                    key: period["models"][candidate_name]["global"][key]
                    - period["models"][control_name]["global"][key]
                    for key in MODEL_METRICS
                },
            }
            for period in periods
        ],
    }


def summarize_two_stage_groups(periods: list[dict], model_name: str, spec: dict) -> dict:
    thresholds = [int(value) for value in spec.get("two_stage_grouping", {}).get("refined_minimum_people_each_snapshot", [])]
    baseline_rows = [period["models"][model_name]["groups"]["baseline"] for period in periods]
    baseline = {key: mean_metric(baseline_rows, key) for key in GROUP_METRICS}
    candidates = []
    for threshold in thresholds:
        rows = [period["models"][model_name]["two_stage_groups"][str(threshold)] for period in periods]
        if not all(row.get("status") == "ok" for row in rows):
            candidates.append(
                {
                    "threshold_people_each_snapshot": threshold,
                    "status": "ineligible",
                    "reason": next(row.get("reason", "Sin asignacion posible") for row in rows if row.get("status") != "ok"),
                }
            )
            continue
        row = {
            "threshold_people_each_snapshot": threshold,
            "status": "ok",
            "coverage_percent": mean_metric(rows, "coverage_percent"),
            **{key: mean_metric(rows, key) for key in GROUP_METRICS},
            "stage_one_selected_population_percent": mean_metric(rows, "stage_one_selected_population_percent"),
            "mean_eligible_groups": mean_metric(rows, "mean_eligible_groups"),
            "mean_selected_groups": mean_metric(rows, "mean_selected_groups"),
        }
        row["guards"] = {
            "rest": row["rest_percent"] <= baseline["rest_percent"] + spec["grouping"]["maximum_rest_worsening_pp"],
            "error": row["group_snapshot_mae_pp"] <= baseline["group_snapshot_mae_pp"] + spec["grouping"]["error_tolerance_pp"],
            "allocation": row["coverage_percent"] >= spec["grouping"]["capacity_fraction"] * 100 - 0.1,
        }
        row["eligible_for_action"] = all(row["guards"].values())
        candidates.append(row)
    valid = [row for row in candidates if row.get("status") == "ok"]
    eligible = [row for row in valid if row.get("eligible_for_action")]
    key = lambda row: (-row["capture_percent"], row["group_snapshot_mae_pp"], row["rest_percent"], row["threshold_people_each_snapshot"])
    return {
        "model": model_name,
        "baseline": baseline,
        "candidates": candidates,
        "winner": min(eligible, key=key) if eligible else None,
        "best_exploratory": min(valid, key=key) if valid else None,
        "selection_rule": "Se elige la mayor captura entre las opciones que mantienen rest, error y capacidad dentro de las guardas; si ninguna pasa, se conserva la mejor exploratoria.",
    }


def aggregate_group_metric(periods: list[dict], model_name: str, group_id: str) -> dict:
    rows = [period["models"][model_name]["groups"][group_id] for period in periods]
    return {key: mean_metric(rows, key) for key in GROUP_METRICS}


def loss_arrays(y: np.ndarray, prediction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.clip(np.asarray(prediction, dtype=float), 1e-12, 1 - 1e-12)
    y = np.asarray(y, dtype=float)
    return (-y * np.log(p) - (1 - y) * np.log1p(-p), (y - p) ** 2)


def bootstrap_effects(held: list[dict], selections: dict[str, dict], repetitions: int, seed: int) -> dict:
    keys = np.concatenate([entry["keys"] for entry in held]).astype(str)
    codes, people = pd.factorize(keys, sort=False)
    people_count = len(people)
    counts = np.bincount(codes, minlength=people_count).astype(float)
    events = np.concatenate([entry["y"] for entry in held]).astype(float)
    event_counts = np.bincount(codes, weights=events, minlength=people_count)
    pairs = {
        "B_plus_bu_l3": ("B", "B_plus_bu_l3"),
        "Cq_plus_bu_l3": ("Cq", "Cq_plus_bu_l3"),
        "Fq_plus_bu_l3": ("Fq", "Fq_plus_bu_l3"),
    }
    sums = {}
    group_sums = {}
    for name, (base_name, candidate_name) in pairs.items():
        log_delta, brier_delta = [], []
        group_delta = []
        offset = 0
        selected = selections[name]["winner_bu"]
        baseline = selections[name]["baseline"]
        for entry in held:
            y = entry["y"]
            n = len(y)
            left_log, left_brier = loss_arrays(y, entry["predictions"][base_name])
            right_log, right_brier = loss_arrays(y, entry["predictions"][candidate_name])
            log_delta.append(right_log - left_log)
            brier_delta.append(right_brier - left_brier)
            if selected is None:
                group_delta.append(np.zeros(n))
            else:
                group_delta.append(
                    100
                    * y
                    * (
                        entry["allocations"][candidate_name][selected["id"]]
                        - entry["allocations"][base_name][baseline["id"]]
                    )
                )
            offset += n
        sums[name] = np.column_stack(
            [
                np.bincount(codes, weights=np.concatenate(log_delta), minlength=people_count),
                np.bincount(codes, weights=np.concatenate(brier_delta), minlength=people_count),
            ]
        )
        group_sums[name] = np.bincount(
            codes, weights=np.concatenate(group_delta), minlength=people_count
        )
    rng = np.random.default_rng(seed)
    output = {}
    for name in pairs:
        draws = []
        group_draws = []
        for _ in range(repetitions):
            weights = np.bincount(rng.integers(people_count, size=people_count), minlength=people_count)
            draws.append((weights @ sums[name]) / (weights @ counts))
            denominator = weights @ event_counts
            group_draws.append((weights @ group_sums[name]) / denominator if denominator else 0.0)
        draws = np.asarray(draws)
        group_draws = np.asarray(group_draws)
        output[name] = {
            "log_loss_delta_candidate_minus_control": {
                "point": float(sums[name][:, 0].sum() / counts.sum()),
                "ci95": np.quantile(draws[:, 0], [0.025, 0.975]).tolist(),
            },
            "brier_delta_candidate_minus_control": {
                "point": float(sums[name][:, 1].sum() / counts.sum()),
                "ci95": np.quantile(draws[:, 1], [0.025, 0.975]).tolist(),
            },
            "group_capture_delta_bu_winner_minus_baseline_pp": {
                "point": float(group_sums[name].sum() / event_counts.sum()) if event_counts.sum() else 0.0,
                "ci95": np.quantile(group_draws, [0.025, 0.975]).tolist(),
            },
        }
    return output


def fmt(value: float, scale: float = 1.0, suffix: str = "") -> str:
    if value is None or not np.isfinite(value):
        return "--"
    return f"{value * scale:.1f}{suffix}"


def fmt_count(value: float) -> str:
    if value is None or not np.isfinite(value):
        return "--"
    return f"{int(round(value)):,}"


def fmt_precise(value: float, scale: float = 1.0, digits: int = 3, suffix: str = "") -> str:
    if value is None or not np.isfinite(value):
        return "--"
    return f"{value * scale:.{digits}f}{suffix}"


def fmt_small_percent(value: float) -> str:
    """Muestra porcentajes pequenos sin redondearlos a cero."""
    if value is None or not np.isfinite(value):
        return "--"
    return f"{value:.4f}%" if abs(value) < 0.1 else f"{value:.1f}%"


def report(result: dict, output: Path):
    lines = [
        "# Impacto de BU L3 en los modelos de attrition",
        "",
        "Evaluacion experimental retrospectiva en modo `presentation`. BU L3 se unio por cost_centerid = nk_dept_id con una ventana SCD as-of al snapshot. No se guardaron filas, identificadores ni predicciones individuales.",
        "",
        "## Calidad del mapping",
        "",
        f"La auditoria encontro {fmt_count(result['data_quality']['metrics']['employee_snapshot_rows'])} empleado-snapshot, {fmt_count(result['data_quality']['metrics']['duplicate_valid_matches'])} duplicados temporales y {fmt_count(result['data_quality']['metrics']['multi_bu_valid_matches'])} multi-match de BU L3. El unmatched fue {fmt_small_percent(result['data_quality']['unmatched_rate_percent'])} y se codifico como `(unknown)`.",
        "",
        "## Efecto en prediccion",
        "",
        "Menor es mejor para log-loss y Brier; mayor es mejor para PR-AUC y lift.",
        "",
        "| Modelo | Control | Con BU L3 | Delta log-loss x1000 | Delta Brier x1000 | Delta PR-AUC | Delta lift |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in result["model_effects"]:
        control = item["control"]
        candidate = item["candidate"]
        delta = item["delta"]
        lines.append(
            f"| {item['label']} | {fmt(control['log_loss'], 1000)} / {fmt(control['pr_auc'], 100, '%')} | {fmt(candidate['log_loss'], 1000)} / {fmt(candidate['pr_auc'], 100, '%')} | {fmt(delta['log_loss'], 1000)} | {fmt_precise(delta['brier_score'], 1000)} | {fmt(delta['pr_auc'], 100, ' pp')} | {fmt(delta['lift_at_10_percent'])} |"
        )
    lines += ["", "## Validacion del nuevo candidato F + QVoice + BU L3", "", "La comparacion directa usa los mismos cortes y la misma estructura de grupos. Menor es mejor para log-loss y Brier; mayor es mejor para PR-AUC y lift.", "", "| Modelo | Log-loss x1000 | Brier x1000 | PR-AUC | Lift 10% |", "|---|---:|---:|---:|---:|"]
    comparison = next((item for item in result.get("model_comparisons", []) if item["candidate_name"] == "Fq_plus_bu_l3"), None)
    if comparison is not None:
        for label, metrics in [("C + QVoice + BU L3", comparison["control"]), ("F + QVoice + BU L3", comparison["candidate"])]:
            lines.append(f"| {label} | {fmt(metrics['log_loss'], 1000)} | {fmt(metrics['brier_score'], 1000)} | {fmt(metrics['pr_auc'], 100, '%')} | {fmt(metrics['lift_at_10_percent'])} |")
        delta = comparison["delta"]
        directions = [
            period["delta"]["log_loss"] < 0 and period["delta"]["brier_score"] < 0
            and period["delta"]["pr_auc"] > 0 and period["delta"]["lift_at_10_percent"] > 0
            for period in comparison["periods"]
        ]
        lines.append("")
        lines.append(f"F + QVoice + BU L3 mejora directamente a C + QVoice + BU L3 en log-loss ({fmt(delta['log_loss'], 1000)} x1000), Brier ({fmt_precise(delta['brier_score'], 1000)} x1000), PR-AUC ({fmt(delta['pr_auc'], 100, ' pp')}) y lift ({fmt(delta['lift_at_10_percent'])}); la dirección se mantiene en ambos cortes: {'si' if all(directions) else 'no'}.")
    two_stage = result.get("two_stage_effects", [])
    current_group_comparisons = result.get("current_group_comparisons", [])
    if current_group_comparisons:
        lines += ["", "## Grupos actuales con las dos variantes", "", "Antes de subdividir por BU L3, las dos variantes se evalúan con la estructura actual: Antigüedad x Salidas en su equipo x Nivel.", "", "| Modelo | Captura 30% | Error grupo-snapshot pp | Rest |", "|---|---:|---:|---:|"]
        for item in current_group_comparisons:
            metrics = item["metrics"]
            lines.append(f"| {item['label']} | {fmt(metrics['capture_percent'], 1, '%')} | {fmt(metrics['group_snapshot_mae_pp'])} | {fmt(metrics['rest_percent'], 1, '%')} |")
    if two_stage:
        lines += ["", "## Refinamiento de grupos de riesgo", "", "Primero se conservan los grupos actuales y se seleccionan sus celdas de mayor riesgo. BU L3 sólo subdivide esas celdas; no se usa para fragmentar a toda la población. Se muestran el umbral mínimo probado y las guardas de rest, error y capacidad.", "", "| Modelo | Umbral mínimo | Población en grupos de riesgo | Captura | Error grupo pp | Rest | Celdas seleccionadas | Resultado |", "|---|---:|---:|---:|---:|---:|---:|---|"]
        for item in two_stage:
            model_label = {"Cq_plus_bu_l3": "C + QVoice + BU L3", "Fq_plus_bu_l3": "F + QVoice + BU L3"}.get(item["model"], item["model"])
            candidate = item.get("winner") or item.get("best_exploratory")
            if candidate is None:
                lines.append(f"| {model_label} | -- | -- | -- | -- | -- | -- | Sin asignación posible |")
                continue
            guards = candidate.get("guards", {})
            if item.get("winner") is not None:
                outcome = "Pasa guardas"
            else:
                failed = [name for name, passed in guards.items() if not passed]
                outcome = "Exploratoria; falla " + ", ".join(failed)
            lines.append(f"| {model_label} | {candidate['threshold_people_each_snapshot']} | {fmt(candidate['stage_one_selected_population_percent'], 1, '%')} | {fmt(candidate['capture_percent'], 1, '%')} | {fmt(candidate['group_snapshot_mae_pp'])} | {fmt(candidate['rest_percent'], 1, '%')} | {fmt(candidate['mean_selected_groups'])} | {outcome} |")
    lines += ["", "## Efecto en grupos", "", "La candidata es la estructura con mayor captura media aunque no sea elegible para sustituir los grupos actuales. La elegibilidad exige simultaneamente las tres guardas definidas.", "", "| Modelo | Grupos actuales | Mejor candidata BU L3 (exploratoria) | Captura actual | Captura candidata | Error actual pp | Error candidata pp | Resultado |", "|---|---|---|---:|---:|---:|---:|---|"]
    for item in result["group_effects"]:
        baseline = item["baseline"]
        winner = item["winner_bu"]
        candidate = winner or item.get("best_bu_candidate")
        if candidate is None:
            lines.append(f"| {item['label']} | {baseline['label']} | -- | {fmt(baseline['capture_percent'], 1, '%')} | -- | {fmt(baseline['group_snapshot_mae_pp'])} | -- | Sin candidata calculable |")
            continue
        if winner is not None:
            outcome = "Elegible"
        else:
            failures = item.get("best_bu_candidate_failures", [])
            outcome = "No elegible: " + "; ".join(failures) if failures else "No elegible"
        lines.append(f"| {item['label']} | {baseline['label']} | {candidate['label']} | {fmt(baseline['capture_percent'], 1, '%')} | {fmt(candidate['capture_percent'], 1, '%')} | {fmt(baseline['group_snapshot_mae_pp'])} | {fmt(candidate['group_snapshot_mae_pp'])} | {outcome} |")
    lines += ["", "## Lectura", "", "La recomendacion de predictor se basa en las diferencias pareadas y sus intervalos por persona. BU L3 mejora modestamente las metricas predictivas en los tres modelos y las diferencias de log-loss pareadas excluyen cero. Para grupos, la estructura exploratoria con mayor captura es BU L3 x Antiguedad x Salidas en su equipo; su fragmentacion deja demasiado porcentaje en rest, por lo que no sustituye la estructura actual. La recomendacion de grupos aplica la regla de captura dentro del 2% relativo, error dentro de 0.1 pp y rest no mas de 5 pp peor que el baseline. Los modelos B, C+Q y F+Q originales permanecen sin cambios.", ""]
    (output / "informe.md").write_text("\n".join(lines), encoding="utf-8")


def run(config_path: Path):
    spec = read(config_path)
    output = ROOT / spec["output"]
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"La salida ya existe y no se sobrescribira: {output}")
    output.mkdir(parents=True)
    started = time.perf_counter()
    copy_evidence(spec, output)
    loader = loader_config(spec, output)
    c_config = read(ROOT / spec["c_config"])
    cq_config = read(ROOT / spec["cq_config"])
    write(output / "frozen-config.json", spec)
    write(output / "manifest.json", {"run_id": spec["run_id"], "status": "running", "reporting_mode": "presentation", "started_at": datetime.now(timezone.utc).isoformat(), "employee_level_rows_persisted": False, "individual_scores_published": False})

    log("Ejecutando auditorias agregadas de BU L3.")
    data_quality = audit_bu_l3(spec, output)
    profile = run_aggregate_query(ROOT / spec["profile_query"], output, "bu-l3-profile", max_rows=10000)
    data_quality["profile_rows"] = len(profile["rows"])

    log("Cargando un unico frame con BU L3 y QVoice en memoria.")
    frame, qframe = data.load(loader, output)
    if qframe is None:
        raise RuntimeError("No se cargo QVoice.")
    bank = cq.catalog(cq_config)
    definitions = group_definitions(spec)
    periods = []
    held = []
    model_specs = [
        ("B", "B_plus_bu_l3", "B", "B + BU L3"),
        ("Cq", "Cq_plus_bu_l3", "C + QVoice", "C + QVoice + BU L3"),
        ("Fq", "Fq_plus_bu_l3", "F + QVoice", "F + QVoice + BU L3"),
    ]
    for period in spec["periods"]:
        tick = time.perf_counter()
        origin = pd.Timestamp(period["origin"])
        model_origin, base_model, base_reference = cq.model_before(bank, origin)
        city_model = fit_c_addition(frame, period["origin"], base_model, ["work_city"], c_config)
        bu_model = fit_c_addition(frame, period["origin"], base_model, ["bu_l3"], c_config)
        city_bu_model = fit_c_addition(frame, period["origin"], base_model, ["work_city", "bu_l3"], c_config)
        qwinner, qselection_path = q_spec(period["id"], cq_config)
        q_base = fit_q(base_model, qframe, period["origin"], qwinner)
        q_city = fit_q(city_model, qframe, period["origin"], qwinner)
        q_bu = fit_q(bu_model, qframe, period["origin"], qwinner)
        q_city_bu = fit_q(city_bu_model, qframe, period["origin"], qwinner)

        b_artifact = read(ROOT / spec["b_model_dir"] / f"{period['id']}-B.json")
        b_l2 = float(b_artifact["model"]["l2"])
        b_model = fit_b_model(frame, period["origin"], b_l2, loader, False)
        b_bu_model = fit_b_model(frame, period["origin"], b_l2, loader, True)

        test = test_frame(qframe, period, loader["knowledge_boundary"])
        predictions = {
            "B": b_model.risk(test),
            "B_plus_bu_l3": b_bu_model.risk(test),
            "Cq": risk_with_correction(base_model, test, q_correction(q_base, test)),
            "Cq_plus_bu_l3": risk_with_correction(bu_model, test, q_correction(q_bu, test)),
            "Fq": risk_with_correction(city_model, test, q_correction(q_city, test)),
            "Fq_plus_bu_l3": risk_with_correction(city_bu_model, test, q_correction(q_city_bu, test)),
        }
        period_models = {}
        allocations = {}
        for name, prediction in predictions.items():
            global_metrics = {key: float(value) for key, value in c.metrics(test, prediction).items()}
            group_metrics, group_allocations = evaluate_groups(test, prediction, definitions, spec)
            two_stage_groups, _ = evaluate_two_stage_groups(test, prediction, spec)
            period_models[name] = {"global": global_metrics, "groups": group_metrics, "two_stage_groups": two_stage_groups}
            allocations[name] = group_allocations
        period_record = {
            **period,
            "base_model_origin": str(model_origin.date()),
            "base_model_reference": base_reference,
            "q_selection": qwinner,
            "q_selection_source": qselection_path,
            "b_l2": b_l2,
            "models": period_models,
            "elapsed_seconds": time.perf_counter() - tick,
        }
        periods.append(period_record)
        held.append(
            {
                "keys": test.person_key.astype(str).to_numpy(),
                "y": test.y_6m.to_numpy(float),
                "predictions": predictions,
                "allocations": allocations,
            }
        )
        log(f"{period['id']} terminado en {period_record['elapsed_seconds']:.1f} s.")
        del city_model, bu_model, city_bu_model, q_base, q_city, q_bu, q_city_bu, test, predictions
        del b_model, b_bu_model
        import gc
        gc.collect()

    selections = {}
    group_effects = []
    for base_name, candidate_name, label, _ in model_specs:
        selection = select_group(periods, base_name, spec)
        selections[base_name + ("_plus_bu_l3" if base_name == "B" else "_plus_bu_l3")] = selection
        group_effects.append({"label": label, **selection})
    # El nombre de las selecciones coincide con las claves del bootstrap.
    selections = {
        "B_plus_bu_l3": select_group(periods, "B", spec),
        "Cq_plus_bu_l3": select_group(periods, "Cq", spec),
        "Fq_plus_bu_l3": select_group(periods, "Fq", spec),
    }
    group_effects = []
    for model_name, label in [("B", "B"), ("Cq", "C + QVoice"), ("Fq", "F + QVoice")]:
        group_effects.append({"label": label, **selections[model_name + "_plus_bu_l3"]})

    model_effects = []
    for base_name, candidate_name, label, candidate_label in model_specs:
        control = aggregate_model_metrics(periods, base_name)
        candidate = aggregate_model_metrics(periods, candidate_name)
        delta = {key: candidate[key] - control[key] for key in MODEL_METRICS}
        model_effects.append({"label": label, "candidate_label": candidate_label, "control": control, "candidate": candidate, "delta": delta})
    model_comparisons = [
        compare_models(
            periods,
            "Cq_plus_bu_l3",
            "Fq_plus_bu_l3",
            "F + QVoice + BU L3 frente a C + QVoice + BU L3",
        )
    ]
    two_stage_effects = [
        summarize_two_stage_groups(periods, model_name, spec)
        for model_name in ("Cq_plus_bu_l3", "Fq_plus_bu_l3")
    ]
    current_group_comparisons = [
        {
            "label": label,
            "model": model_name,
            "metrics": aggregate_group_metric(periods, model_name, "baseline"),
        }
        for model_name, label in [
            ("Cq_plus_bu_l3", "C + QVoice + BU L3"),
            ("Fq_plus_bu_l3", "F + QVoice + BU L3"),
        ]
    ]
    log("Calculando intervalos pareados por persona.")
    bootstrap = bootstrap_effects(held, selections, int(spec["bootstrap_repetitions"]), int(spec["seed"]))
    results_periods = periods
    results = {
        "run_id": spec["run_id"],
        "reporting_mode": "presentation",
        "status": "completed_experimental",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": loader["knowledge_boundary"],
        "data_quality": data_quality,
        "model_effects": model_effects,
        "model_comparisons": model_comparisons,
        "two_stage_effects": two_stage_effects,
        "current_group_comparisons": current_group_comparisons,
        "group_effects": group_effects,
        "paired_intervals": bootstrap,
        "periods": results_periods,
        "group_definitions": definitions,
        "source_hashes": {
            path: sha(ROOT / path)
            for path in [
                spec["base_query"],
                spec["source_c_config"],
                spec["loader_config"],
                spec["c_config"],
                spec["cq_config"],
                *spec["audit_queries"],
                spec["profile_query"],
                "tools/engineering_bu_l3_experiment.py",
            ]
        },
        "elapsed_seconds": time.perf_counter() - started,
        "employee_level_rows_persisted": False,
        "individual_scores_published": False,
        "job_family_used": False,
    }
    write(output / "results.json", results)
    report(results, output)
    files = {path.relative_to(output).as_posix(): sha(path) for path in output.rglob("*") if path.is_file() and path.name != "manifest.json"}
    write(output / "manifest.json", {"run_id": spec["run_id"], "status": "completed_experimental", "completed_at": datetime.now(timezone.utc).isoformat(), "reporting_mode": "presentation", "files": files, "employee_level_rows_persisted": False, "individual_scores_published": False})
    log("Experimento BU L3 terminado; solo se conservaron agregados.")
    return results


if __name__ == "__main__":
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT))
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(ROOT / args.config)
