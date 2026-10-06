"""Grupos de mayor riesgo con el modelo B y los cortes del playbook (2026-10-03).

Para el slide 6: en lugar del árbol, combinaciones fijas declaradas antes de
correr (no se eligen mirando resultados):

- antigüedad del playbook (<1, 1-2, 2-3, 3-5, 5-10, 10+)
- salidas en su equipo en 12 meses (con / sin)
- tiene reportes directos (sí / no)

Riesgo estimado a seis meses con el modelo B (vigente con cortes del playbook
+ tiempo desde la última promoción + recontratación) ajustado en toda la
historia, sobre la última foto. Sólo combinaciones con >= 300 personas; el
observado del último fold sólo con >= 30 salidas. Se ordenan por riesgo
estimado y se publica el top 5 con la parte de la población y de las salidas
esperadas que concentra; las demás quedan en el JSON como referencia.

Reutiliza la carga en memoria y las correcciones de
``engineering_playbook_tenure_confirmation``. Sólo se escriben agregados.
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
import engineering_feature_block_selection as fs  # noqa: E402
import engineering_hazard_adjustment as adj  # noqa: E402
import engineering_playbook_tenure_confirmation as cf  # noqa: E402  (penalización fija y ajustes no finitos)

pm = cf.pm
ROOT = hz.ROOT
DEFAULT_OUTPUT = ROOT / "output" / "analysis" / "engineering" / "20261003" / "playbook-top-risk-groups-v1"
CONFIRMATION = ROOT / "output" / "analysis" / "engineering" / "20261003" / "playbook-tenure-confirmation-v1" / "confirmation-results.json"
TENURE = "tenure_playbook_band"
MIN_GROUP_PEOPLE = 300
TOP = 5
KEYS = ["antiguedad", "salidas_equipo", "reportes"]


def group_keys(frame: pd.DataFrame) -> pd.DataFrame:
    exits = frame["team_exits_12m"].astype(str)
    reports = frame["direct_reports_band"].astype(str)
    return pd.DataFrame(
        {
            "antiguedad": frame[TENURE].astype(str),
            "salidas_equipo": np.select([exits == "0", exits == "(unknown)"], ["sin salidas", "sin dato"], "con salidas"),
            "reportes": np.select([reports == "0", reports == "(unknown)"], ["sin reportes", "sin dato"], "con reportes"),
        },
        index=frame.index,
    )


def build_groups(spec: dict) -> dict:
    monthly, direct = spec["frames"]
    l2 = spec["folds"][-1]["metrics"]["l2"]
    model = adj.fit_converged(monthly, spec["features"], l2, pm.TREND, pm.RECALIBRATION_MONTHS)
    latest = monthly["snapshot_date"].max()
    current = monthly.loc[monthly["snapshot_date"] == latest].reset_index(drop=True)
    risk = hz.six_month_predictions(model, current)
    people = current["exposure_count"].to_numpy(dtype=float)
    now = group_keys(current).assign(people=people, expected=risk * people)
    now = now.groupby(KEYS, as_index=False)[["people", "expected"]].sum()

    fold = spec["folds"][-1]
    test = fold["test"]
    snapshots = test["snapshot_date"].nunique()
    past = group_keys(test).assign(
        exposure=test["exposure_count"].to_numpy(dtype=float),
        events=test["event_count"].to_numpy(dtype=float),
        pred=fold["predictions"] * test["exposure_count"].to_numpy(dtype=float),
    )
    past = past.groupby(KEYS, as_index=False)[["exposure", "events", "pred"]].sum()
    table = now.merge(past, on=KEYS, how="left")

    total_people, total_expected = float(now["people"].sum()), float(now["expected"].sum())
    total_events = float(past["events"].sum())
    mean = total_expected / total_people
    rows = []
    for _, r in table.iterrows():
        if r["people"] < MIN_GROUP_PEOPLE:
            continue
        item = {
            "antiguedad": r["antiguedad"],
            "salidas_equipo": r["salidas_equipo"],
            "reportes": r["reportes"],
            "people": int(round(r["people"])),
            "people_share_percent": round(100.0 * r["people"] / total_people, 2),
            "predicted_6m_percent": round(100.0 * r["expected"] / r["people"], 3),
            "lift_vs_mean": round(float(r["expected"] / r["people"] / mean), 3),
            "expected_exits_share_percent": round(100.0 * r["expected"] / total_expected, 2),
        }
        if pd.notna(r["exposure"]) and r["exposure"] > 0:
            item["last_fold_people_per_snapshot"] = int(round(r["exposure"] / snapshots))
            item["last_fold_predicted_percent"] = round(100.0 * r["pred"] / r["exposure"], 3)
            if r["events"] >= fs.MIN_EVENTS:
                item["last_fold_events"] = int(r["events"])
                item["last_fold_observed_percent"] = round(100.0 * r["events"] / r["exposure"], 3)
                item["last_fold_observed_exits_share_percent"] = round(100.0 * r["events"] / total_events, 2)
        rows.append(item)
    rows.sort(key=lambda x: -x["predicted_6m_percent"])
    top = rows[:TOP]
    excluded_people = total_people - sum(x["people"] for x in rows)
    return {
        "snapshot": str(latest.date()),
        "people": int(round(total_people)),
        "mean_predicted_6m_percent": round(100.0 * mean, 3),
        "l2": model.l2,
        "groups_eligible": len(rows),
        "people_in_groups_below_minimum": int(round(excluded_people)),
        "top": top,
        "top_people_share_percent": round(sum(x["people_share_percent"] for x in top), 2),
        "top_expected_exits_share_percent": round(sum(x["expected_exits_share_percent"] for x in top), 2),
        "top_last_fold_observed_exits_share_percent": round(sum(x.get("last_fold_observed_exits_share_percent", 0.0) for x in top), 2),
        "all_groups": rows,
    }


def build_report(result: dict) -> str:
    g = result["groups"]
    lines = [
        "# Grupos de mayor riesgo — modelo B con cortes del playbook — Engineering",
        "",
        f"Creado: {result['created_at_utc']}. Foto {g['snapshot']}: {g['people']:,} personas, riesgo medio estimado a seis meses {g['mean_predicted_6m_percent']:.2f}%.",
        f"Combinaciones: {result['design']['combinations']}. Mínimo {MIN_GROUP_PEOPLE} personas; observado con >= {fs.MIN_EVENTS} salidas.",
        f"{g['groups_eligible']} combinaciones elegibles; {g['people_in_groups_below_minimum']:,} personas en combinaciones bajo el mínimo.",
        "",
        f"## Top {TOP}",
        "",
        "| Antigüedad | Salidas en su equipo | Reportes | Personas | % población | Riesgo 6m % | × promedio | % salidas esperadas | Último fold: estimado % | observado % |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def row(x: dict) -> str:
        observed = x.get("last_fold_observed_percent")
        return (
            f"| {x['antiguedad']} | {x['salidas_equipo']} | {x['reportes']} | {x['people']} | {x['people_share_percent']:.1f} | "
            f"{x['predicted_6m_percent']:.2f} | {x['lift_vs_mean']:.2f} | {x['expected_exits_share_percent']:.1f} | "
            f"{x.get('last_fold_predicted_percent', float('nan')):.2f} | {'—' if observed is None else f'{observed:.2f}'} |"
        )

    lines += [row(x) for x in g["top"]]
    lines += [
        "",
        f"El top {TOP} reúne el {g['top_people_share_percent']:.1f}% de las personas y el {g['top_expected_exits_share_percent']:.1f}% de las salidas esperadas "
        f"(último fold observado: {g['top_last_fold_observed_exits_share_percent']:.1f}% de las salidas).",
        "",
        "## Todas las combinaciones elegibles (referencia)",
        "",
        lines[8],
        lines[9],
    ]
    lines += [row(x) for x in g["all_groups"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output_dir = (args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"La carpeta de salida ya tiene contenido: {output_dir}")
    authorization = json.loads(fs.AUTHORIZATION.read_text(encoding="utf-8"))
    if authorization.get("status") != "approved":
        raise RuntimeError("La autorización de entrenamiento en memoria no está aprobada.")
    confirmation = json.loads(CONFIRMATION.read_text(encoding="utf-8"))
    if confirmation["final_key"] != "b":
        raise RuntimeError("El modelo final de la confirmación no es B.")

    calendar = [d for d in hz.fetch_calendar() if d >= fs.MIN_SNAPSHOT]
    monthly, direct, totals = pm.load_person_months(calendar)
    windows = fs.fold_windows(direct)
    references = pm.modal_references(direct)
    runner = pm.Runner(monthly, direct, windows, references)
    b = runner.run(cf.features_for(TENURE, cf.CAREER), TENURE, tag="B")
    published = confirmation["specs"]["b"]["summary"]
    if abs(b["summary"]["lift_at_10_percent"] / published["lift_at_10_percent"] - 1.0) >= 0.01:
        raise RuntimeError("B no se reproduce frente a la confirmación.")

    result = {
        "artifact": "engineering-playbook-top-risk-groups",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "knowledge_boundary": hz.KNOWLEDGE_BOUNDARY.strftime("%Y-%m-%d"),
        "deliverable_classification": "presentation",
        "authorization": {"path": str(fs.AUTHORIZATION.relative_to(ROOT)), "id": authorization["authorization_id"]},
        "model": {"name": confirmation["final_name"], "features": b["features"], "summary": b["summary"]},
        "design": {
            "combinations": "antigüedad del playbook × salidas en su equipo 12m (con/sin) × reportes directos (con/sin)",
            "ranking": "riesgo estimado a seis meses en la última foto, modelo B ajustado en toda la historia",
            "min_group_people": MIN_GROUP_PEOPLE,
            "min_published_events": fs.MIN_EVENTS,
            "top": TOP,
        },
        "groups": build_groups(b),
        "privacy": {
            "employee_level_rows_persisted": False,
            "employee_ids_selected": False,
            "aggregate_training_frame_persisted": False,
            "individual_scores_published": False,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "top-risk-groups-results.json"
    report_path = output_dir / "top-risk-groups-report.md"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report_path.write_text(build_report(result), encoding="utf-8")
    manifest = {
        "artifact": result["artifact"],
        "created_at_utc": result["created_at_utc"],
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "authorization": result["authorization"],
        "queries": {"calendar": str(hz.CALENDAR_QUERY.relative_to(ROOT)), "person_month_frame": str(pm.FRAME_QUERY.relative_to(ROOT))},
        "query_sha256": {"calendar": hz.sha256_file(hz.CALENDAR_QUERY), "person_month_frame": hz.sha256_file(pm.FRAME_QUERY)},
        "confirmation_source": str(CONFIRMATION.relative_to(ROOT)),
        "confirmation_source_sha256": hz.sha256_file(CONFIRMATION),
        "result": str(result_path.relative_to(ROOT)),
        "result_sha256": hz.sha256_file(result_path),
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": hz.sha256_file(report_path),
        "employee_level_rows_persisted": False,
        "aggregate_training_frame_persisted": False,
    }
    (output_dir / "top-risk-groups-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(build_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
