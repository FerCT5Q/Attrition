"""Replace only HTML stage slide-20 with the QVoice request/concern visual.

The script consumes the aggregate-only QVoice evidence artifact and atomically
updates the current deck plus its manifest. It never reads or renders raw
comments or employee identifiers.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"
MANIFEST = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7-manifest.json"
EVIDENCE = ROOT / "output" / "distribution" / "json" / "qvoice-open-text-request-concern-evidence-20260922.json"
TARGET_STAGE = 20
GROUP_REQUEST_CONCERN = "requested_remote_hybrid_or_raised_onsite_policy_concern"
GROUP_ALL_OTHER = "all_other_open_text_commenters"
GROUP_NO_COMMENT = "no_open_text_comment"
EXPECTED_WAVES = ("Mar-2023", "Jan-2024", "Jan-2025", "Jan-2026")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_fragment(deck: str, stage_id: int) -> str:
    pattern = rf'(<div class="slide-stage" id="slide-{stage_id}".*?)(?=\n\s*<div class="slide-stage"|\n\s*<script|\Z)'
    match = re.search(pattern, deck, flags=re.S)
    require(match is not None, f"No se encontró el stage slide-{stage_id}.")
    return match.group(1)


def stage_map(deck: str) -> dict[int, str]:
    ids = [int(value) for value in re.findall(r'<div class="slide-stage" id="slide-(\d+)"', deck)]
    require(len(ids) == len(set(ids)), "El deck contiene stage IDs duplicados.")
    return {stage_id: stage_fragment(deck, stage_id) for stage_id in ids}


def load_evidence() -> dict[str, Any]:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    require(evidence.get("artifact") == "internal_analysis", "La evidencia QVoice debe ser internal_analysis.")
    require(evidence.get("outcome") == "pass", "La evidencia QVoice no pasó.")
    require(evidence.get("minimum_shared_cohort") == 30, "La evidencia QVoice debe conservar n>=30.")
    validation = evidence.get("validation", {})
    require(validation.get("outcome") == "pass", "Falta validación QVoice aprobada.")
    require(validation.get("jan_2026_cutoff") == "2026-08-23", "El corte YTD QVoice debe ser agosto de 2026.")
    require(validation.get("jan_2026_ytd_is_partial_and_not_annualized") is True, "2026 debe continuar como YTD parcial.")
    require(validation.get("all_visible_group_and_subtheme_cohorts_n_at_least") == 30, "Las cohortes visibles no cumplen n>=30.")
    encoded = json.dumps(evidence, ensure_ascii=False).casefold()
    for prohibited in ('"employee_id"', '"emp_id"', '"raw_comment"', '"comment_text"'):
        require(prohibited not in encoded, f"La evidencia persiste un campo prohibido: {prohibited}.")

    waves = evidence.get("waves")
    require(isinstance(waves, list) and tuple(str(row.get("wave")) for row in waves) == EXPECTED_WAVES, "Las waves QVoice no coinciden.")
    for row in waves:
        commenter_count = int(row["open_text_commenter_count"])
        groups = row.get("groups")
        require(isinstance(groups, list) and {group["group"] for group in groups} == {GROUP_REQUEST_CONCERN, GROUP_ALL_OTHER}, "Los dos grupos QVoice son obligatorios.")
        no_comment = row.get("no_comment")
        require(isinstance(no_comment, dict) and no_comment.get("group") == GROUP_NO_COMMENT, "Falta el grupo QVoice sin comentario.")
        require(sum(int(group["commenter_count"]) for group in groups) == commenter_count, "Los grupos no reconcilian a los comentaristas.")
        share_sum = sum(float(group["share_of_open_text_commenters_percent"]) for group in groups)
        require(abs(share_sum - 100.0) < 0.001, "Los porcentajes QVoice no reconcilian a 100%.")
        for group in groups:
            source_count = int(group["source_commenter_count"])
            matched = int(group["matched_employee_count"])
            exits = int(group["voluntary_exit_count"])
            rate = float(group["voluntary_attrition_rate_percent"])
            require(source_count == int(group["commenter_count"]), "El join QVoice no reconcilia a la fuente.")
            require(matched >= 30 and 0 <= exits <= matched, "Una cohorte de attrition no es publicable.")
            require(abs(rate - (100.0 * exits / matched)) < 0.00011, "Una tasa de attrition no reconcilia.")
        no_comment_count = int(no_comment["participant_count"])
        no_comment_matched = int(no_comment["matched_employee_count"])
        no_comment_exits = int(no_comment["voluntary_exit_count"])
        no_comment_rate = float(no_comment["voluntary_attrition_rate_percent"])
        require(no_comment_count >= 30, "La cohorte sin comentario no cumple n>=30.")
        require(int(no_comment["source_participant_count"]) == no_comment_count, "La cohorte sin comentario no reconcilia a la fuente.")
        require(no_comment_matched >= 30 and 0 <= no_comment_exits <= no_comment_matched, "La cohorte sin comentario no es publicable.")
        require(abs(no_comment_rate - (100.0 * no_comment_exits / no_comment_matched)) < 0.00011, "La tasa de attrition sin comentario no reconcilia.")
        composition = row.get("composition")
        require(isinstance(composition, dict), "Falta la composici\u00f3n de tres grupos QVoice.")
        composition_groups = composition.get("groups")
        require(
            isinstance(composition_groups, list)
            and {str(group.get("group")) for group in composition_groups}
            == {GROUP_REQUEST_CONCERN, GROUP_ALL_OTHER, GROUP_NO_COMMENT},
            "La composici\u00f3n QVoice debe tener exactamente tres grupos.",
        )
        participant_count = int(row["survey_participant_count"])
        require(int(composition.get("groups_are_mutually_exclusive_and_exhaustive")) == 1, "Los grupos QVoice deben ser excluyentes y exhaustivos.")
        require(sum(int(group["participant_count"]) for group in composition_groups) == participant_count, "La composici\u00f3n QVoice no reconcilia a participantes.")
        require(abs(sum(float(group["share_of_survey_participants_percent"]) for group in composition_groups) - 100.0) < 0.001, "La composici\u00f3n QVoice no suma 100%.")
        require(all(int(group["participant_count"]) >= 30 for group in composition_groups), "Una cohorte visible de composici\u00f3n no es publicable.")
        window = row.get("attrition_window", {})
        if row["wave"] == "Jan-2026":
            require(window.get("outcome_type") == "ytd_partial" and window.get("outcome_end") == "2026-08-23", "La ventana 2026 es incorrecta.")
        else:
            require(window.get("outcome_type") == "annual_12m", "Las waves históricas deben usar 12 meses.")

    subthemes = evidence.get("latest_survey_subthemes")
    require(isinstance(subthemes, list) and 3 <= len(subthemes) <= 5, "El resumen de subtemas debe tener de tres a cinco barras.")
    for row in subthemes:
        require(int(row["commenter_count"]) >= 30, "Un subtema visible no cumple n>=30.")
    return evidence


def display_wave(wave: str) -> str:
    labels = {
        "Mar-2023": "Mar 2023",
        "Jan-2024": "Jan 2024",
        "Jan-2025": "Jan 2025",
        "Jan-2026": "2025 QVoice (fielded Jan 2026)",
    }
    return labels[wave]


def group_by_name(wave: dict[str, Any], name: str) -> dict[str, Any]:
    result = next((row for row in wave["groups"] if row["group"] == name), None)
    require(isinstance(result, dict), f"Falta grupo {name}.")
    return result


def pct(value: float) -> str:
    return f"{value:.1f}%"


def attrition_pill_class(rate: float, rates: list[float]) -> str:
    if len(set(rates)) <= 1:
        return "attr-mid"
    if rate == min(rates):
        return "attr-low"
    if rate == max(rates):
        return "attr-high"
    return "attr-mid"


def render_qvoice18_attrition_pill(label: str, rate: float, rates: list[float]) -> str:
    klass = attrition_pill_class(rate, rates)
    tooltip = f"Voluntary attrition for {label}: {rate:.1f}%"
    return (
        '<span class="qvoice18-attrition-pill v6-rate-pill '
        + klass
        + '" title="'
        + html.escape(tooltip, quote=True)
        + '" aria-label="'
        + html.escape(tooltip, quote=True)
        + '">'
        + f"{rate:.1f}%"
        + "</span>"
    )


def render_coverage_rail(wave: dict[str, Any]) -> str:
    focus = group_by_name(wave, GROUP_REQUEST_CONCERN)
    other = group_by_name(wave, GROUP_ALL_OTHER)
    focus_pct = float(focus["share_of_open_text_commenters_percent"])
    other_pct = float(other["share_of_open_text_commenters_percent"])
    commenter_count = int(wave["open_text_commenter_count"])
    return f'''<div class="qvoice18-rail-card">
      <div class="qvoice18-rail-head"><strong>{html.escape(display_wave(str(wave["wave"])))}</strong><span>n={commenter_count:,} people</span></div>
      <div class="qvoice18-coverage-track" role="img" aria-label="{pct(focus_pct)} remote/hybrid or onsite attendance comments and {pct(other_pct)} other comments">
        <div class="qvoice18-coverage-focus" style="width:{focus_pct:.4f}%"></div>
      </div>
      <div class="qvoice18-rail-labels"><span><b>{pct(focus_pct)}</b> remote/hybrid or onsite attendance</span><span>{pct(other_pct)} other comments</span></div>
    </div>'''


def render_attrition_groups(wave: dict[str, Any], all_rates: list[float]) -> str:
    request = group_by_name(wave, GROUP_REQUEST_CONCERN)
    other = group_by_name(wave, GROUP_ALL_OTHER)
    no_comment = wave["no_comment"]
    rows: list[str] = []
    for group, label, klass in (
        (request, "Remote/hybrid or onsite attendance", "is-focus"),
        (other, "Other comments", "is-other"),
    ):
        share = float(group["share_of_open_text_commenters_percent"])
        attrition = float(group["voluntary_attrition_rate_percent"])
        rows.append(f'''<div class="qvoice18-group-row {klass}">
          <div class="qvoice18-group-label">{label}</div>
          <div class="qvoice18-group-bar" aria-hidden="true"><div style="width:{max(share, 1.5):.4f}%"></div></div>
          <div class="qvoice18-group-stats"><strong>{pct(share)} · n={int(group["commenter_count"]):,}</strong>{render_qvoice18_attrition_pill(label, attrition, all_rates)}</div>
        </div>''')
    no_comment_rate = float(no_comment["voluntary_attrition_rate_percent"])
    rows.append(f'''<div class="qvoice18-group-row qvoice18-no-comment-row">
          <div class="qvoice18-group-label">No written comment</div>
          <div aria-hidden="true"></div>
          <div class="qvoice18-group-stats">{render_qvoice18_attrition_pill("No written comment", no_comment_rate, all_rates)}</div>
        </div>''')
    window_label = html.escape(str(wave["attrition_window"]["label"]))
    return f'''<div class="qvoice18-wave-block">
      <div class="qvoice18-wave-head"><strong>{html.escape(display_wave(str(wave["wave"])))}</strong><span>{window_label}</span></div>
      {''.join(rows)}
    </div>'''


def build_legacy_stage(evidence: dict[str, Any]) -> str:
    waves = list(evidence["waves"])
    maximum_request_share = max(
        float(group_by_name(wave, GROUP_REQUEST_CONCERN)["share_of_open_text_commenters_percent"])
        for wave in waves
    )
    title = (
        "Most comments were not about remote/hybrid work or onsite attendance"
        if maximum_request_share < 50
        else "QVoice: remote/hybrid work and onsite attendance comments"
    )
    rails = "".join(render_coverage_rail(wave) for wave in waves)
    all_rates = [
        float(group["voluntary_attrition_rate_percent"])
        for wave in waves
        for group in wave["groups"]
    ] + [float(wave["no_comment"]["voluntary_attrition_rate_percent"]) for wave in waves]
    attrition_blocks = "".join(render_attrition_groups(wave, all_rates) for wave in waves)
    display_topic_labels = {
        "Request for remote or hybrid flexibility": "Remote/hybrid flexibility",
        "Policy enforcement, compliance, or exceptions": "Onsite policy / enforcement / exceptions",
        "Required days in the office": "Required onsite days",
        "Commute, parking, or travel time": "Commute / parking / travel",
        "Office space or facilities": "Onsite space / facilities",
    }
    topic_rows = "".join(
        f'''<div class="qvoice18-topic-row">
          <div class="qvoice18-topic-label">{html.escape(display_topic_labels.get(str(topic["label"]), str(topic["label"])))}</div>
          <div class="qvoice18-topic-bar" aria-hidden="true"><div style="width:{max(float(topic["share_of_request_or_concern_group_percent"]), 1.5):.4f}%"></div></div>
          <div class="qvoice18-topic-stats"><strong>{pct(float(topic["share_of_request_or_concern_group_percent"]))}</strong><span>n={int(topic["commenter_count"]):,}</span></div>
        </div>'''
        for topic in evidence["latest_survey_subthemes"]
    )
    return f'''<div class="slide-stage" id="slide-20" data-qvoice-open-text-request-concern="20260918" data-v7-qvoice-open-text-attrition-pills="true" data-v7-qvoice-open-text-no-comment-attrition="true">
  <style>
    #slide-20 {{ grid-template-rows:auto 1fr; gap:8px; }}
    #slide-20 .slide-title-text {{ font-size:21px; max-width:1080px; }}
    .qvoice18-shell {{ display:grid; grid-template-rows:auto 1fr auto; gap:10px; min-height:0; }}
    .qvoice18-coverage {{ padding:11px 14px 10px; border:1px solid var(--border-subtle); border-radius:13px; background:color-mix(in oklab, var(--bg-surface) 90%, transparent); }}
    .qvoice18-section-title {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; margin-bottom:8px; }}
    .qvoice18-section-title strong {{ font-size:13px; color:var(--text-main); }}
    .qvoice18-section-title span {{ color:var(--text-muted); font-size:11px; }}
    .qvoice18-rails {{ display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:10px; }}
    .qvoice18-rail-card {{ min-width:0; }}
    .qvoice18-rail-head {{ display:flex; justify-content:space-between; gap:6px; font-size:11px; margin-bottom:5px; }}
    .qvoice18-rail-head strong {{ color:var(--text-main); }}
    .qvoice18-rail-head span {{ color:var(--text-muted); white-space:nowrap; }}
    .qvoice18-coverage-track {{ height:12px; border-radius:999px; overflow:hidden; background:color-mix(in oklab, var(--text-muted) 20%, var(--bg-surface-2)); border:1px solid var(--border-subtle); }}
    .qvoice18-coverage-focus {{ height:100%; min-width:2px; background:var(--accent); border-radius:999px 0 0 999px; }}
    .qvoice18-rail-labels {{ display:flex; justify-content:space-between; gap:6px; font-size:9.5px; color:var(--text-muted); margin-top:4px; line-height:1.2; }}
    .qvoice18-rail-labels b {{ color:var(--accent); }}
    .qvoice18-main {{ display:grid; grid-template-columns:1.64fr 1fr; gap:12px; min-height:0; }}
    .qvoice18-panel {{ border:1px solid var(--border-subtle); border-radius:14px; background:color-mix(in oklab, var(--bg-surface) 92%, transparent); padding:12px 14px; min-height:0; overflow:hidden; }}
    .qvoice18-panel-head {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; border-bottom:2px solid var(--accent); padding-bottom:6px; margin-bottom:7px; }}
    .qvoice18-panel-head strong {{ font-size:13px; color:var(--text-main); }}
    .qvoice18-panel-head span {{ font-size:10px; line-height:1.25; color:var(--text-muted); text-align:right; }}
    .qvoice18-attrition-list {{ display:grid; gap:5px; }}
    .qvoice18-wave-block {{ padding-top:1px; }}
    .qvoice18-wave-head {{ display:flex; align-items:baseline; justify-content:space-between; gap:8px; margin:1px 0 3px; }}
    .qvoice18-wave-head strong {{ font-size:11px; color:var(--text-main); }}
    .qvoice18-wave-head span {{ font-size:9.5px; color:var(--text-muted); white-space:nowrap; }}
    .qvoice18-group-row {{ display:grid; grid-template-columns:222px minmax(78px, 1fr) 158px; gap:8px; align-items:center; min-height:20px; }}
    .qvoice18-group-label {{ font-size:10px; line-height:1.15; color:var(--text-main); }}
    .qvoice18-group-bar {{ height:10px; overflow:hidden; border-radius:999px; background:color-mix(in oklab, var(--text-muted) 18%, var(--bg-surface-2)); border:1px solid var(--border-subtle); }}
    .qvoice18-group-bar > div {{ height:100%; border-radius:999px; }}
    .qvoice18-group-row.is-focus .qvoice18-group-bar > div {{ background:var(--accent); }}
    .qvoice18-group-row.is-other .qvoice18-group-bar > div {{ background:color-mix(in oklab, var(--text-muted) 75%, var(--bg-surface)); }}
    .qvoice18-group-stats {{ display:flex; justify-content:space-between; align-items:baseline; gap:5px; white-space:nowrap; font-size:9.5px; font-variant-numeric:tabular-nums; }}
    #slide-20 .qvoice18-group-stats {{ width:158px; min-width:0; justify-self:stretch; }}
    .qvoice18-group-stats strong {{ color:var(--text-main); font-size:9.5px; }}
    .qvoice18-group-stats span {{ color:var(--text-muted); }}
    #slide-20 .qvoice18-no-comment-row {{ grid-template-columns:222px minmax(78px,1fr) 158px !important; width:100% !important; margin-top:2px; padding-top:3px; border-top:1px dashed var(--border-subtle); }}
    #slide-20 .qvoice18-no-comment-row .qvoice18-group-label {{ color:var(--text-main); font-family:inherit; font-size:10px; font-style:normal; font-weight:500; line-height:1.15; }}
    #slide-20 .qvoice18-no-comment-row .qvoice18-group-stats {{ grid-column:3; justify-self:stretch; min-width:0; justify-content:flex-end; }}
    .qvoice18-topic-intro {{ color:var(--text-muted); font-size:10px; line-height:1.25; margin:-1px 0 8px; }}
    .qvoice18-topic-list {{ display:grid; gap:11px; padding-top:2px; }}
    .qvoice18-topic-label {{ font-size:11px; line-height:1.2; color:var(--text-main); margin-bottom:4px; }}
    .qvoice18-topic-row {{ display:grid; grid-template-columns:minmax(0, 1fr) 72px; column-gap:8px; align-items:end; }}
    .qvoice18-topic-bar {{ grid-column:1; height:11px; border-radius:999px; overflow:hidden; background:color-mix(in oklab, var(--text-muted) 18%, var(--bg-surface-2)); border:1px solid var(--border-subtle); }}
    .qvoice18-topic-bar > div {{ height:100%; border-radius:999px; background:var(--accent-2); }}
    .qvoice18-topic-stats {{ grid-column:2; grid-row:1 / span 2; display:flex; flex-direction:column; align-items:flex-end; gap:1px; font-variant-numeric:tabular-nums; }}
    .qvoice18-topic-stats strong {{ font-size:13px; color:var(--text-main); }}
    .qvoice18-topic-stats span {{ font-size:10px; color:var(--text-muted); }}
    .qvoice18-source {{ border-top:1px solid var(--border-subtle); padding-top:7px; color:var(--text-muted); font-size:9.5px; line-height:1.28; }}
    .qvoice18-source strong {{ color:var(--text-main); }}
  </style>
  <div class="slide-heading"><div><h2 class="slide-title-text">{html.escape(title)}</h2><p class="slide-subtitle">Remote/hybrid or onsite-attendance comments vs. other comments</p></div><span class="badge badge-neutral">Open comments</span></div>
  <article class="card card-full qvoice18-shell">
    <section class="qvoice18-coverage" aria-label="Share of open-text commenters by survey">
      <div class="qvoice18-section-title"><strong>Share of people who submitted a comment</strong><span>Blue = remote/hybrid or onsite attendance</span></div>
      <div class="qvoice18-rails">{rails}</div>
    </section>
    <div class="qvoice18-main">
      <section class="qvoice18-panel" aria-label="Group size and voluntary attrition after each survey">
        <div class="qvoice18-panel-head"><strong>Voluntary attrition after each survey</strong><span>2023–2025: 12 months after survey<br>2026: YTD through Aug 2026 · partial year</span></div>
        <div class="qvoice18-attrition-list">{attrition_blocks}</div>
      </section>
      <section class="qvoice18-panel" aria-label="Most common topics in the most recent survey">
        <div class="qvoice18-panel-head"><strong>Most common topics</strong><span>2025 QVoice survey<br>(fielded Jan 2026)</span></div>
        <p class="qvoice18-topic-intro">Among remote/hybrid or onsite-attendance comments. People may mention more than one topic.</p>
        <div class="qvoice18-topic-list">{topic_rows}</div>
      </section>
    </div>
    <div class="qvoice18-source"><strong>How to read this:</strong> all available open-text prompts are included; 2025 and 2026 had a third prompt, creating another opportunity to mention the topic. Attrition is voluntary exits divided by the matched active-regular group before each survey. The comparison is descriptive only; it does not show that comments caused attrition.</div>
  </article>
</div>'''


def composition_by_name(wave: dict[str, Any], name: str) -> dict[str, Any]:
    composition = wave["composition"]
    result = next((row for row in composition["groups"] if row["group"] == name), None)
    require(isinstance(result, dict), f"Falta grupo de composici\u00f3n {name}.")
    return result


def attrition_metric_by_name(wave: dict[str, Any], name: str) -> dict[str, Any]:
    if name == GROUP_NO_COMMENT:
        return wave["no_comment"]
    return group_by_name(wave, name)


def displayed_composition_shares(wave: dict[str, Any]) -> dict[str, float]:
    """Allocate displayed tenths by largest remainder so every bar shows 100.0%."""
    groups = list(wave["composition"]["groups"])
    total = int(wave["survey_participant_count"])
    require(total > 0, "El denominador de participaci\u00f3n QVoice debe ser positivo.")
    allocated: dict[str, int] = {}
    remainders: list[tuple[int, str]] = []
    for group in groups:
        name = str(group["group"])
        tenths, remainder = divmod(1000 * int(group["participant_count"]), total)
        allocated[name] = tenths
        remainders.append((remainder, name))
    remaining_tenths = 1000 - sum(allocated.values())
    require(0 <= remaining_tenths <= len(groups), "La asignaci\u00f3n de decimales QVoice es inv\u00e1lida.")
    for _, name in sorted(remainders, key=lambda item: (-item[0], item[1]))[:remaining_tenths]:
        allocated[name] += 1
    require(sum(allocated.values()) == 1000, "Los porcentajes QVoice visibles no suman 100.0%.")
    return {name: tenths / 10.0 for name, tenths in allocated.items()}


def render_composition_rate_card(
    wave: dict[str, Any],
    group_name: str,
    label: str,
    css_class: str,
    all_rates: list[float],
    display_share: float,
) -> str:
    composition = composition_by_name(wave, group_name)
    attrition = attrition_metric_by_name(wave, group_name)
    participant_count = int(composition["participant_count"])
    rate = float(attrition["voluntary_attrition_rate_percent"])
    period = (
        "12-month voluntary attrition after the survey"
        if str(wave["attrition_window"]["outcome_type"]) == "annual_12m"
        else "YTD voluntary attrition through Aug 2026; not annualized"
    )
    tooltip = f"{label}: {display_share:.1f}% of QVoice participants (n={participant_count:,}); {period}: {rate:.1f}%"
    return (
        '<div class="qvoice18-rate-card '
        + css_class
        + '" title="'
        + html.escape(tooltip, quote=True)
        + '"><span class="qvoice18-rate-label">'
        + html.escape(label)
        + '</span><span class="qvoice18-rate-cohort">'
        + f"{display_share:.1f}% &middot; n={participant_count:,}"
        + '</span>'
        + render_qvoice18_attrition_pill(label, rate, all_rates)
        + "</div>"
    )


def render_composition_wave(wave: dict[str, Any], all_rates: list[float]) -> str:
    group_specs = (
        (GROUP_REQUEST_CONCERN, "Remote / hybrid / onsite", "is-focus"),
        (GROUP_ALL_OTHER, "Other written comment", "is-other"),
        (GROUP_NO_COMMENT, "No written comment", "is-no-comment"),
    )
    segments = []
    aria_parts = []
    display_shares = displayed_composition_shares(wave)
    for group_name, label, css_class in group_specs:
        composition = composition_by_name(wave, group_name)
        share = float(composition["share_of_survey_participants_percent"])
        participant_count = int(composition["participant_count"])
        segments.append(
            '<span class="qvoice18-composition-segment '
            + css_class
            + '" style="width:'
            + f"{share:.4f}%"
            + '"></span>'
        )
        aria_parts.append(f"{label} {display_shares[group_name]:.1f}% (n={participant_count:,})")
    wave_name = display_wave(str(wave["wave"]))
    survey_participant_count = int(wave["survey_participant_count"])
    period_label = (
        "12-month follow-up"
        if str(wave["attrition_window"]["outcome_type"]) == "annual_12m"
        else "YTD through Aug 2026"
    )
    cards = "".join(
        render_composition_rate_card(wave, group_name, label, css_class, all_rates, display_shares[group_name])
        for group_name, label, css_class in group_specs
    )
    return (
        '<div class="qvoice18-wave">'
        '<div class="qvoice18-wave-head"><strong>'
        + html.escape(wave_name)
        + '</strong><span>QVoice participants n='
        + f"{survey_participant_count:,} &middot; {period_label}"
        + "</span></div>"
        '<div class="qvoice18-composition-bar" role="img" aria-label="'
        + html.escape(f"{wave_name}: " + "; ".join(aria_parts), quote=True)
        + '">'
        + "".join(segments)
        + "</div>"
        '<div class="qvoice18-rate-grid">'
        + cards
        + "</div></div>"
    )


def build_stage(evidence: dict[str, Any]) -> str:
    """Build the approved three-group composition layout for navigation slide 18."""
    waves = list(evidence["waves"])
    all_rates = [
        float(attrition_metric_by_name(wave, group_name)["voluntary_attrition_rate_percent"])
        for wave in waves
        for group_name in (GROUP_REQUEST_CONCERN, GROUP_ALL_OTHER, GROUP_NO_COMMENT)
    ]
    composition_waves = "".join(render_composition_wave(wave, all_rates) for wave in waves)
    display_topic_labels = {
        "Request for remote or hybrid flexibility": "Remote/hybrid flexibility",
        "Policy enforcement, compliance, or exceptions": "Onsite policy / enforcement / exceptions",
        "Required days in the office": "Required onsite days",
        "Commute, parking, or travel time": "Commute / parking / travel",
        "Office space or facilities": "Onsite space / facilities",
    }
    topic_rows = "".join(
        f'''<div class="qvoice18-topic-row">
          <div class="qvoice18-topic-label">{html.escape(display_topic_labels.get(str(topic["label"]), str(topic["label"])))}</div>
          <div class="qvoice18-topic-bar" aria-hidden="true"><div style="width:{max(float(topic["share_of_request_or_concern_group_percent"]), 1.5):.4f}%"></div></div>
          <div class="qvoice18-topic-stats"><strong>{pct(float(topic["share_of_request_or_concern_group_percent"]))}</strong><span>n={int(topic["commenter_count"]):,}</span></div>
        </div>'''
        for topic in evidence["latest_survey_subthemes"]
    )
    return f'''<div class="slide-stage" id="slide-20" data-qvoice-open-text-request-concern="20260922" data-v7-qvoice-open-text-attrition-pills="true" data-v7-qvoice-open-text-no-comment-attrition="true" data-v7-qvoice-open-text-three-group-composition="true">
  <style>
    #slide-20 {{ grid-template-rows:auto 1fr; gap:8px; }}
    #slide-20 .slide-title-text {{ font-size:21px; max-width:1080px; }}
    #slide-20 .qvoice18-shell {{ display:grid; grid-template-rows:auto 1fr auto; gap:10px; min-height:0; padding:14px 16px 11px; }}
    #slide-20 .qvoice18-intro {{ display:flex; align-items:center; justify-content:space-between; gap:14px; padding:8px 11px; border:1px solid var(--border-subtle); border-radius:12px; background:var(--bg-surface-2); }}
    #slide-20 .qvoice18-intro strong {{ color:var(--text-main); font-size:12px; line-height:1.3; }}
    #slide-20 .qvoice18-legend {{ display:flex; align-items:center; flex-wrap:wrap; justify-content:flex-end; gap:7px 13px; color:var(--text-muted); font-size:10px; }}
    #slide-20 .qvoice18-legend span {{ display:inline-flex; align-items:center; gap:5px; white-space:nowrap; }}
    #slide-20 .qvoice18-legend i {{ display:inline-block; width:10px; height:10px; border-radius:3px; }}
    #slide-20 .qvoice18-legend .is-focus {{ background:var(--accent); }}
    #slide-20 .qvoice18-legend .is-other {{ background:color-mix(in oklab, var(--text-muted) 72%, transparent); }}
    #slide-20 .qvoice18-legend .is-no-comment {{ background:var(--accent-soft); border:1px solid var(--border-strong); }}
    #slide-20 .qvoice18-main {{ display:grid; grid-template-columns:1.65fr .95fr; gap:13px; min-height:0; }}
    #slide-20 .qvoice18-panel {{ min-height:0; overflow:hidden; padding:12px 13px; border:1px solid var(--border-subtle); border-radius:14px; background:color-mix(in oklab, var(--bg-surface) 92%, transparent); }}
    #slide-20 .qvoice18-panel-head {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; padding-bottom:7px; border-bottom:2px solid var(--accent); }}
    #slide-20 .qvoice18-panel-head strong {{ color:var(--text-main); font-size:13px; }}
    #slide-20 .qvoice18-panel-head span {{ color:var(--text-muted); font-size:10px; line-height:1.25; text-align:right; }}
    #slide-20 .qvoice18-waves {{ display:grid; gap:5px; padding-top:7px; }}
    #slide-20 .qvoice18-wave {{ padding:5px 0 7px; border-bottom:1px solid var(--border-subtle); }}
    #slide-20 .qvoice18-wave:last-child {{ border-bottom:0; padding-bottom:0; }}
    #slide-20 .qvoice18-wave-head {{ display:flex; align-items:baseline; justify-content:space-between; gap:10px; margin-bottom:5px; }}
    #slide-20 .qvoice18-wave-head strong {{ color:var(--text-main); font-size:12px; }}
    #slide-20 .qvoice18-wave-head span {{ color:var(--text-muted); font-size:10px; text-align:right; white-space:nowrap; }}
    #slide-20 .qvoice18-composition-bar {{ display:flex; height:22px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-2); }}
    #slide-20 .qvoice18-composition-segment {{ min-width:0; height:100%; }}
    #slide-20 .qvoice18-composition-segment.is-focus {{ background:var(--accent); }}
    #slide-20 .qvoice18-composition-segment.is-other {{ background:color-mix(in oklab, var(--text-muted) 72%, transparent); }}
    #slide-20 .qvoice18-composition-segment.is-no-comment {{ background:var(--accent-soft); }}
    #slide-20 .qvoice18-rate-grid {{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:6px; padding-top:6px; }}
    #slide-20 .qvoice18-rate-card {{ display:grid; grid-template-columns:minmax(0, 1fr) auto; column-gap:5px; row-gap:2px; align-items:center; padding:4px 6px; border:1px solid var(--border-subtle); border-radius:8px; background:var(--bg-surface-2); min-width:0; }}
    #slide-20 .qvoice18-rate-label {{ min-width:0; overflow:hidden; color:var(--text-main); font-size:10px; line-height:1.1; text-overflow:ellipsis; white-space:nowrap; }}
    #slide-20 .qvoice18-rate-cohort {{ grid-column:1; color:var(--text-muted); font-size:10px; font-variant-numeric:tabular-nums; white-space:nowrap; }}
    #slide-20 .qvoice18-rate-card .qvoice18-attrition-pill {{ grid-column:2; grid-row:1 / span 2; min-width:46px; margin:0; padding:3px 4px !important; font-size:10px !important; }}
    #slide-20 .qvoice18-topic-intro {{ margin:9px 0 8px; color:var(--text-muted); font-size:10px; line-height:1.3; }}
    #slide-20 .qvoice18-topic-list {{ display:grid; gap:10px; }}
    #slide-20 .qvoice18-topic-label {{ margin-bottom:4px; color:var(--text-main); font-size:11px; line-height:1.2; }}
    #slide-20 .qvoice18-topic-row {{ display:grid; grid-template-columns:minmax(0, 1fr) 70px; column-gap:8px; align-items:end; }}
    #slide-20 .qvoice18-topic-bar {{ grid-column:1; height:10px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }}
    #slide-20 .qvoice18-topic-bar > div {{ height:100%; border-radius:var(--radius-pill); background:var(--accent-2); }}
    #slide-20 .qvoice18-topic-stats {{ grid-column:2; grid-row:1 / span 2; display:flex; flex-direction:column; align-items:flex-end; gap:1px; font-variant-numeric:tabular-nums; }}
    #slide-20 .qvoice18-topic-stats strong {{ color:var(--text-main); font-size:12px; }}
    #slide-20 .qvoice18-topic-stats span {{ color:var(--text-muted); font-size:10px; }}
    #slide-20 .qvoice18-source {{ padding-top:7px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; line-height:1.28; }}
    #slide-20 .qvoice18-source strong {{ color:var(--text-main); }}
  </style>
  <div class="slide-heading"><div><h2 class="slide-title-text">QVoice open comments</h2><p class="slide-subtitle">Three mutually exclusive groups per survey wave; each bar sums to 100%</p></div><span class="badge badge-neutral">Open comments</span></div>
  <article class="card card-full qvoice18-shell">
    <div class="qvoice18-intro"><strong>How to read: each bar is all QVoice participants with a usable key in that wave.</strong><div class="qvoice18-legend" aria-label="Comment group legend"><span><i class="is-focus"></i>Remote / hybrid / onsite</span><span><i class="is-other"></i>Other written comment</span><span><i class="is-no-comment"></i>No written comment</span></div></div>
    <div class="qvoice18-main">
      <section class="qvoice18-panel" aria-label="Three-group comment composition and voluntary attrition by survey wave">
        <div class="qvoice18-panel-head"><strong>Participation mix and subsequent attrition</strong><span>2023-2025: 12 months after survey<br>2026: YTD through Aug 2026; not annualized</span></div>
        <div class="qvoice18-waves">{composition_waves}</div>
      </section>
      <section class="qvoice18-panel" aria-label="Most common topics in the most recent survey">
        <div class="qvoice18-panel-head"><strong>Most common topics</strong><span>2025 QVoice survey<br>(fielded Jan 2026)</span></div>
        <p class="qvoice18-topic-intro">Among remote/hybrid or onsite comments. A person may mention more than one topic.</p>
        <div class="qvoice18-topic-list">{topic_rows}</div>
      </section>
    </div>
    <div class="qvoice18-source"><strong>How attrition is calculated:</strong> voluntary exits divided by the matched active-Regular group before each survey. Composition uses all QVoice participants with a usable key. The comparison is descriptive only; it does not show that comments caused attrition.</div>
  </article>
</div>'''


def main() -> None:
    require(DECK.exists() and MANIFEST.exists() and EVIDENCE.exists(), "Falta el deck, manifest o evidencia QVoice.")
    evidence = load_evidence()
    deck_hash = digest(DECK)
    manifest_hash = digest(MANIFEST)
    before = DECK.read_text(encoding="utf-8")
    replacement = build_stage(evidence)
    original = stage_fragment(before, TARGET_STAGE)
    after = before.replace(original, replacement, 1)
    before_stages = stage_map(before)
    after_stages = stage_map(after)
    require(before_stages.keys() == after_stages.keys(), "El update cambió el inventario de slides.")
    for stage_id in before_stages:
        if stage_id != TARGET_STAGE:
            require(before_stages[stage_id] == after_stages[stage_id], f"El update cambió slide-{stage_id}.")
    slide = after_stages[TARGET_STAGE]
    for required in (
        "Three mutually exclusive groups per survey wave",
        "Participation mix and subsequent attrition",
        "all QVoice participants with a usable key",
        "2025 QVoice survey",
        "fielded Jan 2026",
        "YTD through Aug 2026",
        "The comparison is descriptive only",
    ):
        require(required in slide, f"Falta copy requerido: {required}.")
    for removed in ("qvoice-comment-chart", "Related office comments by survey", "How often employees mentioned each topic", "qvoice18-rail-card"):
        require(removed not in slide, f"Slide 18 conserva un visual reemplazado: {removed}.")
    require(slide.count('class="qvoice18-composition-bar"') == 4, "Slide 18 debe mostrar cuatro barras de composici\u00f3n.")
    require(slide.count('class="qvoice18-rate-card ') == 12, "Slide 18 debe mostrar doce tarjetas de attrition.")
    require(digest(DECK) == deck_hash, "El deck cambió concurrentemente; no se escribió.")
    temp_deck = DECK.with_suffix(".qvoice-request-concern.tmp")
    temp_deck.write_text(after, encoding="utf-8")
    temp_deck.replace(DECK)
    written_deck_hash = digest(DECK)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["updated_slide_18_qvoice_requests_and_concerns"] = {
        "navigation_slide": 18,
        "stage_id": "slide-20",
        "title": html.unescape(re.search(r"<h2 class=\"slide-title-text\">(.*?)</h2>", replacement).group(1)),
        "visual": "Four stacked 100% bars of QVoice participants: remote/hybrid/onsite comment, other written comment, and no written comment. Each group has its own voluntary-attrition pill; the most common non-exclusive latest-wave topics remain on the right.",
        "groups": [
            "Remote/hybrid or onsite attendance",
            "Other comments",
            "No written comment",
        ],
        "attrition_contract": evidence["outcome_contract"],
        "source_evidence": {
            "path": str(EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(EVIDENCE),
            "outcome": evidence["outcome"],
        },
        "privacy": "Aggregate-only internal analysis; no employee identifiers, employee rows, or raw comments are rendered.",
    }
    validation = manifest.setdefault("validation", {})
    validation["qvoice_slide_18_request_concern_refresh"] = {
        "outcome": "pass",
        "only_stage_changed": "slide-20",
        "three_group_composition_bars": 4,
        "three_group_attrition_cards": 12,
        "latest_survey_topics": len(evidence["latest_survey_subthemes"]),
        "all_visible_cohorts_n_at_least": 30,
        "jan_2026_ytd_cutoff": "2026-08-23",
        "raw_comments_or_identifiers_rendered": False,
    }
    manifest["output_deck"] = {
        "path": str(DECK.relative_to(ROOT)).replace("\\", "/"),
        "sha256": written_deck_hash,
    }
    require(digest(DECK) == written_deck_hash, "El deck cambió antes de actualizar el manifest.")
    require(digest(MANIFEST) == manifest_hash, "El manifest cambió concurrentemente; no se escribió.")
    temp_manifest = MANIFEST.with_suffix(".qvoice-request-concern.tmp")
    temp_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_manifest.replace(MANIFEST)
    print(DECK)
    print(MANIFEST)


if __name__ == "__main__":
    main()
