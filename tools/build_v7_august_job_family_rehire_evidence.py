"""Materialize reproducible August-cutoff evidence for two V7 visuals.

The queries return aggregate results only. Employee IDs remain inside Redshift
for deduplication and cohort/outcome joins and are never written to evidence.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
REHIRE_QUERY = ROOT / "queries" / "audits" / "v7_rehire_august_trailing_12m_attrition_20260921.sql"
JOB_FAMILY_QUERY = ROOT / "queries" / "audits" / "v7_job_family_august_snapshot_20260921.sql"
REHIRE_OUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.rehire-august-trailing-12m-evidence-20260921.json"
JOB_FAMILY_OUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.job-family-august-snapshot-evidence-20260921.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def query_rows(query_path: Path, max_rows: int) -> list[dict[str, Any]]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(query_path),
            "--max-rows",
            str(max_rows),
            "--reporting-mode",
            "internal_analysis",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    payload = json.loads(completed.stdout)
    require(payload.get("truncated") is False, f"{query_path.name} aggregate output was truncated.")
    rows = payload.get("rows")
    require(isinstance(rows, list), f"{query_path.name} returned no aggregate rows.")
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_rehire_evidence() -> None:
    source_rows = query_rows(REHIRE_QUERY, max_rows=10)
    expected_years = ("2024", "2025", "2026")
    require(tuple(str(row["fiscal_year"]) for row in source_rows) == expected_years, "Rehire output must have FY2024–FY2026 in order.")

    rows = []
    for row in source_rows:
        cohort = int(row["baseline_rehire_employee_count"])
        distinct = int(row["distinct_employee_count"])
        exits = int(row["voluntary_exit_count"])
        rate = float(row["trailing_12m_voluntary_attrition_rate_percent"])
        duplicate_count = int(row["duplicate_employee_snapshot_count"])
        require(cohort >= 30 and distinct == cohort, "A Rehire August cohort is not publishable or not deduplicated.")
        require(duplicate_count == 0, "A Rehire August snapshot has duplicate employee rows.")
        require(0 <= exits <= cohort, "A Rehire outcome count is invalid.")
        require(abs(rate - (100 * exits / cohort)) < 0.00011, "A Rehire T12 rate does not reconcile.")
        rows.append(
            {
                "fiscal_year": str(row["fiscal_year"]),
                "baseline_snapshot_date": str(row["baseline_snapshot_date"]),
                "outcome_cutoff_date": str(row["outcome_cutoff_date"]),
                "outcome_window": f"({row['baseline_snapshot_date']}, {row['outcome_cutoff_date']}]",
                "baseline_rehire_employee_count": cohort,
                "distinct_employee_count": distinct,
                "voluntary_exit_count": exits,
                "trailing_12m_voluntary_attrition_rate_percent": rate,
                "publication_status": "publishable_trailing_12m",
            }
        )

    write_json(
        REHIRE_OUT,
        {
            "artifact_type": "aggregate_rehire_trailing_12m_attrition_evidence",
            "version": 7,
            "generated_on": date.today().isoformat(),
            "deliverable_mode": "internal_analysis",
            "artifact_classification": "internal_analysis",
            "purpose": "Etiquetar las tres barras recientes de Rehire con attrition voluntaria trailing 12 meses desde cada cierre fiscal de agosto.",
            "definition": {
                "concept": "Stored is_rehire flag",
                "population": "Active Regular Employees at each fiscal August closing snapshot",
                "grain": "Deduplicated employee cohort at baseline snapshot",
                "outcome": "Strict VOLUNTARY termination in (baseline_snapshot_date, outcome_cutoff_date]",
                "minimum_cohort": 30,
            },
            "query": str(REHIRE_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "query_sha256": hashlib.sha256(REHIRE_QUERY.read_bytes()).hexdigest(),
            "rows": rows,
            "acceptance_rule": "Every displayed fiscal-year cohort has n>=30, exactly one baseline row per employee, and voluntary exits / baseline cohort reconciles to the T12 rate.",
            "outcome": "pass",
        },
    )


def build_job_family_evidence() -> None:
    source_rows = query_rows(JOB_FAMILY_QUERY, max_rows=30)
    summaries = [row for row in source_rows if row["row_type"] == "summary"]
    ranked = [row for row in source_rows if row["row_type"] == "top_20"]
    require(len(summaries) == 1 and len(ranked) == 20, "Job family output must contain one summary and 20 categories.")
    summary = summaries[0]
    snapshot = str(summary["snapshot_date"])
    active = int(summary["active_regular_employees"])
    observable = int(summary["observable_employees"])
    top_count = int(summary["top_20_employee_count"])
    other_count = int(summary["other_job_families_employee_count"])
    require(snapshot == "2026-08-23", "Job family snapshot must be the August fiscal close.")
    require(int(summary["duplicate_employee_rows"]) == 0, "Job family snapshot has duplicate employee rows.")
    require(active == observable, "Job family has unobservable active employees.")
    require(int(summary["top_20_category_count"]) == 20, "Job family must retain exactly 20 detailed categories.")
    require(top_count + other_count == observable, "Job family Top 20 + Other does not reconcile.")
    require(int(summary["top_20_min_employee_count"]) >= 30 and other_count >= 30, "A Job family display category is below n=30.")

    top_20 = []
    for expected_rank, row in enumerate(ranked, start=1):
        rank = int(row["category_rank"])
        count = int(row["employee_count"])
        require(rank == expected_rank and count >= 30, "Job family ranks or cohorts are invalid.")
        top_20.append({"rank": rank, "label": str(row["category_label"]), "employee_count": count})

    write_json(
        JOB_FAMILY_OUT,
        {
            "artifact_type": "aggregate_job_family_snapshot_evidence",
            "version": 7,
            "generated_on": date.today().isoformat(),
            "deliverable_mode": "internal_analysis",
            "artifact_classification": "internal_analysis",
            "purpose": "Renderizar una sola distribución de Job family al cierre fiscal de agosto de 2026, sin comparación con un snapshot de septiembre.",
            "definition": {
                "concept": "Stored HRDA job_family",
                "population": "Active Regular Employees at the fiscal August closing snapshot",
                "grain": "Distinct employee snapshot",
                "minimum_cohort": 30,
            },
            "query": str(JOB_FAMILY_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "query_sha256": hashlib.sha256(JOB_FAMILY_QUERY.read_bytes()).hexdigest(),
            "snapshot": {
                "snapshot_date": snapshot,
                "active_regular_employee_count": active,
                "observable_employee_count": observable,
                "top_20_employee_count": top_count,
                "other_job_families_employee_count": other_count,
                "top_20_min_employee_count": int(summary["top_20_min_employee_count"]),
            },
            "top_20": top_20,
            "acceptance_rule": "Exactly one active-Regular row per employee; all active employees have a nonblank job_family; each Top-20 and Other category has n>=30; Top 20 + Other reconciles to the observable population.",
            "outcome": "pass",
        },
    )


def main() -> None:
    build_rehire_evidence()
    build_job_family_evidence()
    print(REHIRE_OUT)
    print(JOB_FAMILY_OUT)


if __name__ == "__main__":
    main()
