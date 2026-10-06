"""Genera el deck v8 de selección del modelo de attrition: modelo B y grupos de mayor riesgo.

Cambios frente a v7 (comentarios de revisión de las diapositivas 5 y 6):

- El modelo elegido pasa a ser B: el vigente con los cortes de antigüedad del
  playbook (<1, 1-2, 2-3, 3-5, 5-10, 10+) más tiempo desde la última
  promoción y recontratación. Ganó al vigente en las 4 pruebas con reglas
  declaradas antes de correr.
- Portada, diapositivas 5, 7 y 8 usan las cifras de B.
- Diapositiva 6: en lugar del árbol de 8 grupos (que juntaba «1 a 7 años»),
  el top 5 de 22 grupos de antigüedad × salidas en el equipo × nivel. La
  agrupación se eligió entre 58 candidatas (56 combinaciones fijas y 2
  árboles) por cuánto conserva la capacidad del modelo para concentrar las
  salidas reales, fuera de muestra.
- Diapositiva 7 (comentarios de revisión): sin lift ni comparación de
  modelos. Una sola gráfica: de cada 100 personas, cuántas se fueron en 6
  meses, real contra estimado, por quintos de riesgo estimado juntando las 4
  pruebas, con título en el eje.
- Diapositiva 8 (comentarios de revisión): sólo 4 pasos de las siguientes 2 semanas en bullets, sin
  detalle ni la sección de decisiones.
- Diapositivas 3 y 4 sin cambios: la comparación de familias de modelos se
  hizo con las señales base.

Fuentes (sólo agregados, ninguna fila individual):

- ``output/analysis/engineering/20261001/model-comparison-rolling-v2-sin-manager/``
- ``output/analysis/engineering/20261001/hazard-adjustment-v2/`` (modelo anterior y techo LightGBM)
- ``output/analysis/engineering/20261003/playbook-tenure-confirmation-v1/``
- ``output/analysis/engineering/20261003/playbook-group-selection-v1/``
- ``docs/research/attrition-literature/literature-matrix.md`` y ``search-log.md``

Las cifras se validan contra valores esperados; si una fuente cambia, el script
falla. Reutiliza estilos y componentes de los builders v2 y v3.

Uso:
    python -B tools/presentations/build_model_selection_deck_v8.py [--out RUTA]
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
CONFIRMATION = ROOT / "output" / "analysis" / "engineering" / "20261003" / "playbook-tenure-confirmation-v1" / "confirmation-results.json"
GROUP_SELECTION = ROOT / "output" / "analysis" / "engineering" / "20261003" / "playbook-group-selection-v1" / "group-selection-results.json"
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
     "Carrera, jefe y equipo, compromiso, arraigo", "Agrupó las variables de la lluvia de ideas y del playbook en bloques y dio el orden para probarlos"),
    ("Uso responsable", ["P34", "P35", "P36", "P37", "P38"],
     "Privacidad de las personas y trato parejo", "Sólo resultados por grupo y revisar que sea justo con todos"),
]

# Las referencias por familia están en la sección 3.2 del plan de Engineering.
# La clave vincula cada familia probada con su error de estimación global.
# Las familias sin prueba no reciben resultados.
FAMILIES = [
    ("Riesgo mes a mes (hazard discreto)", "yes", "Usa cada mes (C1), menor desviación (C2) y mejor orden del riesgo (C3)", "hazard"),
    ("Regresión logística a 6 meses", "yes", "Descarta meses recientes (C1, C7); más desviación (C2)", "logistic"),
    ("Gradient boosting (LightGBM)", "yes", "Difícil de explicar (C5); más desviación (C2)", "lightgbm"),
    ("Promedio histórico", "yes", "No distingue grupos de riesgo (C3)", "historical"),
    ("Random survival forest", "part", "Pendiente de prueba", None),
    ("Cox de riesgos proporcionales", "no", "Menos adecuado para datos mensuales (C1)", None),
    ("Riesgos competitivos y multiestado", "no", "Falta definir tipos de salida", None),
    ("Deep learning y texto", "no", "Difícil de explicar (C5); sin texto libre (C6)", None),
    ("Causal y uplift", "no", "Sin acciones de retención registradas", None),
    ("Ecuaciones estructurales y mediación", "no", "Explica relaciones, no estima riesgo (C3)", None),
]
FAMILY_MARKS = {"yes": ("✓", "Probada"), "part": ("◐", "Pendiente"), "no": ("✗", "Descartada")}

CRITERIA = [
    ("C1", "Aprovecha la historia mensual.", False),
    ("C2", "Estima bien la attrition total y por grupo.", False),
    ("C3", "Identifica los grupos de mayor riesgo.", False),
    ("C4", "Funciona al probarlo en otras fechas.", False),
    ("C5", "Es sencillo de entender.", False),
    ("C6", "Protege la privacidad y permite revisar el trato justo.", False),
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
# Texto visible: sin rutas ni nombres de archivo; las rutas están en el docstring.
SOURCE = "análisis de Engineering del 1 al 3-oct-2026"


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
    family_dev_pct = {}
    hazard_per_100 = []
    for key in ("hazard", "logistic", "lightgbm", "historical"):
        errors, devs = [], []
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
            # Desviación relativa: si lo real es 100, cuánto se alejó lo estimado.
            devs.append(100 * abs(predicted - observed) / observed)
            if key == "hazard":
                hazard_per_100.append(100 * predicted / observed)
        assert len(errors) == len(scope["folds"]) == 4
        family_error_pp[key] = sum(errors) / len(errors)
        family_dev_pct[key] = sum(devs) / len(devs)
    assert [fmt(v) for v in family_error_pp.values()] == ["0.2", "0.4", "0.3", "0.2"], "Cambió el error de estimación"
    assert [fmt(v) for v in family_dev_pct.values()] == ["6.1", "14.5", "10.2", "7.1"], "Cambió la desviación relativa"
    assert [round(v) for v in hazard_per_100] == [98, 94, 91, 93], "Cambió el estimado por cada 100 salidas"

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
    assert len(groups["groups"]) == 8 and set(GROUP_LABELS) == set(GROUP_TREE) == {g["rule"] for g in groups["groups"]}
    assert all(g["people"] >= 30 and g["last_fold_people_per_snapshot"] >= 30 for g in groups["groups"])
    assert all(g["last_fold_events"] >= 30 for g in groups["groups"])
    subgroups = {(s["variable"], s["category"]): s for s in adj["subgroup_calibration"]}

    # Modelo B: confirmación con reglas declaradas antes de correr
    conf = _read(CONFIRMATION)
    _check_privacy(conf["privacy"])
    assert conf["final_key"] == "b" and conf["b_vs_incumbent"]["promoted"]
    assert conf["b_vs_incumbent"]["pr_auc_wins"] == 4 and conf["b_vs_incumbent"]["lift_wins"] == 4
    b = conf["specs"]["b"]
    assert b["parameters"] == 82 and b["tenure"] == "tenure_playbook_band"
    bsum = b["summary"]
    assert fmt(bsum["lift_at_10_percent"] * 10) == "21", "Cambió el lift de B"
    assert fmt(conf["specs"]["incumbent"]["summary"]["lift_at_10_percent"] * 10) == fmt(fsum["lift_at_10_percent"] * 10) == "20.1"
    assert [round(100 * r) for r in bsum["calibration_ratio_by_fold"]] == [111, 111, 106, 104], "Cambió la calibración de B"
    b_last = b["folds"][-1]
    assert b_last["converged"]
    b_cal = b_last["calibration"]
    assert len(b_cal) == 5 and all(x["published"] and x["events"] >= 30 for x in b_cal)
    # Quintos de riesgo estimado juntando las 4 pruebas: real = salidas / exposiciones,
    # estimado ponderado por exposiciones. Todo sale de agregados ya publicados.
    assert len(b["folds"]) == 4 and all(len(f["calibration"]) == 5 for f in b["folds"])
    pooled = []
    for q in range(5):
        bins = [f["calibration"][q] for f in b["folds"]]
        assert all(x["published"] and x["events"] >= 30 for x in bins)
        exposures = sum(x["exposures"] for x in bins)
        pooled.append({
            "observed": 100 * sum(x["events"] for x in bins) / exposures,
            "predicted": sum(x["exposures"] * x["mean_predicted_percent"] for x in bins) / exposures,
        })
    assert [fmt(x["observed"]) for x in pooled] == ["1.3", "2.1", "2.7", "3.6", "5.5"], "Cambiaron los quintos reales"
    assert [fmt(x["predicted"]) for x in pooled] == ["1.4", "2.3", "3", "3.8", "5.9"], "Cambiaron los quintos estimados"
    assert all(x["predicted"] >= x["observed"] for x in pooled)
    exposures = sum(f["exposures"] for f in b["folds"])
    pooled_mean = 100 * sum(f["events"] for f in b["folds"]) / exposures
    assert fmt(pooled_mean) == "3"
    b_interp = conf["interpretation"]["final"]
    b_hr = {c["term"]: c["hazard_ratio_by_fold"][-1] for c in b_interp["coefficients"]}
    assert b_interp["references"]["team_exits_12m"] == "0"
    assert conf["design"]["fold_starts"] == adj["design"]["fold_starts"]

    # Grupos: agrupación elegida fuera de muestra entre combinaciones fijas y árboles
    gsel = _read(GROUP_SELECTION)
    _check_privacy(gsel["privacy"])
    assert gsel["winner"]["variables"] == ["antiguedad", "salidas_equipo", "nivel"]
    top = gsel["final"]
    assert gsel["design"]["min_group_people"] == 300 and gsel["design"]["min_published_events"] == 30
    assert len(top["top"]) == 5 and top["groups_eligible"] == 22
    assert all(g["people"] >= 300 and g["last_fold_events"] >= 30 for g in top["top"])
    assert [g["group"] for g in top["top"]] == [g["group"] for g in top["all_groups"][:5]]
    trees = [c for c in gsel["candidates"] if c["kind"] == "tree"]
    assert len(gsel["candidates"]) == 58 and len(trees) == 2

    fold_starts = adj["design"]["fold_starts"]
    return {
        "lit": load_literature(),
        "cmp_lift": cmp_lift,
        "family_error_pp": family_error_pp,
        "family_dev_pct": family_dev_pct,
        "hazard_per_100": hazard_per_100,
        "n_tests": len(scope["folds"]),
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
        # Modelo B sustituye al anterior en portada y diapositivas 5 a 8.
        "previous_lift": fsum["lift_at_10_percent"] * 10,
        "b": b,
        "b_lift": bsum["lift_at_10_percent"] * 10,
        "b_fold_lifts": [v * 10 for v in bsum["by_fold"]["lift_at_10_percent"]],
        "b_ratios": bsum["calibration_ratio_by_fold"],
        "b_last": b_last,
        "b_calibration": b_cal,
        "b_pooled": pooled,
        "b_pooled_mean": pooled_mean,
        "b_hr": b_hr,
        "b_frame": conf["frame"],
        "top": top,
        "selection": gsel,
        "best_tree_efficiency": max(c["mean_efficiency"] for c in trees),
    }


def _add_months(date_text: str, months: int) -> str:
    year, month, day = (int(x) for x in date_text.split("-"))
    total = year * 12 + month - 1 + months
    return f"{total // 12}-{total % 12 + 1:02d}-{day:02d}"


# Bloques de nivel con la numeración de level_grouped; la leyenda lista los valores de la base.
LEVEL_NAMES = {"entrada": "Niveles 7–8", "medio": "Niveles 5–6", "alto": "Niveles 1–3", "otro": "Otros"}
LEVEL_LEGEND = [
    ("Niveles 7–8", ["8 - Assoc & Int/Eng", "7 - Senior & Lead"]),
    ("Niveles 5–6", ["6 - Staff & /Mgr", "5 - Sr Staff & /Mgr"]),
    ("Niveles 1–3", ["3 - Princ/Directors", "2 - Sr Dir", "1 - VP & Above"]),
]

NAV = [
    "Recomendación",
    "Agenda",
    "Cómo nos documentamos",
    "De 10 familias de modelos a una",
    "El modelo elegido",
    "Grupos de mayor riesgo",
    "Qué tan bueno es",
    "Próximos pasos",
]

# Árbol de los 8 grupos: regla de la fuente -> (antigüedad, división intermedia, hoja).
# El orden sigue las ramas del árbol para dibujarlo de arriba abajo.
GROUP_TREE = {
    "company_tenure_band ≠ 7+ years y team_exits_12m ≠ 0 y company_tenure_band = <1 year":
        ("Menos de 1 año", None, "Con salidas en su equipo"),
    "company_tenure_band ≠ 7+ years y team_exits_12m = 0 y company_tenure_band = <1 year":
        ("Menos de 1 año", None, "Sin salidas en su equipo"),
    "company_tenure_band ≠ 7+ years y team_exits_12m ≠ 0 y company_tenure_band ≠ <1 year":
        ("1 a 7 años", None, "Con salidas en su equipo"),
    "company_tenure_band ≠ 7+ years y team_exits_12m = 0 y company_tenure_band ≠ <1 year":
        ("1 a 7 años", None, "Sin salidas en su equipo"),
    "company_tenure_band = 7+ years y level_grouped = 7 - Senior & Lead y team_exits_12m ≠ 0":
        ("7+ años", "Nivel Senior & Lead", "Con salidas en su equipo"),
    "company_tenure_band = 7+ years y level_grouped = 7 - Senior & Lead y team_exits_12m = 0":
        ("7+ años", "Nivel Senior & Lead", "Sin salidas en su equipo"),
    "company_tenure_band = 7+ years y level_grouped ≠ 7 - Senior & Lead y direct_reports_band = 0":
        ("7+ años", "Otros niveles", "Sin reportes directos"),
    "company_tenure_band = 7+ years y level_grouped ≠ 7 - Senior & Lead y direct_reports_band ≠ 0":
        ("7+ años", "Otros niveles", "Con reportes directos"),
}

CSS = v3.CSS + """
    .muted { color: var(--text-muted); }
    .hlabel small { font-size: 13px; font-weight: 400; }

    /* Portada */
    .cover-kpi { display: flex; flex-direction: column; gap: 6px; padding: 14px 18px; }
    .cover-kpi b { font-size: 34px; font-weight: 800; color: var(--accent); text-transform: none; letter-spacing: 0; line-height: 1.1; }
    .cover-kpi span { font-size: 16.5px; font-weight: 500; line-height: 1.35; }

    /* Agenda */
    .agenda { display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; align-self: center; }
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
    .fam-grid { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(0, .75fr); gap: 24px; }
    .fam-grid > .card { min-width: 0; justify-content: center; gap: 14px; padding: 18px; }
    .fam { width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 16px; line-height: 1.3; }
    .fam th, .fam td { padding: 5px 7px; border-bottom: 1px solid var(--border-subtle); text-align: left; vertical-align: middle; }
    .fam th { font-size: 13px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .05em; }
    .fam th:first-child { width: 31%; }
    .fam th:nth-child(2), .fam td:nth-child(2) { width: 9%; text-align: center; }
    .fam th:nth-child(3), .fam td:nth-child(3) { width: 15%; text-align: center; }
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

    /* Árbol de grupos */
    .tree-grid { display: grid; grid-template-columns: 2.5fr 1fr; gap: 22px; }
    .tree { display: grid; grid-template-columns: 112px 150px 200px minmax(0, 1fr) 84px 118px; column-gap: 12px; align-items: stretch; }
    .tree > div { display: flex; align-items: center; min-height: 50px; border-top: 1px solid var(--border-subtle); }
    .tree > .tr-h { min-height: 0; border-top: none; padding-bottom: 8px; font-size: 13px; font-weight: 700; color: var(--text-muted); line-height: 1.25; align-items: flex-end; grid-row: 1; }
    .tree > .first, .tree > .tr-tenure { border-top: 2px solid var(--text-muted); }
    .tr-tenure { grid-column: 1; font-size: 17px; font-weight: 800; }
    .tr-mid { grid-column: 2; font-size: 15.5px; font-weight: 700; padding-left: 10px; border-left: 3px solid var(--border-subtle); }
    .tr-leaf { font-size: 15.5px; padding-left: 10px; border-left: 3px solid var(--border-subtle); }
    .tr-leaf.hi { font-weight: 800; color: var(--accent); border-left-color: var(--accent); }
    .tr-bar { grid-column: 4; }
    .tr-track { position: relative; height: 24px; width: 100%; }
    .tr-track i { display: block; height: 100%; border-radius: 0 6px 6px 0; background: var(--ctx); }
    .tr-bar.hi .tr-track i { background: var(--accent); }
    .tr-track b { position: absolute; top: 50%; transform: translateY(-50%); padding-left: 8px; font-size: 17px; font-weight: 800; }
    .tr-bar.hi .tr-track b { color: var(--accent); }
    .tr-people { grid-column: 5; flex-direction: column; justify-content: center; align-items: flex-start !important; font-size: 15px; line-height: 1.2; }
    .tr-people small { font-size: 13px; color: var(--text-muted); }
    .tr-test { grid-column: 6; font-size: 14.5px; }
    .tr-test.over { color: #b45309; font-weight: 700; }
    body.theme-dark-royal .tr-test.over, body.theme-dark-carbon .tr-test.over { color: #fbbf24; }

    /* Modelo B: 10 señales en 5 columnas */
    .sig { grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 16px 18px; }
    .sig div { font-size: 15.5px; }
    .sig div b { font-size: 16.5px; }
    .model-content { gap: 16px; }

    /* Top 5 grupos */
    .top-grid { display: grid; grid-template-columns: 2.4fr 1fr; gap: 22px; }
    .top { display: grid; grid-template-columns: 110px 150px 104px minmax(0, 1fr) 92px 124px; column-gap: 12px; }
    .top > div { display: flex; align-items: center; min-height: 62px; border-top: 1px solid var(--border-subtle); font-size: 16.5px; }
    .top > .tp-h { min-height: 0; border-top: none; padding-bottom: 8px; font-size: 13px; font-weight: 700; color: var(--text-muted); line-height: 1.25; align-items: flex-end; }
    .top > .tp-first { font-weight: 800; }
    .tp-rank { font-weight: 800; color: var(--accent); margin-right: 8px; }
    .tp-track { position: relative; height: 26px; width: 100%; }
    .tp-track i { display: block; height: 100%; border-radius: 0 6px 6px 0; background: var(--accent); }
    .tp-track b { position: absolute; top: 50%; transform: translateY(-50%); padding-left: 8px; font-size: 17px; font-weight: 800; color: var(--accent); }
    .tp-track s { position: absolute; top: -4px; bottom: -4px; border-left: 2px dashed var(--text-muted); }
    .top > .tp-people { flex-direction: column; justify-content: center; align-items: flex-start; line-height: 1.2; font-size: 15px; }
    .tp-people small { font-size: 13px; color: var(--text-muted); }
    .top > .tp-test { font-size: 15px; }
    .tp-test.over { color: #b45309; font-weight: 700; }
    .tp-test.under { color: var(--accent); font-weight: 700; }
    body.theme-dark-royal .tp-test.over, body.theme-dark-carbon .tp-test.over { color: #fbbf24; }
    .tp-more { margin-top: 10px; font-size: 15px; color: var(--text-muted); }
    .lv-legend { display: flex; flex-direction: column; gap: 8px; }
    .lv-legend > div { display: grid; grid-template-columns: 104px 1fr; gap: 10px; font-size: 14.5px; line-height: 1.3; border-left: 3px solid var(--accent); padding-left: 10px; }
    .lv-legend b { font-size: 15px; }

    /* Qué tan bueno es: una gráfica */
    .ev7-grid { display: grid; grid-template-columns: 2.1fr 1fr; gap: 22px; }
    .ev7-chart { position: relative; }
    .ev7-chart .cal { height: 360px; gap: 36px; padding: 0 20px; }
    .ev7-chart .cal-bar span { font-size: 19px; }
    .ev7-chart .cal-labels { gap: 36px; padding: 0 20px; font-size: 15.5px; font-weight: 600; color: var(--text-main); margin-top: 8px; }
    .ev7-axis { text-align: center; font-size: 14.5px; color: var(--text-muted); margin-top: 6px; }
    .ev7-read { display: flex; flex-direction: column; gap: 6px; border-left: 3px solid var(--accent); padding-left: 14px; }
    .ev7-read b { font-size: 18px; }
    .ev7-read span { font-size: 16px; line-height: 1.4; }

    /* Qué tan bueno es */
    .eval-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
    .eval-bars .hrow { grid-template-columns: 230px 1fr; }
    .eval-bars .hlabel { font-size: 15.5px; }
    .eval-cal.cal { height: 270px; gap: 16px; }
    .eval-grid .cal-labels { gap: 16px; font-size: 13.5px; }

    /* Próximos pasos */
    .next-after { font-size: 18px; color: var(--text-muted); }
    .next-list { list-style: none; margin: 0; padding: 0 40px; counter-reset: r; display: flex; flex-direction: column; justify-content: center; gap: 32px; }
    .next-list li { counter-increment: r; position: relative; padding-left: 74px; font-size: 30px; font-weight: 600; line-height: 1.3; }
    .next-list li::before { content: counter(r); position: absolute; left: 0; top: 50%; transform: translateY(-50%); width: 50px; height: 50px; border-radius: 50%; background: var(--accent); color: var(--text-invert); font-weight: 800; display: grid; place-items: center; font-size: 24px; }
    .next-list li small { display: block; font-size: 18px; font-weight: 400; color: var(--text-muted); margin-top: 4px; }
"""


def build_slides(d: dict) -> list[str]:
    slides = []
    # El modelo B es el elegido: sus cifras sustituyen a las del modelo anterior.
    lit, final, last = d["lit"], d["b"], d["b_last"]
    top = d["top"]
    obs_last, pred_last = last["observed_rate_percent"], last["mean_predicted_percent"]

    # 1. Portada
    first_test, last_test = d["fold_periods"][0][0], d["fold_periods"][-1][1]
    kpis = [
        (f"{fmt(pred_last)}% vs {fmt(obs_last)}%", "cuánta attrition estimó contra la que hubo en el último periodo"),
        (f"{fmt(top['top_people_share_percent'])}% → {fmt(top['top_last_fold_observed_exits_share_percent'])}%",
         "los 5 grupos de mayor riesgo reúnen al 19% de las personas y concentraron el 31% de las salidas reales"),
        (f"{top['groups_eligible']} grupos", "con datos que RH ya tiene: antigüedad, salidas en el equipo y nivel; cada uno con más de 300 personas"),
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
        ("3", "Qué grupos encuentra", "Diapositiva 6", "Los 5 grupos de Engineering con más riesgo a 6 meses y cómo los elegimos."),
        ("4", "Qué tan bueno es", "Diapositiva 7", "Si ordena bien el riesgo y si le atina a cuántos se van, en 4 pruebas."),
        ("5", "Próximos pasos", "Diapositiva 8", "Lo que haremos en las siguientes 2 semanas."),
    ]
    ag_html = "".join(
        f'<article class="card ag-item"><div class="ag-num">{n}</div><div class="ag-head">{e(h)}</div>'
        f'<div class="ag-slides">{e(s)}</div><div class="ag-body">{e(b)}</div></article>'
        for n, h, s, b in agenda
    )
    slides.append(slide(
        len(slides),
        heading("De la literatura a un modelo listo para piloto, en cinco partes",
                "Cada parte responde una pregunta de la decisión; las cifras vienen de los datos de Engineering, no de los papers")
        + f'<div class="agenda">{ag_html}</div><div class="src">Clasificación: presentación. Sólo resultados agregados por grupo.</div>',
    ))

    # 3. Esfuerzo de documentación
    first_year, last_year = lit["years"]
    funnel = [
        ("9", "líneas de búsqueda", "Supervivencia, turnover, talento técnico, riesgos competitivos, ML, constructos de RH, causalidad, fairness y texto"),
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
            "Dimos prioridad a trabajos con métodos reproducibles, datos longitudinales y salidas reales",
        )
        + f'<div class="lit-grid"><article class="card" style="justify-content:center;gap:8px;padding:18px 20px;"><div class="funnel">{fn_html}</div></article>'
        f'<article class="card" style="justify-content:center;gap:4px;padding:18px 22px;"><div class="side-head" style="margin-bottom:4px;">Trabajos por tema y qué decidió cada tema</div>'
        f'{th_html}<div class="note-box" style="margin-top:10px;">No copiamos ningún modelo ni sus datos: revisamos cada trabajo y lo usamos para aportar ideas. '
        f'Los modelos que probamos se construyeron y ajustaron con los datos de Qualcomm.</div></article></div>'
    ))

    # 4. De 10 familias de modelos a una
    fam_rows = ""
    for name, mark, verdict, key in FAMILIES:
        icon, label = FAMILY_MARKS[mark]
        cls = ' class="chosen"' if key == "hazard" else ""
        error_cell = (
            f'<td class="precision-value" title="Desviación media del total real de salidas: {fmt(d["family_dev_pct"][key])}%">{fmt(d["family_dev_pct"][key])}%</td>'
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
            "De 10 familias de modelos estadísticos, probamos 4 y elegimos el riesgo mes a mes",
            "5 descartadas y 1 pendiente · criterios fijados el 30-sep-2026, antes de ver resultados · pruebas con datos de Engineering (diapositiva 7)",
        )
        + f'<div class="fam-grid"><article class="card">'
        f'<table class="fam" aria-label="Familias de modelos, desviación del total real y decisión de evaluación" aria-describedby="family-error-note"><thead><tr>'
        f'<th scope="col">Familia de modelos</th><th scope="col">Estado</th><th scope="col">Desviación<small>vs. total real · menor es mejor</small></th>'
        f'<th scope="col">Motivo</th></tr></thead><tbody>{fam_rows}</tbody></table>'
        f'<div class="eff-foot" id="family-error-note"><b>Desviación:</b> % de diferencia entre las salidas estimadas y las reales '
        f'(promedio de {d["n_tests"]} pruebas).</div></article>'
        f'<article class="card"><div class="side-head">Qué buscamos en el modelo</div>'
        f'<div class="crit">{crit_html}</div>'
        f'</article></div>'
        f'<div class="src">Desviación: comparación de los modelos base con datos de Engineering, 1-oct-2026.</div>',
    ))

    # 5. El modelo elegido
    frame = d["b_frame"]
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
        ("Antigüedad en la empresa", "cortes del playbook: <1, 1-2, 2-3, 3-5, 5-10, 10+ años", False),
        ("Mes del año", "la temporada de salidas", False),
        ("Cambios de manager", "en los últimos 12 meses: 0, 1, 2+", False),
        ("Salidas del equipo", "renuncias en 12 meses en el equipo del manager actual: 0, 1, 2+", False),
        ("Reportes directos", "personas a cargo: 0, 1 a 5, 6+", False),
        ("Desde la última promoción", "<1, 1-2, 2-3, 3+ años, o sin promoción", False),
        ("Recontratación", "si ya había trabajado antes en la empresa", False),
        ("Nivel × antigüedad", "la antigüedad pesa distinto en cada nivel", True),
        ("Antigüedad × cambios de manager", "cambiar de manager pesa distinto según la antigüedad", True),
    ]
    sig_html = "".join(
        f'<div{" class=combo" if combo else ""}><b>{e(h)}</b>{e(b)}</div>' for h, b, combo in signals
    )
    slides.append(slide(
        len(slides),
        heading(
            "El modelo estima el riesgo de renunciar cada mes con 8 señales y 2 combinaciones, y lo acumula a 6 meses",
            "Riesgo mes a mes, también llamado hazard discreto · especificación final del 3-oct-2026",
        )
        + f'<div class="model-content"><div class="pipe">{pipe_html}</div>'
        f'<article class="card signals-card"><div class="section-head">Las señales</div><div class="sig">{sig_html}</div></article>'
        f'<div class="model-progress">Nuevo frente a la versión anterior: cortes del playbook, promoción y recontratación; ganó en las 4 pruebas.</div></div>'
        f'<div class="src">Fuente: {SOURCE}. Sin segmento, job family ni atributos protegidos como señal.</div>',
    ))

    # 6. Los 5 grupos de mayor riesgo, de 22 grupos de antigüedad × salidas en el equipo × nivel
    mean = top["mean_predicted_6m_percent"]
    g_max = max(g["predicted_6m_percent"] for g in top["top"]) * 1.3
    rows_html = ""
    for i, g in enumerate(top["top"], start=1):
        parts = g["parts"]
        width = g["predicted_6m_percent"] / g_max * 100
        gap = g["last_fold_predicted_percent"] - g["last_fold_observed_percent"]
        test_cls = " over" if gap >= 1.0 else ""
        rows_html += (
            f'<div class="tp-first"><span class="tp-rank">{i}</span>{e(parts["antiguedad"])}</div>'
            f'<div>{e(parts["salidas_equipo"].capitalize())}</div>'
            f'<div>{e(LEVEL_NAMES[parts["nivel"]])}</div>'
            f'<div><div class="tp-track"><i style="width:{width:.2f}%"></i><s style="left:{mean / g_max * 100:.2f}%"></s>'
            f'<b style="left:{width:.2f}%">{fmt(g["predicted_6m_percent"])}%</b></div></div>'
            f'<div class="tp-people">{g["people"]:,}<small>{fmt(g["people_share_percent"])}%</small></div>'
            f'<div class="tp-test{test_cls}">{fmt(g["last_fold_predicted_percent"])}% · {fmt(g["last_fold_observed_percent"])}%</div>'
        )
    with_exits = sum(g["parts"]["salidas_equipo"] == "con salidas" for g in top["top"])
    entry = sum(g["parts"]["nivel"] == "entrada" for g in top["top"])
    levels = set(d["selection"]["design"]["level_values_seen"])
    assert all(v in levels for _, values in LEVEL_LEGEND for v in values)
    legend_html = "".join(
        f'<div><b>{e(name)}</b><span>{"<br>".join(e(v) for v in values)}</span></div>' for name, values in LEVEL_LEGEND
    )
    winner = d["selection"]["winner"]
    others = top["groups_eligible"] - len(top["top"])
    slides.append(slide(
        len(slides),
        heading(
            f"Los 5 grupos de mayor riesgo reúnen al {fmt(top['top_people_share_percent'])}% de Engineering y concentraron el "
            f"{fmt(top['top_last_fold_observed_exits_share_percent'])}% de las salidas reales; {with_exits} tienen renuncias recientes en su equipo",
            f"% que se estima saldrá en 6 meses · foto del {v3.day_label(top['snapshot'])} · {top['people']:,} personas · "
            f"grupos por antigüedad, salidas en el equipo y nivel",
        )
        + f'<div class="top-grid"><article class="card" style="justify-content:center;padding:16px 22px;">'
        f'<div class="top"><div class="tp-h">Antigüedad</div><div class="tp-h">Salidas en su equipo</div><div class="tp-h">Nivel</div>'
        f'<div class="tp-h">Riesgo estimado a 6 meses · línea: promedio {fmt(mean)}%</div><div class="tp-h">Personas</div>'
        f'<div class="tp-h">Última prueba<br>estimado · real</div>{rows_html}</div>'
        f'<div class="tp-more">Se muestran los 5 grupos de mayor riesgo de {top["groups_eligible"]}; los otros {others} tienen menos riesgo. '
        f'{entry} de los 5 son de los niveles 7–8.</div></article>'
        f'<article class="card" style="justify-content:center;gap:16px;padding:22px;">'
        f'<div class="kpi"><b>{fmt(top["top_last_fold_observed_exits_share_percent"])}%</b><span>de las salidas reales de la última prueba, '
        f'con el {fmt(top["top_people_share_percent"])}% de las personas; ordenando persona por persona habría sido '
        f'{fmt(top["individual_last_fold_observed_exits_share_at_same_people_percent"])}%</span></div>'
        f'<div class="side-head" style="margin-bottom:0;">Qué niveles incluye cada bloque</div>'
        f'<div class="lv-legend">{legend_html}</div>'
        f'<div class="note-box" style="font-size:14.5px;">En naranja, estimado 1 punto o más arriba del real: el modelo exagera algo los niveles 7–8 (diapositiva 7).</div></article></div>'
        f'<div class="src">Elegimos esta forma de agrupar entre {len(d["selection"]["candidates"])} opciones, incluido un árbol: conserva el '
        f'{round(100 * winner["mean_efficiency"])}% de lo que ordena el modelo en las 4 pruebas (el árbol, {round(100 * d["best_tree_efficiency"])}%). Salidas en el equipo = 1 o más renuncias en 12 meses en el equipo del manager actual '
        f'(con 2 o más, el riesgo mensual sube {pct_change(d["b_hr"]["team_exits_12m=2+"])}). Cada persona cae en un solo grupo; grupos de 300+ personas y 30+ salidas en la última prueba. '
        f'Fuente: {SOURCE}.</div>',
    ))

    # 7. Qué tan bueno es: de cada 100 personas, cuántas se fueron, real contra estimado
    pooled = d["b_pooled"]
    top_cal = max(x["predicted"] for x in pooled) * 1.2
    cal_pairs = "".join(
        f'<div class="cal-pair"><div class="cal-bar obs"><span>{fmt(x["observed"])}</span><i style="height:{x["observed"] / top_cal * 100:.2f}%"></i></div>'
        f'<div class="cal-bar pred"><span>{fmt(x["predicted"])}</span><i style="height:{x["predicted"] / top_cal * 100:.2f}%"></i></div></div>'
        for x in pooled
    )
    cal_labels = "".join(f"<div>{t}</div>" for t in ["Menor riesgo", "2º", "3º", "4º", "Mayor riesgo"])
    low, high = pooled[0]["observed"], pooled[-1]["observed"]
    times = round(high / low)
    assert times == 4
    lo_over, hi_over = round(100 * (min(d["b_ratios"]) - 1)), round(100 * (max(d["b_ratios"]) - 1))
    avg = d["b_pooled_mean"]
    slides.append(slide(
        len(slides),
        heading(
            f"Qué tan bueno es: los que marca con más riesgo se van {times} veces más que los de menor riesgo, "
            f"y estima un poco más salidas de las que hubo",
            f"4 pruebas con datos que el modelo no vio, de {d['fold_periods'][0][0]} a {d['fold_periods'][-1][1]} · "
            f"de cada 100 personas, cuántas se fueron en 6 meses · Engineering",
        )
        + f'<div class="ev7-grid"><article class="card" style="justify-content:center;gap:12px;padding:20px 26px;">'
        f'<div style="display:flex;align-items:center;"><div class="legend"><span>Se fueron (real)</span><span class="pred">Estimado por el modelo</span></div>'
        f'<div class="muted" style="margin-left:auto;font-size:14.5px;">de cada 100 personas, en 6 meses</div></div>'
        f'<div class="ev7-chart"><div class="cal">{cal_pairs}</div>'
        f'</div>'
        f'<div class="cal-labels">{cal_labels}</div>'
        f'<div class="ev7-axis">Personas ordenadas por el riesgo que estimó el modelo, en 5 grupos del mismo tamaño</div></article>'
        f'<article class="card" style="justify-content:center;gap:24px;padding:24px;">'
        f'<div class="ev7-read"><b>1 · Ordena bien</b><span>De cada 100 personas, en el grupo de menor riesgo se fue {fmt(low)}; '
        f'en el de mayor riesgo, {fmt(high)}. El promedio de Engineering es {fmt(avg)}.</span></div>'
        f'<div class="ev7-read"><b>2 · Le atina a cuántos se van</b><span>Estimó un poco de más en todos los grupos: entre {lo_over}% y {hi_over}% '
        f'más salidas en total. La mayor diferencia está en el grupo de mayor riesgo; es la primera corrección pendiente.</span></div>'
        f'<div class="note-box">Aun en el grupo de mayor riesgo, {round(100 - high)} de cada 100 se quedan: el modelo sirve para elegir grupos donde actuar, no personas.</div>'
        f'</article></div>'
        f'<div class="src">Cada grupo tiene 30+ salidas en cada prueba; en cada una, el modelo se entrenó sólo con la historia anterior. Fuente: {SOURCE}.</div>',
    ))

    # 8. Próximos pasos: 3 bullets, sin detalle
    pending = [f[0] for f in FAMILIES if f[1] == "part"]
    assert pending == ["Random survival forest"]
    steps = [
        ("Revisar otros modelos", "Random survival forest, la única familia de modelos que falta probar"),
        ("Validar otras variables", "como QVoice (intención de quedarse) y tiempo en el nivel"),
        ("Corregir y validar", "bajar el exceso estimado en el grupo de mayor riesgo y revisar que trate igual a todos los grupos"),
        ("Elegir la versión final", "con las mismas 4 pruebas; lo nuevo entra sólo si mejora al modelo actual"),
    ]
    steps_html = "".join(f"<li>{e(h)}<small>{e(t)}</small></li>" for h, t in steps)
    slides.append(slide(
        len(slides),
        heading("Próximos pasos: en las siguientes 2 semanas", "Mejorar, corregir o cambiar el modelo antes de usarlo")
        + f'<article class="card" style="justify-content:center;"><ol class="next-list">{steps_html}</ol></article>'
        + '<div class="next-after">Después, con el modelo final: piloto en 1 o 2 grupos y actualización periódica.</div>',
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
    out = out.replace("<title>[Slide Title]</title>", "<title>Modelo de attrition voluntaria de Engineering: qué elegimos y por qué (v8)</title>", 1)
    if draft_selection:
        out = out.replace(
            "<title>Modelo de attrition voluntaria de Engineering: qué elegimos y por qué (v8)</title>",
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
    topic = "borrador-slide4-seleccion" if args.draft_selection else "seleccion-modelo-v8"
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
