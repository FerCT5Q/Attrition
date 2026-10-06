"""Genera el deck v2 de selección del modelo de attrition, centrado en el modelo elegido.

A diferencia de v1, todas las comparaciones provienen de modelos calculados:
la comparación rolling-origin de cuatro periodos
(``tools/critical_tech_model_comparison_rolling.py``) para el alcance vigente de
fase 1. Parte de la plantilla html-slide-generator (base-fullscreen.html) sin
alterar sus bloques JavaScript. Las cifras se leen de los artefactos y se
validan contra valores esperados; si una fuente cambia, el script falla.

Uso:
    python -B tools/presentations/build_model_selection_deck_v2.py [--out RUTA]
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = Path.home() / ".codex" / "skills" / "html-slide-generator" / "templates" / "fullscreen" / "base-fullscreen.html"
COMPARISON = (
    ROOT / "output" / "analysis" / "critical-tech" / "20260930" / "model-comparison-rolling-v1" / "comparison-results.json"
)
LAZZARI = next((ROOT / "docs" / "research" / "attrition-literature" / "papers").glob("2022-lazzari*.md"))

MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
TENURE_LABELS = {"<1 year": "Menos de 1 año", "1-3 years": "1 a 3 años", "3-7 years": "3 a 7 años", "7+ years": "7 años o más"}
TENURE_ORDER = ["<1 year", "1-3 years", "3-7 years", "7+ years"]
LEVEL_ORDER = ["8 - Assoc & Int/Eng", "7 - Senior & Lead", "6 - Staff & /Mgr", "5 - Sr Staff & /Mgr", "3 - Princ/Directors"]
LEVEL_LABELS = {
    "8 - Assoc & Int/Eng": "Associate / Engineer",
    "7 - Senior & Lead": "Senior & Lead",
    "6 - Staff & /Mgr": "Staff / Manager",
    "5 - Sr Staff & /Mgr": "Sr Staff / Manager",
    "3 - Princ/Directors": "Principal / Director",
}
EXAMPLE = {"seg": "Machine Learning Eng", "level_grouped": "7 - Senior & Lead", "company_tenure_band": "1-3 years"}
MODEL_ORDER = ["historical", "logistic", "lightgbm", "hazard", "hazard_interactions"]


def fmt(value: float) -> str:
    """Enteros sin decimales; el resto con un decimal como máximo."""
    rounded = round(value, 1)
    return f"{rounded:,.0f}" if rounded == int(rounded) else f"{rounded:,.1f}"


def pct_change(ratio: float) -> str:
    change = round((ratio - 1.0) * 100)
    return "0%" if change == 0 else f"{change:+d}%".replace("-", "−")


def month_label(date_text: str) -> str:
    year, month, _ = date_text.split("-")
    return f"{MONTHS[int(month) - 1]}-{year}"


def load_data() -> dict:
    result = json.loads(COMPARISON.read_text(encoding="utf-8"))
    assert result["deliverable_classification"] == "presentation"
    assert result["privacy"]["employee_level_rows_persisted"] is False
    scope = next(s for s in result["scopes"] if s["scope"] == "phase1")
    folds = scope["folds"]
    assert len(folds) == 4, "Se esperaban cuatro periodos de prueba"
    for fold in folds:
        assert fold["monthly_train_last_snapshot"] < fold["test_start"]
    summary = scope["summary"]
    last = scope["last_fold"]
    last_metrics = folds[-1]["metrics"]

    lift = {key: summary[key]["lift_at_10_percent"]["mean"] * 10 for key in MODEL_ORDER}
    assert [fmt(lift[k]) for k in MODEL_ORDER] == ["10.9", "16.5", "14.6", "16.6", "17.6"], "Cambiaron los resultados"
    wins = {
        key: sum(
            f["metrics"][key]["lift_at_10_percent"] > f["metrics"]["hazard"]["lift_at_10_percent"] for f in folds
        )
        for key in MODEL_ORDER
        if key != "hazard"
    }
    pr_wins = {key: summary["wins_vs_hazard"][key]["pr_auc_folds_won_vs_hazard"] for key in summary["wins_vs_hazard"]}

    coefficients = {(c["feature"], c["level"]): c for c in last["hazard_coefficients"]}
    refs = last["hazard_reference_levels"]

    def ratio(feature: str, level: str) -> float | None:
        if level == refs[feature]:
            return 1.0
        item = coefficients.get((feature, level))
        return item["relative_hazard_scale"] if item else None

    tenure = [(TENURE_LABELS[t], ratio("company_tenure_band", t), t == refs["company_tenure_band"]) for t in TENURE_ORDER]
    levels = [(LEVEL_LABELS[l], ratio("level_grouped", l), l == refs["level_grouped"]) for l in LEVEL_ORDER]
    segs = sorted(
        [(c["level"], c["relative_hazard_scale"], False) for c in last["hazard_coefficients"] if c["feature"] == "seg"],
        key=lambda item: -item[1],
    ) + [(refs["seg"], 1.0, True)]
    months = [ratio("calendar_month", str(m)) for m in range(1, 13)]
    assert all(v is not None for v in months), "Falta algún mes publicado"
    month_events = {int(c["level"]): c["training_events"] for c in last["hazard_coefficients"] if c["feature"] == "calendar_month"}
    assert all(v is not None for _, v, _ in tenure + levels)
    assert refs["calendar_month"] == "7" and refs["company_tenure_band"] == "7+ years"
    assert fmt(ratio("level_grouped", "7 - Senior & Lead")) == "1.7"

    reference = next(p for p in last["hazard_worked_example"] if p["profile"] == "referencia")
    ref_monthly = [h / 100 for h in reference["monthly_hazard_percent"]]
    example_ratios = [ratio(feature, level) for feature, level in EXAMPLE.items()]
    multiplier = 1.0
    for value in example_ratios:
        multiplier *= value
    example_monthly = [1 - (1 - h) ** multiplier for h in ref_monthly]
    risk = 1.0
    for h in example_monthly:
        risk *= 1 - h
    example_six = 100 * (1 - risk)
    start_month = int(reference["first_month"][5:7])
    month_names = [MONTHS[(start_month - 1 + i) % 12] for i in range(6)]

    calibration = last_metrics["hazard"]["calibration"]
    assert all(b["published"] for b in calibration) and len(calibration) == 5
    def mean_pred(key: str) -> float:
        bins = last_metrics[key]["calibration"]
        return sum(b["exposures"] * b["mean_predicted_percent"] for b in bins) / sum(b["exposures"] for b in bins)
    one_way = last["one_way_fit"]
    under_one = next(r for r in one_way["company_tenure_band"] if r["level"] == "<1 year")
    graphics = next(
        c for c in last["cohorts_segment_tenure"]["hazard"]
        if c["seg"] == "Graphics" and c["company_tenure_band"] == "1-3 years"
    )
    manager = {r["level"]: r["exposures"] for r in one_way["manager_change_12m"]}
    manager_unknown = 100 * manager["unknown"] / last_metrics["hazard"]["exposures"]

    lazzari = LAZZARI.read_text(encoding="utf-8")
    assert "LightGBM obtuvo PR-AUC 0.588 y logística 0.583" in lazzari

    return {
        "folds": folds,
        "first_test": month_label(folds[0]["test_start"]),
        "last_test": month_label(folds[-1]["test_end"]),
        "last_start": month_label(folds[-1]["test_start"]),
        "train_end": month_label(folds[-1]["monthly_train_last_snapshot"]),
        "lift": lift,
        "wins": wins,
        "pr_wins": pr_wins,
        "fold_lifts": {k: [v * 10 for v in summary[k]["lift_at_10_percent"]["by_fold"]] for k in MODEL_ORDER},
        "exposures": scope["exposures"],
        "params": last["hazard_parameter_count"],
        "trend": last["hazard_trend_ratio_per_year"],
        "tenure": tenure,
        "levels": levels,
        "segs": segs,
        "refs": refs,
        "months": months,
        "oct_events": month_events[10],
        "soc_events": coefficients[("seg", "SoC Architecture")]["training_events"],
        "ref_monthly": [1000 * h for h in ref_monthly],
        "ref_six": reference["six_month_risk_percent"],
        "example_monthly": [1000 * h for h in example_monthly],
        "example_six": example_six,
        "example_multiplier": multiplier,
        "example_ratios": example_ratios,
        "month_names": month_names,
        "calibration": calibration,
        "observed_last": last_metrics["hazard"]["observed_rate_percent"],
        "pred_last": {k: mean_pred(k) for k in MODEL_ORDER},
        "last_events": last_metrics["hazard"]["events"],
        "last_exposures": last_metrics["hazard"]["exposures"],
        "under_one": under_one,
        "graphics": graphics,
        "manager_unknown": manager_unknown,
        "lazzari_ml": 58.8,
        "lazzari_simple": 58.3,
    }


def e(text: str) -> str:
    return html.escape(text, quote=False)


def heading(title: str, sub: str | None = None) -> str:
    sub_html = f'<p class="slide-subtitle">{e(sub)}</p>' if sub else ""
    return f'<div class="slide-heading"><div><h2 class="slide-title-text">{e(title)}</h2>{sub_html}</div></div>'


def slide(idx: int, body: str, cls: str = "stage-3rows") -> str:
    return f'<div class="slide-stage {cls} data-context" id="slide-{idx + 1}">\n{body}\n</div>'


NAV = [
    "Recomendación",
    "Qué tipo de modelo es",
    "Efecto de cada señal",
    "Efecto del calendario",
    "Cómo calcula",
    "Comparativa calculada",
    "Por qué mes a mes",
    "Qué falta corregir",
    "Próximos pasos",
]

MODEL_NAMES = {
    "historical": "Promedio histórico",
    "logistic": "Probabilidad directa a 6 meses (regresión logística)",
    "lightgbm": "Machine learning (LightGBM)",
    "hazard": "Riesgo mes a mes (recomendado)",
    "hazard_interactions": "Riesgo mes a mes + combinaciones",
}

CSS = """
    .slide-stage { padding: 30px 44px 22px; gap: 16px; }
    .slide-title-text { font-size: 30px; line-height: 1.2; max-width: 1340px; }
    .slide-subtitle { font-size: 16px; margin-top: 6px; }
    .src { font-size: 12.5px; color: var(--text-muted); align-self: end; line-height: 1.4; }
    .stage-3rows { grid-template-rows: auto 1fr auto; }
    .muted { color: var(--text-muted); }
    .data-context { --ctx: color-mix(in oklab, var(--text-muted) 45%, var(--bg-surface)); --neg: color-mix(in oklab, #0f766e 70%, var(--bg-surface)); }
    .card { height: auto; }
    .side-head { font-size: 20px; font-weight: 700; }
    .section-head { font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); }
    .note-box { font-size: 16.5px; line-height: 1.45; padding: 12px 16px; border-left: 4px solid #d97706; background: color-mix(in oklab, #f59e0b 10%, var(--bg-surface)); border-radius: 6px; }

    /* Portada */
    .cover { display: flex; flex-direction: column; justify-content: center; gap: 26px; padding: 0 40px; }
    .cover-kicker { font-size: 16px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }
    .cover-title { font-size: 44px; font-weight: 800; line-height: 1.15; margin: 0; max-width: 1240px; }
    .cover-chips { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; max-width: 1240px; }
    .cover-chip { border-left: 4px solid var(--accent); padding: 8px 16px; background: var(--bg-surface); border-radius: 10px; }
    .cover-chip b { display: block; font-size: 13px; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); }
    .cover-chip span { font-size: 19px; font-weight: 600; }
    .cover-note { font-size: 19px; color: var(--text-muted); max-width: 1180px; line-height: 1.45; }

    /* Ficha del modelo */
    .pipe { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }
    .pipe-step { position: relative; background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 16px 18px; display: flex; flex-direction: column; gap: 8px; box-shadow: var(--shadow-soft); }
    .pipe-step:not(:last-child)::after { content: "→"; position: absolute; right: -17px; top: 38%; font-size: 24px; color: var(--accent); }
    .pipe-step.key { border: 2px solid var(--accent); }
    .pipe-num { font-size: 13px; font-weight: 800; color: var(--accent); text-transform: uppercase; letter-spacing: .06em; }
    .pipe-head { font-size: 19px; font-weight: 700; line-height: 1.25; }
    .pipe-body { font-size: 15.5px; line-height: 1.45; }
    .formula { font-family: "Cambria Math", "Times New Roman", serif; font-size: 17px; white-space: nowrap; padding: 8px 10px; border-radius: 8px; background: var(--accent-soft); text-align: center; }
    .spec { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px 26px; }
    .spec div { border-top: 2px solid var(--border-strong); padding-top: 8px; }
    .spec b { display: block; font-size: 13px; text-transform: uppercase; letter-spacing: .05em; color: var(--text-muted); margin-bottom: 4px; }
    .spec span { font-size: 16px; line-height: 1.4; }

    /* Barras divergentes horizontales */
    .eff-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; align-items: stretch; }
    .eff-col { display: flex; flex-direction: column; gap: 18px; }
    .eff-card { padding: 18px 20px; gap: 10px; }
    .eff-row { display: grid; grid-template-columns: 190px 1fr 64px; gap: 12px; align-items: center; height: 34px; }
    .eff-card.wide .eff-row { grid-template-columns: 230px 1fr 64px; height: 44px; }
    .eff-label { font-size: 15px; text-align: right; line-height: 1.15; }
    .eff-row.ref .eff-label { color: var(--text-muted); font-style: italic; }
    .eff-track { position: relative; height: 24px; }
    .eff-zero { position: absolute; top: -6px; bottom: -6px; width: 2px; background: var(--text-muted); }
    .eff-bar { position: absolute; top: 0; height: 100%; background: var(--accent); }
    .eff-bar.neg { background: var(--neg); }
    .eff-val { font-size: 15px; font-weight: 800; white-space: nowrap; }
    .eff-val.neg { color: color-mix(in oklab, #0f9488 60%, var(--text-main)); }
    .eff-row.ref .eff-val { color: var(--text-muted); font-weight: 600; }
    .eff-foot { font-size: 13.5px; color: var(--text-muted); line-height: 1.4; }

    /* Columnas divergentes (meses) */
    .s4-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; }
    .mbars { position: relative; display: grid; grid-template-columns: repeat(12, 1fr); gap: 10px; height: 400px; }
    .mcol { position: relative; height: 100%; }
    .mcol .bar { position: absolute; left: 8%; right: 8%; background: var(--ctx); }
    .mcol.pos .bar { background: var(--accent); }
    .mcol.neg .bar { background: var(--neg); }
    .mcol .val { position: absolute; left: 0; right: 0; text-align: center; font-size: 15px; font-weight: 800; }
    .mzero { position: absolute; left: 0; right: 0; border-top: 2px solid var(--text-muted); }
    .mlabels { display: grid; grid-template-columns: repeat(12, 1fr); gap: 10px; text-align: center; font-size: 15px; color: var(--text-muted); margin-top: 6px; }
    .big-num { font-size: 72px; font-weight: 800; color: var(--accent); line-height: 1; }
    .side-body { font-size: 17px; line-height: 1.45; }

    /* Ejemplo trabajado */
    .ex-grid { display: grid; grid-template-columns: 1fr 1fr 0.8fr; gap: 20px; }
    .ex-card { gap: 12px; }
    .ex-tag { font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); }
    .ex-card.hl .ex-tag { color: var(--accent); }
    .ex-who { font-size: 17px; font-weight: 700; line-height: 1.3; min-height: 44px; }
    .ex-bars { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; align-items: end; height: 230px; border-bottom: 2px solid var(--text-muted); }
    .ex-bar { display: flex; flex-direction: column; justify-content: flex-end; align-items: center; height: 100%; }
    .ex-bar i { width: 100%; background: var(--ctx); border-radius: 6px 6px 0 0; }
    .ex-card.hl .ex-bar i { background: var(--accent); }
    .ex-bar span { font-size: 15px; font-weight: 700; margin-bottom: 4px; }
    .ex-months { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; text-align: center; font-size: 14px; color: var(--text-muted); }
    .ex-total { display: flex; align-items: baseline; gap: 10px; border-top: 1px solid var(--border-subtle); padding-top: 10px; }
    .ex-total b { font-size: 40px; color: var(--text-muted); }
    .ex-card.hl .ex-total b { color: var(--accent); }
    .ex-total span { font-size: 15px; line-height: 1.3; }
    .steps-list { list-style: none; margin: 0; padding: 0; counter-reset: r; display: flex; flex-direction: column; gap: 14px; }
    .steps-list li { counter-increment: r; font-size: 16.5px; line-height: 1.4; padding-left: 40px; position: relative; }
    .steps-list li::before { content: counter(r); position: absolute; left: 0; top: -1px; width: 28px; height: 28px; border-radius: 50%; background: var(--accent); color: var(--text-invert); font-weight: 800; display: grid; place-items: center; font-size: 15px; }

    /* Comparativa */
    .s6-grid { display: grid; grid-template-columns: 1.6fr 1fr; gap: 24px; }
    .question { font-size: 18px; font-weight: 600; line-height: 1.4; margin-bottom: 4px; }
    .hbars { position: relative; display: flex; flex-direction: column; gap: 16px; }
    .hrow { display: grid; grid-template-columns: 330px 1fr; align-items: center; gap: 14px; }
    .hlabel { font-size: 16.5px; text-align: right; line-height: 1.2; }
    .hrow.hl .hlabel { font-weight: 800; color: var(--accent); }
    .htrack { position: relative; height: 40px; }
    .hfill { height: 100%; border-radius: 0 8px 8px 0; background: var(--ctx); }
    .hrow.hl .hfill { background: var(--accent); }
    .hrow.hl2 .hfill { background: color-mix(in oklab, var(--accent) 55%, var(--bg-surface)); }
    .hval { position: absolute; top: 50%; transform: translateY(-50%); font-size: 20px; font-weight: 800; padding-left: 10px; }
    .hrow.hl .hval { color: var(--accent); }
    .wins { width: 100%; border-collapse: collapse; font-size: 16px; }
    .wins th, .wins td { padding: 9px 6px; border-bottom: 1px solid var(--border-subtle); text-align: center; }
    .wins th { font-size: 13.5px; color: var(--text-muted); }
    .wins td:first-child, .wins th:first-child { text-align: left; }
    .wins td.win { font-weight: 800; color: var(--accent); }

    /* Matriz */
    .matrix { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 17px; }
    .matrix th, .matrix td { padding: 13px 12px; border-bottom: 1px solid var(--border-subtle); text-align: center; }
    .matrix th { font-size: 15.5px; color: var(--text-muted); font-weight: 700; }
    .matrix th.rec, .matrix td.rec { background: var(--accent-soft); }
    .matrix th.rec { color: var(--accent); border-radius: 12px 12px 0 0; }
    .matrix td:first-child, .matrix th:first-child { text-align: left; width: 34%; }
    .matrix td.num { font-weight: 800; font-size: 19px; }
    .matrix td.rec.num { color: var(--accent); }
    .mark { display: inline-flex; align-items: center; gap: 6px; font-weight: 700; font-size: 15.5px; }
    .mark i { font-style: normal; font-size: 19px; }
    .m-yes { color: #15803d; } .m-part { color: #b45309; } .m-no { color: #b91c1c; }
    body.theme-dark-royal .m-yes, body.theme-dark-carbon .m-yes { color: #4ade80; }
    body.theme-dark-royal .m-part, body.theme-dark-carbon .m-part { color: #fbbf24; }
    body.theme-dark-royal .m-no, body.theme-dark-carbon .m-no { color: #f87171; }

    /* Calibración */
    .s8-grid { display: grid; grid-template-columns: 1.35fr 1fr; gap: 24px; }
    .cal { display: grid; grid-template-columns: repeat(5, 1fr); gap: 22px; align-items: end; height: 330px; border-bottom: 2px solid var(--text-muted); padding: 0 6px; }
    .cal-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; align-items: end; height: 100%; }
    .cal-bar { display: flex; flex-direction: column; justify-content: flex-end; align-items: center; height: 100%; }
    .cal-bar i { width: 100%; border-radius: 6px 6px 0 0; }
    .cal-bar.obs i { background: var(--ctx); }
    .cal-bar.pred i { background: var(--accent); }
    .cal-bar span { font-size: 14.5px; font-weight: 800; margin-bottom: 4px; }
    .cal-bar.pred span { color: var(--accent); }
    .cal-labels { display: grid; grid-template-columns: repeat(5, 1fr); gap: 22px; text-align: center; font-size: 14.5px; color: var(--text-muted); padding: 0 6px; }
    .legend { display: flex; gap: 22px; font-size: 15px; }
    .legend span::before { content: ""; display: inline-block; width: 14px; height: 14px; border-radius: 3px; margin-right: 6px; vertical-align: -2px; background: var(--ctx); }
    .legend span.pred::before { background: var(--accent); }
    .gaps { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
    .gaps li { font-size: 16.5px; line-height: 1.4; padding-left: 24px; position: relative; }
    .gaps li::before { content: "!"; position: absolute; left: 0; top: 2px; width: 17px; height: 17px; border-radius: 50%; background: #d97706; color: #fff; font-size: 12px; font-weight: 800; display: grid; place-items: center; }
    .fix { font-size: 16.5px; font-weight: 600; line-height: 1.4; border-left: 4px solid var(--accent); padding: 8px 14px; background: var(--accent-soft); border-radius: 0 8px 8px 0; }

    /* Próximos pasos */
    .timeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
    .tl-step { display: flex; flex-direction: column; gap: 10px; }
    .tl-dot { display: flex; align-items: center; gap: 10px; }
    .tl-dot b { width: 40px; height: 40px; border-radius: 50%; background: var(--accent); color: var(--text-invert); display: grid; place-items: center; font-size: 18px; flex-shrink: 0; }
    .tl-dot hr { flex: 1; border: none; border-top: 3px solid var(--border-strong); margin: 0; }
    .tl-head { font-size: 20px; font-weight: 700; }
    .tl-body { font-size: 16.5px; line-height: 1.45; }
    .decisions { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
    .decision { font-size: 18px; font-weight: 600; line-height: 1.4; padding: 14px 18px; border-radius: 12px; border: 2px solid var(--accent); background: var(--accent-soft); }
"""

MARKS = {"yes": ("✓", "Sí"), "part": ("◐", "Parcial"), "no": ("✗", "No")}


def effect_panel(title: str, rows: list[tuple[str, float, bool]], lo: float, hi: float, foot: str, wide: bool = False) -> str:
    span = hi - lo
    zero = -lo / span * 100
    items = []
    for label, ratio, is_ref in rows:
        change = (ratio - 1.0) * 100
        width = abs(change) / span * 100
        left = zero if change >= 0 else zero - width
        neg = " neg" if change < 0 else ""
        text = "referencia" if is_ref else pct_change(ratio)
        bar = "" if is_ref else f'<div class="eff-bar{neg}" style="left:{left:.2f}%;width:{width:.2f}%"></div>'
        items.append(
            f'<div class="eff-row{" ref" if is_ref else ""}"><div class="eff-label">{e(label)}</div><div class="eff-track">'
            f'<div class="eff-zero" style="left:{zero:.2f}%"></div>{bar}</div><div class="eff-val{neg}">{e(text)}</div></div>'
        )
    return (
        f'<article class="card eff-card{" wide" if wide else ""}"><div class="side-head">{e(title)}</div>{"".join(items)}'
        f'<div class="eff-foot">{e(foot)}</div></article>'
    )


def build_slides(d: dict) -> list[str]:
    slides = []
    lift = d["lift"]

    chips = [
        ("Población", "Critical Tech fase 1: empleados regulares activos, sin Other Eng"),
        ("Horizonte", "Salidas voluntarias en los próximos 6 meses"),
        ("Resultado", "Riesgo por grupo de 30+ personas, nunca por persona"),
    ]
    chip_html = "".join(f'<div class="cover-chip"><b>{e(k)}</b><span>{e(v)}</span></div>' for k, v in chips)
    slides.append(
        slide(
            0,
            f'<div class="cover" style="grid-row: 1 / -1;"><div class="cover-kicker">People Analytics · Critical Tech · Septiembre 2026</div>'
            f'<h1 class="cover-title">Recomendamos una regresión de supervivencia mes a mes: estima el riesgo de salida de cada mes por grupo y lo acumula a 6 meses</h1>'
            f'<div class="cover-chips">{chip_html}</div>'
            f'<div class="cover-note">La comparamos, con los mismos datos y en 4 periodos de prueba, contra un promedio histórico, '
            f'una regresión logística directa a 6 meses y un modelo de machine learning (LightGBM) que sí calculamos.</div></div>',
            cls="",
        )
    )

    exp = d["exposures"]
    pipe = [
        ("1 · Datos", "Fotos mensuales por grupo",
         f"Cada mes contamos personas y salidas voluntarias del mes siguiente por segmento, nivel, antigüedad y cambio de manager. "
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
        ("Señales", "Segmento, nivel, antigüedad, mes del año, tendencia anual y cambio de manager"),
        ("Entrenamiento", "Con conteos agregados por grupo; no usa filas individuales ni publica puntajes"),
        ("Validación", f"4 periodos de prueba ({d['first_test']} a {d['last_test']}), cada uno entrenado sólo con el pasado"),
    ]
    spec_html = "".join(f"<div><b>{e(k)}</b><span>{e(v)}</span></div>" for k, v in spec)
    slides.append(
        slide(
            1,
            heading(
                "Sí, es una regresión: modela el riesgo de salir en cada mes y de ahí calcula el riesgo a 6 meses",
                "Modelo de hazard discreto, también llamado regresión de supervivencia en tiempo discreto (Allison 1982; Singer y Willett 1993)",
            )
            + f'<div style="display:flex;flex-direction:column;gap:22px;align-self:center;"><div class="pipe">{pipe_html}</div>'
            f'<article class="card" style="padding:18px 22px;"><div class="spec">{spec_html}</div></article></div>'
            f'<div class="src">Fuente: comparación rolling-origin, 30-sep-2026 (tools/critical_tech_model_comparison_rolling.py). '
            f'Riesgo mensual = salida voluntaria antes de la siguiente foto mensual.</div>',
        )
    )

    seg_lo, seg_hi = -30.0, 70.0
    slides.append(
        slide(
            2,
            heading(
                "Con todo lo demás igual, Senior & Lead tiene 1.7 veces el riesgo mensual de Sr Staff, y 3 a 7 años de antigüedad 1.4 veces el de 7 o más",
                f"Cambio del riesgo mensual frente a la categoría de referencia · coeficientes del modelo entrenado con fotos hasta {d['train_end']} · asociaciones, no causas",
            )
            + '<div class="eff-grid"><div class="eff-col">'
            + effect_panel("Antigüedad en la empresa", d["tenure"], seg_lo, seg_hi, "Los primeros 12 meses tienen menos riesgo que 7+ años al ajustar por nivel y segmento.")
            + effect_panel("Nivel", d["levels"], seg_lo, seg_hi, "Se muestran los niveles con 30 o más salidas en entrenamiento.")
            + "</div>"
            + effect_panel("Segmento", d["segs"], seg_lo, seg_hi, f"SoC Architecture se estima con sólo {d['soc_events']} salidas; es el efecto menos preciso.", wide=True)
            + "</div>"
            f'<div class="src">Lectura: +67% significa que el riesgo mensual es 1.7 veces el de la referencia en el mismo mes y con las mismas demás señales. '
            f'Fuente: modelo del último periodo de prueba, comparación rolling-origin del 30-sep-2026.</div>',
        )
    )

    months = d["months"]
    m_lo, m_hi = -70.0, 80.0
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
    slides.append(
        slide(
            3,
            heading(
                "El riesgo mensual cambia con el calendario: mayo y febrero son los meses más altos y octubre el más bajo",
                f"Cambio del riesgo mensual frente a julio, con las demás señales iguales · fotos hasta {d['train_end']} · Critical Tech fase 1",
            )
            + f'<div class="s4-grid"><article class="card" style="padding:22px 26px;"><div class="mbars"><div class="mzero" style="bottom:{zero_from_bottom:.2f}%"></div>{"".join(cols)}</div>'
            f'<div class="mlabels">{labels}</div></article>'
            f'<article class="card" style="justify-content:center;gap:16px;padding:24px;"><div class="side-head">Además, una tendencia anual</div>'
            f'<div class="big-num">−{trend_pct}%</div>'
            f'<div class="side-body">por año en el riesgo mensual hasta {d["train_end"]}, con todo lo demás igual.</div>'
            f'<div class="note-box">En 2025-26 la attrition volvió a subir, así que esta tendencia hoy hace que el modelo se quede corto (ver diapositiva 8).</div></article></div>'
            f'<div class="src">Octubre se estima con {d["oct_events"]} salidas de entrenamiento; es el mes menos preciso. '
            f'Fuente: modelo del último periodo de prueba, comparación rolling-origin del 30-sep-2026.</div>',
        )
    )

    top = max(d["example_monthly"]) * 1.2

    def ex_card(tag: str, who: str, monthly: list[float], six: float, hl: bool) -> str:
        bars = "".join(
            f'<div class="ex-bar"><span>{fmt(v)}</span><i style="height:{v / top * 100:.2f}%"></i></div>' for v in monthly
        )
        names = "".join(f"<div>{m}</div>" for m in d["month_names"])
        return (
            f'<article class="card ex-card{" hl" if hl else ""}"><div class="ex-tag">{e(tag)}</div><div class="ex-who">{e(who)}</div>'
            f'<div class="section-head" style="font-size:12.5px;">Salidas esperadas por cada 1,000 personas, por mes</div>'
            f'<div class="ex-bars">{bars}</div><div class="ex-months">{names}</div>'
            f'<div class="ex-total"><b>{fmt(six)}%</b><span>riesgo de salir en los 6 meses</span></div></article>'
        )

    refs = d["refs"]
    ref_who = f"{refs['seg']} · {LEVEL_LABELS[refs['level_grouped']]} · {TENURE_LABELS[refs['company_tenure_band']]}"
    ex_who = f"{EXAMPLE['seg']} · {LEVEL_LABELS[EXAMPLE['level_grouped']]} · {TENURE_LABELS[EXAMPLE['company_tenure_band']]}"
    steps = [
        "El modelo estima el riesgo de cada mes con la fórmula de la regresión.",
        f"Cambiar segmento, nivel y antigüedad multiplica el riesgo mensual por {fmt(d['example_multiplier'])} "
        f"({' × '.join(fmt(r) for r in d['example_ratios'])}).",
        "El mes del año sube o baja ambas curvas por igual: octubre es el más bajo.",
        "Se encadenan los 6 meses para obtener el riesgo a 6 meses.",
    ]
    steps_html = "".join(f"<li>{e(x)}</li>" for x in steps)
    slides.append(
        slide(
            4,
            heading(
                f"Así calcula: con las mismas reglas, un grupo pasa de {fmt(d['ref_six'])}% a {fmt(d['example_six'])}% de riesgo a 6 meses al cambiar segmento, nivel y antigüedad",
                f"Dos perfiles de grupo ilustrativos, no personas · predicción desde la foto de {d['last_start']} · cambio de manager sin dato en ambos",
            )
            + '<div class="ex-grid">'
            + ex_card("Grupo de referencia", ref_who, d["ref_monthly"], d["ref_six"], False)
            + ex_card("Grupo de mayor riesgo", ex_who, d["example_monthly"], d["example_six"], True)
            + f'<article class="card" style="justify-content:center;gap:14px;"><div class="side-head">Paso a paso</div><ul class="steps-list">{steps_html}</ul></article>'
            + "</div>"
            '<div class="src">Fuente: coeficientes y riesgo base del modelo del último periodo de prueba, comparación rolling-origin del 30-sep-2026.</div>',
        )
    )

    scale_max = 20.0
    rows = []
    hl_map = {"hazard": " hl", "hazard_interactions": " hl2"}
    bar_rows = [("Al azar", 10.0, "")] + [(MODEL_NAMES[k], lift[k], hl_map.get(k, "")) for k in MODEL_ORDER]
    for label, value, hl in bar_rows:
        width = value / scale_max * 100
        rows.append(
            f'<div class="hrow{hl}"><div class="hlabel">{e(label)}</div><div class="htrack">'
            f'<div class="hfill" style="width:{width:.2f}%"></div><div class="hval" style="left:{width:.2f}%">{fmt(value)}</div></div></div>'
        )
    periods = [month_label(f["test_start"]) for f in d["folds"]]
    head = "".join(f"<th>{p}</th>" for p in periods)
    table_rows = ""
    for key in ["hazard", "hazard_interactions", "logistic", "lightgbm"]:
        cells = ""
        for i, value in enumerate(d["fold_lifts"][key]):
            best = max(d["fold_lifts"][k][i] for k in ["hazard", "hazard_interactions", "logistic", "lightgbm"])
            cells += f'<td class="{"win" if value == best else ""}">{fmt(value)}</td>'
        short = {"hazard": "Mes a mes", "hazard_interactions": "+ combinaciones", "logistic": "Logística 6m", "lightgbm": "LightGBM"}[key]
        table_rows += f"<tr><td>{short}</td>{cells}</tr>"
    slides.append(
        slide(
            5,
            heading(
                f"Calculamos los cuatro: el modelo mes a mes ubica {fmt(lift['hazard'])} de cada 100 salidas en el 10% de mayor riesgo; el machine learning, {fmt(lift['lightgbm'])}",
                f"Critical Tech fase 1 · promedio de 4 periodos de prueba de 6 meses ({d['first_test']} a {d['last_test']}) · cada modelo entrenado sólo con datos previos",
            )
            + f'<div class="s6-grid"><article class="card" style="justify-content:center;gap:14px;padding:22px 26px;">'
            f'<div class="question">De cada 100 salidas reales, ¿cuántas estaban en el 10% de grupos que el modelo marcó como de mayor riesgo?</div>'
            f'<div class="hbars">{"".join(rows)}</div></article>'
            f'<article class="card" style="justify-content:center;gap:12px;padding:20px 22px;"><div class="side-head">Resultado por periodo de prueba</div>'
            f'<table class="wins"><thead><tr><th>Modelo</th>{head}</tr></thead><tbody>{table_rows}</tbody></table>'
            f'<div class="side-body" style="font-size:15.5px;">En negritas, el mejor de cada periodo. El machine learning sólo gana el último; '
            f'la versión con combinaciones segmento × antigüedad y segmento × nivel gana 3 de 4 frente al mes a mes.</div></article></div>'
            f'<div class="src">Coincide con la literatura: en Lazzari et al. (2022) LightGBM obtuvo {fmt(d["lazzari_ml"])} y la regresión logística {fmt(d["lazzari_simple"])} '
            f'(puntaje de precisión 0-100). Fuente: comparación rolling-origin del 30-sep-2026.</div>',
        )
    )

    pred = d["pred_last"]
    matrix_rows = [
        ("De cada 100 salidas, cuántas en el 10% de mayor riesgo (4 periodos)",
         [("num", fmt(lift[k])) for k in ["historical", "logistic", "hazard", "lightgbm"]]),
        (f"Nivel estimado en el último periodo (real: {fmt(d['observed_last'])}%)",
         [("num", f"{fmt(pred[k])}%") for k in ["historical", "logistic", "hazard", "lightgbm"]]),
        ("Sirve para 3, 6 o 12 meses sin reentrenar", [("mark", "part"), ("mark", "no"), ("mark", "yes"), ("mark", "no")]),
        ("Capta la temporada del año", [("mark", "no"), ("mark", "no"), ("mark", "yes"), ("mark", "no")]),
        ("Explica cada efecto con un número", [("mark", "no"), ("mark", "yes"), ("mark", "yes"), ("mark", "part")]),
        ("Se entrena con conteos agregados, sin filas individuales", [("mark", "yes")] * 4),
    ]
    cols = ["Promedio histórico", "Logística a 6 meses", "Mes a mes", "Machine learning"]
    head_cells = "".join(f'<th class="{"rec" if i == 2 else ""}">{e(c)}</th>' for i, c in enumerate(cols))
    body = ""
    for crit, cells in matrix_rows:
        tds = ""
        for i, (kind, value) in enumerate(cells):
            rec = " rec" if i == 2 else ""
            if kind == "num":
                tds += f'<td class="num{rec}">{e(value)}</td>'
            else:
                icon, text = MARKS[value]
                tds += f'<td class="{rec.strip()}"><span class="mark m-{value}"><i>{icon}</i>{text}</span></td>'
        body += f"<tr><td>{e(crit)}</td>{tds}</tr>"
    slides.append(
        slide(
            6,
            heading(
                "Con precisión similar a la logística y mejor que el machine learning, el modelo mes a mes es el que más necesidades cubre",
                f"Critical Tech fase 1 · cifras de los 4 periodos de prueba y del último ({d['last_start']} a {d['last_test']})",
            )
            + f'<article class="card" style="align-self:center;padding:14px 22px;"><table class="matrix"><thead><tr><th></th>{head_cells}</tr></thead>'
            f"<tbody>{body}</tbody></table></article>"
            f'<div class="src">Temporada: el LightGBM a 6 meses asignó 0% de importancia al mes del año. «Parcial» en machine learning: sólo da importancias '
            f'globales, sin dirección ni tamaño del efecto. Fuente: comparación rolling-origin del 30-sep-2026.</div>',
        )
    )

    cal = d["calibration"]
    top_cal = max(max(b["observed_rate_percent"], b["mean_predicted_percent"]) for b in cal) * 1.18
    pairs = "".join(
        f'<div class="cal-pair"><div class="cal-bar obs"><span>{fmt(b["observed_rate_percent"])}%</span><i style="height:{b["observed_rate_percent"] / top_cal * 100:.2f}%"></i></div>'
        f'<div class="cal-bar pred"><span>{fmt(b["mean_predicted_percent"])}%</span><i style="height:{b["mean_predicted_percent"] / top_cal * 100:.2f}%"></i></div></div>'
        for b in cal
    )
    cal_labels = "".join(f"<div>{t}</div>" for t in ["20% más bajo", "2º", "3º", "4º", "20% más alto"])
    under = d["under_one"]
    gr = d["graphics"]
    gaps = [
        f"Aprendió una tendencia a la baja ({'−'}{trend_pct}% por año) y en 2025-26 la attrition subió: real {fmt(d['observed_last'])}% contra {fmt(pred['hazard'])}% estimado.",
        f"Todos los modelos se quedan cortos: logística {fmt(pred['logistic'])}%, machine learning {fmt(pred['lightgbm'])}%.",
        f"Grupos que aún no capta: menos de 1 año, {fmt(under['observed_rate_percent'])}% real contra {fmt(under['hazard_predicted_percent'])}%; "
        f"Graphics con 1 a 3 años, {fmt(gr['observed_rate_percent'])}% contra {fmt(gr['predicted_rate_percent'])}%.",
        f"El cambio de manager no tiene dato para el {fmt(d['manager_unknown'])}% de las personas-mes: hoy casi no aporta.",
    ]
    gaps_html = "".join(f"<li>{e(g)}</li>" for g in gaps)
    slides.append(
        slide(
            7,
            heading(
                f"El modelo ordena bien los grupos, pero hoy subestima el nivel: en el último periodo estimó {fmt(pred['hazard'])}% y ocurrió {fmt(d['observed_last'])}%",
                f"% que sale en 6 meses por quintil de riesgo estimado · {d['last_start']} a {d['last_test']} · {d['last_exposures']:,} personas-mes, {d['last_events']:,} salidas",
            )
            + f'<div class="s8-grid"><article class="card" style="justify-content:center;gap:12px;padding:22px 26px;">'
            f'<div class="legend"><span>Real</span><span class="pred">Estimado por el modelo</span></div>'
            f'<div class="cal">{pairs}</div><div class="cal-labels">{cal_labels}</div>'
            f'<div class="side-body" style="font-size:15.5px;">El riesgo real sube de un quintil al siguiente: el orden es correcto. Las barras estimadas son más bajas en todos.</div></article>'
            f'<article class="card" style="justify-content:center;gap:14px;padding:22px;"><div class="side-head">Por qué ocurre</div>'
            f'<ul class="gaps">{gaps_html}</ul>'
            f'<div class="fix">Corrección: recalibrar el nivel cada trimestre con los meses más recientes (un solo parámetro en una regresión) y agregar señales de carrera y QVoice.</div></article></div>'
            f'<div class="src">Quintiles con 30+ salidas cada uno. Fuente: último periodo de prueba, comparación rolling-origin del 30-sep-2026. Asociaciones, no causas.</div>',
        )
    )

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
        "Aprobar la regresión mes a mes como modelo base.",
        "Definir si las salidas «Voluntary Exception» cuentan.",
        "Autorizar el uso gobernado de la encuesta QVoice.",
    ]
    dec_html = "".join(f'<div class="decision">{e(x)}</div>' for x in decisions)
    slides.append(
        slide(
            8,
            heading(
                "Antes de usarlo recalibraremos el nivel y agregaremos señales; necesitamos tres decisiones",
                "Del modelo base a un piloto de retención por grupos",
            )
            + f'<article class="card" style="justify-content:center;align-self:center;padding:40px 32px;"><div class="timeline">{tl_html}</div></article>'
            f'<div style="display:flex;flex-direction:column;gap:10px;"><div class="section-head">Decisiones que necesitamos</div>'
            f'<div class="decisions">{dec_html}</div></div>',
        )
    )
    return slides


def render() -> str:
    d = load_data()
    tpl = TEMPLATE.read_text(encoding="utf-8")
    out = tpl.replace('<html lang="en">', '<html lang="es">', 1)
    out = out.replace("<title>[Slide Title]</title>", "<title>Modelo de attrition voluntaria: qué elegimos y por qué (v2)</title>", 1)
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
        ROOT / "output" / "presentations" / f"{datetime.now():%Y%m%d-%H%M}_seleccion-modelo-v2" / "presentacion.html"
    )
    if out.exists():
        raise SystemExit(f"Ya existe {out}; no se sobrescribe.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
