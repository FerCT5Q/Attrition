"""Freeze the latest scoped V7 workforce distributions as presentation evidence.

The query is aggregate-only and intentionally contains no employee identifiers
in its result.  It is separate from the annual attrition evidence because this
artifact answers a different question: current composition at the latest
available workforce snapshot.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "v7_scoped_latest_distribution_20260917.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7.scoped-latest-distribution-evidence-20260917.json"
MINIMUM_COHORT = 30


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if not QUERY.exists() or not HELPER.exists():
        raise FileNotFoundError("Missing the saved aggregate query or guarded read-only helper.")

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
            "presentation",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())

    result = json.loads(completed.stdout)
    rows = result.get("rows")
    if result.get("truncated") or not isinstance(rows, list) or not rows:
        raise ValueError("The scoped current-distribution query did not return a complete aggregate result.")
    required = {
        "snapshot_date",
        "metric",
        "category",
        "employee_count",
        "scoped_employee_count",
        "workforce_share_percent",
    }
    if any(not required <= set(row) for row in rows):
        raise ValueError("The scoped current-distribution result does not meet its aggregate contract.")
    if any(int(row["employee_count"]) < MINIMUM_COHORT for row in rows):
        raise ValueError("The result contains a category below the presentation cohort threshold.")

    snapshot_dates = {str(row["snapshot_date"]) for row in rows}
    denominators = {int(row["scoped_employee_count"]) for row in rows}
    if len(snapshot_dates) != 1 or len(denominators) != 1:
        raise ValueError("All current-distribution rows must reconcile to one snapshot and denominator.")

    payload = {
        "artifact_classification": "presentation",
        "version": 7,
        "generated_on": date.today().isoformat(),
        "outcome": "pass",
        "population": (
            "Active Critical Tech employees: worker_type='Employee', employee_type='Regular', "
            "active_status=1, is_rf360_yes_no=0; exact Critical Tech job-family match; seg<>'Other Eng'."
        ),
        "grain": "employee at the latest monthly workforce snapshot",
        "snapshot_date": next(iter(snapshot_dates)),
        "scoped_employee_count": next(iter(denominators)),
        "minimum_cohort": MINIMUM_COHORT,
        "metrics": sorted({str(row["metric"]) for row in rows}),
        "row_count": len(rows),
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": sha256(QUERY),
        "result_sha256": hashlib.sha256(
            json.dumps(rows, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        ).hexdigest(),
        "publication_rule": "Only categories with n >= 30 are emitted. Protected gender labels are anonymized.",
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{OUT}\nrows={len(rows)}; snapshot={payload['snapshot_date']}; n={payload['scoped_employee_count']}")


if __name__ == "__main__":
    main()
