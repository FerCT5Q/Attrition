"""Build presentation-safe six-month voluntary attrition evidence by distance.

The Redshift query returns only aggregated employee-snapshot groups keyed by
one-way location hashes.  Public office and postal-centroid references are
joined only in memory.  Neither employee identifiers, postal values, hashes,
nor raw location groups are written to the final artifact.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from build_global_commute_distance_evidence import (
    COUNTRY_ISO,
    canonical_country,
    choose_offices,
    download_centroids,
    haversine_km,
    load_offices,
    query_postal_hashes,
)


ROOT = Path(__file__).resolve().parents[1]
ONSITE_QUERY = ROOT / "queries" / "profiles" / "commute_distance_onsite_six_month_attrition_hash_profile_20260917.sql"
ONSITE_COUNTRY_PARTITIONS_QUERY = ROOT / "queries" / "profiles" / "commute_distance_onsite_six_month_attrition_country_partitions_20260917.sql"
ONSITE_AUDIT_QUERY = ROOT / "queries" / "audits" / "commute_distance_onsite_six_month_attrition_audit_20260917.sql"
ALL_ELIGIBLE_QUERY = ROOT / "queries" / "profiles" / "commute_distance_all_eligible_six_month_attrition_hash_profile_20260917.sql"
ALL_ELIGIBLE_COUNTRY_PARTITIONS_QUERY = ROOT / "queries" / "profiles" / "commute_distance_all_eligible_six_month_attrition_country_partitions_20260917.sql"
ALL_ELIGIBLE_AUDIT_QUERY = ROOT / "queries" / "audits" / "commute_distance_all_eligible_six_month_attrition_audit_20260917.sql"
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
DEFAULT_OUTPUTS = {
    "onsite": ROOT / "output" / "distribution" / "json" / "commute-distance-onsite-six-month-attrition-evidence-20260917.json",
    "all-eligible": ROOT / "output" / "distribution" / "json" / "commute-distance-all-eligible-six-month-attrition-evidence-20260917.json",
}

# Backward-compatible aliases keep the existing Onsite constructor stable.
QUERY = ONSITE_QUERY
COUNTRY_PARTITIONS_QUERY = ONSITE_COUNTRY_PARTITIONS_QUERY
AUDIT_QUERY = ONSITE_AUDIT_QUERY
DEFAULT_OUTPUT = DEFAULT_OUTPUTS["onsite"]

MINIMUM_COHORT = 30
MAX_DETAILED_KM = 30
EXPECTED_SNAPSHOT_COUNT = 24
MINIMUM_MATCHED_COVERAGE_PERCENT = 70.0

COHORTS: dict[str, dict[str, Any]] = {
    "onsite": {
        "query": ONSITE_QUERY,
        "country_partitions_query": ONSITE_COUNTRY_PARTITIONS_QUERY,
        "audit_query": ONSITE_AUDIT_QUERY,
        "population": "Employee, Regular, active_status=1 y work_arrangement=ONSITE en cada snapshot",
        "eligible_exposure_key": "eligible_onsite_employee_snapshots",
        "complete_location_exposure_key": "eligible_onsite_complete_location_employee_snapshots",
        "complete_location_exit_key": "eligible_onsite_complete_location_voluntary_exits",
        "multirow_key": "multirow_onsite_employee_snapshots",
        "conflicting_location_key": "conflicting_location_onsite_employee_snapshots",
        "coverage_key": "matched_distance_coverage_percent_of_eligible_onsite",
        "average_band_exposure_key": "average_monthly_onsite_employee_snapshots",
        "display_name": "Onsite",
        "require_zero_multirow": True,
        "require_zero_conflicts": True,
    },
    "all-eligible": {
        "query": ALL_ELIGIBLE_QUERY,
        "country_partitions_query": ALL_ELIGIBLE_COUNTRY_PARTITIONS_QUERY,
        "audit_query": ALL_ELIGIBLE_AUDIT_QUERY,
        "population": "Employee, Regular y active_status=1 en cada snapshot, sin filtro de work_arrangement",
        "eligible_exposure_key": "eligible_employee_snapshots",
        "complete_location_exposure_key": "eligible_complete_location_employee_snapshots",
        "complete_location_exit_key": "eligible_complete_location_voluntary_exits",
        "multirow_key": "multirow_employee_snapshots",
        "conflicting_location_key": "conflicting_location_employee_snapshots",
        "coverage_key": "matched_distance_coverage_percent_of_eligible",
        "average_band_exposure_key": "average_monthly_employee_snapshots",
        "display_name": "All eligible",
        "require_zero_multirow": False,
        "require_zero_conflicts": False,
    },
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def query_rows(
    path: Path,
    max_rows: int,
    *,
    allow_truncated: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    """Run the project-approved read-only helper and retain raw groups in memory only."""
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(QUERY_HELPER),
            "--sql-file",
            str(path),
            "--max-rows",
            str(max_rows),
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
    if not isinstance(rows, list) or (payload.get("truncated") and not allow_truncated):
        raise ValueError(f"La consulta {path.name} debe devolver todas las filas agregadas sin truncar.")
    result_sha256 = hashlib.sha256(
        json.dumps(rows, sort_keys=True, default=str, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return [dict(row) for row in rows], payload, result_sha256


def partition_condition(country_hash: str, postal_hash_prefix: str) -> str:
    """Build a constrained, hash-only partition predicate for the saved SQL template."""
    allowed = set("0123456789abcdef")
    if len(country_hash) != 32 or any(character not in allowed for character in country_hash):
        raise ValueError("La partición de país no contiene un hash MD5 válido.")
    if any(character not in allowed for character in postal_hash_prefix):
        raise ValueError("La partición postal no contiene un prefijo hexadecimal válido.")
    conditions = [
        "MD5(UPPER(TRIM(CAST(w.country AS VARCHAR(256))))) = " + repr(country_hash),
    ]
    if postal_hash_prefix:
        conditions.append(
            "SUBSTRING(MD5(UPPER(TRIM(CAST(w.postal_code AS VARCHAR(64))))) "
            f"FROM 1 FOR {len(postal_hash_prefix)}) = {postal_hash_prefix!r}"
        )
    return " AND ".join(conditions)


def query_partitioned_profile(cohort: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]], str]:
    """Read the hash profile in small, non-overlapping aggregate partitions."""
    partition_query = Path(cohort["country_partitions_query"]) if cohort else COUNTRY_PARTITIONS_QUERY
    profile_query = Path(cohort["query"]) if cohort else QUERY
    partition_rows, _, partition_result_sha256 = query_rows(partition_query, max_rows=1000)
    template = profile_query.read_text(encoding="utf-8")
    marker = "/* COMMUTE_DISTANCE_PARTITION_FILTER */ 1 = 1"
    if marker not in template:
        raise ValueError("El perfil hash no contiene el marcador de partición requerido.")

    rows: list[dict[str, Any]] = []
    query_log: list[dict[str, Any]] = []
    temp_parent = ROOT / ".tmp"
    temp_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="commute-distance-attrition-", dir=temp_parent) as temp_directory:
        temp_path = Path(temp_directory) / "partition.sql"

        def fetch(country_hash: str, postal_hash_prefix: str) -> None:
            rendered = template.replace(marker, partition_condition(country_hash, postal_hash_prefix))
            temp_path.write_text(rendered, encoding="utf-8")
            part_rows, payload, part_sha256 = query_rows(temp_path, max_rows=1000, allow_truncated=True)
            if payload.get("truncated"):
                if len(postal_hash_prefix) >= 4:
                    raise ValueError("Una partición hash sigue superando 1,000 filas tras cuatro niveles.")
                for suffix in "0123456789abcdef":
                    fetch(country_hash, postal_hash_prefix + suffix)
                return
            rows.extend(part_rows)
            query_log.append(
                {
                    "country_hash": country_hash,
                    "postal_hash_prefix": postal_hash_prefix or "all",
                    "row_count": len(part_rows),
                    "result_sha256": part_sha256,
                }
            )

        for partition in partition_rows:
            fetch(str(partition["country_hash"]), "")

    if not rows:
        raise ValueError("El perfil particionado no devolvió grupos de distancia.")
    result_sha256 = hashlib.sha256(
        json.dumps(rows, sort_keys=True, default=str, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return rows, result_sha256, query_log, partition_result_sha256


def label_for_band(lower_km: int, upper_km: int | None) -> str:
    return f"{lower_km}–<{upper_km} km" if upper_km is not None else f"{lower_km}+ km"


def band_is_publishable(band: dict[str, Any]) -> bool:
    return (
        int(band["employee_snapshot_count"]) >= MINIMUM_COHORT
        and int(band["voluntary_exits"]) >= MINIMUM_COHORT
    )


def merge_adjacent_bands(bands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Coalesce adjacent one-km cells until both exposure and exit thresholds pass."""
    merged = [dict(band) for band in bands]
    while len(merged) > 1 and any(not band_is_publishable(band) for band in merged):
        bad_index = min(
            (index for index, band in enumerate(merged) if not band_is_publishable(band)),
            key=lambda index: (
                int(merged[index]["voluntary_exits"]),
                int(merged[index]["employee_snapshot_count"]),
            ),
        )
        if bad_index == 0:
            neighbor_index = 1
        elif bad_index == len(merged) - 1:
            neighbor_index = bad_index - 1
        else:
            candidate_indexes = (bad_index - 1, bad_index + 1)
            neighbor_index = max(
                candidate_indexes,
                key=lambda index: (
                    min(
                        (int(merged[bad_index]["voluntary_exits"]) + int(merged[index]["voluntary_exits"])) / MINIMUM_COHORT,
                        (int(merged[bad_index]["employee_snapshot_count"]) + int(merged[index]["employee_snapshot_count"])) / MINIMUM_COHORT,
                    ),
                    int(merged[index]["voluntary_exits"]),
                    int(merged[index]["employee_snapshot_count"]),
                ),
            )
        first, second = sorted((bad_index, neighbor_index))
        left, right = merged[first], merged[second]
        merged[first] = {
            "lower_km": int(left["lower_km"]),
            "upper_km": right["upper_km"],
            "employee_snapshot_count": int(left["employee_snapshot_count"]) + int(right["employee_snapshot_count"]),
            "voluntary_exits": int(left["voluntary_exits"]) + int(right["voluntary_exits"]),
        }
        del merged[second]
    if not all(band_is_publishable(band) for band in merged):
        raise ValueError("La población calculable no permite publicar una tasa con la regla de cohorte mínima.")
    return merged


def build_distance_bands(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, Any]]:
    """Resolve external references and return only coalesced, presentation-safe bands."""
    offices, office_catalog_sha256 = load_offices()
    from build_global_commute_distance_evidence import office_candidates  # local import avoids a wider public surface

    by_alias, by_city = office_candidates(offices)
    row_candidates: list[tuple[dict[str, Any], list[dict[str, Any]], str]] = []
    required_countries: set[str] = set()
    for row in rows:
        candidates, resolution = choose_offices(row, by_alias, by_city, offices)
        row_candidates.append((row, candidates, resolution))
        for office in candidates:
            country_code = COUNTRY_ISO.get(canonical_country(office["country"]))
            if country_code:
                required_countries.add(country_code)

    centroid_by_country: dict[str, dict[str, tuple[float, float]]] = {}
    source_manifest: dict[str, dict[str, Any]] = {}
    unavailable_sources: list[str] = []
    for country_code in sorted(required_countries):
        try:
            centroids, source_hash, source_rows = download_centroids(country_code)
        except Exception as error:  # The country is counted as unmatched below; no fallback distance is invented.
            unavailable_sources.append(f"{country_code}: {type(error).__name__}")
            continue
        centroid_by_country[country_code] = centroids
        source_manifest[country_code] = {"sha256": source_hash, "source_rows_read": source_rows}

    raw_bands: dict[int, dict[str, Any]] = {
        kilometre: {
            "lower_km": kilometre,
            "upper_km": kilometre + 1 if kilometre < MAX_DETAILED_KM else None,
            "employee_snapshot_count": 0,
            "voluntary_exits": 0,
        }
        for kilometre in range(MAX_DETAILED_KM + 1)
    }
    coverage = defaultdict(int)
    for row, candidates, resolution in row_candidates:
        exposure = int(row["employee_snapshot_count"])
        exits = int(row["voluntary_exits"])
        if exposure < 1 or exits < 0 or exits > exposure:
            raise ValueError("Una fila agregada de distancia no reconcilia exposición y salidas voluntarias.")
        coverage["input_employee_snapshot_count"] += exposure
        coverage["input_voluntary_exits"] += exits
        if not candidates:
            coverage["unmatched_office_employee_snapshot_count"] += exposure
            coverage["unmatched_office_voluntary_exits"] += exits
            continue

        centroid_candidates: list[float] = []
        for office in candidates:
            country_code = COUNTRY_ISO.get(canonical_country(office["country"]))
            if not country_code:
                continue
            for postal_hash in query_postal_hashes(row, country_code):
                centroid = centroid_by_country.get(country_code, {}).get(postal_hash)
                if centroid is not None:
                    centroid_candidates.append(haversine_km(*centroid, office))
                    break
        if not centroid_candidates:
            coverage["unmatched_centroid_employee_snapshot_count"] += exposure
            coverage["unmatched_centroid_voluntary_exits"] += exits
            continue

        distance = min(centroid_candidates)
        kilometre = min(int(math.floor(distance)), MAX_DETAILED_KM)
        band = raw_bands[kilometre]
        band["employee_snapshot_count"] += exposure
        band["voluntary_exits"] += exits
        coverage["matched_distance_employee_snapshot_count"] += exposure
        coverage["matched_distance_voluntary_exits"] += exits
        if resolution == "office_site":
            coverage["office_site_resolved_employee_snapshot_count"] += exposure
        else:
            coverage["fallback_office_resolved_employee_snapshot_count"] += exposure

    if coverage["input_employee_snapshot_count"] != (
        coverage["matched_distance_employee_snapshot_count"]
        + coverage["unmatched_office_employee_snapshot_count"]
        + coverage["unmatched_centroid_employee_snapshot_count"]
    ):
        raise ValueError("La cobertura de distancia no reconcilia las exposiciones de entrada.")
    coalesced = merge_adjacent_bands(list(raw_bands.values()))
    if sum(int(band["employee_snapshot_count"]) for band in coalesced) != coverage["matched_distance_employee_snapshot_count"]:
        raise ValueError("Las bandas publicadas no reconcilian la población con distancia calculable.")

    reference = {
        "office_catalog_sha256": office_catalog_sha256,
        "office_catalog_locations": len(offices),
        "postal_centroid_sources": source_manifest,
        "unavailable_postal_sources": unavailable_sources,
    }
    return coalesced, dict(coverage), reference


def build_evidence() -> dict[str, Any]:
    audit_rows, _, audit_result_sha256 = query_rows(AUDIT_QUERY, max_rows=10)
    if len(audit_rows) != 1:
        raise ValueError("El audit de distancia debe devolver una única fila agregada.")
    audit = audit_rows[0]
    if int(audit["snapshot_count"]) != EXPECTED_SNAPSHOT_COUNT:
        raise ValueError(f"Se esperaban {EXPECTED_SNAPSHOT_COUNT} snapshots; se recibieron {audit['snapshot_count']}.")
    if int(audit["multirow_onsite_employee_snapshots"]) != 0:
        raise ValueError("Hay employee-snapshots Onsite multirow sin una regla aprobada de reconciliación.")
    if int(audit["conflicting_location_onsite_employee_snapshots"]) != 0:
        raise ValueError("Hay employee-snapshots Onsite con ubicaciones conflictivas; no se publicará una tasa ambigua.")

    input_rows, profile_result_sha256, partition_log, partition_catalog_result_sha256 = query_partitioned_profile()
    raw_exposure = sum(int(row["employee_snapshot_count"]) for row in input_rows)
    raw_exits = sum(int(row["voluntary_exits"]) for row in input_rows)
    if raw_exposure != int(audit["eligible_onsite_complete_location_employee_snapshots"]):
        raise ValueError("El perfil hash no reconcilia las exposiciones Onsite con ubicación completa del audit.")
    if raw_exits != int(audit["eligible_onsite_complete_location_voluntary_exits"]):
        raise ValueError("El perfil hash no reconcilia las salidas voluntarias del audit.")

    bands, coverage, reference = build_distance_bands(input_rows)
    matched_exposure = int(coverage["matched_distance_employee_snapshot_count"])
    matched_exits = int(coverage["matched_distance_voluntary_exits"])
    eligible_exposure = int(audit["eligible_onsite_employee_snapshots"])
    matched_coverage_percent = 100.0 * matched_exposure / eligible_exposure if eligible_exposure else 0.0
    baseline_rate = 100.0 * matched_exits / matched_exposure if matched_exposure else 0.0
    rendered_bands: list[dict[str, Any]] = []
    for band in bands:
        exposure = int(band["employee_snapshot_count"])
        exits = int(band["voluntary_exits"])
        rate = 100.0 * exits / exposure
        rendered_bands.append(
            {
                "category": label_for_band(int(band["lower_km"]), band["upper_km"]),
                "lower_km": int(band["lower_km"]),
                "upper_km": band["upper_km"],
                "employee_snapshot_count": exposure,
                "average_monthly_onsite_employee_snapshots": round(exposure / EXPECTED_SNAPSHOT_COUNT),
                "voluntary_exits": exits,
                "attrition_rate_percent": round(rate, 2),
                "lift_vs_matched_distance_baseline": round(rate / baseline_rate, 3) if baseline_rate else None,
                "snapshot_window_count": EXPECTED_SNAPSHOT_COUNT,
            }
        )

    outcome = "pass" if (
        matched_coverage_percent >= MINIMUM_MATCHED_COVERAGE_PERCENT
        and all(
            item["employee_snapshot_count"] >= MINIMUM_COHORT and item["voluntary_exits"] >= MINIMUM_COHORT
            for item in rendered_bands
        )
        and sum(item["employee_snapshot_count"] for item in rendered_bands) == matched_exposure
    ) else "warning"
    if outcome != "pass":
        raise ValueError("La evidencia de distancia no cumple su regla de aceptación para publicación.")

    return {
        "artifact_type": "aggregate_distance_attrition_evidence",
        "version": 1,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "presentation",
        "variable": "Commute distance",
        "purpose": "Describir la relación no causal entre distancia geográfica estimada y attrition voluntaria posterior al snapshot.",
        "outcome_contract": {
            "population": "Employee, Regular, active_status=1 y work_arrangement=ONSITE en cada snapshot",
            "grain": "employee_snapshot",
            "snapshot_window": "24 snapshots mensuales, 2024-03-24 a 2026-02-22",
            "target": "term_type='VOLUNTARY' con term_date en (snapshot_date, snapshot_date + 6 meses]",
            "excluded": ["Voluntary Exception", "tipos de terminación nulos o ambiguos", "terminaciones involuntarias"],
        },
        "method": {
            "distance": "Distancia Haversine entre el centroide del código postal residencial y la coordenada del office_site resuelto",
            "unit": "kilómetros",
            "binning": "Celdas iniciales de 1 km desde 0 hasta 30 km; 30+ km se mantiene como cola. Las celdas vecinas se combinan hasta que cada banda tenga al menos 30 employee-snapshots y 30 salidas Voluntary.",
            "interpretation": "Proxy geográfico. No mide distancia por carretera, tiempo de traslado ni commute real.",
            "residential_data_handling": "postal_code se consulta solo como hash y no se persiste ni se publica.",
        },
        "coverage": {
            "eligible_onsite_employee_snapshots": eligible_exposure,
            "complete_location_nonconflicting_employee_snapshots": int(audit["eligible_onsite_complete_location_employee_snapshots"]),
            "matched_distance_employee_snapshots": matched_exposure,
            "matched_distance_coverage_percent_of_eligible_onsite": round(matched_coverage_percent, 2),
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
            "profile": str(QUERY.relative_to(ROOT)).replace("\\", "/"),
            "profile_sha256": sha256_file(QUERY),
            "profile_result_sha256": profile_result_sha256,
            "country_partitions": str(COUNTRY_PARTITIONS_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "country_partitions_sha256": sha256_file(COUNTRY_PARTITIONS_QUERY),
            "country_partitions_result_sha256": partition_catalog_result_sha256,
            "executed_hash_partitions": partition_log,
            "audit": str(AUDIT_QUERY.relative_to(ROOT)).replace("\\", "/"),
            "audit_sha256": sha256_file(AUDIT_QUERY),
            "audit_result_sha256": audit_result_sha256,
        },
        "acceptance_rule": "24 snapshots exactos; cero conflictos de ubicación; el perfil hash reconcilia exposición y exits con el audit; cobertura de distancia calculable >=70% de Onsite; cada banda publicada tiene >=30 employee-snapshots y >=30 salidas Voluntary.",
        "outcome": outcome,
        "limitations": [
            "La distancia usa centroides postales y coordenadas de oficina, por lo que es una aproximación geográfica.",
            "La relación es descriptiva; no demuestra causalidad ni produce una predicción individual.",
            "La población sin distancia calculable permanece fuera de la comparación de tasas y se reporta como cobertura.",
        ],
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Construye evidencia de attrition por distancia Onsite.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    evidence = build_evidence()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "outcome": evidence["outcome"],
                "bands": len(evidence["bands"]),
                "coverage_percent": evidence["coverage"]["matched_distance_coverage_percent_of_eligible_onsite"],
                "baseline_rate_percent": evidence["baseline"]["attrition_rate_percent"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
