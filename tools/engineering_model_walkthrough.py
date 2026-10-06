"""Agregados para explicar cómo calcula el riesgo el modelo B (2026-10-03).

Alimenta la diapositiva «cómo calcula el riesgo» del deck v9 (idea de la
revisora: personas × meses, grupos × meses y riesgo acumulado a seis meses con
R6 = 1 - (1 - h1)...(1 - h6)). Reglas declaradas antes de correr:

- Modelo: B de la 4.ª prueba (entrenado sólo con la historia anterior a
  ago-2025), reproducido con las mismas funciones de la confirmación.
- Foto de ejemplo: la de enero de 2026, que cae dentro del periodo de prueba;
  el riesgo de cada mes (feb-jul) cambia sólo por la temporada, las demás
  señales se congelan en la foto, como en ``hz.six_month_predictions``.
- Empleados de ejemplo: 6 personas ficticias con nombre, 2 por cada grupo
  fijo (alto, medio, bajo) de la agrupación elegida. Sus señales son
  inventadas pero coherentes con su grupo; su riesgo sale de aplicar el
  modelo real a esas señales. No corresponden a ninguna persona real.
- Grupos: promedio de h por mes ponderado por personas, R6 con la fórmula
  sobre ese promedio, promedio de R6 por persona y lo real feb-jul (sólo con
  >= 30 salidas).
- Pasos del plano (foto de jul-2026, modelo con toda la historia, como el
  slide de grupos): todos; antigüedad; + salidas en el equipo; + nivel. Grupos
  con < 300 personas van a "resto". El último paso debe reproducir los grupos
  publicados en la selección de grupos. La eficiencia de cada paso se mide en
  las 4 pruebas como en la selección.

Sólo se escriben agregados; no se publican riesgos individuales.
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
import engineering_feature_block_selection as fs  # noqa: E402
import engineering_hazard_adjustment as adj  # noqa: E402
import engineering_playbook_group_selection as gs  # noqa: E402
import engineering_playbook_tenure_confirmation as cf  # noqa: E402  (penalización fija y ajustes no finitos)

pm = cf.pm
ROOT = hz.ROOT
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "engineering" / "20261003" / "model-walkthrough-v1"
CONFIRMATION = gs.CONFIRMATION
SELECTION = ROOT / "output" / "analysis" / "engineering" / "20261003" / "playbook-group-selection-v1" / "group-selection-results.json"
EXAMPLE_MONTH = (2026, 1)
GROUPS = {
    "I": "3-5 años · con salidas · entrada",
    "II": "5-10 años · sin salidas · entrada",
    "III": "10+ años · sin salidas · medio",
}
STEPS = [
    ("todos", []),
    ("antiguedad", ["antiguedad"]),
    ("salidas", ["antiguedad", "salidas_equipo"]),
    ("nivel", ["antiguedad", "salidas_equipo", "nivel"]),
]
# Empleados ficticios: sólo ilustran el cálculo; las señales se eligen a mano.
EXAMPLE_PEOPLE = [
    ("Fernando", "I", {"level_grouped": "8 - Assoc & Int/Eng", "tenure_playbook_band": "3-5 years", "manager_changes_12m": "1", "team_exits_12m": "2+", "direct_reports_band": "0", "time_since_promotion_band": "sin promo, contratado 3+ years", "rehire": "no"}),
    ("Julia", "I", {"level_grouped": "7 - Senior & Lead", "tenure_playbook_band": "3-5 years", "manager_changes_12m": "0", "team_exits_12m": "1", "direct_reports_band": "0", "time_since_promotion_band": "promo 1-2 years", "rehire": "no"}),
    ("Leah", "II", {"level_grouped": "7 - Senior & Lead", "tenure_playbook_band": "5-10 years", "manager_changes_12m": "1", "team_exits_12m": "0", "direct_reports_band": "0", "time_since_promotion_band": "promo 3+ years", "rehire": "no"}),
    ("Ana", "II", {"level_grouped": "8 - Assoc & Int/Eng", "tenure_playbook_band": "5-10 years", "manager_changes_12m": "0", "team_exits_12m": "0", "direct_reports_band": "0", "time_since_promotion_band": "promo 2-3 years", "rehire": "yes"}),
    ("Carlos", "III", {"level_grouped": "6 - Staff & /Mgr", "tenure_playbook_band": "10+ years", "manager_changes_12m": "0", "team_exits_12m": "0", "direct_reports_band": "1-5", "time_since_promotion_band": "promo 3+ years", "rehire": "no"}),
    ("Sofía", "III", {"level_grouped": "5 - Sr Staff & /Mgr", "tenure_playbook_band": "10+ years", "manager_changes_12m": "0", "team_exits_12m": "0", "direct_reports_band": "6+", "time_since_promotion_band": "promo <1 year", "rehire": "no"}),
]
PROFILE_FEATURES = ["level_grouped", "tenure_playbook_band", "manager_changes_12m", "team_exits_12m", "direct_reports_band", "time_since_promotion_band", "rehire"]
MONTHS_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


# ---------------------------------------------------------------- cálculo


def cumulative(hazards: np.ndarray) -> np.ndarray:
    """R6 = 1 - (1 - h1)...(1 - h6) sobre el último eje."""
    return 1.0 - np.prod(1.0 - np.asarray(hazards, dtype=float), axis=-1)


def monthly_hazards(model, frame: pd.DataFrame) -> np.ndarray:
    """h por mes (filas × 6), igual que ``hz.six_month_predictions`` antes de acumular."""
    pieces = []
    for month_ahead in range(6):
        part = frame.copy()
        part["snapshot_date"] = part["snapshot_date"] + pd.DateOffset(months=month_ahead)
        part["calendar_month"] = part["snapshot_date"].dt.month.astype(str)
        pieces.append(model.predict(part))
    return np.column_stack(pieces)


def month_labels(date: pd.Timestamp) -> list[str]:
    """Mes en que termina cada periodo mensual: la foto de enero cubre feb..jul."""
    return [MONTHS_ES[(date + pd.DateOffset(months=k + 1)).month - 1] for k in range(6)]


def group_summary(people: np.ndarray, hazards: np.ndarray, events: np.ndarray | None = None) -> dict:
    """Las dos cuentas: promedio por mes y luego acumular; acumular por persona y luego promediar."""
    weights = np.asarray(people, dtype=float)
    mean_h = np.average(hazards, axis=0, weights=weights)
    out = {
        "people": int(round(weights.sum())),
        "hazard_percent_by_month": [round(100.0 * v, 3) for v in mean_h],
        "r6_formula_percent": round(100.0 * float(cumulative(mean_h)), 3),
        "r6_mean_of_people_percent": round(100.0 * float(np.average(cumulative(hazards), weights=weights)), 3),
    }
    if events is not None:
        total = float(np.sum(events))
        out["observed_events_published"] = bool(total >= fs.MIN_EVENTS)
        if total >= fs.MIN_EVENTS:
            out["observed_events"] = int(total)
            out["observed_6m_percent"] = round(100.0 * total / weights.sum(), 3)
    return out


def example_frame(people: list[tuple[str, str, dict]], date: pd.Timestamp, references: dict[str, str]) -> pd.DataFrame:
    """Filas ficticias con las mismas columnas que las celdas del modelo, interacciones incluidas."""
    frame = pd.DataFrame([raw for _, _, raw in people])
    for name, (left, right) in pm.interaction_pairs(gs.TENURE).items():
        a, b = frame[left], frame[right]
        frame[name] = np.where((a != references[left]) & (b != references[right]), a + " | " + b, adj.REFERENCE_NAME)
    frame["snapshot_date"] = date
    frame["calendar_month"] = str(date.month)
    frame["exposure_count"] = 1
    return frame


def check_known(model, frame: pd.DataFrame) -> None:
    """Cada valor ficticio debe ser una categoría que el modelo conoce (si no, contaría como referencia)."""
    for feature in model.encoder.features:
        if feature == "calendar_month":
            continue
        unknown = set(frame[feature].astype(str)) - set(model.encoder.categories[feature])
        if unknown:
            raise RuntimeError(f"Valores ficticios desconocidos para {feature}: {sorted(unknown)}")


def dot_count(people: int, per_dot: int = 100) -> int:
    return int(round(people / per_dot))


def profile_text(row: pd.Series) -> dict:
    """Descripción corta del perfil, sin identificadores."""
    exits = {"0": "sin salidas en su equipo", "1": "1 salida en su equipo", "2+": "2+ salidas en su equipo"}
    changes = {"0": "sin cambio de manager", "1": "1 cambio de manager", "2+": "2+ cambios de manager"}
    reports = {"0": "sin reportes", "1-5": "1-5 reportes", "6+": "6+ reportes"}
    promo = {
        "promo <1 year": "promoción hace <1 año",
        "promo 1-2 years": "promoción hace 1-2 años",
        "promo 2-3 years": "promoción hace 2-3 años",
        "promo 3+ years": "promoción hace 3+ años",
    }
    raw = {f: str(row[f]) for f in PROFILE_FEATURES}
    level = raw["level_grouped"].split(" - ")[0]
    return {
        "raw": raw,
        "antiguedad": gs.TENURE_LABELS.get(raw["tenure_playbook_band"], raw["tenure_playbook_band"]),
        "nivel": f"nivel {level}",
        "salidas_equipo": exits.get(raw["team_exits_12m"], raw["team_exits_12m"]),
        "cambios_manager": changes.get(raw["manager_changes_12m"], raw["manager_changes_12m"]),
        "reportes": reports.get(raw["direct_reports_band"], raw["direct_reports_band"]),
        "promocion": promo.get(raw["time_since_promotion_band"], "sin promoción registrada"),
        "recontratado": raw["rehire"] == "yes",
    }


# ---------------------------------------------------------------- piezas


def example(spec: dict, windows: list[dict], references: dict[str, str]) -> dict:
    """Empleados ficticios y grupos I-III en la foto de enero de 2026 con el modelo de la 4.ª prueba."""
    fold = spec["folds"][-1]
    model = fold["model"]
    _, direct = spec["frames"]
    dates = sorted(d for d in direct["snapshot_date"].unique() if (pd.Timestamp(d).year, pd.Timestamp(d).month) == EXAMPLE_MONTH)
    if len(dates) != 1:
        raise RuntimeError("No hay una única foto de enero de 2026.")
    date = pd.Timestamp(dates[0])
    if date not in windows[-1]["test_dates"]:
        raise RuntimeError("La foto de ejemplo no está en la 4.ª prueba.")
    cells = direct.loc[direct["snapshot_date"] == date].reset_index(drop=True)
    hazards = monthly_hazards(model, cells)
    if not np.allclose(np.clip(cumulative(hazards), 1e-8, 1 - 1e-8), hz.six_month_predictions(model, cells)):
        raise RuntimeError("La acumulación por mes no reproduce el riesgo a seis meses del modelo.")
    labels = gs.combination_labels(gs.coarse_keys(cells), ("antiguedad", "salidas_equipo", "nivel"))
    people = cells["exposure_count"].to_numpy(dtype=float)
    events = cells["event_count"].to_numpy(dtype=float)

    groups = {}
    for key, label in GROUPS.items():
        mask = (labels == label).to_numpy()
        summary = group_summary(people[mask], hazards[mask], events[mask])
        if summary["people"] < gs.MIN_GROUP_PEOPLE:
            raise RuntimeError(f"El grupo {key} tiene menos de {gs.MIN_GROUP_PEOPLE} personas.")
        groups[key] = {"label": label, **summary}

    fake = example_frame(EXAMPLE_PEOPLE, date, references)
    check_known(model, fake)
    fake_labels = gs.combination_labels(gs.coarse_keys(fake), ("antiguedad", "salidas_equipo", "nivel"))
    fake_hazards = monthly_hazards(model, fake)
    employees = []
    for i, (name, key, _) in enumerate(EXAMPLE_PEOPLE):
        if fake_labels.iloc[i] != GROUPS[key]:
            raise RuntimeError(f"{name} no cae en el grupo {key}.")
        employees.append(
            {
                "name": name,
                "fictitious": True,
                "group": key,
                "description": profile_text(fake.iloc[i]),
                "hazard_percent_by_month": [round(100.0 * v, 3) for v in fake_hazards[i]],
                "r6_percent": round(100.0 * float(cumulative(fake_hazards[i])), 3),
            }
        )
    total = group_summary(people, hazards, events)
    return {
        "snapshot": str(date.date()),
        "months": month_labels(date),
        "model_fold": 4,
        "model_trained_before": str(windows[-1]["start"].date()),
        "people": total["people"],
        "overall": total,
        "groups": groups,
        "employees": employees,
        "coefficients": {c: round(float(v), 6) for c, v in zip(model.encoder.columns, model.beta)},
    }


def plane(spec: dict, published: dict) -> dict:
    """Los cuatro pasos del plano en la foto de jul-2026, con su eficiencia en las 4 pruebas."""
    monthly, _ = spec["frames"]
    l2 = spec["folds"][-1]["metrics"]["l2"]
    model = adj.fit_converged(monthly, spec["features"], l2, pm.TREND, pm.RECALIBRATION_MONTHS)
    latest = monthly["snapshot_date"].max()
    current, risk = gs.snapshot_risk(model, monthly, latest)
    keys = gs.coarse_keys(current)
    people = current["exposure_count"].to_numpy(dtype=float)
    tests = [(f, f["test"], gs.coarse_keys(f["test"]), f["test"]["snapshot_date"].nunique()) for f in spec["folds"]]

    steps = []
    for name, variables in STEPS:
        labels = gs.combination_labels(keys, tuple(variables)) if variables else pd.Series("Engineering", index=current.index)
        table = gs.grouped(labels, people, np.zeros_like(people), risk * people, 1, gs.MIN_GROUP_PEOPLE)
        efficiency = 0.0
        if variables:
            values = [
                gs.evaluate_fold(gs.combination_labels(k, tuple(variables)), t["exposure_count"].to_numpy(dtype=float), t["event_count"].to_numpy(dtype=float), f["predictions"], n)["efficiency"]
                for f, t, k, n in tests
            ]
            efficiency = float(np.mean(values))
        rows = [
            {"group": label, "people": int(round(r["exposure"])), "predicted_6m_percent": round(100.0 * r["risk"], 3), "dots": dot_count(int(round(r["exposure"])))}
            for label, r in table.sort_values("risk", ascending=False).iterrows()
        ]
        steps.append(
            {
                "name": name,
                "variables": variables,
                "groups": rows,
                "groups_eligible": sum(r["group"] != gs.REST for r in rows),
                "mean_efficiency": round(efficiency, 5),
            }
        )

    last = {r["group"]: r for r in steps[-1]["groups"] if r["group"] != gs.REST}
    expected = {r["group"]: r for r in published["final"]["all_groups"]}
    if set(last) != set(expected) or any(abs(last[g]["predicted_6m_percent"] - expected[g]["predicted_6m_percent"]) > 0.01 for g in last):
        raise RuntimeError("El último paso no reproduce los grupos publicados.")
    if abs(steps[-1]["mean_efficiency"] - published["winner"]["mean_efficiency"]) > 1e-4:
        raise RuntimeError("La eficiencia del último paso no reproduce la selección.")
    tree = max((c for c in published["candidates"] if c["kind"] == "tree"), key=lambda c: c["mean_efficiency"])
    return {
        "snapshot": str(latest.date()),
        "people": int(round(people.sum())),
        "mean_predicted_6m_percent": round(100.0 * float(np.average(risk, weights=people)), 3),
        "people_per_dot": 100,
        "steps": steps,
        "candidates": len(published["candidates"]),
        "best_tree_efficiency": tree["mean_efficiency"],
        "top": [r["group"] for r in published["final"]["top"]],
    }


# ---------------------------------------------------------------- reporte


def build_report(result: dict) -> str:
    ex, pl = result["example"], result["plane"]
    months = ex["months"]
    lines = [
        "# Cómo calcula el riesgo el modelo B — Engineering",
        "",
        f"Creado: {result['created_at_utc']}. Modelo de la 4.ª prueba (entrenado antes de {ex['model_trained_before']}).",
        "",
        f"## Paso 1 · Empleados ficticios, foto {ex['snapshot']} (h mensual %)",
        "",
        "Personas inventadas para ilustrar el cálculo; su riesgo sale del modelo real.",
        "",
        "| Nombre | Grupo | Descripción | " + " | ".join(months) + " | R6 % |",
        "|---|---|---|" + "---:|" * 7,
    ]
    for p in ex["employees"]:
        d = p["description"]
        text = f"{d['antiguedad']}, {d['nivel']}, {d['salidas_equipo']}, {d['cambios_manager']}, {d['reportes']}, {d['promocion']}"
        lines.append(f"| {p['name']} | {p['group']} | {text} | " + " | ".join(f"{v:.2f}" for v in p["hazard_percent_by_month"]) + f" | {p['r6_percent']:.2f} |")
    lines += [
        "",
        "## Paso 2 · Grupos (promedio de h por mes %)",
        "",
        "| Grupo | Personas | " + " | ".join(months) + " | R6 con la fórmula % | Promedio de R6 % | Real % |",
        "|---|---:|" + "---:|" * 9,
    ]
    for key, g in [*ex["groups"].items(), ("Engineering", ex["overall"])]:
        observed = g.get("observed_6m_percent")
        lines.append(
            f"| {key} {g.get('label', '')} | {g['people']} | " + " | ".join(f"{v:.2f}" for v in g["hazard_percent_by_month"])
            + f" | {g['r6_formula_percent']:.2f} | {g['r6_mean_of_people_percent']:.2f} | {'—' if observed is None else f'{observed:.2f}'} |"
        )
    lines += ["", f"## Paso 3 · Pasos del plano, foto {pl['snapshot']} ({pl['people']:,} personas)", ""]
    for s in pl["steps"]:
        lines.append(f"- {s['name']}: {s['groups_eligible']} grupos, eficiencia media {s['mean_efficiency']:.3f}, mayor riesgo {s['groups'][0]['predicted_6m_percent']:.2f}%")
    lines.append(f"- Árbol (mejor): eficiencia {pl['best_tree_efficiency']:.3f}; {pl['candidates']} candidatas.")
    return "\n".join(lines) + "\n"


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
    published = json.loads(SELECTION.read_text(encoding="utf-8"))
    if confirmation["final_key"] != "b":
        raise RuntimeError("El modelo final de la confirmación no es B.")

    calendar = [d for d in hz.fetch_calendar() if d >= fs.MIN_SNAPSHOT]
    monthly, direct, _ = pm.load_person_months(calendar)
    windows = fs.fold_windows(direct)
    references = pm.modal_references(direct)
    runner = pm.Runner(monthly, direct, windows, references)
    b = runner.run(cf.features_for(gs.TENURE, cf.CAREER), gs.TENURE, tag="B")
    reference_lift = confirmation["specs"]["b"]["folds"][-1]["lift_at_10_percent"]
    if abs(b["folds"][-1]["metrics"]["lift_at_10_percent"] / reference_lift - 1.0) >= 0.01:
        raise RuntimeError("La 4.ª prueba de B no se reproduce frente a la confirmación.")

    result = {
        "artifact": "engineering-model-walkthrough",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": hz.KNOWLEDGE_BOUNDARY.strftime("%Y-%m-%d"),
        "deliverable_classification": "presentation",
        "authorization": {"path": str(fs.AUTHORIZATION.relative_to(ROOT)), "id": authorization["authorization_id"]},
        "model": {"name": confirmation["final_name"], "features": b["features"], "parameters": b["parameters"]},
        "design": {
            "groups": GROUPS,
            "example_people": "ficticios, con señales elegidas a mano",
            "min_group_people": gs.MIN_GROUP_PEOPLE,
            "min_published_events": fs.MIN_EVENTS,
            "steps": [{"name": n, "variables": v} for n, v in STEPS],
        },
        "example": example(b, windows, references),
        "plane": plane(b, published),
        "privacy": {
            "employee_level_rows_persisted": False,
            "employee_ids_selected": False,
            "aggregate_training_frame_persisted": False,
            "individual_scores_published": False,
            "example_employees_fictitious": True,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "walkthrough-results.json"
    report_path = output_dir / "walkthrough-report.md"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    manifest = {
        "artifact": result["artifact"],
        "created_at_utc": result["created_at_utc"],
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "authorization": result["authorization"],
        "queries": {"calendar": str(hz.CALENDAR_QUERY.relative_to(ROOT)), "person_month_frame": str(pm.FRAME_QUERY.relative_to(ROOT))},
        "query_sha256": {"calendar": hz.sha256_file(hz.CALENDAR_QUERY), "person_month_frame": hz.sha256_file(pm.FRAME_QUERY)},
        "sources": {str(p.relative_to(ROOT)): hz.sha256_file(p) for p in (CONFIRMATION, SELECTION)},
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": hz.sha256_file(result_path),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": hz.sha256_file(report_path),
        "employee_level_rows_persisted": False,
        "aggregate_training_frame_persisted": False,
        "individual_scores_published": False,
    }
    (output_dir / "walkthrough-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(build_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
