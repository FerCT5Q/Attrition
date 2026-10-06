"""Freeze aggregate FY2026 observed attrition evidence for the Rehire slide.

This is deliberately separate from the prospective 12-month Rehire evidence:
it measures realized voluntary exits during the completed fiscal year.
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
QUERY = ROOT / "queries" / "audits" / "rehire_fy2026_observed_voluntary_attrition_20260920.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.rehire-fy2026-observed-attrition-evidence-20260920.json"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_row(row: dict[str, Any]) -> None:
    if str(row.get("publication_status")) != "publishable_observed_period_rate":
        raise ValueError("FY2026 Rehire observed attrition did not meet its publication rule.")
    if int(row.get("observed_snapshot_count") or 0) < 12:
        raise ValueError("FY2026 Rehire must include all 12 observed monthly snapshots.")
    if int(row.get("employee_snapshot_count") or 0) < 30:
        raise ValueError("FY2026 Rehire has fewer than 30 employee-snapshot exposures.")
    if int(row.get("distinct_employee_count") or 0) < 30:
        raise ValueError("FY2026 Rehire has fewer than 30 distinct employees.")
    if int(row.get("voluntary_exit_count") or 0) < 0:
        raise ValueError("FY2026 Rehire has a negative voluntary-exit count.")
    headcount = float(row.get("average_monthly_rehire_headcount") or 0)
    rate = float(row.get("observed_voluntary_attrition_rate_percent") or -1)
    if headcount <= 0 or rate < 0:
        raise ValueError("FY2026 Rehire is missing a valid denominator or observed rate.")
    expected_rate = 100 * int(row["voluntary_exit_count"]) / headcount
    if abs(rate - expected_rate) > 0.0001:
        raise ValueError("FY2026 Rehire observed rate does not reconcile to exits / average monthly headcount.")


def build_evidence(row: dict[str, Any], columns: list[str] | None) -> dict[str, Any]:
    validate_row(row)
    return {
        "artifact_type": "aggregate_rehire_fy2026_observed_attrition_evidence",
        "version": 7,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "artifact_classification": "internal_analysis",
        "purpose": "Etiquetar la attrition voluntaria observada de FY2026 debajo de la barra Rehire (1) de FY2026 en la lámina 16.",
        "definition": {
            "concept": "Realized fiscal-year voluntary attrition for the Rehire (1) population",
            "population": "Active Regular Employees with is_rehire = 1 at FY2026 monthly snapshots",
            "denominator": "Average monthly active-Rehire headcount across the 12 FY2026 snapshots",
            "numerator": "Distinct employee-term-date VOLUNTARY events during FY2026 whose employee had an earlier FY2026 active-Rehire snapshot",
            "grain": "Employee-snapshot exposure for the denominator; employee-term-date for voluntary exits",
            "not_equivalent_to": "The prospective 12-month attrition target used for FY2024 and FY2025 labels",
            "minimum_cohort": 30,
        },
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": digest(QUERY),
        "columns": columns,
        "row_count": 1,
        "row": row,
        "acceptance_rule": "Publish only if FY2026 contains at least 12 observed monthly snapshots, at least 30 Rehire employee-snapshot exposures, and at least 30 distinct Rehire employees; label it observed, not prospective.",
        "outcome": "pass",
    }


def main() -> None:
    if not QUERY.exists() or not HELPER.exists():
        raise FileNotFoundError("No existe la consulta o el helper read-only requerido para Rehire FY2026.")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HELPER),
            "--sql-file",
            str(QUERY),
            "--max-rows",
            "10",
            "--reporting-mode",
            "internal_analysis",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    payload = json.loads(result.stdout)
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != 1 or payload.get("truncated"):
        raise ValueError("La consulta de Rehire FY2026 debe devolver exactamente un agregado completo.")
    evidence = build_evidence(rows[0], payload.get("columns"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
