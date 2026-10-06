"""Freeze aggregate-only internal-analysis evidence used by V7.

The source query returns snapshot-by-bucket aggregates.  This wrapper keeps
all four bucket counts and percentages, including sub-30 buckets, under the
explicit V7 internal-analysis authorization.  No employee-level result is
persisted.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "profiles" / "application_employee_snapshot_trailing_6m_distribution_20260913.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
AUTHORIZATION = ROOT / "config" / "attrition_v7_internal_analysis_authorization_20260917.json"
OUTPUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.application-employee-snapshot-trailing-6m-internal-evidence-20260917.json"
BUCKETS = ("0", "1", "2+", "Unknown")


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
            "1000",
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
    rows = payload.get("rows")
    columns = payload.get("columns")
    if payload.get("truncated") or not isinstance(rows, list) or not rows:
        raise ValueError("The internal application profile did not return a complete aggregate result.")
    if not isinstance(columns, list) or "employee_id" in {str(column).lower() for column in columns}:
        raise ValueError("Employee identifiers must not appear in the persisted aggregate result.")
    return [dict(row) for row in rows], [str(column) for column in columns]


def normalize_row(row: dict) -> dict:
    return {
        "snapshot_date": str(row["snapshot_date"]),
        "fiscal_year": str(row["fiscal_year"]),
        "application_bucket": str(row["application_bucket"]),
        "employee_snapshots": int(row["employee_snapshots"]),
        "eligible_employee_snapshots": int(row["eligible_employee_snapshots"]),
        "observed_employee_snapshots": int(row["observed_employee_snapshots"]),
        "unknown_employee_snapshots": int(row["unknown_employee_snapshots"]),
        "percent_of_eligible_snapshots": float(row["percent_of_eligible_snapshots"]),
        "coverage_percent": float(row["coverage_percent"]),
        "unknown_percent": float(row["unknown_percent"]),
    }


def main() -> None:
    if not QUERY.exists() or not HELPER.exists() or not AUTHORIZATION.exists():
        raise FileNotFoundError("The V7 internal-analysis inputs are incomplete.")

    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    if authorization.get("reporting_mode") != "internal_analysis":
        raise ValueError("The V7 authorization must explicitly use internal_analysis.")
    if not authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets"):
        raise ValueError("The V7 authorization does not allow the requested aggregate exception.")

    rows, columns = run_query()
    normalized = [normalize_row(row) for row in rows]
    by_snapshot: dict[str, list[dict]] = {}
    for row in normalized:
        by_snapshot.setdefault(row["snapshot_date"], []).append(row)
    if len(by_snapshot) < 12:
        raise ValueError("The internal application profile has fewer than 12 monthly snapshots.")
    for snapshot_date, snapshot_rows in by_snapshot.items():
        buckets = {row["application_bucket"] for row in snapshot_rows}
        if buckets != set(BUCKETS):
            raise ValueError(f"Snapshot {snapshot_date} does not contain all four application buckets.")
        eligible = snapshot_rows[0]["eligible_employee_snapshots"]
        if sum(row["employee_snapshots"] for row in snapshot_rows) != eligible:
            raise ValueError(f"Snapshot {snapshot_date} does not reconcile to its aggregate denominator.")

    trend_dates = sorted(by_snapshot)[-12:]
    trend: list[dict] = []
    for snapshot_date in trend_dates:
        rows_by_bucket = {row["application_bucket"]: row for row in by_snapshot[snapshot_date]}
        base = rows_by_bucket["0"]
        trend.append(
            {
                "snapshot_date": snapshot_date,
                "fiscal_year": base["fiscal_year"],
                "eligible_employee_snapshots": base["eligible_employee_snapshots"],
                "observed_employee_snapshots": base["observed_employee_snapshots"],
                "unknown_employee_snapshots": base["unknown_employee_snapshots"],
                "coverage_percent": base["coverage_percent"],
                "unknown_percent": base["unknown_percent"],
                "buckets": {
                    bucket: {
                        "employee_snapshots": rows_by_bucket[bucket]["employee_snapshots"],
                        "percent_of_eligible_snapshots": rows_by_bucket[bucket]["percent_of_eligible_snapshots"],
                    }
                    for bucket in BUCKETS
                },
                "publication_status": "internal_analysis_exception",
            }
        )

    latest_date = trend[-1]["snapshot_date"]
    latest_rows = sorted(by_snapshot[latest_date], key=lambda row: BUCKETS.index(row["application_bucket"]))
    result_hash = hashlib.sha256(json.dumps(normalized, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    payload = {
        "schema_version": 1,
        "artifact": "application_employee_snapshot_trailing_6m_distribution",
        "artifact_classification": "internal_analysis",
        "generated_on": date.today().isoformat(),
        "reporting_mode": "internal_analysis",
        "authorization": authorization,
        "query": {
            "path": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(QUERY),
            "result_sha256": result_hash,
            "columns": columns,
        },
        "population": "Active regular employee-snapshots with time-safe qualified application coverage handling.",
        "grain": "employee-snapshot aggregate by application bucket",
        "window": "Six months before and including each monthly snapshot.",
        "bucket_definition": {
            "0": "zero unique requisitions with time-safe source coverage",
            "1": "one unique requisition",
            "2+": "two or more unique requisitions",
            "Unknown": "no usable qualified event observable by the snapshot",
        },
        "latest_snapshot": latest_date,
        "latest_distribution": latest_rows,
        "trend": trend,
        "privacy": {
            "aggregate_only": True,
            "small_cell_exception": True,
            "minimum_displayed_count": 0,
            "employee_rows_persisted": False,
            "employee_ids_persisted": False,
            "names_persisted": False,
            "emails_persisted": False,
        },
        "outcome": "pass",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)
    print(f"snapshots={len(trend)}; latest={latest_date}; aggregate_rows={len(normalized)}")


if __name__ == "__main__":
    main()
