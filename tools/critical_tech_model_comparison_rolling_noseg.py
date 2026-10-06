"""Comparación rolling-origin sin segmento (``seg``) en todo Critical Tech.

Motivo: el 2026-09-01 se reasignó ``job_family`` de forma masiva. En las fotos
mensuales 2026-08-23 y 2026-09-27, 5,420 de 49,653 empleados regulares activos
(10.9%) cambiaron de ``seg`` derivado del catálogo ``hrda.critical_tech``,
mientras que la pertenencia a Critical Tech se mantuvo (<= 58 cambios).
Evidencia: ``queries/audits/critical_tech_seg_stability_job_family_reassignment_20261001.sql``.

Por eso ``seg`` no es comparable entre historia y futuro y se elimina como
feature y como filtro de alcance (``Other Eng`` dependía de ``seg``). La
población es todo Critical Tech; ``job_family`` sólo define pertenencia.

Reutiliza el diseño de ``critical_tech_model_comparison_rolling.py`` (mismos
folds, reglas de etiquetas conocidas y selección de hiperparámetros) y agrega:

- grupos nivel × antigüedad con riesgo estimado y observado del último periodo;
- curva de captura (qué parte de las salidas cae en el x% de mayor riesgo);
- riesgo por grupo para la foto más reciente con el modelo entrenado con toda
  la historia etiquetada.

Sólo se consultan y conservan agregados; los grupos publicados tienen al menos
30 personas promedio por foto y los observados al menos 30 salidas.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import critical_tech_discrete_hazard_model as hz  # noqa: E402
import critical_tech_lightgbm_challenger as ch  # noqa: E402
import critical_tech_model_comparison_rolling as ro  # noqa: E402

ROOT = hz.ROOT
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "critical-tech" / "20261001" / "model-comparison-rolling-noseg-v1"
SEG_AUDIT = ROOT / "queries" / "audits" / "critical_tech_seg_stability_job_family_reassignment_20261001.sql"
FEATURES = ["level_grouped", "company_tenure_band", "manager_change_12m", "calendar_month"]
GROUP_KEYS = ["level_grouped", "company_tenure_band"]
CELL_KEYS = ["snapshot_date", "level_grouped", "company_tenure_band", "manager_change_12m"]
SCOPE_LABEL = "Critical Tech"

# Alternativa de población: todos los ingenieros (eng_or_noneng), sin RF360.
# eng_or_noneng no cambió con la reasignación del 2026-09-01.
POPULATIONS = {
    "critical_tech": {
        "label": "Critical Tech",
        "monthly_query": hz.MONTHLY_QUERY,
        "six_month_query": hz.SIX_MONTH_QUERY,
        "description": "Critical Tech completo (incluye Other Eng); seg excluido como feature y como filtro",
        "audits": [],
        "default_output": DEFAULT_OUTPUT,
    },
    "engineering": {
        "label": "Engineering",
        "monthly_query": ROOT / "queries" / "profiles" / "engineering_model_frame_20261001.sql",
        "six_month_query": ROOT / "queries" / "profiles" / "engineering_six_month_model_frame_20261001.sql",
        "description": (
            "Employee Regular activos, sin RF360, eng_or_noneng='Engineering' en cada foto; "
            "sin catálogo critical_tech ni job family"
        ),
        "audits": [
            ROOT / "queries" / "audits" / "eng_or_noneng_scope_stability_by_snapshot_20261001.sql",
            ROOT / "queries" / "audits" / "eng_or_noneng_reassignment_flips_20261001.sql",
        ],
        "default_output": ROOT / "output" / "analysis" / "engineering" / "20261001" / "model-comparison-rolling-v1",
    },
}


def add_interactions(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["level_x_tenure"] = result["level_grouped"] + " | " + result["company_tenure_band"]
    return result


def configure() -> None:
    """Redirige los módulos reutilizados al conjunto de features sin ``seg``."""
    hz.FEATURES = FEATURES
    ch.CATEGORICAL = FEATURES
    ro.ADDITIVE = FEATURES
    ro.INTERACTION = FEATURES + ["level_x_tenure"]
    ro.add_interactions = add_interactions


def collapse_seg(raw: pd.DataFrame) -> pd.DataFrame:
    """Suma las celdas de todos los segmentos; ``seg`` queda constante."""
    data = raw.copy()
    for column in ["exposure_count", "distinct_employee_count", "event_count"]:
        data[column] = pd.to_numeric(data[column], errors="raise")
    for column in CELL_KEYS[1:]:
        data[column] = data[column].fillna("(unknown)").astype(str)
    grouped = data.groupby(CELL_KEYS, as_index=False)[
        ["exposure_count", "distinct_employee_count", "event_count"]
    ].sum()
    grouped["seg"] = SCOPE_LABEL
    return grouped


def capture_curve(frame: pd.DataFrame, predictions: np.ndarray, steps: int = 10) -> list[dict]:
    """Parte de las salidas reales que cae en el x% de personas de mayor riesgo."""
    rows = [{"people_percent": 0, "exits_percent": 0.0}]
    for step in range(1, steps + 1):
        fraction = step / steps
        lift = hz.lift_at_fraction(frame, predictions, fraction)
        rows.append({"people_percent": int(round(100 * fraction)), "exits_percent": round(100.0 * fraction * lift, 4)})
    return rows


def group_table(frame: pd.DataFrame, predictions: np.ndarray, snapshots: int) -> list[dict]:
    data = frame[GROUP_KEYS + ["exposure_count", "event_count"]].copy()
    data["_pred"] = predictions * data["exposure_count"]
    grouped = data.groupby(GROUP_KEYS, as_index=False)[["exposure_count", "event_count", "_pred"]].sum()
    total_n = float(grouped["exposure_count"].sum())
    total_events = float(grouped["event_count"].sum())
    rows = []
    for _, row in grouped.iterrows():
        exposures = float(row["exposure_count"])
        events = float(row["event_count"])
        people = exposures / snapshots
        if people < 30:
            continue
        observed = events >= 30
        rows.append(
            {
                "level_grouped": row["level_grouped"],
                "company_tenure_band": row["company_tenure_band"],
                "people_per_snapshot": int(round(people)),
                "people_share_percent": round(100.0 * exposures / total_n, 4),
                "predicted_percent": round(100.0 * float(row["_pred"]) / exposures, 4),
                "events": int(events) if observed else None,
                "exits_share_percent": round(100.0 * events / total_events, 4) if observed else None,
                "observed_percent": round(100.0 * events / exposures, 4) if observed else None,
            }
        )
    return sorted(rows, key=lambda item: item["predicted_percent"], reverse=True)


def current_groups(monthly: pd.DataFrame, l2: float) -> dict:
    """Riesgo a seis meses por grupo en la foto más reciente con etiqueta mensual."""
    model = ro.fit_hazard(monthly, ro.ADDITIVE, l2)
    latest = monthly["snapshot_date"].max()
    frame = monthly.loc[monthly["snapshot_date"] == latest].reset_index(drop=True)
    predictions = hz.six_month_predictions(model, frame)
    rows = group_table(frame, predictions, snapshots=1)
    for row in rows:
        for key in ["events", "exits_share_percent", "observed_percent"]:
            row.pop(key, None)
    return {
        "snapshot": str(latest.date()),
        "train_last_snapshot": str(latest.date()),
        "l2": l2,
        "people": int(frame["exposure_count"].sum()),
        "mean_predicted_percent": round(
            100.0 * float(np.average(predictions, weights=frame["exposure_count"])), 4
        ),
        "trend_ratio_per_year": round(float(np.exp(model.beta[1] * 12.0 / model.encoder.time_scale)), 6),
        "groups": rows,
    }


def build_report(result: dict) -> str:
    scope = result["scope"]
    lines = [
        f"# Comparación rolling-origin sin segmento ({SCOPE_LABEL})",
        "",
        f"Creado: {result['created_at_utc']}. Frontera de conocimiento: {result['knowledge_boundary']}.",
        "",
        "`seg` y `job_family` se excluyen por la reasignación de job family del 2026-09-01",
        f"({result['seg_stability']['changed_percent']:.1f}% de las personas cambió de segmento).",
        f"Población: {result['design']['population']}.",
        "",
        ro.build_report({**result, "scopes": [scope]}).split("\n", 6)[-1],
        "## Curva de captura del último periodo (hazard aditivo)",
        "",
    ]
    for point in scope["last_fold_extra"]["capture"]["hazard"]:
        lines.append(f"- {point['people_percent']}% de personas: {point['exits_percent']:.1f}% de salidas")
    lines += ["", "## Grupos del último periodo (hazard aditivo)", ""]
    lines.append("| Nivel | Antigüedad | Personas/foto | Estimado % | Observado % |")
    lines.append("|---|---|---:|---:|---:|")
    for row in scope["last_fold_extra"]["groups"]["hazard"]:
        observed = "—" if row["observed_percent"] is None else f"{row['observed_percent']:.1f}"
        lines.append(
            f"| {row['level_grouped']} | {row['company_tenure_band']} | {row['people_per_snapshot']} | "
            f"{row['predicted_percent']:.1f} | {observed} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--population", choices=sorted(POPULATIONS), default="critical_tech")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--seg-audit-json", type=Path, required=True,
                        help="Resultado JSON del SQL de estabilidad de seg ya ejecutado.")
    parser.add_argument("--drop-manager-change", action="store_true",
                        help="Excluye manager_change_12m: 97%% de las personas-mes no tiene dato.")
    args = parser.parse_args()
    global SCOPE_LABEL, FEATURES
    if args.drop_manager_change:
        FEATURES = [feature for feature in FEATURES if feature != "manager_change_12m"]
    configure()
    population = POPULATIONS[args.population]
    SCOPE_LABEL = population["label"]
    hz.MONTHLY_QUERY = population["monthly_query"]
    hz.SIX_MONTH_QUERY = population["six_month_query"]
    if args.output_dir is None:
        args.output_dir = population["default_output"]

    output_dir = (args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"La carpeta de salida ya tiene contenido: {output_dir}")

    audit_rows = json.loads(args.seg_audit_json.read_text(encoding="utf-8"))["rows"]
    total = sum(r["employees"] for r in audit_rows)
    same = sum(r["employees"] for r in audit_rows if r["seg_before"] == r["seg_after"])
    seg_stability = {
        "sql": str(SEG_AUDIT.relative_to(ROOT)),
        "sql_sha256": hz.sha256_file(SEG_AUDIT),
        "snapshots": ["2026-08-23", "2026-09-27"],
        "employees_in_both": total,
        "employees_seg_changed": total - same,
        "changed_percent": round(100.0 * (total - same) / total, 4),
        "acceptance_rule": ">=99% conserva el mismo seg",
        "outcome": "fail" if same / total < 0.99 else "pass",
        "pairs": audit_rows,
    }

    original_query = hz.run_readonly_query

    def logged_query(path: Path, max_rows: int = 1000) -> dict:
        payload = original_query(path, max_rows)
        print(f"consulta {path.name}: {len(payload.get('rows', []))} celdas", file=sys.stderr, flush=True)
        return payload

    hz.run_readonly_query = logged_query
    calendar = hz.fetch_calendar()
    monthly_raw, monthly_hash = hz.fetch_frame(hz.MONTHLY_QUERY, calendar, hz.EXPECTED_MONTHLY_COLUMNS)
    direct_dates = [value for value in calendar if value <= hz.HOLDOUT_END]
    direct_raw, direct_hash = hz.fetch_frame(hz.SIX_MONTH_QUERY, direct_dates, hz.EXPECTED_MONTHLY_COLUMNS)
    monthly = hz.prepare_frame(collapse_seg(monthly_raw))
    direct = hz.prepare_frame(collapse_seg(direct_raw), six_month=True)

    scope = ro.run_scope(f"{args.population}_noseg", monthly, direct)

    # Reconstruye el último fold para grupos y curva de captura (mismas reglas).
    dates = sorted(add_interactions(direct)["snapshot_date"].unique())
    last_start = pd.Timestamp(ro.FOLD_STARTS[-1])
    test_dates = [pd.Timestamp(d) for d in dates if d >= last_start]
    _, models = ro.run_fold(add_interactions(monthly), add_interactions(direct), test_dates)
    test = models["test"]
    snapshots = int(test["snapshot_date"].nunique())
    scope["last_fold_extra"] = {
        "test_snapshots": snapshots,
        "capture": {key: capture_curve(test, models["predictions"][key]) for key in ["hazard", "hazard_interactions", "logistic", "lightgbm"]},
        "groups": {key: group_table(test, models["predictions"][key], snapshots) for key in ["hazard", "lightgbm"]},
    }
    scope["current"] = current_groups(add_interactions(monthly), scope["folds"][-1]["chosen"]["hazard_l2"])

    import lightgbm

    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "artifact": "critical-tech-model-comparison-rolling-noseg",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": hz.KNOWLEDGE_BOUNDARY.strftime("%Y-%m-%d"),
        "deliverable_classification": "presentation",
        "seg_stability": seg_stability,
        "design": {
            "features": FEATURES,
            "interaction_terms": ["level_x_tenure"],
            "population_key": args.population,
            "population": population["description"],
            "population_audits": {
                str(path.relative_to(ROOT)): hz.sha256_file(path) for path in population["audits"]
            },
            "fold_starts": ro.FOLD_STARTS,
            "fold_snapshots": ro.FOLD_SNAPSHOTS,
            "monthly_train_rule": "snapshot < inicio de prueba",
            "six_month_train_rule": "snapshot <= inicio de prueba - 6 meses",
            "l2_grid": ro.L2_GRID,
            "lightgbm_grid": ch.LGB_GRID,
        },
        "lightgbm_version": lightgbm.__version__,
        "frame_sha256": {"monthly": monthly_hash, "six_month": direct_hash},
        "privacy": {
            "employee_level_rows_persisted": False,
            "aggregate_training_frame_persisted": False,
            "individual_scores_published": False,
            "minimum_group_people_per_snapshot": 30,
            "minimum_published_events": 30,
        },
        "scope": scope,
    }
    result_path = output_dir / "comparison-results.json"
    report_path = output_dir / "comparison-report.md"
    manifest_path = output_dir / "comparison-manifest.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    manifest = {
        "artifact": result["artifact"],
        "created_at_utc": result["created_at_utc"],
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "queries": {
            "calendar": str(hz.CALENDAR_QUERY.relative_to(ROOT)),
            "monthly_frame": str(hz.MONTHLY_QUERY.relative_to(ROOT)),
            "six_month_frame": str(hz.SIX_MONTH_QUERY.relative_to(ROOT)),
            "seg_stability": seg_stability["sql"],
        },
        "query_sha256": {
            "calendar": hz.sha256_file(hz.CALENDAR_QUERY),
            "monthly_frame": hz.sha256_file(hz.MONTHLY_QUERY),
            "six_month_frame": hz.sha256_file(hz.SIX_MONTH_QUERY),
            "seg_stability": seg_stability["sql_sha256"],
        },
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": hz.sha256_file(result_path),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": hz.sha256_file(report_path),
        "employee_level_rows_persisted": False,
        "aggregate_training_frame_persisted": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(build_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
