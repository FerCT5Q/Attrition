"""Deck «Evolución B → CQ» (Engineering, 9 diapositivas, inglés proyectado).

Parte de la base vigente de Julia (`config/presentations/model-selection-base.json`),
conserva cabecera, CSS, navegación y selector de tema, sustituye las 9
diapositivas y añade tres animaciones opcionales (diapositivas 3, 6 y 7).

Todas las cifras se leen por campo de los JSON archivados (plan final §5) y se
redondean sólo al mostrarlas. Escribe en la carpeta de salida:
`presentacion-eng.html`, `guion-presentador.md`, `evidence.json` y
`validation.json`.

Uso:
    python -B tools/presentations/build_model_evolution_b_cq.py [--out DIR]
    python -B tools/presentations/build_model_evolution_b_cq.py --record-browser-review DIR
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from datetime import datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/presentations/model-evolution-b-cq-20261010.json"
VERIFY = ROOT / ".agents/skills/build-html-presentation/scripts/verify_deck.py"
CQ_TOLERANCE = 1e-8
JARGON = ("hazard", "cloglog", "brier", "pr-auc", "log-loss", "bootstrap", "fold", "bias")


# ---------------------------------------------------------------------------
# Formato visible
# ---------------------------------------------------------------------------

def fmt(value: float, decimals: int = 1) -> str:
    """Entero sin decimales; resto con `decimals` como máximo; positivo ~0 → <0.1."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        raise ValueError("Cifra ausente")
    rounded = round(float(value), decimals)
    if float(value) > 0 and rounded == 0:
        return "<0." + "0" * (decimals - 1) + "1" if decimals else "<1"
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.{decimals}f}"


def pct(value: float, decimals: int = 1) -> str:
    return fmt(value, decimals) + "%"


def get(data: dict, path: str):
    """Lee `a.b["30"].c` con error explícito si falta un campo."""
    node = data
    for part in re.findall(r'[^.\[\]"]+', path):
        if isinstance(node, list):
            match = [p for p in node if isinstance(p, dict) and p.get("id") == part]
            if not match:
                raise KeyError(f"Falta el periodo {part!r} en {path}")
            node = match[0]
            continue
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"Falta el campo {path} (en {part!r})")
        node = node[part]
    if node is None:
        raise KeyError(f"Campo vacío: {path}")
    return node


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Cifras (plan §5)
# ---------------------------------------------------------------------------

class Evidence:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.records: list[dict] = []
        self.cache: dict[str, dict] = {}

    def load(self, sid: str) -> dict:
        if sid not in self.cache:
            self.cache[sid] = json.loads((ROOT / self.cfg["sources"][sid]).read_text(encoding="utf-8"))
        return self.cache[sid]

    def field(self, sid: str, path: str):
        return get(self.load(sid), path)

    def add(self, slide, fid, sid, fields, value, formula, shown, measure=None, period=None):
        self.records.append({
            "slide": slide, "id": fid, "source": sid, "source_path": self.cfg["sources"][sid],
            "fields": fields, "value": value, "formula": formula, "shown": shown,
            "error_measure": measure, "period": period,
        })
        return shown


def compute(ev: Evidence) -> dict:
    f: dict = {}
    s30 = 'summary.{m}.scenarios["30"]'
    p30 = 'periods.{p}.evaluation.{m}.scenarios["30"].metrics'

    # Diapositiva 5 · B frente a C (4 periodos)
    b = ev.field("S08", 'summary["30"].B_cuts.metrics')
    c = ev.field("S08", 'summary["30"].C_Bcuts.metrics')
    cmpc = ev.field("S08", 'summary["30"].C_Bcuts')
    f["b_cap"] = ev.add(5, "b_capture", "S08", ['summary["30"].B_cuts.metrics.capture_percent'], b["capture_percent"], "valor", pct(b["capture_percent"]), period="4 periods")
    f["cb_cap"] = ev.add(5, "c_capture_4p", "S08", ['summary["30"].C_Bcuts.metrics.capture_percent'], c["capture_percent"], "valor", pct(c["capture_percent"]), period="4 periods")
    f["b_gap"] = ev.add(5, "b_gap", "S08", ['summary["30"].B_cuts.metrics.group_mae_pp'], b["group_mae_pp"], "valor", fmt(b["group_mae_pp"]), "group_mae_pp", "4 periods")
    f["cb_gap"] = ev.add(5, "c_gap_4p", "S08", ['summary["30"].C_Bcuts.metrics.group_mae_pp'], c["group_mae_pp"], "valor", fmt(c["group_mae_pp"]), "group_mae_pp", "4 periods")
    red_bc = 100 * (1 - c["group_mae_pp"] / b["group_mae_pp"])
    f["bc_red"] = ev.add(5, "bc_gap_reduction", "S08", ["group_mae_pp B_cuts", "group_mae_pp C_Bcuts"], red_bc, "100*(1-C/B)", pct(red_bc, 0), "group_mae_pp", "4 periods")
    f["bc_diff"] = cmpc["comparison"]["difference_vs_B_cuts_pp"]
    f["bc_ci"] = cmpc["comparison"]["ci95_pp"]
    f["bc_wins"] = (cmpc["winning_periods"], cmpc["losing_periods"])
    ev.add(5, "bc_capture_diff_notes", "S08", ['summary["30"].C_Bcuts.comparison'], f["bc_diff"], "C-B (guion)", f"+{fmt(f['bc_diff'], 2)} [{fmt(f['bc_ci'][0], 2)}, {fmt(f['bc_ci'][1], 2)}]", period="4 periods")
    b40 = ev.field("S08", 'summary["40"].B_cuts.metrics.capture_percent')
    c40 = ev.field("S08", 'summary["40"].C_Bcuts.metrics.capture_percent')
    f["b40"], f["c40"] = pct(b40), pct(c40)
    folds = ev.field("S08", "folds")
    f["bc_periods"] = len(folds)
    if f["bc_periods"] != 4:
        raise ValueError("S08 debe tener 4 periodos")

    # Diapositiva 6 · C frente a CQ (2 periodos), S12 con S11 de control
    s12 = {m: ev.field("S12", s30.format(m=m)) for m in ("C", "CQ", "D", "RSF_Q")}
    s11 = {m: ev.field("S11", s30.format(m=m)) for m in ("C", "CQ", "disjoint")}
    for key in ("capture_percent", "group_snapshot_mae_pp"):
        for m in ("C", "CQ"):
            if abs(s12[m][key] - s11[m][key]) > CQ_TOLERANCE:
                raise ValueError(f"{m}.{key} difiere entre S11 y S12")
    if ev.cfg["cq_version"] != "engineering-c-qvoice-20261008-v1":
        raise ValueError("Versión CQ inesperada")
    cap_c, cap_cq = s12["C"]["capture_percent"], s12["CQ"]["capture_percent"]
    gap_c, gap_cq = s12["C"]["group_snapshot_mae_pp"], s12["CQ"]["group_snapshot_mae_pp"]
    f["c_cap"] = ev.add(6, "c_capture", "S12", [s30.format(m="C") + ".capture_percent"], cap_c, "valor", pct(cap_c), period="2 periods")
    f["cq_cap"] = ev.add(1, "cq_capture", "S12", [s30.format(m="CQ") + ".capture_percent"], cap_cq, "valor", pct(cap_cq), period="2 periods")
    gain = cap_cq - cap_c
    f["gain"] = ev.add(1, "cq_gain_vs_c", "S12", ["capture_percent CQ", "capture_percent C"], gain, "CQ-C", "+" + fmt(gain), period="2 periods")
    random_cov = s12["CQ"]["coverage_percent"]
    f["random"] = ev.add(6, "random_reference", "S12", [s30.format(m="CQ") + ".coverage_percent"], random_cov, "selección al azar = cobertura", pct(random_cov, 0), period="2 periods")
    f["lift"] = fmt(s12["CQ"]["lift"], 2)
    red_cq = 100 * (1 - gap_cq / gap_c)
    f["cq_red"] = ev.add(1, "cq_gap_reduction", "S12", ["group_snapshot_mae_pp C", "group_snapshot_mae_pp CQ"], red_cq, "100*(1-CQ/C)", pct(red_cq), "group_snapshot_mae_pp", "2 periods")
    f["cq_gap"] = ev.add(1, "cq_group_gap", "S12", [s30.format(m="CQ") + ".group_snapshot_mae_pp"], gap_cq, "valor; salidas por cada 100 personas", fmt(gap_cq), "group_snapshot_mae_pp", "2 periods")
    f["pred"] = {m: fmt(s12[m]["predicted_percent"]) for m in ("C", "CQ")}
    f["obs"] = {m: fmt(s12[m]["observed_percent"]) for m in ("C", "CQ")}
    f["over"] = {m: fmt(s12[m]["bias_pp"], 2) for m in ("C", "CQ")}
    f["over_red"] = fmt(100 * (1 - s12["CQ"]["bias_pp"] / s12["C"]["bias_pp"]), 0)
    ev.add(6, "overestimate_notes", "S12", ["bias_pp C", "bias_pp CQ"], s12["CQ"]["bias_pp"] / s12["C"]["bias_pp"] - 1, "CQ/C-1 (sólo guion)", f"-{f['over_red']}%", period="2 periods")

    periods = {}
    for pid in ("aug_dec_2025", "jan_feb_2026"):
        row = {}
        for m in ("C", "CQ", "D", "RSF_Q"):
            row[m] = ev.field("S12", p30.format(p=pid, m=m))
        row["disjoint"] = ev.field("S11", p30.format(p=pid, m="disjoint"))
        row["people"] = ev.field("S12", f"periods.{pid}.people")
        periods[pid] = row
    f["periods"] = {}
    for pid, label in (("aug_dec_2025", "Aug–Dec 2025"), ("jan_feb_2026", "Jan–Feb 2026")):
        pc, pq = periods[pid]["C"]["capture_percent"], periods[pid]["CQ"]["capture_percent"]
        reading = "tied" if abs(pq - pc) < 1e-9 else ("better" if pq > pc else "worse")
        f["periods"][pid] = {"label": label, "c": pct(pc), "cq": pct(pq), "reading": reading,
                             "worst_c": fmt(periods[pid]["C"]["worst_publishable_group_error_pp"], 2),
                             "worst_cq": fmt(periods[pid]["CQ"]["worst_publishable_group_error_pp"], 2),
                             "people": periods[pid]["people"],
                             "rsf_over": fmt(periods[pid]["RSF_Q"]["bias_pp"], 2)}
        ev.add(6, f"period_{pid}", "S12", [p30.format(p=pid, m=m) + ".capture_percent" for m in ("C", "CQ")], [pc, pq], "C, CQ; lectura por igualdad", f"{pct(pc)} → {pct(pq)} ({reading})", period=pid)
    readings = [p["reading"] for p in f["periods"].values()]
    if readings != ["better", "tied"]:
        raise ValueError(f"Lectura por periodo inesperada: {readings}")
    cq_ci = [i for i in ev.field("S11", "intervals") if (i["left"], i["right"], i["metric"]) == ("CQ", "C", "capture30")]
    if len(cq_ci) != 1:
        raise KeyError("Falta el intervalo CQ-C capture30 en S11")
    f["cq_ci"] = [fmt(v, 2) for v in cq_ci[0]["ci95"]]

    # Diapositiva 8 · pruebas adicionales
    gap_ref = gap_cq
    def rel(v):
        return 100 * (v / gap_ref - 1)
    rows = []
    rows.append({"key": "CQ", "src": "S12", "cap": cap_cq, "gap": None, "jan": periods["jan_feb_2026"]["CQ"]["capture_percent"], "reading": "Reference"})
    rows.append({"key": "disjoint", "src": "S11", "cap": s11["disjoint"]["capture_percent"], "gap": rel(s11["disjoint"]["group_snapshot_mae_pp"]), "jan": periods["jan_feb_2026"]["disjoint"]["capture_percent"], "reading": "Same share; estimates further from actual"})
    rows.append({"key": "D", "src": "S12", "cap": s12["D"]["capture_percent"], "gap": rel(s12["D"]["group_snapshot_mae_pp"]), "jan": periods["jan_feb_2026"]["D"]["capture_percent"], "reading": "Slightly closer estimates; fewer exits found in the latest period"})
    rows.append({"key": "RSF_Q", "src": "S12", "cap": s12["RSF_Q"]["capture_percent"], "gap": rel(s12["RSF_Q"]["group_snapshot_mae_pp"]), "jan": periods["jan_feb_2026"]["RSF_Q"]["capture_percent"], "reading": "Similar share; estimates further from actual"})
    for r in rows:
        r["cap_s"], r["jan_s"] = pct(r["cap"]), pct(r["jan"])
        if r["gap"] is None:
            r["gap_s"] = "—"
        else:
            r["gap_s"] = f"{pct(abs(r['gap']))} {'larger' if r['gap'] > 0 else 'smaller'}"
        ev.add(8, f"row_{r['key']}", r["src"], ["capture_percent", "group_snapshot_mae_pp", "jan_feb_2026 capture_percent"], [r["cap"], r["gap"], r["jan"]], "100*(error_alt/error_CQ-1)", f"{r['cap_s']} · {r['gap_s']} · {r['jan_s']}", "group_snapshot_mae_pp", "2 periods")
    f["rows"] = rows
    dec = ev.field("S12_decision", "promote_D")
    if dec is not False:
        raise ValueError("S12 indica promote_D distinto de false")
    f["d_red"] = ev.field("S12_decision", "relative_group_snapshot_error_reduction")
    f["d_floor"] = ev.field("S12_decision", "common_guards.period_floor")
    dci = ev.field("S12", "intervals.capture30_pp")
    f["d_ci"] = (fmt(dci["difference_D_minus_CQ"]), fmt(dci["ci95"][0]), fmt(dci["ci95"][1]))
    f["c_updated"] = pct(ev.field("S12", s30.format(m="C_updated") + ".capture_percent"))

    # Diapositiva 3 · grupos de B (S04)
    final = ev.field("S04", "final")
    design = ev.field("S04", "design")
    groups = final["all_groups"]
    f["groups"] = ev.add(3, "groups_eligible", "S04", ["final.groups_eligible"], final["groups_eligible"], "valor", str(final["groups_eligible"]))
    f["min_people"] = ev.add(3, "min_group_people", "S04", ["design.min_group_people"], design["min_group_people"], "valor", f"{design['min_group_people']}+")
    if min(g["people"] for g in groups) < design["min_group_people"] or len(groups) != final["groups_eligible"]:
        raise ValueError("Grupos de S04 incoherentes con el mínimo publicado")
    f["snapshot"] = final["snapshot"]
    parts = {k: sorted({g["parts"][k] for g in groups}) for k in ("antiguedad", "salidas_equipo", "nivel")}
    combos = math.prod(len(v) for v in parts.values())
    f["combos"] = ev.add(3, "possible_combinations", "S04", ["final.all_groups[].parts"], combos, "producto de valores distintos por corte", str(combos))
    f["parts"] = parts

    # Diapositiva 4 · B + QVoice
    variants = ev.field("S05", "variants")
    better = sum(1 for v in variants if v["decision"]["checks"]["ranking_vs_control"])
    all_ok = sum(1 for v in variants if all(v["decision"]["checks"].values()))
    q4 = [v for v in variants if v["id"] == "intent_q4"][0]["decision"]["checks"]
    f["variants"] = ev.add(4, "survey_variants", "S05", ["variants[]"], len(variants), "conteo", str(len(variants)))
    ev.add(4, "variants_better_ranking", "S05", ["variants[].decision.checks.ranking_vs_control"], better, "conteo true", str(better))
    ev.add(4, "variants_all_checks", "S05", ["variants[].decision.checks"], all_ok, "conteo todas true", "None" if all_ok == 0 else str(all_ok))
    if better != len(variants) or all_ok != 0:
        raise ValueError("S05 no respalda el texto de la diapositiva 4")
    f["q4"] = (sum(q4.values()), len(q4))
    s06 = ev.field("S06", "decision.checks")
    if not (s06["ranking_vs_availability"] and not s06["calibration_error_pp_vs_control"]):
        raise ValueError("S06 no respalda el texto de la diapositiva 4")
    cal = ev.field("S07", "calibration_details")
    fitted = [c["target"] for c in cal if c["target"] != "final" and c["status"] == "fitted"]
    checks7 = ev.field("S07", "checks.jan_feb_2026")
    if fitted != ["jan_feb_2026"] or any(checks7.values()):
        raise ValueError("S07 no respalda el texto de la diapositiva 4")

    # Privacidad
    for sid in ("S11", "S12"):
        if ev.field(sid, "employee_level_rows_persisted") is not False or ev.field(sid, "individual_scores_published") is not False:
            raise ValueError(f"{sid} no confirma ausencia de filas o scores individuales")
    return f


# ---------------------------------------------------------------------------
# Diapositivas
# ---------------------------------------------------------------------------

TENURE = {"<1 año": "<1 yr", "1-2 años": "1–2 yrs", "2-3 años": "2–3 yrs", "3-5 años": "3–5 yrs", "5-10 años": "5–10 yrs", "10+ años": "10+ yrs"}
TENURE_ORDER = list(TENURE)
EXITS = {"con salidas": "With team exits", "sin salidas": "No team exits"}
LEVEL = {"entrada": "Entry", "medio": "Mid", "alto": "Senior"}
LEVEL_ORDER = ["entrada", "medio", "alto"]
SRC_POP = "Engineering · active regular employees, excl. RF360"


def anim_ctrl(name: str) -> str:
    return (f'<div class="anim-ctrl" role="group" aria-label="Animation controls">'
            f'<button type="button" class="wt-btn" data-anim-act="play" data-anim="{name}">▶ Play</button>'
            f'<button type="button" class="wt-btn" data-anim-act="replay" data-anim="{name}">↺ Replay</button>'
            f'<button type="button" class="wt-btn" data-anim-act="all" data-anim="{name}">Show all</button></div>')


def heading(title: str, subtitle: str = "", strip: str = "") -> str:
    sub = f'<p class="slide-subtitle">{subtitle}</p>' if subtitle else ""
    st = f'<div class="period-strip" title="Results compare only within this set of periods"><span>◷</span>{strip}</div>' if strip else ""
    return f'<div class="slide-heading"><div><h2 class="slide-title-text">{title}</h2>{sub}</div>{st}</div>'


def slides(f: dict, cfg: dict) -> list[str]:
    vn = cfg["visible_names"]
    risk_groups = cfg["risk_groups"]["label_en"]
    pa, pj = f["periods"]["aug_dec_2025"], f["periods"]["jan_feb_2026"]
    strip2 = "2 historical periods · Aug 2025–Feb 2026"
    src2 = f"{SRC_POP} · Aug–Dec 2025 and Jan–Feb 2026 snapshots · 6-month follow-up · 9–10 Oct 2026 analyses"
    out = []

    # 1 · Decisión
    out.append(f'''<div class="slide-stage data-context" id="slide-1">
<div class="cover" style="grid-row: 1 / -1;"><div class="cover-kicker">Engineering · Historical averages · Voluntary exits over the next 6 months · October 2026</div>
<h1 class="cover-title">We selected {risk_groups} covering 30% of people.<br>These groups contained {f["cq_cap"]} of all voluntary exits.</h1>
<div class="cover-chips">
<div class="cover-chip cover-kpi"><b>{f["cq_red"]} less error</b><span>vs expanded HR (C) · CQ's average gap per group: ~{f["cq_gap"]} exit per 100 people</span></div>
<div class="cover-chip cover-kpi"><b>{f["gain"]} points</b><span>more of all observed exits in the selected groups, compared with expanded HR (C)</span></div>
<div class="cover-chip cover-kpi"><b>Same group definitions</b><span>Years at Qualcomm · team exits · level</span></div></div>
<div class="cover-decision"><b>Selected:</b> {vn["CQ"]}, for the next validation stage. A pilot has not started.</div>
<div class="src">{src2} · S12, S11, S01</div></div>
</div>''')

    # 2 · Agenda
    items = [("3–4", "Our starting point", f"{vn['B']} and the first survey tests"),
             ("5–7", "What improved", f"{vn['C']} and employee feedback (CQ)"),
             ("8", "Further checks", "Survey mixes, additional signals (D) and an alternative method"),
             ("9", "Decision and next steps", "Confirm, review, pilot")]
    ag = "".join(f'<article class="card ag-item"><div class="ag-num">{i}</div><div class="ag-head">{h}</div><div class="ag-slides">Slide{"s" if "–" in s else ""} {s}</div><div class="ag-body">{b}</div></article>' for i, (s, h, b) in enumerate(items, 1))
    out.append(f'''<div class="slide-stage stage-3rows data-context" id="slide-2">
{heading("From our starting model to today's choice")}
<div class="ag-wrap"><div class="agenda agenda-4">{ag}</div>
<div class="flow" role="img" aria-label="Work path: Core HR model B, then expanded HR model C, then HR plus employee feedback CQ, selected. Related tests branch off in grey.">
<div class="flow-main"><div class="flow-node">Core HR (B)</div><div class="flow-arrow">→</div><div class="flow-node">Expanded HR (C)</div><div class="flow-arrow">→</div><div class="flow-node sel">HR + feedback (CQ) <span class="mark m-yes">✓ Selected</span></div></div>
<div class="flow-branches"><div class="flow-branch">↳ First survey tests</div><div></div><div></div><div></div><div class="flow-branch">↳ Survey mixes · D · alternative method</div></div></div></div>
<div class="src">Results come from two sets of historical checks — 4 periods (Feb 2024–Jan 2026) and 2 recent periods (Aug 2025–Feb 2026). Numbers compare only within each set.</div>
</div>''')

    # 3 · Punto de partida (animación A)
    ten = "".join(f'<span class="chip-g">{TENURE[t]}</span>' for t in TENURE_ORDER if t in f["parts"]["antiguedad"])
    exi = "".join(f'<span class="chip-g">{EXITS[t]}</span>' for t in ("con salidas", "sin salidas") if t in f["parts"]["salidas_equipo"])
    lev = "".join(f'<span class="chip-g">{LEVEL[t]}</span>' for t in LEVEL_ORDER if t in f["parts"]["nivel"])
    snap = datetime.strptime(f["snapshot"], "%Y-%m-%d").strftime("%d %b %Y").lstrip("0")
    commits = [
        ("m-yes", "✓ Done", "Test the remaining model type (random survival forest)", "slide 8"),
        ("m-yes", "✓ Done", "Add more signals: QVoice and time at level", "slides 5–7"),
        ("m-yes", "✓ Modest improvement", "Adopt changes only if they improve the model", "CQ better in one period, tied in the other — slide 6."),
        ("m-part", "◐ Further validation needed", "Reduce overestimates in the highest-risk group", "some group estimates still need work"),
        ("m-open", "○ Open", "Check fairness across groups", "not found in the studies reviewed"),
    ]
    cl = "".join(f'<li><div class="cm-head">{h}</div><div class="cm-status"><span class="mark {c}">{s}</span> — {d}</div></li>' for c, s, h, d in commits)
    out.append(f'''<div class="slide-stage stage-3rows data-context" id="slide-3">
{heading("We started with understandable groups — what we completed and what remains")}
<div class="s3-grid">
<article class="card split-card anim" data-anim-name="A">
<div class="split-top"><div class="side-head">How the Core HR model (B) forms groups</div>{anim_ctrl("A")}</div>
<div class="split" role="img" aria-label="B splits all of Engineering by years at Qualcomm, then team exits, then level: {f["groups"]} groups eligible, each with {f["min_people"]} people">
<div class="split-col" data-step="1"><div class="split-k">Start</div><div class="split-h">All Engineering</div><div class="split-chips"><span class="chip-g big">Active regular employees</span></div></div>
<div class="split-arrow" data-step="2">→</div>
<div class="split-col" data-step="2"><div class="split-k">Split 1</div><div class="split-h">Years at Qualcomm</div><div class="split-chips">{ten}</div></div>
<div class="split-arrow" data-step="3">→</div>
<div class="split-col" data-step="3"><div class="split-k">Split 2</div><div class="split-h">Team exits</div><div class="split-chips">{exi}</div></div>
<div class="split-arrow" data-step="4">→</div>
<div class="split-col" data-step="4"><div class="split-k">Split 3</div><div class="split-h">Level</div><div class="split-chips">{lev}</div></div>
</div>
<div class="split-result" data-step="4"><b>{f["groups"]} groups</b> eligible on {snap} · each with {f["min_people"]} people <span class="muted">· {f["combos"]} possible combinations; smaller ones are pooled</span></div>
<div class="split-foot"><span>B used information HR already tracks.</span><span>Groups make results easier to discuss and act on.</span></div>
</article>
<article class="card commit-card"><div class="side-head">Since our last update</div><ul class="commits">{cl}</ul></article>
</div>
<div class="src">Groups summarize many people; no individual predictions are shown · Engineering, {snap} snapshot · S04, S02, S12, S13, S01</div>
</div>''')

    # 4 · Primeras pruebas con encuesta
    steps4 = [(f'{f["variants"]} survey variants evaluated', f'All {f["variants"]} ranked risk better than B', "m-no", "✗", "None passed every agreed check", "S05"),
              ("Broader combinations", "Useful beyond whether people answered", "m-part", "◐", "Overall estimates still off", "S06"),
              ("Added adjustment to estimated risk", "Better fit to earlier data", "m-no", "✗", "Did not improve the Jan–Feb 2026 test", "S07")]
    st = "".join(f'<article class="card st4"><div class="pipe-num">Step {i}</div><div class="st4-head">{h}</div><div class="st4-row"><span class="mark m-yes">✓</span><span>{g}</span></div><div class="st4-row"><span class="mark {c}">{s}</span><span>{bad}</span></div><div class="st4-src">{src}</div></article>' for i, (h, g, c, s, bad, src) in enumerate(steps4, 1))
    out.append(f'''<div class="slide-stage stage-3rows data-context" id="slide-4">
{heading("Survey answers helped rank risk, but the first tests fell short", f"{vn['B_qvoice']} · what improved and what was missing")}
<div class="s4n"><div class="st4-grid">{st}</div>
<div class="fix">The feedback was useful — we kept it and changed the base model.</div></div>
<div class="src">Engineering · 2 historical periods · 8 Oct 2026 analyses · S05, S06, S07</div>
</div>''')

    # 5 · B frente a C
    out.append(f'''<div class="slide-stage stage-3rows data-context" id="slide-5">
{heading("The expanded HR model kept the group definitions and cut the gap by " + f["bc_red"], f"Core HR (B) vs Expanded HR (C) · same group definitions · {risk_groups} covering 30% of Engineering", "4 historical periods · Feb 2024–Jan 2026")}
<div class="s5-grid">
<article class="card s5-card"><table class="cmp" aria-label="Core HR model B versus expanded HR model C">
<thead><tr><th scope="col">Measure</th><th scope="col" class="num">Core HR (B)</th><th scope="col" class="num rec">Expanded HR (C)</th></tr></thead>
<tbody><tr><td>Share of exits in {risk_groups}</td><td class="num">{f["b_cap"]}</td><td class="num rec">{f["cb_cap"]}</td></tr>
<tr><td>Average gap per group, per 100 people<small>gap = difference between estimated and actual exits per 100 people, by group</small></td><td class="num">{f["b_gap"]}</td><td class="num rec">{f["cb_gap"]}</td></tr>
<tr class="hlrow"><td>Gap change</td><td class="num muted">—</td><td class="num rec"><b>{f["bc_red"]} smaller</b></td></tr></tbody></table></article>
<div class="s5-side"><div class="tags"><span class="tag">More HR information, incl. time at level</span><span class="tag">Same group definitions</span><span class="tag">Similar share of exits</span></div>
<div class="note-box">The change in share of exits was small and uncertain; the gain is mainly in closer estimates. {f["bc_red"]} is a relative reduction of the group gap.</div></div>
</div>
<div class="src">{SRC_POP} · 4 historical periods · 6-month exits · 8 Oct 2026 analysis · S08, S09</div>
</div>''')

    # 6 · C frente a CQ (animación B)
    def w(v):
        return f"{float(v.rstrip('%')) / 50 * 100:.2f}%"
    out.append(f'''<div class="slide-stage stage-3rows data-context" id="slide-6">
{heading(f'Adding employee feedback found modestly more exits in <span style="white-space: nowrap">{risk_groups}</span>', f"Share of observed exits in {risk_groups} covering 30% of Engineering · next 6 months", strip2)}
<div class="s6n anim" data-anim-name="B">
<article class="card chart-card"><div class="split-top"><div class="side-head">Share of exits in {risk_groups}</div>{anim_ctrl("B")}</div>
<div class="bars" role="img" aria-label="Random 30% holds about 30% of exits; expanded HR model C {f["c_cap"]}; HR plus feedback CQ {f["cq_cap"]}, {f["gain"]} points more">
<div class="bars-plot">
<div class="rand" data-step="1" style="left:{w(f["random"])}"><span>Random {f["random"]}</span></div>
<div class="brow" data-step="2"><div class="blabel">{vn["C"].replace("model ", "")}</div><div class="btrack"><div class="bfill ctx" style="width:{w(f["c_cap"])}"></div><div class="bval" style="left:{w(f["c_cap"])}">{f["c_cap"]}</div></div></div>
<div class="brow hl" data-step="3"><div class="blabel">HR + feedback (CQ)</div><div class="btrack"><div class="bfill" style="width:{w(f["cq_cap"])}"></div><div class="bval" style="left:{w(f["cq_cap"])}">{f["cq_cap"]} <em>{f["gain"]} points</em></div></div></div>
</div>
<div class="axis"><span style="left:0%">0%</span><span style="left:20%">10%</span><span style="left:40%">20%</span><span style="left:60%">30%</span><span style="left:80%">40%</span><span style="left:100%">50%</span></div>
</div>
<div class="periods" data-step="4"><span><b>{pa["label"]}:</b> {pa["c"]} → {pa["cq"]} ({pa["reading"]})</span><span><b>{pj["label"]}:</b> {pj["c"]} → {pj["cq"]} ({pj["reading"]})</span></div>
</article>
<article class="card kpi-card" data-step="4"><div class="big-num">{f["cq_red"]}</div><div class="kpi-head">smaller average gap per group</div><div class="kpi-body">difference between estimated and actual exits; relative reduction</div>
<div class="kpi-note">Historical, average results. Some group estimates still need improvement.</div></article>
</div>
<div class="src">{src2} · S12, S11</div>
</div>''')

    # 7 · Cómo funciona CQ (animación C)
    stations = [("1", "HR information", "Work history, team context, time at level"),
                ("2", "Employee feedback", "Career goals · overall feedback · wellbeing · confidence"),
                ("3", risk_groups.capitalize(), "Years at Qualcomm · team exits · level")]
    stn = []
    for i, (n, h, b) in enumerate(stations, 1):
        if i > 1:
            stn.append(f'<div class="st-link" data-step="{i}"><span>{"adds to the estimate" if i == 2 else "orders the groups"}</span>→</div>')
        stn.append(f'<div class="station{" fb" if i == 2 else ""}" data-step="{i}"><div class="st-num">{n}</div><div class="st-head">{h}</div><div class="st-body">{b}</div></div>')
    out.append(f'''<div class="slide-stage stage-3rows data-context" id="slide-7">
{heading("Feedback refines risk estimates within the same familiar groups", vn["CQ"] + " · how the pieces fit")}
<div class="s7n"><article class="card anim st-card" data-anim-name="C"><div class="split-top"><div></div>{anim_ctrl("C")}</div>
<div class="stations" role="img" aria-label="HR information and employee feedback refine risk estimates for the same group definitions. {escape(cfg['risk_groups']['definition_en'], quote=True)}">{"".join(stn)}</div></article>
<div class="s7-notes"><div class="fix">Only group-level results are reported; no individual scores are published.</div>
<div class="note-box">Final September version shown. Historical checks used the model available at each date; the final version still needs a check on later data.</div></div></div>
<div class="src">Engineering · group-level reporting · S01, S10, S11, S14</div>
</div>''')

    # 8 · Pruebas adicionales
    names = {"CQ": vn["CQ"], "disjoint": vn["disjoint"], "D": vn["D"], "RSF_Q": vn["RSF_Q"]}
    tr = []
    for r in f["rows"]:
        sel = r["key"] == "CQ"
        name = names[r["key"]] + (' <span class="sel-badge">Selected</span>' if sel else "")
        tr.append(f'<tr class="{"chosen" if sel else ""}"><td>{name}</td><td class="num">{r["cap_s"]}</td><td class="num">{r["gap_s"]}</td><td class="num">{r["jan_s"]}</td><td class="reading">{r["reading"]}</td></tr>')
    d = [r for r in f["rows"] if r["key"] == "D"][0]
    out.append(f'''<div class="slide-stage stage-3rows data-context" id="slide-8">
{heading("Further tests did not justify replacing CQ", f"Share of exits and gap per group · {risk_groups} covering 30% of Engineering", strip2)}
<div class="s8n"><article class="card"><table class="tests" aria-label="Further tests compared with the selected model CQ">
<thead><tr><th scope="col">Model</th><th scope="col" class="num">Share of exits, 30%</th><th scope="col" class="num">Gap per group vs CQ</th><th scope="col" class="num">Jan–Feb 2026 share</th><th scope="col">Reading</th></tr></thead>
<tbody>{"".join(tr)}</tbody></table></article>
<div class="note-box"><b>D:</b> slightly closer estimates ({d["gap_s"]} gap), but fewer exits found in Jan–Feb 2026 ({d["jan_s"]} vs {f["rows"][0]["jan_s"]}) — below its own adoption rules.</div>
<div class="s8-note">New team-history signals were tested in D but not kept in its final version.</div></div>
<div class="src">{src2} · S12, S11</div>
</div>''')

    # 9 · Siguientes pasos
    steps9 = [("Check a new period", "Evaluate the final September version after its training date, including group-level gaps"),
              ("Review differences across groups", "Confirm or complete the fairness review"),
              ("Confirm how survey data may be used", "Agree the scope with HR before any pilot"),
              ("Prepare a limited pilot", "Scope, owners, capacity (e.g. the 30%) and measures, before starting")]
    li = "".join(f"<li>{h}<small>{b}</small></li>" for h, b in steps9)
    out.append(f'''<div class="slide-stage stage-3rows data-context" id="slide-9">
{heading("Next: confirm on new data, review groups, then a limited pilot", "")}
<div class="s9n"><div class="decision-line">{vn["CQ"]} remains our selected model.</div><ol class="next-list n9">{li}</ol></div>
<div class="next-after">Proposed steps — not yet scheduled or approved. Historical results support the selection; the effect of retention actions has not been measured.</div>
</div>''')
    return out


CSS = r"""
    /* ===== Evolución B → CQ (2026-10-10) ===== */
    .slide-heading { gap: 24px; }
    .period-strip { flex-shrink: 0; display: inline-flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700; padding: 7px 14px; border-radius: 999px; border: 1px dashed var(--border-strong); color: var(--text-muted); background: var(--bg-surface); white-space: nowrap; }
    .period-strip span { color: var(--accent); font-size: 17px; }
    .muted { color: var(--text-muted); }
    .m-open { color: var(--text-muted); }
    .cover { gap: 24px; }
    .cover-decision { font-size: 21px; line-height: 1.4; max-width: 1240px; padding: 12px 18px; border-radius: 10px; border: 2px solid var(--accent); background: var(--accent-soft); }
    .cover .src { align-self: start; font-size: 13.5px; }
    .cover-kpi b { font-size: 32px; }
    /* Agenda */
    .ag-wrap { display: flex; flex-direction: column; justify-content: center; gap: 34px; }
    .agenda-4 { grid-template-columns: repeat(4, 1fr); align-self: stretch; }
    .ag-body { font-size: 17px; }
    .flow { display: flex; flex-direction: column; gap: 8px; padding: 0 6px; }
    .flow-main, .flow-branches { display: grid; grid-template-columns: 1fr 48px 1fr 48px 1fr; align-items: center; }
    .flow-node { font-size: 19px; font-weight: 700; text-align: center; padding: 12px 10px; border-radius: 12px; border: 1px solid var(--border-subtle); background: var(--bg-surface); }
    .flow-node.sel { border: 2px solid var(--accent); background: var(--accent-soft); color: var(--accent); }
    .flow-node.sel .mark { font-size: 16px; margin-left: 6px; }
    .flow-arrow { text-align: center; font-size: 26px; color: var(--text-muted); }
    .flow-branch { font-size: 16px; color: var(--text-muted); text-align: center; border: 1px dashed var(--border-subtle); border-radius: 10px; padding: 6px 8px; background: color-mix(in oklab, var(--ctx) 18%, transparent); }
    .stage-3rows .src { font-size: 13.5px; }
    #slide-2 .src { font-size: 16px; color: var(--text-muted); }
    /* Diapositiva 3 */
    .s3-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 22px; min-height: 0; }
    .split-card { padding: 18px 22px; gap: 14px; justify-content: space-between; }
    .split-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
    .anim-ctrl { display: flex; gap: 6px; flex-shrink: 0; }
    .anim-ctrl .wt-btn { font-size: 14px; padding: 5px 12px; }
    .split { display: grid; grid-template-columns: 1fr 30px 1fr 30px 1fr 30px 1fr; align-items: start; }
    .split-col { display: flex; flex-direction: column; gap: 6px; padding: 8px; margin: -8px; border-radius: 12px; }
    .split-k { font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; color: var(--accent); }
    .split-h { font-size: 19px; font-weight: 700; line-height: 1.2; min-height: 46px; }
    .split-chips { display: flex; flex-direction: column; gap: 6px; }
    .chip-g { font-size: 16px; font-weight: 600; padding: 6px 10px; border-radius: 8px; border: 1px solid var(--border-subtle); background: var(--bg-surface-2); text-align: center; }
    .chip-g.big { padding: 40px 10px; font-size: 17px; background: var(--accent-soft); border-color: var(--border-strong); }
    .split-arrow { font-size: 24px; color: var(--accent); text-align: center; padding-top: 96px; }
    .split-result { font-size: 18px; padding: 10px 16px; border-radius: 10px; border-left: 4px solid var(--accent); background: var(--accent-soft); }
    .split-result b { color: var(--accent); font-size: 21px; }
    .split-result .muted { font-size: 16px; }
    .split-foot { display: flex; gap: 28px; font-size: 17px; color: var(--text-muted); }
    .commit-card { padding: 18px 20px; gap: 10px; }
    .commits { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
    .commits li { border-bottom: 1px solid var(--border-subtle); padding-bottom: 9px; }
    .commits li:last-child { border-bottom: none; padding-bottom: 0; }
    .cm-head { font-size: 17px; font-weight: 700; line-height: 1.3; }
    .cm-status { font-size: 16px; line-height: 1.35; color: var(--text-muted); margin-top: 3px; }
    .cm-status .mark { font-size: 16px; }
    /* Diapositiva 4 */
    .s4n { display: flex; flex-direction: column; justify-content: center; gap: 26px; }
    .st4-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 34px; }
    .st4 { position: relative; padding: 22px 24px; gap: 14px; }
    .st4:not(:last-child)::after { content: "→"; position: absolute; right: -27px; top: 44%; font-size: 26px; color: var(--accent); }
    .st4-grid > .card { overflow: visible; }
    .st4-head { font-size: 22px; font-weight: 700; line-height: 1.25; min-height: 56px; }
    .st4-row { display: grid; grid-template-columns: 30px 1fr; gap: 8px; font-size: 19px; line-height: 1.35; align-items: baseline; }
    .st4-row .mark { font-size: 21px; }
    .st4-src { font-size: 13px; color: var(--text-muted); margin-top: auto; }
    .fix { font-size: 20px; }
    /* Diapositiva 5 */
    .s5-grid { display: grid; grid-template-columns: 1.55fr 1fr; gap: 26px; align-items: center; }
    .s5-card { padding: 16px 22px; }
    .cmp { width: 100%; border-collapse: collapse; font-size: 19px; }
    .cmp th, .cmp td { padding: 16px 14px; border-bottom: 1px solid var(--border-subtle); text-align: left; vertical-align: middle; }
    .cmp th { white-space: nowrap; font-size: 15px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .05em; }
    .cmp .num { text-align: right; font-variant-numeric: tabular-nums; width: 25%; white-space: nowrap; }
    .cmp td.num { font-size: 30px; font-weight: 800; }
    .cmp td.rec { background: var(--accent-soft); color: var(--accent); }
    .cmp th.rec { color: var(--accent); }
    .cmp td small { display: block; font-size: 15px; color: var(--text-muted); margin-top: 4px; line-height: 1.35; }
    .cmp tr.hlrow td.num b { font-size: 26px; }
    .cmp tr:last-child td { border-bottom: none; }
    .s5-side { display: flex; flex-direction: column; gap: 20px; }
    .tags { display: flex; flex-direction: column; gap: 10px; }
    .tag { font-size: 18px; font-weight: 600; padding: 10px 16px; border-radius: 999px; border: 1px solid var(--border-strong); background: var(--bg-surface); }
    .tag::before { content: "✓ "; color: var(--accent); font-weight: 800; }
    .note-box { font-size: 18px; }
    /* Diapositiva 6 */
    .s6n { display: grid; grid-template-columns: 1.75fr 1fr; gap: 24px; min-height: 0; }
    .chart-card { padding: 18px 26px; gap: 18px; justify-content: space-between; }
    .bars { padding: 0 190px 0 0; margin: auto 0; }
    .bars-plot { position: relative; display: flex; flex-direction: column; gap: 30px; padding: 44px 0 14px; margin-left: 230px; border-left: 2px solid var(--text-muted); }
    .brow { position: relative; display: flex; align-items: center; height: 70px; }
    .blabel { position: absolute; right: calc(100% + 16px); width: 220px; text-align: right; font-size: 19px; font-weight: 600; line-height: 1.2; }
    .brow.hl .blabel { color: var(--accent); font-weight: 800; }
    .btrack { position: relative; width: 100%; height: 100%; }
    .bfill { height: 100%; background: var(--accent); border-radius: 0 8px 8px 0; transform-origin: left center; transition: transform 650ms ease, opacity 500ms; }
    .bfill.ctx { background: var(--ctx); }
    .bval { position: absolute; top: 50%; transform: translateY(-50%); padding-left: 12px; font-size: 26px; font-weight: 800; white-space: nowrap; }
    .brow.hl .bval { color: var(--accent); }
    .bval em { font-style: normal; font-size: 18px; font-weight: 800; margin-left: 10px; padding: 3px 10px; border-radius: 999px; background: var(--accent-soft); }
    .rand { position: absolute; top: 0; bottom: 0; border-left: 3px dashed var(--text-muted); z-index: 2; }
    .rand span { position: absolute; top: 4px; left: 8px; font-size: 16px; font-weight: 700; color: var(--text-muted); white-space: nowrap; }
    .axis { position: relative; height: 22px; margin-left: 230px; }
    .axis span { position: absolute; transform: translateX(-50%); font-size: 16px; color: var(--text-muted); }
    .periods { display: flex; gap: 14px; flex-wrap: wrap; font-size: 18px; }
    .periods span { padding: 8px 14px; border-radius: 10px; background: var(--bg-surface-2); border: 1px solid var(--border-subtle); }
    .kpi-card { justify-content: center; gap: 10px; padding: 26px 28px; border: 2px solid var(--accent); }
    .kpi-head { font-size: 24px; font-weight: 700; line-height: 1.25; }
    .kpi-body { font-size: 17px; color: var(--text-muted); line-height: 1.4; }
    .kpi-note { margin-top: 18px; font-size: 17px; line-height: 1.4; padding-top: 14px; border-top: 1px solid var(--border-subtle); }
    /* Diapositiva 7 */
    .s7n { display: flex; flex-direction: column; justify-content: center; gap: 22px; }
    .st-card { padding: 18px 24px 30px; gap: 8px; }
    .stations { display: grid; grid-template-columns: 1fr 150px 1fr 150px 1fr; align-items: center; }
    .station { padding: 24px 22px; border-radius: 16px; border: 1px solid var(--border-subtle); background: var(--bg-surface-2); display: flex; flex-direction: column; gap: 8px; min-height: 190px; }
    .station.fb { border: 2px solid var(--accent); background: var(--accent-soft); }
    .st-num { width: 38px; height: 38px; border-radius: 50%; background: var(--accent); color: var(--text-invert); display: grid; place-items: center; font-weight: 800; font-size: 18px; }
    .st-head { font-size: 23px; font-weight: 700; }
    .st-body { font-size: 18px; line-height: 1.4; }
    .st-link { text-align: center; font-size: 30px; color: var(--accent); line-height: 1.1; }
    .st-link span { display: block; font-size: 15px; font-weight: 700; color: var(--text-muted); }
    .s7-notes { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    /* Diapositiva 8 */
    .s8n { display: flex; flex-direction: column; justify-content: center; gap: 16px; }
    .tests { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 18px; line-height: 1.3; }
    .tests th, .tests td { padding: 13px 12px; border-bottom: 1px solid var(--border-subtle); text-align: left; vertical-align: middle; }
    .tests th { font-size: 14.5px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em; }
    .tests th:nth-child(1) { width: 30%; } .tests th:nth-child(2) { width: 13%; } .tests th:nth-child(3) { width: 15%; } .tests th:nth-child(4) { width: 14%; }
    .tests .num { text-align: right; font-variant-numeric: tabular-nums; }
    .tests td.num { font-size: 21px; font-weight: 700; }
    .tests td.reading { font-size: 16.5px; color: var(--text-muted); }
    .tests tr.chosen td { background: var(--accent-soft); font-weight: 700; }
    .tests tr.chosen td.num { color: var(--accent); }
    .tests tr:not(.chosen) td:first-child { color: var(--text-main); }
    .tests tr:last-child td { border-bottom: none; }
    .sel-badge { display: inline-block; margin-left: 8px; font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; padding: 2px 9px; border-radius: 999px; background: var(--accent); color: var(--text-invert); vertical-align: 2px; }
    .s8-note { font-size: 17px; color: var(--text-muted); }
    /* Diapositiva 9 */
    .s9n { display: flex; flex-direction: column; justify-content: center; gap: 30px; }
    .decision-line { font-size: 26px; font-weight: 700; padding: 14px 22px; border-radius: 12px; border: 2px solid var(--accent); background: var(--accent-soft); align-self: flex-start; }
    .next-list.n9 { gap: 24px; }
    .next-list.n9 li { font-size: 27px; }
    /* Animaciones: estado completo por defecto; «building» atenúa los pasos pendientes */
    .anim [data-step] { transition: opacity 550ms ease, transform 550ms ease, box-shadow 550ms ease; }
    .anim.building [data-step]:not(.on) { opacity: .1; }
    .anim.building .brow[data-step]:not(.on) { opacity: 1; }
    .anim.building .brow[data-step]:not(.on) .bfill { transform: scaleX(0); }
    .anim.building .brow[data-step]:not(.on) .bval { opacity: 0; }
    .anim.building .brow[data-step]:not(.on) .blabel { opacity: .25; }
    .anim .bval, .anim .blabel { transition: opacity 500ms ease; }
    .anim.building .split-col[data-step]:not(.on), .anim.building .station[data-step]:not(.on) { transform: translateY(8px); }
    .anim .now { box-shadow: 0 0 0 3px var(--accent); border-radius: 12px; }
    @media (prefers-reduced-motion: reduce) { .anim [data-step], .bfill, .anim .bval { transition: none !important; } }
"""

ANIM_JS = r"""
  <script>
    /* Animaciones opcionales A (3), B (6) y C (7): Play / Replay / Show all.
       Sin reproducción automática; salir o volver a la diapositiva cancela y
       restablece el estado completo. Con movimiento reducido se muestra el final. */
    (function () {
      var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var STEP_MS = 1150, FIRST_MS = 120;
      var anims = {};
      Array.from(document.querySelectorAll('.anim[data-anim-name]')).forEach(function (box) {
        var name = box.dataset.animName;
        var slide = box.closest('.slide-stage');
        var root = slide;  // los pasos pueden estar fuera del contenedor (tarjeta lateral)
        var steps = Array.from(root.querySelectorAll('[data-step]'));
        var maxStep = steps.reduce(function (m, el) { return Math.max(m, Number(el.dataset.step)); }, 0);
        var a = { box: box, slide: slide, steps: steps, max: maxStep, timers: [] };
        anims[name] = a;
        new MutationObserver(function () { reset(a); }).observe(slide, { attributes: true, attributeFilter: ['style'] });
      });
      function clear(a) { a.timers.forEach(clearTimeout); a.timers = []; }
      function setState(a, k) {
        a.steps.forEach(function (el) {
          var s = Number(el.dataset.step);
          el.classList.toggle('on', s <= k);
          el.classList.toggle('now', s === k && k < a.max && el.classList.contains('split-col'));
        });
      }
      function containerOf(a) { return a.slide.querySelector('.s6n') || a.box; }
      function reset(a) {
        clear(a);
        a.slide.querySelectorAll('.anim').forEach(function (b) { b.classList.remove('building'); });
        a.steps.forEach(function (el) { el.classList.remove('on', 'now'); });
        a.slide.dataset.animState = 'all';
      }
      function showAll(a) { clear(a); setState(a, a.max); a.slide.querySelectorAll('.anim').forEach(function (b) { b.classList.remove('building'); }); a.slide.dataset.animState = 'all'; }
      function play(a) {
        clear(a);
        if (reduce) { showAll(a); return; }
        var c = containerOf(a);
        c.classList.add('building'); a.box.classList.add('building');
        a.slide.dataset.animState = 'playing';
        setState(a, 0);
        for (var k = 1; k <= a.max; k++) {
          (function (k) {
            a.timers.push(setTimeout(function () {
              setState(a, k);
              if (k === a.max) { a.timers.push(setTimeout(function () { showAll(a); }, 700)); }
            }, FIRST_MS + (k - 1) * STEP_MS));
          })(k);
        }
      }
      document.querySelectorAll('[data-anim-act]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var a = anims[btn.dataset.anim]; if (!a) return;
          var act = btn.dataset.animAct;
          if (act === 'all') showAll(a);
          else if (act === 'replay') play(a);
          else if (a.slide.dataset.animState !== 'playing') play(a);
          btn.blur();
        });
      });
      window.__deckAnimations = anims;
    })();
  </script>"""


# ---------------------------------------------------------------------------
# Ensamblado
# ---------------------------------------------------------------------------

def assemble(base: str, cfg: dict, slide_html: list[str]) -> str:
    style_end = base.index("</style>")
    head = base[:style_end] + CSS + "  </style>\n</head>\n"
    head = re.sub(r"<title>.*?</title>", "<title>Engineering attrition: from the core HR model to HR + employee feedback (CQ)</title>", head, count=1)
    body_open = re.search(r"<body[^>]*>", base).group(0)
    nav_start = base.index('<div class="nav-ctrl" id="slide-nav">')
    first_script = base.index("<script>", nav_start)
    nav_block = base[nav_start:first_script]
    pills = "\n".join(
        f'      <button class="nav-pill{" pill-active" if i == 0 else ""}" data-slide="{i}">{escape(lbl)}</button>'
        for i, lbl in enumerate(cfg["nav_labels"]))
    nav_block = re.sub(r'(<div class="nav-label">Navigation</div>\n)(?:\s*<button class="nav-pill[^\n]*\n)+', lambda m: m.group(1) + pills + "\n", nav_block)
    scripts = re.findall(r"  <script>.*?</script>", base[first_script - 2:], flags=re.DOTALL)
    keep = [s for s in scripts if "slide-studio-theme" in s or ("#slide-nav [data-slide]" in s and "KeyboardEvent" in s)]
    if len(keep) != 2:
        raise ValueError("No se encontraron los bloques JS base esperados")
    return (head + body_open + "\n" + "\n".join(slide_html) + "\n\n  " + nav_block.rstrip() + "\n\n"
            + "\n".join(keep) + ANIM_JS + "\n</body>\n</html>\n")


def visible_text(html: str) -> str:
    t = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.DOTALL | re.IGNORECASE)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def jargon_hits(html: str) -> list[str]:
    text = visible_text(html).lower()
    return [w for w in JARGON if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", text)]


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_deck", VERIFY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def script_md(f: dict, cfg: dict) -> str:
    t = cfg["timings_seconds"]
    risk_groups = cfg["risk_groups"]["label_es"]
    acc, cum = 0, []
    for s in t:
        acc += s
        cum.append(f"{acc // 60}:{acc % 60:02d}")
    pa, pj = f["periods"]["aug_dec_2025"], f["periods"]["jan_feb_2026"]
    d = [r for r in f["rows"] if r["key"] == "D"][0]
    rsf = [r for r in f["rows"] if r["key"] == "RSF_Q"][0]
    dis = [r for r in f["rows"] if r["key"] == "disjoint"][0]
    S = [
        ("Decisión", "Presentar la elección y su alcance.",
         f"Primero ordenamos los grupos por riesgo estimado y los seleccionamos hasta reunir el 30% de las personas de Engineering. Después medimos las salidas voluntarias durante los 6 meses siguientes. En promedio, en ese conjunto ocurrió el {f['cq_cap']} de todas las salidas de la población evaluada. La primera tarjeta compara el error absoluto promedio por grupo y fecha: CQ lo reduce un {f['cq_red']} frente al modelo ampliado de RH (C). Con CQ, la diferencia media entre salidas estimadas y observadas equivale aproximadamente a {f['cq_gap']} salida por cada 100 personas. Esa reducción relativa se calcula antes de redondear. La segunda tarjeta muestra los {f['gain'].lstrip('+')} puntos adicionales de captura que aporta la retroalimentación de los empleados frente a C. Probamos alternativas antes de mantener CQ.",
         "No hay animación.", f"{f['cq_cap']} de las salidas en 30% de la plantilla.",
         "Es retrospectivo y promedio; no es la probabilidad de que una persona se vaya ni salidas evitadas. El piloto no ha empezado.",
         "Empecemos por el modelo de partida y los puntos que queríamos mejorar."),
        ("Agenda", "Orientar el recorrido B → C → CQ.",
         "Primero, el punto de partida y las primeras pruebas con la encuesta; luego lo que mejoró con C y con CQ; después las pruebas adicionales, y al final la decisión y los pasos siguientes.",
         "No hay animación.", "Hay dos conjuntos de periodos: 4 periodos (feb-2024 a ene-2026) para B–C y 2 periodos recientes para C–CQ–D.",
         "Las cifras sólo se comparan dentro de cada conjunto; no forman una serie.",
         "Veamos de dónde partimos."),
        ("Punto de partida y avances", "Recordar cómo B forma los grupos y rendir cuentas de los compromisos.",
         f"B divide Engineering por años en Qualcomm, salidas en el equipo y nivel. El {f['snapshot']} quedaron {f['groups']} grupos elegibles, cada uno con al menos 300 personas. Hay {f['combos']} cruces posibles; los que no alcanzan ese tamaño se agrupan aparte. Entre los grupos elegibles se seleccionan los {risk_groups} hasta cubrir el 30% de Engineering. A la derecha están los puntos que nos propusimos mejorar. CQ aportó una mejora modesta: ganó en un periodo y empató en el otro; el slide 6 muestra esa comparación. La regla estricta original de ganar en ambos periodos se conserva como antecedente en S01. Sobre la sobreestimación: el promedio de los {risk_groups} mejoró, pero esa comparación no sigue al grupo concreto de mayor riesgo mostrado antes.",
         "Pulsar Play al explicar la división (≈5 s): todo Engineering → años → salidas del equipo → nivel.",
         f"{f['groups']} grupos, cada uno con 300 personas o más.",
         "Fairness no se encontró en los estudios revisados: queda abierto.",
         "La primera pregunta fue qué podíamos aprender de lo que los empleados dijeron en QVoice."),
        ("Primeras pruebas con encuesta", "Explicar por qué QVoice era útil pero las primeras variantes no se adoptaron.",
         f"Evaluamos {f['variants']} variantes de la encuesta sobre los mismos dos periodos; todas ordenaron mejor el riesgo que B, pero ninguna superó todas las comprobaciones acordadas. Q4 fue la más sencilla y prometedora ({f['q4'][0]} de {f['q4'][1]}). Las combinaciones más amplias aportaron información más allá de si la persona respondió, pero el balance de la estimación global seguía limitando. El ajuste a seis meses sólo pudo probarse en ene–feb 2026 (ago–dic 2025 no tenía historia suficiente) y no mejoró el balance.",
         "No hay animación.", f"{f['variants']} de {f['variants']} ordenaron mejor; ninguna pasó todo.",
         "No invalida QVoice ni la calibración en general.",
         "También ampliamos la información de RH y comprobamos si C mejoraba el balance con las mismas definiciones de grupo."),
        ("B frente a C", "Mostrar que C acercó las estimaciones con los mismos grupos.",
         f"Con las mismas definiciones de grupo, C reduce el gap promedio por grupo de {f['b_gap']} a {f['cb_gap']} salidas por cada 100 personas: {f['bc_red']} menos en términos relativos. La proporción de salidas pasa de {f['b_cap']} a {f['cb_cap']}, una diferencia pequeña e incierta (+{fmt(f['bc_diff'], 2)} puntos, IC95 {fmt(f['bc_ci'][0], 2)} a {fmt(f['bc_ci'][1], 2)}; C gana {f['bc_wins'][0]} de 4 periodos). La preferencia por C fue práctica (S09). Si preguntan por el escenario de 40%: {f['b40']} frente a {f['c40']}.",
         "No hay animación.", f"Gap {f['bc_red']} menor con las mismas definiciones.",
         "C no ganó todas las medidas en todas las fechas.",
         "Con esa base, volvimos a comprobar qué añadía QVoice."),
        ("C frente a CQ", "Mostrar el aporte modesto de la retroalimentación.",
         f"En las comprobaciones históricas, {f['cq_cap']} de las salidas observadas vinieron de {risk_groups} que suman 30% de Engineering. Al azar serían cerca de {f['random']}; añadir la retroalimentación al modelo ampliado agregó unos {f['gain'].lstrip('+')} puntos. La línea aleatoria muestra el valor del modelo completo; la diferencia con C muestra el aporte de la encuesta. Mejora en un periodo ({pa['c']} → {pa['cq']}) y empata en el otro ({pj['c']}): es una mejora modesta. El gap promedio por grupo es {f['cq_red']} menor.",
         "Pulsar Play al llegar al gráfico (≈5 s): línea aleatoria → C → CQ (+0.7) → tarjeta y periodos. Show all si se necesita ir directo.",
         f"{f['c_cap']} → {f['cq_cap']}; {f['gain']} puntos.",
         f"Respaldo si preguntan: en los {risk_groups}, estimado {f['pred']['C']} vs {f['pred']['CQ']} y observado {f['obs']['C']} vs {f['obs']['CQ']} por cada 100 personas (el observado cambia porque cada modelo puede identificar distintos grupos como de riesgo alto); sobreestimación media {f['over']['C']} → {f['over']['CQ']} puntos (unos {f['over_red']}% menor, CQ frente a C, {risk_groups} que cubren el 30%). Mayor gap publicable: ago–dic {pa['worst_c']} → {pa['worst_cq']}, ene–feb {pj['worst_c']} → {pj['worst_cq']}; el indicador no sigue siempre al mismo grupo. IC95 de la diferencia de captura: {f['cq_ci'][0]} a {f['cq_ci'][1]} puntos, condicionado a los modelos ajustados, los grupos seleccionados por riesgo y los periodos observados.",
         f"La encuesta refina las estimaciones para identificar los {risk_groups}, que siguen siendo fáciles de describir."),
        ("Cómo funciona CQ", "Explicar CQ sin tecnicismos y aclarar privacidad.",
         f"La información de RH y la retroalimentación de los empleados forman la estimación; con ella se ordenan los mismos grupos conocidos y se identifican los {risk_groups} hasta cubrir el 30% de Engineering. Durante el análisis autorizado se procesan respuestas individuales en memoria; no se guardan filas de empleados; los resultados compartidos son agregados por grupo y no se publican puntuaciones individuales. Cada encuesta se usa al año siguiente y las preguntas elegidas variaron entre periodos.",
         f"Pulsar Play (≈3 s): RH → retroalimentación → {risk_groups}.", "Sólo resultados por grupo.",
         "La versión final de septiembre aún necesita una comprobación con datos posteriores.",
         "Antes de cerrar la elección, comprobamos otras combinaciones y modelos."),
        ("Pruebas adicionales", "Mostrar que las alternativas no justificaron reemplazar CQ.",
         f"Las filas resumen grupos de pruebas, no un inventario exhaustivo. Fijar las preguntas con un promedio revisado mantiene {dis['cap_s']} pero aleja las estimaciones ({dis['gap_s']}). D acerca un poco las estimaciones ({d['gap_s']}), pero encuentra menos salidas en ene–feb 2026 ({d['jan_s']}) y no alcanza su propio umbral de 10%; su diferencia media de captura es {f['d_ci'][0]} puntos (IC95 {f['d_ci'][1]} a {f['d_ci'][2]}). El método alternativo con retroalimentación tiene una proporción similar ({rsf['cap_s']}) con {rsf['gap_s']} de gap. Su sobreestimación media es la más cercana a cero porque compensa periodos de signo contrario ({pa['rsf_over']} y {pj['rsf_over']}); por eso la selección usa el error por grupo. Variantes de respaldo: promedio 33 y sin promedio tienen más error; el modelo mensual simple da prácticamente lo mismo que D; C actualizado captura {f['c_updated']} con más error.",
         "No hay animación.", "Ninguna alternativa ofreció un balance mejor y estable.",
         "Las pruebas negativas también son un resultado del trabajo.",
         "Con estas comprobaciones, la decisión se mantiene; el siguiente paso es contrastarla con datos nuevos."),
        ("Siguientes pasos", "Cerrar con la elección y los pasos propuestos.",
         "CQ sigue siendo el modelo seleccionado. Proponemos comprobarlo en un periodo nuevo, revisar diferencias entre grupos, confirmar con RH cómo puede usarse la encuesta y preparar un piloto limitado. Son pasos propuestos, aún sin calendario ni aprobación.",
         "No hay animación.", "CQ seleccionado; ganancia modesta.",
         "El efecto de las acciones de retención no se ha medido. Fairness y el acuerdo de uso de QVoice siguen sin confirmar.",
         "Cerrar hacia el minuto 18 y abrir preguntas sobre esta diapositiva."),
    ]
    lines = ["# Guion del presentador · Evolución de B a CQ (Engineering)", "",
             f"Deck en inglés (excepción de idioma registrada en `{CONFIG.relative_to(ROOT).as_posix()}`); guion en español. Duración objetivo: 18 minutos.", "",
             "## Término usado en la presentación", "",
             f"**{cfg['risk_groups']['label_en'].capitalize()} = {risk_groups}.** {cfg['risk_groups']['definition_es']}", ""]
    for i, (name, goal, talk, play, num, limit, trans) in enumerate(S):
        lines += [f"## {i + 1}. {name} · {t[i] // 60}:{t[i] % 60:02d} (acumulado {cum[i]})", "",
                  f"- **Objetivo:** {goal}", f"- **Explicación:** {talk}", f"- **Animación:** {play}",
                  f"- **Cifra para recordar:** {num}", f"- **Limitación:** {limit}", f"- **Transición:** «{trans}»", ""]
    qa = [
        (f"¿Quiénes son los {risk_groups}?", cfg["risk_groups"]["definition_es"]),
        ("¿Por qué no B?", f"C mantiene las definiciones de grupo y reduce {f['bc_red']} el gap por grupo; el cambio en la proporción de salidas fue pequeño e incierto."),
        ("¿Por qué CQ si no ganó los dos periodos?", f"Ganó uno y empató el otro, con {f['gain']} puntos de media y {f['cq_red']} menos de gap. La regla estricta original se conserva como antecedente; la elección ponderó magnitud, error y utilidad (S01)."),
        ("¿Cuánto aporta la encuesta y cuánto el modelo?", f"Al azar, alrededor de {f['random']}; C, {f['c_cap']}; CQ, {f['cq_cap']}. La encuesta aporta los últimos {f['gain'].lstrip('+')} puntos."),
        (f"¿{f['cq_cap']} significa que esas personas se irán?", "No. El denominador es el total de salidas voluntarias de la población evaluada durante los 6 meses siguientes. El numerador son las salidas ocurridas en los grupos seleccionados por riesgo estimado, que reúnen el 30% de las personas. Es un promedio histórico."),
        ("¿Se resolvió la sobreestimación?", f"En los {risk_groups}, la sobreestimación media de CQ es unos {f['over_red']}% menor que la de C. El grupo con mayor error mejora en un periodo y empeora en el otro, y algunos grupos siguen necesitando trabajo. Esta comparación no sigue al grupo concreto de mayor riesgo mostrado antes."),
        ("¿Por qué no usar la sobreestimación media para elegir?", f"Errores de signo contrario se compensan. El método alternativo tiene la media más cercana a cero, pero {rsf['gap_s'].replace('larger', 'más')} de error por grupo."),
        ("¿Y fairness?", "No se encontró una evaluación archivada en los estudios revisados; es el paso 2."),
        ("¿Se usan las respuestas individuales de QVoice?", "En el análisis autorizado se procesan en memoria; no se guardan filas de empleados; sólo se reportan resultados por grupo y no se publican puntuaciones individuales."),
        ("¿D fue peor en todo?", f"No. Acercó un poco las estimaciones ({d['gap_s'].replace(' smaller', '')}), pero no alcanzó su propio umbral de 10% y perdió captura en el periodo reciente."),
        ("¿QVoice causa las salidas?", "No. Son asociaciones predictivas."),
        ("¿Está probado el modelo final de septiembre?", "No. Sus coeficientes requieren datos posteriores a su ajuste."),
        ("¿Por qué 30%?", "Es el escenario de comparación; la capacidad real se define para el piloto."),
        (f"¿Por qué C tiene {f['cb_cap']} en la diapositiva 5 y {f['c_cap']} en la 6?", "Son conjuntos de periodos distintos; no es un deterioro."),
    ]
    lines += ["## Preguntas preparadas", ""] + [f"- **{q}** {a}" for q, a in qa] + [""]
    return "\n".join(lines)


def qualitative_claims() -> list[dict]:
    return [
        {"claim": "Se conservan las definiciones de grupo (años, salidas del equipo, nivel)", "source": "S08", "scope": "B_cuts y C_Bcuts usan los mismos cortes"},
        {"claim": "Fairness no se encontró en los estudios revisados", "source": "plan alterno H1/O08", "scope": "Estudios S01–S14 revisados hasta 2026-10-10"},
        {"claim": "Las señales de historia del equipo de D no quedaron en su versión final", "source": "S12", "scope": "final_selected.features sin señales de historia del equipo"},
        {"claim": "La versión final de septiembre requiere evaluación con datos posteriores", "source": "S01/S10", "scope": "Modelos históricos usaron el modelo disponible en cada fecha"},
        {"claim": "Procesamiento en memoria; sin filas de empleados persistidas; sin scores individuales publicados", "source": "S11, S12, S14", "scope": "employee_level_rows_persisted=false, individual_scores_published=false"},
        {"claim": "El piloto no ha empezado", "source": "S01", "scope": "Alcance de la decisión"},
        {"claim": "Compromisos del deck anterior", "source": "S02", "scope": "Diapositiva 9 de la base"},
        {"claim": "time_at_level_band forma parte de C", "source": "S13", "scope": "Términos de C"},
    ]


def build(out: Path) -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    base_reg = json.loads((ROOT / cfg["base_registry"]).read_text(encoding="utf-8"))
    base_path = ROOT / base_reg["source_html"]
    if sha256(base_path) != base_reg["source_sha256"]:
        raise SystemExit("El hash de la base no coincide con el registro; detenido.")
    if out.exists():
        raise SystemExit(f"La salida ya existe: {out}")
    ev = Evidence(cfg)
    f = compute(ev)
    final_feats = ev.field("S12", "final_selected.features")
    if any("team" in x or "hist" in x for x in final_feats):
        raise ValueError("D final incluye señales de historia del equipo; revisar la nota de la diapositiva 8")
    html = assemble(base_path.read_text(encoding="utf-8"), cfg, slides(f, cfg))
    hits = jargon_hits(html)
    if hits:
        raise ValueError(f"Jerga visible: {hits}")
    out.mkdir(parents=True)
    deck = out / "presentacion-eng.html"
    deck.write_text(html, encoding="utf-8")
    (out / "guion-presentador.md").write_text(script_md(f, cfg), encoding="utf-8")
    evidence = {
        "deck": cfg["deck"], "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "language": cfg["language"], "deliverable_classification": cfg["deliverable_classification"],
        "cq_version": cfg["cq_version"], "timings_seconds": cfg["timings_seconds"],
        "risk_groups": cfg["risk_groups"],
        "base": {"path": base_reg["source_html"], "sha256": base_reg["source_sha256"]},
        "sources": {sid: {"path": p, "sha256": sha256(ROOT / p)} for sid, p in cfg["sources"].items()},
        "population": "Engineering; Employee, Regular, activos, sin RF360; salida voluntaria a 6 meses",
        "figures": ev.records, "qualitative_claims": qualitative_claims(),
        "pending_confirmations": cfg["pending_confirmations"],
    }
    (out / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    errors, warnings = load_verifier().check(html, "presentation")
    lang_error = 'El elemento <html> debe declarar lang="es".'
    other = [e for e in errors if e != lang_error]
    validation = {
        "verifier": {"command": f"verify_deck.py {deck.relative_to(ROOT).as_posix()} --mode presentation",
                     "errors": errors, "warnings": warnings,
                     "result": "verificador original con excepción documentada de idioma" if not other else "con errores"},
        "language_exception": cfg["language_exception"],
        "jargon_visible": hits,
        "privacy": {"aggregates_only": True, "employee_rows": False, "individual_scores": False,
                    "min_group_people": f["min_people"], "protected_labels": False},
        "browser_review": {"status": "pendiente"},
    }
    (out / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
    if other:
        raise SystemExit(f"Errores del verificador: {other}")
    return validation


def record_browser_review(out: Path) -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    review = ROOT / cfg["preview_root"] / out.name / "browser-review.json"
    data = json.loads(review.read_text(encoding="utf-8"))
    vpath = out / "validation.json"
    validation = json.loads(vpath.read_text(encoding="utf-8"))
    validation["browser_review"] = {"file": review.relative_to(ROOT).as_posix(), **data}
    vpath.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", type=Path)
    p.add_argument("--record-browser-review", type=Path)
    a = p.parse_args()
    if a.record_browser_review:
        record_browser_review(a.record_browser_review)
        return 0
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    out = a.out or ROOT / cfg["output_root"] / f"{datetime.now():%Y%m%d-%H%M}_{cfg['output_suffix']}"
    v = build(out.resolve())
    print(out)
    print(json.dumps(v["verifier"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
