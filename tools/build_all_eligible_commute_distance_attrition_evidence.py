"""Build safe aggregate six-month attrition evidence for the All eligible bars.

The implementation reuses the approved hash-only distance pipeline.  It changes
only the declared cohort: active regular employees at each snapshot, without a
work-arrangement restriction.  No employee, postal value, office label or raw
location group is written to the evidence artifact.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

import build_commute_distance_attrition_evidence as base
from build_residential_manager_distance_evidence import (
    CENTROID_CACHE,
    PublicCentroidReferenceUnavailable,
    load_centroids,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "distribution" / "json" / "commute-distance-all-eligible-six-month-attrition-evidence-20260917.json"
POPULATION = "Employee, Regular y active_status=1 en cada snapshot, sin filtro de work_arrangement"
SNAPSHOT_WINDOW = "24 snapshots mensuales, 2024-03-24 a 2026-02-22"
TARGET = "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 6 meses]"


def cached_geonames_centroids(country_code: str):
    """Load only verified public GeoNames references already cached in the project.

    The prior direct-text endpoint is not a stable reference for every country.
    Reusing the checked GeoNames cache avoids treating a temporary HTTP failure
    as missing employee distance and records the public-source hash below.
    """
    try:
        centroids, metadata = load_centroids(country_code, CENTROID_CACHE)
    except PublicCentroidReferenceUnavailable as error:
        raise RuntimeError(str(error)) from error
    return centroids, str(metadata["sha256"]), int(metadata["source_rows_read"])


def build_evidence() -> dict[str, Any]:
    """Run aggregate queries, reconcile their totals, and return publishable bands."""
    # The shared functions read these module globals so the identical hash-only
    # partitioning and public centroid logic is used for All eligible.
    base.QUERY = base.ALL_ELIGIBLE_QUERY
    base.COUNTRY_PARTITIONS_QUERY = base.ALL_ELIGIBLE_COUNTRY_PARTITIONS_QUERY
    base.AUDIT_QUERY = base.ALL_ELIGIBLE_AUDIT_QUERY

    audit_rows, _, audit_result_sha256 = base.query_rows(base.AUDIT_QUERY, max_rows=10)
    if len(audit_rows) != 1:
        raise ValueError("El audit de All eligible debe devolver una unica fila agregada.")
    audit = audit_rows[0]
    if int(audit["snapshot_count"]) != base.EXPECTED_SNAPSHOT_COUNT:
        raise ValueError("La ventana de All eligible no contiene los 24 snapshots esperados.")

    input_rows, profile_result_sha256, partition_log, partition_catalog_result_sha256 = base.query_partitioned_profile()
    raw_exposure = sum(int(row["employee_snapshot_count"]) for row in input_rows)
    raw_exits = sum(int(row["voluntary_exits"]) for row in input_rows)
    if raw_exposure != int(audit["eligible_complete_location_employee_snapshots"]):
        raise ValueError("El perfil hash de All eligible no reconcilia la exposicion con ubicacion completa.")
    if raw_exits != int(audit["eligible_complete_location_voluntary_exits"]):
        raise ValueError("El perfil hash de All eligible no reconcilia las salidas voluntarias.")

    base.download_centroids = cached_geonames_centroids
    bands, coverage, reference = base.build_distance_bands(input_rows)
    matched_exposure = int(coverage["matched_distance_employee_snapshot_count"])
    matched_exits = int(coverage["matched_distance_voluntary_exits"])
    eligible_exposure = int(audit["eligible_employee_snapshots"])
    matched_coverage_percent = 100.0 * matched_exposure / eligible_exposure if eligible_exposure else 0.0
    baseline_rate = 100.0 * matched_exits / matched_exposure if matched_exposure else 0.0
    rendered_bands: list[dict[str, Any]] = []
    for band in bands:
        exposure = int(band["employee_snapshot_count"])
        exits = int(band["voluntary_exits"])
        rendered_bands.append(
            {
                "category": base.label_for_band(int(band["lower_km"]), band["upper_km"]),
                "lower_km": int(band["lower_km"]),
                "upper_km": band["upper_km"],
                "employee_snapshot_count": exposure,
                "average_monthly_employee_snapshots": round(exposure / base.EXPECTED_SNAPSHOT_COUNT),
                "voluntary_exits": exits,
                "attrition_rate_percent": round(100.0 * exits / exposure, 2),
                "lift_vs_matched_distance_baseline": round((100.0 * exits / exposure) / baseline_rate, 3) if baseline_rate else None,
                "snapshot_window_count": base.EXPECTED_SNAPSHOT_COUNT,
            }
        )

    outcome = "pass" if (
        matched_coverage_percent >= base.MINIMUM_MATCHED_COVERAGE_PERCENT
        and all(
            item["employee_snapshot_count"] >= base.MINIMUM_COHORT and item["voluntary_exits"] >= base.MINIMUM_COHORT
            for item in rendered_bands
        )
        and sum(item["employee_snapshot_count"] for item in rendered_bands) == matched_exposure
    ) else "warning"
    if outcome != "pass":
        raise ValueError("La evidencia All eligible no cumple la regla de aceptacion para publicacion.")

    return {
        "artifact_type": "aggregate_distance_attrition_evidence",
        "version": 1,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "presentation",
        "cohort": "all_eligible",
        "variable": "Commute distance",
        "purpose": "Describe la relacion no causal entre distancia geografica estimada y attrition voluntaria posterior al snapshot para All eligible.",
        "outcome_contract": {
            "population": POPULATION,
            "grain": "employee_snapshot",
            "snapshot_window": SNAPSHOT_WINDOW,
            "target": TARGET,
            "excluded": ["Voluntary Exception", "tipos de terminacion nulos o ambiguos", "terminaciones involuntarias"],
        },
        "method": {
            "distance": "Distancia Haversine entre el centroide postal residencial y la coordenada del office_site resuelto",
            "unit": "kilometros",
            "binning": "Celdas iniciales de 1 km desde 0 hasta 30 km; 30+ km permanece como cola. Las celdas vecinas se combinan hasta que cada banda tenga al menos 30 employee-snapshots y 30 salidas Voluntary.",
            "interpretation": "Proxy geografico. No mide distancia por carretera, tiempo de traslado ni commute real.",
            "residential_data_handling": "postal_code se consulta solo como hash y no se persiste ni se publica.",
        },
        "coverage": {
            "eligible_employee_snapshots": eligible_exposure,
            "complete_location_nonconflicting_employee_snapshots": int(audit["eligible_complete_location_employee_snapshots"]),
            "matched_distance_employee_snapshots": matched_exposure,
            "matched_distance_coverage_percent_of_eligible": round(matched_coverage_percent, 2),
            **coverage,
        },
        "baseline": {
            "employee_snapshot_count": matched_exposure,
            "voluntary_exits": matched_exits,
            "attrition_rate_percent": round(baseline_rate, 2),
        },
        "bands": rendered_bands,
        "audit_metrics": audit,
        "reference_sources": reference,
        "query": {
            "profile": str(base.ALL_ELIGIBLE_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "profile_sha256": base.sha256_file(base.ALL_ELIGIBLE_QUERY),
            "profile_result_sha256": profile_result_sha256,
            "country_partitions": str(base.ALL_ELIGIBLE_COUNTRY_PARTITIONS_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "country_partitions_sha256": base.sha256_file(base.ALL_ELIGIBLE_COUNTRY_PARTITIONS_QUERY),
            "country_partitions_result_sha256": partition_catalog_result_sha256,
            "executed_hash_partitions": partition_log,
            "audit": str(base.ALL_ELIGIBLE_AUDIT_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "audit_sha256": base.sha256_file(base.ALL_ELIGIBLE_AUDIT_QUERY),
            "audit_result_sha256": audit_result_sha256,
        },
        "acceptance_rule": "24 snapshots exactos; el perfil hash reconcilia exposicion y exits con el audit para ubicacion completa y no conflictiva; cobertura de distancia calculable >=70% de All eligible; cada banda publicada tiene >=30 employee-snapshots y >=30 salidas Voluntary.",
        "outcome": outcome,
        "limitations": [
            "La distancia usa centroides postales y coordenadas de oficina, por lo que es una aproximacion geografica.",
            "La relacion es descriptiva; no demuestra causalidad ni produce una prediccion individual.",
            "La poblacion sin distancia calculable permanece fuera de la comparacion de tasas y se reporta como No calculable.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Construye evidencia de attrition por distancia para All eligible.")
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    evidence = build_evidence()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "outcome": evidence["outcome"], "bands": len(evidence["bands"]), "coverage_percent": evidence["coverage"]["matched_distance_coverage_percent_of_eligible"], "baseline_rate_percent": evidence["baseline"]["attrition_rate_percent"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
