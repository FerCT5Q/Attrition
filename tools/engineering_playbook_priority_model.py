"""Modelo v2 de Engineering con las variables prioritarias del playbook (2026-10-03).

No modifica ni reemplaza el modelo vigente (``hazard-adjustment-v2``). Usa el
mismo hazard discreto ``cloglog`` sin tendencia ni recalibración, los mismos
cuatro folds rolling-origin y la misma población, con un frame nuevo
(``engineering_person_month_features_playbook_v2_20261003.sql``) leído en
memoria bajo ``config/attrition_model_in_memory_training_authorization_20261001.json``.

Pasos:

0. Reproduce el modelo vigente con el frame nuevo (mismas exposiciones,
   salidas y métricas) para que la comparación sea justa.
1. Cortes de antigüedad: vigentes (<1, 1-3, 3-7, 7+), los de Julia (<1, 1-3,
   3-5, 5+) y los del playbook (<1, 1-2, 2-3, 3-5, 5-10, 10+), sobre base +
   manager/equipo. Entre los que quedan a menos de 2% relativo del mejor en
   PR-AUC y lift@10% se prefiere el alineado al playbook (Julia, playbook,
   vigente, en ese orden).
2. Selección hacia delante de variables del playbook (QVoice excluido): en
   cada paso se agrega la candidata con mayor mejora entre las que cumplen la
   regla de promoción (gana >= 3 de 4 folds en PR-AUC y lift@10% sin peor
   Brier medio).
3. Interacciones del modelo vigente (nivel × antigüedad, antigüedad × cambios
   de manager) con los cortes elegidos, aceptadas con la misma regla.
4. Comparación final contra el vigente: el v2 sólo es "mejor" si cumple la
   regla de promoción frente a él.

Sólo se escriben agregados: métricas, coeficientes y grupos >= 30 personas
(observado sólo con >= 30 salidas).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import critical_tech_discrete_hazard_model as hz  # noqa: E402
import critical_tech_model_comparison_rolling as ro  # noqa: E402
import engineering_feature_block_selection as fs  # noqa: E402
import engineering_hazard_adjustment as adj  # noqa: E402

ROOT = hz.ROOT
FRAME_QUERY = ROOT / "queries" / "profiles" / "engineering_person_month_features_playbook_v2_20261003.sql"
INCUMBENT_RESULTS = ROOT / "output" / "analysis" / "engineering" / "20261001" / "hazard-adjustment-v2" / "adjustment-results.json"
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "engineering" / "20261003" / "playbook-priority-v1"
AUDITS = [
    ROOT / "queries" / "audits" / "engineering_playbook_priority_feature_coverage_by_year_20261003.sql",
    ROOT / "queries" / "audits" / "engineering_playbook_priority_source_start_by_month_20261003.sql",
    ROOT / "queries" / "audits" / "engineering_playbook_priority_hire_date_fields_by_month_20261003.sql",
    ROOT / "queries" / "audits" / "engineering_playbook_priority_service_date_rehire_agreement_20261003.sql",
    ROOT / "queries" / "audits" / "engineering_playbook_priority_value_continuity_20261003.sql",
    ROOT / "queries" / "audits" / "engineering_playbook_priority_promo_level_entry_continuity_20261003.sql",
    ROOT / "queries" / "audits" / "engineering_playbook_priority_band_profile_20261003.sql",
]
TREND = "none"
RECALIBRATION_MONTHS = 0
# ``hz.fit_irls`` escala la penalización por el tamaño medio de celda; al
# colapsar celdas la misma L2 penalizaría ~8 veces más. Se fija la escala en
# el tamaño medio de celda del frame vigente (~8 personas por celda mensual),
# con lo que el vigente colapsado reproduce sus métricas publicadas
# (diagnóstico de 2026-10-03: PR-AUC 0.0512 y lift@10% 2.014 en ambos granos).
PENALTY_CELL_SCALE = 8.0
_ORIGINAL_FIT_IRLS = hz.fit_irls


def fit_irls_fixed_scale(frame: pd.DataFrame, link: str, l2: float, encoder=None, max_iter: int = 150) -> hz.IRLSModel:
    mean_n = max(float(np.mean(frame["exposure_count"].to_numpy(dtype=float))), 1.0)
    model = _ORIGINAL_FIT_IRLS(frame, link, l2 * PENALTY_CELL_SCALE / mean_n, encoder, max_iter)
    model.l2 = l2
    return model


# Sólo en este proceso; los scripts y resultados del modelo vigente no cambian.
hz.fit_irls = fit_irls_fixed_scale

TENURE_OPTIONS = {
    "tenure_julia_band": "cortes de Julia (<1, 1-3, 3-5, 5+)",
    "tenure_playbook_band": "cortes del playbook (<1, 1-2, 2-3, 3-5, 5-10, 10+)",
    "company_tenure_band": "cortes vigentes (<1, 1-3, 3-7, 7+)",
}
MANAGER_BLOCK = ["manager_changes_12m", "team_exits_12m", "direct_reports_band"]
CANDIDATES = {
    "prior_experience_band": "años de experiencia antes de Qualcomm",
    "rehire": "recontratación",
    "time_since_promotion_band": "tiempo desde la última promoción",
    "time_at_level_band": "tiempo en el nivel (desde 2022-10)",
    "manager_left_6m": "el manager salió en los últimos 6 meses",
    "ios_12m": "movimiento interno (IOS) en 12 meses (desde 2023-10)",
    "layers_band": "capas desde el CEO (desde 2023-03)",
    "work_arrangement_group": "modalidad de trabajo (desde 2024-08)",
}
FRAME_FEATURES = ["level_grouped", "company_tenure_band", "tenure_julia_band", "tenure_playbook_band"] + MANAGER_BLOCK + list(CANDIDATES)
OUTPUT_COLUMNS = ["snapshot_date"] + FRAME_FEATURES + ["y_next", "y_6m"]
INCUMBENT_INTERACTIONS = ["level_x_tenure", "tenure_x_manager_changes"]


# ---------------------------------------------------------------- carga en memoria


def check_output_columns(columns: list[str]) -> None:
    sys.path.insert(0, str(fs.HELPER_DIR))
    import run_readonly_query as helper

    leaked = sorted(set(columns) & helper.SENSITIVE_OUTPUT_COLUMNS)
    if leaked:
        raise RuntimeError(f"La consulta devolvería columnas restringidas: {leaked}")
    if columns != OUTPUT_COLUMNS:
        raise RuntimeError(f"Columnas inesperadas: {columns}")


def load_person_months(dates: list[pd.Timestamp]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Lee persona-mes por lotes y devuelve celdas exactas mensual y a seis meses."""
    sys.path.insert(0, str(fs.HELPER_DIR))
    import run_readonly_query as helper

    template = FRAME_QUERY.read_text(encoding="utf-8")
    keys = ["snapshot_date"] + FRAME_FEATURES
    monthly_parts, direct_parts = [], []
    totals = {"person_months": 0, "monthly_labeled": 0, "six_month_labeled": 0}
    connection = helper.connect()
    try:
        for offset in range(0, len(dates), fs.SNAPSHOTS_PER_QUERY):
            chunk = dates[offset : offset + fs.SNAPSHOTS_PER_QUERY]
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
            for column in FRAME_FEATURES:
                frame[column] = frame[column].fillna("(unknown)").astype(str)
            totals["person_months"] += len(frame)
            for target, parts, name in [("y_next", monthly_parts, "monthly_labeled"), ("y_6m", direct_parts, "six_month_labeled")]:
                labeled = frame.loc[frame[target].notna(), keys + [target]]
                totals[name] += len(labeled)
                if labeled.empty:
                    continue
                cells = labeled.groupby(keys, observed=True)[target].agg(["size", "sum"]).reset_index()
                parts.append(cells.rename(columns={"size": "exposure_count", "sum": "event_count"}))
            fs.log(f"fotos {chunk[0].date()}..{chunk[-1].date()}: {len(frame)} persona-mes en {time.time() - started:.0f}s")
            del frame
    finally:
        connection.close()
    return finalize(pd.concat(monthly_parts)), finalize(pd.concat(direct_parts), six_month=True), totals


def finalize(cells: pd.DataFrame, six_month: bool = False) -> pd.DataFrame:
    cells = cells.copy()
    for column in FRAME_FEATURES:
        cells[column] = cells[column].astype("category")
    cells["exposure_count"] = cells["exposure_count"].astype(int)
    cells["event_count"] = cells["event_count"].astype(int)
    cells["six_month_frame"] = six_month
    return cells.reset_index(drop=True)


# ---------------------------------------------------------------- especificaciones


def interaction_pairs(tenure: str) -> dict[str, tuple[str, str]]:
    return {
        "level_x_tenure": ("level_grouped", tenure),
        "tenure_x_manager_changes": (tenure, "manager_changes_12m"),
    }


def modal_references(direct: pd.DataFrame) -> dict[str, str]:
    columns = ["level_grouped", "manager_changes_12m"] + list(TENURE_OPTIONS)
    return {c: str(direct.groupby(c, observed=True)["exposure_count"].sum().idxmax()) for c in columns}


def spec_frames(monthly: pd.DataFrame, direct: pd.DataFrame, features: list[str], tenure: str, references: dict[str, str]):
    """Colapsa las celdas a las variables de la especificación y agrega interacciones.

    El colapso conserva exposiciones y salidas exactas; sólo reduce filas.
    """
    pairs = interaction_pairs(tenure)
    wanted = [f for f in features if f in pairs]
    raw = sorted({f for f in features if f not in pairs and f != "calendar_month"} | {c for f in wanted for c in pairs[f]})
    out = []
    for frame in (monthly, direct):
        cells = frame.groupby(["snapshot_date"] + raw, observed=True)[["exposure_count", "event_count"]].sum().reset_index()
        cells = cells.loc[cells["exposure_count"] > 0].reset_index(drop=True)
        for column in raw:
            cells[column] = cells[column].astype(str)
        for name in wanted:
            left, right = pairs[name]
            a, b = cells[left], cells[right]
            cells[name] = np.where((a != references[left]) & (b != references[right]), a + " | " + b, adj.REFERENCE_NAME)
        cells["distinct_employee_count"] = cells["exposure_count"]
        cells["calendar_month"] = cells["snapshot_date"].dt.month.astype(str)
        cells["six_month_frame"] = frame is direct
        out.append(cells)
    return out


class Runner:
    def __init__(self, monthly: pd.DataFrame, direct: pd.DataFrame, windows: list[dict], references: dict[str, str]):
        self.monthly, self.direct, self.windows, self.references = monthly, direct, windows, references
        self.cache: dict[tuple, dict] = {}

    def run(self, features: list[str], tenure: str, tag: str = "") -> dict:
        key = tuple(features)
        if key not in self.cache:
            started = time.time()
            monthly, direct = spec_frames(self.monthly, self.direct, features, tenure, self.references)
            spec = adj.evaluate(monthly, direct, features, self.windows, TREND, RECALIBRATION_MONTHS)
            spec["tenure"] = tenure
            spec["frames"] = (monthly, direct)
            self.cache[key] = spec
            s = spec["summary"]
            fs.log(f"{tag or label(spec)}: PR-AUC {s['pr_auc']:.5f} lift10 {s['lift_at_10_percent']:.4f} brier {s['brier_score']:.6f} ({time.time() - started:.0f}s, {len(monthly)} celdas)")
        return self.cache[key]


def label(spec: dict) -> str:
    extra = [f for f in spec["features"] if f not in ["level_grouped", "calendar_month", spec["tenure"]] + MANAGER_BLOCK]
    return f"base ({spec['tenure']}) + manager/equipo" + (f" + {' + '.join(extra)}" if extra else "")


def score(spec: dict, reference: dict) -> float:
    return spec["summary"]["pr_auc"] / reference["summary"]["pr_auc"] + spec["summary"]["lift_at_10_percent"] / reference["summary"]["lift_at_10_percent"]


def public(spec: dict) -> dict:
    return {
        "label": label(spec),
        "features": spec["features"],
        "tenure": spec["tenure"],
        "parameters": spec["parameters"],
        "summary": spec["summary"],
        "folds": [f["metrics"] for f in spec["folds"]],
    }


def within_tolerance(spec: dict, best_pr: float, best_lift: float) -> bool:
    return (
        spec["summary"]["pr_auc"] >= (1 - fs.PARSIMONY_TOLERANCE) * best_pr
        and spec["summary"]["lift_at_10_percent"] >= (1 - fs.PARSIMONY_TOLERANCE) * best_lift
    )


# ---------------------------------------------------------------- pasos


def tenure_step(runner: Runner) -> tuple[str, list[dict]]:
    specs = {t: runner.run(["level_grouped", t, "calendar_month"] + MANAGER_BLOCK, t) for t in TENURE_OPTIONS}
    best_pr = max(s["summary"]["pr_auc"] for s in specs.values())
    best_lift = max(s["summary"]["lift_at_10_percent"] for s in specs.values())
    current = specs["company_tenure_band"]
    rows = []
    for tenure, spec in specs.items():
        rows.append(
            {
                "tenure": tenure,
                "description": TENURE_OPTIONS[tenure],
                "parameters": spec["parameters"],
                "summary": spec["summary"],
                "within_tolerance": within_tolerance(spec, best_pr, best_lift),
                "vs_current_cuts": adj.promotion(spec, current) if tenure != "company_tenure_band" else None,
            }
        )
    chosen = next(r["tenure"] for r in rows if r["within_tolerance"])
    return chosen, rows


def forward_step(runner: Runner, start: dict) -> tuple[dict, list[dict]]:
    current = start
    trail = []
    remaining = list(CANDIDATES)
    while remaining:
        candidates = []
        for name in remaining:
            spec = runner.run(current["features"] + [name], current["tenure"])
            rule = adj.promotion(spec, current)
            trail.append({"step": len(trail), "added": name, "base": label(current), "parameters": spec["parameters"], "summary": spec["summary"], "rule": rule})
            candidates.append((spec, rule, name))
        promoted = [c for c in candidates if c[1]["promoted"]]
        if not promoted:
            break
        best = max(promoted, key=lambda c: score(c[0], current))
        current = best[0]
        remaining.remove(best[2])
        trail.append({"accepted": best[2], "now": label(current)})
        fs.log(f"aceptada {best[2]}")
    return current, trail


def interaction_step(runner: Runner, start: dict) -> tuple[dict, list[dict]]:
    current = start
    trail = []
    remaining = list(INCUMBENT_INTERACTIONS)
    while remaining:
        candidates = []
        for name in remaining:
            spec = runner.run(current["features"] + [name], current["tenure"])
            rule = adj.promotion(spec, current)
            trail.append({"step": len(trail), "added": name, "base": label(current), "parameters": spec["parameters"], "summary": spec["summary"], "rule": rule})
            candidates.append((spec, rule, name))
        promoted = [c for c in candidates if c[1]["promoted"]]
        if not promoted:
            break
        best = max(promoted, key=lambda c: score(c[0], current))
        current = best[0]
        remaining.remove(best[2])
        trail.append({"accepted": best[2], "now": label(current)})
    return current, trail


def drop_one(runner: Runner, final: dict) -> list[dict]:
    rows = []
    for feature in [f for f in final["features"] if f in CANDIDATES]:
        features = [f for f in final["features"] if f != feature]
        spec = runner.run(features, final["tenure"], tag=f"sin {feature}")
        rows.append({"dropped": feature, "parameters": spec["parameters"], "summary": spec["summary"]})
    return rows


def category_profile(direct: pd.DataFrame) -> list[dict]:
    """Distribución y tasa observada a seis meses por categoría (agregada, >= 30)."""
    snapshots = direct["snapshot_date"].nunique()
    rows = []
    for feature in FRAME_FEATURES:
        grouped = direct.groupby(feature, observed=True)[["exposure_count", "event_count"]].sum()
        for value, row in grouped.iterrows():
            people = row["exposure_count"] / snapshots
            if people < fs.MIN_PEOPLE:
                continue
            rows.append(
                {
                    "variable": feature,
                    "category": str(value),
                    "people_per_snapshot": int(round(people)),
                    "six_month_rate_percent": round(100.0 * row["event_count"] / row["exposure_count"], 3) if row["event_count"] >= fs.MIN_EVENTS else None,
                }
            )
    return rows


# ---------------------------------------------------------------- reporte


def fmt(s: dict) -> str:
    ratios = ", ".join(f"{r:.2f}" for r in s["calibration_ratio_by_fold"])
    return f"{s['pr_auc']:.4f} | {s['lift_at_10_percent']:.3f} | {s['lift_at_20_percent']:.3f} | {s['brier_score']:.5f} | {ratios}"


def rule_cells(r: dict) -> str:
    return f"{r['pr_auc_wins']}/4 | {r['lift_wins']}/4 | {'sí' if r['brier_not_worse'] else 'no'} | {'sí' if r['promoted'] else 'no'}"


def trail_lines(trail: list[dict]) -> list[str]:
    lines = ["| Paso | Agregada | Sobre | Parámetros | PR-AUC | Lift@10% | Brier | Gana PR | Gana lift | Brier no peor | Aceptada |", "|---:|---|---|---:|---:|---:|---:|---:|---:|---|---|"]
    for row in trail:
        if "accepted" in row:
            lines.append(f"| | **aceptada: {row['accepted']}** | → {row['now']} | | | | | | | | |")
            continue
        s = row["summary"]
        lines.append(f"| {row['step']} | {row['added']} | {row['base']} | {row['parameters']} | {s['pr_auc']:.4f} | {s['lift_at_10_percent']:.3f} | {s['brier_score']:.5f} | {rule_cells(row['rule'])} |")
    return lines


def build_report(result: dict) -> str:
    header = "| Especificación | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado por fold |"
    rule = "|---|---:|---:|---:|---:|---:|---|"
    frame = result["frame"]
    inc = result["incumbent"]
    lines = [
        "# Modelo v2 de Engineering con variables prioritarias del playbook",
        "",
        f"Creado: {result['created_at_utc']}. Frontera de conocimiento: {result['knowledge_boundary']}. QVoice excluido (modelo en desarrollo).",
        f"Fotos {frame['first_snapshot']} a {frame['last_snapshot']}: {frame['six_month_exposures']:,} exposiciones a seis meses y {frame['six_month_events']:,} salidas.",
        f"Entrenamiento en memoria bajo `{result['authorization']['path']}`; sin filas ni IDs persistidos. Hazard `cloglog` sin tendencia ni recalibración.",
        "",
        "## 0. Reproducción del modelo vigente con el frame nuevo",
        "",
        header,
        rule,
        f"| Vigente publicado ({inc['published_label']}) | {inc['published']['parameters']} | {fmt(inc['published']['summary'])} |",
        f"| Vigente reproducido | {inc['reproduced']['parameters']} | {fmt(inc['reproduced']['summary'])} |",
        "",
        f"Exposiciones iguales al vigente: {'sí' if inc['same_exposures'] else 'no'}. Métricas a menos de 1% relativo: {'sí' if inc['same_metrics'] else 'no'}. "
        "La comparación final usa el vigente reproducido (misma medición que el v2).",
        "",
        "## 1. Cortes de antigüedad (base + manager/equipo)",
        "",
        "| Cortes | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado | Dentro de 2% | Frente a cortes vigentes |",
        "|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in result["tenure_step"]:
        versus = "—" if row["vs_current_cuts"] is None else f"PR {row['vs_current_cuts']['pr_auc_wins']}/4, lift {row['vs_current_cuts']['lift_wins']}/4, Brier no peor {'sí' if row['vs_current_cuts']['brier_not_worse'] else 'no'}"
        lines.append(f"| {row['description']} | {row['parameters']} | {fmt(row['summary'])} | {'sí' if row['within_tolerance'] else 'no'} | {versus} |")
    lines += ["", f"Cortes elegidos: **{result['tenure_choice']}**.", "", "## 2. Variables del playbook (selección hacia delante, regla de promoción)", ""]
    lines += trail_lines(result["forward_trail"])
    lines += ["", "## 3. Interacciones del vigente con los cortes elegidos", ""]
    lines += trail_lines(result["interaction_trail"])
    lines += ["", "## 4. Contribución de cada variable del playbook en el v2 (quitar una)", "", "| Variable quitada | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado |", "|---|---:|---:|---:|---:|---:|---|"]
    for row in result["drop_one"]:
        lines.append(f"| {row['dropped']} | {row['parameters']} | {fmt(row['summary'])} |")
    final = result["final"]
    verdict = result["final_vs_incumbent"]
    lines += [
        "",
        "## 5. Comparación final",
        "",
        header,
        rule,
        f"| Vigente reproducido | {inc['reproduced']['parameters']} | {fmt(inc['reproduced']['summary'])} |",
        f"| v2: {final['label']} | {final['parameters']} | {fmt(final['summary'])} |",
        "",
        f"Regla de promoción frente al vigente: PR-AUC {verdict['pr_auc_wins']}/4, lift@10% {verdict['lift_wins']}/4, Brier no peor {'sí' if verdict['brier_not_worse'] else 'no'}. "
        f"**{'El v2 es mejor que el vigente.' if verdict['promoted'] else 'El v2 no supera al vigente.'}**",
        "",
        "| Fold | L2 | PR-AUC vigente | PR-AUC v2 | Lift@10% vigente | Lift@10% v2 | Brier vigente | Brier v2 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, (a, b) in enumerate(zip(inc["reproduced"]["folds"], final["folds"]), start=1):
        lines.append(f"| {index} | {b['l2']} | {a['pr_auc']:.4f} | {b['pr_auc']:.4f} | {a['lift_at_10_percent']:.3f} | {b['lift_at_10_percent']:.3f} | {a['brier_score']:.5f} | {b['brier_score']:.5f} |")
    lines += ["", "## 6. Hazard ratios del v2 por fold", "", f"Referencias: {result['references']}", "", "| Término | HR por fold | Mismo signo |", "|---|---|---|"]
    for row in result["coefficients"]:
        hrs = ", ".join("—" if v is None else f"{v:.2f}" for v in row["hazard_ratio_by_fold"])
        lines.append(f"| {row['term']} | {hrs} | {'sí' if row['same_sign_all_folds'] else 'no'} |")
    lines += ["", "## 7. Perfil de categorías (todas las fotos con etiqueta a seis meses)", "", "| Variable | Categoría | Personas/foto | Salidas 6m % |", "|---|---|---:|---:|"]
    for row in result["category_profile"]:
        rate = "—" if row["six_month_rate_percent"] is None else f"{row['six_month_rate_percent']:.2f}"
        lines.append(f"| {row['variable']} | {row['category']} | {row['people_per_snapshot']} | {rate} |")
    lines += ["", "## 8. Calibración por subgrupo del v2 (último fold)", "", "| Variable | Categoría | Personas/foto | Estimado % | Observado % | Razón |", "|---|---|---:|---:|---:|---:|"]
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
    published = json.loads(INCUMBENT_RESULTS.read_text(encoding="utf-8"))

    calendar = [d for d in hz.fetch_calendar() if d >= fs.MIN_SNAPSHOT]
    monthly, direct, totals = load_person_months(calendar)
    windows = fs.fold_windows(direct)
    references = modal_references(direct)
    runner = Runner(monthly, direct, windows, references)

    # 0. Vigente reproducido.
    incumbent_features = adj.CHOSEN + INCUMBENT_INTERACTIONS
    incumbent = runner.run(incumbent_features, "company_tenure_band", tag="vigente reproducido")
    same_exposures = int(direct["exposure_count"].sum()) == published["frame"]["six_month_exposures"] and int(direct["event_count"].sum()) == published["frame"]["six_month_events"]
    # Tolerancia 1% relativo: el colapso de celdas sólo cambia el orden de empates y el redondeo de la penalización.
    same_metrics = all(
        abs(incumbent["summary"][k] / published["final"]["summary"][k] - 1.0) < 0.01 for k in ["pr_auc", "lift_at_10_percent", "brier_score"]
    )

    # 1-3. Selección.
    tenure, tenure_rows = tenure_step(runner)
    start = runner.run(["level_grouped", tenure, "calendar_month"] + MANAGER_BLOCK, tenure)
    with_playbook, forward_trail = forward_step(runner, start)
    final, interaction_trail = interaction_step(runner, with_playbook)
    drops = drop_one(runner, final)
    verdict = adj.promotion(final, incumbent)

    coefficients, model_references = fs.coefficient_stability(final)
    calibration = fs.subgroup_calibration(final, [f for f in final["features"] if f != "calendar_month" and f not in INCUMBENT_INTERACTIONS])

    result = {
        "artifact": "engineering-playbook-priority-model",
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
            "trend": TREND,
            "penalty": f"L2 × {PENALTY_CELL_SCALE} (escala fija, independiente del grano de las celdas)",
            "recalibration_months": RECALIBRATION_MONTHS,
            "tenure_options": TENURE_OPTIONS,
            "tenure_rule": "entre los cortes a menos de 2% relativo del mejor en PR-AUC y lift@10%, se prefiere Julia, luego playbook, luego vigentes",
            "candidates": CANDIDATES,
            "excluded": {"qvoice": "excluido por decisión del usuario (modelo en desarrollo)"},
            "acceptance_rule": "gana >= 3 de 4 folds en PR-AUC y lift@10% sin peor Brier medio",
            "short_history_coding": "antes del inicio de la fuente la variable vale '(antes de la fuente)' en todas las personas",
            "interaction_references": references,
            "fold_starts": ro.FOLD_STARTS,
            "l2_grid": ro.L2_GRID,
            "audits": [str(p.relative_to(ROOT)) for p in AUDITS],
        },
        "incumbent": {
            "published_label": published["final"]["label"],
            "published": {"parameters": published["final"]["parameters"], "summary": published["final"]["summary"]},
            "reproduced": public(incumbent),
            "same_exposures": same_exposures,
            "same_metrics": same_metrics,
        },
        "tenure_step": tenure_rows,
        "tenure_choice": TENURE_OPTIONS[tenure],
        "forward_trail": forward_trail,
        "interaction_trail": interaction_trail,
        "drop_one": drops,
        "final": public(final),
        "final_vs_incumbent": verdict,
        "coefficients": coefficients,
        "references": model_references,
        "category_profile": category_profile(direct),
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
    result_path = output_dir / "playbook-model-results.json"
    report_path = output_dir / "playbook-model-report.md"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    manifest = {
        "artifact": result["artifact"],
        "created_at_utc": result["created_at_utc"],
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "authorization": result["authorization"],
        "queries": {"calendar": str(hz.CALENDAR_QUERY.relative_to(ROOT)), "person_month_frame": str(FRAME_QUERY.relative_to(ROOT))},
        "query_sha256": {"calendar": hz.sha256_file(hz.CALENDAR_QUERY), "person_month_frame": hz.sha256_file(FRAME_QUERY)},
        "audit_sha256": {str(p.relative_to(ROOT)): hz.sha256_file(p) for p in AUDITS},
        "incumbent_source": str(INCUMBENT_RESULTS.relative_to(ROOT)),
        "incumbent_source_sha256": hz.sha256_file(INCUMBENT_RESULTS),
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": hz.sha256_file(result_path),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": hz.sha256_file(report_path),
        "employee_level_rows_persisted": False,
        "aggregate_training_frame_persisted": False,
    }
    (output_dir / "playbook-model-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(build_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
