"""Render intuitive HTML v2 reports from frozen variable-assessment artifacts.

The renderer is intentionally separate from ``evaluate-attrition-variable``. It
does not execute notebooks, SQL, or Redshift queries and it never recalculates
scores. Every statement shown in the report comes from the frozen assessment,
decision, report detail, coverage, and evidence-ledger files for the run, plus
an optional, aggregate-only ``private-aggregate-metrics.json`` artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


CRITERION_ORDER = [
    "source",
    "definition",
    "coverage",
    "missingness",
    "consistency",
    "history",
    "join",
    "effort",
]

CRITERION_LABELS = {
    "source": "Fuente",
    "definition": "Definición",
    "coverage": "Cobertura",
    "missingness": "Datos faltantes",
    "consistency": "Consistencia",
    "history": "Historia",
    "join": "Integración",
    "effort": "Esfuerzo",
}

SEMANTIC_LABELS = {
    "direct_field": "Campo directo",
    "derived_metric": "Métrica derivada",
    "precomputed_metric": "Métrica precalculada",
    "ratio": "Ratio",
    "rate": "Tasa",
    "count": "Conteo",
    "flag": "Indicador",
    "event": "Evento",
    "category": "Categoría",
    "group": "Agrupación",
    "hierarchy": "Jerarquía",
    "survey": "Encuesta",
    "external": "Fuente externa",
    "text": "Texto",
    "unknown": "Por confirmar",
}

SENSITIVE_COLUMN_PATTERNS = (
    "employee_id",
    "emplid",
    "email",
    "first_name",
    "last_name",
    "employee_name",
    "manager_name",
    "supervisor_name",
    "dept_head_name",
    "address",
    "postal",
    "birth",
    "citizenship",
    "gender",
    "race",
    "disability",
    "veteran",
    "salary",
    "base_pay",
    "compensation",
    "comment",
    "free_text",
)

SENSITIVE_EXACT_COLUMNS = {
    "name",
    "emp_name",
    "legal_first_name",
    "legal_last_name",
    "preferred_first_name",
}

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.27.0.min.js"
DEFAULT_RUN = Path("output/assessments/attrition-43-monthly-fiscal-20260816")
PRIVATE_METRICS_FILENAME = "private-aggregate-metrics.json"
CHARTS_MANIFEST_FILENAME = "charts-manifest.json"


CONTENT_CSS = r"""
    /* Attrition variable assessment v2 */
    .slide-stage { grid-template-rows: auto 1fr; }
    .slide-title-text { font-size: clamp(20px, 3vw, 28px); }
    .slide-subtitle { font-size: 13px; }
    .card p { margin: 0; font-size: 14px; line-height: 1.45; }
    .card strong { color: var(--text-main); }
    .muted { color: var(--text-muted); }
    .small { font-size: 13px !important; line-height: 1.4 !important; }
    .micro { font-size: 11px !important; line-height: 1.35 !important; }
    .mono { font-family: "Cascadia Code", "Fira Code", Consolas, monospace; }
    .wrap-anywhere { overflow-wrap: anywhere; word-break: break-word; }

    .summary-layout {
      display: grid;
      grid-template-columns: 0.82fr 1.42fr;
      gap: 14px;
      min-height: 0;
    }
    .hero-card { align-items: center; justify-content: center; text-align: center; }
    .score-ring {
      --score-angle: 0deg;
      position: relative;
      width: 238px;
      height: 238px;
      border-radius: 50%;
      background: conic-gradient(var(--accent) 0 var(--score-angle), var(--border-subtle) var(--score-angle) 360deg);
      display: grid;
      place-items: center;
      margin: 4px auto 8px;
    }
    .score-ring::after {
      content: "";
      width: 164px;
      height: 164px;
      border-radius: 50%;
      background: var(--donut-hole-bg);
      border: 1px solid var(--border-subtle);
      position: absolute;
    }
    .score-ring-label { position: relative; z-index: 1; }
    .score-ring-label b { display: block; font-size: 50px; line-height: 1; color: var(--accent); }
    .score-ring-label span { font-size: 13px; color: var(--text-muted); }
    .hero-result { font-size: 23px; line-height: 1.2; font-weight: 800; max-width: 420px; }
    .hero-definition { font-size: 14px; color: var(--text-muted); max-width: 460px; }
    .summary-right { display: grid; grid-template-rows: auto 1fr auto; gap: 12px; min-height: 0; }
    .summary-facts { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .fact-card {
      background: var(--bg-surface-2);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 13px 14px;
      min-height: 90px;
    }
    .fact-label { font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); font-weight: 700; }
    .fact-value { font-size: 16px; line-height: 1.3; font-weight: 750; margin-top: 5px; }
    .decision-callout {
      background: color-mix(in oklab, var(--accent) 9%, var(--bg-surface));
      border-left: 4px solid var(--accent);
      border-radius: 10px;
      padding: 13px 15px;
      font-size: 15px;
      line-height: 1.45;
    }

    .agenda-vertical { display: flex; flex-direction: column; gap: 7px; }
    .agenda-item {
      display: flex;
      align-items: baseline;
      gap: 12px;
      background: var(--bg-surface-2);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 9px 14px;
    }
    .agenda-num {
      flex-shrink: 0;
      min-width: 92px;
      text-align: center;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: var(--accent);
      background: color-mix(in oklab, var(--accent) 12%, transparent);
      border: 1px solid color-mix(in oklab, var(--accent) 30%, var(--border-subtle));
      border-radius: var(--radius-pill);
      padding: 3px 8px;
    }
    .agenda-item strong { font-size: 14px; white-space: nowrap; }
    .agenda-sep { color: var(--border-strong); }
    .agenda-desc { color: var(--text-muted); font-size: 14px; line-height: 1.4; }

    .profile-grid { display: grid; grid-template-columns: 1.08fr .92fr; gap: 14px; min-height: 0; }
    .definition-box {
      background: color-mix(in oklab, var(--accent) 8%, var(--bg-surface));
      border: 1px solid var(--border-strong);
      border-radius: 12px;
      padding: 16px;
      font-size: 18px;
      font-weight: 650;
      line-height: 1.4;
    }
    .detail-list { display: grid; gap: 8px; }
    .detail-row {
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px solid var(--border-subtle);
      font-size: 14px;
      line-height: 1.4;
    }
    .detail-row:last-child { border-bottom: none; }
    .detail-key { color: var(--text-muted); font-weight: 700; }

    .score-grid { display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(2, 1fr); gap: 12px; min-height: 0; }
    .score-card { position: relative; justify-content: space-between; padding: 15px; }
    .score-card-top { display: flex; justify-content: space-between; gap: 8px; align-items: flex-start; }
    .score-card-name { font-size: 17px; font-weight: 800; }
    .score-value {
      width: 42px;
      height: 42px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-size: 20px;
      font-weight: 900;
      flex-shrink: 0;
    }
    .score-2 { background: color-mix(in oklab, #22c55e 17%, transparent); color: #16a34a; border: 1px solid color-mix(in oklab, #22c55e 36%, transparent); }
    .score-1 { background: color-mix(in oklab, #f59e0b 17%, transparent); color: #d97706; border: 1px solid color-mix(in oklab, #f59e0b 36%, transparent); }
    .score-0 { background: color-mix(in oklab, #ef4444 15%, transparent); color: #dc2626; border: 1px solid color-mix(in oklab, #ef4444 32%, transparent); }
    .score-track { height: 8px; border-radius: 5px; overflow: hidden; background: var(--border-subtle); }
    .score-track span { display: block; height: 100%; background: var(--accent); border-radius: 5px; }
    .score-summary { font-size: 14px; line-height: 1.4; color: var(--text-muted); }

    .criteria-grid { display: grid; grid-template-columns: repeat(2, 1fr); grid-template-rows: repeat(2, 1fr); gap: 12px; min-height: 0; }
    .criterion-card { padding: 13px 15px; gap: 7px; }
    .criterion-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
    .criterion-heading h3 { margin: 0; font-size: 17px; }
    .criterion-section { font-size: 13px; line-height: 1.38; }
    .criterion-section b { display: block; color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }
    .criterion-conclusion { border-left: 3px solid var(--accent); padding-left: 9px; }

    .history-layout { display: grid; grid-template-columns: 1.48fr .72fr; gap: 14px; min-height: 0; }
    .plot-card { padding: 12px 14px; }
    .plotly-chart { width: 100%; height: 430px; }
    .plot-fallback { height: 430px; display: flex; align-items: flex-end; gap: 3px; padding: 18px 8px 26px; position: relative; }
    .plot-fallback::before {
      content: "Plotly no disponible: vista compacta de cobertura mensual";
      position: absolute;
      top: 2px;
      left: 8px;
      font-size: 11px;
      color: var(--text-muted);
    }
    .fallback-bar { flex: 1; min-width: 3px; background: var(--accent); border-radius: 3px 3px 0 0; opacity: .78; }
    .history-side { display: grid; grid-template-rows: auto 1fr; gap: 12px; min-height: 0; }
    .kpi-stack { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
    .kpi-mini { background: var(--bg-surface-2); border: 1px solid var(--border-subtle); border-radius: 10px; padding: 10px; }
    .kpi-mini b { display: block; font-size: 22px; margin-top: 3px; }
    .kpi-mini span { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--text-muted); font-weight: 700; }
    .fiscal-list { display: flex; flex-direction: column; gap: 8px; }
    .fiscal-row { display: grid; grid-template-columns: 54px 1fr 58px; gap: 8px; align-items: center; font-size: 13px; }
    .bar-track { height: 12px; background: var(--border-subtle); border-radius: 8px; overflow: hidden; }
    .bar-track > span { display: block; height: 100%; background: var(--accent); border-radius: 8px; }

    .behavior-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; min-height: 0; }
    .chart-gallery { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; min-height: 0; }
    .chart-gallery .card { padding: 10px 12px; }
    .chart-gallery img { width: 100%; max-height: 560px; object-fit: contain; display: block; border-radius: 10px; background: var(--bg-surface-2); }
    .chart-caption { margin: 0 0 8px; color: var(--text-muted); font-size: 12px; font-weight: 700; }
    .private-behavior-grid { display: grid; grid-template-columns: 1.16fr .84fr; gap: 14px; min-height: 0; }
    .private-chart { width: 100%; height: 350px; }
    .private-fallback { display: flex; flex-direction: column; gap: 8px; min-height: 350px; justify-content: center; }
    .private-note { font-size: 12px; line-height: 1.38; color: var(--text-muted); }
    .private-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 3px; }
    .private-table th, .private-table td { padding: 6px 7px; border-bottom: 1px solid var(--border-subtle); text-align: left; }
    .private-table th { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .05em; }
    .private-table .private-number { text-align: right; font-variant-numeric: tabular-nums; }
    .private-status { background: color-mix(in oklab, #8b5cf6 10%, var(--bg-surface)); border-left: 4px solid #8b5cf6; border-radius: 10px; padding: 10px 12px; font-size: 13px; line-height: 1.4; }
    .hbar-list { display: flex; flex-direction: column; gap: 7px; min-height: 0; }
    .behavior-grid .hbar-list { flex: 1; justify-content: space-evenly; }
    .hbar-row { display: grid; grid-template-columns: minmax(100px, 160px) 1fr 74px; gap: 8px; align-items: center; font-size: 13px; }
    .hbar-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .hbar-value { text-align: right; font-variant-numeric: tabular-nums; color: var(--text-muted); }
    .privacy-panel { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; gap: 14px; }
    .privacy-icon { width: 92px; height: 92px; border-radius: 50%; display: grid; place-items: center; font-size: 42px; background: color-mix(in oklab, #8b5cf6 13%, transparent); border: 1px solid color-mix(in oklab, #8b5cf6 30%, transparent); }
    .callout {
      background: var(--bg-surface-2);
      border: 1px solid var(--border-subtle);
      border-left: 4px solid var(--accent);
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 13px;
      line-height: 1.4;
    }

    .validation-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; min-height: 0; }
    .validation-layout > .card { padding: 14px 15px; gap: 8px; }
    .question-box { font-size: 20px; font-weight: 800; line-height: 1.28; padding: 13px; border-radius: 12px; background: color-mix(in oklab, var(--accent) 9%, var(--bg-surface)); border: 1px solid var(--border-strong); }
    .validation-section { display: flex; flex-direction: column; gap: 3px; }
    .validation-section h3 { margin: 0; font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); }
    .validation-section p { font-size: 13px; line-height: 1.34; }
    .metric-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 7px; }
    .metric-box { background: var(--bg-surface-2); border: 1px solid var(--border-subtle); border-radius: 9px; padding: 8px 10px; }
    .metric-box span { display: block; font-size: 11px; color: var(--text-muted); overflow-wrap: anywhere; }
    .metric-box b { display: block; margin-top: 3px; font-size: 15px; overflow-wrap: anywhere; }
    .outcome-banner { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 10px; background: var(--bg-surface-2); border: 1px solid var(--border-subtle); }
    .outcome-banner strong { font-size: 17px; }

    .final-layout { display: grid; grid-template-columns: .9fr 1.1fr; gap: 14px; min-height: 0; }
    .recommendation-card { justify-content: center; text-align: center; }
    .recommendation-title { font-size: 29px; font-weight: 900; line-height: 1.2; }
    .recommendation-sub { font-size: 16px; color: var(--text-muted); line-height: 1.45; }
    .action-list { counter-reset: actions; display: flex; flex-direction: column; gap: 9px; }
    .action-item { counter-increment: actions; display: grid; grid-template-columns: 34px 1fr; gap: 10px; align-items: start; padding: 9px 10px; background: var(--bg-surface-2); border: 1px solid var(--border-subtle); border-radius: 10px; font-size: 14px; line-height: 1.4; }
    .action-item::before { content: counter(actions); width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center; background: var(--accent); color: var(--text-invert); font-weight: 800; }

    .badge-score-good { background: color-mix(in oklab, #22c55e 15%, transparent); color: #16a34a; border: 1px solid color-mix(in oklab, #22c55e 30%, transparent); }
    .badge-score-warn { background: color-mix(in oklab, #f59e0b 15%, transparent); color: #d97706; border: 1px solid color-mix(in oklab, #f59e0b 30%, transparent); }
    .badge-score-bad { background: color-mix(in oklab, #ef4444 12%, transparent); color: #dc2626; border: 1px solid color-mix(in oklab, #ef4444 25%, transparent); }
    .badge-restricted { background: color-mix(in oklab, #8b5cf6 13%, transparent); color: #7c3aed; border: 1px solid color-mix(in oklab, #8b5cf6 28%, transparent); }

    .audit-anchor { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; }
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera reportes HTML v2 desde artefactos congelados."
    )
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--variables", nargs="+", help="Carpetas, slugs o nombres de variables.")
    selection.add_argument("--all", action="store_true", help="Genera todas las variables del run.")
    parser.add_argument("--template", type=Path, help="Ruta explícita a base-fullscreen.html.")
    parser.add_argument("--force", action="store_true", help="Sobrescribe HTML v2 existentes.")
    parser.add_argument("--validate-only", action="store_true", help="Valida HTML v2 existentes sin regenerar.")
    return parser.parse_args(argv)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_text(value: Any, default: str = "No documentado") -> str:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    text = re.sub(r"\s+", " ", str(value)).strip()
    text = re.sub(r"\.\.+$", ".", text)
    return text or default


def esc(value: Any, default: str = "No documentado") -> str:
    return html.escape(clean_text(value, default), quote=True)


def short_text(value: Any, limit: int, default: str = "No documentado") -> str:
    text = clean_text(value, default)
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return cut.rstrip(".,;:") + "…"


def fmt_number(value: Any, decimals: int = 1) -> str:
    if value is None or value == "":
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return clean_text(value)
    if math.isfinite(number) and number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.{decimals}f}"


def normalize_column_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, (list, tuple, set)):
        return [clean_text(item, "") for item in value if clean_text(item, "")]
    return [clean_text(value, "")]


def is_sensitive_column(value: Any) -> bool:
    normalized = normalize_column_name(value)
    return normalized in SENSITIVE_EXACT_COLUMNS or any(
        pattern in normalized for pattern in SENSITIVE_COLUMN_PATTERNS
    )


def resolve_template(explicit: Path | None) -> Path:
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.append(
        Path.home()
        / ".codex"
        / "skills"
        / "html-slide-generator"
        / "templates"
        / "fullscreen"
        / "base-fullscreen.html"
    )
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved.is_file():
            return resolved
    raise FileNotFoundError(
        "No se encontró base-fullscreen.html. Use --template con la ruta del skill."
    )


def load_bundle(variable_dir: Path) -> dict[str, Any]:
    required = {
        "assessment": variable_dir / "assessment.json",
        "decision": variable_dir / "decision.json",
        "report": variable_dir / "report_detail.json",
        "coverage": variable_dir / "coverage.json",
        "ledger": variable_dir / "evidence-ledger.json",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Faltan artefactos congelados: " + ", ".join(missing))
    bundle = {name: read_json(path) for name, path in required.items()}
    bundle["paths"] = required
    private_metrics_path = variable_dir / PRIVATE_METRICS_FILENAME
    if private_metrics_path.is_file():
        bundle["private_metrics"] = read_json(private_metrics_path)
        bundle["paths"]["private_metrics"] = private_metrics_path
    else:
        bundle["private_metrics"] = {}
    charts_manifest_path = variable_dir / CHARTS_MANIFEST_FILENAME
    if charts_manifest_path.is_file():
        charts = read_json(charts_manifest_path)
        if not isinstance(charts, list):
            raise ValueError(f"El manifest de gráficos debe ser una lista: {charts_manifest_path}")
        bundle["charts"] = charts
        bundle["paths"]["charts_manifest"] = charts_manifest_path
    else:
        bundle["charts"] = []
    bundle["variable_dir"] = variable_dir
    return bundle


def select_variable_dirs(run_dir: Path, selectors: list[str] | None, use_all: bool) -> list[Path]:
    variables_root = run_dir / "vars"
    if not variables_root.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de variables: {variables_root}")
    directories = sorted(path for path in variables_root.iterdir() if path.is_dir())
    if use_all:
        return directories

    selected: list[Path] = []
    for selector in selectors or []:
        needle = selector.casefold().strip()
        matches: list[Path] = []
        for path in directories:
            folder_forms = {
                path.name.casefold(),
                re.sub(r"^\d+-", "", path.name).casefold(),
            }
            if needle in folder_forms:
                matches.append(path)
                continue
            assessment_path = path / "assessment.json"
            if assessment_path.is_file():
                variable = clean_text(read_json(assessment_path).get("variable"), "").casefold()
                if needle == variable:
                    matches.append(path)
        unique = list(OrderedDict((match.resolve(), match) for match in matches).values())
        if len(unique) != 1:
            raise ValueError(
                f"El selector '{selector}' produjo {len(unique)} coincidencias; use el nombre exacto de carpeta."
            )
        if unique[0] not in selected:
            selected.append(unique[0])
    return selected


def semantic_type(bundle: dict[str, Any]) -> str:
    assessment = bundle["assessment"]
    verification = assessment.get("score_verification") or {}
    source = verification.get("source") or {}
    raw = clean_text(source.get("semantic_type"), "unknown")
    return SEMANTIC_LABELS.get(raw, raw.replace("_", " ").capitalize())


def score_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    report_rows = bundle["report"].get("score_application") or []
    by_key = {clean_text(row.get("criterion_key"), ""): row for row in report_rows}
    scores = bundle["assessment"].get("scores") or {}
    rows = []
    for key in CRITERION_ORDER:
        row = dict(by_key.get(key) or {})
        row["criterion_key"] = key
        row["criterion"] = CRITERION_LABELS[key]
        row["score"] = int(row.get("score", scores.get(key, 0)) or 0)
        rows.append(row)
    return rows


def recent_coverage(bundle: dict[str, Any]) -> dict[str, Any]:
    assessment = bundle["assessment"]
    diagnostics = assessment.get("diagnostics") or {}
    rows = bundle["coverage"] or []
    recent = rows[-12:] if rows else []
    eligible = sum(float(row.get("eligible_employees") or 0) for row in recent)
    observable = sum(float(row.get("observable_employees") or 0) for row in recent)
    missing = sum(float(row.get("missing_employees") or 0) for row in recent)
    coverage = diagnostics.get("recent_coverage_percent")
    if coverage is None and eligible:
        coverage = 100.0 * observable / eligible
    missingness = diagnostics.get("recent_missingness_percent")
    if missingness is None and eligible:
        missingness = 100.0 * missing / eligible
    return {
        "coverage": coverage,
        "missingness": missingness,
        "history_months": diagnostics.get("history_months"),
        "first": assessment.get("first_observed_date"),
        "usable": assessment.get("usable_since_date"),
        "latest": assessment.get("latest_observation_date"),
        "rows": len(rows),
    }


def fiscal_coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: OrderedDict[str, dict[str, float]] = OrderedDict()
    for row in rows:
        fiscal_year = clean_text(row.get("fiscal_year"), "Sin FY")
        group = groups.setdefault(
            fiscal_year,
            {"eligible": 0.0, "observable": 0.0, "missing": 0.0, "snapshots": 0.0},
        )
        group["eligible"] += float(row.get("eligible_employees") or 0)
        group["observable"] += float(row.get("observable_employees") or 0)
        group["missing"] += float(row.get("missing_employees") or 0)
        group["snapshots"] += 1
    result = []
    for fiscal_year, group in groups.items():
        eligible = group["eligible"]
        result.append(
            {
                "fiscal_year": fiscal_year,
                "coverage": (100.0 * group["observable"] / eligible) if eligible else None,
                "missingness": (100.0 * group["missing"] / eligible) if eligible else None,
                "snapshots": int(group["snapshots"]),
            }
        )
    return result


def safe_distributions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    safe = []
    internal_analysis = (
        bundle["report"].get("reporting_mode") == "internal_analysis"
    )
    for item in bundle["report"].get("value_distributions") or []:
        column = item.get("column")
        if item.get("suppressed") or (
            is_sensitive_column(column) and not internal_analysis
        ):
            continue
        values = [
            value
            for value in (item.get("values") or [])
            if int(value.get("employee_count") or 0) >= 30
        ]
        if values:
            safe.append({**item, "values": values[:10]})
    return safe


def safe_numeric_bands(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in (bundle["report"].get("numeric_bands") or [])
        if int(item.get("employee_count") or 0) >= 30
    ]


def notebook_charts(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """Return only chart files declared by the executed notebook."""
    result: list[dict[str, str]] = []
    root = bundle["variable_dir"]
    for item in bundle.get("charts") or []:
        if not isinstance(item, dict):
            continue
        relative = str(item.get("file") or "").replace("\\", "/")
        if not relative.startswith("charts/") or ".." in Path(relative).parts:
            continue
        path = root / relative
        if path.is_file():
            result.append({
                "file": relative,
                "title": clean_text(item.get("title"), "Gráfico agregado reproducible"),
            })
    return result


def safe_mappings(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    relationships = bundle["report"].get("column_relationships") or {}
    result = []
    for item in relationships.get("top_mappings") or []:
        pair = clean_text(item.get("pair"), "")
        if is_sensitive_column(pair):
            continue
        if int(item.get("employee_count") or 0) < 30:
            continue
        result.append(item)
    return result[:10]


def data_type_summary(bundle: dict[str, Any]) -> str:
    values = []
    for column in bundle["report"].get("columns") or []:
        data_type = clean_text(column.get("data_type"), "")
        if data_type and data_type not in values:
            values.append(data_type)
    return ", ".join(values) if values else clean_text(bundle["assessment"].get("measurement_type"))


def problem_context(bundle: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = bundle["assessment"].get("analysis_plan") or bundle["report"].get("analysis_plan") or {}
    isolation = plan.get("context_isolation") or {}
    return isolation.get("problem_context") or {}, isolation.get("current_variable_alignment") or {}


def score_badge(score: int) -> str:
    cls = {2: "badge-score-good", 1: "badge-score-warn", 0: "badge-score-bad"}.get(score, "badge-neutral")
    label = {2: "Cumple", 1: "Parcial", 0: "No cumple"}.get(score, "Sin score")
    return f'<span class="badge {cls}">{score} · {label}</span>'


def result_badge(result: str) -> str:
    lowered = result.casefold()
    if "sensible" in lowered or "restring" in lowered:
        cls = "badge-restricted"
    elif "no disponible" in lowered or "excluir" in lowered:
        cls = "badge-score-bad"
    elif "trabajo" in lowered or "externa" in lowered or "definir" in lowered:
        cls = "badge-score-warn"
    else:
        cls = "badge-score-good"
    return f'<span class="badge {cls}">{html.escape(result)}</span>'


def decision_message(result: str) -> str:
    lowered = result.casefold()
    if "sensible" in lowered or "restring" in lowered:
        return "La evidencia técnica existe, pero la variable no debe entrar al modelo sin una decisión explícita de gobernanza y uso responsable."
    if "no disponible" in lowered or "excluir" in lowered:
        return "La evidencia actual no permite construir esta variable de forma auditable para el modelo."
    if "externa" in lowered:
        return "El concepto puede ser relevante, pero depende de acceso, propiedad y una ruta de integración todavía no aprobada."
    if "por definir" in lowered:
        return "El concepto todavía no está definido con suficiente precisión para evaluarlo o implementarlo."
    if "trabajo" in lowered:
        return "La variable puede convertirse en candidata, pero aún necesita cerrar las brechas señaladas antes de incorporarla al pipeline."
    return "La variable cuenta con evidencia suficiente para continuar bajo las condiciones documentadas."


def model_recommendation(result: str) -> tuple[str, str]:
    lowered = result.casefold()
    if "sensible" in lowered or "restring" in lowered:
        return (
            "No usar como predictor sin aprobación",
            "Mantenerla fuera del entrenamiento hasta contar con gobernanza, propósito permitido y controles de privacidad; puede evaluarse por separado para monitoreo autorizado.",
        )
    if "no disponible" in lowered or "excluir" in lowered:
        return ("Excluir por ahora", "No existe evidencia suficiente para una implementación reproducible y auditable.")
    if "externa" in lowered:
        return ("Esperar integración aprobada", "Resolver acceso, owner, refresh, población y join antes de tratarla como feature.")
    if "por definir" in lowered:
        return ("Definir antes de construir", "Acordar concepto, población, ventana y fuente antes de escribir SQL de producción.")
    if "trabajo" in lowered:
        return ("Candidata condicionada", "Puede continuar al backlog de features cuando se completen las acciones que limitan Definition, Consistency, Join o Effort.")
    return ("Candidata para continuar", "Mantener las reglas y evidencia del assessment como controles de implementación.")


def slide(index: int, title: str, subtitle: str, content: str) -> str:
    return f"""
  <div class="slide-stage" id="slide-{index}">
    <div class="slide-heading">
      <div>
        <h2 class="slide-title-text">{html.escape(title)}</h2>
        <p class="slide-subtitle">{html.escape(subtitle)}</p>
      </div>
    </div>
    {content}
  </div>"""


def render_summary(bundle: dict[str, Any]) -> str:
    assessment = bundle["assessment"]
    decision = bundle["decision"]
    result = clean_text(assessment.get("result") or decision.get("final_result"))
    total = int(assessment.get("total") or sum(item["score"] for item in score_rows(bundle)))
    angle = max(0.0, min(360.0, total / 16 * 360.0))
    blocker = decision.get("blocker") or {}
    blocker_label = clean_text(blocker.get("label") if isinstance(blocker, dict) else blocker, "Ninguno")
    source_columns = ", ".join(text_list(assessment.get("source_columns")))
    if not source_columns:
        source_columns = "No documentadas"
    content = f"""
    <div class="summary-layout">
      <article class="card hero-card">
        <div class="score-ring" style="--score-angle:{angle:.2f}deg">
          <div class="score-ring-label"><b>{total}</b><span>de 16 puntos</span></div>
        </div>
        <div class="hero-result">{html.escape(result)}</div>
        <div>{result_badge(result)}</div>
        <div class="hero-definition">{esc(short_text(assessment.get('definition_text'), 310))}</div>
      </article>
      <div class="summary-right">
        <div class="summary-facts">
          <div class="fact-card"><div class="fact-label">Tipo semántico</div><div class="fact-value">{html.escape(semantic_type(bundle))}</div></div>
          <div class="fact-card"><div class="fact-label">Tipo de dato</div><div class="fact-value">{html.escape(data_type_summary(bundle))}</div></div>
          <div class="fact-card"><div class="fact-label">Fuente</div><div class="fact-value wrap-anywhere">{esc(assessment.get('source_table'))}</div></div>
          <div class="fact-card"><div class="fact-label">Campos evaluados</div><div class="fact-value wrap-anywhere">{html.escape(source_columns)}</div></div>
        </div>
        <article class="card">
          <div class="card-title">Conclusión central</div>
          <div class="decision-callout">{html.escape(decision_message(result))}</div>
          <ul class="bullet-list">
            <li><strong>Blocker:</strong> {html.escape(blocker_label)}</li>
            <li><strong>Frecuencia:</strong> {esc(assessment.get('observation_frequency'))}</li>
            <li><strong>Grain:</strong> {esc(assessment.get('level_data'))}</li>
          </ul>
        </article>
        <p class="small muted">Reporte v2 construido exclusivamente desde resultados congelados; no recalcula scores ni sustituye la evidencia SQL.</p>
      </div>
    </div>"""
    return slide(1, clean_text(assessment.get("variable")), "Resultado en una mirada", content)


def render_agenda(bundle: dict[str, Any]) -> str:
    variable = clean_text(bundle["assessment"].get("variable"))
    validation_start = 9
    validation_count = max(1, len(bundle["report"].get("validation_story") or []))
    validation_end = validation_start + validation_count - 1
    chart_groups = notebook_chart_groups(bundle)
    chart_start = validation_end + 1
    final_index = chart_start + len(chart_groups)

    def span(start: int, end: int) -> str:
        return f"Slide {start}" if start == end else f"Slides {start}–{end}"

    entries = [
        ("Slide 3", "Qué es la variable", "Definición, contexto de attrition, fuente, población y granularidad."),
        ("Slide 4", "Scorecard", "Los ocho criterios y la lectura general del resultado."),
        ("Slides 5–6", "Por qué recibió esos scores", "Reglas, evidencia observada, conclusión y acción por criterio."),
        ("Slides 7–8", "Evidencia visual", "Historia, cobertura, missingness, frecuencias, bandas o límites de publicación."),
        (span(validation_start, validation_end), "Validaciones", "Qué se preguntó, cómo se probó, qué ocurrió y cómo impactó el score."),
    ]
    if chart_groups:
        entries.append(
            (span(chart_start, final_index - 1), "Gráficos reproducibles", "Visualizaciones guardadas por el notebook a partir de evidencia agregada congelada.")
        )
    entries.append((f"Slide {final_index}", "Decisión", "Uso recomendado en el modelo y siguientes pasos concretos."))
    rows = "".join(
        f'<div class="agenda-item"><span class="agenda-num">{number}</span><strong>{title}</strong><span class="agenda-sep">—</span><span class="agenda-desc">{description}</span></div>'
        for number, title, description in entries
    )
    content = f'<article class="card card-full"><div class="agenda-vertical">{rows}</div></article>'
    return slide(2, "Guía del reporte", f"{variable}: del concepto a la decisión", content)


def render_profile(bundle: dict[str, Any]) -> str:
    assessment = bundle["assessment"]
    problem, alignment = problem_context(bundle)
    source_columns = ", ".join(text_list(assessment.get("source_columns"))) or "No documentadas"
    problem_statement = problem.get("problem_statement") or "Predecir attrition voluntario con snapshots mensuales y lectura fiscal."
    use_case = problem.get("decision_or_use_case") or "Construcción y evaluación de features para un modelo de attrition voluntario."
    role = alignment.get("role") or "Variable candidata"
    relevance = alignment.get("relevance") or assessment.get("notes") or "La relevancia específica está documentada en el plan de análisis."
    content = f"""
    <div class="profile-grid">
      <article class="card">
        <div class="card-title">Definición evaluada</div>
        <div class="definition-box">{esc(assessment.get('definition_text'))}</div>
        <div class="validation-section"><h3>Problema que ayuda a resolver</h3><p>{esc(problem_statement)}</p></div>
        <div class="validation-section"><h3>Uso esperado</h3><p>{esc(use_case)}</p></div>
        <div class="validation-section"><h3>Rol y relevancia</h3><p><strong>{esc(role)}.</strong> {esc(relevance)}</p></div>
      </article>
      <article class="card">
        <div class="card-title">Contrato de datos</div>
        <div class="detail-list">
          <div class="detail-row"><div class="detail-key">Tipo semántico</div><div>{html.escape(semantic_type(bundle))}</div></div>
          <div class="detail-row"><div class="detail-key">Tipo de dato</div><div>{html.escape(data_type_summary(bundle))}</div></div>
          <div class="detail-row"><div class="detail-key">Tabla fuente</div><div class="mono wrap-anywhere">{esc(assessment.get('source_table'))}</div></div>
          <div class="detail-row"><div class="detail-key">Columnas</div><div class="mono wrap-anywhere">{html.escape(source_columns)}</div></div>
          <div class="detail-row"><div class="detail-key">Población</div><div>{esc(assessment.get('population_filter'))}</div></div>
          <div class="detail-row"><div class="detail-key">Grain</div><div>{esc(assessment.get('level_data'))}</div></div>
          <div class="detail-row"><div class="detail-key">Fecha de conocimiento</div><div>{esc((assessment.get('analysis_plan') or {}).get('knowledge_date') or assessment.get('usable_since_date'))}</div></div>
          <div class="detail-row"><div class="detail-key">Frecuencia</div><div>{esc(assessment.get('observation_frequency'))}</div></div>
        </div>
      </article>
    </div>"""
    return slide(3, "Qué es esta variable", clean_text(assessment.get("variable")), content)


def render_scorecard(bundle: dict[str, Any]) -> str:
    cards = []
    for row in score_rows(bundle):
        score = row["score"]
        width = max(0, min(100, score / 2 * 100))
        why = short_text(row.get("why") or row.get("observed_evidence"), 185)
        cards.append(
            f"""<article class="card score-card">
              <div class="score-card-top"><div class="score-card-name">{html.escape(row['criterion'])}</div><div class="score-value score-{score}">{score}</div></div>
              <div class="score-summary">{html.escape(why)}</div>
              <div><div class="score-track"><span style="width:{width:.0f}%"></span></div><p class="micro muted" style="margin-top:5px">0 = no cumple · 1 = parcial · 2 = cumple con evidencia</p></div>
            </article>"""
        )
    total = int(bundle["assessment"].get("total") or sum(row["score"] for row in score_rows(bundle)))
    content = '<div class="score-grid">' + "".join(cards) + "</div>"
    return slide(4, "Scorecard de ocho criterios", f"Total: {total}/16; cada score conserva su regla y evidencia", content)


def criterion_card(row: dict[str, Any]) -> str:
    score = row["score"]
    return f"""<article class="card criterion-card">
      <div class="criterion-heading"><h3>{html.escape(row['criterion'])}</h3>{score_badge(score)}</div>
      <div class="criterion-section"><b>Regla evaluada</b>{esc(short_text(row.get('status_rule'), 235))}</div>
      <div class="criterion-section"><b>Evidencia observada</b>{esc(short_text(row.get('observed_evidence'), 245))}</div>
      <div class="criterion-section criterion-conclusion"><b>Conclusión</b>{esc(short_text(row.get('why'), 245))}</div>
      <div class="criterion-section"><b>Acción</b>{esc(short_text(row.get('recommended_action'), 210))}</div>
    </article>"""


def render_criteria(bundle: dict[str, Any], index: int, keys: list[str], title: str) -> str:
    by_key = {row["criterion_key"]: row for row in score_rows(bundle)}
    content = '<div class="criteria-grid">' + "".join(criterion_card(by_key[key]) for key in keys) + "</div>"
    return slide(index, title, "Regla → evidencia → conclusión → acción", content)


def render_fiscal_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="muted">No existe historia fiscal calculada.</p>'
    rendered = []
    for row in rows[-7:]:
        coverage = row.get("coverage")
        width = max(0.0, min(100.0, float(coverage or 0)))
        rendered.append(
            f'<div class="fiscal-row"><strong>FY{html.escape(str(row["fiscal_year"]))}</strong><div class="bar-track"><span style="width:{width:.2f}%"></span></div><span>{fmt_number(coverage)}%</span></div>'
        )
    return '<div class="fiscal-list">' + "".join(rendered) + "</div>"


def fallback_bars(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<div class="plot-fallback"><p class="muted">No existe coverage mensual publicable.</p></div>'
    bars = []
    for row in rows[-48:]:
        value = float(row.get("observable_coverage_percent") or 0)
        bars.append(
            f'<span class="fallback-bar" title="{esc(row.get("snapshot_date"))}: {value:.2f}%" style="height:{max(2.0, min(100.0, value)):.2f}%"></span>'
        )
    return '<div class="plot-fallback" id="coverage-fallback">' + "".join(bars) + "</div>"


def render_history(bundle: dict[str, Any]) -> str:
    rows = bundle["coverage"] or []
    recent = recent_coverage(bundle)
    if rows:
        chart = f'<div id="coverage-chart" class="plotly-chart" aria-label="Cobertura y missingness por snapshot"></div>{fallback_bars(rows)}'
    else:
        chart = '<div class="privacy-panel"><div class="privacy-icon">∅</div><h3>No hay historia calculada</h3><p class="muted">La fuente o el concepto aún no permiten construir coverage mensual para la población objetivo.</p></div>'
    content = f"""
    <div class="history-layout">
      <article class="card plot-card"><div class="card-title">Tendencia mensual</div>{chart}</article>
      <div class="history-side">
        <article class="card card-compact">
          <div class="card-title">Lectura reciente</div>
          <div class="kpi-stack">
            <div class="kpi-mini"><span>Coverage</span><b>{fmt_number(recent['coverage'])}%</b></div>
            <div class="kpi-mini"><span>Missingness</span><b>{fmt_number(recent['missingness'])}%</b></div>
            <div class="kpi-mini"><span>Meses útiles</span><b>{fmt_number(recent['history_months'])}</b></div>
            <div class="kpi-mini"><span>Snapshots</span><b>{fmt_number(recent['rows'])}</b></div>
          </div>
          <p class="small"><strong>Primera observación:</strong> {esc(recent['first'])}<br><strong>Utilizable desde:</strong> {esc(recent['usable'])}<br><strong>Última observación:</strong> {esc(recent['latest'])}</p>
        </article>
        <article class="card card-compact"><div class="card-title">Resumen fiscal ponderado</div>{render_fiscal_rows(fiscal_coverage(rows))}</article>
      </div>
    </div>"""
    return slide(7, "Historia, cobertura y datos faltantes", "Snapshots mensuales con resumen fiscal", content)


def render_hbars(title: str, rows: Iterable[dict[str, Any]], label_key: str, value_key: str) -> str:
    rows = list(rows)
    maximum = max([int(row.get(value_key) or 0) for row in rows] or [1])
    items = []
    for row in rows[:10]:
        value = int(row.get(value_key) or 0)
        width = 100.0 * value / maximum if maximum else 0
        items.append(
            f'<div class="hbar-row"><span class="hbar-label" title="{esc(row.get(label_key))}">{esc(row.get(label_key))}</span><div class="bar-track"><span style="width:{width:.2f}%"></span></div><span class="hbar-value">{fmt_number(value, 0)}</span></div>'
        )
    return f'<article class="card"><div class="card-title">{html.escape(title)}</div><div class="hbar-list">{"".join(items)}</div></article>'


def render_completeness(bundle: dict[str, Any]) -> str:
    rows = []
    for item in (bundle["report"].get("columns") or [])[:10]:
        populated = int(item.get("populated_employees") or 0)
        missing = int(item.get("missing_employees") or 0)
        total = populated + missing
        pct = 100.0 * populated / total if total else 0
        rows.append({"label": item.get("column"), "value": pct})
    if not rows:
        return '<p class="muted">No existe perfil de completitud publicable.</p>'
    rendered = []
    for row in rows:
        rendered.append(
            f'<div class="hbar-row"><span class="hbar-label">{esc(row["label"])}</span><div class="bar-track"><span style="width:{row["value"]:.2f}%"></span></div><span class="hbar-value">{row["value"]:.1f}%</span></div>'
        )
    return '<div class="hbar-list">' + "".join(rendered) + "</div>"


def private_aggregate_metrics(bundle: dict[str, Any]) -> dict[str, Any]:
    metrics = bundle.get("private_metrics") or {}
    if not isinstance(metrics, dict) or not metrics.get("schema_version"):
        return {}
    report_mode = bundle["report"].get("reporting_mode", "presentation")
    metrics_mode = metrics.get("reporting_mode", "presentation")
    return metrics if report_mode == metrics_mode else {}


def private_metric_value(card: dict[str, Any]) -> str:
    value = card.get("value")
    if isinstance(value, str):
        return esc(value)
    rendered = fmt_number(value, 1)
    return f"{rendered}%" if card.get("format") == "percent" and rendered != "—" else rendered


def render_private_metric_cards(metrics: dict[str, Any]) -> str:
    cards = metrics.get("metric_cards") or []
    if not cards:
        return '<p class="muted">No se registraron métricas agregadas adicionales.</p>'
    rendered = []
    for card in cards[:4]:
        rendered.append(
            f'<div class="metric-box"><span>{esc(card.get("label"))}</span><b>{private_metric_value(card)}</b><p class="micro muted">{esc(card.get("note"), "")}</p></div>'
        )
    return '<div class="metric-grid">' + "".join(rendered) + "</div>"


def render_private_distribution_table(distribution: dict[str, Any]) -> str:
    categories = distribution.get("categories") or []
    if not categories:
        return '<p class="muted">No existe una distribución agregada verificable.</p>'
    rows = []
    for item in categories[:10]:
        count = fmt_number(item.get("count"), 0)
        percent = fmt_number(item.get("percent"), 1)
        percent = f"{percent}%" if percent != "—" else "—"
        rows.append(
            f'<tr><td>{esc(item.get("label"))}</td><td class="private-number">{count}</td><td class="private-number">{percent}</td></tr>'
        )
    return (
        '<table class="private-table"><thead><tr><th>Grupo</th><th class="private-number">N</th><th class="private-number">%</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def render_private_fallback(distribution: dict[str, Any]) -> str:
    return (
        '<div id="private-metrics-fallback" class="private-fallback">'
        '<div class="card-title">Vista tabular si el gráfico no carga</div>'
        f'{render_private_distribution_table(distribution)}'
        '</div>'
    )


def render_private_behavior(bundle: dict[str, Any], metrics: dict[str, Any]) -> str:
    status = clean_text(metrics.get("status"), "unavailable")
    distribution = metrics.get("distribution") or {}
    limitations = metrics.get("limitations") or []
    if status == "unavailable":
        reason = limitations[0] if limitations else "No existe una fuente aprobada que permita calcular cifras agregadas."
        content = f"""
        <div class="behavior-grid">
          <article class="card privacy-panel">
            <div class="privacy-icon">∅</div>
            <h3>No hay cifras verificables</h3>
            <p>{esc(reason)}</p>
          </article>
          <article class="card">
            <div class="card-title">Estado de la evidencia</div>
            {render_private_metric_cards(metrics)}
            <div class="private-status">Este reporte muestra el límite de la fuente de forma explícita; no crea una distribución ni una métrica derivada sin evidencia.</div>
          </article>
        </div>"""
        return slide(8, "Cómo se comporta la variable", "Cifras agregadas privadas y límites de evidencia", content)

    title = clean_text(distribution.get("title"), "Métricas agregadas")
    subtitle = clean_text(distribution.get("subtitle"), "Sólo se muestran cohortes agregadas y publicables.")
    limitations_html = "".join(f"<li>{esc(item)}</li>" for item in limitations[:3])
    content = f"""
    <div class="private-behavior-grid">
      <article class="card plot-card">
        <div class="card-title">{html.escape(title)}</div>
        <div id="private-metrics-chart" class="private-chart" aria-label="{esc(title)}"></div>
        {render_private_fallback(distribution)}
      </article>
      <article class="card">
        <div class="card-title">Cifras privadas agregadas</div>
        {render_private_metric_cards(metrics)}
        <div class="card-title">Detalle del gráfico</div>
        {render_private_distribution_table(distribution)}
        <p class="private-note">{esc(subtitle)}</p>
        <ul class="bullet-list">{limitations_html or '<li>Las cifras no recalculan scores ni sustituyen validaciones pendientes.</li>'}</ul>
      </article>
    </div>"""
    return slide(8, "Cómo se comporta la variable", "Cifras agregadas privadas; no se recalculan scores", content)


def render_behavior(bundle: dict[str, Any]) -> str:
    metrics = private_aggregate_metrics(bundle)
    if metrics:
        return render_private_behavior(bundle, metrics)
    distributions = safe_distributions(bundle)
    bands = safe_numeric_bands(bundle)
    mappings = safe_mappings(bundle)
    report = bundle["report"]
    internal_analysis = report.get("reporting_mode") == "internal_analysis"
    suppressed = [
        item
        for item in report.get("value_distributions") or []
        if item.get("suppressed")
        or (is_sensitive_column(item.get("column")) and not internal_analysis)
    ]

    panels: list[str] = []
    subtitle = "Sólo se muestran agregados y cohortes publicables"
    if bands:
        band_total = sum(int(item.get("employee_count") or 0) for item in bands)
        largest_band = max(bands, key=lambda item: int(item.get("employee_count") or 0))
        largest_count = int(largest_band.get("employee_count") or 0)
        largest_share = 100.0 * largest_count / band_total if band_total else 0.0
        panels.append(render_hbars("Bandas seguras", bands, "band_label", "employee_count"))
        panels.append(
            f'<article class="card"><div class="card-title">Qué demuestra este gráfico</div><div class="decision-callout">Las bandas permiten observar forma y concentración sin publicar compensación exacta.</div><div class="metric-grid"><div class="metric-box"><span>Empleados agregados</span><b>{fmt_number(band_total, 0)}</b></div><div class="metric-box"><span>Banda principal</span><b>{esc(largest_band.get("band_label"))}</b></div><div class="metric-box"><span>Participación principal</span><b>{largest_share:.1f}%</b></div><div class="metric-box"><span>Bandas publicables</span><b>{len(bands)}</b></div></div><div class="card-title">Completitud de columnas</div>{render_completeness(bundle)}<ul class="bullet-list"><li>La concentración ayuda a identificar rangos dominantes y posibles extremos.</li><li>Una distribución plausible no confirma por sí sola la fórmula, el lineage ni la definición de negocio.</li></ul></article>'
        )
    elif distributions:
        for item in distributions[:2]:
            panels.append(render_hbars(f"Frecuencias: {clean_text(item.get('column'))}", item.get("values") or [], "value_label", "employee_count"))
        if len(panels) == 1 and mappings:
            panels.append(render_hbars("Mappings principales", mappings, "left_value", "employee_count"))
        elif len(panels) == 1:
            panels.append(f'<article class="card"><div class="card-title">Completitud de columnas</div>{render_completeness(bundle)}<div class="callout">Las frecuencias ayudan a detectar concentración y valores dominantes; no demuestran que el dominio sea correcto.</div></article>')
        elif mappings:
            panels[-1] = panels[-1].replace(
                "</article>",
                '<div class="callout">Además se revisaron mappings agregados entre columnas para detectar relaciones ambiguas.</div></article>',
            )
    elif mappings:
        panels.append(render_hbars("Mappings principales", mappings, "left_value", "employee_count"))
        panels.append(f'<article class="card"><div class="card-title">Completitud de columnas</div>{render_completeness(bundle)}<div class="callout">Un mapping frecuente no prueba que sea el mapping correcto ni que permanezca estable en el tiempo.</div></article>')
    elif suppressed:
        columns = ", ".join(clean_text(item.get("column")) for item in suppressed)
        panels.append(
            f'<article class="card privacy-panel"><div class="privacy-icon">🔒</div><h3>Valores intencionalmente suprimidos</h3><p>{html.escape(columns)}</p><p class="muted">No se muestran categorías protegidas, compensación exacta, texto libre ni otras distribuciones restringidas.</p></article>'
        )
        panels.append(
            f'<article class="card"><div class="card-title">Evidencia segura disponible</div>{render_completeness(bundle)}<div class="callout">La observabilidad puede evaluarse de forma agregada; la prevalencia o las categorías no se publican en este reporte.</div><div class="card-title">Cómo interpretar esta página</div><ul class="bullet-list"><li>Una completitud alta indica que el campo suele estar presente en el snapshot.</li><li>No demuestra que la definición, las categorías o el propósito de uso estén aprobados.</li><li>La ausencia de frecuencias visibles es un control de privacidad, no una ausencia de datos.</li></ul><p class="small muted">{esc(report.get("privacy_note"))}</p></article>'
        )
    else:
        panels.append(
            '<article class="card privacy-panel"><div class="privacy-icon">∅</div><h3>No existe una distribución publicable</h3><p class="muted">La variable puede depender de una fuente externa, de un concepto todavía no disponible o de evidencia que no debe exponerse.</p></article>'
        )
        panels.append(
            f'<article class="card"><div class="card-title">Qué sí pudo revisarse</div>{render_completeness(bundle)}<div class="callout">La ausencia de un gráfico es una limitación de evidencia, no una señal de que la variable sea consistente.</div></article>'
        )
    while len(panels) < 2:
        panels.append('<article class="card"><p class="muted">Sin evidencia adicional publicable.</p></article>')
    content = '<div class="behavior-grid">' + "".join(panels[:2]) + "</div>"
    return slide(8, "Cómo se comporta la variable", subtitle, content)


def render_chart_gallery(
    bundle: dict[str, Any], index: int, charts: list[dict[str, str]]
) -> str:
    cards = []
    for chart in charts:
        cards.append(
            f'''<article class="card">
              <p class="chart-caption">{html.escape(chart["title"])}</p>
              <img src="{html.escape(chart["file"], quote=True)}" alt="{html.escape(chart["title"], quote=True)}" />
            </article>'''
        )
    content = '<div class="chart-gallery">' + "".join(cards) + "</div>"
    return slide(index, "Gráficos reproducibles", "Generados por el notebook con evidencia agregada congelada", content)


def metric_boxes(metrics: dict[str, Any]) -> str:
    if not metrics:
        return '<p class="muted">No se registraron métricas calculadas para esta validación.</p>'
    boxes = []
    for key, value in list(metrics.items())[:8]:
        boxes.append(f'<div class="metric-box"><span>{html.escape(str(key).replace("_", " "))}</span><b>{esc(value)}</b></div>')
    return '<div class="metric-grid">' + "".join(boxes) + "</div>"


def render_validation_story(bundle: dict[str, Any], index: int, story_index: int) -> str:
    stories = bundle["report"].get("validation_story") or []
    variable = clean_text(bundle["assessment"].get("variable"))
    if story_index >= len(stories):
        report = bundle["report"]
        content = f"""
        <div class="validation-layout">
          <article class="card privacy-panel">
            <div class="privacy-icon">🛡</div>
            <div class="question-box">¿Qué límites de gobernanza y publicación siguen vigentes?</div>
            <p>{esc(report.get('privacy_note'))}</p>
          </article>
          <article class="card">
            <div class="card-title">Condiciones que no deben perderse</div>
            <ul class="bullet-list">
              <li>El HTML muestra únicamente métricas agregadas y cohortes con al menos 30 empleados.</li>
              <li>No publica filas, IDs, nombres, correos, categorías protegidas, compensación exacta ni texto libre.</li>
              <li>La evidencia contextual ayuda a formular hipótesis, pero no eleva scores.</li>
              <li>Una validación pendiente continúa pendiente; el reporte no convierte ausencia de evidencia en un pass.</li>
            </ul>
            <div class="callout">Esta página sustituye una cuarta validación porque el plan de {html.escape(variable)} contiene sólo {len(stories)} validaciones materiales.</div>
          </article>
        </div>"""
        return slide(index, "Gobernanza, privacidad y límites", variable, content)

    item = stories[story_index]
    outcome = clean_text(item.get("outcome_label") or item.get("outcome"), "Pendiente")
    outcome_lower = outcome.casefold()
    if "cumple" in outcome_lower and "parcial" not in outcome_lower:
        outcome_class = "badge-score-good"
    elif "falla" in outcome_lower or "no cumple" in outcome_lower:
        outcome_class = "badge-score-bad"
    else:
        outcome_class = "badge-score-warn"
    sql_refs = short_text(
        ", ".join(str(value) for value in (item.get("sql_references") or []))
        or "No registrada para esta validación",
        220,
    )
    fields = ", ".join(str(value) for value in (item.get("fields") or [])) or "No documentados"
    content = f"""
    <div class="validation-layout">
      <article class="card">
        <div class="question-box">{esc(item.get('question'))}</div>
        <div class="validation-section"><h3>Por qué se evaluó</h3><p>{esc(item.get('why'))}</p></div>
        <div class="validation-section"><h3>Método</h3><p>{esc(item.get('method'))}</p></div>
        <div class="validation-section"><h3>Regla de aceptación</h3><p>{esc(item.get('acceptance_rule'))}</p></div>
        <div class="validation-section"><h3>Alcance</h3><p><strong>Campos:</strong> {html.escape(fields)}<br><strong>Población:</strong> {esc(item.get('population'))}<br><strong>Grain:</strong> {esc(item.get('grain'))}</p></div>
      </article>
      <article class="card">
        <div class="outcome-banner"><span class="badge {outcome_class}">{html.escape(outcome)}</span><strong>Resultado observado</strong></div>
        <div class="validation-section"><h3>Evidencia</h3><p>{esc(item.get('observed_evidence'))}</p></div>
        {metric_boxes(item.get('observed_metrics') or {})}
        <div class="validation-section"><h3>Interpretación</h3><p>{esc(item.get('interpretation'))}</p></div>
        <div class="validation-section"><h3>Impacto en score</h3><p>{esc(item.get('score_effect'))}</p></div>
        <div class="validation-section"><h3>Acción recomendada</h3><p>{esc(item.get('recommended_action'))}</p></div>
        <div class="validation-section"><h3>SQL agregado</h3><p class="mono small wrap-anywhere">{html.escape(sql_refs)}</p></div>
      </article>
    </div>"""
    return slide(index, f"Validación {story_index + 1}", clean_text(item.get("question")), content)


def dedupe_actions(bundle: dict[str, Any]) -> list[str]:
    candidates = []
    for row in score_rows(bundle):
        if row["score"] < 2 and row.get("recommended_action"):
            candidates.append(clean_text(row.get("recommended_action")))
    for action in bundle["decision"].get("recommended_actions") or []:
        if action:
            candidates.append(clean_text(action))
    result = []
    seen = set()
    for action in candidates:
        key = action.casefold()
        if key not in seen:
            seen.add(key)
            result.append(action)
    return result[:5]


def render_final(bundle: dict[str, Any], index: int) -> str:
    assessment = bundle["assessment"]
    result = clean_text(assessment.get("result") or bundle["decision"].get("final_result"))
    title, description = model_recommendation(result)
    actions = dedupe_actions(bundle)
    action_html = "".join(f'<div class="action-item">{html.escape(action)}</div>' for action in actions)
    if not action_html:
        action_html = '<div class="callout">No se registraron acciones adicionales; repetir las validaciones si cambia la fuente, la población o la definición.</div>'
    low_criteria = [row["criterion"] for row in score_rows(bundle) if row["score"] < 2]
    low_label = ", ".join(low_criteria) if low_criteria else "Ninguno"
    content = f"""
    <div class="final-layout">
      <article class="card recommendation-card">
        <div>{result_badge(result)}</div>
        <div class="recommendation-title">{html.escape(title)}</div>
        <div class="recommendation-sub">{html.escape(description)}</div>
        <div class="decision-callout">{html.escape(decision_message(result))}</div>
        <div class="fact-card" style="width:100%; text-align:left"><div class="fact-label">Criterios que todavía limitan la variable</div><div class="fact-value">{html.escape(low_label)}</div></div>
      </article>
      <article class="card">
        <div class="card-title">Siguientes pasos</div>
        <div class="action-list">{action_html}</div>
        <div class="callout"><strong>Regla de uso:</strong> si cambia el claim, la población, el grain, la ventana o la fuente, la evidencia debe revalidarse; este reporte no autoriza reutilización automática.</div>
      </article>
    </div>"""
    return slide(index, "Conclusión y siguientes pasos", clean_text(assessment.get("variable")), content)


def notebook_chart_groups(bundle: dict[str, Any]) -> list[list[dict[str, str]]]:
    """Split saved notebook charts into readable two-chart slides."""
    charts = notebook_charts(bundle)
    return [charts[index:index + 2] for index in range(0, len(charts), 2)]


def expected_slide_count(bundle: dict[str, Any]) -> int:
    """Return the deck size implied by frozen validations and saved charts."""
    validation_count = max(1, len(bundle["report"].get("validation_story") or []))
    return 8 + validation_count + len(notebook_chart_groups(bundle)) + 1


def build_slides(bundle: dict[str, Any]) -> list[str]:
    slides = [
        render_summary(bundle),
        render_agenda(bundle),
        render_profile(bundle),
        render_scorecard(bundle),
        render_criteria(bundle, 5, CRITERION_ORDER[:4], "Por qué: Fuente a Datos faltantes"),
        render_criteria(bundle, 6, CRITERION_ORDER[4:], "Por qué: Consistencia a Esfuerzo"),
        render_history(bundle),
        render_behavior(bundle),
    ]
    index = 9
    story_count = max(1, len(bundle["report"].get("validation_story") or []))
    for story_index in range(story_count):
        slides.append(render_validation_story(bundle, index, story_index))
        index += 1
    for charts in notebook_chart_groups(bundle):
        slides.append(render_chart_gallery(bundle, index, charts))
        index += 1
    slides.append(render_final(bundle, index))
    return slides


def nav_buttons(bundle: dict[str, Any]) -> str:
    labels = [
        "Resumen",
        "Guía",
        "Definición",
        "Scorecard",
        "Criterios 1–4",
        "Criterios 5–8",
        "Historia",
        "Comportamiento",
    ]
    story_count = max(1, len(bundle["report"].get("validation_story") or []))
    labels.extend(f"Validación {index}" for index in range(1, story_count + 1))
    labels.extend(
        f"Gráficos {index}"
        for index in range(1, len(notebook_chart_groups(bundle)) + 1)
    )
    labels.append("Conclusión")
    return "\n".join(
        f'      <button class="nav-pill{" pill-active" if index == 0 else ""}" data-slide="{index}">{index + 1}. {html.escape(label)}</button>'
        for index, label in enumerate(labels)
    )


def coverage_payload(bundle: dict[str, Any]) -> dict[str, list[Any]]:
    rows = bundle["coverage"] or []
    return {
        "dates": [row.get("snapshot_date") for row in rows],
        "coverage": [row.get("observable_coverage_percent") for row in rows],
        "missingness": [
            (100.0 - float(row.get("observable_coverage_percent")))
            if row.get("observable_coverage_percent") is not None
            else None
            for row in rows
        ],
    }


def private_chart_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    metrics = private_aggregate_metrics(bundle)
    distribution = metrics.get("distribution") or {}
    kind = clean_text(distribution.get("kind"), "")
    if not metrics or metrics.get("status") == "unavailable" or not kind:
        return {"series": []}

    if kind == "anonymized_category_yearly":
        annual = distribution.get("annual_categories") or []
        labels: list[str] = []
        for row in annual:
            for category in row.get("categories") or []:
                label = clean_text(category.get("label"), "")
                if label and label not in labels:
                    labels.append(label)
        series = []
        for label in labels:
            values = []
            custom = []
            for row in annual:
                match = next(
                    (item for item in (row.get("categories") or []) if clean_text(item.get("label"), "") == label),
                    {},
                )
                values.append(match.get("percent"))
                custom.append(match.get("count"))
            series.append(
                {
                    "name": label,
                    "x": [clean_text(row.get("fiscal_year"), "Sin FY") for row in annual],
                    "y": values,
                    "customdata": custom,
                }
            )
        return {
            "series": series,
            "title": clean_text(distribution.get("title"), "Distribución anual agregada"),
            "y_title": "Porcentaje de observaciones pobladas",
            "barmode": "group",
            "hover_suffix": "%",
        }

    categories = distribution.get("categories") or []
    labels = [clean_text(item.get("label"), "Grupo") for item in categories]
    has_percent = bool(categories) and all(item.get("percent") is not None for item in categories)
    values = [item.get("percent") if has_percent else item.get("count") for item in categories]
    return {
        "series": [
            {
                "name": clean_text(distribution.get("title"), "Métrica agregada"),
                "x": labels,
                "y": values,
                "customdata": [item.get("count") for item in categories],
            }
        ],
        "title": clean_text(distribution.get("title"), "Métrica agregada"),
        "y_title": "Porcentaje" if has_percent else "Observaciones agregadas",
        "barmode": "group",
        "hover_suffix": "%" if has_percent else "",
    }


def custom_javascript(bundle: dict[str, Any], has_chart: bool) -> str:
    payload = json.dumps(coverage_payload(bundle), ensure_ascii=False).replace("</", "<\\/")
    private_payload = json.dumps(private_chart_payload(bundle), ensure_ascii=False).replace("</", "<\\/")
    chart_code = ""
    if has_chart:
        chart_code = f"""
      var coverageData = {payload};
      var privateMetricData = {private_payload};
      function getThemeColors() {{
        var s = getComputedStyle(document.body);
        return {{
          text: s.getPropertyValue('--text-main').trim() || '#0f172a',
          muted: s.getPropertyValue('--text-muted').trim() || '#5b6478',
          accent: s.getPropertyValue('--accent').trim() || '#2457ff',
          accent2: s.getPropertyValue('--accent-2').trim() || '#3b82f6',
          border: s.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
          font: 'Aptos, Segoe UI, system-ui, sans-serif'
        }};
      }}
      function renderCoverageChart() {{
        var target = document.getElementById('coverage-chart');
        if (!target || !window.Plotly) return;
        var t = getThemeColors();
        var traces = [
          {{x: coverageData.dates, y: coverageData.coverage, name: 'Coverage', type: 'scatter', mode: 'lines+markers', line: {{color:t.accent, width:3}}, marker:{{size:4}}}},
          {{x: coverageData.dates, y: coverageData.missingness, name: 'Missingness', type: 'scatter', mode: 'lines', line: {{color:'#f59e0b', width:2, dash:'dot'}}}}
        ];
        var layout = {{
          title: {{text:'Coverage y missingness por snapshot', font:{{family:t.font,size:14,color:t.text}}, x:0.02}},
          plot_bgcolor:'rgba(0,0,0,0)', paper_bgcolor:'rgba(0,0,0,0)',
          font:{{family:t.font,color:t.text}},
          xaxis:{{gridcolor:t.border, zerolinecolor:t.border, tickfont:{{size:11,color:t.muted}}, nticks:10}},
          yaxis:{{title:'Porcentaje', range:[0,100], gridcolor:t.border, zerolinecolor:t.border, tickfont:{{size:11,color:t.muted}}}},
          legend:{{orientation:'h', x:0.02, y:1.12, font:{{size:11,color:t.text}}, bgcolor:'rgba(0,0,0,0)', bordercolor:'rgba(0,0,0,0)'}},
          margin:{{t:64,r:20,b:48,l:56}}, hovermode:'x unified'
        }};
        window.Plotly.react(target, traces, layout, {{responsive:false, displayModeBar:false}});
        var fallback = document.getElementById('coverage-fallback');
        if (fallback) fallback.style.display = 'none';
      }}
      function renderPrivateMetricsChart() {{
        var target = document.getElementById('private-metrics-chart');
        if (!target || !window.Plotly || !privateMetricData.series || !privateMetricData.series.length) return;
        var t = getThemeColors();
        var colors = [t.accent, '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', t.accent2];
        var traces = privateMetricData.series.map(function (series, index) {{
          return {{
            x: series.x,
            y: series.y,
            customdata: series.customdata,
            name: series.name,
            type: 'bar',
            marker: {{color: colors[index % colors.length]}},
            hovertemplate: '%{{x}}<br>%{{y:.2f}}' + (privateMetricData.hover_suffix || '') + '<br>N: %{{customdata:,}}<extra>%{{fullData.name}}</extra>'
          }};
        }});
        var layout = {{
          title: {{text:privateMetricData.title, font:{{family:t.font,size:14,color:t.text}}, x:0.02}},
          plot_bgcolor:'rgba(0,0,0,0)', paper_bgcolor:'rgba(0,0,0,0)',
          font:{{family:t.font,color:t.text}},
          barmode:privateMetricData.barmode || 'group',
          xaxis:{{gridcolor:t.border, zerolinecolor:t.border, tickfont:{{size:11,color:t.muted}}}},
          yaxis:{{title:privateMetricData.y_title, gridcolor:t.border, zerolinecolor:t.border, tickfont:{{size:11,color:t.muted}}, ticksuffix:privateMetricData.hover_suffix || ''}},
          legend:{{orientation:'h', x:0.02, y:1.12, font:{{size:11,color:t.text}}, bgcolor:'rgba(0,0,0,0)', bordercolor:'rgba(0,0,0,0)'}},
          margin:{{t:64,r:20,b:54,l:62}}, hovermode:'x unified'
        }};
        window.Plotly.react(target, traces, layout, {{responsive:false, displayModeBar:false}});
        var fallback = document.getElementById('private-metrics-fallback');
        if (fallback) fallback.style.display = 'none';
      }}
      function renderAllCharts() {{
        renderCoverageChart();
        renderPrivateMetricsChart();
      }}
      window.addEventListener('load', renderAllCharts);
      new MutationObserver(renderAllCharts).observe(document.body, {{attributes:true, attributeFilter:['class']}});
"""
    return f"""
  <script>
    (function () {{
      function dispatchKey(key) {{ document.dispatchEvent(new KeyboardEvent('keydown', {{key:key, bubbles:true}})); }}
      function goToSlide(index) {{
        dispatchKey('Home');
        for (var i = 0; i < index; i += 1) dispatchKey('ArrowRight');
      }}
      Array.from(document.querySelectorAll('#slide-nav [data-slide]')).forEach(function (btn) {{
        btn.addEventListener('click', function () {{ goToSlide(Number(btn.dataset.slide || 0)); }});
      }});
      var params = new URLSearchParams(window.location.search);
      var requested = Number(params.get('slide'));
      if (Number.isFinite(requested) && requested >= 0) window.addEventListener('load', function () {{ goToSlide(requested); }});
      var requestedTheme = params.get('theme');
      if (requestedTheme) {{
        window.addEventListener('load', function () {{
          var button = document.querySelector('#theme-selector [data-theme="' + requestedTheme + '"]');
          if (button) button.click();
        }});
      }}
{chart_code}
      function runLayoutAudit() {{
        if (new URLSearchParams(window.location.search).get('audit') !== '1') return;
        window.setTimeout(function () {{
          var stages = Array.from(document.querySelectorAll('.slide-stage'));
          var failures = [];
          stages.forEach(function (stage, index) {{
            var oldDisplay = stage.style.display;
            var oldTransform = stage.style.transform;
            var oldLeft = stage.style.left;
            var oldTop = stage.style.top;
            stage.style.display = 'grid'; stage.style.transform = 'none'; stage.style.left = '0'; stage.style.top = '0';
            if (stage.scrollHeight > stage.clientHeight + 2 || stage.scrollWidth > stage.clientWidth + 2) failures.push({{slide:index+1, element:'stage', scrollHeight:stage.scrollHeight, clientHeight:stage.clientHeight}});
            Array.from(stage.querySelectorAll('.card')).forEach(function (card, cardIndex) {{
              if (card.scrollHeight > card.clientHeight + 3 || card.scrollWidth > card.clientWidth + 3) failures.push({{slide:index+1, element:'card-'+(cardIndex+1), scrollHeight:card.scrollHeight, clientHeight:card.clientHeight, scrollWidth:card.scrollWidth, clientWidth:card.clientWidth}});
            }});
            stage.style.display = oldDisplay; stage.style.transform = oldTransform; stage.style.left = oldLeft; stage.style.top = oldTop;
          }});
          document.body.setAttribute('data-layout-audit', encodeURIComponent(JSON.stringify({{slideCount:stages.length, failures:failures}})));
        }}, 1200);
      }}
      window.addEventListener('load', runLayoutAudit);
    }})();
  </script>
"""


def replace_slides(template: str, slides_html: str) -> str:
    start_marker = "  <!-- ================================================================\n       SLIDE 1"
    end_marker = "  <!-- ================================================================\n       LEFT EDGE"
    start = template.index(start_marker)
    end = template.index(end_marker)
    return template[:start] + slides_html + "\n\n" + template[end:]


def replace_nav(template: str, buttons: str) -> str:
    label = '<div class="nav-label">Navigation</div>'
    start = template.index(label) + len(label)
    end = template.index("    </div>\n  </div>", start)
    return template[:start] + "\n" + buttons + "\n" + template[end:]


def build_document(bundle: dict[str, Any], template_text: str) -> str:
    assessment = bundle["assessment"]
    variable = clean_text(assessment.get("variable"))
    slides_html = "\n".join(build_slides(bundle))
    document = template_text
    document = document.replace('<html lang="en">', '<html lang="es">', 1)
    document = document.replace("<title>[Slide Title]</title>", f"<title>{html.escape(variable)} · Assessment v2</title>", 1)
    marker = "    /* 13. CONTENT-SPECIFIC STYLES — add below this line\n       ================================================================== */"
    if marker not in document:
        raise ValueError("El template no contiene el marcador de estilos específicos esperado.")
    document = document.replace(marker, marker + "\n" + CONTENT_CSS, 1)
    document = replace_slides(document, slides_html)
    document = replace_nav(document, nav_buttons(bundle))
    has_chart = bool(bundle["coverage"]) or bool(private_chart_payload(bundle).get("series"))
    if has_chart:
        document = document.replace("  </style>\n</head>", f'  </style>\n  <script src="{PLOTLY_CDN}"></script>\n</head>', 1)
    metadata = {
        "renderer": "render_variable_assessment_v2.py",
        "schema_version": 1,
        "variable": variable,
        "source_hashes": {name: sha256_file(path) for name, path in bundle["paths"].items()},
    }
    document = document.replace(
        "</body>",
        f'<script id="assessment-v2-metadata" type="application/json">{html.escape(json.dumps(metadata, ensure_ascii=False))}</script>\n{custom_javascript(bundle, has_chart)}\n</body>',
        1,
    )
    return document


def validate_document(document: str, bundle: dict[str, Any]) -> list[str]:
    errors = []
    visible_document = re.sub(r"<!--.*?-->", "", document, flags=re.DOTALL)
    if ".app-header" in document or '<div class="app-header"' in document:
        errors.append("No debe existir app-header.")
    slide_count = len(re.findall(r'class="slide-stage"', visible_document))
    nav_section_start = visible_document.index('<div class="nav-ctrl" id="slide-nav">')
    nav_section_end = visible_document.index('<div class="side-controls" id="theme-selector">')
    nav_section = visible_document[nav_section_start:nav_section_end]
    nav_count = len(
        re.findall(
            r'<button class="nav-pill(?: pill-active)?" data-slide=',
            nav_section,
        )
    )
    expected_count = expected_slide_count(bundle)
    if slide_count != expected_count:
        errors.append(
            f"Se esperaban {expected_count} slides y se encontraron {slide_count}."
        )
    if nav_count != slide_count:
        errors.append(f"Slides ({slide_count}) y nav pills ({nav_count}) no coinciden.")
    for index in range(1, expected_count + 1):
        if f'id="slide-{index}"' not in document:
            errors.append(f"Falta id slide-{index}.")
        if f'data-slide="{index - 1}"' not in document:
            errors.append(f"Falta data-slide={index - 1}.")
    for chart in notebook_charts(bundle):
        source = html.escape(chart["file"], quote=True)
        if f'src="{source}"' not in document:
            errors.append(f"Falta el grafico declarado por el notebook: {chart['file']}.")
    required = [
        "theme-light-classic",
        "theme-light-soft",
        "theme-dark-royal",
        "theme-dark-carbon",
        "localStorage.setItem('slide-studio-theme'",
        "localStorage.getItem('slide-studio-theme'",
        "querySelectorAll('.slide-stage')",
        "showSlide(0)",
        "transform-origin: top left",
        "width: 1440px",
        "height: 810px",
        "overflow: hidden",
        "Guía del reporte",
    ]
    for token in required:
        if token not in document:
            errors.append(f"Falta requisito del template: {token}")
    private_metrics = private_aggregate_metrics(bundle)
    has_private_chart = bool(private_chart_payload(bundle).get("series"))
    if bundle["coverage"] or has_private_chart:
        plotly_required = [
            PLOTLY_CDN,
            "plot_bgcolor:'rgba(0,0,0,0)'",
            "paper_bgcolor:'rgba(0,0,0,0)'",
            "responsive:false",
            "displayModeBar:false",
            "MutationObserver(renderAllCharts)",
        ]
        for token in plotly_required:
            if token not in document:
                errors.append(f"Falta requisito Plotly: {token}")
    if private_metrics:
        if private_metrics.get("audience") != "private_aggregate":
            errors.append("Las métricas privadas deben declarar audience=private_aggregate.")
        if private_metrics.get("score_recalculated") is not False:
            errors.append("Las métricas privadas no pueden recalcular scores.")
        try:
            minimum_cohort = int(private_metrics.get("minimum_cohort") or 0)
        except (TypeError, ValueError):
            minimum_cohort = 0
        if minimum_cohort < 30:
            errors.append("Las métricas privadas deben conservar cohortes mínimas de 30.")
        if private_metrics.get("status") != "unavailable" and "Cifras privadas agregadas" not in document:
            errors.append("Falta la sección de cifras privadas agregadas.")
        if has_private_chart:
            for token in ('id="private-metrics-chart"', "renderPrivateMetricsChart"):
                if token not in document:
                    errors.append(f"Falta visualización privada requerida: {token}")
    rows = score_rows(bundle)
    if len(rows) != 8:
        errors.append("La evaluación debe contener exactamente ocho criterios.")
    for row in rows:
        if CRITERION_LABELS[row["criterion_key"]] not in document:
            errors.append(f"No se renderizó el criterio {row['criterion_key']}.")
    expected_total = sum(row["score"] for row in rows)
    actual_total = int(bundle["assessment"].get("total") or expected_total)
    if expected_total != actual_total:
        errors.append(f"El total congelado ({actual_total}) no coincide con la suma de criterios ({expected_total}).")
    if "value_label" in document or "query_results" in document:
        errors.append("El HTML no debe incluir estructuras JSON crudas de distribución o resultados.")
    return errors


def output_path_for(bundle: dict[str, Any]) -> Path:
    html_files = [path for path in bundle["variable_dir"].glob("*.html") if not path.name.endswith("-v2.html")]
    if html_files:
        slug = html_files[0].stem
    else:
        slug = re.sub(r"^\d+-", "", bundle["variable_dir"].name)
    return bundle["variable_dir"] / f"{slug}-v2.html"


def render_one(bundle: dict[str, Any], template_path: Path, force: bool) -> dict[str, Any]:
    destination = output_path_for(bundle)
    if destination.exists() and not force:
        raise FileExistsError(f"Ya existe {destination}; use --force para regenerar.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, destination)
    template_text = destination.read_text(encoding="utf-8")
    document = build_document(bundle, template_text)
    errors = validate_document(document, bundle)
    if errors:
        destination.unlink(missing_ok=True)
        raise ValueError("; ".join(errors))
    destination.write_text(document, encoding="utf-8")
    return {
        "variable": bundle["assessment"].get("variable"),
        "variable_folder": bundle["variable_dir"].name,
        "report": str(destination),
        "report_sha256": sha256_file(destination),
        "slide_count": expected_slide_count(bundle),
        "source_hashes": {name: sha256_file(path) for name, path in bundle["paths"].items()},
        "validation": "pass",
    }


def validate_existing(bundle: dict[str, Any]) -> dict[str, Any]:
    destination = output_path_for(bundle)
    if not destination.is_file():
        raise FileNotFoundError(f"No existe el reporte v2: {destination}")
    errors = validate_document(destination.read_text(encoding="utf-8"), bundle)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "variable": bundle["assessment"].get("variable"),
        "variable_folder": bundle["variable_dir"].name,
        "report": str(destination),
        "report_sha256": sha256_file(destination),
        "slide_count": expected_slide_count(bundle),
        "source_hashes": {name: sha256_file(path) for name, path in bundle["paths"].items()},
        "validation": "pass",
    }


def write_manifest(run_dir: Path, template_path: Path, entries: list[dict[str, Any]]) -> Path:
    path = run_dir / "html-v2-manifest.json"
    existing: dict[str, Any] = {}
    if path.is_file():
        existing = read_json(path)
    by_folder = {
        item["variable_folder"]: item
        for item in (existing.get("reports") or [])
        if isinstance(item, dict) and item.get("variable_folder")
    }
    for entry in entries:
        relative = Path(entry["report"]).resolve().relative_to(Path.cwd().resolve())
        entry = dict(entry)
        entry["report"] = str(relative)
        by_folder[entry["variable_folder"]] = entry
    manifest = {
        "schema_version": 1,
        "run_id": run_dir.name,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "renderer": "tools/presentations/render_variable_assessment_v2.py",
        "template": str(template_path),
        "template_sha256": sha256_file(template_path),
        "source_policy": "frozen_json_plus_private_aggregate_metrics_no_score_recalculation",
        "reports": [by_folder[key] for key in sorted(by_folder)],
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir.resolve()
    template_path = resolve_template(args.template)
    variable_dirs = select_variable_dirs(run_dir, args.variables, args.all)
    if not variable_dirs:
        raise ValueError("No se seleccionaron variables.")
    entries = []
    for variable_dir in variable_dirs:
        bundle = load_bundle(variable_dir)
        entry = validate_existing(bundle) if args.validate_only else render_one(bundle, template_path, args.force)
        entries.append(entry)
        print(f"PASS {entry['variable']}: {entry['report']}")
    if args.validate_only:
        print(f"Validated reports: {len(entries)}")
        return 0
    manifest_path = write_manifest(run_dir, template_path, entries)
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # concise CLI failure with non-zero status
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
