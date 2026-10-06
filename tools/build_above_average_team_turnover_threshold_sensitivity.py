"""Freeze aggregate threshold sensitivity evidence for candidate 44.

The query is intentionally presentation-safe: manager-level counts are
suppressed below n=30, and no manager identifier, individual rate, or ranking
is selected or persisted.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "queries" / "audits" / "above_average_team_turnover_threshold_sensitivity_20260911.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "above-average-team-turnover-threshold-sensitivity-20260911.json"
QUERY_HELPER = ROOT / "tools" / "read_only_redshift_query_helper.py"
MINIMUM_COHORT = 30
EXPECTED_THRESHOLDS = {"1.20", "1.30", "1.40"}
EXPECTED_COLUMNS = [
    "row_type",
    "snapshot_date",
    "threshold_multiplier",
    "eligible_manager_count",
    "eligible_report_count",
    "flagged_manager_count",
    "flagged_report_count",
    "significant_manager_count",
    "significant_report_count",
    "flagged_and_significant_manager_count",
    "flagged_and_significant_report_count",
    "benchmark_six_month_rate",
    "ratio_p25",
    "ratio_p50",
    "ratio_p75",
    "ratio_p90",
    "ratio_p95",
    "avg_flagged_report_share_percent",
    "min_flagged_report_share_percent",
    "max_flagged_report_share_percent",
    "avg_flagged_report_count",
    "min_flagged_report_count",
    "max_flagged_report_count",
    "snapshots_checked",
    "snapshots_with_reportable_flagged_count",
    "interpretation",
]
FORBIDDEN_KEYS = {
    "employee_id",
    "manager_employee_id",
    "manager_name",
    "manager_rate",
    "manager_rates",
    "manager_ranking",
    "manager_rankings",
    "term_date",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_helper() -> Any:
    module_spec = importlib.util.spec_from_file_location(
        "above_average_team_turnover_threshold_sensitivity_readonly", QUERY_HELPER
    )
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el helper read-only: {QUERY_HELPER}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def execute_query(sql: str) -> list[dict[str, Any]]:
    helper = load_helper()
    guarded_sql = helper.validate_readonly(sql)
    with helper.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
        with connection.cursor(cursor_factory=helper.psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(guarded_sql)
            columns = [description.name for description in cursor.description or []]
            if columns != EXPECTED_COLUMNS:
                raise ValueError(f"El esquema de sensibilidad cambió: {columns}")
            return [dict(row) for row in cursor.fetchall()]


def integer(value: Any, label: str, *, allow_null: bool = False) -> int | None:
    if value is None and allow_null:
        return None
    if value is None:
        raise ValueError(f"Falta el conteo agregado {label}.")
    numeric = float(str(value))
    if not numeric.is_integer():
        raise ValueError(f"{label} debe ser entero.")
    return int(numeric)


def number(value: Any, label: str, *, allow_null: bool = False) -> float | None:
    if value is None and allow_null:
        return None
    if value is None:
        raise ValueError(f"Falta la métrica agregada {label}.")
    return float(str(value))


def reject_restricted_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise ValueError(f"La evidencia conserva una clave restringida: {key}")
            reject_restricted_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            reject_restricted_keys(nested)


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    """Keep only safe aggregate values from the executed result."""
    return {
        "row_type": row["row_type"],
        "snapshot_date": None if row["snapshot_date"] is None else str(row["snapshot_date"]),
        "threshold_multiplier": None if row["threshold_multiplier"] is None else str(row["threshold_multiplier"]),
        "eligible_manager_count": integer(row.get("eligible_manager_count"), "eligible_manager_count", allow_null=True),
        "eligible_report_count": integer(row.get("eligible_report_count"), "eligible_report_count", allow_null=True),
        "flagged_manager_count": integer(row.get("flagged_manager_count"), "flagged_manager_count", allow_null=True),
        "flagged_report_count": integer(row.get("flagged_report_count"), "flagged_report_count", allow_null=True),
        "significant_manager_count": integer(row.get("significant_manager_count"), "significant_manager_count", allow_null=True),
        "significant_report_count": integer(row.get("significant_report_count"), "significant_report_count", allow_null=True),
        "flagged_and_significant_manager_count": integer(
            row.get("flagged_and_significant_manager_count"),
            "flagged_and_significant_manager_count",
            allow_null=True,
        ),
        "flagged_and_significant_report_count": integer(
            row.get("flagged_and_significant_report_count"),
            "flagged_and_significant_report_count",
            allow_null=True,
        ),
        "benchmark_six_month_rate": number(row.get("benchmark_six_month_rate"), "benchmark_six_month_rate", allow_null=True),
        "ratio_p25": number(row.get("ratio_p25"), "ratio_p25", allow_null=True),
        "ratio_p50": number(row.get("ratio_p50"), "ratio_p50", allow_null=True),
        "ratio_p75": number(row.get("ratio_p75"), "ratio_p75", allow_null=True),
        "ratio_p90": number(row.get("ratio_p90"), "ratio_p90", allow_null=True),
        "ratio_p95": number(row.get("ratio_p95"), "ratio_p95", allow_null=True),
        "avg_flagged_report_share_percent": number(row.get("avg_flagged_report_share_percent"), "avg_flagged_report_share_percent", allow_null=True),
        "min_flagged_report_share_percent": number(row.get("min_flagged_report_share_percent"), "min_flagged_report_share_percent", allow_null=True),
        "max_flagged_report_share_percent": number(row.get("max_flagged_report_share_percent"), "max_flagged_report_share_percent", allow_null=True),
        "avg_flagged_report_count": number(row.get("avg_flagged_report_count"), "avg_flagged_report_count", allow_null=True),
        "min_flagged_report_count": integer(row.get("min_flagged_report_count"), "min_flagged_report_count", allow_null=True),
        "max_flagged_report_count": integer(row.get("max_flagged_report_count"), "max_flagged_report_count", allow_null=True),
        "snapshots_checked": integer(row.get("snapshots_checked"), "snapshots_checked", allow_null=True),
        "snapshots_with_reportable_flagged_count": integer(
            row.get("snapshots_with_reportable_flagged_count"),
            "snapshots_with_reportable_flagged_count",
            allow_null=True,
        ),
        "interpretation": row.get("interpretation"),
    }


def validate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    compact = [compact_row(row) for row in rows]
    distribution = [row for row in compact if row["row_type"] == "rate_distribution"]
    snapshots = [row for row in compact if row["row_type"] == "threshold_snapshot"]
    stability = [row for row in compact if row["row_type"] == "threshold_stability"]
    if len(distribution) != 1 or len(snapshots) != 18 or len(stability) != 3:
        raise ValueError("La sensibilidad no contiene 1 distribución, 18 snapshots y 3 resúmenes.")
    latest = distribution[0]
    if latest["eligible_manager_count"] is None or latest["eligible_manager_count"] < MINIMUM_COHORT:
        raise ValueError("La distribución de managers elegibles no cumple n >= 30.")
    ratios = [latest[key] for key in ("ratio_p25", "ratio_p50", "ratio_p75", "ratio_p90", "ratio_p95")]
    if any(value is None for value in ratios) or ratios != sorted(ratios):
        raise ValueError("Los percentiles de ratio no son completos u ordenados.")
    if latest["benchmark_six_month_rate"] is None or latest["benchmark_six_month_rate"] <= 0:
        raise ValueError("Falta el benchmark positivo de la distribución.")
    if {str(row["threshold_multiplier"]) for row in snapshots} != EXPECTED_THRESHOLDS:
        raise ValueError("La sensibilidad no compara exactamente 1.2, 1.3 y 1.4.")
    snapshot_dates = {str(row["snapshot_date"]) for row in snapshots}
    if len(snapshot_dates) != 6:
        raise ValueError("La sensibilidad no cubre seis snapshots distintos.")
    for row in snapshots:
        for key in ("eligible_report_count", "flagged_report_count", "significant_report_count", "flagged_and_significant_report_count"):
            value = row[key]
            if value is None or value < MINIMUM_COHORT:
                raise ValueError(f"{key} no cumple n >= {MINIMUM_COHORT} en {row['snapshot_date']}.")
        if row["significant_report_count"] != row["flagged_and_significant_report_count"]:
            raise ValueError("El screening significativo dejó de estar contenido en cada umbral.")
    for row in stability:
        if row["snapshots_checked"] != 6 or row["snapshots_with_reportable_flagged_count"] != 6:
            raise ValueError("La estabilidad no cubre seis snapshots reportables.")
        if row["avg_flagged_report_share_percent"] is None:
            raise ValueError("Falta la proporción agregada de flags.")
    evidence = {
        "artifact_type": "aggregate_threshold_sensitivity_evidence",
        "deliverable_mode": "presentation",
        "variable": "Above-average team turnover",
        "candidate_number": 44,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "query": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
        "population": "Managers elegibles y reportes directos actuales, sin identidades ni tasas individuales.",
        "grain": "Manager-snapshot agregado y reporte-snapshot agregado.",
        "thresholds_compared": [1.2, 1.3, 1.4],
        "latest_snapshot": latest["snapshot_date"],
        "rate_distribution": {
            "eligible_manager_count": latest["eligible_manager_count"],
            "benchmark_six_month_rate": latest["benchmark_six_month_rate"],
            "ratio_percentiles": {
                "p25": latest["ratio_p25"],
                "p50": latest["ratio_p50"],
                "p75": latest["ratio_p75"],
                "p90": latest["ratio_p90"],
                "p95": latest["ratio_p95"],
            },
            "interpretation": latest["interpretation"],
        },
        "latest_thresholds": [row for row in snapshots if str(row["snapshot_date"]) == str(latest["snapshot_date"])],
        "threshold_stability": stability,
        "significance_screen": {
            "method": "Límite inferior unilateral aproximado de 95% de Wilson para salidas por employee-month, expresado a seis meses y comparado con el benchmark del mismo snapshot.",
            "purpose": "Screening de señal estadísticamente separable del benchmark, no prueba causal ni estimación out-of-time.",
            "caveat": "La aproximación no corrige dependencia entre meses, managers compartidos ni incertidumbre por estimar el benchmark con la misma población.",
            "latest_significant_report_count": next(
                row["significant_report_count"]
                for row in snapshots
                if str(row["snapshot_date"]) == str(latest["snapshot_date"]) and str(row["threshold_multiplier"]) == "1.30"
            ),
        },
        "recommendation": {
            "working_multiplier": 1.3,
            "reason": "1.3x aumenta a ~25% los flags entre reportes con historia observable, frente a ~20% con 1.4x, y la proporción se mantiene estable en los seis snapshots. 1.2x es menos selectivo.",
            "status": "Inicial y sujeto a backtest out-of-time y gobierno.",
        },
        "privacy": {
            "minimum_shared_cohort": MINIMUM_COHORT,
            "identifiers_persisted": False,
            "employee_rows_persisted": False,
            "manager_rates_persisted": False,
            "manager_rankings_persisted": False,
            "suppressed_subthreshold_manager_counts": True,
        },
        "provenance": {
            "query_sha256": sha256_bytes(QUERY.read_bytes()),
            "result_sha256": sha256_bytes(json.dumps(rows, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")),
        },
        "outcome": "pass",
    }
    reject_restricted_keys(evidence)
    return evidence


def build_evidence() -> dict[str, Any]:
    if not QUERY.exists():
        raise FileNotFoundError(QUERY)
    sql = QUERY.read_text(encoding="utf-8")
    evidence = validate(execute_query(sql))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(OUTPUT.name + ".tmp")
    temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(OUTPUT)
    return evidence


if __name__ == "__main__":
    document = build_evidence()
    print(OUTPUT)
    print(
        "latest={latest}; p50={p50:.4f}x; p75={p75:.4f}x; "
        "working_multiplier={multiplier}".format(
            latest=document["latest_snapshot"],
            p50=document["rate_distribution"]["ratio_percentiles"]["p50"],
            p75=document["rate_distribution"]["ratio_percentiles"]["p75"],
            multiplier=document["recommendation"]["working_multiplier"],
        )
    )
