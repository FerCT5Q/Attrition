"""Construye evidencia agregada y segura para el slide de adquisiciones.

El script no consulta Redshift. Convierte únicamente el resultado congelado y
validado del assessment v4 en un contrato de presentación que el builder V8
puede verificar y consumir en cada reconstrucción.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "acquisition-entry-v4-20260929-r4"
RUN_ROOT = ROOT / "output" / "assessments" / RUN_ID
VARIABLE_ROOT = RUN_ROOT / "vars" / "01-ingreso-por-adquisici-n"
RUN_MANIFEST = RUN_ROOT / "manifest.json"
RUN_LEDGER = RUN_ROOT / "evidence-ledger.json"
VARIABLE_LEDGER = VARIABLE_ROOT / "evidence-ledger.json"
QUERY_RESULTS = VARIABLE_ROOT / "evidence" / "query-results.json"
VARIABLE_DECISION = VARIABLE_ROOT / "decision.json"
SOURCE_SQL = ROOT / "queries" / "audits" / "acquisition_entry_distribution_attrition_20260929.sql"
SOURCE_ACCESS_SQL = ROOT / "queries" / "audits" / "acquisition_entry_source_access_20260929.sql"
OUTPUT = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v8.acquisition-entry-evidence-20260929.json"
)

DISTRIBUTION_QUERY = "queries/audits/acquisition_entry_distribution_attrition_20260929.sql"
SOURCE_ACCESS_QUERY = "queries/audits/acquisition_entry_source_access_20260929.sql"
EXPECTED_DISTRIBUTION_SQL_SHA256 = "4c0bef229458d3cce31edbb26e74a6863012eec853eba1a4a30cccacbb5b6af8"
EXPECTED_DISTRIBUTION_RESULT_SHA256 = "3567cc86914e6ddb2947c08c92a5db0939382ac1dc7ebf91c70df6c249651930"
EXPECTED_SOURCE_ACCESS_SQL_SHA256 = "089f875e0f11ac28f79ad37ef770fd35b715b108c0bb6d9e5c0d12dec7ebfdd1"
EXPECTED_SOURCE_ACCESS_RESULT_SHA256 = "26673cb1f8fc8cdf7079d419fe7d40d53e6e0fbe123b0f4da4a0165c83c6d5d6"

CURRENT_SNAPSHOT = "2026-08-23"
BASELINE_SNAPSHOT = "2025-08-24"
OUTCOME_WINDOW = "(2025-08-24, 2026-08-23]"
MINIMUM_COHORT = 30
MINIMUM_VOLUNTARY_EVENTS = 30
PROHIBITED_KEY_FRAGMENTS = (
    "employee_id",
    "employeeid",
    "manager_employee_id",
    "manager_name",
    "employee_name",
    "email",
    "address",
    "term_date",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sql_hash(path: Path) -> str:
    normalized = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def relative_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"No existe el artefacto requerido: {relative_path(path)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"El artefacto debe ser un objeto JSON: {relative_path(path)}")
    return value


def decimal(value: object, label: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive input validation
        raise ValueError(f"{label} debe ser numérico.") from exc


def integer(value: object, label: str) -> int:
    parsed = decimal(value, label)
    require(parsed == parsed.to_integral_value(), f"{label} debe ser un entero.")
    return int(parsed)


def rate_percent(exits: int, baseline: int) -> Decimal:
    require(baseline > 0, "El denominador de attrition debe ser positivo.")
    require(0 <= exits <= baseline, "Las salidas voluntarias no reconcilian con la cohorte basal.")
    return Decimal("100") * Decimal(exits) / Decimal(baseline)


def matching_ledger_entry(ledger: dict[str, Any], query_reference: str) -> dict[str, Any]:
    matches = [
        row
        for row in ledger.get("queries", [])
        if isinstance(row, dict) and row.get("query_reference") == query_reference
    ]
    require(len(matches) == 1, f"Se esperaba exactamente una entrada de ledger para {query_reference}.")
    return matches[0]


def source_query_rows(query_results: dict[str, Any], query_reference: str) -> list[dict[str, Any]]:
    rows = query_results.get(query_reference)
    require(isinstance(rows, list) and rows, f"No existen filas congeladas para {query_reference}.")
    require(all(isinstance(row, dict) for row in rows), f"Las filas de {query_reference} no son objetos agregados.")
    return rows


def assert_query_provenance(
    *,
    ledger: dict[str, Any],
    query_reference: str,
    sql_path: Path,
    expected_sql_hash: str,
    expected_result_hash: str,
    rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    entry = matching_ledger_entry(ledger, query_reference)
    require(entry.get("source") == "executed_redshift_sql", f"{query_reference} no proviene de SQL ejecutado.")
    require(entry.get("sql_sha256") == expected_sql_hash, f"El hash SQL congelado no coincide para {query_reference}.")
    require(entry.get("result_sha256") == expected_result_hash, f"El hash de resultado congelado no coincide para {query_reference}.")
    require(sql_hash(sql_path) == expected_sql_hash, f"El SQL guardado cambió para {query_reference}.")
    if rows is not None:
        require(canonical_json_hash(rows) == expected_result_hash, f"El resultado agregado cambió para {query_reference}.")
        require(integer(entry.get("row_count"), "row_count") == len(rows), f"El conteo de filas no reconcilia para {query_reference}.")
    return entry


def as_overall_segment(row: dict[str, Any]) -> dict[str, Any]:
    current = integer(row.get("current_employee_count"), "conteo actual")
    current_total = integer(row.get("current_denominator_count"), "denominador actual")
    baseline = integer(row.get("baseline_employee_count"), "cohorte basal")
    baseline_total = integer(row.get("baseline_denominator_count"), "denominador basal")
    exits = integer(row.get("voluntary_exit_count"), "salidas voluntarias")
    share = decimal(row.get("current_share_percent"), "participación actual")
    source_rate = decimal(row.get("annual_attrition_rate_percent"), "tasa anual")
    require(row.get("publication_status") == "publishable", "Los dos segmentos generales deben ser publicables.")
    require(current >= MINIMUM_COHORT and baseline >= MINIMUM_COHORT and exits >= MINIMUM_VOLUNTARY_EVENTS, "Un segmento general no cumple la regla de publicación.")
    require(abs(share - Decimal("100") * current / current_total) < Decimal("0.000000000001"), "La participación del segmento no reconcilia.")
    computed_rate = rate_percent(exits, baseline)
    require(abs(source_rate - computed_rate) < Decimal("0.000000000001"), "La tasa del segmento no reconcilia.")
    return {
        "label": str(row["segment_label"]),
        "current_employee_count": current,
        "current_share_percent": str(share),
        "baseline_employee_count": baseline,
        "voluntary_exit_count": exits,
        "annual_attrition_rate_percent": str(computed_rate),
        "publication_status": "publishable",
    }


def as_top_acquisition(row: dict[str, Any]) -> dict[str, Any]:
    current = integer(row.get("current_employee_count"), "conteo actual por adquisición")
    current_total = integer(row.get("current_denominator_count"), "denominador adquirido actual")
    baseline = integer(row.get("baseline_employee_count"), "cohorte basal por adquisición")
    share = decimal(row.get("current_share_percent"), "participación por adquisición")
    status = str(row.get("publication_status"))
    require(current >= MINIMUM_COHORT, "Una adquisición visible no cumple el mínimo de empleados.")
    require(abs(share - Decimal("100") * current / current_total) < Decimal("0.000000000001"), "La participación de adquisición no reconcilia.")
    result: dict[str, Any] = {
        "label": str(row["segment_label"]),
        "current_employee_count": current,
        "current_share_percent": str(share),
        "annual_attrition": {
            "publication_status": status,
            "baseline_employee_count": baseline,
        },
    }
    if status == "publishable":
        exits = integer(row.get("voluntary_exit_count"), "salidas por adquisición")
        source_rate = decimal(row.get("annual_attrition_rate_percent"), "tasa por adquisición")
        require(baseline >= MINIMUM_COHORT and exits >= MINIMUM_VOLUNTARY_EVENTS, "Una tasa publicada no cumple la supresión.")
        computed_rate = rate_percent(exits, baseline)
        require(abs(source_rate - computed_rate) < Decimal("0.000000000001"), "La tasa por adquisición no reconcilia.")
        result["annual_attrition"].update(
            {
                "voluntary_exit_count": exits,
                "annual_attrition_rate_percent": str(computed_rate),
                "display_note": None,
            }
        )
    elif status == "suppressed_voluntary_events_lt_30":
        exits = integer(row.get("voluntary_exit_count"), "salidas suprimidas")
        require(baseline >= MINIMUM_COHORT and 0 <= exits < MINIMUM_VOLUNTARY_EVENTS, "La supresión por eventos no aplica.")
        require(row.get("annual_attrition_rate_percent") is None, "Una tasa suprimida no debe persistir.")
        result["annual_attrition"].update(
            {
                "annual_attrition_rate_percent": None,
                "display_note": "Tasa suprimida: menos de 30 salidas voluntarias.",
            }
        )
    elif status == "no_annual_comparable_cohort":
        require(baseline == 0, "Una cohorte no comparable debe tener base anual cero.")
        require(row.get("annual_attrition_rate_percent") is None, "Una cohorte no comparable no debe tener tasa.")
        result["annual_attrition"].update(
            {
                "annual_attrition_rate_percent": None,
                "display_note": "Sin cohorte anual comparable.",
            }
        )
    else:
        raise ValueError(f"Estado de publicación no reconocido: {status}.")
    return result


def ensure_aggregate_only(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).casefold()
            require(
                not any(fragment in normalized for fragment in PROHIBITED_KEY_FRAGMENTS),
                f"El artefacto de presentación intentó persistir un campo restringido: {key}.",
            )
            ensure_aggregate_only(nested)
    elif isinstance(value, list):
        for nested in value:
            ensure_aggregate_only(nested)


def authorize_internal_rates(
    payload: dict[str, Any],
    source_rows: list[dict[str, Any]],
    authorization_path: Path,
) -> None:
    """Recalcula tasas de los agregados congelados bajo una excepción explícita."""
    authorization = load_json(authorization_path)
    exception = authorization.get("small_cell_exception", {})
    scope = authorization.get("scope", {})
    require(authorization.get("status") == "approved", "La excepción interna no está aprobada.")
    require(authorization.get("reporting_mode") == "internal_analysis", "La excepción debe ser de análisis interno.")
    require(exception.get("allow_subthreshold_voluntary_event_rates") is True, "La excepción no permite tasas con pocos eventos.")
    require(scope.get("stage_id") == "slide-acquisition", "La excepción no corresponde a adquisiciones.")
    require(scope.get("baseline_snapshot") == BASELINE_SNAPSHOT, "La excepción corresponde a otra cohorte basal.")
    require(scope.get("outcome_window") == OUTCOME_WINDOW, "La excepción corresponde a otra ventana anual.")
    controls = authorization.get("non_negotiable_controls", {})
    require(controls.get("aggregate_only") is True, "La excepción debe limitarse a agregados.")
    for key in (
        "employee_rows_persisted", "employee_ids_persisted", "names_persisted",
        "emails_persisted", "addresses_persisted", "exact_compensation_values",
        "manager_access", "redistribution", "operational_use", "score_v4_change",
        "production_feature_approval",
    ):
        require(controls.get(key) is False, f"La excepción no mantiene el control {key}.")

    top_source = {str(row["segment_label"]): row for row in source_rows if row["row_type"] == "top_acquisition"}
    restored: list[dict[str, Any]] = []
    calculated = 0
    no_cohort = 0
    maximum_error = Decimal(0)
    for row in payload["top_acquisitions"]:
        raw = top_source[row["label"]]
        annual = row["annual_attrition"]
        baseline = integer(raw["baseline_employee_count"], "base anual interna")
        exits = integer(raw["voluntary_exit_count"], "salidas anuales internas")
        require(baseline >= 0 and 0 <= exits <= baseline, "El numerador no cabe en la cohorte basal.")
        annual["source_publication_status"] = str(raw["publication_status"])
        annual["voluntary_exit_count"] = exits
        if baseline == 0:
            require(raw["publication_status"] == "no_annual_comparable_cohort", "La ausencia de base no coincide con el SQL.")
            annual["annual_attrition_rate_percent"] = None
            annual["display_note"] = "Sin cohorte al 24 ago 2025; la tasa anual no es estimable."
            no_cohort += 1
            continue
        value = rate_percent(exits, baseline)
        independent = Fraction(100 * exits, baseline)
        difference = abs(value - Decimal(independent.numerator) / Decimal(independent.denominator))
        require(difference < Decimal("0.000000000001"), "No reconcilia el recálculo independiente de la tasa.")
        maximum_error = max(maximum_error, difference)
        annual["annual_attrition_rate_percent"] = str(value)
        annual["display_note"] = None
        calculated += 1
        if raw["publication_status"] != "publishable":
            annual["publication_status"] = "internal_analysis_exception"
            restored.append({
                "label": row["label"], "baseline_employee_count": baseline,
                "voluntary_exit_count": exits, "annual_attrition_rate_percent": str(value),
            })

    acquired = payload["overall_distribution"][0]
    top = payload["top_acquisitions"]
    require(sum(row["annual_attrition"]["baseline_employee_count"] for row in top) == acquired["baseline_employee_count"], "Top 10 y Otras no cierran la cohorte basal adquirida.")
    require(sum(row["annual_attrition"]["voluntary_exit_count"] for row in top) == acquired["voluntary_exit_count"], "Top 10 y Otras no cierran las salidas de adquisición.")
    payload["artifact_classification"] = payload["deliverable_mode"] = "internal_analysis"
    payload["authorization"] = {
        "path": relative_path(authorization_path), "sha256": sha256_file(authorization_path),
        "authorization_id": authorization["authorization_id"],
        "authorized_audience": authorization["authorized_audience"],
    }
    payload["suppression_policy"] = {
        "scope": "Sólo revisión interna autorizada de la lámina de adquisiciones.",
        "minimum_rate_denominator": 1, "minimum_published_voluntary_events": 0,
        "small_event_rates_allowed": True,
        "non_comparable_label": "Sin cohorte al 24 ago 2025",
    }
    payload["recalculation"] = {
        "method": "División Decimal y comprobación con aritmética racional Fraction sobre agregados congelados.",
        "source": "frozen_executed_redshift_aggregates",
        "source_executed_at": payload["source_provenance"]["distribution_query"]["executed_at"],
        "calculated_at_utc": datetime.now(timezone.utc).isoformat(),
        "formula": "100 * voluntary_exit_count / baseline_employee_count",
        "acceptance_rule": "Base positiva, salidas entre cero y base, error menor a 0.000000000001 puntos; base cero implica tasa nula.",
        "metrics": {
            "top_categories_checked": len(top), "estimable_rates": calculated,
            "restored_rates": len(restored), "zero_baseline_categories": no_cohort,
            "maximum_recalculation_difference_pp": str(maximum_error),
            "top_baseline_total": sum(row["annual_attrition"]["baseline_employee_count"] for row in top),
            "top_voluntary_exit_total": sum(row["annual_attrition"]["voluntary_exit_count"] for row in top),
        },
        "restored_categories": restored, "outcome": "pass", "score_v4_change": False,
    }
    payload["privacy"]["small_voluntary_event_counts_persisted"] = bool(restored)
    payload["validation"]["small_event_rates_suppressed"] = "not_applicable_authorized_internal_analysis"
    payload["validation"].update({
        "internal_authorization_verified": "pass", "all_estimable_rates_recalculated": "pass",
        "independent_rational_recalculation": "pass", "baseline_and_exits_partition_reconcile": "pass",
    })


def build(output: Path = OUTPUT, *, authorization: Path | None = None) -> dict[str, Any]:
    if authorization is not None:
        require(output.resolve() != OUTPUT.resolve(), "La evidencia interna debe usar una salida nueva; no reemplaza la evidencia de presentación.")
    run_manifest = load_json(RUN_MANIFEST)
    run_ledger = load_json(RUN_LEDGER)
    variable_ledger = load_json(VARIABLE_LEDGER)
    query_results = load_json(QUERY_RESULTS)
    decision = load_json(VARIABLE_DECISION)

    require(run_manifest.get("run_id") == RUN_ID, "El manifest no corresponde al run de adquisición aprobado.")
    require(run_manifest.get("status") == "validated", "El assessment de adquisición no está validado.")
    require(run_manifest.get("schema_version") == 4, "El assessment de adquisición debe usar schema v4.")
    require(run_manifest.get("reporting", {}).get("deliverable_mode") == "presentation", "El assessment no está clasificado para presentación.")
    require(variable_ledger.get("variable") == "Ingreso por adquisición", "El ledger no corresponde a la variable esperada.")
    require(integer(variable_ledger.get("query_count"), "query_count") == 8, "El ledger de adquisición debe contener ocho consultas.")
    require(decision.get("final_result") == "Baja - exploratoria", "El resultado del assessment no coincide con la decisión aprobada.")

    distribution_rows = source_query_rows(query_results, DISTRIBUTION_QUERY)
    distribution_entry = assert_query_provenance(
        ledger=variable_ledger,
        query_reference=DISTRIBUTION_QUERY,
        sql_path=SOURCE_SQL,
        expected_sql_hash=EXPECTED_DISTRIBUTION_SQL_SHA256,
        expected_result_hash=EXPECTED_DISTRIBUTION_RESULT_SHA256,
        rows=distribution_rows,
    )
    source_access_entry = assert_query_provenance(
        ledger=variable_ledger,
        query_reference=SOURCE_ACCESS_QUERY,
        sql_path=SOURCE_ACCESS_SQL,
        expected_sql_hash=EXPECTED_SOURCE_ACCESS_SQL_SHA256,
        expected_result_hash=EXPECTED_SOURCE_ACCESS_RESULT_SHA256,
    )
    run_variable_ledgers = [
        item
        for item in run_ledger.get("variables", [])
        if isinstance(item, dict) and item.get("variable") == "Ingreso por adquisición"
    ]
    require(len(run_variable_ledgers) == 1, "El ledger del run no contiene la variable esperada.")
    require(
        matching_ledger_entry(run_variable_ledgers[0], DISTRIBUTION_QUERY).get("result_sha256")
        == EXPECTED_DISTRIBUTION_RESULT_SHA256,
        "El ledger del run no reconcilia con el resultado de distribución.",
    )

    overall_rows = sorted(
        (row for row in distribution_rows if row.get("row_type") == "overall_segment"),
        key=lambda row: integer(row.get("row_order"), "orden de segmento"),
    )
    require(len(overall_rows) == 2, "La distribución general debe tener exactamente dos segmentos.")
    overall = [as_overall_segment(row) for row in overall_rows]
    require(
        [row["label"] for row in overall] == ["Con adquisición registrada", "Sin adquisición registrada"],
        "Las etiquetas de segmento no son las aprobadas.",
    )
    current_total = sum(row["current_employee_count"] for row in overall)
    baseline_total = sum(row["baseline_employee_count"] for row in overall)
    voluntary_exits = sum(row["voluntary_exit_count"] for row in overall)
    require(current_total == 50_043, "Los segmentos no reconcilian con la población actual.")
    require(baseline_total == 45_002, "Los segmentos no reconcilian con la cohorte basal.")
    require(voluntary_exits == 2_484, "Los segmentos no reconcilian con las salidas voluntarias.")

    snapshot_rows = {str(row.get("segment_label")): row for row in distribution_rows if row.get("row_type") == "snapshot_reconciliation"}
    require(integer(snapshot_rows["Snapshot 2025-08-24"].get("current_employee_count"), "baseline de snapshot") == baseline_total, "El snapshot basal no reconcilia.")
    require(integer(snapshot_rows["Snapshot 2026-08-23"].get("current_employee_count"), "snapshot actual") == current_total, "El snapshot actual no reconcilia.")

    top_rows = sorted(
        (row for row in distribution_rows if row.get("row_type") == "top_acquisition"),
        key=lambda row: integer(row.get("row_order"), "orden de adquisición"),
    )
    require(len(top_rows) == 11, "El panel debe contener Top 10 más Otras adquisiciones.")
    require(top_rows[-1].get("segment_label") == "Otras adquisiciones", "Falta la fila Otras adquisiciones.")
    top = [as_top_acquisition(row) for row in top_rows]
    acquired_total = overall[0]["current_employee_count"]
    require(sum(row["current_employee_count"] for row in top) == acquired_total, "Top 10 más Otras no reconcilia con el grupo adquirido.")

    overall_reference = {
        "reference_id": "acquisition-overall-annual",
        "label": "Población basal total",
        "voluntary_exits": voluntary_exits,
        "eligible_baseline_count": baseline_total,
        "rate_percent": str(rate_percent(voluntary_exits, baseline_total)),
        "denominator_definition": "Empleados Regular activos al 2025-08-24",
    }
    acquired_reference = {
        "reference_id": "acquisition-registered-annual",
        "label": "Con adquisición registrada",
        "voluntary_exits": overall[0]["voluntary_exit_count"],
        "eligible_baseline_count": overall[0]["baseline_employee_count"],
        "rate_percent": str(rate_percent(overall[0]["voluntary_exit_count"], overall[0]["baseline_employee_count"])),
        "denominator_definition": "Segmento con adquisición registrada al 2025-08-24",
    }

    payload: dict[str, Any] = {
        "artifact_type": "acquisition_entry_distribution_attrition_evidence",
        "schema_version": 1,
        "artifact_classification": "presentation",
        "deliverable_mode": "presentation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_assessment": {
            "run_id": RUN_ID,
            "status": run_manifest["status"],
            "schema_version": run_manifest["schema_version"],
            "variable": "Ingreso por adquisición",
            "final_result": decision["final_result"],
            "run_manifest_path": relative_path(RUN_MANIFEST),
            "run_manifest_sha256": sha256_file(RUN_MANIFEST),
            "variable_evidence_ledger_path": relative_path(VARIABLE_LEDGER),
            "variable_evidence_ledger_sha256": sha256_file(VARIABLE_LEDGER),
        },
        "definition": {
            "field": "hrda.post_hire_monthly_worker_dtls.acquisition",
            "reader_label": "Adquisición registrada",
            "interpretation": "Marca textual de adquisición registrada en el snapshot mensual. Un valor vacío se presenta como sin adquisición registrada; no prueba que la persona no ingresó mediante una adquisición.",
            "normalization": "Los valores se normalizaron para espacios y mayúsculas; los nombres mostrados conservan la etiqueta almacenada. No se aplicó un mapping de alias no documentado.",
        },
        "population": {
            "worker_type": "Employee",
            "employee_type": "Regular",
            "active_status": 1,
            "unit_of_analysis": "Empleado-snapshot mensual; empleados distintos en cada fecha.",
            "rf360_included": True,
        },
        "dates": {
            "current_snapshot": CURRENT_SNAPSHOT,
            "baseline_snapshot": BASELINE_SNAPSHOT,
            "outcome_window": OUTCOME_WINDOW,
            "attrition_definition": "Una salida voluntaria por persona de la cohorte basal; sólo VOLUNTARY.",
            "classification_boundary": "La clasificación para attrition se toma del snapshot basal; no se usa un valor posterior para reclasificar la cohorte.",
        },
        "suppression_policy": {
            "minimum_published_cohort": MINIMUM_COHORT,
            "minimum_published_voluntary_events": MINIMUM_VOLUNTARY_EVENTS,
            "suppressed_rate_label": "Tasa suprimida: menos de 30 salidas voluntarias.",
            "non_comparable_label": "Sin cohorte anual comparable.",
        },
        "totals": {
            "current_active_regular_employee_count": current_total,
            "baseline_active_regular_employee_count": baseline_total,
            "baseline_voluntary_exit_count": voluntary_exits,
        },
        "overall_distribution": overall,
        "top_acquisitions": top,
        "color_references": {
            "overall_distribution": overall_reference,
            "acquisition_panel": acquired_reference,
        },
        "historical_baseline_reconciliation": {
            "current_evidence_baseline_count": baseline_total,
            "previous_deck_baseline_count": 45_003,
            "difference": baseline_total - 45_003,
            "status": "requires_data_owner_reconciliation",
            "note": "La diferencia de un empleado frente a evidencia previa del deck está documentada, pero su causa no se atribuye en este artefacto; requiere reconciliación del responsable de datos antes de uso externo.",
        },
        "source_provenance": {
            "distribution_query": {
                "query_path": DISTRIBUTION_QUERY,
                "sql_sha256": distribution_entry["sql_sha256"],
                "result_sha256": distribution_entry["result_sha256"],
                "row_count": integer(distribution_entry["row_count"], "filas de distribución"),
                "executed_at": distribution_entry["executed_at"],
            },
            "source_access_query": {
                "query_path": SOURCE_ACCESS_QUERY,
                "sql_sha256": source_access_entry["sql_sha256"],
                "result_sha256": source_access_entry["result_sha256"],
                "row_count": integer(source_access_entry["row_count"], "filas de acceso de fuente"),
                "executed_at": source_access_entry["executed_at"],
            },
        },
        "validation": {
            "validated_assessment_v4": "pass",
            "saved_sql_and_result_hashes_match": "pass",
            "overall_segments_reconcile": "pass",
            "top_10_plus_other_reconcile": "pass",
            "published_rates_recalculate_from_counts": "pass",
            "small_event_rates_suppressed": "pass",
            "no_comparable_cohorts_not_zero_filled": "pass",
            "historical_baseline_difference": "documented_requires_owner_reconciliation",
            "aggregate_only": "pass",
        },
        "privacy": {
            "aggregate_only": True,
            "employee_rows_persisted": False,
            "individual_identifiers_persisted": False,
            "small_voluntary_event_counts_persisted": False,
        },
        "outcome": "pass",
    }
    if authorization is not None:
        authorize_internal_rates(payload, distribution_rows, authorization)
    ensure_aggregate_only(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Construye evidencia agregada para Adquisiciones y attrition.")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="Ruta de salida JSON.")
    parser.add_argument("--authorization", type=Path, help="Excepción explícita para tasas agregadas internas.")
    args = parser.parse_args()
    result = build(args.output, authorization=args.authorization)
    print(f"Evidencia generada: {relative_path(args.output)} ({result['outcome']})")


if __name__ == "__main__":
    main()
