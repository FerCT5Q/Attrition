"""Freeze the aggregate IOS evidence for the authorized V7 internal artifact."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "ios_business_process_reason_ytd_attrition_20260917.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
AUTHORIZATION = ROOT / "config" / "attrition_v7_internal_analysis_authorization_20260917.json"
OUTPUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.ios-movement-reasons-ytd-evidence-20260917.json"

GROUPS = {
    "All eligible IOS movements": ("total", "All IOS movements"),
    "Transfer > Transfer > Reorg Department and/or Manager Change": ("reorg_manager_change", "Reorg / manager change"),
    "Transfer > Transfer > Lateral IOS": ("lateral_ios", "Lateral IOS"),
    "Transfer > Transfer > Country-to-Country Location Change": ("country_move", "Country-to-country move"),
    "Promotion > Transfer > Promo IOS": ("promo_ios", "Promo IOS"),
    "Transfer > Transfer > Immigration Parking": ("immigration_parking", "Immigration parking"),
    "Demotion > Transfer > Downlevel IOS": ("downlevel_ios", "Downlevel IOS"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_query() -> tuple[list[dict], list[str]]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(QUERY),
            "--max-rows",
            "100",
            "--reporting-mode",
            "internal_analysis",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    payload = json.loads(completed.stdout)
    if payload.get("truncated") or not isinstance(payload.get("rows"), list):
        raise ValueError("The IOS query did not return a complete aggregate result.")
    return [dict(row) for row in payload["rows"]], [str(column) for column in payload.get("columns", [])]


def main() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    rows, columns = run_query()
    if "employee_id" in {column.lower() for column in columns}:
        raise ValueError("Employee identifiers must not be persisted in IOS evidence.")
    if len(rows) != 21:
        raise ValueError(f"Expected 21 IOS group-year rows, got {len(rows)}.")

    output_rows = []
    cutoffs = {}
    for row in rows:
        group_label = str(row["group_label"])
        if group_label not in GROUPS:
            raise ValueError(f"Unexpected IOS group label: {group_label}")
        group_key, short_label = GROUPS[group_label]
        year = int(row["calendar_year"])
        cutoff_date = str(row["cutoff_date"])
        cohort_n = int(row["cohort_n"])
        attrition = row["post_event_voluntary_attrition_percent"]
        output_rows.append(
            {
                "calendar_year": year,
                "cutoff_date": cutoff_date,
                "observed_monthly_snapshots": int(row["observed_monthly_snapshots"]),
                "ytd_average_scoped_critical_tech_workforce": int(row["ytd_average_scoped_critical_tech_workforce"]),
                "group_key": group_key,
                "group_label": group_label,
                "short_label": short_label,
                "cohort_n": cohort_n,
                "workforce_share_percent": float(row["workforce_share_percent"]),
                "post_event_voluntary_attrition_percent": None if attrition is None else float(attrition),
                "publication_status": str(row["publication_status"]),
            }
        )
        cutoffs[str(year)] = {
            "cutoff_date": cutoff_date,
            "observed_monthly_snapshots": int(row["observed_monthly_snapshots"]),
            "average_scoped_critical_tech_workforce": int(row["ytd_average_scoped_critical_tech_workforce"]),
        }

    result_hash = hashlib.sha256(
        json.dumps(rows, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()
    payload = {
        "schema_version": 2,
        "evidence_type": "ios_business_process_reason_ytd_attrition",
        "executed_on": date.today().isoformat(),
        "reporting_mode": "internal_analysis",
        "deliverable_classification": "internal_analysis",
        "authorization": authorization,
        "query": {
            "path": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(QUERY),
            "result_sha256": result_hash,
            "columns": columns,
        },
        "population": "Empleados regulares activos con el último snapshot mensual activo dentro de los 45 días anteriores al evento IOS.",
        "grain": "Empleado distinto × año calendario × motivo IOS; Total deduplicado por empleado-año.",
        "comparison_window": "Enero al último snapshot mensual de agosto de cada año calendario.",
        "cutoffs": cutoffs,
        "definition": {
            "movement": "Primer evento IOS elegible por empleado, motivo y año; los motivos pueden solaparse, por lo que sus filas no suman necesariamente al Total.",
            "workforce_share": "n de la cohorte dividido entre el promedio de empleados regulares activos en los ocho snapshots mensuales YTD.",
            "attrition": "Salida con term_type exactamente Voluntary después del primer evento y hasta el snapshot de agosto del mismo año; es attrition observado YTD, no un follow-up completo de doce meses.",
        },
        "privacy": {
            "aggregate_only": True,
            "minimum_shared_cohort": 30,
            "small_cell_exception": True,
            "suppression": "No se suprimen conteos ni tasas agregadas bajo la autorización internal_analysis; una tasa con cohorte n=0 permanece Not estimable por denominador vacío.",
            "prohibited": ["employee rows", "employee IDs", "names", "emails", "addresses"],
        },
        "rows": output_rows,
        "validation": {
            "expected_years": [2024, 2025, 2026],
            "expected_groups": list(GROUPS),
            "rows": len(output_rows),
            "all_available_aggregate_counts_retained": True,
            "outcome": "pass",
        },
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)
    print(f"rows={len(output_rows)}; subthreshold={sum(row['cohort_n'] < 30 for row in output_rows)}")


if __name__ == "__main__":
    main()
