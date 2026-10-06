"""Genera el deck ejecutivo de selección del modelo de attrition.

Parte de la plantilla html-slide-generator (base-fullscreen.html) sin alterar
sus bloques JavaScript. Las cifras se leen de los artefactos del proyecto y se
validan contra valores esperados; si una fuente cambia, el script falla.
Los textos visibles viven en STRINGS[lang] para generar la versión en inglés
sin tocar layout ni datos.

Uso:
    python -B tools/presentations/build_model_selection_deck.py [--lang es] [--out RUTA]
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
MODEL_RESULTS = ROOT / "output" / "analysis" / "critical-tech" / "20260914" / "baseline-v2-calendar-brier" / "model-results.json"
MODEL_REPORT = ROOT / "output" / "analysis" / "critical-tech" / "20260914" / "baseline-v2-calendar-brier" / "model-report.md"
COHORT_SCREEN = ROOT / "output" / "analysis" / "critical-tech" / "20260907" / "cohort-screen-report.md"
TENURE_EVIDENCE = (
    ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v3.six-month-attrition-evidence-20260914.json"
)
LAZZARI = next((ROOT / "docs" / "research" / "attrition-literature" / "papers").glob("2022-lazzari*.md"))

TENURE_ORDER = ["<1 año", "1–<2 años", "2–<4 años", "4–<6 años", "6–<10 años", "10+ años"]
TENURE_PEAK = "2–<4 años"


def fmt(value: float, lang: str = "es") -> str:
    """Enteros sin decimales; el resto con un decimal como máximo."""
    rounded = round(value, 1)
    text = f"{rounded:,.0f}" if rounded == int(rounded) else f"{rounded:,.1f}"
    return text


def load_data() -> dict:
    results = json.loads(MODEL_RESULTS.read_text(encoding="utf-8"))
    holdout = results["final_holdout"]
    hazard = holdout["champion_six_month"]
    logistic = holdout["direct_logistic_six_month"]
    assert results["windows"]["holdout_start"] == "2025-08-24", "Cambió la ventana de prueba"
    assert results["windows"]["holdout_end"] == "2026-02-22", "Cambió la ventana de prueba"
    assert hazard["snapshot_count"] == 7 and hazard["events"] == 7404
    assert round(hazard["lift_at_10_percent"], 2) == 1.51
    assert round(logistic["lift_at_10_percent"], 2) == 1.56
    under = [b for b in hazard["calibration"] if b["mean_predicted_percent"] < b["observed_rate_percent"]]
    assert [b["bin"] for b in under][:2] == [1, 2], "Cambió el patrón de calibración"

    report = MODEL_REPORT.read_text(encoding="utf-8")
    season = re.search(r"\|\s*calendar_month\s*\|\s*5 vs 7\s*\|\s*([\d.]+)", report)
    assert season, "No se encontró el efecto mayo vs julio"
    season_ratio = float(season.group(1))
    assert round(season_ratio, 1) == 1.7

    screen = COHORT_SCREEN.read_text(encoding="utf-8")
    base = re.search(r"\*\*([\d.]+)%\*\* de target voluntario a seis meses", screen)
    assert base and base.group(1) == "3.1588", "Cambió la tasa base de Critical Tech"

    tenure = json.loads(TENURE_EVIDENCE.read_text(encoding="utf-8"))
    rows = {r["category"]: r for r in tenure["rows"] if r["metric"] == "company_tenure"}
    assert set(rows) == set(TENURE_ORDER), "Cambiaron las bandas de antigüedad"
    first = rows[TENURE_ORDER[0]]
    assert (first["first_snapshot_date"], first["last_snapshot_date"]) == ("2024-03-24", "2026-02-22")
    assert first["baseline_rate_percent"] == "2.8085"
    peak = max(rows.values(), key=lambda r: float(r["attrition_rate_percent"]))
    assert peak["category"] == TENURE_PEAK

    lazzari = LAZZARI.read_text(encoding="utf-8")
    assert "LightGBM obtuvo PR-AUC 0.588 y logística 0.583" in lazzari
    assert "9,296 respuestas" in lazzari

    return {
        "base_ct": float(base.group(1)),
        "hazard_top10": hazard["lift_at_10_percent"] * 10,
        "logistic_top10": logistic["lift_at_10_percent"] * 10,
        "holdout_months": hazard["snapshot_count"],
        "season_ratio": season_ratio,
        "tenure": [(c, float(rows[c]["attrition_rate_percent"])) for c in TENURE_ORDER],
        "tenure_base": float(first["baseline_rate_percent"]),
        "lazzari_ml": 58.8,
        "lazzari_simple": 58.3,
        "lazzari_n": 9296,
    }


STRINGS = {
    "es": {
        "doc_title": "Modelo de attrition voluntaria: qué elegimos y por qué",
        "theme_label": "Tema",
        "themes": ["Claro – Clásico", "Claro – Azul suave", "Oscuro – Real", "Oscuro – Carbón"],
        "nav_tab": "Diapositivas",
        "nav_label": "Navegación",
        "nav": [
            "Recomendación",
            "Dónde, no quién",
            "El riesgo cambia",
            "Cuatro opciones",
            "Resultados",
            "Por qué mes a mes",
            "Lo complejo",
            "Próximos pasos",
        ],
        "s1_kicker": "People Analytics · Critical Tech · Septiembre 2026",
        "s1_title": "Recomendamos un modelo que sigue el riesgo de salida mes a mes para anticipar dónde se concentrará la attrition",
        "s1_chips": [
            ("Población", "Critical Tech, empleados regulares activos"),
            ("Horizonte", "Salidas voluntarias en los próximos 6 meses"),
            ("Resultado", "Grupos de 100+ personas, nunca personas"),
        ],
        "s1_note": "Lo acompañan dos referencias simples y un rival más complejo que tendrá que ganarse su lugar.",
        "s2_title": "Queremos anticipar dónde se concentrarán las salidas, no quién se irá",
        "s2_sub": "Critical Tech · salida voluntaria en los 6 meses siguientes a cada foto mensual · fotos con 6 meses completos de seguimiento, corte sep-2026",
        "s2_kpi_label": "de las personas de Critical Tech sale de forma voluntaria en un periodo típico de 6 meses",
        "s2_steps": [
            ("1", "Foto mensual", "Cada mes vemos antigüedad, nivel, cambios de manager y otras señales conocidas en ese momento."),
            ("2", "Probabilidad por grupo", "El modelo estima cuántas salidas esperar en cada grupo en los próximos meses."),
            ("3", "Acción de RH", "RH prioriza grupos de 100+ personas con una palanca concreta (carrera, movilidad, manager)."),
        ],
        "s2_guard": "Nunca se publican listas de personas ni puntajes individuales.",
        "s2_source": "Fuente: screen de cohortes Critical Tech, 07-sep-2026. Tasa: salidas voluntarias ÷ fotos empleado-mes con 6 meses de seguimiento.",
        "s3_title": "El riesgo de salida cambia con el tiempo: sube hacia los 2-4 años de antigüedad y varía según la época del año",
        "s3_sub": "Toda la población elegible · % que sale en los 6 meses siguientes · 24 fotos mensuales, mar-2024 a feb-2026",
        "s3_bars_title": "% que sale en 6 meses, por años en la empresa",
        "s3_tenure_labels": ["Menos de 1", "1 a 2", "2 a 4", "4 a 6", "6 a 10", "10 o más"],
        "s3_base_label": "Promedio",
        "s3_season_head": "También cambia con la época del año",
        "s3_season_body": "En mayo, el riesgo mensual de salida en Critical Tech es {ratio} veces el de julio, con todo lo demás igual.",
        "s3_implication": "Un modelo que sigue el riesgo mes a mes captura ambos efectos sin tener que adivinarlos.",
        "s3_source": "Fuentes: evidencia de distribuciones que usa el deck v8 (antigüedad) y modelo base de Critical Tech del 14-sep-2026 (estacionalidad). Asociaciones, no causas.",
        "s4_title": "Evaluamos cuatro formas de anticipar las salidas",
        "s4_sub": "De la más simple a la más compleja",
        "s4_cards": [
            ("Promedio histórico", "Referencia", "Como pronosticar la lluvia con el promedio del año pasado: da el total esperado, pero no dice dónde."),
            ("Probabilidad directa a 6 meses", "Referencia fuerte", "Una foto: mira a cada grupo hoy y estima si saldrán en los próximos 6 meses."),
            ("Riesgo mes a mes", "Recomendado", "Una película: estima el riesgo de cada mes y lo suma para 3, 6 o 12 meses."),
            ("Machine learning avanzado", "Rival por probar", "Combina cientos de árboles de decisión. Puede captar patrones complejos, pero es más difícil de explicar."),
        ],
        "s5_title": "Los dos modelos simples ubican ~50% más salidas que elegir al azar, y quedan empatados entre sí",
        "s5_sub": "Critical Tech · prueba sobre {months} meses que el modelo no vio (ago-2025 a feb-2026)",
        "s5_question": "De cada 100 salidas reales, ¿cuántas estaban en el 10% de personas que el modelo marcó como de mayor riesgo?",
        "s5_rows": ["Al azar", "Probabilidad directa a 6 meses", "Riesgo mes a mes", "Machine learning avanzado"],
        "s5_pending": "Aún no probado",
        "s5_caveats_head": "Lo que todavía no sabemos",
        "s5_caveats": [
            "Es una sola prueba, en un solo periodo.",
            "Usó sólo 5 señales; las más fuertes (carrera, encuesta QVoice) aún no entran.",
            "Incluyó un segmento que la población vigente excluye; se repetirá sin él.",
        ],
        "s5_source": "Fuente: modelo base de Critical Tech v2, 14-sep-2026. Asociaciones, no causas.",
        "s6_title": "Con precisión empatada, el modelo mes a mes encaja mejor con cómo ocurren las salidas",
        "s6_sub": "Comparación cualitativa de las cuatro opciones",
        "s6_cols": ["Promedio histórico", "Probabilidad directa", "Riesgo mes a mes", "Machine learning"],
        "s6_rows": [
            ("Ordena qué grupos tienen más riesgo", ["no", "yes", "yes", "tbd"]),
            ("Aprovecha los meses más recientes", ["part", "no", "yes", "part"]),
            ("Sirve para 3, 6 o 12 meses sin rehacerse", ["part", "no", "yes", "no"]),
            ("Capta cambios dentro del periodo (temporada, cambio de manager)", ["no", "no", "yes", "part"]),
            ("Se explica fácil a RH", ["yes", "yes", "yes", "part"]),
            ("Se entrena sin guardar datos individuales", ["yes", "yes", "yes", "no"]),
        ],
        "s6_legend": {"yes": "Sí", "part": "Parcial", "no": "No", "tbd": "Por probar"},
        "s6_note": "Punto a corregir: hoy el modelo mes a mes subestima un poco el riesgo en los grupos de riesgo bajo y medio. Si al corregirlo la probabilidad directa gana de forma consistente, la adoptamos; cambiar cuesta poco.",
        "s7_title": "Un modelo más complejo tendrá que ganarse su lugar",
        "s7_sub": "La evidencia publicada muestra ganancias mínimas frente a modelos simples",
        "s7_chart_head": "Estudio europeo, {n} personas: puntaje de precisión (0 a 100)",
        "s7_bars": ["Machine learning avanzado", "Modelo simple"],
        "s7_gap": "Diferencia: menos de 1 punto",
        "s7_rule_head": "Regla que proponemos",
        "s7_rules": [
            "El rival se prueba con los mismos datos y periodos.",
            "Sólo se adopta si gana en al menos 3 de 4 periodos de prueba.",
            "Sin perder claridad ni empeorar sus estimaciones por grupo.",
        ],
        "s7_warning": "Las cifras de precisión muy altas que circulan suelen venir de datos simulados o de intención de salida, no de salidas reales.",
        "s7_source": "Fuente: Lazzari, Álvarez y Ruggieri (2022), encuesta de intención de salida; revisión bibliográfica del proyecto.",
        "s8_title": "Antes de usarlo validaremos en cuatro pasos, y necesitamos tres decisiones",
        "s8_sub": "Del modelo base a un piloto de retención por grupos",
        "s8_steps": [
            ("Ajustar población", "Repetir la prueba sólo con la población vigente de Critical Tech."),
            ("Probar en varios periodos", "Al menos 4 periodos de prueba, con separación entre entrenar y evaluar."),
            ("Agregar señales por bloques", "Carrera, manager y equipo, encuesta QVoice; cada bloque entra sólo si mejora."),
            ("Piloto por grupos", "Acciones de RH en grupos priorizados, con métrica y responsable."),
        ],
        "s8_decisions_head": "Decisiones que necesitamos",
        "s8_decisions": [
            "Confirmar el horizonte de 6 meses.",
            "Definir si las salidas «Voluntary Exception» cuentan.",
            "Autorizar el uso gobernado de la encuesta QVoice.",
        ],
    }
}

MARKS = {"yes": "✓", "part": "◐", "no": "✗", "tbd": "?"}


CSS = """
    .slide-stage { padding: 30px 44px 22px; gap: 16px; }
    .slide-title-text { font-size: 30px; line-height: 1.2; max-width: 1300px; }
    .slide-subtitle { font-size: 16px; margin-top: 6px; }
    .s2-grid > .card, .s3-grid > .card, .s5-grid > .card, .s7-grid > .card { align-self: center; height: 480px; justify-content: center; }
    .s2-grid > .card { height: 400px; }
    .matrix-card { align-self: center; height: auto; }
    .src { font-size: 12px; color: var(--text-muted); align-self: end; }
    .stage-3rows { grid-template-rows: auto 1fr auto; }
    .muted { color: var(--text-muted); }
    .accent-text { color: var(--accent); }
    .data-context { --ctx: color-mix(in oklab, var(--text-muted) 45%, var(--bg-surface)); }

    /* Portada */
    .cover { display: flex; flex-direction: column; justify-content: center; gap: 26px; padding: 0 40px; }
    .cover-kicker { font-size: 16px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }
    .cover-title { font-size: 46px; font-weight: 800; line-height: 1.15; margin: 0; max-width: 1200px; }
    .cover-chips { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; max-width: 1200px; }
    .cover-chip { border-left: 4px solid var(--accent); padding: 8px 16px; background: var(--bg-surface); border-radius: 10px; }
    .cover-chip b { display: block; font-size: 13px; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); }
    .cover-chip span { font-size: 19px; font-weight: 600; }
    .cover-note { font-size: 19px; color: var(--text-muted); max-width: 1100px; }

    /* Diapositiva 2 */
    .s2-grid { display: grid; grid-template-columns: 0.8fr 2fr; gap: 26px; align-items: center; }
    .kpi-big { font-size: 110px; font-weight: 800; color: var(--accent); line-height: 1; }
    .kpi-label { font-size: 19px; line-height: 1.4; }
    .flow { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
    .flow-step { position: relative; background: var(--bg-surface-2); border-radius: 14px; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
    .flow-step:not(:last-child)::after { content: "→"; position: absolute; right: -16px; top: 42%; font-size: 26px; color: var(--accent); }
    .flow-num { width: 38px; height: 38px; border-radius: 50%; background: var(--accent); color: var(--text-invert); display: grid; place-items: center; font-weight: 800; font-size: 18px; }
    .flow-head { font-size: 21px; font-weight: 700; }
    .flow-body { font-size: 17px; line-height: 1.45; color: var(--text-main); }
    .guard { margin-top: 6px; font-size: 18px; font-weight: 600; padding: 12px 16px; border-radius: 10px; background: var(--accent-soft); color: var(--text-main); }

    /* Barras verticales */
    .s3-grid { display: grid; grid-template-columns: 1.7fr 1fr; gap: 26px; }
    .vbars { position: relative; display: grid; grid-template-columns: repeat(6, 1fr); gap: 18px; align-items: end; height: 380px; border-bottom: 2px solid var(--text-muted); padding: 0 8px; }
    .vbar { position: relative; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; height: 100%; }
    .vbar-fill { width: 100%; border-radius: 8px 8px 0 0; background: var(--ctx); }
    .vbar.hl .vbar-fill { background: var(--accent); }
    .vbar-val { font-size: 18px; font-weight: 700; margin-bottom: 6px; color: var(--text-muted); }
    .vbar.hl .vbar-val { color: var(--accent); font-size: 22px; }
    .vlabels { display: grid; grid-template-columns: repeat(6, 1fr); gap: 18px; padding: 8px 8px 0; text-align: center; font-size: 16px; color: var(--text-muted); }
    .vlabels .hl { color: var(--accent); font-weight: 700; }
    .baseline { position: absolute; left: 0; right: 0; border-top: 2px dashed var(--text-muted); pointer-events: none; }
    .baseline span { position: absolute; right: 0; top: -24px; font-size: 13px; color: var(--text-muted); background: var(--bg-surface); padding: 0 4px; }
    .big-ratio { font-size: 84px; font-weight: 800; color: var(--accent); line-height: 1; }
    .side-head { font-size: 21px; font-weight: 700; }
    .side-body { font-size: 18px; line-height: 1.45; }
    .implication { font-size: 18px; font-weight: 600; border-left: 4px solid var(--accent); padding: 8px 14px; }

    /* Tarjetas de opciones */
    .opt-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; align-items: stretch; height: 340px; align-self: center; }
    .opt { background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-card); padding: 24px 22px; display: flex; flex-direction: column; gap: 14px; box-shadow: var(--shadow-soft); }
    .opt.rec { border: 3px solid var(--accent); }
    .opt-num { font-size: 15px; font-weight: 700; color: var(--text-muted); }
    .opt-name { font-size: 24px; font-weight: 800; line-height: 1.2; }
    .opt-tag { align-self: flex-start; font-size: 14px; font-weight: 700; padding: 4px 12px; border-radius: var(--radius-pill); background: color-mix(in oklab, var(--text-muted) 14%, transparent); color: var(--text-muted); }
    .opt.rec .opt-tag { background: var(--accent); color: var(--text-invert); }
    .opt-body { font-size: 18px; line-height: 1.5; }
    .scale-arrow { display: flex; justify-content: space-between; font-size: 15px; color: var(--text-muted); border-top: 2px solid var(--border-strong); padding-top: 8px; }

    /* Barras horizontales */
    .s5-grid { display: grid; grid-template-columns: 1.75fr 1fr; gap: 26px; }
    .question { font-size: 20px; font-weight: 600; line-height: 1.4; margin-bottom: 18px; }
    .hbars { position: relative; display: flex; flex-direction: column; gap: 22px; }
    .hrow { display: grid; grid-template-columns: 300px 1fr; align-items: center; gap: 16px; }
    .hlabel { font-size: 18px; text-align: right; }
    .hrow.hl .hlabel { font-weight: 800; color: var(--accent); }
    .htrack { position: relative; height: 46px; }
    .hfill { height: 100%; border-radius: 0 8px 8px 0; background: var(--ctx); display: flex; align-items: center; justify-content: flex-end; }
    .hrow.hl .hfill { background: var(--accent); }
    .hval { position: absolute; top: 50%; transform: translateY(-50%); font-size: 22px; font-weight: 800; padding-left: 10px; }
    .hrow.hl .hval { color: var(--accent); }
    .hpending { height: 100%; border: 2px dashed var(--text-muted); border-radius: 8px; display: flex; align-items: center; padding: 0 14px; font-size: 16px; color: var(--text-muted); width: 55%; }
    .caveats { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
    .caveats li { font-size: 18px; line-height: 1.4; padding-left: 26px; position: relative; }
    .caveats li::before { content: "!"; position: absolute; left: 0; top: 1px; width: 18px; height: 18px; border-radius: 50%; background: #d97706; color: #fff; font-size: 12px; font-weight: 800; display: grid; place-items: center; }

    /* Matriz */
    .matrix { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 18px; }
    .matrix th, .matrix td { padding: 17px 12px; border-bottom: 1px solid var(--border-subtle); text-align: center; }
    .matrix th { font-size: 16px; color: var(--text-muted); font-weight: 700; }
    .matrix th.rec, .matrix td.rec { background: var(--accent-soft); }
    .matrix th.rec { color: var(--accent); border-radius: 12px 12px 0 0; }
    .matrix td:first-child, .matrix th:first-child { text-align: left; }
    .mark { display: inline-flex; align-items: center; gap: 6px; font-weight: 700; font-size: 16px; }
    .mark i { font-style: normal; font-size: 20px; }
    .m-yes { color: #15803d; } .m-part { color: #b45309; } .m-no { color: #b91c1c; } .m-tbd { color: var(--text-muted); }
    body.theme-dark-royal .m-yes, body.theme-dark-carbon .m-yes { color: #4ade80; }
    body.theme-dark-royal .m-part, body.theme-dark-carbon .m-part { color: #fbbf24; }
    body.theme-dark-royal .m-no, body.theme-dark-carbon .m-no { color: #f87171; }
    .note-box { font-size: 17px; line-height: 1.45; padding: 12px 16px; border-left: 4px solid #d97706; background: color-mix(in oklab, #f59e0b 10%, var(--bg-surface)); border-radius: 6px; }

    /* Diapositiva 7 */
    .s7-grid { display: grid; grid-template-columns: 1.3fr 1fr; gap: 26px; }
    .gap-label { font-size: 22px; font-weight: 800; color: var(--accent); margin-top: 8px; }
    .rules { list-style: none; margin: 0; padding: 0; counter-reset: r; display: flex; flex-direction: column; gap: 16px; }
    .rules li { counter-increment: r; font-size: 19px; line-height: 1.4; padding-left: 44px; position: relative; }
    .rules li::before { content: counter(r); position: absolute; left: 0; top: -2px; width: 30px; height: 30px; border-radius: 50%; background: var(--accent); color: var(--text-invert); font-weight: 800; display: grid; place-items: center; font-size: 16px; }

    /* Diapositiva 8 */
    .timeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; position: relative; }
    .tl-step { display: flex; flex-direction: column; gap: 10px; }
    .tl-dot { display: flex; align-items: center; gap: 10px; }
    .tl-dot b { width: 40px; height: 40px; border-radius: 50%; background: var(--accent); color: var(--text-invert); display: grid; place-items: center; font-size: 18px; flex-shrink: 0; }
    .tl-dot hr { flex: 1; border: none; border-top: 3px solid var(--border-strong); margin: 0; }
    .tl-head { font-size: 21px; font-weight: 700; }
    .tl-body { font-size: 17px; line-height: 1.45; }
    .decisions { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
    .decision { font-size: 19px; font-weight: 600; line-height: 1.4; padding: 16px 18px; border-radius: 12px; border: 2px solid var(--accent); background: var(--accent-soft); }
    .section-head { font-size: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); }
"""


def e(text: str) -> str:
    return html.escape(text, quote=False)


def heading(title: str, sub: str | None = None) -> str:
    sub_html = f'<p class="slide-subtitle">{e(sub)}</p>' if sub else ""
    return f'<div class="slide-heading"><div><h2 class="slide-title-text">{e(title)}</h2>{sub_html}</div></div>'


def slide(idx: int, body: str, cls: str = "stage-3rows") -> str:
    return f'<div class="slide-stage {cls} data-context" id="slide-{idx + 1}">\n{body}\n</div>'


def build_slides(s: dict, d: dict) -> list[str]:
    slides = []

    chips = "".join(f'<div class="cover-chip"><b>{e(k)}</b><span>{e(v)}</span></div>' for k, v in s["s1_chips"])
    slides.append(
        slide(
            0,
            f'<div class="cover" style="grid-row: 1 / -1;"><div class="cover-kicker">{e(s["s1_kicker"])}</div>'
            f'<h1 class="cover-title">{e(s["s1_title"])}</h1><div class="cover-chips">{chips}</div>'
            f'<div class="cover-note">{e(s["s1_note"])}</div></div>',
            cls="",
        )
    )

    steps = "".join(
        f'<div class="flow-step"><div class="flow-num">{n}</div><div class="flow-head">{e(h)}</div>'
        f'<div class="flow-body">{e(b)}</div></div>'
        for n, h, b in s["s2_steps"]
    )
    slides.append(
        slide(
            1,
            heading(s["s2_title"], s["s2_sub"])
            + f'<div class="s2-grid"><article class="card" style="justify-content:center;padding:36px 28px;">'
            f'<div class="kpi-big">{fmt(d["base_ct"])}%</div><div class="kpi-label">{e(s["s2_kpi_label"])}</div></article>'
            f'<div style="display:flex;flex-direction:column;gap:16px;justify-content:center;"><div class="flow">{steps}</div>'
            f'<div class="guard">{e(s["s2_guard"])}</div></div></div>'
            f'<div class="src">{e(s["s2_source"])}</div>',
        )
    )

    top = max(v for _, v in d["tenure"]) * 1.15
    bars = "".join(
        f'<div class="vbar{" hl" if c == TENURE_PEAK else ""}"><div class="vbar-val">{fmt(v)}%</div>'
        f'<div class="vbar-fill" style="height:{v / top * 100:.2f}%"></div></div>'
        for c, v in d["tenure"]
    )
    labels = "".join(
        f'<div class="{"hl" if c == TENURE_PEAK else ""}">{e(lab)}</div>'
        for (c, _), lab in zip(d["tenure"], s["s3_tenure_labels"])
    )
    base_pos = d["tenure_base"] / top * 100
    slides.append(
        slide(
            2,
            heading(s["s3_title"], s["s3_sub"])
            + f'<div class="s3-grid"><article class="card"><div class="card-title" style="font-size:14px;">{e(s["s3_bars_title"])}</div>'
            f'<div class="vbars">{bars}<div class="baseline" style="bottom:{base_pos:.2f}%"><span>{e(s["s3_base_label"])} {fmt(d["tenure_base"])}%</span></div></div>'
            f'<div class="vlabels">{labels}</div></article>'
            f'<article class="card" style="justify-content:center;gap:18px;"><div class="side-head">{e(s["s3_season_head"])}</div>'
            f'<div class="big-ratio">{fmt(d["season_ratio"])}×</div>'
            f'<div class="side-body">{e(s["s3_season_body"].format(ratio=fmt(d["season_ratio"])))}</div>'
            f'<div class="implication">{e(s["s3_implication"])}</div></article></div>'
            f'<div class="src">{e(s["s3_source"])}</div>',
        )
    )

    cards = "".join(
        f'<div class="opt{" rec" if i == 2 else ""}"><div class="opt-num">{i + 1}</div><div class="opt-name">{e(n)}</div>'
        f'<div class="opt-tag">{e(t)}</div><div class="opt-body">{e(b)}</div></div>'
        for i, (n, t, b) in enumerate(s["s4_cards"])
    )
    simple, complex_ = ("Más simple", "Más complejo") if s is STRINGS["es"] else ("Simpler", "More complex")
    slides.append(
        slide(
            3,
            heading(s["s4_title"], s["s4_sub"])
            + f'<div style="display:flex;flex-direction:column;gap:16px;align-self:center;"><div class="opt-grid">{cards}</div>'
            f'<div class="scale-arrow"><span>← {simple}</span><span>{complex_} →</span></div></div><div></div>',
        )
    )

    values = [10.0, d["logistic_top10"], d["hazard_top10"], None]
    scale_max = 20.0
    rows = []
    for i, (label, value) in enumerate(zip(s["s5_rows"], values)):
        hl = " hl" if i == 2 else ""
        if value is None:
            track = f'<div class="hpending">{e(s["s5_pending"])}</div>'
        else:
            width = value / scale_max * 100
            track = f'<div class="hfill" style="width:{width:.2f}%"></div><div class="hval" style="left:{width:.2f}%">{fmt(value)}</div>'
        rows.append(f'<div class="hrow{hl}"><div class="hlabel">{e(label)}</div><div class="htrack">{track}</div></div>')
    caveats = "".join(f"<li>{e(c)}</li>" for c in s["s5_caveats"])
    slides.append(
        slide(
            4,
            heading(s["s5_title"], s["s5_sub"].format(months=d["holdout_months"]))
            + f'<div class="s5-grid"><article class="card"><div class="question">{e(s["s5_question"])}</div>'
            f'<div class="hbars">{"".join(rows)}</div></article>'
            f'<article class="card" style="justify-content:center;"><div class="side-head">{e(s["s5_caveats_head"])}</div>'
            f'<ul class="caveats">{caveats}</ul></article></div>'
            f'<div class="src">{e(s["s5_source"])}</div>',
        )
    )

    head_cells = "".join(f'<th class="{"rec" if i == 2 else ""}">{e(c)}</th>' for i, c in enumerate(s["s6_cols"]))
    body_rows = ""
    for crit, marks in s["s6_rows"]:
        cells = "".join(
            f'<td class="{"rec" if i == 2 else ""}"><span class="mark m-{m}"><i>{MARKS[m]}</i>{e(s["s6_legend"][m])}</span></td>'
            for i, m in enumerate(marks)
        )
        body_rows += f"<tr><td>{e(crit)}</td>{cells}</tr>"
    slides.append(
        slide(
            5,
            heading(s["s6_title"], s["s6_sub"])
            + f'<article class="card matrix-card"><table class="matrix"><thead><tr><th></th>{head_cells}</tr></thead>'
            f"<tbody>{body_rows}</tbody></table></article>"
            f'<div class="note-box">{e(s["s6_note"])}</div>',
        )
    )

    lz = [(s["s7_bars"][0], d["lazzari_ml"]), (s["s7_bars"][1], d["lazzari_simple"])]
    lz_rows = "".join(
        f'<div class="hrow" style="grid-template-columns:260px 1fr;"><div class="hlabel">{e(n)}</div><div class="htrack">'
        f'<div class="hfill" style="width:{v:.2f}%"></div><div class="hval" style="left:{v:.2f}%">{fmt(v)}</div></div></div>'
        for n, v in lz
    )
    rules = "".join(f"<li>{e(r)}</li>" for r in s["s7_rules"])
    n_fmt = f"{d['lazzari_n']:,}"
    slides.append(
        slide(
            6,
            heading(s["s7_title"], s["s7_sub"])
            + f'<div class="s7-grid"><article class="card" style="justify-content:center;gap:22px;">'
            f'<div class="side-head">{e(s["s7_chart_head"].format(n=n_fmt))}</div><div class="hbars">{lz_rows}</div>'
            f'<div class="gap-label">{e(s["s7_gap"])}</div><div class="note-box">{e(s["s7_warning"])}</div></article>'
            f'<article class="card" style="justify-content:center;gap:20px;"><div class="side-head">{e(s["s7_rule_head"])}</div>'
            f'<ul class="rules">{rules}</ul></article></div>'
            f'<div class="src">{e(s["s7_source"])}</div>',
        )
    )

    tl = "".join(
        f'<div class="tl-step"><div class="tl-dot"><b>{i + 1}</b><hr></div><div class="tl-head">{e(h)}</div>'
        f'<div class="tl-body">{e(b)}</div></div>'
        for i, (h, b) in enumerate(s["s8_steps"])
    )
    decisions = "".join(f'<div class="decision">{e(x)}</div>' for x in s["s8_decisions"])
    slides.append(
        slide(
            7,
            heading(s["s8_title"], s["s8_sub"])
            + f'<article class="card" style="justify-content:center;align-self:center;height:auto;padding:44px 32px;"><div class="timeline">{tl}</div></article>'
            f'<div style="display:flex;flex-direction:column;gap:10px;"><div class="section-head">{e(s["s8_decisions_head"])}</div>'
            f'<div class="decisions">{decisions}</div></div>',
        )
    )
    return slides


def render(lang: str) -> str:
    s = STRINGS[lang]
    d = load_data()
    tpl = TEMPLATE.read_text(encoding="utf-8")

    out = tpl.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    out = out.replace("<title>[Slide Title]</title>", f"<title>{e(s['doc_title'])}</title>", 1)
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
    out = out[:body_start] + "\n" + "\n".join(build_slides(s, d)) + "\n\n" + out[nav_start:]

    pills = "\n".join(
        f'      <button class="nav-pill{" pill-active" if i == 0 else ""}" data-slide="{i}">{i + 1}. {e(t)}</button>'
        for i, t in enumerate(s["nav"])
    )
    out = re.sub(
        r'<div class="nav-tab">Slides</div>.*?</div>\n  </div>',
        lambda _: f'<div class="nav-tab">{e(s["nav_tab"])}</div>\n    <div class="nav-panel">\n'
        f'      <div class="nav-label">{e(s["nav_label"])}</div>\n{pills}\n    </div>\n  </div>',
        out,
        count=1,
        flags=re.DOTALL,
    )
    for old, new in zip(["Light – Classic", "Light – Soft Blue", "Dark – Royal", "Dark – Carbon"], s["themes"]):
        out = out.replace(f">{old}</button>", f">{e(new)}</button>", 1)
    out = out.replace('<div class="side-label">Theme</div>', f'<div class="side-label">{e(s["theme_label"])}</div>', 1)
    out = out.replace('<div class="side-tab">Theme</div>', f'<div class="side-tab">{e(s["theme_label"])}</div>', 1)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lang", default="es", choices=sorted(STRINGS))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or (
        ROOT / "output" / "presentations" / f"{datetime.now():%Y%m%d-%H%M}_seleccion-modelo" / "presentacion.html"
    )
    if out.exists():
        raise SystemExit(f"Ya existe {out}; no se sobrescribe.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(args.lang), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
