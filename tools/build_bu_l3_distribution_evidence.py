"""Ejecuta y conserva la evidencia agregada de BU L3 para el playbook V12."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import psycopg2.extras


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries/audits/bu_l3_distribution_attrition_20261013.sql"
OUTPUT = (
    ROOT
    / "output/distribution/json/attrition-43-variable-distributions-v12-bu-l3-evidence-20261013.json"
)
HELPER = ROOT / ".codex/skills/attrition-redshift-db/scripts/run_readonly_query.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_helper():
    spec = importlib.util.spec_from_file_location("attrition_readonly_query", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decimal(value) -> Decimal:
    return Decimal(str(value))


def main() -> None:
    helper = load_helper()
    sql = helper.validate_readonly(QUERY.read_text(encoding="utf-8"))

    with helper.connect() as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(sql)
            columns = [description.name for description in cursor.description]
            rows = [dict(row) for row in cursor.fetchall()]

    restricted = sorted({column.lower() for column in columns} & helper.SENSITIVE_OUTPUT_COLUMNS)
    if restricted:
        raise RuntimeError(f"La salida contiene columnas restringidas: {', '.join(restricted)}")

    summaries = [row for row in rows if row["row_type"] == "summary"]
    categories = [row for row in rows if row["row_type"] == "category"]
    if len(summaries) != 1 or not categories:
        raise RuntimeError("La consulta no devolvio una fila summary y categorias.")
    summary = summaries[0]

    zero_quality_fields = (
        "current_duplicate_source_rows",
        "current_contradictory_cost_centers",
        "current_missing_cost_centers",
        "current_unmatched_mappings",
        "current_duplicate_valid_mappings",
        "current_multi_bu_mappings",
        "current_unknown_bu",
        "baseline_duplicate_source_rows",
        "baseline_contradictory_cost_centers",
        "baseline_missing_cost_centers",
        "baseline_unmatched_mappings",
        "baseline_duplicate_valid_mappings",
        "baseline_multi_bu_mappings",
        "baseline_unknown_bu",
    )
    failures = {field: int(summary[field]) for field in zero_quality_fields if int(summary[field]) != 0}
    if failures:
        raise RuntimeError(f"Fallo la unicidad o cobertura del mapping: {failures}")

    current_total = sum(int(row["current_employee_count"]) for row in categories)
    baseline_total = sum(int(row["baseline_employee_count"]) for row in categories)
    exit_total = sum(int(row["voluntary_exit_count"]) for row in categories)
    share_total = sum(decimal(row["current_share_percent"]) for row in categories)
    if current_total != int(summary["current_distinct_employees"]):
        raise RuntimeError("La distribucion actual no reconcilia con el denominador.")
    if baseline_total != int(summary["baseline_distinct_employees"]):
        raise RuntimeError("Las cohortes historicas no reconcilian con el baseline.")
    if exit_total != int(summary["voluntary_exit_count"]):
        raise RuntimeError("Las salidas por BU L3 no reconcilian con el total.")
    if abs(share_total - Decimal("100")) > Decimal("0.01"):
        raise RuntimeError(f"Los porcentajes no suman 100: {share_total}")

    for row in categories:
        if int(row["current_employee_count"]) < 30:
            raise RuntimeError(f"Categoria visible menor de 30: {row['category_label']}")
        if row["publication_status"] == "publishable":
            expected = (
                Decimal(100)
                * Decimal(int(row["voluntary_exit_count"]))
                / Decimal(int(row["baseline_employee_count"]))
            )
            if abs(expected - decimal(row["annual_attrition_rate_percent"])) > Decimal("0.00011"):
                raise RuntimeError(f"Tasa que no reconcilia: {row['category_label']}")
        elif row["annual_attrition_rate_percent"] is not None:
            raise RuntimeError(f"Una tasa suprimida persiste: {row['category_label']}")

    evidence = {
        "artifact_type": "bu_l3_distribution_attrition_evidence",
        "artifact_classification": "internal_analysis",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "query": {"path": relative(QUERY), "sha256": digest(QUERY)},
        "execution_date": datetime.now(timezone.utc).date().isoformat(),
        "definition": {
            "current_snapshot_date": str(summary["current_snapshot_date"]),
            "baseline_snapshot_date": str(summary["baseline_snapshot_date"]),
            "outcome_window": "(2025-08-24, 2026-08-23]",
            "population": {
                "worker_type": "Employee",
                "employee_type": "Regular",
                "active_status": 1,
                "is_rf360_yes_no": 0,
            },
            "mapping": {
                "source": "hrda.d_department.ude_bu_reporting_l3",
                "join": "post_hire_monthly_worker_dtls.cost_centerid = d_department.nk_dept_id",
                "as_of": "edw_effective_dt <= snapshot_date < edw_end_dt, with null edw_end_dt open",
            },
            "outcome": "At least one strict VOLUNTARY termination after baseline through current snapshot",
            "minimum_visible_cohort": 30,
            "minimum_events_for_rate": 30,
        },
        "acceptance_rule": {
            "duplicate_source_rows": 0,
            "contradictory_cost_centers": 0,
            "duplicate_valid_mappings": 0,
            "multi_bu_mappings": 0,
            "unmatched_mappings": 0,
            "visible_categories_n_gte": 30,
            "published_rates_events_gte": 30,
        },
        "summary": summary,
        "categories": categories,
        "checks": {
            "current_category_total": current_total,
            "baseline_category_total": baseline_total,
            "voluntary_exit_total": exit_total,
            "current_share_total_percent": str(share_total),
            "quality_zero_fields": list(zero_quality_fields),
            "outcome": "pass",
        },
        "outcome": "pass",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": relative(OUTPUT), "categories": len(categories), "outcome": "pass"}))


if __name__ == "__main__":
    main()
