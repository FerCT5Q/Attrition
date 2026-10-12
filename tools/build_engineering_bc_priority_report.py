"""Informe agregado en español para la comparación de prioridades B/C."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
import numpy as np

from engineering_model_c import ROOT, read, write, sha

OUT = ROOT / "output/analysis/engineering/20261008/bc-priority-comparison-v1"
LABELS = {
    "level_grouped": "Nivel", "tenure_playbook_band": "Antigüedad", "manager_changes_12m": "Cambios de manager en 12 meses",
    "team_exits_12m": "Salidas del equipo en 12 meses", "direct_reports_band": "Reportes directos",
    "time_since_promotion_band": "Tiempo desde promoción", "rehire": "Recontratación registrada",
    "prior_experience_band": "Experiencia previa", "time_at_level_band": "Tiempo en nivel",
    "manager_left_6m": "Salida del manager en 6 meses", "ios_12m": "Movimiento IOS en 12 meses",
    "layers_band": "Capa organizativa almacenada", "work_arrangement_group": "Modalidad de trabajo",
    "region": "Región", "comp_ratio_band": "Banda de comp ratio almacenado", "grade_family": "Prefijo del grado",
    "acquisition_recorded": "Adquisición registrada", "transfer_12m": "Transferencia en 12 meses"}


def fmt(value):
    if value is None:
        return "—"
    if 0 < abs(value) < .05:
        return "<0.1" if value > 0 else "−<0.1"
    return f"{value:.1f}".rstrip("0").rstrip(".")


def mean_at(folds, key, name, section, metric):
    vals = [f["scenarios"][key][name][section].get(metric) for f in folds]
    return float(np.mean(vals)) if all(v is not None for v in vals) else None


def rule_text(rule):
    conditions = []
    for part in rule["conditions"]:
        f, v = part["condition"].split("=", 1)
        v = v.replace(" years", " años").replace(" year", " año").replace("|", " / ")
        conditions.append(f"{LABELS.get(f, f)} {'=' if part['present'] else '≠'} {v}")
    return "; ".join(conditions)


def plot(results):
    summary = results["summary"]
    capacities = np.array([int(k) for k in summary])
    colors = {"B": "#707780", "C": "#1769ab"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    for name in ["B", "C"]:
        values = [summary[str(k)][name]["capture_percent"] for k in capacities]
        axes[0].plot(capacities, values, "o-", color=colors[name], label=name, lw=2)
    axes[0].plot(capacities, capacities, "--", color="#bcbcbc", label="Selección aleatoria")
    axes[0].set_ylim(0, 75)
    axes[0].set_title("Captura de salidas a igual capacidad", loc="left", fontweight="bold")
    axes[0].set_ylabel("% de salidas en ventanas de 6 meses")
    axes[0].legend(frameon=False, ncol=3, loc="upper left")
    differences = np.array([summary[str(k)]["capture_interval"]["difference_C_minus_B_pp"] for k in capacities])
    intervals = np.array([summary[str(k)]["capture_interval"]["ci95_pp"] for k in capacities])
    # Dibujar intervalos directamente: el percentil bootstrap no tiene que contener el estimador puntual.
    axes[1].vlines(capacities, intervals[:, 0], intervals[:, 1], color=colors["C"], lw=2)
    axes[1].scatter(capacities, differences, color=colors["C"], zorder=3)
    axes[1].axhline(0, color="#777", lw=1)
    for x, value in zip(capacities, differences):
        axes[1].annotate(fmt(value), (x, value), xytext=(8, 0), textcoords="offset points", va="center")
    axes[1].set_title("Ventaja de C en captura e IC95", loc="left", fontweight="bold")
    axes[1].set_ylabel("C − B, puntos porcentuales; positivo favorece C")
    axes[1].set_xlim(18, 43)
    axes[1].yaxis.set_major_locator(MultipleLocator(.5))
    for ax in axes:
        ax.set_xticks(capacities, [f"{k}%" for k in capacities])
        ax.set_xlabel("Proporción de personas que se atendería por snapshot")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: fmt(v)))
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.15)
        ax.set_axisbelow(True)
    fig.suptitle("C aporta una ganancia pequeña al priorizar al 30%", fontweight="bold")
    fig.supxlabel("Engineering, activos regulares sin RF360 · snapshots feb-2024 a ene-2026\n"
                  "Fuente: engineering_model_c_person_month_20261008.sql · ejecución 8-oct-2026\n"
                  "Hoja del límite ponderada; captura esperada, no salidas evitadas. Ventanas solapadas.", fontsize=8)
    fig.savefig(OUT / "captura-por-capacidad.png", dpi=160)
    fig.savefig(OUT / "captura-por-capacidad.svg")
    plt.close(fig)


def main():
    r = read(OUT / "results.json")
    cfg = read(OUT / "frozen-config.json")
    folds, summary = r["folds"], r["summary"]
    key = str(int(round(cfg["primary_capacity_fraction"] * 100)))
    central = summary[key]
    preferred = central["C_preferred_under_rule"]
    favorable_balance = central["C"]["capture_percent"] > central["B"]["capture_percent"] and central["C"]["group_mae_pp"] < central["B"]["group_mae_pp"]
    conclusion = "C mejora ligeramente la captura y la estimación de los grupos prioritarios al 30%" if favorable_balance else "La comparación de grupos prioritarios al 30% ofrece resultados mixtos"
    rule_conclusion = "C cumple todas las condiciones de la regla conservadora" if preferred else "C no cumple todas las condiciones de la regla conservadora"
    plot(r)
    lines = ["# B frente a C: utilidad para priorizar grupos", "", f"**{conclusion}.**", "",
             "Modo de entrega: `presentation`. Ejecución: 8 de octubre de 2026.", "",
             "## Qué se comparó", "",
             "Misma población Engineering, Employee, Regular, activa y sin RF360; salida voluntaria en los seis meses siguientes a cada snapshot. "
             "Se evaluaron 24 snapshots, de febrero de 2024 a enero de 2026, agrupados en cuatro periodos. "
             "El seguimiento de la última foto termina en julio de 2026. Se da el mismo peso a cada periodo.", "",
             "Se priorizan hojas de los árboles por el riesgo predicho en entrenamiento, sin usar las salidas del periodo evaluado. "
             "Las capacidades de 20%, 30% y 40% son escenarios; el 30% se fijó como central antes del cálculo. "
             "Representan alta prioridad y su ampliación; no son etiquetas absolutas de riesgo ni una capacidad operativa confirmada.", "",
             "**Para igualar capacidad se pondera la hoja que cruza el límite.** Todos sus integrantes reciben la misma probabilidad de selección. "
             "La captura es el valor esperado si se atiende aleatoriamente a una parte de esa hoja; más abajo se presentan alternativas con hojas completas. "
             "No se publican ni seleccionan personas concretas.", "",
             "## Resultado principal", "", "![Captura y diferencia entre modelos](captura-por-capacidad.png)", "",
             "| Capacidad | Captura B | Captura C | Diferencia C − B (pp) | IC95 (pp) | Periodos: C / B / empate | Error por grupo B (pp) | Error por grupo C (pp) |",
             "|---|---:|---:|---:|---|---|---:|---:|"]
    for cap, s in summary.items():
        interval = s["capture_interval"]
        lo, hi = interval["ci95_pp"]
        lines.append(f"| {cap}% | {fmt(s['B']['capture_percent'])}% | {fmt(s['C']['capture_percent'])}% | {fmt(interval['difference_C_minus_B_pp'])} | [{fmt(lo)}, {fmt(hi)}] | {s['capture_wins_C']} / {s['capture_wins_B']} / {s['capture_ties']} | {fmt(s['B']['group_mae_pp'])} | {fmt(s['C']['group_mae_pp'])} |")
    lines += ["", "Captura = salidas en las ventanas de la selección / salidas en todas las ventanas elegibles. "
              "Una persona y una salida pueden contribuir a varias ventanas solapadas. El bootstrap agrupa todas las ventanas de la misma persona. "
              "Error por grupo = promedio ponderado del error absoluto de cada hoja seleccionada; evita que se compensen errores entre hojas. "
              "Las cifras se redondean; diferencias e intervalos se calculan antes de redondear.", "",
              f"## Escenario central: atender {key}%", "",
              "| Métrica | B | C |", "|---|---:|---:|"]
    labels = [("Personas atendidas medias por foto (esperadas)", "mean_people_per_snapshot", ""),
              ("Attrition observado a 6 meses", "observed_percent", "%"),
              ("Attrition estimado a 6 meses", "predicted_percent", "%"),
              ("Lift frente a toda la población", "lift", "×"),
              ("Error del total seleccionado (pp)", "aggregate_error_pp", ""),
              ("Error medio por grupo seleccionado (pp)", "group_mae_pp", ""),
              ("Error medio por grupo y snapshot (pp)", "group_snapshot_mae_pp", ""),
              ("Promedio del peor error de grupo publicable por periodo (pp)", "worst_publishable_group_error_pp", ""),
              ("Personas seleccionadas con tasas de grupo publicables", "publishable_group_exposure_percent", "%")]
    for label, metric, suffix in labels:
        lines.append(f"| {label} | {fmt(central['B'][metric])}{suffix} | {fmt(central['C'][metric])}{suffix} |")
    lines += ["", "El error por grupo y snapshot tampoco permite compensar subestimaciones de un mes con sobreestimaciones de otro. "
              "El peor error sólo se publica para hojas que cumplen los mínimos; no se interpreta como máximo de todas las hojas si hay supresión.", "",
              f"C mejora el error medio por grupo prioritario en {central['selected_group_error_wins_C']} de 4 periodos. "
              f"En captura gana en {central['capture_wins_C']}, pierde en {central['capture_wins_B']} y empata en {central['capture_ties']}. "
              "La ventaja media al 30% es pequeña. El error del peor grupo publicable y la estabilidad al reajustar siguen favoreciendo B en este escenario.", "",
              "### Comportamiento temporal", "",
              "| Snapshots | Captura B | Captura C | Error por grupo B (pp) | Error por grupo C (pp) |", "|---|---:|---:|---:|---:|"]
    for fold in folds:
        b, c = [fold["scenarios"][key][name]["metrics"] for name in ["B", "C"]]
        lines.append(f"| {fold['first_snapshot']} a {fold['last_snapshot']} | {fmt(b['capture_percent'])}% | {fmt(c['capture_percent'])}% | {fmt(b['group_mae_pp'])} | {fmt(c['group_mae_pp'])} |")
    lines += ["", "### Estimación sobre las mismas personas y reglas", "",
              "| Grupos y selección definidos por | Error por grupo con estimador B (pp) | Error por grupo con estimador C (pp) |", "|---|---:|---:|"]
    for owner in ["B", "C"]:
        values = {}
        for estimator in ["B", "C"]:
            section = "metrics" if estimator == owner else "same_selection_other_estimator"
            values[estimator] = mean_at(folds, key, owner, section, "group_mae_pp")
        lines.append(f"| {owner} | {fmt(values['B'])} | {fmt(values['C'])} |")
    lines += ["", "Esta comparación mantiene fijas las personas y las hojas. Permite separar la selección de grupos de la estimación de su attrition.", "",
              "### Ampliar desde el 20% prioritario", "",
              "| Ampliación | Captura adicional B | Captura adicional C | Attrition del tramo añadido B | Attrition del tramo añadido C |", "|---|---:|---:|---:|---:|"]
    for cap in summary:
        if cap == "20":
            continue
        captures = [mean_at(folds, cap, name, "increment_above_20_percent", "capture_percent") for name in ["B", "C"]]
        rates = [mean_at(folds, cap, name, "increment_above_20_percent", "observed_percent") for name in ["B", "C"]]
        lines.append(f"| 20% → {cap}% | {fmt(captures[0])}% | {fmt(captures[1])}% | {fmt(rates[0])}% | {fmt(rates[1])}% |")
    lines += ["", "Captura adicional usa como denominador todas las salidas del periodo. Attrition del tramo añadido usa sólo la población adicional esperada.", "",
              "## Claridad y estabilidad de los grupos", "",
              "Los dos modelos usan árboles de hasta 8 hojas y hasta 3 condiciones por hoja, aprendidos antes de la evaluación. "
              "C conserva variables originales. El árbol resume el modelo y puede perder parte de su señal.", "",
              "| Capacidad | Coincidencia al reajustar B | Coincidencia al reajustar C | Captura con ranking individual B | Captura con ranking individual C |", "|---|---:|---:|---:|---:|"]
    for cap, s in summary.items():
        lines.append(f"| {cap}% | {fmt(s['stability_overlap_percent']['B'])}% | {fmt(s['stability_overlap_percent']['C'])}% | {fmt(s['individual_diagnostic']['B'])}% | {fmt(s['individual_diagnostic']['C'])}% |")
    lines += ["", "Coincidencia: suma del mínimo de las dos asignaciones ponderadas / capacidad, aplicando las reglas anteriores y nuevas a la misma foto. "
              "Es el solapamiento de asignaciones esperadas, no la retención real de personas de un programa. Se promedian los tres cambios de periodo. "
              "El ranking individual es sólo un diagnóstico agregado; no se publican puntuaciones ni listas individuales.", "",
              "## Opciones con grupos completos", "",
              "| Periodo | Modelo | Cobertura media excluyendo hoja del límite | Cobertura media incluyendo hoja del límite |", "|---|---|---:|---:|"]
    for fold in folds:
        for name in ["B", "C"]:
            brackets = fold["scenarios"][key][name]["whole_group_brackets"]
            lower = np.mean([b["lower_whole_group_coverage_percent"] for b in brackets])
            upper = np.mean([b["upper_whole_group_coverage_percent"] for b in brackets])
            lines.append(f"| {fold['origin']} | {name} | {fmt(lower)}% | {fmt(upper)}% |")
    lines += ["", "Estas alternativas explican el costo de conservar grupos completos. Sus capacidades pueden diferir entre B y C; "
              "no se presentan como comparación a igual cantidad de personas. Los límites por snapshot están en results.json.", "",
              "## Grupos prioritarios del último periodo", "",
              "Snapshots agosto de 2025 a enero de 2026; grupos ordenados por riesgo de entrenamiento. "
              "Personas = media de personas que se atendería por foto, ponderando la hoja del límite al 30%. "
              "Las tasas observadas requieren 30 personas efectivas por foto seleccionada y 30 personas distintas con salida.", "",
              "| Modelo / grupo | Regla | Personas medias esperadas | Observado R6 | Estimado R6 | Error (pp) |", "|---|---|---:|---:|---:|---:|"]
    last = folds[-1]
    for name in ["B", "C"]:
        group_rows = {g["node"]: g for g in last["scenarios"][key][name]["selected_groups"]}
        rules = sorted(last["group_definitions"][name]["rules"], key=lambda g: -g["training_mean_risk"])
        for rule in rules:
            row = group_rows.get(int(rule["node"]))
            if row is None:
                continue
            values = [fmt(row.get(field)) for field in ["mean_people_per_snapshot", "observed_percent", "predicted_percent", "error_pp"]]
            lines.append(f"| {name} / G{rule['node']} | {rule_text(rule)} | {values[0]} | {values[1]}% | {values[2]}% | {values[3]} |".replace("—%", "—"))
    extension = r["extension"]
    lines += ["", "## Foto adicional: febrero de 2026", "",
              f"Snapshot {extension['snapshot']}; seguimiento hasta {extension['followup_end']}; {extension['people']} personas. "
              "Usa los modelos y las reglas del corte de agosto de 2025, sin reajuste. Es una foto adicional fuera de los cuatro periodos originales; "
              "no equivale a seis snapshots ni constituye un holdout virgen. Se mantiene aparte del promedio principal.", "",
              "| Capacidad | Captura B | Captura C | Error por grupo B (pp) | Error por grupo C (pp) |", "|---|---:|---:|---:|---:|"]
    for cap, scenario in extension["scenarios"].items():
        b, c = scenario["B"]["metrics"], scenario["C"]["metrics"]
        lines.append(f"| {cap}% | {fmt(b['capture_percent'])}% | {fmt(c['capture_percent'])}% | {fmt(b['group_mae_pp'])} | {fmt(c['group_mae_pp'])} |")
    lines += ["", "## Criterio fijado antes de calcular", "",
              "La prioridad es capturar salidas dentro de la capacidad disponible, con estimaciones fiables por grupo. "
              "Se conservó la exigencia temporal de al menos 3 de 4 periodos y la tolerancia de 0.1 pp del experimento anterior; "
              "el error global deja de ser la puerta principal. El criterio es exploratorio, posterior a haber visto los resultados anteriores.", "",
              "| Comprobación al 30% | Cumple C |", "|---|---|" ]
    labels = {"capture_gain": "Mayor captura media", "temporal_capture": "Mayor captura en al menos 3 de 4 periodos",
              "capture_interval": "IC95 de ventaja de captura completamente positivo",
              "selected_group_error": "Error por grupo prioritario no empeora más de 0.1 pp",
              "group_snapshot_error": "Error por grupo-snapshot no empeora más de 0.1 pp"}
    for field, value in central["C_preference_checks"].items():
        lines.append(f"| {labels[field]} | {'Sí' if value else 'No'} |")
    lines += ["", f"**Resultado formal: {rule_conclusion}.**", "",
              "La condición pendiente al 30% es ganar en al menos tres periodos: C obtiene dos victorias y dos empates en captura. "
              "La diferencia media de captura tiene un IC95 positivo y C reduce el error medio de los grupos prioritarios. "
              "Por ello, el balance práctico favorece ligeramente a C para este escenario, aunque no supera la regla conservadora completa. "
              "Se conserva esa regla y su resultado, sin modificar los umbrales después de ver los datos.", "",
              "El criterio no sustituye una evaluación de costos y beneficios de la acción. "
              "Los grupos de bajo riesgo siguen en el entrenamiento y se reportan como seguimiento en results.json; su precisión tiene un papel secundario en esta decisión.", "",
              "## Límites y reproducción", "",
              "- Se reutilizan cuatro C congelados y se reconstruye B cuatro veces con las especificaciones ya elegidas. No se repite la selección de variables.",
              "- Población, métricas B/C y ranking de sus grupos reproducen la ejecución original dentro de la tolerancia de cálculo. La evidencia está en analysis-checks.json.",
              "- Los IC95 de captura provienen de 500 réplicas de personas; mantienen fijos modelos, reglas y asignaciones. No incluyen incertidumbre de selección, cambios macrotemporales o efecto de una intervención.",
              "- La evaluación es retrospectiva y usa años ya explorados. La política por capacidad se formuló después de conocer las métricas anteriores. No es confirmación prospectiva independiente.",
              "- La comparación usa definiciones y fechas de conocimiento del experimento C: snapshots fiscales de duración desigual, otras salidas tratadas como no voluntarias, limitaciones de historia de IOS/transferencias y de campos almacenados.",
              "- Capturar una salida no demuestra que una acción pueda evitarla; las asociaciones no identifican causas.",
              "- El modelo C archivado sigue siendo el evaluado con corte agosto de 2025. No es un modelo actualizado a septiembre de 2026; C + QVoice no se ha iniciado.", "",
              f"Tiempo de cálculo: {fmt(r['elapsed_seconds'] / 60)} minutos, incluida carga de datos ({fmt(r['load_seconds'] / 60)} minutos).", "",
              "## Fuentes", "",
              f"- Consulta: `{r['query']}`. Frontera de conocimiento: `{r['knowledge_boundary']}`.",
              "- [Resultados agregados](results.json), [configuración previa](frozen-config.json), [comprobaciones del cálculo](analysis-checks.json), [manifiesto](manifest.json).",
              "- Experimento de origen: `../model-c-v2/`; autorización de RAM: `config/attrition_model_in_memory_training_authorization_20261001.json`.",
              "- No se persistieron filas, llaves efímeras, puntuaciones individuales, salarios exactos ni texto libre."]
    (OUT / "informe.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    source_target = OUT / "source-finalization" / Path(__file__).name
    source_target.parent.mkdir(parents=True, exist_ok=True)
    source_target.write_bytes(Path(__file__).read_bytes())
    manifest = read(OUT / "manifest.json")
    manifest["files"] = {str(p.relative_to(OUT)): sha(p) for p in OUT.rglob("*") if p.is_file() and p.name != "manifest.json"}
    manifest["report_builder"] = {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))}
    write(OUT / "manifest.json", manifest)
    print(json.dumps({"report": str(OUT / "informe.md"), "conclusion": conclusion}, ensure_ascii=True))


if __name__ == "__main__":
    main()
