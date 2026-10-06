"""Freeze aggregate-only evidence for the Engineering lower display.

The artifact is an exploratory display view.  It validates the documented CTO
organization split and its denominator, but it does not redefine
``eng_or_noneng`` or reopen the v4 assessment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
READONLY_QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
MAIN_SQL = ROOT / "queries" / "audits" / "engineering_cto_org_split_display_20260911.sql"
DENOMINATOR_SQL = ROOT / "queries" / "audits" / "engineering_cto_display_denominator_reconciliation_20260911.sql"
JIM_SQL = ROOT / "queries" / "audits" / "engineering_cto_branch_diagnostic_20260911.sql"
UPPER_SQL = ROOT / "queries" / "audits" / "engineering_cto_display_upper_category_reconciliation_20260911.sql"
DEFAULT_OUTPUT = ROOT / "output" / "distribution" / "json" / "engineering-cto-org-split-display-evidence-20260911.json"
SNAPSHOT_DATE = "2026-08-23"
MINIMUM_COHORT = 30
FROZEN_UPPER_TOTAL = 50_033

MAIN_COLUMNS = [
    "snapshot_date",
    "result_type",
    "metric",
    "category",
    "employee_count",
    "percentage",
    "metric_value",
]
DENOMINATOR_COLUMNS = [
    "snapshot_date",
    "variant",
    "source_row_count",
    "distinct_employee_count",
    "duplicate_employee_count",
    "frozen_upper_chart_employee_count",
    "difference_to_frozen_upper_chart",
]
JIM_COLUMNS = ["snapshot_date", "metric", "metric_value"]
UPPER_COLUMNS = [
    "snapshot_date",
    "category",
    "current_employee_count",
    "frozen_employee_count",
    "difference_to_frozen",
    "current_total",
    "frozen_total",
    "total_difference_to_frozen",
]

REQUIRED_MAIN_METRICS = {
    "eligible_employee_count",
    "source_snapshot_row_count",
    "duplicate_source_employee_count",
    "manager_conflict_employee_count",
    "et_leader_conflict_employee_count",
    "eng_or_noneng_conflict_employee_count",
    "eng_or_noneng_observable_employee_count",
    "eng_or_noneng_missing_employee_count",
    "eng_or_noneng_category_count",
    "jim_root_present",
    "baaziz_root_present",
    "jim_hierarchy_member_count",
    "jim_descendant_path_count",
    "jim_cycle_count",
    "jim_maximum_depth",
    "jim_duplicate_member_count",
    "duplicate_branch_membership_count",
    "branch_overlap_count",
    "jim_depth_limit_count",
    "jim_leader_in_cto_branch_count",
    "baaziz_leader_in_cto_branch_count",
    "jim_leader_in_eligible_cto_count",
    "baaziz_leader_in_eligible_cto_count",
    "baaziz_et_member_count",
    "jim_branch_count",
    "baaziz_branch_count",
    "cto_employee_count",
    "category_total_count",
    "category_reconciliation_difference",
    "categories_below_minimum_count",
    "minimum_category_count",
    "category_percentage_sum",
    "eng_or_noneng_denominator_difference",
}

REQUIRED_JIM_METRICS = {
    "active_regular_employee_count",
    "active_regular_manager_null_employee_count",
    "active_regular_rf360_zero_employee_count",
    "baaziz_et_member_active_count",
    "baaziz_et_member_regular_count",
    "baaziz_root_active_count",
    "baaziz_root_in_active_cto_count",
    "baaziz_root_present_count",
    "jim_baaziz_branch_overlap_count",
    "jim_cycle_row_count",
    "jim_depth_limit_employee_count",
    "jim_descendant_active_count",
    "jim_descendant_regular_count",
    "jim_direct_report_active_count",
    "jim_direct_report_regular_count",
    "jim_duplicate_path_employee_count",
    "jim_et_leader_active_count",
    "jim_et_leader_regular_count",
    "jim_reachable_active_count",
    "jim_reachable_regular_count",
    "jim_root_active_count",
    "jim_root_in_active_cto_count",
    "jim_root_present_count",
    "regular_duplicate_employee_count",
    "regular_employee_count",
    "regular_manager_conflict_employee_count",
    "regular_manager_null_employee_count",
}


def public_aggregate_key(key: object) -> str:
    """Replace internal leader labels before persisting aggregate evidence."""
    text = str(key)
    for old, new in (
        ("jim_baaziz_", "leader_a_leader_b_"),
        ("jim_", "leader_a_"),
        ("baaziz_", "leader_b_"),
    ):
        text = text.replace(old, new)
    return text


def public_aggregate_value(value: object) -> object:
    """Anonymize internal leader labels in nested aggregate dictionaries."""
    if isinstance(value, dict):
        return {public_aggregate_key(key): public_aggregate_value(nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [public_aggregate_value(nested) for nested in value]
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def numeric(value: object, label: str) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"La métrica {label!r} no es numérica.") from exc


def integer(value: object, label: str) -> int:
    parsed = numeric(value, label)
    if not parsed.is_integer():
        raise ValueError(f"La métrica {label!r} debe ser entera.")
    return int(parsed)


def run_query(sql_path: Path) -> tuple[dict[str, Any], str, str]:
    if not sql_path.exists():
        raise FileNotFoundError(sql_path)
    if not READONLY_QUERY_HELPER.exists():
        raise FileNotFoundError(READONLY_QUERY_HELPER)
    command = [
        sys.executable,
        "-B",
        str(READONLY_QUERY_HELPER),
        "--sql-file",
        str(sql_path.relative_to(ROOT)),
        "--max-rows",
        "100",
        "--reporting-mode",
        "internal_analysis",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"El helper no devolvió JSON válido para {sql_path.name}.") from exc
    if not isinstance(result, dict) or not isinstance(result.get("rows"), list):
        raise ValueError(f"El helper devolvió un contrato inválido para {sql_path.name}.")
    if result.get("truncated"):
        raise ValueError(f"El resultado agregado de {sql_path.name} fue truncado.")
    sql_hash = sha256_bytes(sql_path.read_bytes())
    result_hash = sha256_bytes(canonical_json(result["rows"]))
    return result, sql_hash, result_hash


def check_columns(result: dict[str, Any], expected: list[str], label: str) -> list[dict[str, Any]]:
    if result.get("columns") != expected:
        raise ValueError(f"{label}: columnas inesperadas; se esperaban {expected!r}.")
    rows = result.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{label}: no devolvió filas agregadas.")
    return rows


def parse_main(result: dict[str, Any]) -> tuple[dict[str, int | float], list[dict[str, int | float | str]]]:
    rows = check_columns(result, MAIN_COLUMNS, "Auditoría CTO")
    metrics: dict[str, int | float] = {}
    categories: list[dict[str, int | float | str]] = []
    for row in rows:
        if str(row.get("snapshot_date")) != SNAPSHOT_DATE:
            raise ValueError("Auditoría CTO: snapshot distinto de 2026-08-23.")
        row_type = str(row.get("result_type"))
        if row_type == "metric":
            metric = str(row.get("metric"))
            if metric in metrics or row.get("category") is not None or row.get("employee_count") is not None:
                raise ValueError(f"Auditoría CTO: métrica inválida o duplicada {metric!r}.")
            value = numeric(row.get("metric_value"), metric)
            metrics[metric] = int(value) if value.is_integer() else value
        elif row_type == "category":
            category = str(row.get("category"))
            if row.get("metric") is not None or row.get("metric_value") is not None:
                raise ValueError("Auditoría CTO: fila de categoría con columnas de métrica.")
            categories.append(
                {
                    "category": category,
                    "employee_count": integer(row.get("employee_count"), f"category:{category}"),
                    "percentage": numeric(row.get("percentage"), f"percentage:{category}"),
                }
            )
        else:
            raise ValueError(f"Auditoría CTO: result_type no soportado {row_type!r}.")
    if set(metrics) != REQUIRED_MAIN_METRICS:
        raise ValueError(
            f"Auditoría CTO: contrato de métricas inválido; missing={sorted(REQUIRED_MAIN_METRICS - set(metrics))}, "
            f"extra={sorted(set(metrics) - REQUIRED_MAIN_METRICS)}."
        )
    if [row["category"] for row in categories] != ["CTO", "Corp Fxn & BU"]:
        raise ValueError("Auditoría CTO: las categorías no coinciden con el contrato visible.")
    return metrics, categories


def parse_metric_audit(result: dict[str, Any], label: str, required: set[str]) -> dict[str, int]:
    rows = check_columns(result, JIM_COLUMNS, label)
    metrics: dict[str, int] = {}
    for row in rows:
        if str(row.get("snapshot_date")) != SNAPSHOT_DATE:
            raise ValueError(f"{label}: snapshot distinto de 2026-08-23.")
        metric = str(row.get("metric"))
        if metric in metrics:
            raise ValueError(f"{label}: métrica duplicada {metric!r}.")
        metrics[metric] = integer(row.get("metric_value"), metric)
    missing = required - set(metrics)
    extra = set(metrics) - required
    if missing or extra:
        raise ValueError(f"{label}: contrato inválido; missing={sorted(missing)}, extra={sorted(extra)}.")
    return metrics


def parse_denominator(result: dict[str, Any]) -> list[dict[str, int | str]]:
    rows = check_columns(result, DENOMINATOR_COLUMNS, "Reconciliación de denominador")
    parsed: list[dict[str, int | str]] = []
    variants: set[str] = set()
    for row in rows:
        if str(row.get("snapshot_date")) != SNAPSHOT_DATE:
            raise ValueError("Reconciliación de denominador: snapshot distinto de 2026-08-23.")
        variant = str(row.get("variant"))
        if variant in variants:
            raise ValueError(f"Reconciliación de denominador: variante duplicada {variant!r}.")
        variants.add(variant)
        parsed.append(
            {
                "variant": variant,
                "source_row_count": integer(row.get("source_row_count"), f"{variant}:source_rows"),
                "distinct_employee_count": integer(row.get("distinct_employee_count"), f"{variant}:distinct"),
                "duplicate_employee_count": integer(row.get("duplicate_employee_count"), f"{variant}:duplicates"),
                "frozen_upper_chart_employee_count": integer(
                    row.get("frozen_upper_chart_employee_count"), f"{variant}:frozen_upper"
                ),
                "difference_to_frozen_upper_chart": integer(
                    row.get("difference_to_frozen_upper_chart"), f"{variant}:difference"
                ),
            }
        )
    required_variants = {
        "active_regular_no_rf_filter",
        "active_regular_no_rf_filter_eng_observable",
        "active_regular_rf360_zero",
    }
    if not required_variants.issubset(variants):
        raise ValueError(f"Reconciliación de denominador: faltan variantes {sorted(required_variants - variants)}.")
    return parsed


def parse_upper(result: dict[str, Any]) -> list[dict[str, int | str]]:
    rows = check_columns(result, UPPER_COLUMNS, "Reconciliación del gráfico superior")
    parsed: list[dict[str, int | str]] = []
    categories: set[str] = set()
    for row in rows:
        if str(row.get("snapshot_date")) != SNAPSHOT_DATE:
            raise ValueError("Reconciliación superior: snapshot distinto de 2026-08-23.")
        category = str(row.get("category"))
        if category in categories:
            raise ValueError(f"Reconciliación superior: categoría duplicada {category!r}.")
        categories.add(category)
        parsed.append(
            {
                "category": category,
                "current_employee_count": integer(row.get("current_employee_count"), f"{category}:current"),
                "frozen_employee_count": integer(row.get("frozen_employee_count"), f"{category}:frozen"),
                "difference_to_frozen": integer(row.get("difference_to_frozen"), f"{category}:difference"),
                "current_total": integer(row.get("current_total"), f"{category}:current_total"),
                "frozen_total": integer(row.get("frozen_total"), f"{category}:frozen_total"),
                "total_difference_to_frozen": integer(
                    row.get("total_difference_to_frozen"), f"{category}:total_difference"
                ),
            }
        )
    if categories != {"Engineering", "Non_Engineering"}:
        raise ValueError("Reconciliación superior: categorías inesperadas.")
    return parsed


def find_variant(rows: list[dict[str, int | str]], variant: str) -> dict[str, int | str]:
    matches = [row for row in rows if row["variant"] == variant]
    if len(matches) != 1:
        raise ValueError(f"No existe una única variante {variant!r}.")
    return matches[0]


def validate(
    metrics: dict[str, int | float],
    categories: list[dict[str, int | float | str]],
    denominator: list[dict[str, int | str]],
    jim: dict[str, int],
    upper: list[dict[str, int | str]],
) -> dict[str, object]:
    category_counts = {str(row["category"]): int(row["employee_count"]) for row in categories}
    if sum(category_counts.values()) != int(metrics["eligible_employee_count"]):
        raise ValueError("CTO + Corp Fxn & BU no reconcilia con la población elegible.")
    if int(metrics["category_total_count"]) != int(metrics["eligible_employee_count"]):
        raise ValueError("La métrica category_total_count no reconcilia con el denominador.")
    if int(metrics["category_reconciliation_difference"]) != 0:
        raise ValueError("La auditoría CTO reportó una diferencia de reconciliación distinta de cero.")
    if int(metrics["categories_below_minimum_count"]) != 0 or min(category_counts.values()) < MINIMUM_COHORT:
        raise ValueError("La vista CTO contiene una cohorte menor a n=30.")
    for metric in (
        "duplicate_source_employee_count",
        "manager_conflict_employee_count",
        "et_leader_conflict_employee_count",
        "eng_or_noneng_conflict_employee_count",
        "eng_or_noneng_missing_employee_count",
        "duplicate_branch_membership_count",
        "branch_overlap_count",
        "jim_cycle_count",
        "jim_depth_limit_count",
        "jim_duplicate_member_count",
    ):
        if int(metrics[metric]) != 0:
            raise ValueError(f"La salvaguarda {metric} no es cero.")
    if int(metrics["eng_or_noneng_denominator_difference"]) != 0:
        raise ValueError("eng_or_noneng no cubre el mismo denominador actual.")
    if int(metrics["jim_root_present"]) != 1 or int(metrics["baaziz_root_present"]) != 1:
        raise ValueError("No están presentes ambos anclajes documentados de CTO.")
    if int(metrics["jim_leader_in_cto_branch_count"]) != 1 or int(metrics["baaziz_leader_in_cto_branch_count"]) != 1:
        raise ValueError("No se incluyeron ambos líderes en la regla de ramas CTO.")
    if int(metrics["baaziz_leader_in_eligible_cto_count"]) != 1:
        raise ValueError("El líder Baaziz no está incluido en la población CTO elegible.")

    current = find_variant(denominator, "active_regular_no_rf_filter")
    observable = find_variant(denominator, "active_regular_no_rf_filter_eng_observable")
    if current["duplicate_employee_count"] != 0 or observable["duplicate_employee_count"] != 0:
        raise ValueError("El denominador actual contiene empleados duplicados.")
    if current["distinct_employee_count"] != int(metrics["eligible_employee_count"]):
        raise ValueError("La auditoría de denominador no coincide con la auditoría CTO.")
    if observable["distinct_employee_count"] != current["distinct_employee_count"]:
        raise ValueError("eng_or_noneng no cubre todos los empleados del denominador actual.")
    if current["frozen_upper_chart_employee_count"] != FROZEN_UPPER_TOTAL:
        raise ValueError("La referencia del gráfico superior congelado cambió inesperadamente.")
    if current["difference_to_frozen_upper_chart"] != int(metrics["eligible_employee_count"]) - FROZEN_UPPER_TOTAL:
        raise ValueError("La diferencia contra el gráfico superior no reconcilia.")

    if any(jim[name] != 0 for name in (
        "jim_root_active_count",
        "jim_direct_report_active_count",
        "jim_descendant_active_count",
        "jim_reachable_active_count",
        "jim_cycle_row_count",
        "jim_duplicate_path_employee_count",
        "jim_depth_limit_employee_count",
        "jim_baaziz_branch_overlap_count",
    )):
        raise ValueError("La rama Jim no cumple la excepción de rama activa vacía o tiene una salvaguarda fallida.")
    if jim["jim_root_present_count"] != 1 or jim["baaziz_root_present_count"] != 1:
        raise ValueError("El diagnóstico de Jim no confirma ambos líderes documentados.")
    if jim["baaziz_root_in_active_cto_count"] != 1:
        raise ValueError("El líder Baaziz no aparece en la rama CTO activa.")
    if jim["jim_reachable_regular_count"] < 1 or jim["jim_descendant_regular_count"] < 0:
        raise ValueError("El diagnóstico de Jim no reconcilia la rama regular.")

    for row in upper:
        if row["current_total"] != int(metrics["eligible_employee_count"]):
            raise ValueError("El total actual del gráfico superior no reconcilia con el denominador CTO.")
        if row["frozen_total"] != FROZEN_UPPER_TOTAL or row["total_difference_to_frozen"] != 10:
            raise ValueError("La diferencia documentada del gráfico superior congelado cambió inesperadamente.")

    return {
        "population_reconciliation": True,
        "category_minimum_cohort": True,
        "zero_duplicate_employee_snapshot": True,
        "zero_manager_conflicts": True,
        "zero_et_leader_conflicts": True,
        "zero_eng_or_noneng_conflicts": True,
        "eng_or_noneng_same_current_denominator": True,
        "zero_cto_branch_overlap": True,
        "zero_hierarchy_cycles": True,
        "zero_hierarchy_depth_limit": True,
        "leader_a_active_branch_empty_accepted": True,
        "upper_chart_preserved_with_denominator_note": True,
    }


def build_evidence_from_results(
    main_result: dict[str, Any],
    denominator_result: dict[str, Any],
    jim_result: dict[str, Any],
    upper_result: dict[str, Any],
    provenance: dict[str, dict[str, str]],
    execution_date: str | None = None,
) -> dict[str, object]:
    metrics, categories = parse_main(main_result)
    denominator = parse_denominator(denominator_result)
    jim = parse_metric_audit(jim_result, "Diagnóstico de rama Jim", REQUIRED_JIM_METRICS)
    upper = parse_upper(upper_result)
    validations = validate(metrics, categories, denominator, jim, upper)
    evidence = {
        "artifact_type": "aggregate_display_evidence",
        "evidence_version": 1,
        "deliverable_mode": "internal_analysis",
        "variable": "Engineering organizational split",
        "semantic_type": "hierarchy",
        "publication_status": "exploratory_display_only",
        "snapshot_date": SNAPSHOT_DATE,
        "population": "worker_type='Employee'; employee_type='Regular'; active_status=1; no RF360 filter",
        "grain": "Distinct employee snapshot",
        "score_v4_change": "none",
        "rule_applied": {
            "cto": "Documented CTO branches: same-snapshot descendants of leader A plus employees with the documented et_leader value for leader B; both leader anchors are retained in the rule.",
            "leader_inclusion": "A leader contributes to the eligible display only when present in the active snapshot universe. Leader A is present in the regular snapshot but inactive, so its active branch contributes zero employees here.",
            "complement": "Corp Fxn & BU is the complement of CTO inside the same eligible snapshot universe.",
            "rf360_rule": "No is_rf360_yes_no filter is applied so the lower view uses the current eng_or_noneng display universe.",
            "upper_chart": "The upper eng_or_noneng chart remains frozen at 50,033; the lower display uses the current reconciled universe of 50,043 and states the 10-employee difference visibly.",
        },
        "category_distribution": categories,
        "metrics": public_aggregate_value(metrics),
        "leader_a_branch_diagnostic": public_aggregate_value(jim),
        "upper_chart_reconciliation": upper,
        "denominator_reconciliation": denominator,
        "validations": validations,
        "provenance": {
            "main_cto_audit": provenance["main_cto_audit"],
            "denominator_reconciliation": provenance["denominator_reconciliation"],
            "branch_diagnostic": provenance["jim_branch_diagnostic"],
            "upper_chart_reconciliation": provenance["upper_chart_reconciliation"],
        },
        "publication_rule": "Aggregate counts and percentages only; every displayed category has n >= 30; no identities, IDs, names, or employee rows are persisted.",
        "outcome": "pass",
        "generated_on": execution_date or date.today().isoformat(),
    }
    ensure_no_sensitive_keys(evidence)
    return evidence


def ensure_no_sensitive_keys(value: object) -> None:
    prohibited = {
        "employee_id",
        "manager_employee_id",
        "employee_ids",
        "name",
        "names",
        "email",
        "raw_rows",
        "rows",
    }
    prohibited_tokens = ("jim", "baaziz")
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered_key = str(key).lower()
            if lowered_key in prohibited or any(token in lowered_key for token in prohibited_tokens):
                raise ValueError(f"El artefacto intentó persistir una clave restringida: {key!r}.")
            ensure_no_sensitive_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            ensure_no_sensitive_keys(nested)


def build_evidence(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    main_result, main_sql_hash, main_result_hash = run_query(MAIN_SQL)
    denominator_result, denominator_sql_hash, denominator_result_hash = run_query(DENOMINATOR_SQL)
    jim_result, jim_sql_hash, jim_result_hash = run_query(JIM_SQL)
    upper_result, upper_sql_hash, upper_result_hash = run_query(UPPER_SQL)
    provenance = {
        "main_cto_audit": {
            "query_path": str(MAIN_SQL.relative_to(ROOT)).replace("\\", "/"),
            "sql_sha256": main_sql_hash,
            "result_sha256": main_result_hash,
        },
        "denominator_reconciliation": {
            "query_path": str(DENOMINATOR_SQL.relative_to(ROOT)).replace("\\", "/"),
            "sql_sha256": denominator_sql_hash,
            "result_sha256": denominator_result_hash,
        },
        "jim_branch_diagnostic": {
            "query_path": str(JIM_SQL.relative_to(ROOT)).replace("\\", "/"),
            "sql_sha256": jim_sql_hash,
            "result_sha256": jim_result_hash,
        },
        "upper_chart_reconciliation": {
            "query_path": str(UPPER_SQL.relative_to(ROOT)).replace("\\", "/"),
            "sql_sha256": upper_sql_hash,
            "result_sha256": upper_result_hash,
        },
    }
    evidence = build_evidence_from_results(
        main_result,
        denominator_result,
        jim_result,
        upper_result,
        provenance,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(output)
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Congela evidencia agregada del split CTO vs. Corp Fxn & BU.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build_evidence(args.output)
    print(json.dumps({
        "output": str(args.output),
        "outcome": result["outcome"],
        "categories": result["category_distribution"],
        "generated_on": result["generated_on"],
    }, ensure_ascii=False, indent=2))
