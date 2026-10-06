"""Genera el deck v5 de selección del modelo de attrition: población Engineering y modelo final.

Cambios frente a v4:

- Los 8 grupos pasan justo después del modelo (diapositiva 6).
- Validación consolidada: la medida, las 4 pruebas, la comparativa contra
  alternativas y el techo de machine learning quedan en una sola diapositiva.
- Bloques de señales y efectos de cada señal se unen en una diapositiva.
- Próximos pasos: Random survival forest pendiente, variables nuevas para la
  misma población, correcciones antes del piloto y decisiones.
- De 13 a 10 diapositivas.

Fuentes (sólo agregados, ninguna fila individual):

- ``output/analysis/engineering/20261001/model-comparison-rolling-v2-sin-manager/``
- ``output/analysis/engineering/20261001/feature-block-selection-v1/``
- ``output/analysis/engineering/20261001/hazard-adjustment-v2/``
- ``docs/research/attrition-literature/literature-matrix.md`` y ``search-log.md``

Las cifras se validan contra valores esperados; si una fuente cambia, el script
falla. Reutiliza estilos y componentes de los builders v2 y v3.

Uso:
    python -B tools/presentations/build_model_selection_deck_v5.py [--out RUTA]
    python -B tools/presentations/build_model_selection_deck_v5.py --draft-selection
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v2 = _load("deck_v2", HERE / "build_model_selection_deck_v2.py")
v3 = _load("deck_v3", HERE / "build_model_selection_deck_v3.py")

fmt, pct_change, month_label, e, heading, slide, effect_panel = (
    v2.fmt, v2.pct_change, v2.month_label, v2.e, v2.heading, v2.slide, v2.effect_panel,
)
MONTHS, TENURE_LABELS = v2.MONTHS, v2.TENURE_LABELS

ANALYSIS = ROOT / "output" / "analysis" / "engineering" / "20261001"
COMPARISON = ANALYSIS / "model-comparison-rolling-v2-sin-manager" / "comparison-results.json"
SELECTION = ANALYSIS / "feature-block-selection-v1" / "selection-results.json"
ADJUSTMENT = ANALYSIS / "hazard-adjustment-v2" / "adjustment-results.json"
LITERATURE = ROOT / "docs" / "research" / "attrition-literature"

THEMES = [
    ("Cómo medir el riesgo en el tiempo", ["P01", "P02", "P03", "P05", "P07"],
     "Seguir a cada persona mes a mes, aunque todavía no se haya ido", "Eligió calcular el riesgo mes a mes"),
    ("Estudios de rotación en empresas", ["P04", "P06", "P09", "P11"],
     "Las salidas llegan en olas y se miden con salidas reales", "Confirmaron que ese método funciona con datos de RH"),
    ("Modelos más complejos (machine learning)", ["P08", "P10", "P12", "P32", "P41", "P42"],
     "Comparados con modelos simples en las mismas condiciones", "Ganan poco: los usamos sólo como punto de comparación"),
    ("Qué explica que alguien se vaya", [
        "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20", "P21", "P22", "P23", "P24",
        "P25", "P26", "P27", "P28", "P29", "P30", "P31", "P33", "P39", "P40", "P43"],
     "Carrera, jefe y equipo, compromiso, arraigo", "De aquí salió la lista de datos a probar"),
    ("Uso responsable", ["P34", "P35", "P36", "P37", "P38"],
     "Privacidad de las personas y trato parejo", "Sólo resultados por grupo y revisar que sea justo con todos"),
]

# Las referencias por familia están en la sección 3.2 del plan de Engineering.
# La clave vincula cada familia probada con su error de estimación global.
# Las familias sin prueba no reciben resultados.
FAMILIES = [
    ("Riesgo mes a mes (hazard discreto)", "yes", "Elegido", "hazard"),
    ("Regresión logística a 6 meses", "yes", "Alternativa sencilla", "logistic"),
    ("Gradient boosting (LightGBM)", "yes", "Alternativa compleja", "lightgbm"),
    ("Promedio histórico", "yes", "No distingue grupos", "historical"),
    ("Random survival forest", "part", "Pendiente de prueba", None),
    ("Cox de riesgos proporcionales", "no", "Menos adecuado para datos mensuales", None),
    ("Riesgos competitivos y multiestado", "no", "Falta definir tipos de salida", None),
    ("Deep learning y texto", "no", "Complejidad; sin texto libre", None),
    ("Causal y uplift", "no", "Sin acciones de retención registradas", None),
    ("Ecuaciones estructurales y mediación", "no", "Explica relaciones", None),
]
FAMILY_MARKS = {"yes": ("✓", "Probada"), "part": ("◐", "Pendiente"), "no": ("✗", "Descartada")}

CRITERIA = [
    ("C1", "Aprovecha la historia mensual.", False),
    ("C2", "Estima bien la attrition total y por grupo.", False),
    ("C3", "Identifica los grupos de mayor riesgo.", False),
    ("C4", "Funciona al probarlo en otras fechas.", False),
    ("C5", "Es sencillo de entender.", False),
    ("C6", "Protege la privacidad y permite revisar el trato justo.", True),
    ("C7", "Funciona aun con datos incompletos.", False),
    ("C8", "Es fácil de actualizar.", False),
    ("C9", "Tiene respaldo en estudios de salidas reales.", False),
]

GROUP_LABELS = {
    "company_tenure_band ≠ 7+ years y team_exits_12m ≠ 0 y company_tenure_band ≠ <1 year":
        ("1 a 7 años", "con salidas en su equipo"),
    "company_tenure_band = 7+ years y level_grouped = 7 - Senior & Lead y team_exits_12m ≠ 0":
        ("7+ años · Senior & Lead", "con salidas en su equipo"),
    "company_tenure_band ≠ 7+ years y team_exits_12m = 0 y company_tenure_band ≠ <1 year":
        ("1 a 7 años", "sin salidas en su equipo"),
    "company_tenure_band ≠ 7+ years y team_exits_12m ≠ 0 y company_tenure_band = <1 year":
        ("Menos de 1 año", "con salidas en su equipo"),
    "company_tenure_band = 7+ years y level_grouped = 7 - Senior & Lead y team_exits_12m = 0":
        ("7+ años · Senior & Lead", "sin salidas en su equipo"),
    "company_tenure_band ≠ 7+ years y team_exits_12m = 0 y company_tenure_band = <1 year":
        ("Menos de 1 año", "sin salidas en su equipo"),
    "company_tenure_band = 7+ years y level_grouped ≠ 7 - Senior & Lead y direct_reports_band = 0":
        ("7+ años · otros niveles", "sin reportes directos"),
    "company_tenure_band = 7+ years y level_grouped ≠ 7 - Senior & Lead y direct_reports_band ≠ 0":
        ("7+ años · otros niveles", "con reportes directos"),
}

BLOCK_LABELS = {
    (): "Base: nivel, antigüedad y mes",
    ("manager_equipo",): "+ manager y equipo",
    ("carrera", "manager_equipo"): "+ carrera (promoción en 12 meses)",
    ("carrera", "geografia", "manager_equipo"): "+ geografía (región)",
    ("carrera", "compensacion", "geografia", "manager_equipo"): "+ compensación (bandas)",
}
DROP_LABELS = {
    "team_exits_12m": "Salidas del equipo",
    "manager_changes_12m": "Cambios de manager",
    "direct_reports_band": "Reportes directos",
}
CMP_MODELS = ["hazard", "hazard_interactions", "logistic", "lightgbm"]
CMP_NAMES = {
    "hazard": "Riesgo mes a mes (elegido)",
    "hazard_interactions": "Mes a mes + nivel × antigüedad",
    "logistic": "Regresión logística a 6 meses",
    "lightgbm": "Machine learning (LightGBM)",
}
CMP_SHORT = {"hazard": "Mes a mes", "hazard_interactions": "+ nivel × antig.", "logistic": "Logística 6m", "lightgbm": "LightGBM"}
SOURCE = "análisis de Engineering del 1 y 2-oct-2026 (output/analysis/engineering/20261001/)"


def _read(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["deliverable_classification"] == "presentation", path
    return data


def _check_privacy(privacy: dict) -> None:
    assert privacy["employee_level_rows_persisted"] is False
    for key in ("employee_ids_selected", "individual_scores_published"):
        assert privacy.get(key, False) is False, key


def load_literature() -> dict:
    matrix = (LITERATURE / "literature-matrix.md").read_text(encoding="utf-8")
    rows = [line.split("|") for line in matrix.splitlines() if re.match(r"^\| P\d\d \|", line)]
    ids = [r[1].strip() for r in rows]
    years = [int(re.match(r"\s*(\d{4})", r[3]).group(1)) for r in rows]
    status = [r[9].strip() for r in rows]
    assert len(ids) == 43 and status.count("Revisado") == 42 and status.count("Candidato") == 1
    themed = sorted(pid for _, pids, _, _ in THEMES for pid in pids)
    assert themed == sorted(ids), "Cada trabajo debe pertenecer a un solo tema"
    log = (LITERATURE / "search-log.md").read_text(encoding="utf-8")
    searches = sum(1 for line in log.splitlines() if re.match(r"^\| 20\d\d-", line))
    return {"count": len(ids), "reviewed": status.count("Revisado"), "years": (min(years), max(years)), "searches": searches}


def load_data() -> dict:
    cmp_, sel, adj = _read(COMPARISON), _read(SELECTION), _read(ADJUSTMENT)
    for source in (cmp_, sel, adj):
        _check_privacy(source["privacy"])
    # Comparación de familias con las señales base
    scope = cmp_["scope"]
    summary = scope["summary"]
    cmp_lift = {k: summary[k]["lift_at_10_percent"]["mean"] * 10 for k in CMP_MODELS}
    assert [fmt(cmp_lift[k]) for k in CMP_MODELS] == ["17.3", "17.5", "16.9", "16.5"], "Cambió la comparación"
    cmp_folds = {k: [v * 10 for v in summary[k]["lift_at_10_percent"]["by_fold"]] for k in CMP_MODELS}
    hazard_wins = {
        k: sum(h > o for h, o in zip(cmp_folds["hazard"], cmp_folds[k])) for k in ("logistic", "lightgbm")
    }
    assert hazard_wins == {"logistic": 4, "lightgbm": 3}

    # Precisión en la estimación global: error absoluto medio, en puntos
    # porcentuales. Se reconstruye el promedio predicho desde los agregados
    # por quintil y se reconcilian sus denominadores y salidas por periodo.
    # Los cuatro periodos pesan igual, como en las otras comparaciones.
    family_error_pp = {}
    for key in ("hazard", "logistic", "lightgbm", "historical"):
        errors = []
        for fold in scope["folds"]:
            metrics = fold["metrics"][key]
            bins = metrics["calibration"]
            assert all(b["published"] and b["exposures"] >= 30 and b["events"] >= 30 for b in bins)
            assert sum(b["exposures"] for b in bins) == metrics["exposures"]
            assert sum(b["events"] for b in bins) == metrics["events"]
            predicted = sum(b["exposures"] * b["mean_predicted_percent"] for b in bins) / metrics["exposures"]
            observed = 100 * metrics["events"] / metrics["exposures"]
            assert abs(observed - metrics["observed_rate_percent"]) <= 0.0001
            errors.append(abs(predicted - observed))
        assert len(errors) == 4
        family_error_pp[key] = sum(errors) / len(errors)
    assert [fmt(v) for v in family_error_pp.values()] == ["0.2", "0.4", "0.3", "0.2"], "Cambió el error de estimación"

    # Selección por bloques
    path = [
        (BLOCK_LABELS[tuple(sorted(step["blocks"]))], step["summary"]["lift_at_10_percent"] * 10, step["parameters"])
        for step in sel["forward_path"]
    ]
    assert [fmt(v) for _, v, _ in path] == ["17.1", "19.4", "19.6", "19.4", "19.3"]
    assert sel["parsimony"]["chosen_blocks"] == ["manager_equipo"]
    drops = [(DROP_LABELS[d["dropped"]], d["summary"]["lift_at_10_percent"] * 10) for d in sel["drop_one"]]

    # Modelo final
    final = adj["final"]
    assert final["trend"] == "none" and final["parameters"] == 53
    assert all(f["converged"] for f in final["folds"])
    fsum = final["summary"]
    assert fmt(fsum["lift_at_10_percent"] * 10) == "20.1"
    last = final["folds"][-1]
    calibration = last["calibration"]
    assert len(calibration) == 5 and all(b["published"] and b["events"] >= 30 for b in calibration)
    trend = {v["label"]: v["summary"]["calibration_ratio_by_fold"] for v in adj["trend_variants"]}
    ceiling = adj["ceiling"]["summary"]
    parsimony = {r["spec"]: r for r in adj["ceiling_check"]["rows"]}
    wider = adj["finalists"][-1]
    assert wider["parameters"] == 58

    hr = {c["term"]: c["hazard_ratio_by_fold"][-1] for c in adj["coefficients"]}
    refs = adj["references"]
    assert refs["company_tenure_band"] == "7+ years" and refs["manager_changes_12m"] == "0"
    assert refs["team_exits_12m"] == "0" and refs["direct_reports_band"] == "0"

    groups = adj["groups"]
    assert len(groups["groups"]) == 8 and set(GROUP_LABELS) == {g["rule"] for g in groups["groups"]}
    assert all(g["people"] >= 30 and g["last_fold_people_per_snapshot"] >= 30 for g in groups["groups"])
    assert all(g["last_fold_events"] >= 30 for g in groups["groups"])
    subgroups = {(s["variable"], s["category"]): s for s in adj["subgroup_calibration"]}

    fold_starts = adj["design"]["fold_starts"]
    return {
        "lit": load_literature(),
        "cmp_lift": cmp_lift,
        "family_error_pp": family_error_pp,
        "cmp_folds": cmp_folds,
        "cmp_fold_labels": [month_label(f["test_start"]) for f in scope["folds"]],
        "hazard_wins": hazard_wins,
        "inter_lift_wins": summary["wins_vs_hazard"]["hazard_interactions"]["lift10_folds_won_vs_hazard"],
        "path": path,
        "drops": drops,
        "frame": adj["frame"],
        "final": final,
        "lift": fsum["lift_at_10_percent"] * 10,
        "fold_lifts": [v * 10 for v in fsum["by_fold"]["lift_at_10_percent"]],
        "ratios": fsum["calibration_ratio_by_fold"],
        "linear_ratios": trend["linear, sin recal"],
        "last": last,
        "calibration": calibration,
        "fold_periods": [(month_label(s), month_label(_add_months(s, 5))) for s in fold_starts],
        "ceiling": ceiling,
        "parsimony": parsimony,
        "ceiling_best": adj["ceiling_check"]["best_pr_auc"],
        "wider": wider,
        "base_none": next(v for v in adj["trend_variants"] if v["label"] == "none, sin recal"),
        "hr": hr,
        "groups": groups,
        "subgroups": subgroups,
    }


def _add_months(date_text: str, months: int) -> str:
    year, month, day = (int(x) for x in date_text.split("-"))
    total = year * 12 + month - 1 + months
    return f"{total // 12}-{total % 12 + 1:02d}-{day:02d}"


NAV = [
    "Recomendación",
    "Agenda",
    "Cómo nos documentamos",
    "De 10 familias a una",
    "El modelo elegido",
    "Los 8 grupos",
    "Cómo lo validamos",
    "Qué señales aportan",
    "Estimado contra real",
    "Próximos pasos",
]

# Candidatas para la misma población, en el orden de bloques de la literatura.
# Puntajes del scorecard de datos (output/current/00-scorecard-43.xlsx): 11-12
# de 16 para las cinco primeras filas y 7 de 16 para QVoice.
NEXT_CANDIDATES = [
    ("Carrera", "Tiempo desde la última promoción y tiempo en el nivel", "Estancamiento: la literatura lo asocia con más salidas."),
    ("Carrera", "Promovido o contratado en el nivel, recontratación, experiencia previa",
     "Cómo entró la persona: hoy el modelo no lo sabe y es su punto débil con menos de 1 año."),
    ("Manager", "Salida del propio manager y capas hasta el CEO", "Completa el bloque que ya entró; capas sólo desde mar-2023."),
    ("Movilidad", "Transferencia en el último año", "Cambio de puesto o equipo dentro de la empresa."),
    ("Modalidad", "Remoto, híbrido o en oficina", "Sólo desde ago-2024: cabe en 2 de las 4 pruebas."),
    ("Encuesta", "QVoice: intención de quedarse", "La señal más fuerte en la literatura; antes hay que validar sus olas."),
]

CSS = v3.CSS + """
    .muted { color: var(--text-muted); }
    .hlabel small { font-size: 13px; font-weight: 400; }

    /* Portada */
    .cover-kpi { display: flex; flex-direction: column; gap: 6px; padding: 14px 18px; }
    .cover-kpi b { font-size: 34px; font-weight: 800; color: var(--accent); text-transform: none; letter-spacing: 0; line-height: 1.1; }
    .cover-kpi span { font-size: 16.5px; font-weight: 500; line-height: 1.35; }

    /* Agenda */
    .agenda { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; align-self: center; }
    .ag-item { display: flex; flex-direction: column; gap: 8px; padding: 20px 22px; }
    .ag-num { font-size: 40px; font-weight: 800; color: var(--accent); line-height: 1; }
    .ag-head { font-size: 21px; font-weight: 700; line-height: 1.25; }
    .ag-slides { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); }
    .ag-body { font-size: 16px; line-height: 1.45; }

    /* Literatura */
    .lit-grid { display: grid; grid-template-columns: 1fr 1.45fr; gap: 24px; }
    .funnel { display: flex; flex-direction: column; gap: 10px; }
    .fn-step { display: grid; grid-template-columns: 78px 1fr; gap: 14px; align-items: center; padding: 10px 14px; border-radius: 10px; background: var(--bg-surface); border: 1px solid var(--border-subtle); }
    .fn-step b { font-size: 34px; font-weight: 800; color: var(--accent); text-align: center; line-height: 1; }
    .fn-step.final { border: 2px solid var(--accent); background: var(--accent-soft); }
    .fn-step span { font-size: 15px; line-height: 1.35; }
    .fn-step span strong { display: block; font-size: 16.5px; }
    .fn-arrow { text-align: center; color: var(--accent); font-size: 18px; line-height: 1; margin: -4px 0; }
    .th-row { display: grid; grid-template-columns: 290px 135px 1fr; gap: 14px; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--border-subtle); }
    .th-label { font-size: 16.5px; font-weight: 700; line-height: 1.25; }
    .th-label small { display: block; font-size: 13.5px; font-weight: 400; color: var(--text-muted); line-height: 1.3; }
    .th-track { position: relative; height: 26px; }
    .th-fill { height: 100%; border-radius: 0 6px 6px 0; background: var(--accent); }
    .th-use { font-size: 14.5px; line-height: 1.3; }
    .th-n { position: absolute; top: 50%; transform: translateY(-50%); padding-left: 8px; font-size: 20px; font-weight: 800; }

    /* Familias y criterios */
    .fam-grid { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr); gap: 24px; }
    .fam-grid > .card { min-width: 0; justify-content: center; gap: 14px; padding: 18px; }
    .fam { width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 16px; line-height: 1.3; }
    .fam th, .fam td { padding: 6px 7px; border-bottom: 1px solid var(--border-subtle); text-align: left; vertical-align: middle; }
    .fam th { font-size: 13px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .05em; }
    .fam th:first-child { width: 35%; }
    .fam th:nth-child(2), .fam td:nth-child(2) { width: 11%; text-align: center; }
    .fam th:nth-child(3), .fam td:nth-child(3) { width: 18%; text-align: center; }
    .fam th small { display: block; font-size: 12px; font-weight: 500; text-transform: none; letter-spacing: 0; margin-top: 3px; }
    .fam td.precision-value { font-size: 21px; font-weight: 700; font-variant-numeric: tabular-nums; }
    .fam td.precision-empty { color: var(--text-muted); }
    .fam tr.chosen td { background: var(--accent-soft); font-weight: 700; }
    .fam .mark { justify-content: center; font-size: 22px; line-height: 1; }
    .crit { display: flex; flex-direction: column; gap: 16px; }
    .crit div { display: grid; grid-template-columns: 34px 1fr; gap: 10px; font-size: 19px; line-height: 1.35; align-items: baseline; }
    .crit b { color: var(--accent); }
    .crit div.gate { font-weight: 700; }
    .crit div.gate b { color: #b45309; }
    .fam-grid .eff-foot { font-size: 14px; line-height: 1.35; }
    body.theme-dark-royal .crit div.gate b, body.theme-dark-carbon .crit div.gate b { color: #fbbf24; }

    /* Modelo */
    .model-content { display: flex; flex-direction: column; gap: 20px; align-self: center; }
    .signals-card { width: 100%; padding: 20px 24px; gap: 16px; }
    .sig { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px 24px; }
    .sig div { min-width: 0; border-left: 3px solid var(--accent); padding: 4px 12px; font-size: 17px; line-height: 1.35; }
    .sig div b { display: block; font-size: 18px; margin-bottom: 4px; }
    .sig div.combo { border-left-color: color-mix(in oklab, var(--accent) 50%, var(--bg-surface)); }
    .model-progress { padding: 0 4px; font-size: 19px; line-height: 1.35; font-weight: 600; color: var(--text-main); }

    /* Grupos */
    .grp-grid { display: grid; grid-template-columns: 1.9fr 1fr; gap: 22px; }
    .grp-head, .grp-row { display: grid; grid-template-columns: 300px 1fr 150px 150px; gap: 12px; align-items: center; }
    .grp-head { font-size: 13px; color: var(--text-muted); font-weight: 700; }
    .grp-row { height: 52px; border-bottom: 1px solid var(--border-subtle); }
    .grp-label { font-size: 15.5px; font-weight: 700; line-height: 1.2; }
    .grp-label small { display: block; font-weight: 400; font-size: 14px; }
    .grp-track { position: relative; height: 26px; }
    .grp-fill { height: 100%; border-radius: 0 6px 6px 0; background: var(--ctx); }
    .grp-row.hi .grp-fill { background: var(--accent); }
    .grp-val { position: absolute; top: 50%; transform: translateY(-50%); padding-left: 8px; font-size: 17px; font-weight: 800; }
    .grp-people { font-size: 14.5px; line-height: 1.25; }
    .grp-test { font-size: 14px; line-height: 1.25; }
    .grp-test.over { color: #b45309; font-weight: 700; }
    body.theme-dark-royal .grp-test.over, body.theme-dark-carbon .grp-test.over { color: #fbbf24; }

    /* Próximos pasos */
    .stage-next { grid-template-rows: auto 1fr auto; }
    .next-grid { display: grid; grid-template-columns: 1fr 1.75fr 1fr; gap: 18px; min-height: 0; }
    .next-card { justify-content: flex-start; gap: 12px; padding: 18px 20px; }
    .next-card.key { border: 2px solid var(--accent); }
    .next-num { font-size: 13px; font-weight: 800; color: var(--accent); text-transform: uppercase; letter-spacing: .06em; }
    .next-head { font-size: 21px; font-weight: 700; line-height: 1.25; }
    .next-card .side-body { font-size: 15.5px; }
    .next-card .steps-list { gap: 12px; }
    .next-card .steps-list li { font-size: 15.5px; }
    .cands { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 16px; }
    .cand { display: grid; grid-template-columns: 92px 1fr; gap: 10px; align-items: start; border-left: 3px solid var(--accent); padding: 2px 0 2px 10px; }
    .cand-tag { font-size: 12.5px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; color: var(--text-muted); padding-top: 2px; }
    .cand b { display: block; font-size: 15.5px; line-height: 1.3; }
    .cand small { display: block; font-size: 13.5px; line-height: 1.35; margin-top: 2px; }
    .stage-next .decision { font-size: 16.5px; padding: 12px 16px; }
"""


def build_slides(d: dict) -> list[str]:
    slides = []
    lit, final, last = d["lit"], d["final"], d["last"]
    groups = d["groups"]
    obs_last, pred_last = last["observed_rate_percent"], last["mean_predicted_percent"]
    over_last = round((d["ratios"][-1] - 1) * 100)
    lgb_lift = d["ceiling"]["lift_at_10_percent"] * 10

    # 1. Portada
    by_risk = sorted(groups["groups"], key=lambda g: -g["predicted_6m_percent"])
    hi_obs, lo_obs = by_risk[0]["last_fold_observed_percent"], by_risk[-1]["last_fold_observed_percent"]
    first_test, last_test = d["fold_periods"][0][0], d["fold_periods"][-1][1]
    kpis = [
        (f"{fmt(pred_last)}% vs {fmt(obs_last)}%", "cuánta attrition estimó contra la que hubo en el último periodo"),
        (f"{fmt(hi_obs)}% vs {fmt(lo_obs)}%", "attrition real del grupo de mayor riesgo contra la del de menor riesgo"),
        (f"{len(groups['groups'])} grupos", "identificados con datos que RH ya tiene: antigüedad, salidas en el equipo, nivel y personas a cargo; cada uno con más de 300 personas"),
    ]
    kpi_html = "".join(f'<div class="cover-chip cover-kpi"><b>{e(n)}</b><span>{e(t)}</span></div>' for n, t in kpis)
    slides.append(slide(
        len(slides),
        f'<div class="cover" style="grid-row: 1 / -1;"><div class="cover-kicker">People Analytics · Engineering · salidas voluntarias a 6 meses · octubre 2026</div>'
        f'<h1 class="cover-title">Recomendamos un modelo que identifica los grupos de Engineering con más attrition, '
        f'y que acertó al probarlo en 4 periodos pasados que no conocía</h1>'
        f'<div class="cover-chips">{kpi_html}</div>'
        f'<div class="cover-note"><b>Cómo lo probamos:</b> le dimos la historia sólo hasta una fecha, estimó los 6 meses siguientes y lo comparamos con lo que pasó; '
        f'lo repetimos 4 veces, con periodos de {first_test} a {last_test}. Partimos de 43 trabajos de investigación y comparamos 4 tipos de modelo. '
        f'Antes de usarlo falta afinar el grupo más alto y revisar que sea justo con todos los grupos.</div></div>',
        cls="",
    ))

    # 2. Agenda
    agenda = [
        ("1", "Cómo nos documentamos", "Diapositivas 3–4", "43 trabajos, criterios de búsqueda y de 10 familias de modelos a una."),
        ("2", "El modelo elegido", "Diapositiva 5", "Cómo usa la historia mensual para estimar el riesgo a 6 meses."),
        ("3", "Qué grupos encuentra", "Diapositiva 6", "Los 8 grupos de Engineering, su riesgo a 6 meses y su tamaño."),
        ("4", "Cómo lo validamos", "Diapositivas 7–8", "4 periodos de prueba, alternativas y qué señales aportan."),
        ("5", "Qué tan bien estima", "Diapositiva 9", "Estimado contra real y lo que falta corregir."),
        ("6", "Próximos pasos", "Diapositiva 10", "Modelo pendiente, variables nuevas, piloto y decisiones."),
    ]
    ag_html = "".join(
        f'<article class="card ag-item"><div class="ag-num">{n}</div><div class="ag-head">{e(h)}</div>'
        f'<div class="ag-slides">{e(s)}</div><div class="ag-body">{e(b)}</div></article>'
        for n, h, s, b in agenda
    )
    slides.append(slide(
        len(slides),
        heading("De la literatura a un modelo listo para piloto, en seis partes",
                "Cada parte responde una pregunta de la decisión; las cifras vienen de los datos de Engineering, no de los papers")
        + f'<div class="agenda">{ag_html}</div><div class="src">Clasificación: presentación. Sólo resultados agregados por grupo.</div>',
    ))

    # 3. Esfuerzo de documentación
    first_year, last_year = lit["years"]
    funnel = [
        ("9", "familias de búsqueda", "Supervivencia, turnover, talento técnico, riesgos competitivos, ML, constructos de RH, causalidad, fairness y texto"),
        (str(lit["searches"]), "búsquedas registradas", "Crossref, OpenAlex, editoriales, JSTOR, arXiv, PubMed Central y repositorios; Scholar sólo para descubrir"),
        ("5", "criterios de inclusión", "Estudia turnover o retención, método longitudinal, censura o riesgo temporal, constructos de RH, o gobierno"),
        (str(lit["count"]), f"trabajos, de {first_year} a {last_year}", f"{lit['reviewed']} con ficha revisada y 1 sin texto accesible. Se excluyeron estudios sin método, duplicados y modelos sin validación"),
    ]
    fn_html = '<div class="fn-arrow">▼</div>'.join(
        f'<div class="fn-step{" final" if i == len(funnel) - 1 else ""}"><b>{e(n)}</b><span><strong>{e(h)}</strong>{e(b)}</span></div>'
        for i, (n, h, b) in enumerate(funnel)
    )
    th_max = max(len(p) for _, p, _, _ in THEMES) * 1.3
    th_html = "".join(
        f'<div class="th-row"><div class="th-label">{e(name)}<small>{e(what)}</small></div>'
        f'<div class="th-track"><div class="th-fill" style="width:{len(pids) / th_max * 100:.2f}%"></div>'
        f'<div class="th-n" style="left:{len(pids) / th_max * 100:.2f}%">{len(pids)}</div></div>'
        f'<div class="th-use">{e(use)}</div></div>'
        for name, pids, what, use in THEMES
    )
    slides.append(slide(
        len(slides),
        heading(
            f"Revisamos {lit['count']} trabajos de investigación: nos dijeron qué tipo de modelo usar y qué datos probar; los datos de Engineering decidieron la versión final",
            f"Búsqueda del 7-sep al 30-sep-2026 · meta de unos 40 trabajos fijada antes de buscar · prioridad a métodos reproducibles, datos longitudinales y salidas reales",
        )
        + f'<div class="lit-grid"><article class="card" style="justify-content:center;gap:8px;padding:18px 20px;"><div class="funnel">{fn_html}</div></article>'
        f'<article class="card" style="justify-content:center;gap:4px;padding:18px 22px;"><div class="side-head" style="margin-bottom:4px;">Trabajos por tema y qué decidió cada tema</div>'
        f'{th_html}<div class="note-box" style="margin-top:10px;">No copiamos ningún modelo ni sus datos: revisamos cada trabajo y lo usamos para aportar ideas. '
        f'Los modelos que probamos se construyeron y ajustaron con los datos de Qualcomm.</div></article></div>'
        f'<div class="src">Fuente: docs/research/attrition-literature/ (matriz de literatura, bitácora de búsquedas y criterios de inclusión). '
        f'«Revisado» puede ser texto completo o sólo abstract, según el acceso.</div>',
    ))

    # 4. De 10 familias a una
    fam_rows = ""
    for name, mark, verdict, key in FAMILIES:
        icon, label = FAMILY_MARKS[mark]
        cls = ' class="chosen"' if verdict == "Elegido" else ""
        error_cell = (
            f'<td class="precision-value" title="Error medio de estimación: {fmt(d["family_error_pp"][key])} puntos porcentuales">{fmt(d["family_error_pp"][key])}</td>'
            if key else '<td class="precision-empty" aria-label="Sin prueba" title="Sin prueba">—</td>'
        )
        fam_rows += (
            f'<tr{cls}><td>{e(name)}</td>'
            f'<td><span class="mark m-{mark}" role="img" aria-label="{e(label)}" title="{e(label)}">{icon}</span></td>'
            f'{error_cell}<td>{e(verdict)}</td></tr>'
        )
    crit_html = "".join(
        f'<div{" class=gate" if gate else ""}><b>{e(c)}</b><span>{e(text)}</span></div>'
        for c, text, gate in CRITERIA
    )
    slides.append(slide(
        len(slides),
        heading(
            "De 10 familias, probamos 4 y elegimos el riesgo mes a mes",
            "5 descartadas y 1 pendiente · criterios fijados el 30-sep-2026, antes de ver resultados · pruebas con datos de Engineering (diapositiva 7)",
        )
        + f'<div class="fam-grid"><article class="card">'
        f'<table class="fam" aria-label="Familias, error de estimación y decisión de evaluación" aria-describedby="family-error-note"><thead><tr>'
        f'<th scope="col">Familia</th><th scope="col">Estado</th><th scope="col">Error<small>Menor es mejor</small></th>'
        f'<th scope="col">Motivo</th></tr></thead><tbody>{fam_rows}</tbody></table>'
        f'<div class="eff-foot" id="family-error-note"><b>Menor error = mejor estimación.</b> Diferencia media entre attrition estimada y real, en puntos porcentuales.<br>'
        f'Engineering · 4 pruebas · modelos base · — sin prueba.</div></article>'
        f'<article class="card"><div class="side-head">Qué buscamos en el modelo</div>'
        f'<div class="crit">{crit_html}</div>'
        f'<div class="eff-foot">C6 obligatorio. Revisión de trato justo pendiente.</div></article></div>'
        f'<div class="src">Criterios: docs/plans/attrition-model-selection-20260930.md y attrition-model-engineering-selection-20261001.md, sección 3. '
        f'Error: comparación base de Engineering, 1-oct-2026 (output/analysis/engineering/20261001/model-comparison-rolling-v2-sin-manager/comparison-results.json).</div>',
    ))

    # 5. El modelo elegido
    frame = d["frame"]
    pipe = [
        ("1 · Datos", "Fotos mensuales de Engineering",
         f"{frame['person_months_read']:,} personas-mes, de {month_label(frame['first_snapshot'])} a {month_label(frame['last_snapshot'])}. "
         "Para cada persona y mes: sus señales y si salió de forma voluntaria antes de la foto siguiente.", None, False),
        ("2 · Modelo", "Una regresión, como la logística",
         "Cada señal suma un coeficiente y la fórmula convierte la suma en un riesgo mensual entre 0 y 1.",
         "h = 1 − exp(−exp(α + Σ βx))", True),
        ("3 · Riesgo mensual", "Cambia con el calendario",
         "El mismo grupo tiene un riesgo distinto en mayo que en octubre: el mes del año es una señal.", None, False),
        ("4 · Riesgo a 6 meses", "Se acumula mes a mes",
         "Se encadenan los 6 riesgos mensuales; la misma fórmula da el riesgo a 3 o 12 meses sin reentrenar.",
         "R₆ = 1 − (1−h₁)(1−h₂)…(1−h₆)", False),
    ]
    pipe_html = "".join(
        f'<div class="pipe-step{" key" if key else ""}"><div class="pipe-num">{e(n)}</div><div class="pipe-head">{e(h)}</div>'
        f'<div class="pipe-body">{e(b)}</div>{f"<div class=formula>{e(f)}</div>" if f else ""}</div>'
        for n, h, b, f, key in pipe
    )
    signals = [
        ("Nivel", "7 grupos, de Associate a VP, y «otros»", False),
        ("Antigüedad en la empresa", "menos de 1, 1 a 3, 3 a 7, 7+ años", False),
        ("Mes del año", "la temporada de salidas", False),
        ("Cambios de manager", "en los últimos 12 meses: 0, 1, 2+", False),
        ("Salidas del equipo", "renuncias en 12 meses en el equipo del manager actual: 0, 1, 2+", False),
        ("Reportes directos", "personas a cargo: 0, 1 a 5, 6+", False),
        ("Nivel × antigüedad", "la antigüedad pesa distinto en cada nivel", True),
        ("Antigüedad × cambios de manager", "cambiar de manager pesa distinto según la antigüedad", True),
    ]
    sig_html = "".join(
        f'<div{" class=combo" if combo else ""}><b>{e(h)}</b>{e(b)}</div>' for h, b, combo in signals
    )
    slides.append(slide(
        len(slides),
        heading(
            "El modelo: estima el riesgo de renunciar en cada mes con 6 señales y 2 combinaciones, y lo acumula a 6 meses",
            "Riesgo mes a mes, también llamado hazard discreto · especificación final del 2-oct-2026",
        )
        + f'<div class="model-content"><div class="pipe">{pipe_html}</div>'
        f'<article class="card signals-card"><div class="section-head">Las señales</div><div class="sig">{sig_html}</div></article>'
        f'<div class="model-progress">Seguimos evaluando e incorporando nuevas variables al modelo.</div></div>'
        f'<div class="src">Fuente: {SOURCE}, hazard-adjustment-v2. Sin segmento, job family ni atributos protegidos como señal.</div>',
    ))

    # 6. Los 8 grupos: siguen al modelo para mostrar qué produce
    rows_g = sorted(groups["groups"], key=lambda g: -g["predicted_6m_percent"])
    g_max = max(g["predicted_6m_percent"] for g in rows_g) * 1.5
    mean = groups["mean_predicted_6m_percent"]
    g_html = ""
    for g in rows_g:
        who, what = GROUP_LABELS[g["rule"]]
        hi = " hi" if g["predicted_6m_percent"] > mean * 1.4 else ""
        over = " over" if g["last_fold_predicted_percent"] - g["last_fold_observed_percent"] >= 1.0 else ""
        g_html += (
            f'<div class="grp-row{hi}"><div class="grp-label">{e(who)}<small>{e(what)}</small></div>'
            f'<div class="grp-track"><div class="grp-fill" style="width:{g["predicted_6m_percent"] / g_max * 100:.2f}%"></div>'
            f'<div class="grp-val" style="left:{g["predicted_6m_percent"] / g_max * 100:.2f}%">{fmt(g["predicted_6m_percent"])}%</div></div>'
            f'<div class="grp-people">{g["people"]:,} personas<br><span class="muted">{fmt(g["people_share_percent"])}% del total</span></div>'
            f'<div class="grp-test{over}">est. {fmt(g["last_fold_predicted_percent"])}% · real {fmt(g["last_fold_observed_percent"])}%</div></div>'
        )
    top = rows_g[0]
    top_who, top_what = GROUP_LABELS[top["rule"]]
    high = [g for g in rows_g if g["predicted_6m_percent"] > mean * 1.4]
    high_share = sum(g["people_share_percent"] for g in high)
    slides.append(slide(
        len(slides),
        heading(
            f"El modelo resume Engineering en 8 grupos: el de mayor riesgo, {top_who.lower()} de antigüedad {top_what}, tiene {fmt(top['predicted_6m_percent'])}% a 6 meses y reúne {fmt(top['people_share_percent'])}% de las personas",
            f"% que se estima saldrá en 6 meses · foto del {v3.day_label(groups['snapshot'])} · {groups['people']:,} personas · grupos de 300+ personas",
        )
        + f'<div class="grp-grid"><article class="card" style="justify-content:center;gap:0;padding:12px 22px;">'
        f'<div class="grp-head"><div>Grupo</div><div>Riesgo estimado a 6 meses</div><div>Tamaño</div><div>Último periodo de prueba</div></div>{g_html}</article>'
        f'<article class="card" style="justify-content:center;gap:18px;padding:22px;">'
        f'<div class="kpi"><b>{fmt(mean)}%</b><span>riesgo promedio a 6 meses en Engineering</span></div>'
        f'<div class="kpi"><b>{fmt(high_share)}%</b><span>de las personas está en los {len(high)} grupos con 40% o más de riesgo sobre el promedio</span></div>'
        f'<div class="side-body" style="font-size:15.5px;">Las reglas usan sólo antigüedad, salidas del equipo, nivel y reportes: RH puede ubicar cada grupo sin el modelo.</div>'
        f'<div class="note-box">En naranja, grupos donde el estimado superó al real por 1 punto o más (diapositiva 9).</div></article></div>'
        f'<div class="src">Grupos formados con un árbol de 3 niveles sobre el riesgo estimado; resume {round(100 * groups["variance_explained_r2"])}% de su variación. '
        f'Último periodo de prueba: 30+ salidas en cada grupo. Fuente: {SOURCE}, hazard-adjustment-v2.</div>',
    ))

    # 7. Cómo lo validamos: une la medida, las 4 pruebas y la comparación con alternativas
    scale_max = 25.0
    cmp_lift = d["cmp_lift"]
    val_rows = [
        ("Al azar", "sin modelo", 10.0, ""),
        ("Regresión logística a 6 meses", "señales base", cmp_lift["logistic"], ""),
        ("Machine learning (LightGBM)", "señales base", cmp_lift["lightgbm"], ""),
        ("Riesgo mes a mes", "señales base", cmp_lift["hazard"], " hl2"),
        ("Machine learning (LightGBM)", "las 10 señales candidatas", lgb_lift, ""),
        ("Modelo final: mes a mes", f"{final['parameters']} coeficientes legibles", d["lift"], " hl"),
    ]
    val_html = "".join(
        f'<div class="hrow{hl}"><div class="hlabel">{e(label)}<br><small class="muted">{e(note)}</small></div><div class="htrack">'
        f'<div class="hfill" style="width:{value / scale_max * 100:.2f}%"></div><div class="hval" style="left:{value / scale_max * 100:.2f}%">{fmt(value)}</div></div></div>'
        for label, note, value, hl in val_rows
    )
    fold_table = "".join(
        f'<tr><td>{a} a {b}</td><td class="win">{fmt(v)}</td><td>{round(100 * r)}%</td></tr>'
        for (a, b), v, r in zip(d["fold_periods"], d["fold_lifts"], d["ratios"])
    )
    wins = d["hazard_wins"]
    slides.append(slide(
        len(slides),
        heading(
            f"Lo probamos 4 veces con datos que no vio: el 10% de mayor riesgo concentró {fmt(d['lift'])} de cada 100 salidas, contra 10 al azar, "
            f"y empató al machine learning con todas las señales",
            "De cada 100 salidas voluntarias reales en 6 meses, cuántas estaban en el 10% de personas con mayor riesgo estimado · promedio de 4 periodos de prueba",
        )
        + f'<div class="s6-grid"><article class="card" style="justify-content:center;gap:14px;padding:20px 26px;">'
        f'<div class="hbars">{val_html}</div></article>'
        f'<article class="card" style="justify-content:center;gap:12px;padding:20px 22px;"><div class="side-head">El modelo final en cada prueba</div>'
        f'<table class="wins"><thead><tr><th>Periodo de prueba</th><th>De cada 100</th><th>Estimado / real</th></tr></thead><tbody>{fold_table}</tbody></table>'
        f'<div class="side-body" style="font-size:15.5px;">Cada prueba entrena sólo con fotos anteriores a su inicio. Con las mismas señales base, el mes a mes superó a la logística '
        f'en {wins["logistic"]} de 4 periodos y al machine learning en {wins["lightgbm"]}.</div>'
        f'<div class="note-box">No mide acertar persona por persona: aun en el 10% más alto la mayoría se queda.</div></article></div>'
        f'<div class="src">Señales base: nivel, antigüedad y mes. Estimado / real: 100% = estima exactamente las salidas reales. El promedio histórico no aparece porque da el mismo riesgo a todos. '
        f'Fuente: {SOURCE}, model-comparison-rolling-v2 y hazard-adjustment-v2.</div>',
    ))

    # 8. Qué señales aportan: bloques probados y efecto de las señales elegidas
    path_html = "".join(
        f'<div class="hrow{" hl" if i == 1 else ""}"><div class="hlabel">{e(label)}<br><small class="muted">{p} coeficientes</small></div><div class="htrack">'
        f'<div class="hfill" style="width:{value / scale_max * 100:.2f}%"></div><div class="hval" style="left:{value / scale_max * 100:.2f}%">{fmt(value)}</div></div></div>'
        for i, (label, value, p) in enumerate(d["path"])
    )
    with_block = d["path"][1][1]
    hr = d["hr"]
    effects = [
        (pct_change(hr["team_exits_12m=2+"]), "2 o más salidas en el equipo en 12 meses, frente a ninguna"),
        (pct_change(hr["team_exits_12m=1"]), "1 salida en el equipo"),
        (pct_change(hr["manager_changes_12m=2+"]), "2 o más cambios de manager con 7+ años de antigüedad, frente a ninguno"),
        (pct_change(hr["direct_reports_band=6+"]), "6 o más reportes directos, frente a ninguno"),
    ]
    eff_html = "".join(
        f'<div class="prec" style="border-top:none;padding-top:0;"><b>{e(v)}</b><span>{e(t)}</span></div>' for v, t in effects
    )
    slides.append(slide(
        len(slides),
        heading(
            f"De los 4 bloques de la literatura, sólo manager y equipo mejora el orden, de {fmt(d['path'][0][1])} a {fmt(with_block)}; "
            f"la señal más clara son las salidas recientes del equipo",
            "Izquierda: de cada 100 salidas, cuántas en el 10% de mayor riesgo al agregar bloques · derecha: cambio del riesgo mensual, con las demás señales iguales",
        )
        + f'<div class="s6-grid"><article class="card" style="justify-content:center;gap:14px;padding:22px 26px;">'
        f'<div class="hbars">{path_html}</div></article>'
        f'<article class="card" style="justify-content:center;gap:14px;padding:22px;"><div class="side-head">Cuánto cambia el riesgo mensual</div>'
        f'{eff_html}'
        f'<div class="eff-foot">Carrera, geografía y compensación suman menos de 2%: por la regla de elegir lo más simple, no entraron. '
        f'Son asociaciones, no causas.</div></article></div>'
        f'<div class="src">Bloques: carrera = promoción en 12 meses; geografía = región; compensación = bandas de comp ratio y grado, nunca valores exactos. '
        f'Efectos del modelo del último periodo de prueba; los signos se repiten en los 4. Fuente: {SOURCE}, feature-block-selection-v1 y hazard-adjustment-v2.</div>',
    ))

    # 9. Estimado contra real
    cal = d["calibration"]
    top_cal = max(max(b["observed_rate_percent"], b["mean_predicted_percent"]) for b in cal) * 1.18
    cal_pairs = "".join(
        f'<div class="cal-pair"><div class="cal-bar obs"><span>{fmt(b["observed_rate_percent"])}%</span><i style="height:{b["observed_rate_percent"] / top_cal * 100:.2f}%"></i></div>'
        f'<div class="cal-bar pred"><span>{fmt(b["mean_predicted_percent"])}%</span><i style="height:{b["mean_predicted_percent"] / top_cal * 100:.2f}%"></i></div></div>'
        for b in cal
    )
    cal_labels = "".join(f"<div>{t}</div>" for t in ["20% más bajo", "2º", "3º", "4º", "20% más alto"])
    fold_head = "".join(f"<th>{a}</th>" for a, _ in d["fold_periods"])
    lin = "".join(f"<td>{round(100 * r)}%</td>" for r in d["linear_ratios"])
    fin = "".join(f'<td class="win">{round(100 * r)}%</td>' for r in d["ratios"])
    sub = d["subgroups"]
    assoc = sub[("level_grouped", "8 - Assoc & Int/Eng")]
    vp = sub[("level_grouped", "1 - VP & Above")]
    top_bin = cal[-1]
    slides.append(slide(
        len(slides),
        heading(
            f"Quitar la tendencia de largo plazo corrigió el nivel: el modelo pasó de estimar {round(100 * min(d['linear_ratios']))}–{round(100 * max(d['linear_ratios']))}% "
            f"de las salidas reales a {round(100 * min(d['ratios']))}–{round(100 * max(d['ratios']))}%; queda una sobreestimación en el 20% más alto",
            f"% que sale en 6 meses por quintil de riesgo estimado · último periodo, desde {d['fold_periods'][-1][0]} · {last['exposures']:,} personas-mes, {last['events']:,} salidas",
        )
        + f'<div class="s8-grid"><article class="card" style="justify-content:center;gap:12px;padding:22px 26px;">'
        f'<div class="legend"><span>Real</span><span class="pred">Estimado por el modelo</span></div>'
        f'<div class="cal">{cal_pairs}</div><div class="cal-labels">{cal_labels}</div>'
        f'<div class="side-body" style="font-size:15.5px;">El riesgo real sube en cada quintil. Los 4 primeros quedan a 0.2 puntos o menos; '
        f'en el más alto estima {fmt(top_bin["mean_predicted_percent"])}% y salió {fmt(top_bin["observed_rate_percent"])}%.</div></article>'
        f'<article class="card" style="justify-content:center;gap:12px;padding:20px 22px;"><div class="side-head">Estimado como % de lo real, por periodo</div>'
        f'<table class="wins"><thead><tr><th>Versión</th>{fold_head}</tr></thead><tbody>'
        f'<tr><td>Con tendencia</td>{lin}</tr><tr><td>Sin tendencia (final)</td>{fin}</tr></tbody></table>'
        f'<ul class="gaps"><li>La tendencia aprendió la baja de 2022-24 y la siguió proyectando cuando la attrition volvió a subir.</li>'
        f'<li>Associate / Engineer: estima {round(100 * (assoc["ratio"] - 1))}% por encima de lo real.</li>'
        f'<li>VP o superior ({vp["people_per_snapshot"]} personas): estima {fmt(vp["predicted_percent"])}% y salió {fmt(vp["observed_percent"])}%; no se publica como grupo propio.</li></ul>'
        f'<div class="fix">Siguiente corrección: ajustar la pendiente del riesgo estimado con los meses recientes y medir de nuevo en los 4 periodos.</div></article></div>'
        f'<div class="src">Quintiles con 30+ salidas cada uno. 100% = estima exactamente lo real. Fuente: {SOURCE}, hazard-adjustment-v2.</div>',
    ))

    # 10. Próximos pasos: modelo pendiente, variables nuevas para la misma población y piloto
    cand_html = "".join(
        f'<div class="cand"><span class="cand-tag">{e(tag)}</span><div><b>{e(name)}</b><small>{e(why)}</small></div></div>'
        for tag, name, why in NEXT_CANDIDATES
    )
    before_pilot = [
        "Ajustar la pendiente del 20% más alto y de Associate.",
        "Auditar trato justo por grupo, en agregado.",
        "Calcular intervalos de confianza por grupo.",
        "Piloto en 1 o 2 grupos, con grupo de comparación.",
    ]
    before_html = "".join(f"<li>{e(x)}</li>" for x in before_pilot)
    decisions = [
        f"Aprobar el modelo mes a mes de {final['parameters']} coeficientes y los 8 grupos como base para Engineering.",
        "Priorizar las variables de carrera y probar en paralelo el Random survival forest.",
        "Definir si «Voluntary Exception» cuenta como salida y autorizar la validación de QVoice.",
    ]
    dec_html = "".join(f'<div class="decision">{e(x)}</div>' for x in decisions)
    slides.append(slide(
        len(slides),
        heading(
            "Próximos pasos: probar el modelo pendiente y nuevas variables de carrera, manager y encuesta en la misma población; después, el piloto",
            "Cada prueba usa las mismas 4 fechas y la misma regla: algo nuevo entra sólo si mejora más de 2% al modelo actual · Engineering, mismas fotos mensuales",
        )
        + f'<div class="next-grid">'
        f'<article class="card next-card"><div class="next-num">1 · Modelo pendiente</div><div class="next-head">Random survival forest</div>'
        f'<div class="side-body">La única familia que quedó a medias: faltaba instalar su librería (scikit-survival).</div>'
        f'<div class="side-body">Mismas señales, mismas 4 pruebas y misma medida que el resto.</div>'
        f'<div class="eff-foot">LightGBM, también no lineal, empató con {fmt(lgb_lift)} de cada 100 salidas: esperamos una confirmación más que un cambio de modelo.</div></article>'
        f'<article class="card next-card key"><div class="next-num">2 · Variables nuevas · recomendamos empezar aquí</div>'
        f'<div class="cands">{cand_html}</div>'
        f'<div class="eff-foot">Las 5 primeras tienen 11 o 12 de 16 puntos en el scorecard de datos; QVoice, 7 de 16.</div></article>'
        f'<article class="card next-card"><div class="next-num">3 · Antes del piloto</div><div class="next-head">Corregir y auditar</div>'
        f'<ul class="steps-list">{before_html}</ul></article></div>'
        f'<div style="display:flex;flex-direction:column;gap:10px;"><div class="section-head">Decisiones que necesitamos</div>'
        f'<div class="decisions">{dec_html}</div></div>',
        cls="stage-next",
    ))
    assert len(slides) == len(NAV), "La navegación debe tener una entrada por diapositiva."
    return slides


DRAFT_CSS = """
    .selection-draft .slide-title-text { font-size: 37px; max-width: 1180px; }
    .selection-draft .slide-subtitle { font-size: 19px; }
    .draft-kicker { color: var(--accent); font-size: 14px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 12px; }
    .draft-content { display: flex; flex-direction: column; justify-content: center; gap: 20px; min-height: 0; }
    .draft-card { padding: 14px 24px; gap: 10px; flex-shrink: 0; }
    .draft-table { border-collapse: collapse; table-layout: fixed; width: 100%; }
    .draft-table th, .draft-table td { border-bottom: 1px solid var(--border-subtle); padding: 10px 12px; text-align: center; vertical-align: middle; }
    .draft-table thead th { font-size: 18px; line-height: 1.25; font-weight: 700; }
    .draft-table th:first-child { width: 240px; text-align: left; }
    .draft-table tbody th { font-size: 20px; line-height: 1.25; font-weight: 600; }
    .draft-table tbody th small { display: block; font-size: 14px; font-weight: 400; margin-top: 5px; color: var(--text-muted); }
    .draft-table tbody tr:last-child > * { border-bottom: 0; }
    .draft-table .draft-choice > * { background: var(--accent-soft); }
    .draft-table .draft-choice th { border-left: 4px solid var(--accent); }
    .draft-table .draft-precision { color: var(--accent); }
    .draft-mark { font-size: 30px; font-weight: 700; line-height: 1; }
    .draft-legend { display: flex; justify-content: space-between; align-items: center; gap: 20px; font-size: 15px; color: var(--text-muted); }
    .draft-legend b { font-size: 18px; margin-right: 5px; }
    .draft-explanations { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px 30px; }
    .draft-explanation { border-left: 2px solid var(--border-subtle); padding-left: 14px; font-size: 17px; line-height: 1.35; }
    .draft-explanation:first-child { border-left-color: var(--accent); }
    .draft-explanation strong { display: block; font-size: 18px; margin-bottom: 5px; }
    .draft-explanation:first-child strong { color: var(--accent); }
    .draft-foot { font-size: 15px; line-height: 1.4; color: var(--text-muted); }
"""


def build_selection_draft() -> str:
    """Maqueta aislada: las marcas son ejemplos, sin leer ni evaluar datos."""
    criteria = [
        ("Precisión", "La attrition estimada se acerca a la real, en el total y en cada grupo."),
        ("Distingue el riesgo", "Los grupos de mayor riesgo concentran más salidas reales."),
        ("Aprovecha el tiempo", "Usa la historia mes a mes, incluso con seguimiento incompleto."),
        ("Funciona en otras fechas", "Sigue acertando al probarlo en distintos periodos."),
        ("Sencillo de entender", "Se entiende por qué un grupo tiene mayor o menor riesgo."),
        ("Fácil de mantener", "El equipo puede actualizarlo con los recursos disponibles."),
    ]
    # Sólo diseño: no interpretar estas marcas como resultados de los modelos.
    examples = [
        ("Riesgo mes a mes", "Ejemplo de fila elegida", [True, True, True, True, True, True]),
        ("Regresión logística", "A 6 meses", [True, True, False, True, True, True]),
        ("Machine learning", "LightGBM", [True, True, False, True, False, False]),
        ("Promedio histórico", "Referencia mínima", [False, False, False, False, True, True]),
    ]
    headers = "".join(
        f'<th scope="col" class="{"draft-precision" if i == 0 else ""}">{e(label)}</th>'
        for i, (label, _) in enumerate(criteria)
    )
    rows = []
    for i, (name, detail, marks) in enumerate(examples):
        cells = "".join(
            f'<td><span class="draft-mark m-{"yes" if value else "no"}" role="img" '
            f'aria-label="Ejemplo: {"cumple" if value else "no cumple"}">{"✓" if value else "✗"}</span></td>'
            for value in marks
        )
        rows.append(
            f'<tr class="{"draft-choice" if i == 0 else ""}"><th scope="row">{e(name)}'
            f'<small>{e(detail)}</small></th>{cells}</tr>'
        )
    definitions = "".join(
        f'<div class="draft-explanation"><strong>{e(label)}</strong>{e(text)}</div>'
        for label, text in criteria
    )
    return slide(
        0,
        '<div><div class="draft-kicker">Propuesta para la diapositiva 4 · borrador visual</div>'
        + heading(
            "Buscamos precisión y un modelo sencillo de entender",
            "Los modelos se comparan con los mismos criterios; la fila elegida queda resaltada.",
        )
        + '</div><div class="draft-content"><article class="card draft-card">'
        f'<table class="draft-table" aria-label="Comparación ilustrativa de modelos, sin resultados reales">'
        f'<thead><tr><th scope="col">Modelo</th>{headers}</tr></thead><tbody>{"".join(rows)}</tbody></table>'
        '<div class="draft-legend"><span><b class="m-yes">✓</b> Cumple &nbsp;&nbsp; '
        '<b class="m-no">✗</b> No cumple</span><span>Marcas ilustrativas · sin evaluación real</span></div>'
        f'</article><div class="draft-explanations">{definitions}</div></div>'
        '<div class="draft-foot">Borrador de diseño: las marcas no representan resultados reales. '
        'Privacidad y trato justo siguen siendo requisitos antes de usar cualquier modelo.</div>',
        cls="stage-3rows selection-draft",
    )


def render(*, draft_selection: bool = False) -> str:
    slides = [build_selection_draft()] if draft_selection else build_slides(load_data())
    navigation = ["Borrador de la diapositiva 4"] if draft_selection else NAV
    tpl = v2.TEMPLATE.read_text(encoding="utf-8")
    out = tpl.replace('<html lang="en">', '<html lang="es">', 1)
    out = out.replace("<title>[Slide Title]</title>", "<title>Modelo de attrition voluntaria de Engineering: qué elegimos y por qué (v5)</title>", 1)
    if draft_selection:
        out = out.replace(
            "<title>Modelo de attrition voluntaria de Engineering: qué elegimos y por qué (v5)</title>",
            "<title>Borrador visual de la diapositiva 4: criterios de elección</title>",
            1,
        )
    out = out.replace(
        '<meta charset="UTF-8" />',
        '<meta charset="UTF-8" />\n  <meta name="deliverable-classification" content="presentation" />',
        1,
    )
    marker = "/* 13. CONTENT-SPECIFIC STYLES — add below this line\n       ================================================================== */"
    assert marker in out, "La plantilla cambió: no se encontró CONTENT-SPECIFIC STYLES"
    out = out.replace(marker, marker + CSS + (DRAFT_CSS if draft_selection else ""), 1)

    body_start = out.index('<body class="theme-light-classic">') + len('<body class="theme-light-classic">')
    nav_start = out.index("  <!-- ================================================================\n       LEFT EDGE")
    out = out[:body_start] + "\n" + "\n".join(slides) + "\n\n" + out[nav_start:]

    pills = "\n".join(
        f'      <button class="nav-pill{" pill-active" if i == 0 else ""}" data-slide="{i}">{i + 1}. {e(t)}</button>'
        for i, t in enumerate(navigation)
    )
    out = re.sub(
        r'<div class="nav-tab">Slides</div>.*?</div>\n  </div>',
        lambda _: '<div class="nav-tab">Diapositivas</div>\n    <div class="nav-panel">\n'
        f'      <div class="nav-label">Navegación</div>\n{pills}\n    </div>\n  </div>',
        out,
        count=1,
        flags=re.DOTALL,
    )
    themes = ["Claro – Clásico", "Claro – Azul suave", "Oscuro – Real", "Oscuro – Carbón"]
    for old, new in zip(["Light – Classic", "Light – Soft Blue", "Dark – Royal", "Dark – Carbon"], themes):
        out = out.replace(f">{old}</button>", f">{e(new)}</button>", 1)
    out = out.replace('<div class="side-label">Theme</div>', '<div class="side-label">Tema</div>', 1)
    out = out.replace('<div class="side-tab">Theme</div>', '<div class="side-tab">Tema</div>', 1)
    # La plantilla conserva su índice de diapositiva dentro de un cierre.
    # Conectamos el menú a su navegación existente sin alterar los bloques base.
    out = out.replace("</body>", """  <script>
    (function () {
      var buttons = Array.from(document.querySelectorAll('#slide-nav [data-slide]'));
      buttons.forEach(function (button) {
        button.addEventListener('click', function () {
          var current = buttons.findIndex(function (item) { return item.classList.contains('pill-active'); });
          var target = Number(button.dataset.slide);
          var key = target > current ? 'ArrowRight' : 'ArrowLeft';
          for (var step = 0; step < Math.abs(target - current); step++) {
            document.dispatchEvent(new KeyboardEvent('keydown', { key: key }));
          }
        });
      });
    })();
  </script>
</body>""", 1)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--draft-selection", action="store_true", help="Genera sólo el borrador visual de la diapositiva 4, con marcas ilustrativas.")
    args = parser.parse_args()
    topic = "borrador-slide4-seleccion" if args.draft_selection else "seleccion-modelo-v5"
    out = args.out or (
        ROOT / "output" / "presentations" / f"{datetime.now():%Y%m%d-%H%M}_{topic}" / "presentacion.html"
    )
    if out.exists():
        raise SystemExit(f"Ya existe {out}; no se sobrescribe.")
    out.parent.mkdir(parents=True, exist_ok=True)
    html = render(draft_selection=args.draft_selection)
    out.write_bytes(v2.TEMPLATE.read_bytes())
    out.write_text(html, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
