"""Build the frozen aggregate evidence used by the V3 distribution deck.

This is deliberately a thin wrapper around the guarded read-only Redshift
helper.  It never connects with ad-hoc credentials, never requests employee
rows, and persists only the aggregated response that the helper permits.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "profiles" / "attrition_v3_six_month_segment_rates_20260914.sql"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
OUT = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v3.six-month-attrition-evidence-20260914.json"


def suppress_restricted_work_arrangement_categories(rows: list[dict]) -> list[dict]:
    """Pool medical/caregiving/leave categories before an artifact is persisted."""
    public_rows: list[dict] = []
    restricted_rows: list[dict] = []
    for row in rows:
        category = str(row.get("category", ""))
        if str(row.get("metric")) == "work_arrangement" and re.search(
            r"medical|caregiv|\bloa\b", category, flags=re.IGNORECASE
        ):
            restricted_rows.append(row)
        else:
            public_rows.append(row)
    if not restricted_rows:
        return public_rows

    exposure = sum(int(row["employee_snapshot_count"]) for row in restricted_rows)
    exits = sum(int(row["voluntary_exits"]) for row in restricted_rows)
    baseline = float(restricted_rows[0]["baseline_rate_percent"])
    public_rows.append(
        {
            "metric": "work_arrangement",
            "category": "Restricted arrangement categories",
            "first_snapshot_date": min(str(row["first_snapshot_date"]) for row in restricted_rows),
            "last_snapshot_date": max(str(row["last_snapshot_date"]) for row in restricted_rows),
            # The V3 card does not show a person count; this conservative sum is
            # solely a cohort gate after the raw category labels are removed.
            "employee_count": sum(int(row["employee_count"]) for row in restricted_rows),
            "employee_snapshot_count": exposure,
            "voluntary_exits": exits,
            "attrition_rate_percent": round(100.0 * exits / exposure, 4),
            "baseline_employee_snapshots": restricted_rows[0]["baseline_employee_snapshots"],
            "baseline_voluntary_exits": restricted_rows[0]["baseline_voluntary_exits"],
            "baseline_rate_percent": restricted_rows[0]["baseline_rate_percent"],
            "lift_vs_baseline": round((100.0 * exits / exposure) / baseline, 4) if baseline else 0.0,
        }
    )
    return public_rows


def build_evidence(rows: list[dict], columns: list[str] | None, provenance: str) -> dict:
    rows = suppress_restricted_work_arrangement_categories(rows)
    required = {
        "metric",
        "category",
        "employee_count",
        "employee_snapshot_count",
        "voluntary_exits",
        "attrition_rate_percent",
        "baseline_rate_percent",
        "lift_vs_baseline",
    }
    if not all(required <= set(row) for row in rows if isinstance(row, dict)):
        raise ValueError("La evidencia de V3 no contiene el contrato agregado requerido.")
    if any(
        int(row["employee_count"]) < 30
        or int(row["employee_snapshot_count"]) < 30
        or int(row["voluntary_exits"]) < 30
        for row in rows
    ):
        raise ValueError("La evidencia contiene una cohorte o un conteo de eventos bajo el mínimo publicable.")

    return {
        "artifact_type": "aggregate_segment_attrition_evidence",
        "version": 3,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "internal_analysis",
        "purpose": (
            "Comparar distribuciones vigentes con tasa histórica de attrition voluntario "
            "a seis meses por categoría; no genera predicciones o scores individuales."
        ),
        "outcome_contract": {
            "population": "worker_type='Employee' AND employee_type='Regular' AND active_status=1",
            "grain": "employee_snapshot",
            "target": "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 6 months]",
            "excluded": ["Voluntary Exception", "null/ambiguous termination type", "involuntary terms"],
            "history": "latest 24 complete monthly six-month follow-up snapshots",
            "minimum_cohort": 30,
        },
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": hashlib.sha256(QUERY.read_bytes()).hexdigest(),
        "columns": columns,
        "row_count": len(rows),
        "metrics": sorted({str(row["metric"]) for row in rows}),
        "rows": rows,
        "publication_rule": (
            "Sólo se emiten categorías con >=30 empleados distintos, >=30 exposiciones "
            "empleado-snapshot y >=30 salidas Voluntary. Las categorías protegidas se usan "
            "exclusivamente en internal_analysis."
        ),
        "restricted_category_policy": "Las categorías sensibles de modalidad se agrupan antes de persistir o renderizar.",
        "provenance": provenance,
        "no_estimate_policy": (
            "Una variable sin fuente, definición o join temporal aprobado se etiqueta "
            "'Attrition no estimable'; no se sustituye con un proxy."
        ),
        "outcome": "pass",
    }


def write_evidence(evidence: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    print(f"aggregate_rows={evidence['row_count']}; metrics={len(evidence['metrics'])}")


def main(sanitize_existing: bool = False) -> None:
    if not QUERY.exists() or not HELPER.exists():
        raise FileNotFoundError("La consulta o el helper read-only no existen.")

    if sanitize_existing:
        if not OUT.exists():
            raise FileNotFoundError("No existe evidencia previa para sanitizar.")
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        rows = previous.get("rows")
        if not isinstance(rows, list):
            raise ValueError("La evidencia previa no contiene filas agregadas.")
        write_evidence(build_evidence(rows, previous.get("columns"), "aggregate_republication_after_restricted_category_pooling"))
        return

    result = subprocess.run(
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
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    payload = json.loads(result.stdout)
    rows = payload.get("rows")
    if not isinstance(rows, list) or payload.get("truncated"):
        raise ValueError("La consulta de V3 debe devolver todas las filas agregadas sin truncar.")
    write_evidence(build_evidence(rows, payload.get("columns"), "fresh_guarded_readonly_query"))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Congela evidencia agregada V3 de attrition.")
    parser.add_argument("--sanitize-existing", action="store_true")
    arguments = parser.parse_args()
    main(sanitize_existing=arguments.sanitize_existing)
