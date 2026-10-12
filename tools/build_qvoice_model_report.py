"""Informe en español, gráficos y consolidado de assessments QVoice terminados."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from qvoice_model_data import ROOT, DEFAULT_CONFIG, load_config, sha256_file, utc_now, write_json

SHORT = {"intent": "Intent to Stay (Q4/Q12)", "career": "Career goals", "mean33": "Promedio de 33 preguntas",
         "engagement": "Engagement (Q1/Q2/Q3)", "connection": "Connection (Q5/Q7)",
         "wellbeing": "Wellbeing (Q8/Q10/Q11)", "confidence": "Confidence (Q13/Q17)", "heartbeat": "Heartbeat (6 signos)"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def number(value) -> str:
    if value is None:
        return "—"
    value = float(value)
    return f"{value:,.0f}" if value.is_integer() else f"{value:,.1f}".rstrip("0").rstrip(".")


def link(label: str, path: Path, root: Path) -> str:
    return f"[{label}](<{os.path.relpath(path, root).replace(os.sep, '/')}>)"


def collect(config: dict, root: Path) -> list[dict]:
    records = []
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    for candidate in config["candidates"]:
        pointer = read_json(root / "variables" / candidate["id"] / "assessment-reference.json")
        run = ROOT / pointer["path"]
        manifest = read_json(run / "manifest.json")
        if manifest["status"] != "validated" or sha256_file(run / "manifest.json") != pointer["manifest_sha256"]:
            raise ValueError(f"El assessment de {candidate['id']} no está validado o cambió.")
        evidence_root = ROOT / pointer["evidence_path"]
        evidence = read_json(evidence_root / "evidence.json")
        if evidence["execution_hashes"]["configuration"] != config_hash:
            raise ValueError("Un concepto se evaluó con otra configuración; no se mezclan ejecuciones.")
        profile = read_json(run / "profile.json")
        if len(profile["assessments"]) != 1:
            raise ValueError("Se esperaba un concepto por assessment secuencial.")
        records.append({"candidate": candidate, "run": run, "manifest": manifest, "profile": profile,
                        "evidence": evidence, "evidence_root": evidence_root,
                        "artifacts": manifest["artifacts"]["variable_folders"][0]})
    return records


def consolidate(records: list[dict], root: Path) -> Path:
    sys.path.insert(0, str(ROOT / ".codex/skills/evaluate-attrition-variable/scripts"))
    import render_assessment as renderer

    target = ROOT / "output/assessments" / f"{root.name}-consolidated"
    if target.exists():
        raise FileExistsError("El consolidado ya existe; use una nueva carpeta de experimento.")
    profile = copy.deepcopy(records[0]["profile"])
    profile["run_id"] = target.name
    profile["artifact_root"] = str(target.relative_to(ROOT))
    profile["assessments"] = [record["profile"]["assessments"][0] for record in records]
    profile["original_order"] = [a["variable"] for a in profile["assessments"]]
    profile["evaluation_order"] = profile["original_order"]
    profile["consolidation_note"] = "Consolidado de ocho assessments v4 ejecutados y revisados de forma secuencial; conserva sus evidencias y scores."
    write_json(target / "profile.json", profile)
    renderer.render(profile, ROOT / ".codex/skills/evaluate-attrition-variable/assets/variable-assessment-template.xlsx", target / "assessment.xlsx")
    renderer.validate_workbook(target / "assessment.xlsx", profile)
    write_json(target / "manifest.json", {"manifest_version": 4, "status": "validated_consolidation", "generated_at": utc_now(),
               "source_assessments": [{"path": str(r["run"].relative_to(ROOT)), "manifest_sha256": sha256_file(r["run"] / "manifest.json")} for r in records],
               "workbook_sha256": sha256_file(target / "assessment.xlsx"), "profile_sha256": sha256_file(target / "profile.json"),
               "reporting_mode": "presentation", "employee_level_rows_persisted": False,
               "sheets": ["Variable assessment", "Coverage", "Score rationale"]})
    return target


def charts(records: list[dict], root: Path) -> list[Path]:
    destination = root / "charts"
    destination.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.spines.left": False, "axes.labelcolor": "#334155",
                         "text.color": "#172B4D", "xtick.color": "#475569", "ytick.color": "#172B4D"})
    years, colors = (2024, 2025, 2026), ("#254B82", "#278C8A", "#B26729")
    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    y = np.arange(len(records))[::-1]
    for index, (year, color) in enumerate(zip(years, colors)):
        values = [next(w for w in r["evidence"]["waves"] if w["year"] == year)["scopes"]["Engineering"]["coverage_percent"] for r in records]
        ax.barh(y + (1 - index) * .22, values, height=.18, label=str(year), color=color)
        for position, value in zip(y + (1 - index) * .22, values):
            ax.text(value + .8, position, number(value), va="center", fontsize=8)
    ax.set_yticks(y, [SHORT[r["candidate"]["id"]] for r in records])
    ax.set_xlim(0, 105)
    ax.set_xticks(range(0, 101, 20), [f"{x}%" for x in range(0, 101, 20)])
    ax.set_xlabel("Personas con señal primaria / personas elegibles en el baseline")
    fig.legend(*ax.get_legend_handles_labels(), loc="upper right", bbox_to_anchor=(.98, .91), ncols=3, frameon=False)
    fig.suptitle("La cobertura descriptiva depende del conjunto de preguntas", x=.03, ha="left", fontsize=17, weight="bold")
    fig.text(.03, .91, "Engineering · empleados regulares activos · RF360 excluido · baselines anteriores a cada encuesta", fontsize=10)
    fig.text(.03, .035, "Señal primaria: al menos un componente válido. El promedio exige 33 respuestas válidas; Heartbeat exige\n53 ítems ordinales disponibles y al menos 38 respuestas válidas. Cero indica que la definición no puede calcularse.", fontsize=9)
    fig.subplots_adjust(left=.27, right=.98, top=.86, bottom=.15)
    coverage_path = destination / "cobertura-qvoice-engineering.png"
    fig.savefig(coverage_path, dpi=180, facecolor="white")
    plt.close(fig)

    by_id = {r["candidate"]["id"]: r for r in records}
    selections = [("intent", "Q4", "Q4 · Permanencia futura"), ("intent", "Q12", "Q12 · Búsqueda de empleo"),
                  ("intent", "intent_both", "Q4 y Q12 · Ambas favorables"), ("career", "career", "Career goals")]
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 6.2), sharex=True, sharey=True)
    maximum = 0
    for ax, year in zip(axes, (2024, 2025)):
        for offset, response, color in ((.16, "Favorable", "#254B82"), (-.16, "No favorable", "#B26729")):
            values = []
            for concept, feature, _ in selections:
                wave = next(w for w in by_id[concept]["evidence"]["waves"] if w["year"] == year)
                group = next(g for g in wave["scopes"]["Engineering"]["groups"] if g["feature"] == feature and g["response"] == response)
                if not group["rate_published"]:
                    raise ValueError("No se puede publicar una tasa suprimida en el gráfico.")
                values.append(group["attrition_percent"])
            maximum = max(maximum, *values)
            positions = np.arange(len(selections))[::-1] + offset
            ax.barh(positions, values, height=.26, color=color, label=response)
            for position, value in zip(positions, values):
                ax.text(value + .15, position, number(value) + "%", va="center", fontsize=10)
        ax.set_title(str(year), loc="left", fontsize=13, weight="bold")
        ax.set_xlabel("Salida voluntaria durante el año")
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: number(v) + "%"))
    axes[0].set_yticks(np.arange(len(selections))[::-1], [label for _, _, label in selections])
    axes[0].set_xlim(0, max(14, np.ceil(maximum * 1.16)))
    fig.legend(*axes[1].get_legend_handles_labels(), loc="upper right", bbox_to_anchor=(.97, .90), ncols=2, frameon=False)
    fig.suptitle("Las respuestas no favorables se asocian con mayor attrition anual", x=.025, ha="left", fontsize=17, weight="bold")
    fig.text(.025, .91, "Engineering · cohortes con respuesta válida y enlace al baseline · asociaciones descriptivas", fontsize=10)
    fig.text(.025, .035, "Tasa = salidas voluntarias / personas del grupo. Cada barra cumple al menos 30 personas y 30 eventos.\nLos conteos y ventanas se detallan en el informe. Las asociaciones no demuestran incremento predictivo ni causalidad.", fontsize=9)
    fig.subplots_adjust(left=.265, right=.97, top=.82, bottom=.18, wspace=.12)
    associations_path = destination / "asociaciones-anuales-intent-career.png"
    fig.savefig(associations_path, dpi=180, facecolor="white")
    plt.close(fig)
    return [coverage_path, associations_path]


def markdown(config: dict, root: Path, records: list[dict], comparison: dict, consolidated: Path) -> str:
    control = read_json(root / "control/control-reproduction.json")
    states = [v["decision"]["status"] for v in comparison["variants"]]
    heartbeat = next(record for record in records if record["candidate"]["id"] == "heartbeat")
    heartbeat_reconciliation = next(wave for wave in heartbeat["evidence"]["waves"] if wave["year"] == 2026)["historical_reconciliation"]
    heartbeat_checks = heartbeat_reconciliation["checks"]
    cutoff_differences = [row["events_retrospective"] - row["events_at_boundary"]
                          for row in heartbeat_reconciliation.get("cutoff_comparison", [])
                          if row["events_retrospective"] is not None and row["events_at_boundary"] is not None
                          and row["events_retrospective"] != row["events_at_boundary"]]
    heartbeat_note = f"Heartbeat: {sum(check['pass'] for check in heartbeat_checks)} de {len(heartbeat_checks)} comprobaciones coinciden al reproducir el filtro retrospectivo del playbook."
    if cutoff_differences:
        heartbeat_note += (f" Al limitar los registros de eventos a snapshots conocidos al corte, {len(cutoff_differences)} segmentos tienen "
                           f"entre {min(cutoff_differences)} y {max(cutoff_differences)} salidas menos. Las cifras principales conservan ese límite. "
                           "Los segmentos se solapan entre preguntas; esas diferencias no se suman como personas distintas.")
    lines = ["# QVoice en el modelo de Engineering", "", f"Ejecución iniciada el 6 de octubre de 2026. Informe generado el {utc_now()[:10]} (UTC). Clasificación: `presentation`.", "",
             "## Resultado", "", f"Se implementaron **{len(comparison['variants'])} configuraciones** y se completaron **{len(records)} assessments v4**. "
             f"El modelo B {'se reprodujo correctamente' if control['passed'] else 'requiere revisión'}. "
             f"Hay **{comparison['available_wave_count']} encuestas con fecha acreditada de disponibilidad de resultados**.", ""]
    if all(s == "evidencia temporal insuficiente" for s in states):
        lines += ["**El aporte predictivo de QVoice sigue pendiente.** Ninguna configuración tiene dos periodos principales evaluables. "
                  "Las tasas anuales permiten priorizar señales, pero no sustituyen una comparación con información disponible antes de cada predicción.", ""]
    lines += ["## Control B", "", "La reproducción mantuvo la población, las diez features, el hazard cloglog, las interacciones y el procedimiento histórico del 3 de octubre.", "",
              "| Comprobación | Resultado |", "|---|---:|"]
    for check in control["checks"][:4]:
        labels = {"person_months_read": "Registros persona-mes", "six_month_exposures": "Exposiciones con etiqueta a seis meses",
                  "six_month_events": "Exposiciones con salida", "parameters": "Parámetros"}
        lines.append(f"| {labels[check['check']]} | {number(check['observed'])} |")
    lines += ["", "| Métrica histórica media | Valor |", "|---|---:|",
              f"| PR-AUC × 100 | {number(np.mean([f['pr_auc'] for f in control['model']['folds']]) * 100)} |",
              f"| Lift del 10% superior | {number(np.mean([f['lift_at_10_percent'] for f in control['model']['folds']]))} |",
              f"| Brier × 1,000 | {number(np.mean([f['brier_score'] for f in control['model']['folds']]) * 1000)} |"]
    lines += ["", f"Los {len(control['checks'])} controles de reproducción {'cumplieron' if control['passed'] else 'se conservan para revisión'}. "
              "Las exposiciones con evento incluyen observaciones mensuales repetidas de una persona; no son un conteo de personas distintas.", "",
              link("Resultados completos del control", root / "control/control-reproduction.json", root), "",
              "## Señales y cobertura descriptiva", "", "La población corresponde a Engineering activo Regular, excluyendo RF360, en la foto previa a cada encuesta. "
              "Esta cobertura aún no acredita que la respuesta pudiera usarse en ese snapshot.", "",
              "![Cobertura descriptiva](charts/cobertura-qvoice-engineering.png)", "",
              "| Concepto | 2024 | 2025 | 2026 | Assessment |", "|---|---:|---:|---:|---|"]
    for record in records:
        values = [w["scopes"]["Engineering"]["coverage_percent"] for w in record["evidence"]["waves"]]
        lines.append(f"| {SHORT[record['candidate']['id']]} | " + " | ".join(number(v) + "%" for v in values) + " | " + link("Abrir HTML", ROOT / record["artifacts"]["html"], root) + " |")
    lines += ["", "Las familias usan al menos un componente primario válido. El promedio exige 33 respuestas válidas; Heartbeat aplica su regla ordinal completa. "
              "Los assessments detallan completitud, ausencia de pregunta, falta de respuesta, valor inválido y falta de enlace por separado.", "",
              "## Asociaciones anuales comprobadas", "", "![Asociaciones anuales](charts/asociaciones-anuales-intent-career.png)", "",
              "| Año | Señal | Respuesta | Personas | Salidas | Tasa |", "|---|---|---|---:|---:|---:|"]
    for record in records[:2]:
        for wave in record["evidence"]["waves"]:
            if wave["year"] >= 2026:
                continue
            for group in wave["scopes"]["Engineering"]["groups"]:
                if group["response"] in ("Favorable", "No favorable") and group["rate_published"]:
                    label = {"intent_both": "Q4 y Q12", "career": "Career goals"}.get(group["feature"], group["feature"])
                    lines.append(f"| {wave['year']} | {label} | {group['response']} | {number(group['people'])} | {number(group['events'])} | {number(group['attrition_percent'])}% |")
    lines += ["", "Ventanas: (1 de enero de 2024, 1 de enero de 2025] y (1 de enero de 2025, 1 de enero de 2026]. "
              "Baselines: 24 de diciembre de 2023 y 29 de diciembre de 2024. Se exige respuesta válida por componente; la alternativa Q4 y Q12 exige ambas válidas. "
              "El contraste anual puede incluir salidas anteriores a la publicación de resultados; por eso es descriptivo.", "",
              "## Conciliación con el playbook v11", "",
              "- Los conteos del Excel, la fórmula del promedio y sus seis bandas se contrastaron con sus JSON originales; los resultados detallados están en la evidencia por concepto.",
              "- La plantilla actual con el filtro original tiene 40,144 personas en el baseline de 2024 y 42,341 en el de 2025: una menos en cada año que en el JSON publicado. "
              "La consulta independiente confirma estos totales y cero duplicados. La causa del cambio individual no se puede establecer con los agregados históricos disponibles.",
              "- Las pequeñas diferencias de cohortes y tasas de Intent/Career quedan registradas; no se alteraron cifras para forzar una coincidencia.",
              "- " + heartbeat_note,
              "- El acumulado descriptivo de 2026 termina el 23 de agosto, la última foto conocida al corte del 7 de septiembre. Las referencias anuales de Intent/Career llegan al 27 de septiembre; esas tasas no tienen la misma ventana. La referencia de Heartbeat sí termina el 23 de agosto y sus 18 segmentos se concilian con esa misma ventana.", "",
              link("SQL de conciliación del baseline", ROOT / "queries/audits/qvoice_model_baseline_reconciliation_20261006.sql", root), "",
              "## Resultado por configuración", "", "| Configuración | Periodos principales completos | Conclusión |", "|---|---:|---|"]
    for variant in comparison["variants"]:
        lines.append(f"| `{variant['id']}` | {variant['decision']['complete_main_periods']} | {variant['decision']['status']} |")
    notes = list(dict.fromkeys(note for variant in comparison["variants"] for note in variant.get("eligibility_notes", [])))
    lines += ["", "### Brechas que condicionan las comparaciones", ""] + [f"- {note}" for note in notes]
    lines += ["- Las tres fechas de publicación siguen pendientes. El año del archivo, las fechas de respuesta y el lanzamiento no las sustituyen.", "",
              "### Procedimiento implementado", "",
              "- Periodos principales: febrero–julio de 2025 y agosto de 2025–enero de 2026. Sólo se admiten snapshots con seguimiento completo a seis meses.",
              "- Selección L2 mediante Brier mensual en los últimos tres intervalos terminados antes del inicio calendario del periodo. Todas las etiquetas de entrenamiento respetan ese corte.",
              "- Comparación con B y con indicadores de disponibilidad usando las mismas personas, snapshots y etiquetas. Los faltantes permanecen en la cohorte general.",
              "- Se evalúa también la cohorte con respuestas completas cuando cumple los mínimos de publicación.",
              "- Incertidumbre mediante 500 réplicas pareadas por persona, conservando juntas sus observaciones mensuales.",
              "- PR-AUC, lift del decil, Brier y calibración general y del quintil superior. La nueva comparación agrupa empates; la reproducción B conserva el método histórico para comprobar sus cifras.",
              "- Una nueva wave reemplaza a la anterior aunque falte la respuesta. Caducidad máxima de 12 meses y comprobación de continuidad del episodio laboral.", "",
              "## Entregables y siguiente paso", "",
              "1. Aportar evidencia de la fecha de disponibilidad de cada wave y registrar fecha, estado y referencia en la configuración.",
              "2. Confirmar la equivalencia de Career goals de 2024 y mantener separadas las versiones completas de Connection y Wellbeing.",
              "3. Ejecutar una nueva carpeta de experimento con las fechas verificadas. El pipeline conserva el bloqueo cuando falta historia comparable.", "",
              "- " + link("Excel consolidado de ocho conceptos", consolidated / "assessment.xlsx", root),
              "- " + link("Resultados de las 17 configuraciones", root / "comparison-results.json", root),
              "- " + link("Configuración ejecutable", DEFAULT_CONFIG, root),
              "- " + link("Guía de reproducción", ROOT / "docs/context/qvoice-model-experiment.md", root),
              "- " + link("Pruebas y verificaciones", root / "validation/test-results.json", root), "",
              "Todos los entregables contienen agregados. No se guardaron filas de empleados, identificadores, predicciones individuales ni texto libre. "
              "El procesamiento del modelo respeta la autorización de uso en memoria del 1 de octubre.", ""]
    return "\n".join(lines)


def build(config: dict, root: Path, config_path: Path) -> None:
    if (root / "comparison-report.md").exists():
        raise FileExistsError("El informe ya existe; no se sobrescriben entregables anteriores.")
    metadata = read_json(root / "preflight/source-metadata.json")
    for wave in metadata["waves"]:
        if sha256_file(ROOT / wave["file"]) != wave["sha256"]:
            raise ValueError("Una fuente cambió después de su extracción.")
    if sha256_file(ROOT / config["sources"]["dictionary"]) != metadata["dictionary_sha256"]:
        raise ValueError("El diccionario cambió después del preflight.")
    records = collect(config, root)
    comparison = read_json(root / "comparison-results.json")
    consolidated = consolidate(records, root)
    chart_paths = charts(records, root)
    (root / "comparison-report.md").write_text(markdown(config, root, records, comparison, consolidated), encoding="utf-8")
    shutil.copy2(config_path, root / "experiment-config.yaml")
    code = sorted((ROOT / "tools").glob("qvoice_model_*.py")) + [Path(__file__), ROOT / "tools/verify_qvoice_model_sql.py", ROOT / "tests/test_qvoice_model_experiment.py"]
    for path in code:
        target = root / "code" / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    dependencies = ["tools/critical_tech_discrete_hazard_model.py", "tools/engineering_playbook_priority_model.py", "tools/engineering_playbook_tenure_confirmation.py",
                    "tools/engineering_hazard_adjustment.py", "tools/engineering_feature_block_selection.py", "tools/build_qvoice_comment_evidence.py",
                    "tools/build_qvoice_comparable_favorable_evidence.py", "tools/qvoice_excel_assessment.py", "tools/presentations/render_variable_assessment_v2.py",
                    ".codex/skills/attrition-redshift-db/scripts/run_readonly_query.py", ".codex/skills/evaluate-attrition-variable/scripts/run_assessment.py",
                    ".codex/skills/evaluate-attrition-variable/scripts/profile_variable.py", ".codex/skills/evaluate-attrition-variable/scripts/portfolio_workflow.py",
                    ".codex/skills/evaluate-attrition-variable/scripts/render_assessment.py", ".codex/skills/evaluate-attrition-variable/references/scoring-rules.yaml"]
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    files = [root / "comparison-report.md", root / "comparison-results.json", root / "experiment-config.yaml", root / "control/control-reproduction.json", *chart_paths,
             consolidated / "assessment.xlsx", consolidated / "profile.json", consolidated / "manifest.json"]
    write_json(root / "manifest.json", {"manifest_version": 1, "created_at": utc_now(), "experiment": config["experiment_id"], "git_base_commit": git,
               "implementation_status": "implemented_and_validated", "predictive_status": "pending_verified_availability" if comparison["available_wave_count"] == 0 else "see_comparison_results",
               "reporting_mode": "presentation", "knowledge_boundary": config["knowledge_boundary"], "authorization": config["authorization"],
               "privacy": config["privacy"], "employee_level_rows_persisted": False, "individual_scores_published": False,
               "source_sha256": {w["file"]: w["sha256"] for w in metadata["waves"]}, "dictionary_sha256": metadata["dictionary_sha256"],
               "configuration_sha256": sha256_file(config_path), "code_sha256": {str(p.relative_to(ROOT)): sha256_file(p) for p in code},
               "dependency_sha256": {p: sha256_file(ROOT / p) for p in dependencies},
               "artifacts_sha256": {str(p.relative_to(ROOT)): sha256_file(p) for p in files},
               "variable_assessments": [{"candidate": r["candidate"]["id"], "path": str(r["run"].relative_to(ROOT)),
                                          "manifest_sha256": sha256_file(r["run"] / "manifest.json"), "evidence": str((r["evidence_root"] / "evidence.json").relative_to(ROOT)),
                                          "evidence_sha256": sha256_file(r["evidence_root"] / "evidence.json")} for r in records],
               "validation": {str(p.relative_to(ROOT)): sha256_file(p) for p in (root / "validation").glob("*.json")}})
    print(root / "comparison-report.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-root", type=Path, required=True)
    arguments = parser.parse_args()
    build(load_config(arguments.config), arguments.run_root.resolve(), arguments.config.resolve())
