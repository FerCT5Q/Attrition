"""Freeze presentation-safe annual comp-ratio trend evidence for V7."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "comp_ratio_annual_attrition_trend_20260917.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = ROOT / "output" / "distribution" / "json" / "comp-ratio-annual-attrition-trend-evidence-20260917.json"
MINIMUM_COHORT = 30
EXPECTED_SNAPSHOTS = 24
APPROVED_GROUPS = {"<0.8 (incl. 0)", ">=0.8"}
REQUIRED_GROUP = ">=0.8"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
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
            "presentation",
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
    rows = payload.get("rows")
    if not isinstance(rows, list) or payload.get("truncated"):
        raise ValueError("La tendencia anual debe devolver todas sus filas agregadas.")
    if any(set(row) - {"snapshot_date", "group_label", "employee_snapshot_count", "voluntary_exits", "attrition_rate_percent"} for row in rows):
        raise ValueError("La consulta devolviÃ³ una columna no permitida para presentaciÃ³n.")
    dates = sorted({str(row["snapshot_date"]) for row in rows})
    observed_groups = {str(row["group_label"]) for row in rows}
    if (
        len(dates) != EXPECTED_SNAPSHOTS
        or not observed_groups
        or not observed_groups <= APPROVED_GROUPS
        or REQUIRED_GROUP not in observed_groups
    ):
        raise ValueError("La tendencia anual no reconciliÃ³ 24 snapshots y los dos grupos aprobados.")
    for row in rows:
        if int(row["employee_snapshot_count"]) < MINIMUM_COHORT or int(row["voluntary_exits"]) < MINIMUM_COHORT:
            raise ValueError("La tendencia anual contiene una celda bajo la cohorte publicable.")
        rate = float(row["attrition_rate_percent"])
        if not 0 <= rate <= 100:
            raise ValueError("La tendencia anual contiene una tasa fuera del rango 0â€“100.")

    pooled: dict[str, dict[str, int]] = {group: {"employee_snapshot_count": 0, "voluntary_exits": 0} for group in observed_groups}
    for row in rows:
        bucket = pooled[str(row["group_label"])]
        bucket["employee_snapshot_count"] += int(row["employee_snapshot_count"])
        bucket["voluntary_exits"] += int(row["voluntary_exits"])
    output = {
        "artifact_classification": "presentation",
        "generated_on": date.today().isoformat(),
        "outcome": "pass",
        "population": "Active non-RF360 Critical Tech employee snapshots, excluding Other Eng",
        "grain": "employee_snapshot",
        "outcome_contract": "strict term_type='VOLUNTARY' in (snapshot_date, snapshot_date + 12 months]",
        "history": {"snapshot_count": len(dates), "first_snapshot_date": dates[0], "last_snapshot_date": dates[-1]},
        "minimum_cohort": MINIMUM_COHORT,
        "groups": [
            {
                "group_label": group,
                "employee_snapshot_count": values["employee_snapshot_count"],
                "voluntary_exits": values["voluntary_exits"],
                "attrition_rate_percent": round(100 * values["voluntary_exits"] / values["employee_snapshot_count"], 4),
            }
            for group, values in sorted(pooled.items())
        ],
        "rows": rows,
        "suppressed_groups": sorted(APPROVED_GROUPS - observed_groups),
        "acceptance_rule": "24 complete annual-follow-up snapshots; every displayed point has n >= 30 and >=30 voluntary outcomes. A group with no publishable annual points is removed rather than rendered as zero.",
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": sha256(QUERY),
        "result_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{OUT}\nrows={len(rows)}; snapshots={len(dates)}")


if __name__ == "__main__":
    main()
