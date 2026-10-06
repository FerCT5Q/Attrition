"""Freeze aggregate evidence for the V7 IOS movement-reason slide.

Input is the JSON emitted by the guarded Redshift read-only helper.  This
script deliberately accepts only aggregate rows and writes a presentation-safe
evidence file; it never receives or persists employee-level records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "ios_business_process_reason_ytd_attrition_20260917.sql"
DEFAULT_OUTPUT = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.ios-movement-reasons-ytd-evidence-20260917.json"
)

GROUPS = (
    ("total", "All eligible IOS movements", "All IOS movements"),
    (
        "reorg_manager_change",
        "Transfer > Transfer > Reorg Department and/or Manager Change",
        "Reorg / manager change",
    ),
    ("lateral_ios", "Transfer > Transfer > Lateral IOS", "Lateral IOS"),
    (
        "country_move",
        "Transfer > Transfer > Country-to-Country Location Change",
        "Country-to-country move",
    ),
    ("promo_ios", "Promotion > Transfer > Promo IOS", "Promo IOS"),
    (
        "immigration_parking",
        "Transfer > Transfer > Immigration Parking",
        "Immigration parking",
    ),
    ("downlevel_ios", "Demotion > Transfer > Downlevel IOS", "Downlevel IOS"),
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def integer(value: Any) -> int | None:
    return None if value is None else int(float(value))


def decimal(value: Any) -> float | None:
    return None if value is None else float(value)


def load_input(path: str) -> tuple[dict[str, Any], str]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    return json.loads(raw), raw


def validate(source: dict[str, Any]) -> list[dict[str, Any]]:
    columns = source.get("columns")
    required = {
        "calendar_year",
        "cutoff_date",
        "observed_monthly_snapshots",
        "ytd_average_scoped_critical_tech_workforce",
        "group_label",
        "published_cohort_n",
        "published_percent_of_ytd_average_scoped_critical_tech_workforce",
        "published_post_event_voluntary_attrition_percent",
        "publication_status",
    }
    if not isinstance(columns, list) or not required.issubset(columns):
        raise ValueError("The read-only result does not satisfy the V7 aggregate contract.")
    if source.get("truncated"):
        raise ValueError("The read-only result was truncated.")

    rows = source.get("rows")
    if not isinstance(rows, list) or len(rows) != 21:
        raise ValueError("Expected exactly seven rows for each of the three calendar years.")

    expected_labels = {label for _, label, _ in GROUPS}
    expected_years = {2024, 2025, 2026}
    seen: set[tuple[int, str]] = set()
    rendered: list[dict[str, Any]] = []
    group_map = {label: (key, short) for key, label, short in GROUPS}
    for row in rows:
        year = integer(row.get("calendar_year"))
        label = row.get("group_label")
        if year not in expected_years or label not in expected_labels:
            raise ValueError("Unexpected period or business-process-reason label in the result.")
        key = (year, label)
        if key in seen:
            raise ValueError("The aggregate result contains duplicate year/reason rows.")
        seen.add(key)

        snapshots = integer(row.get("observed_monthly_snapshots"))
        if snapshots != 8:
            raise ValueError(f"{year} must contain eight monthly snapshots, found {snapshots}.")
        status = row.get("publication_status")
        cohort_n = integer(row.get("published_cohort_n"))
        share = decimal(row.get("published_percent_of_ytd_average_scoped_critical_tech_workforce"))
        attrition = decimal(row.get("published_post_event_voluntary_attrition_percent"))
        if status == "publish":
            if cohort_n is None or cohort_n < 30 or share is None or attrition is None:
                raise ValueError("Published rows require n >= 30 and both displayed rates.")
        elif status == "suppress: cohort below 30":
            if cohort_n is not None or share is not None or attrition is not None:
                raise ValueError("Suppressed rows must not retain display values.")
        else:
            raise ValueError("Unexpected publication status.")

        group_key, short_label = group_map[label]
        rendered.append(
            {
                "calendar_year": year,
                "cutoff_date": str(row["cutoff_date"]),
                "observed_monthly_snapshots": snapshots,
                "ytd_average_scoped_critical_tech_workforce": integer(
                    row["ytd_average_scoped_critical_tech_workforce"]
                ),
                "group_key": group_key,
                "group_label": label,
                "short_label": short_label,
                "cohort_n": cohort_n,
                "workforce_share_percent": share,
                "post_event_voluntary_attrition_percent": attrition,
                "publication_status": status,
            }
        )

    if len(seen) != len(expected_years) * len(expected_labels):
        raise ValueError("One or more required year/reason combinations are absent.")
    return sorted(rendered, key=lambda item: (item["calendar_year"], GROUPS.index(next(group for group in GROUPS if group[0] == item["group_key"]))))


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze V7 IOS movement-reason evidence from aggregate JSON.")
    parser.add_argument("--input", default="-", help="Guarded read-only query JSON path, or - for stdin.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not QUERY.exists():
        raise FileNotFoundError(f"Missing query: {QUERY}")
    source, raw_result = load_input(args.input)
    rows = validate(source)
    cutoffs = {
        str(year): {
            "cutoff_date": next(row["cutoff_date"] for row in rows if row["calendar_year"] == year),
            "observed_monthly_snapshots": 8,
            "average_scoped_critical_tech_workforce": next(
                row["ytd_average_scoped_critical_tech_workforce"]
                for row in rows
                if row["calendar_year"] == year
            ),
        }
        for year in (2024, 2025, 2026)
    }
    payload = {
        "schema_version": 1,
        "evidence_type": "ios_business_process_reason_ytd_attrition",
        "executed_on": date.today().isoformat(),
        "reporting_mode": "presentation",
        "deliverable_classification": "presentation",
        "query": {
            "path": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(QUERY.read_bytes()).hexdigest(),
            "result_sha256": sha256_text(raw_result),
        },
        "population": (
            "Empleados regulares activos con el último snapshot mensual activo dentro de "
            "los 45 días anteriores al evento IOS."
        ),
        "grain": "Empleado distinto × año calendario × motivo IOS; Total deduplicado por empleado-año.",
        "comparison_window": "Enero al último snapshot mensual de agosto de cada año calendario.",
        "cutoffs": cutoffs,
        "definition": {
            "movement": (
                "Primer evento IOS elegible por empleado, motivo y año; los motivos pueden "
                "solaparse, por lo que sus filas no suman necesariamente al Total."
            ),
            "workforce_share": (
                "n de la cohorte dividido entre el promedio de empleados regulares activos "
                "en los ocho snapshots mensuales YTD."
            ),
            "attrition": (
                "Salida con term_type exactamente Voluntary después del primer evento y hasta "
                "el snapshot de agosto del mismo año. Es attrition observado YTD, no un "
                "follow-up completo de doce meses."
            ),
        },
        "source_scope": {
            "movement_source": "hrda.workers_ios_transfers.business_process_reason",
            "workforce_source": "hrda.post_hire_monthly_worker_dtls",
            "outcome_source": "hrda.all_terminations",
            "prior_feature_caveat": (
                "Esta vista IOS no desagrega el antiguo flag rolling Transfer within the past year; "
                "la reconciliación histórica documentada conserva una coincidencia exacta por "
                "empleado-fecha de 5.7793%."
            ),
        },
        "privacy": {
            "aggregate_only": True,
            "minimum_shared_cohort": 30,
            "suppression": "Cualquier celda con n menor a 30 se entrega sin conteo ni tasas.",
            "prohibited": ["employee rows", "employee IDs", "names", "emails", "addresses"],
        },
        "rows": rows,
        "validation": {
            "expected_years": [2024, 2025, 2026],
            "expected_groups": [label for _, label, _ in GROUPS],
            "rows": len(rows),
            "outcome": "pass",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
