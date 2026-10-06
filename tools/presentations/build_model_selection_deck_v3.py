"""Genera el deck v3 de selección del modelo de attrition, sin segmento ni job family.

Cambios frente a v2:

- ``seg`` (derivado de ``job_family``) sale del modelo: la reasignación de job
  family del 2026-09-01 cambió el segmento del 10.9% de las personas
  (``queries/audits/critical_tech_seg_stability_job_family_reassignment_20261001.sql``).
  La población pasa a ser todo Critical Tech.
- Muestra los grupos nivel × antigüedad que genera el modelo, con su riesgo
  actual y con estimado contra real en el último periodo de prueba.
- Explica la métrica de orden con la curva de captura.

Las cifras se leen de ``tools/critical_tech_model_comparison_rolling_noseg.py``
y se validan contra valores esperados; si la fuente cambia, el script falla.
Reutiliza estilos y componentes del builder v2.

Uso:
    python -B tools/presentations/build_model_selection_deck_v3.py [--out RUTA]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("deck_v2", Path(__file__).resolve().parent / "build_model_selection_deck_v2.py")
v2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v2)

fmt, pct_change, month_label, e, heading, slide, effect_panel = (
    v2.fmt, v2.pct_change, v2.month_label, v2.e, v2.heading, v2.slide, v2.effect_panel,
)
MONTHS, MARKS = v2.MONTHS, v2.MARKS

COMPARISON = (
    ROOT / "output" / "analysis" / "critical-tech" / "20261001" / "model-comparison-rolling-noseg-v1" / "comparison-results.json"
)
TENURE_LABELS = v2.TENURE_LABELS
TENURE_ORDER = v2.TENURE_ORDER
LEVEL_ORDER = [
    "8 - Assoc & Int/Eng", "7 - Senior & Lead", "6 - Staff & /Mgr", "5 - Sr Staff & /Mgr",
    "3 - Princ/Directors", "2 - Sr Dir", "1 - VP & Above",
]
LEVEL_LABELS = {**v2.LEVEL_LABELS, "2 - Sr Dir": "Sr Director", "1 - VP & Above": "VP o superior"}
MODELS = ["hazard", "hazard_interactions", "logistic", "lightgbm"]
MODEL_NAMES = {
    "hazard": "Riesgo mes a mes (recomendado)",
    "hazard_interactions": "Mes a mes + nivel × antigüedad",
    "logistic": "Regresión logística directa a 6 meses",
    "lightgbm": "Machine learning (LightGBM)",
}
SHORT = {"hazard": "Mes a mes", "hazard_interactions": "+ nivel × antig.", "logistic": "Logística 6m", "lightgbm": "LightGBM"}
SOURCE = "comparación rolling-origin sin segmento, 1-oct-2026"


def day_label(date_text: str) -> str:
    year, month, day = date_text.split("-")
    return f"{int(day)}-{MONTHS[int(month) - 1]}-{year}"


def group_label(row: dict) -> str:
    return f"{LEVEL_LABELS[row['level_grouped']]} · {TENURE_LABELS[row['company_tenure_band']]}"


def load_data() -> dict:
    result = json.loads(COMPARISON.read_text(encoding="utf-8"))
    assert result["deliverable_classification"] == "presentation"
    assert result["privacy"]["employee_level_rows_persisted"] is False
    assert "seg" not in result["design"]["features"], "El modelo v3 no debe usar segmento"
    seg = result["seg_stability"]
    assert seg["outcome"] == "fail" and fmt(seg["changed_percent"]) == "10.9"
    scope = result["scope"]
    folds = scope["folds"]
    assert len(folds) == 4
    for fold in folds:
        assert fold["monthly_train_last_snapshot"] < fold["test_start"]
    summary = scope["summary"]
    last = scope["last_fold"]
    extra = scope["last_fold_extra"]
    last_metrics = folds[-1]["metrics"]

    lift = {key: summary[key]["lift_at_10_percent"]["mean"] * 10 for key in MODELS}
    assert [fmt(lift[k]) for k in MODELS] == ["17", "17.1", "16.8", "16.4"], "Cambiaron los resultados"

    coefficients = {(c["feature"], c["level"]): c for c in last["hazard_coefficients"]}
    refs = last["hazard_reference_levels"]

    def ratio(feature: str, level: str) -> float | None:
        if level == refs[feature]:
            return 1.0
        item = coefficients.get((feature, level))
        return item["relative_hazard_scale"] if item else None

    tenure = [(TENURE_LABELS[t], ratio("company_tenure_band", t), t == refs["company_tenure_band"]) for t in TENURE_ORDER]
    levels = [
        (LEVEL_LABELS[l], ratio("level_grouped", l), l == refs["level_grouped"])
        for l in LEVEL_ORDER
        if ratio("level_grouped", l) is not None
    ]
    months = [ratio("calendar_month", str(m)) for m in range(1, 13)]
    assert all(v is not None for v in months) and refs["calendar_month"] == "7"
    assert refs["company_tenure_band"] == "7+ years" and refs["level_grouped"] == "7 - Senior & Lead"
    assert fmt(ratio("company_tenure_band", "3-7 years")) == "1.6"

    worked = {p["profile"]: p for p in last["hazard_worked_example"]}
    reference = worked["referencia"]
    example = next(p for p in last["hazard_worked_example"] if p["levels"]["company_tenure_band"] == "3-7 years"
                   and p["levels"]["manager_change_12m"] == "unknown")
    start_month = int(reference["first_month"][5:7])

    def mean_pred(key: str) -> float:
        bins = last_metrics[key]["calibration"]
        return sum(b["exposures"] * b["mean_predicted_percent"] for b in bins) / sum(b["exposures"] for b in bins)

    calibration = last_metrics["hazard"]["calibration"]
    assert all(b["published"] for b in calibration) and len(calibration) == 5
    one_way = last["one_way_fit"]
    under_one = next(r for r in one_way["company_tenure_band"] if r["level"] == "<1 year")
    manager = {r["level"]: r for r in one_way["manager_change_12m"]}

    current = scope["current"]
    groups_now = current["groups"]
    assert all(g["people_per_snapshot"] >= 30 for g in groups_now)
    expected_total = sum(g["people_per_snapshot"] * g["predicted_percent"] for g in groups_now)
    top5 = groups_now[:5]
    top5_people = sum(g["people_share_percent"] for g in top5)
    top5_exits = 100 * sum(g["people_per_snapshot"] * g["predicted_percent"] for g in top5) / expected_total

    test_groups = [g for g in extra["groups"]["hazard"] if g["observed_percent"] is not None]
    assert all(g["events"] >= 30 for g in test_groups)
    hidden_groups = len(extra["groups"]["hazard"]) - len(test_groups)

    capture = {p["people_percent"]: p["exits_percent"] for p in extra["capture"]["hazard"]}
    assert round(capture[10]) == 15 and round(capture[20]) == 28
    observed_last = last_metrics["hazard"]["observed_rate_percent"]
    top10_rate = last_metrics["hazard"]["lift_at_10_percent"] * observed_last

    pairs = seg["pairs"]
    moves = sorted(
        [p for p in pairs if p["seg_before"] != p["seg_after"] and not p["seg_before"].startswith("(pares")],
        key=lambda p: -p["employees"],
    )
    grouped_small = sum(p["employees"] for p in pairs if p["seg_before"].startswith("(pares"))

    return {
        "folds": folds,
        "first_test": month_label(folds[0]["test_start"]),
        "last_test": month_label(folds[-1]["test_end"]),
        "last_start": month_label(folds[-1]["test_start"]),
        "train_end": month_label(folds[-1]["monthly_train_last_snapshot"]),
        "lift": lift,
        "fold_lifts": {k: [v * 10 for v in summary[k]["lift_at_10_percent"]["by_fold"]] for k in MODELS},
        "wins": summary["wins_vs_hazard"],
        "exposures": scope["exposures"],
        "params": last["hazard_parameter_count"],
        "params_inter": last["hazard_interactions_parameter_count"],
        "trend": last["hazard_trend_ratio_per_year"],
        "tenure": tenure,
        "levels": levels,
        "months": months,
        "oct_events": coefficients[("calendar_month", "10")]["training_events"],
        "srdir_events": coefficients[("level_grouped", "2 - Sr Dir")]["training_events"],
        "manager_ratio": ratio("manager_change_12m", "yes"),
        "manager_share": 100 * manager["yes"]["exposures"] / last_metrics["hazard"]["exposures"],
        "manager_obs": (manager["yes"]["observed_rate_percent"], manager["unknown"]["observed_rate_percent"]),
        "reference": reference,
        "example": example,
        "example_ratio": ratio("company_tenure_band", "3-7 years"),
        "month_names": [MONTHS[(start_month - 1 + i) % 12] for i in range(6)],
        "calibration": calibration,
        "observed_last": observed_last,
        "pred_last": {k: mean_pred(k) for k in MODELS + ["historical"]},
        "last_events": last_metrics["hazard"]["events"],
        "last_exposures": last_metrics["hazard"]["exposures"],
        "under_one": under_one,
        "lgb_month_gain": next(g for g in last["lightgbm_gain_importance"] if g["feature"] == "calendar_month")["gain_share_percent"],
        "current": current,
        "groups_now": groups_now,
        "top5_people": top5_people,
        "top5_exits": top5_exits,
        "test_groups": test_groups,
        "hidden_groups": hidden_groups,
        "capture": capture,
        "top10_rate": top10_rate,
        "seg": seg,
        "moves": moves,
        "grouped_small": grouped_small,
    }


NAV = [
    "Recomendación",
    "Por qué sin job family",
    "Qué tipo de modelo es",
    "Los grupos que genera",
    "Grupos: estimado vs real",
    "Efecto de cada señal",
    "Efecto del calendario",
    "Cómo calcula",
    "Cómo medimos el orden",
    "Comparativa calculada",
    "Por qué mes a mes",
    "Qué tan bien estima el nivel",
    "Próximos pasos",
]

CSS = v2.CSS + """
    /* Estabilidad de segmento */
    .s2-grid { display: grid; grid-template-columns: 1fr 1.25fr; gap: 24px; }
    .stack { display: flex; height: 46px; border-radius: 8px; overflow: hidden; }
    .stack div { display: grid; place-items: center; font-weight: 800; font-size: 16px; }
    .stack .keep { background: var(--ctx); }
    .stack .chg { background: #d97706; color: #fff; }
    .stack-legend { display: flex; justify-content: space-between; font-size: 15px; color: var(--text-muted); }
    .mv-row { display: grid; grid-template-columns: 300px 1fr; gap: 14px; align-items: center; height: 38px; }
    .mv-label { font-size: 15.5px; text-align: right; line-height: 1.2; }
    .mv-label small { display: block; font-size: 12.5px; color: var(--text-muted); }
    .mv-track { position: relative; height: 28px; }
    .mv-fill { height: 100%; background: #d97706; border-radius: 0 6px 6px 0; }
    .mv-val { position: absolute; top: 50%; transform: translateY(-50%); padding-left: 8px; font-size: 16px; font-weight: 800; }
    .big-warn { font-size: 72px; font-weight: 800; color: #d97706; line-height: 1; }

    /* Mapa de grupos */
    .s4v3-grid { display: grid; grid-template-columns: 1.7fr 1fr; gap: 24px; }
    .heat { width: 100%; border-collapse: separate; border-spacing: 6px; }
    .heat th { font-size: 14.5px; color: var(--text-muted); font-weight: 700; padding: 2px 4px; }
    .heat th.rowh { text-align: right; font-size: 15.5px; color: var(--text-main); font-weight: 600; white-space: nowrap; padding-right: 8px; }
    .heat td { height: 56px; border-radius: 8px; text-align: center; line-height: 1.15; }
    .heat td b { display: block; font-size: 21px; }
    .heat td span { font-size: 12.5px; }
    .heat td.empty { background: transparent; border: 1px dashed var(--border-subtle); color: var(--text-muted); font-size: 13px; }
    .heat td.top { outline: 3px solid var(--text-main); outline-offset: -3px; }
    .kpi { display: flex; flex-direction: column; gap: 4px; }
    .kpi b { font-size: 54px; font-weight: 800; color: var(--accent); line-height: 1; }
    .kpi span { font-size: 16px; line-height: 1.35; }

    /* Estimado vs real por grupo */
    .db-grid { display: grid; grid-template-columns: 1.75fr 1fr; gap: 24px; }
    .db-head, .db-row { display: grid; grid-template-columns: 270px 1fr 130px; gap: 12px; align-items: center; }
    .db-row { height: 21px; }
    .db-head { font-size: 13px; color: var(--text-muted); font-weight: 700; }
    .db-label { font-size: 14px; text-align: right; white-space: nowrap; }
    .db-track { position: relative; height: 100%; }
    .db-track::before { content: ""; position: absolute; left: 0; right: 0; top: 50%; border-top: 1px solid var(--border-subtle); }
    .db-line { position: absolute; top: calc(50% - 2px); height: 4px; background: var(--ctx); }
    .db-row.gap .db-line { background: #d97706; }
    .db-dot { position: absolute; top: 50%; width: 14px; height: 14px; margin: -7px 0 0 -7px; border-radius: 50%; }
    .db-dot.pred { background: var(--accent); }
    .db-dot.obs { background: var(--bg-surface); border: 3px solid var(--text-muted); }
    .db-row.gap .db-dot.obs { border-color: #d97706; }
    .db-val { font-size: 13.5px; white-space: nowrap; }
    .db-row.gap .db-val { color: #b45309; font-weight: 700; }
    body.theme-dark-royal .db-row.gap .db-val, body.theme-dark-carbon .db-row.gap .db-val { color: #fbbf24; }
    .db-axis { position: relative; height: 18px; font-size: 12.5px; color: var(--text-muted); }
    .db-axis span { position: absolute; transform: translateX(-50%); }
    .legend span.gap::before { background: #d97706; }
    .legend span.dot-pred::before { border-radius: 50%; background: var(--accent); }
    .legend span.dot-obs::before { border-radius: 50%; background: transparent; border: 3px solid var(--text-muted); width: 9px; height: 9px; }

    /* Curva de captura */
    .cap-grid { display: grid; grid-template-columns: 1.35fr 1fr; gap: 24px; }
    .cap { display: grid; grid-template-columns: repeat(5, 1fr); gap: 28px; align-items: end; height: 330px; border-bottom: 2px solid var(--text-muted); padding: 0 10px; }
    .cap-labels { display: grid; grid-template-columns: repeat(5, 1fr); gap: 28px; text-align: center; font-size: 15px; color: var(--text-muted); padding: 0 10px; line-height: 1.25; }
    .cap-bar.rand i { background: var(--ctx); }
    .cap-bar.model i { background: var(--accent); }
    .cap-bar.model span { color: var(--accent); }
    .cap-bar span { font-size: 17px; }
    .legend span.model::before { background: var(--accent); }
    .prec { display: grid; grid-template-columns: auto 1fr; gap: 6px 14px; align-items: baseline; border-top: 1px solid var(--border-subtle); padding-top: 12px; }
    .prec b { font-size: 34px; color: var(--accent); }
    .prec b.muted { color: var(--text-muted); }
    .prec span { font-size: 15px; line-height: 1.3; }
"""


def heat_color(value: float, lo: float, hi: float) -> tuple[str, bool]:
    share = 12 + 78 * (value - lo) / (hi - lo)
    return f"background: color-mix(in oklab, var(--accent) {share:.0f}%, var(--bg-surface));", share > 52


def build_slides(d: dict) -> list[str]:
    slides = []
    lift = d["lift"]
    seg = d["seg"]
    cur = d["current"]

    # 1. Portada
    chips = [
        ("Población", "Todo Critical Tech: empleados regulares activos"),
        ("Horizonte", "Salidas voluntarias en los próximos 6 meses"),
        ("Resultado", "Riesgo por grupo de nivel × antigüedad con 30+ personas, nunca por persona"),
    ]
    chip_html = "".join(f'<div class="cover-chip"><b>{e(k)}</b><span>{e(v)}</span></div>' for k, v in chips)
    slides.append(slide(
        0,
        f'<div class="cover" style="grid-row: 1 / -1;"><div class="cover-kicker">People Analytics · Critical Tech · Octubre 2026</div>'
        f'<h1 class="cover-title">Recomendamos una regresión de supervivencia mes a mes que estima el riesgo de salida por grupo de nivel y antigüedad</h1>'
        f'<div class="cover-chips">{chip_html}</div>'
        f'<div class="cover-note">Versión sin job family ni segmento, porque la reasignación de septiembre de 2026 rompió su comparabilidad. '
        f'La comparamos en 4 periodos de prueba contra una regresión logística y un modelo de machine learning (LightGBM) calculados con los mismos datos.</div></div>',
        cls="",
    ))

    # 2. Por qué sin job family
    kept = 100 - seg["changed_percent"]
    moves = d["moves"][:6]
    mv_max = moves[0]["employees"] * 1.18
    mv_rows = "".join(
        f'<div class="mv-row"><div class="mv-label">{e(m["seg_after"])}<small>antes: {e(m["seg_before"])}</small></div>'
        f'<div class="mv-track"><div class="mv-fill" style="width:{m["employees"] / mv_max * 100:.2f}%"></div>'
        f'<div class="mv-val" style="left:{m["employees"] / mv_max * 100:.2f}%">{m["employees"]:,}</div></div></div>'
        for m in moves
    )
    slides.append(slide(
        1,
        heading(
            f"Quitamos job family del modelo: con la reasignación de septiembre, {fmt(seg['changed_percent'])}% de las personas cambió de segmento en un mes",
            "Mismas personas en las fotos mensuales del 23-ago-2026 y del 27-sep-2026 · empleados regulares activos · segmento derivado de job family",
        )
        + f'<div class="s2-grid"><article class="card" style="justify-content:center;gap:16px;padding:24px 26px;">'
        f'<div class="side-head">Personas que cambiaron de segmento</div><div class="big-warn">{seg["employees_seg_changed"]:,}</div>'
        f'<div class="side-body">de {seg["employees_in_both"]:,} presentes en ambas fotos. Para aceptar el segmento pedíamos que al menos 99% lo conservara; lo conservó {fmt(kept)}%.</div>'
        f'<div class="stack"><div class="keep" style="width:{kept:.2f}%">{fmt(kept)}%</div><div class="chg" style="width:{seg["changed_percent"]:.2f}%">{fmt(seg["changed_percent"])}%</div></div>'
        f'<div class="stack-legend"><span>Conservó el segmento</span><span>Cambió</span></div>'
        f'<div class="note-box">Un modelo entrenado con el segmento anterior asignaría a estas personas el riesgo de un grupo al que ya no pertenecen.</div></article>'
        f'<article class="card" style="justify-content:center;gap:10px;padding:22px 24px;"><div class="side-head">Segmento nuevo de quienes cambiaron (principales movimientos)</div>'
        f'{mv_rows}<div class="eff-foot">Casi todo sale de «Other Eng». Pertenecer o no a Critical Tech casi no cambió, así que job family sigue definiendo la población, '
        f'pero ya no entra como señal. Movimientos con menos de 30 personas se agrupan.</div></article></div>'
        f'<div class="src">Fuente: queries/audits/critical_tech_seg_stability_job_family_reassignment_20261001.sql, ejecutada el 1-oct-2026. '
        f'Consecuencia: la población es todo Critical Tech, incluido Other Eng.</div>',
    ))

    # 3. Tipo de modelo
    exp = d["exposures"]
    pipe = [
        ("1 · Datos", "Fotos mensuales por grupo",
         f"Cada mes contamos personas y salidas voluntarias del mes siguiente por nivel, antigüedad y cambio de manager. "
         f"Desde jul-2020: {exp['monthly']:,} personas-mes y {exp['monthly_events']:,} salidas.", None, False),
        ("2 · Modelo", "Una regresión, como la logística",
         "Cada señal suma un coeficiente; el enlace log-log complementario convierte la suma en un riesgo mensual entre 0 y 1.",
         "h = 1 − exp(−exp(α + Σ βx))", True),
        ("3 · Riesgo mensual", "Cambia con el calendario",
         "El mismo grupo tiene un riesgo distinto en mayo que en octubre, porque el mes del año es una de las señales.", None, False),
        ("4 · Riesgo a 6 meses", "Se acumula mes a mes",
         "Se encadenan los 6 riesgos mensuales; con la misma fórmula sale el riesgo a 3 o 12 meses sin reentrenar.",
         "R₆ = 1 − (1−h₁)(1−h₂)…(1−h₆)", False),
    ]
    pipe_html = "".join(
        f'<div class="pipe-step{" key" if key else ""}"><div class="pipe-num">{e(n)}</div><div class="pipe-head">{e(h)}</div>'
        f'<div class="pipe-body">{e(b)}</div>{f"<div class=formula>{e(f)}</div>" if f else ""}</div>'
        for n, h, b, f, key in pipe
    )
    spec = [
        ("Tipo de modelo", "Regresión de supervivencia en tiempo discreto: un modelo lineal generalizado binomial"),
        ("Cómo se lee", "exp(β) es una razón de riesgos: cuántas veces más riesgo mensual, con todo lo demás igual"),
        ("Tamaño", f"{d['params']} coeficientes; penalización L2 elegida en una validación previa a cada prueba"),
        ("Señales", "Nivel, antigüedad, cambio de manager, mes del año y tendencia anual; sin segmento ni job family"),
        ("Entrenamiento", "Con conteos agregados por grupo; no usa filas individuales ni publica puntajes"),
        ("Validación", f"4 periodos de prueba ({d['first_test']} a {d['last_test']}), cada uno entrenado sólo con el pasado"),
    ]
    spec_html = "".join(f"<div><b>{e(k)}</b><span>{e(v)}</span></div>" for k, v in spec)
    slides.append(slide(
        2,
        heading(
            "Es una regresión: modela el riesgo de salir en cada mes y de ahí calcula el riesgo a 6 meses",
            "Modelo de hazard discreto, también llamado regresión de supervivencia en tiempo discreto (Allison 1982; Singer y Willett 1993)",
        )
        + f'<div style="display:flex;flex-direction:column;gap:22px;align-self:center;"><div class="pipe">{pipe_html}</div>'
        f'<article class="card" style="padding:18px 22px;"><div class="spec">{spec_html}</div></article></div>'
        f'<div class="src">Fuente: {SOURCE} (tools/critical_tech_model_comparison_rolling_noseg.py). '
        f'Riesgo mensual = salida voluntaria antes de la siguiente foto mensual.</div>',
    ))

    # 4. Los grupos que genera (foto actual)
    groups = {(g["level_grouped"], g["company_tenure_band"]): g for g in d["groups_now"]}
    top_keys = {(g["level_grouped"], g["company_tenure_band"]) for g in d["groups_now"][:5]}
    lo = min(g["predicted_percent"] for g in d["groups_now"])
    hi = max(g["predicted_percent"] for g in d["groups_now"])
    head = "".join(f"<th>{e(TENURE_LABELS[t])}</th>" for t in TENURE_ORDER)
    body = ""
    for level in LEVEL_ORDER:
        cells = ""
        for tenure in TENURE_ORDER:
            g = groups.get((level, tenure))
            if g is None:
                cells += '<td class="empty">menos de 30</td>'
                continue
            style, dark = heat_color(g["predicted_percent"], lo, hi)
            color = " color: var(--text-invert);" if dark else ""
            top = ' class="top"' if (level, tenure) in top_keys else ""
            cells += (
                f'<td{top} style="{style}{color}"><b>{fmt(g["predicted_percent"])}%</b>'
                f'<span>{g["people_per_snapshot"]:,} personas</span></td>'
            )
        body += f'<tr><th class="rowh">{e(LEVEL_LABELS[level])}</th>{cells}</tr>'
    first = d["groups_now"][0]
    slides.append(slide(
        3,
        heading(
            f"El modelo genera {len(d['groups_now'])} grupos de nivel × antigüedad; los 5 de mayor riesgo reúnen {fmt(round(d['top5_people']))}% "
            f"de las personas y {fmt(round(d['top5_exits']))}% de las salidas esperadas",
            f"% que se estima saldrá en 6 meses, por grupo · foto del {day_label(cur['snapshot'])} · modelo entrenado con toda la historia · {cur['people']:,} personas",
        )
        + f'<div class="s4v3-grid"><article class="card" style="justify-content:center;padding:14px 20px;">'
        f'<table class="heat"><thead><tr><th></th>{head}</tr></thead><tbody>{body}</tbody></table>'
        f'<div class="eff-foot" style="text-align:center;">Antigüedad en la empresa · el recuadro marca los 5 grupos de mayor riesgo</div></article>'
        f'<article class="card" style="justify-content:center;gap:20px;padding:24px;">'
        f'<div class="kpi"><b>{fmt(cur["mean_predicted_percent"])}%</b><span>riesgo promedio a 6 meses en Critical Tech</span></div>'
        f'<div class="kpi"><b>{fmt(first["predicted_percent"])}%</b><span>el grupo más alto: {e(group_label(first))}</span></div>'
        f'<div class="side-body">El riesgo más alto está en los niveles de entrada con 1 a 7 años de antigüedad. '
        f'Senior & Lead con 3 a 7 años es el grupo más grande ({fmt(groups[("7 - Senior & Lead", "3-7 years")]["people_share_percent"])}% de las personas).</div>'
        f'<div class="note-box">Es el promedio de cada grupo; dentro de un grupo el riesgo cambia con el cambio de manager. '
        f'Con lo visto en la prueba, el nivel real puede ser algo mayor (diapositiva 12).</div></article></div>'
        f'<div class="src">Grupos con menos de 30 personas no se muestran. Riesgo a 6 meses desde la foto más reciente con datos mensuales completos. Fuente: {SOURCE}.</div>',
    ))

    # 5. Estimado vs real por grupo, último periodo de prueba
    tg = d["test_groups"]
    scale = 6.0
    rows = []
    for g in tg:
        p, o = g["predicted_percent"], g["observed_percent"]
        gap = " gap" if o - p >= 1.0 else ""
        left, right = sorted([p, o])
        rows.append(
            f'<div class="db-row{gap}"><div class="db-label">{e(group_label(g))}</div><div class="db-track">'
            f'<div class="db-line" style="left:{left / scale * 100:.2f}%;width:{(right - left) / scale * 100:.2f}%"></div>'
            f'<div class="db-dot obs" style="left:{o / scale * 100:.2f}%"></div><div class="db-dot pred" style="left:{p / scale * 100:.2f}%"></div></div>'
            f'<div class="db-val">est. {fmt(p)} · real {fmt(o)}</div></div>'
        )
    axis = "".join(f'<span style="left:{v / scale * 100:.2f}%">{v}%</span>' for v in range(0, 7))
    gaps = [g for g in tg if g["observed_percent"] - g["predicted_percent"] >= 1.0]
    close = [g for g in tg if abs(g["observed_percent"] - g["predicted_percent"]) < 1.0]
    close_people = sum(g["people_share_percent"] for g in close)
    under_one_gaps = sum(g["company_tenure_band"] == "<1 year" for g in gaps)
    slides.append(slide(
        4,
        heading(
            f"En la prueba, {len(close)} de {len(tg)} grupos quedaron a menos de 1 punto de lo real; "
            f"falla sobre todo en quienes tienen menos de 1 año en niveles Senior o superiores",
            f"% que salió en 6 meses: estimado por el modelo contra real · periodo de prueba {d['last_start']} a {d['last_test']} · entrenado con fotos hasta {d['train_end']}",
        )
        + f'<div class="db-grid"><article class="card" style="justify-content:center;gap:3px;padding:10px 22px;">'
        f'<div class="legend" style="margin-bottom:2px;font-size:14px;"><span class="dot-pred">Estimado</span><span class="dot-obs">Real</span><span class="gap">Real 1 punto o más arriba</span></div>'
        f'<div class="db-head"><div style="text-align:right;">Grupo (nivel · antigüedad)</div><div></div><div>%</div></div>'
        f'{"".join(rows)}<div class="db-head"><div></div><div class="db-axis">{axis}</div><div></div></div></article>'
        f'<article class="card" style="justify-content:center;gap:16px;padding:24px;">'
        f'<div class="kpi"><b>{fmt(round(close_people))}%</b><span>de las personas está en grupos donde el estimado quedó a menos de 1 punto del real</span></div>'
        f'<div class="side-body">El orden se sostiene: los grupos con más riesgo estimado son los que más salidas tuvieron.</div>'
        f'<div class="note-box">{under_one_gaps} de los {len(gaps)} grupos que se quedan cortos tienen menos de 1 año. '
        f'Necesitamos señales de carrera para separarlos (próximos pasos).</div></article></div>'
        f'<div class="src">Grupos con 30+ personas por foto y 30+ salidas; {d["hidden_groups"]} grupos con menos salidas no se muestran. '
        f'Ordenados por riesgo estimado. Fuente: {SOURCE}.</div>',
    ))

    # 6. Efectos
    lo_e, hi_e = -70.0, 70.0
    slides.append(slide(
        5,
        heading(
            "Con todo lo demás igual, 3 a 7 años de antigüedad tiene 1.6 veces el riesgo mensual de 7 o más, y el riesgo baja al subir de nivel",
            f"Cambio del riesgo mensual frente a la categoría de referencia · modelo entrenado con fotos hasta {d['train_end']} · asociaciones, no causas",
        )
        + '<div class="eff-grid">'
        + effect_panel("Antigüedad en la empresa", d["tenure"], lo_e, hi_e,
                       "Los primeros 12 meses tienen menos riesgo que 7+ años al ajustar por nivel; en la prueba se quedó corto en ese grupo.", wide=True)
        + effect_panel("Nivel", d["levels"], lo_e, hi_e,
                       f"Sólo niveles con 30+ salidas en entrenamiento; Sr Director se estima con {d['srdir_events']}. VP no tiene coeficiente propio.", wide=True)
        + "</div>"
        f'<div class="src">Lectura: +61% significa 1.6 veces el riesgo mensual de la referencia, en el mismo mes y con las demás señales iguales. '
        f'Cambio de manager: dato sólo para el {fmt(d["manager_share"])}% de las personas-mes; su coeficiente ({pct_change(d["manager_ratio"])}) no es confiable. Fuente: {SOURCE}.</div>',
    ))

    # 7. Calendario
    months = d["months"]
    m_lo, m_hi = -80.0, 80.0
    span = m_hi - m_lo
    zero_from_bottom = -m_lo / span * 100
    cols = []
    for i, ratio in enumerate(months):
        change = (ratio - 1.0) * 100
        h = abs(change) / span * 100
        is_ref = i == 6
        cls = "ref" if is_ref else ("pos" if change > 0 else "neg")
        if change >= 0:
            bar = f'<div class="bar" style="bottom:{zero_from_bottom:.2f}%;height:{h:.2f}%"></div>'
            val = f'<div class="val" style="bottom:calc({zero_from_bottom + h:.2f}% + 4px)">{"ref." if is_ref else pct_change(ratio)}</div>'
        else:
            bar = f'<div class="bar" style="bottom:{zero_from_bottom - h:.2f}%;height:{h:.2f}%"></div>'
            val = f'<div class="val" style="top:calc({100 - zero_from_bottom + h:.2f}% + 4px)">{pct_change(ratio)}</div>'
        cols.append(f'<div class="mcol {cls}">{bar}{val}</div>')
    labels = "".join(f"<div>{m}</div>" for m in MONTHS)
    trend_pct = round((1 - d["trend"]) * 100)
    slides.append(slide(
        6,
        heading(
            "El riesgo mensual cambia con el calendario: mayo y febrero son los meses más altos y octubre el más bajo",
            f"Cambio del riesgo mensual frente a julio, con las demás señales iguales · fotos hasta {d['train_end']} · todo Critical Tech",
        )
        + f'<div class="s4-grid"><article class="card" style="padding:22px 26px;"><div class="mbars"><div class="mzero" style="bottom:{zero_from_bottom:.2f}%"></div>{"".join(cols)}</div>'
        f'<div class="mlabels">{labels}</div></article>'
        f'<article class="card" style="justify-content:center;gap:16px;padding:24px;"><div class="side-head">Además, una tendencia anual</div>'
        f'<div class="big-num">−{trend_pct}%</div>'
        f'<div class="side-body">por año en el riesgo mensual hasta {d["train_end"]}, con todo lo demás igual.</div>'
        f'<div class="note-box">En 2025-26 la attrition volvió a subir; por eso el modelo estima un nivel algo bajo (diapositiva 12).</div></article></div>'
        f'<div class="src">Octubre se estima con {d["oct_events"]} salidas de entrenamiento; es el mes menos preciso. Fuente: {SOURCE}.</div>',
    ))

    # 8. Cómo calcula
    ref, ex = d["reference"], d["example"]
    ref_m = [10 * h for h in ref["monthly_hazard_percent"]]
    ex_m = [10 * h for h in ex["monthly_hazard_percent"]]
    top = max(ex_m) * 1.2

    def ex_card(tag: str, who: str, monthly: list[float], six: float, hl: bool) -> str:
        bars = "".join(f'<div class="ex-bar"><span>{fmt(v)}</span><i style="height:{v / top * 100:.2f}%"></i></div>' for v in monthly)
        names = "".join(f"<div>{m}</div>" for m in d["month_names"])
        return (
            f'<article class="card ex-card{" hl" if hl else ""}"><div class="ex-tag">{e(tag)}</div><div class="ex-who">{e(who)}</div>'
            f'<div class="section-head" style="font-size:12.5px;">Salidas esperadas por cada 1,000 personas, por mes</div>'
            f'<div class="ex-bars">{bars}</div><div class="ex-months">{names}</div>'
            f'<div class="ex-total"><b>{fmt(six)}%</b><span>riesgo de salir en los 6 meses</span></div></article>'
        )

    steps = [
        "El modelo estima el riesgo de cada mes con la fórmula de la regresión.",
        f"Pasar de 7+ a 3 a 7 años de antigüedad multiplica el riesgo de cada mes por {fmt(d['example_ratio'])}.",
        "El mes del año sube o baja ambas curvas por igual: octubre es el más bajo.",
        "Se encadenan los 6 meses para obtener el riesgo a 6 meses; así se llena cada casilla del mapa de grupos.",
    ]
    steps_html = "".join(f"<li>{e(x)}</li>" for x in steps)
    level = LEVEL_LABELS[ref["levels"]["level_grouped"]]
    slides.append(slide(
        7,
        heading(
            f"Así calcula: con las mismas reglas, Senior & Lead pasa de {fmt(ref['six_month_risk_percent'])}% a {fmt(ex['six_month_risk_percent'])}% "
            f"de riesgo a 6 meses si tiene 3 a 7 años en vez de 7 o más",
            f"Dos grupos ilustrativos, no personas · predicción desde la foto de {d['last_start']} · cambio de manager sin dato en ambos",
        )
        + '<div class="ex-grid">'
        + ex_card("Grupo de referencia", f"{level} · {TENURE_LABELS['7+ years']}", ref_m, ref["six_month_risk_percent"], False)
        + ex_card("Mismo nivel, otra antigüedad", f"{level} · {TENURE_LABELS['3-7 years']}", ex_m, ex["six_month_risk_percent"], True)
        + f'<article class="card" style="justify-content:center;gap:14px;"><div class="side-head">Paso a paso</div><ul class="steps-list">{steps_html}</ul></article>'
        + "</div>"
        f'<div class="src">Fuente: coeficientes y riesgo base del modelo del último periodo de prueba, {SOURCE}.</div>',
    ))

    # 9. Cómo medimos el orden
    cap = d["capture"]
    points = [10, 20, 30, 40, 50]
    cap_top = 70.0
    pairs = "".join(
        f'<div class="cal-pair"><div class="cal-bar cap-bar rand"><span>{p}</span><i style="height:{p / cap_top * 100:.2f}%"></i></div>'
        f'<div class="cal-bar cap-bar model"><span>{round(cap[p])}</span><i style="height:{cap[p] / cap_top * 100:.2f}%"></i></div></div>'
        for p in points
    )
    cap_labels = "".join(f"<div>{p}% de mayor riesgo</div>" for p in points)
    how = [
        "El modelo da a cada grupo un riesgo; todas las personas del grupo comparten ese riesgo.",
        "Ordenamos a las personas de mayor a menor riesgo estimado, con datos hasta el inicio de la prueba.",
        "Tomamos el 10% de arriba y contamos cuántas de las salidas reales de los 6 meses siguientes estaban ahí.",
    ]
    how_html = "".join(f"<li>{e(x)}</li>" for x in how)
    slides.append(slide(
        8,
        heading(
            f"Cómo medimos si ordena bien: en el 10% de personas con mayor riesgo estimado estaban {round(cap[10])} de cada 100 salidas; al azar serían 10",
            f"De cada 100 salidas reales, cuántas estaban en el x% de personas que el modelo marcó como de mayor riesgo · prueba {d['last_start']} a {d['last_test']}",
        )
        + f'<div class="cap-grid"><article class="card" style="justify-content:center;gap:12px;padding:22px 26px;">'
        f'<div class="legend"><span>Al azar</span><span class="model">Modelo mes a mes</span></div>'
        f'<div class="cap">{pairs}</div><div class="cap-labels">{cap_labels}</div>'
        f'<div class="side-body" style="font-size:15.5px;">Atendiendo a la mitad de mayor riesgo se cubren {round(cap[50])} de cada 100 salidas, no 50.</div></article>'
        f'<article class="card" style="justify-content:center;gap:14px;padding:22px;"><div class="side-head">Qué mide y qué no</div>'
        f'<ul class="steps-list">{how_html}</ul>'
        f'<div class="prec"><b>{fmt(d["top10_rate"])}</b><span>de cada 100 personas de ese 10% salió en 6 meses</span>'
        f'<b class="muted">{fmt(d["observed_last"])}</b><span>de cada 100 en todo Critical Tech</span></div>'
        f'<div class="side-body" style="font-size:15px;">No mide acertar persona por persona: aun en el grupo de mayor riesgo la mayoría se queda. '
        f'Mide si las salidas se concentran donde el modelo dijo.</div></article></div>'
        f'<div class="src">Fuente: último periodo de prueba, {SOURCE}. Es la misma medida de la comparativa siguiente, allí promediada en 4 periodos.</div>',
    ))

    # 10. Comparativa
    scale_max = 20.0
    bar_rows = [("Al azar", 10.0, "")] + [(MODEL_NAMES[k], lift[k], {"hazard": " hl", "hazard_interactions": " hl2"}.get(k, "")) for k in MODELS]
    rows = "".join(
        f'<div class="hrow{hl}"><div class="hlabel">{e(label)}</div><div class="htrack">'
        f'<div class="hfill" style="width:{value / scale_max * 100:.2f}%"></div><div class="hval" style="left:{value / scale_max * 100:.2f}%">{fmt(value)}</div></div></div>'
        for label, value, hl in bar_rows
    )
    head = "".join(f"<th>{month_label(f['test_start'])}</th>" for f in d["folds"])
    table_rows = ""
    for key in MODELS:
        cells = ""
        for i, value in enumerate(d["fold_lifts"][key]):
            best = max(d["fold_lifts"][k][i] for k in MODELS)
            cells += f'<td class="{"win" if value == best else ""}">{fmt(value)}</td>'
        table_rows += f"<tr><td>{SHORT[key]}</td>{cells}</tr>"
    slides.append(slide(
        9,
        heading(
            f"Calculamos los cuatro y ordenan casi igual: entre {fmt(min(lift.values()))} y {fmt(max(lift.values()))} de cada 100 salidas en el 10% de mayor riesgo",
            f"Todo Critical Tech, sin segmento · promedio de 4 periodos de prueba de 6 meses ({d['first_test']} a {d['last_test']}) · cada modelo entrenado sólo con datos previos",
        )
        + f'<div class="s6-grid"><article class="card" style="justify-content:center;gap:14px;padding:22px 26px;">'
        f'<div class="question">De cada 100 salidas reales, ¿cuántas estaban en el 10% de personas que el modelo marcó como de mayor riesgo?</div>'
        f'<div class="hbars">{rows}</div></article>'
        f'<article class="card" style="justify-content:center;gap:12px;padding:20px 22px;"><div class="side-head">Resultado por periodo de prueba</div>'
        f'<table class="wins"><thead><tr><th>Modelo</th>{head}</tr></thead><tbody>{table_rows}</tbody></table>'
        f'<div class="side-body" style="font-size:15.5px;">En negritas, el mejor de cada periodo. El machine learning gana 2 de 4 y pierde por 2 puntos en {month_label(d["folds"][1]["test_start"])}; '
        f'agregar la combinación nivel × antigüedad mejora poco ({d["params_inter"]} coeficientes en vez de {d["params"]}).</div></article></div>'
        f'<div class="src">El promedio histórico no aparece: da el mismo riesgo a todos y no puede ordenar. Diferencias menores a 1 punto no son concluyentes. Fuente: {SOURCE}.</div>',
    ))

    # 11. Matriz
    pred = d["pred_last"]
    cols_m = ["historical", "logistic", "hazard", "lightgbm"]
    matrix_rows = [
        ("De cada 100 salidas, cuántas en el 10% de mayor riesgo (4 periodos)",
         [("text", "No ordena"), ("num", fmt(lift["logistic"])), ("num", fmt(lift["hazard"])), ("num", fmt(lift["lightgbm"]))]),
        (f"Nivel estimado en el último periodo (real: {fmt(d['observed_last'])}%)", [("num", f"{fmt(pred[k])}%") for k in cols_m]),
        ("Sirve para 3, 6 o 12 meses sin reentrenar", [("mark", "part"), ("mark", "no"), ("mark", "yes"), ("mark", "no")]),
        ("Capta la temporada del año", [("mark", "no"), ("mark", "no"), ("mark", "yes"), ("mark", "no")]),
        ("Explica cada efecto con un número", [("mark", "no"), ("mark", "yes"), ("mark", "yes"), ("mark", "part")]),
        ("Se entrena con conteos agregados, sin filas individuales", [("mark", "yes")] * 4),
    ]
    names = ["Promedio histórico", "Logística a 6 meses", "Mes a mes", "Machine learning"]
    head_cells = "".join(f'<th class="{"rec" if i == 2 else ""}">{e(c)}</th>' for i, c in enumerate(names))
    body = ""
    for crit, cells in matrix_rows:
        tds = ""
        for i, (kind, value) in enumerate(cells):
            rec = " rec" if i == 2 else ""
            if kind == "num":
                tds += f'<td class="num{rec}">{e(value)}</td>'
            elif kind == "text":
                tds += f'<td class="{rec.strip()} muted">{e(value)}</td>'
            else:
                icon, text = MARKS[value]
                tds += f'<td class="{rec.strip()}"><span class="mark m-{value}"><i>{icon}</i>{text}</span></td>'
        body += f"<tr><td>{e(crit)}</td>{tds}</tr>"
    slides.append(slide(
        10,
        heading(
            "Con un orden equivalente al de los demás, el modelo mes a mes es el que más necesidades cubre",
            f"Todo Critical Tech, sin segmento · cifras de los 4 periodos de prueba y del último ({d['last_start']} a {d['last_test']})",
        )
        + f'<article class="card" style="align-self:center;padding:14px 22px;"><table class="matrix"><thead><tr><th></th>{head_cells}</tr></thead>'
        f"<tbody>{body}</tbody></table></article>"
        f'<div class="src">Temporada: el LightGBM a 6 meses asignó {fmt(d["lgb_month_gain"])}% de su importancia al mes del año. «Parcial» en machine learning: sólo da importancias '
        f'globales, sin dirección ni tamaño del efecto. El machine learning sobreestima el nivel y la logística lo subestima. Fuente: {SOURCE}.</div>',
    ))

    # 12. Calibración
    cal = d["calibration"]
    top_cal = max(max(b["observed_rate_percent"], b["mean_predicted_percent"]) for b in cal) * 1.18
    cal_pairs = "".join(
        f'<div class="cal-pair"><div class="cal-bar obs"><span>{fmt(b["observed_rate_percent"])}%</span><i style="height:{b["observed_rate_percent"] / top_cal * 100:.2f}%"></i></div>'
        f'<div class="cal-bar pred"><span>{fmt(b["mean_predicted_percent"])}%</span><i style="height:{b["mean_predicted_percent"] / top_cal * 100:.2f}%"></i></div></div>'
        for b in cal
    )
    cal_labels = "".join(f"<div>{t}</div>" for t in ["20% más bajo", "2º", "3º", "4º", "20% más alto"])
    under = d["under_one"]
    gaps_list = [
        f"Aprendió una tendencia a la baja (−{trend_pct}% por año) y en 2025-26 la attrition subió: real {fmt(d['observed_last'])}% contra {fmt(pred['hazard'])}% estimado.",
        f"Menos de 1 año de antigüedad: {fmt(under['observed_rate_percent'])}% real contra {fmt(under['hazard_predicted_percent'])}% estimado.",
        f"Cambio de manager: dato sólo para el {fmt(d['manager_share'])}% de las personas-mes; hoy casi no aporta.",
    ]
    gaps_html = "".join(f"<li>{e(g)}</li>" for g in gaps_list)
    slides.append(slide(
        11,
        heading(
            f"Ordena bien y estima el nivel con poco margen: en el último periodo calculó {fmt(pred['hazard'])}% y ocurrió {fmt(d['observed_last'])}%",
            f"% que sale en 6 meses por quintil de riesgo estimado · {d['last_start']} a {d['last_test']} · {d['last_exposures']:,} personas-mes, {d['last_events']:,} salidas",
        )
        + f'<div class="s8-grid"><article class="card" style="justify-content:center;gap:12px;padding:22px 26px;">'
        f'<div class="legend"><span>Real</span><span class="pred">Estimado por el modelo</span></div>'
        f'<div class="cal">{cal_pairs}</div><div class="cal-labels">{cal_labels}</div>'
        f'<div class="side-body" style="font-size:15.5px;">El riesgo real sube de un quintil al siguiente. Los dos quintiles más altos quedan casi exactos; '
        f'en los tres más bajos el modelo se queda corto.</div></article>'
        f'<article class="card" style="justify-content:center;gap:14px;padding:22px;"><div class="side-head">Dónde se queda corto</div>'
        f'<ul class="gaps">{gaps_html}</ul>'
        f'<div class="fix">Corrección: recalibrar el nivel cada trimestre con los meses más recientes y agregar señales de carrera para el primer año.</div></article></div>'
        f'<div class="src">Quintiles con 30+ salidas cada uno. Fuente: último periodo de prueba, {SOURCE}. Asociaciones, no causas.</div>',
    ))

    # 13. Próximos pasos
    tl = [
        ("Recalibrar el nivel", "Ajustar el riesgo base con los meses más recientes y medir de nuevo en los 4 periodos."),
        ("Agregar señales por bloques", "Carrera, manager y equipo, encuesta QVoice; cada bloque entra sólo si mejora los 4 periodos."),
        ("Mantener el rival de ML", "LightGBM se recalcula con cada bloque; se adopta sólo si gana 3 de 4 periodos sin perder precisión de nivel."),
        ("Piloto por grupos", "Acciones de RH en grupos priorizados de 30+ personas, con métrica y responsable."),
    ]
    tl_html = "".join(
        f'<div class="tl-step"><div class="tl-dot"><b>{i + 1}</b><hr></div><div class="tl-head">{e(h)}</div><div class="tl-body">{e(b)}</div></div>'
        for i, (h, b) in enumerate(tl)
    )
    decisions = [
        "Aprobar la regresión mes a mes por nivel y antigüedad como modelo base.",
        "Confirmar con HR si habrá un mapeo de job family anterior y posterior a sep-2026.",
        "Definir si las salidas «Voluntary Exception» cuentan y autorizar el uso de QVoice.",
    ]
    dec_html = "".join(f'<div class="decision">{e(x)}</div>' for x in decisions)
    slides.append(slide(
        12,
        heading(
            "Antes de usarlo recalibraremos el nivel y agregaremos señales; necesitamos tres decisiones",
            "Del modelo base a un piloto de retención por grupos",
        )
        + f'<article class="card" style="justify-content:center;align-self:center;padding:40px 32px;"><div class="timeline">{tl_html}</div></article>'
        f'<div style="display:flex;flex-direction:column;gap:10px;"><div class="section-head">Decisiones que necesitamos</div>'
        f'<div class="decisions">{dec_html}</div></div>',
    ))
    return slides


def render() -> str:
    d = load_data()
    tpl = v2.TEMPLATE.read_text(encoding="utf-8")
    out = tpl.replace('<html lang="en">', '<html lang="es">', 1)
    out = out.replace("<title>[Slide Title]</title>", "<title>Modelo de attrition voluntaria: qué elegimos y por qué (v3)</title>", 1)
    out = out.replace(
        '<meta charset="UTF-8" />',
        '<meta charset="UTF-8" />\n  <meta name="deliverable-classification" content="presentation" />',
        1,
    )
    marker = "/* 13. CONTENT-SPECIFIC STYLES — add below this line\n       ================================================================== */"
    assert marker in out, "La plantilla cambió: no se encontró CONTENT-SPECIFIC STYLES"
    out = out.replace(marker, marker + CSS, 1)

    body_start = out.index('<body class="theme-light-classic">') + len('<body class="theme-light-classic">')
    nav_start = out.index("  <!-- ================================================================\n       LEFT EDGE")
    out = out[:body_start] + "\n" + "\n".join(build_slides(d)) + "\n\n" + out[nav_start:]

    pills = "\n".join(
        f'      <button class="nav-pill{" pill-active" if i == 0 else ""}" data-slide="{i}">{i + 1}. {e(t)}</button>'
        for i, t in enumerate(NAV)
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
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or (
        ROOT / "output" / "presentations" / f"{datetime.now():%Y%m%d-%H%M}_seleccion-modelo-v3" / "presentacion.html"
    )
    if out.exists():
        raise SystemExit(f"Ya existe {out}; no se sobrescribe.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
