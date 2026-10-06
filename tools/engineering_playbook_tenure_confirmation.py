"""Confirmación de cortes de antigüedad del playbook y variables de carrera (2026-10-03).

Responde a los comentarios de revisión de los slides 5 y 6 con dos pasos
declarados antes de correr (no se elige nada mirando resultados):

A. Modelo vigente con un solo cambio: la antigüedad pasa de los cortes
   heredados (<1, 1-3, 3-7, 7+) a los del playbook (<1, 1-2, 2-3, 3-5, 5-10,
   10+). Mismas variables, mismas dos interacciones (nivel × antigüedad y
   antigüedad × cambios de manager), mismo hazard sin tendencia ni
   recalibración. A se promueve si gana >= 3 de 4 folds en PR-AUC y lift@10%
   sin peor Brier medio frente al vigente.
B. Sobre el campeón después de A (A si se promovió; si no, el vigente), se
   agregan juntas tiempo desde la última promoción y recontratación. B se
   promueve con la misma regla frente a ese campeón.

Reutiliza el frame, la carga en memoria y la penalización de escala fija de
``engineering_playbook_priority_model`` (el vigente se reproduce con PR-AUC
0.0512 y lift@10% 2.014). No modifica scripts ni resultados anteriores.

Sólo se escriben agregados: métricas, coeficientes y grupos >= 30 personas
(observado sólo con >= 30 salidas).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import critical_tech_discrete_hazard_model as hz  # noqa: E402
import critical_tech_model_comparison_rolling as ro  # noqa: E402
import engineering_feature_block_selection as fs  # noqa: E402
import engineering_hazard_adjustment as adj  # noqa: E402
import engineering_playbook_priority_model as pm  # noqa: E402  (aplica la penalización de escala fija)

ROOT = hz.ROOT
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "engineering" / "20261003" / "playbook-tenure-confirmation-v1"
EXPLORATION = ROOT / "output" / "analysis" / "engineering" / "20261003" / "playbook-priority-v1" / "playbook-model-results.json"
INTERACTIONS = ["level_x_tenure", "tenure_x_manager_changes"]
CAREER = ["time_since_promotion_band", "rehire"]

_FIT_IRLS_FIXED_SCALE = hz.fit_irls


def fit_irls_or_unconverged(frame, link, l2, encoder=None, max_iter=150):
    """Coeficientes no finitos (p. ej. L2 = 0 con celdas sin salidas) = ajuste no convergido, no elegible."""
    try:
        return _FIT_IRLS_FIXED_SCALE(frame, link, l2, encoder, max_iter)
    except RuntimeError as error:
        if "no finitos" not in str(error):
            raise
        return hz.IRLSModel(link, l2, np.zeros(1), encoder, max_iter, False)


hz.fit_irls = fit_irls_or_unconverged


def features_for(tenure: str, extra: list[str] | None = None) -> list[str]:
    return ["level_grouped", tenure, "calendar_month"] + pm.MANAGER_BLOCK + (extra or []) + INTERACTIONS


def describe(spec: dict, name: str) -> dict:
    return pm.public(spec) | {"name": name}


def groups_for(spec: dict) -> dict:
    """Árbol de grupos sobre la última foto con el modelo ajustado en toda la historia."""
    monthly, direct = spec["frames"]
    l2 = spec["folds"][-1]["metrics"]["l2"]
    model = adj.fit_converged(monthly, spec["features"], l2, pm.TREND, pm.RECALIBRATION_MONTHS)
    tree_features = [f for f in spec["features"] if f != "calendar_month" and f not in INTERACTIONS]
    return fs.tree_groups(monthly, direct, spec, l2, model=model, tree_features=tree_features)


def interpret(spec: dict) -> dict:
    coefficients, references = fs.coefficient_stability(spec)
    keys = [f for f in spec["features"] if f != "calendar_month" and f not in INTERACTIONS]
    return {
        "coefficients": coefficients,
        "references": references,
        "groups": groups_for(spec),
        "subgroup_calibration": fs.subgroup_calibration(spec, keys),
    }


# ---------------------------------------------------------------- reporte


def rule_text(rule: dict) -> str:
    return (
        f"PR-AUC {rule['pr_auc_wins']}/4, lift@10% {rule['lift_wins']}/4, Brier no peor {'sí' if rule['brier_not_worse'] else 'no'} → "
        f"**{'promovido' if rule['promoted'] else 'no promovido'}**"
    )


def build_report(result: dict) -> str:
    header = "| Modelo | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado por fold |"
    rule = "|---|---:|---:|---:|---:|---:|---|"
    specs = result["specs"]
    lines = [
        "# Confirmación: cortes de antigüedad del playbook y variables de carrera — Engineering",
        "",
        f"Creado: {result['created_at_utc']}. Frontera de conocimiento: {result['knowledge_boundary']}.",
        f"{result['frame']['six_month_exposures']:,} exposiciones a seis meses y {result['frame']['six_month_events']:,} salidas; mismos 4 folds.",
        f"Entrenamiento en memoria bajo `{result['authorization']['path']}`; sin filas ni IDs persistidos.",
        "",
        "Reglas declaradas antes de correr:",
        "",
        f"- A: {result['design']['step_a']}",
        f"- B: {result['design']['step_b']}",
        "",
        "## Métricas",
        "",
        header,
        rule,
    ]
    for key in ["incumbent", "a", "b"]:
        s = specs[key]
        lines.append(f"| {s['name']} | {s['parameters']} | {pm.fmt(s['summary'])} |")
    lines += [
        "",
        "## Decisiones",
        "",
        f"- A frente al vigente: {rule_text(result['a_vs_incumbent'])}",
        f"- Campeón después de A: **{result['champion_after_a']}**.",
        f"- B frente al campeón después de A: {rule_text(result['b_vs_champion'])}",
        f"- B frente al vigente (informativo): {rule_text(result['b_vs_incumbent'])}",
        f"- **Modelo final: {result['final_name']}.**",
        "",
        "## Por fold",
        "",
        "| Fold | PR-AUC vigente | PR-AUC A | PR-AUC B | Lift@10% vigente | Lift@10% A | Lift@10% B | Brier vigente | Brier A | Brier B |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, (i, a, b) in enumerate(zip(specs["incumbent"]["folds"], specs["a"]["folds"], specs["b"]["folds"]), start=1):
        lines.append(
            f"| {index} | {i['pr_auc']:.4f} | {a['pr_auc']:.4f} | {b['pr_auc']:.4f} | {i['lift_at_10_percent']:.3f} | {a['lift_at_10_percent']:.3f} | "
            f"{b['lift_at_10_percent']:.3f} | {i['brier_score']:.5f} | {a['brier_score']:.5f} | {b['brier_score']:.5f} |"
        )
    lines += ["", "## Quitar una variable de carrera de B (informativo)", "", header, rule]
    for row in result["b_drop_one"]:
        lines.append(f"| sin {row['dropped']} | {row['parameters']} | {pm.fmt(row['summary'])} |")
    for key, title in [("a", "A"), ("final", "modelo final")]:
        if key == "final" and result["final_key"] == "a":
            continue
        if key == "final" and result["final_key"] == "incumbent":
            continue
        block = result["interpretation"][key]
        groups = block["groups"]
        lines += [
            "",
            f"## Grupos de {title} (árbol profundidad ≤ {groups['max_depth']}, hojas ≥ {groups['min_leaf_people']} personas), foto {groups['snapshot']}",
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
        lines += ["", f"### Hazard ratios de {title} por fold", "", f"Referencias: {block['references']}", "", "| Término | HR por fold | Mismo signo |", "|---|---|---|"]
        for row in block["coefficients"]:
            hrs = ", ".join("—" if v is None else f"{v:.2f}" for v in row["hazard_ratio_by_fold"])
            lines.append(f"| {row['term']} | {hrs} | {'sí' if row['same_sign_all_folds'] else 'no'} |")
        lines += ["", f"### Calibración por subgrupo de {title} (último fold)", "", "| Variable | Categoría | Personas/foto | Estimado % | Observado % | Razón |", "|---|---|---:|---:|---:|---:|"]
        for row in block["subgroup_calibration"]:
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
    published = json.loads(pm.INCUMBENT_RESULTS.read_text(encoding="utf-8"))

    calendar = [d for d in hz.fetch_calendar() if d >= fs.MIN_SNAPSHOT]
    monthly, direct, totals = pm.load_person_months(calendar)
    windows = fs.fold_windows(direct)
    references = pm.modal_references(direct)
    runner = pm.Runner(monthly, direct, windows, references)

    incumbent = runner.run(features_for("company_tenure_band"), "company_tenure_band", tag="vigente")
    if abs(incumbent["summary"]["lift_at_10_percent"] / published["final"]["summary"]["lift_at_10_percent"] - 1.0) >= 0.01:
        raise RuntimeError("El vigente no se reproduce (lift@10% a más de 1% relativo); la comparación no sería justa.")

    a = runner.run(features_for("tenure_playbook_band"), "tenure_playbook_band", tag="A: cortes del playbook")
    a_rule = adj.promotion(a, incumbent)
    champion, champion_key = (a, "a") if a_rule["promoted"] else (incumbent, "incumbent")
    tenure = champion["tenure"]
    b = runner.run(features_for(tenure, CAREER), tenure, tag="B: + promoción + recontratación")
    b_rule = adj.promotion(b, champion)
    final, final_key = (b, "b") if b_rule["promoted"] else (champion, champion_key)
    drops = []
    for feature in CAREER:
        spec = runner.run(features_for(tenure, [f for f in CAREER if f != feature]), tenure, tag=f"B sin {feature}")
        drops.append({"dropped": feature, "parameters": spec["parameters"], "summary": spec["summary"]})

    names = {
        "incumbent": "Vigente (cortes <1, 1-3, 3-7, 7+)",
        "a": "A: vigente con cortes del playbook",
        "b": f"B: {'A' if champion_key == 'a' else 'vigente'} + promoción + recontratación",
    }
    interpretation = {"a": interpret(a)}
    if final_key not in ("a", "incumbent"):
        interpretation["final"] = interpret(final)
    result = {
        "artifact": "engineering-playbook-tenure-confirmation",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": hz.KNOWLEDGE_BOUNDARY.strftime("%Y-%m-%d"),
        "deliverable_classification": "presentation",
        "authorization": {"path": str(fs.AUTHORIZATION.relative_to(ROOT)), "id": authorization["authorization_id"]},
        "frame": {
            "first_snapshot": str(monthly["snapshot_date"].min().date()),
            "last_snapshot": str(monthly["snapshot_date"].max().date()),
            "person_months_read": totals["person_months"],
            "six_month_exposures": int(direct["exposure_count"].sum()),
            "six_month_events": int(direct["event_count"].sum()),
        },
        "design": {
            "step_a": "vigente con cortes del playbook en lugar de los heredados; promovido si gana >= 3 de 4 folds en PR-AUC y lift@10% sin peor Brier medio frente al vigente",
            "step_b": "campeón después de A + tiempo desde la última promoción + recontratación (juntas); misma regla frente a ese campeón",
            "origin_of_b": f"combinación observada en la exploración {EXPLORATION.relative_to(ROOT)}; aquí se confirma con regla declarada",
            "trend": pm.TREND,
            "recalibration_months": pm.RECALIBRATION_MONTHS,
            "penalty": f"L2 × {pm.PENALTY_CELL_SCALE} (escala fija, independiente del grano de las celdas)",
            "non_finite_fits": "un ajuste con coeficientes no finitos cuenta como no convergido y no es elegible en la rejilla L2",
            "interaction_references": references,
            "fold_starts": ro.FOLD_STARTS,
            "l2_grid": ro.L2_GRID,
        },
        "specs": {"incumbent": describe(incumbent, names["incumbent"]), "a": describe(a, names["a"]), "b": describe(b, names["b"])},
        "a_vs_incumbent": a_rule,
        "champion_after_a": names[champion_key],
        "b_vs_champion": b_rule,
        "b_vs_incumbent": adj.promotion(b, incumbent),
        "final_key": final_key,
        "final_name": names[final_key],
        "b_drop_one": drops,
        "interpretation": interpretation,
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
    result_path = output_dir / "confirmation-results.json"
    report_path = output_dir / "confirmation-report.md"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    manifest = {
        "artifact": result["artifact"],
        "created_at_utc": result["created_at_utc"],
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "authorization": result["authorization"],
        "queries": {"calendar": str(hz.CALENDAR_QUERY.relative_to(ROOT)), "person_month_frame": str(pm.FRAME_QUERY.relative_to(ROOT))},
        "query_sha256": {"calendar": hz.sha256_file(hz.CALENDAR_QUERY), "person_month_frame": hz.sha256_file(pm.FRAME_QUERY)},
        "incumbent_source": str(pm.INCUMBENT_RESULTS.relative_to(ROOT)),
        "incumbent_source_sha256": hz.sha256_file(pm.INCUMBENT_RESULTS),
        "exploration_source": str(EXPLORATION.relative_to(ROOT)),
        "exploration_source_sha256": hz.sha256_file(EXPLORATION),
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": hz.sha256_file(result_path),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": hz.sha256_file(report_path),
        "employee_level_rows_persisted": False,
        "aggregate_training_frame_persisted": False,
    }
    (output_dir / "confirmation-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(build_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
