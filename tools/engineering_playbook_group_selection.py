"""Selección analítica de los grupos del slide 6 con el modelo B (2026-10-03).

Hay un solo modelo de riesgo (B: vigente con cortes del playbook + tiempo desde
la última promoción + recontratación). Los grupos sólo resumen su resultado;
la agrupación óptima es la que mejor conserva, fuera de muestra, la capacidad
del modelo para concentrar las salidas observadas. Reglas declaradas antes de
correr:

- Candidatas: todas las combinaciones de 2 y 3 variables entre antigüedad
  (6 tramos del playbook), salidas en su equipo (con/sin), reportes (con/sin),
  nivel (entrada/medio/alto), cambios de manager (0 / 1+), tiempo desde la
  última promoción (reciente / 2+ años / sin promoción registrada) y
  recontratación (sí/no); además el árbol de riesgo con profundidad 3 y 4,
  ajustado en la última foto de entrenamiento de cada periodo.
- Grupos con < 300 personas por foto van a "resto", que nunca entra al top.
- Métrica: en cada uno de los 4 periodos de prueba, los grupos se ordenan por
  su riesgo estimado medio (modelo entrenado antes del periodo) y se mide la
  curva de concentración de las salidas observadas. Eficiencia = Gini de la
  agrupación / Gini del ranking individual del modelo.
- Selección: entre las combinaciones fijas a <= 2% relativo de la mejor
  eficiencia media, gana la de menos variables; después, la de menos grupos;
  después, la más estable. El árbol sólo gana si supera a la mejor
  combinación fija por más de 2%.

Sólo se escriben agregados (grupos >= 300 personas; observado con >= 30
salidas).
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
import engineering_feature_block_selection as fs  # noqa: E402
import engineering_hazard_adjustment as adj  # noqa: E402
import engineering_playbook_tenure_confirmation as cf  # noqa: E402  (penalización fija y ajustes no finitos)

pm = cf.pm
ROOT = hz.ROOT
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "engineering" / "20261003" / "playbook-group-selection-v1"
CONFIRMATION = ROOT / "output" / "analysis" / "engineering" / "20261003" / "playbook-tenure-confirmation-v1" / "confirmation-results.json"
TENURE = "tenure_playbook_band"
MIN_GROUP_PEOPLE = 300
TOP = 5
CAPTURE_SHARE = 0.25
TREE_DEPTHS = [3, 4]
REST = "resto"

VARIABLES = ["antiguedad", "salidas_equipo", "reportes", "nivel", "cambios_manager", "promocion", "recontratacion"]
DISPLAY = {
    "antiguedad": "Antigüedad",
    "salidas_equipo": "Salidas en su equipo",
    "reportes": "Reportes",
    "nivel": "Nivel",
    "cambios_manager": "Cambios de manager",
    "promocion": "Última promoción",
    "recontratacion": "Recontratación",
}
TENURE_LABELS = {
    "<1 year": "<1 año",
    "1-2 years": "1-2 años",
    "2-3 years": "2-3 años",
    "3-5 years": "3-5 años",
    "5-10 years": "5-10 años",
    "10+ years": "10+ años",
}
LEVEL_GROUPS = {"1": "alto", "2": "alto", "3": "alto", "5": "medio", "6": "medio", "7": "entrada", "8": "entrada"}
TREE_SOURCE = ["level_grouped", TENURE, "manager_changes_12m", "team_exits_12m", "direct_reports_band", "time_since_promotion_band", "rehire"]


# ---------------------------------------------------------------- cortes


def coarse_keys(frame: pd.DataFrame) -> pd.DataFrame:
    """Cortes gruesos declarados para cada variable candidata."""
    exits = frame["team_exits_12m"].astype(str)
    reports = frame["direct_reports_band"].astype(str)
    changes = frame["manager_changes_12m"].astype(str)
    promo = frame["time_since_promotion_band"].astype(str)
    rehire = frame["rehire"].astype(str)
    level = frame["level_grouped"].astype(str).str.split(" - ").str[0]
    return pd.DataFrame(
        {
            "antiguedad": frame[TENURE].astype(str).map(TENURE_LABELS).fillna("sin dato"),
            "salidas_equipo": np.select([exits == "0", exits == "(unknown)"], ["sin salidas", "sin dato"], "con salidas"),
            "reportes": np.select([reports == "0", reports == "(unknown)"], ["sin reportes", "sin dato"], "con reportes"),
            "nivel": level.map(LEVEL_GROUPS).fillna("otro"),
            "cambios_manager": np.where(changes == "0", "sin cambios de manager", "con cambios de manager"),
            "promocion": np.select(
                [promo.isin(["promo <1 year", "promo 1-2 years"]), promo.isin(["promo 2-3 years", "promo 3+ years"]), promo == "(unknown)"],
                ["promoción reciente", "promoción hace 2+ años", "sin dato"],
                "sin promoción registrada",
            ),
            "recontratacion": np.select([rehire == "yes", rehire == "no"], ["recontratado", "no recontratado"], "sin dato"),
        },
        index=frame.index,
    )


def combination_labels(keys: pd.DataFrame, variables: tuple[str, ...]) -> pd.Series:
    return keys[list(variables)].agg(" · ".join, axis=1)


# ---------------------------------------------------------------- métricas


def concentration_curve(exposure: np.ndarray, events: np.ndarray, score: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Curva de concentración (población acumulada, salidas acumuladas) ordenando por riesgo.

    Los empates de ``score`` se tratan como un bloque (segmento lineal), igual
    que un grupo: dentro de un grupo no hay orden.
    """
    table = pd.DataFrame({"score": score, "exposure": exposure, "events": events}).groupby("score")[["exposure", "events"]].sum()
    table = table.sort_index(ascending=False)
    x = np.concatenate([[0.0], np.cumsum(table["exposure"].to_numpy(dtype=float))]) / float(table["exposure"].sum())
    y = np.concatenate([[0.0], np.cumsum(table["events"].to_numpy(dtype=float))]) / float(table["events"].sum())
    return x, y


def gini(x: np.ndarray, y: np.ndarray) -> float:
    return float(2.0 * np.sum((x[1:] - x[:-1]) * (y[1:] + y[:-1]) / 2.0) - 1.0)


def share_at(x: np.ndarray, y: np.ndarray, q: float) -> float:
    return float(np.interp(q, x, y))


def grouped(labels: pd.Series, exposure: np.ndarray, events: np.ndarray, expected: np.ndarray, snapshots: int, min_people: int) -> pd.DataFrame:
    """Suma por grupo; grupos con menos de ``min_people`` personas por foto van a ``REST``."""
    table = pd.DataFrame({"group": labels.to_numpy(), "exposure": exposure, "events": events, "expected": expected})
    sums = table.groupby("group")[["exposure", "events", "expected"]].sum()
    small = sums.index[sums["exposure"] / snapshots < min_people]
    table.loc[table["group"].isin(small), "group"] = REST
    out = table.groupby("group")[["exposure", "events", "expected"]].sum()
    out["risk"] = out["expected"] / out["exposure"]
    return out


def evaluate_fold(labels: pd.Series, exposure: np.ndarray, events: np.ndarray, predictions: np.ndarray, snapshots: int) -> dict:
    expected = predictions * exposure
    groups = grouped(labels, exposure, events, expected, snapshots, MIN_GROUP_PEOPLE)
    gx, gy = concentration_curve(groups["exposure"].to_numpy(), groups["events"].to_numpy(), groups["risk"].to_numpy())
    ix, iy = concentration_curve(exposure, events, predictions)
    individual = gini(ix, iy)
    ranked = groups.drop(index=REST, errors="ignore").sort_values("risk", ascending=False)
    return {
        "gini_groups": round(gini(gx, gy), 5),
        "gini_individual": round(individual, 5),
        "efficiency": round(gini(gx, gy) / individual, 5),
        "capture_groups": round(share_at(gx, gy, CAPTURE_SHARE), 5),
        "capture_individual": round(share_at(ix, iy, CAPTURE_SHARE), 5),
        "groups": int(len(ranked)),
        "rest_people_share": round(float(groups.loc[REST, "exposure"] / groups["exposure"].sum()) if REST in groups.index else 0.0, 5),
        "_risk": ranked["risk"],
    }


def stability(folds: list[dict]) -> dict:
    """Correlación de rangos entre periodos consecutivos y coincidencia del top con el último periodo."""
    correlations = []
    for a, b in zip(folds[:-1], folds[1:]):
        common = a["_risk"].index.intersection(b["_risk"].index)
        if len(common) >= 3:
            correlations.append(float(a["_risk"][common].rank().corr(b["_risk"][common].rank())))
    last_top = set(folds[-1]["_risk"].index[:TOP])
    overlap = [len(set(f["_risk"].index[:TOP]) & last_top) / TOP for f in folds[:-1]]
    return {
        "rank_correlation": round(float(np.mean(correlations)), 4) if correlations else None,
        "top_overlap_with_last_fold": round(float(np.mean(overlap)), 4),
    }


def select(candidates: list[dict], tolerance: float) -> dict:
    """Regla declarada: parsimonia entre fijas a <= tolerancia de la mejor; el árbol sólo gana por más de la tolerancia."""
    fixed = [c for c in candidates if c["kind"] == "fixed"]
    best_fixed = max(c["mean_efficiency"] for c in fixed)
    trees = [c for c in candidates if c["kind"] == "tree"]
    best_tree = max(trees, key=lambda c: c["mean_efficiency"]) if trees else None
    if best_tree is not None and best_tree["mean_efficiency"] > (1.0 + tolerance) * best_fixed:
        return {"winner": best_tree["name"], "reason": "árbol más de la tolerancia por encima de la mejor combinación fija", "best_fixed_efficiency": best_fixed}
    eligible = [c for c in fixed if c["mean_efficiency"] >= (1.0 - tolerance) * best_fixed]
    eligible.sort(key=lambda c: (len(c["variables"]), c["mean_groups"], -(c["stability"]["rank_correlation"] or -1.0)))
    return {
        "winner": eligible[0]["name"],
        "reason": "menos variables, después menos grupos y después más estabilidad entre las combinaciones a <= tolerancia de la mejor",
        "best_fixed_efficiency": best_fixed,
        "within_tolerance": [c["name"] for c in eligible],
    }


# ---------------------------------------------------------------- árbol


class TreeGrouping:
    """Árbol de riesgo ajustado sobre predicciones de una foto; asigna hojas con su regla."""

    def __init__(self, frame: pd.DataFrame, risk: np.ndarray, depth: int):
        from sklearn.tree import DecisionTreeRegressor

        self.x_columns = None
        x = self._design(frame)
        weights = frame["exposure_count"].to_numpy(dtype=float)
        self.tree = DecisionTreeRegressor(max_depth=depth, min_weight_fraction_leaf=MIN_GROUP_PEOPLE / weights.sum(), random_state=0)
        self.tree.fit(x, risk, sample_weight=weights)
        self.rules = {leaf: " y ".join(rule) for leaf, rule in fs.describe_path(self.tree.tree_, list(x.columns), 0, [])}

    def _design(self, frame: pd.DataFrame) -> pd.DataFrame:
        x = pd.get_dummies(frame[TREE_SOURCE].astype(str), prefix_sep="=").astype(float)
        if self.x_columns is None:
            self.x_columns = list(x.columns)
            return x
        return x.reindex(columns=self.x_columns, fill_value=0.0)

    def labels(self, frame: pd.DataFrame) -> pd.Series:
        leaves = self.tree.apply(self._design(frame))
        return pd.Series([self.rules[leaf] for leaf in leaves], index=frame.index)


def snapshot_risk(model, monthly: pd.DataFrame, date: pd.Timestamp) -> tuple[pd.DataFrame, np.ndarray]:
    current = monthly.loc[monthly["snapshot_date"] == date].reset_index(drop=True)
    return current, hz.six_month_predictions(model, current)


# ---------------------------------------------------------------- evaluación


def evaluate_candidates(spec: dict, windows: list[dict]) -> list[dict]:
    monthly, _ = spec["frames"]
    folds = spec["folds"]
    tests = [(f["test"], coarse_keys(f["test"]), f["test"]["snapshot_date"].nunique()) for f in folds]
    candidates = []
    for size in (2, 3):
        for variables in itertools.combinations(VARIABLES, size):
            results = []
            for fold, (test, keys, snapshots) in zip(folds, tests):
                labels = combination_labels(keys, variables)
                results.append(evaluate_fold(labels, test["exposure_count"].to_numpy(dtype=float), test["event_count"].to_numpy(dtype=float), fold["predictions"], snapshots))
            candidates.append(summarize(" × ".join(DISPLAY[v] for v in variables), "fixed", list(variables), results))
    for depth in TREE_DEPTHS:
        results = []
        for fold, window, (test, _, snapshots) in zip(folds, windows, tests):
            train_date = monthly.loc[monthly["snapshot_date"] < window["start"], "snapshot_date"].max()
            current, risk = snapshot_risk(fold["model"], monthly, train_date)
            grouping = TreeGrouping(current, risk, depth)
            results.append(evaluate_fold(grouping.labels(test), test["exposure_count"].to_numpy(dtype=float), test["event_count"].to_numpy(dtype=float), fold["predictions"], snapshots))
        candidates.append(summarize(f"Árbol de riesgo, profundidad {depth}", "tree", [f"profundidad {depth}"], results))
    candidates.sort(key=lambda c: -c["mean_efficiency"])
    return candidates


def summarize(name: str, kind: str, variables: list[str], results: list[dict]) -> dict:
    return {
        "name": name,
        "kind": kind,
        "variables": variables,
        "mean_efficiency": round(float(np.mean([r["efficiency"] for r in results])), 5),
        "mean_capture_groups": round(float(np.mean([r["capture_groups"] for r in results])), 5),
        "mean_capture_individual": round(float(np.mean([r["capture_individual"] for r in results])), 5),
        "mean_groups": round(float(np.mean([r["groups"] for r in results])), 2),
        "mean_rest_people_share": round(float(np.mean([r["rest_people_share"] for r in results])), 5),
        "stability": stability(results),
        "by_fold": [{k: v for k, v in r.items() if not k.startswith("_")} for r in results],
    }


# ---------------------------------------------------------------- resultado para el slide


def final_groups(spec: dict, winner: dict) -> dict:
    """Top de la agrupación ganadora en la última foto con B ajustado en toda la historia."""
    monthly, _ = spec["frames"]
    l2 = spec["folds"][-1]["metrics"]["l2"]
    model = adj.fit_converged(monthly, spec["features"], l2, pm.TREND, pm.RECALIBRATION_MONTHS)
    latest = monthly["snapshot_date"].max()
    current, risk = snapshot_risk(model, monthly, latest)
    if winner["kind"] == "tree":
        grouping = TreeGrouping(current, risk, int(winner["variables"][0].split()[-1]))
        label_of = grouping.labels
    else:
        label_of = lambda frame: combination_labels(coarse_keys(frame), tuple(winner["variables"]))  # noqa: E731

    people = current["exposure_count"].to_numpy(dtype=float)
    now = grouped(label_of(current), people, np.zeros_like(people), risk * people, 1, MIN_GROUP_PEOPLE)
    total_people, total_expected = float(now["exposure"].sum()), float(now["expected"].sum())
    mean = total_expected / total_people

    fold = spec["folds"][-1]
    test = fold["test"]
    snapshots = test["snapshot_date"].nunique()
    exposure, events = test["exposure_count"].to_numpy(dtype=float), test["event_count"].to_numpy(dtype=float)
    past = grouped(label_of(test), exposure, events, fold["predictions"] * exposure, snapshots, 1)
    total_events = float(past["events"].sum())

    ranked = now.drop(index=REST, errors="ignore").sort_values("risk", ascending=False)
    rows = []
    for label, r in ranked.iterrows():
        item = {
            "group": label,
            "people": int(round(r["exposure"])),
            "people_share_percent": round(100.0 * r["exposure"] / total_people, 2),
            "predicted_6m_percent": round(100.0 * r["risk"], 3),
            "lift_vs_mean": round(float(r["risk"] / mean), 3),
            "expected_exits_share_percent": round(100.0 * r["expected"] / total_expected, 2),
        }
        if winner["kind"] == "fixed":
            item["parts"] = dict(zip(winner["variables"], label.split(" · ")))
        if label in past.index:
            p = past.loc[label]
            item["last_fold_predicted_percent"] = round(100.0 * p["expected"] / p["exposure"], 3)
            if p["events"] >= fs.MIN_EVENTS:
                item["last_fold_events"] = int(p["events"])
                item["last_fold_observed_percent"] = round(100.0 * p["events"] / p["exposure"], 3)
                item["last_fold_observed_exits_share_percent"] = round(100.0 * p["events"] / total_events, 2)
        rows.append(item)
    top = rows[:TOP]
    top_people = sum(x["people_share_percent"] for x in top) / 100.0

    ix, iy = concentration_curve(people, risk * people, risk)
    ox, oy = concentration_curve(exposure, events, fold["predictions"])
    return {
        "snapshot": str(latest.date()),
        "people": int(round(total_people)),
        "mean_predicted_6m_percent": round(100.0 * mean, 3),
        "groups_eligible": len(rows),
        "people_in_rest": int(round(float(now.loc[REST, "exposure"]))) if REST in now.index else 0,
        "top": top,
        "top_people_share_percent": round(100.0 * top_people, 2),
        "top_expected_exits_share_percent": round(sum(x["expected_exits_share_percent"] for x in top), 2),
        "individual_expected_exits_share_at_same_people_percent": round(100.0 * share_at(ix, iy, top_people), 2),
        "top_last_fold_observed_exits_share_percent": round(sum(x.get("last_fold_observed_exits_share_percent", 0.0) for x in top), 2),
        "individual_last_fold_observed_exits_share_at_same_people_percent": round(100.0 * share_at(ox, oy, top_people), 2),
        "all_groups": rows,
    }


# ---------------------------------------------------------------- reporte


def build_report(result: dict) -> str:
    s = result["selection"]
    candidates = result["candidates"]
    g = result["final"]
    lines = [
        "# Selección analítica de los grupos del slide 6 — modelo B — Engineering",
        "",
        f"Creado: {result['created_at_utc']}. Modelo: {result['model']['name']}.",
        "",
        "Reglas declaradas antes de correr:",
        "",
        *[f"- {line}" for line in result["design"]["rules"]],
        "",
        "## Decisión",
        "",
        f"- Mejor eficiencia media de una combinación fija: {s['best_fixed_efficiency']:.3f}.",
        f"- Dentro de la tolerancia: {', '.join(s.get('within_tolerance', [])) or '—'}.",
        f"- **Ganadora: {s['winner']}** ({s['reason']}).",
        "",
        "## Candidatas (orden por eficiencia media en los 4 periodos)",
        "",
        "| Agrupación | Eficiencia | Eficiencia por periodo | Captura@25% grupos | Captura@25% individual | Grupos | % resto | Correlación de rangos | Top 5 = último periodo |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for c in candidates:
        corr = c["stability"]["rank_correlation"]
        by_fold = ", ".join(f"{f['efficiency']:.3f}" for f in c["by_fold"])
        lines.append(
            f"| {c['name']} | {c['mean_efficiency']:.3f} | {by_fold} | "
            f"{100 * c['mean_capture_groups']:.1f}% | {100 * c['mean_capture_individual']:.1f}% | {c['mean_groups']:.1f} | "
            f"{100 * c['mean_rest_people_share']:.1f}% | {'—' if corr is None else f'{corr:.2f}'} | {100 * c['stability']['top_overlap_with_last_fold']:.0f}% |"
        )
    lines += [
        "",
        f"## Top {TOP} de la ganadora, foto {g['snapshot']}",
        "",
        f"{g['people']:,} personas; riesgo medio estimado a seis meses {g['mean_predicted_6m_percent']:.2f}%. "
        f"{g['groups_eligible']} grupos elegibles; {g['people_in_rest']:,} personas en resto.",
        "",
        "| Grupo | Personas | % población | Riesgo 6m % | × promedio | % salidas esperadas | Último periodo: estimado % | observado % |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def row(x: dict) -> str:
        observed = x.get("last_fold_observed_percent")
        return (
            f"| {x['group']} | {x['people']} | {x['people_share_percent']:.1f} | {x['predicted_6m_percent']:.2f} | {x['lift_vs_mean']:.2f} | "
            f"{x['expected_exits_share_percent']:.1f} | {x.get('last_fold_predicted_percent', float('nan')):.2f} | {'—' if observed is None else f'{observed:.2f}'} |"
        )

    lines += [row(x) for x in g["top"]]
    lines += [
        "",
        f"El top {TOP} reúne el {g['top_people_share_percent']:.1f}% de las personas y el {g['top_expected_exits_share_percent']:.1f}% de las salidas esperadas; "
        f"el mismo % de personas con mayor riesgo individual reúne el {g['individual_expected_exits_share_at_same_people_percent']:.1f}%.",
        f"Último periodo observado: top {TOP} {g['top_last_fold_observed_exits_share_percent']:.1f}% de las salidas; ranking individual "
        f"{g['individual_last_fold_observed_exits_share_at_same_people_percent']:.1f}%.",
        "",
        "## Todos los grupos elegibles de la ganadora (referencia)",
        "",
        "| Grupo | Personas | % población | Riesgo 6m % | × promedio | % salidas esperadas | Último periodo: estimado % | observado % |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    lines += [row(x) for x in g["all_groups"]]
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
    confirmation = json.loads(CONFIRMATION.read_text(encoding="utf-8"))
    if confirmation["final_key"] != "b":
        raise RuntimeError("El modelo final de la confirmación no es B.")

    calendar = [d for d in hz.fetch_calendar() if d >= fs.MIN_SNAPSHOT]
    monthly, direct, totals = pm.load_person_months(calendar)
    windows = fs.fold_windows(direct)
    references = pm.modal_references(direct)
    runner = pm.Runner(monthly, direct, windows, references)
    b = runner.run(cf.features_for(TENURE, cf.CAREER), TENURE, tag="B")
    if abs(b["summary"]["lift_at_10_percent"] / confirmation["specs"]["b"]["summary"]["lift_at_10_percent"] - 1.0) >= 0.01:
        raise RuntimeError("B no se reproduce frente a la confirmación.")

    candidates = evaluate_candidates(b, windows)
    fs.log(f"{len(candidates)} agrupaciones evaluadas; mejor: {candidates[0]['name']} ({candidates[0]['mean_efficiency']:.3f})")
    selection = select(candidates, fs.PARSIMONY_TOLERANCE)
    winner = next(c for c in candidates if c["name"] == selection["winner"])
    level_values = sorted(direct["level_grouped"].astype(str).unique())

    result = {
        "artifact": "engineering-playbook-group-selection",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": hz.KNOWLEDGE_BOUNDARY.strftime("%Y-%m-%d"),
        "deliverable_classification": "presentation",
        "authorization": {"path": str(fs.AUTHORIZATION.relative_to(ROOT)), "id": authorization["authorization_id"]},
        "model": {"name": confirmation["final_name"], "features": b["features"], "summary": b["summary"]},
        "design": {
            "rules": [
                "candidatas: combinaciones de 2 y 3 variables con cortes gruesos fijos, y árbol de riesgo de profundidad 3 y 4 ajustado en la última foto de entrenamiento de cada periodo",
                f"grupos con < {MIN_GROUP_PEOPLE} personas por foto van a resto (nunca entra al top)",
                "eficiencia = Gini de la curva de concentración de salidas observadas ordenando grupos por riesgo estimado / Gini del ranking individual del modelo, en cada uno de los 4 periodos de prueba",
                f"selección: entre combinaciones fijas a <= {100 * fs.PARSIMONY_TOLERANCE:.0f}% de la mejor eficiencia media, menos variables, después menos grupos, después más estabilidad",
                f"el árbol sólo gana si supera a la mejor combinación fija por más de {100 * fs.PARSIMONY_TOLERANCE:.0f}%",
                f"captura@{100 * CAPTURE_SHARE:.0f}% y estabilidad son informativas",
            ],
            "variables": VARIABLES,
            "level_groups": LEVEL_GROUPS,
            "level_values_seen": level_values,
            "tree_depths": TREE_DEPTHS,
            "min_group_people": MIN_GROUP_PEOPLE,
            "min_published_events": fs.MIN_EVENTS,
            "top": TOP,
        },
        "candidates": candidates,
        "selection": selection,
        "winner": {k: v for k, v in winner.items() if k != "by_fold"},
        "final": final_groups(b, winner),
        "privacy": {
            "employee_level_rows_persisted": False,
            "employee_ids_selected": False,
            "aggregate_training_frame_persisted": False,
            "individual_scores_published": False,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "group-selection-results.json"
    report_path = output_dir / "group-selection-report.md"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    manifest = {
        "artifact": result["artifact"],
        "created_at_utc": result["created_at_utc"],
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "authorization": result["authorization"],
        "queries": {"calendar": str(hz.CALENDAR_QUERY.relative_to(ROOT)), "person_month_frame": str(pm.FRAME_QUERY.relative_to(ROOT))},
        "query_sha256": {"calendar": hz.sha256_file(hz.CALENDAR_QUERY), "person_month_frame": hz.sha256_file(pm.FRAME_QUERY)},
        "confirmation_source": str(CONFIRMATION.relative_to(ROOT)),
        "confirmation_source_sha256": hz.sha256_file(CONFIRMATION),
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": hz.sha256_file(result_path),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": hz.sha256_file(report_path),
        "employee_level_rows_persisted": False,
        "aggregate_training_frame_persisted": False,
    }
    (output_dir / "group-selection-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(build_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
