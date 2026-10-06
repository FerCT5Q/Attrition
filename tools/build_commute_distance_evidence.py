"""Build privacy-safe aggregate evidence for the Mexico City commute proxy.

The HR query returns only MD5 hashes of normalized employee postal codes and
distinct-employee counts. The public postal-centroid reference is held in
memory, joined by the same hash, and never written to disk. The output keeps
only aggregate distance bands and provenance hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import urllib3
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
PROFILE_SQL = ROOT / "queries" / "profiles" / "commute_distance_mexico_city_zip_hash_distribution_20260908.sql"
SNAPSHOT = "2026-09-27"
POSTAL_REFERENCE_URL = "https://symerio.github.io/postal-codes-data/data/geonames/MX.txt"
OFFICE_LAT = 19.4287845
OFFICE_LON = -99.207451
MINIMUM_COHORT = 30


def query_zip_hash_counts() -> tuple[dict[str, object], str]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(QUERY_HELPER),
            "--sql-file",
            str(PROFILE_SQL),
            "--max-rows",
            "200",
            "--reporting-mode",
            "presentation",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    result_sha256 = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return payload, result_sha256


def download_postal_reference() -> tuple[dict[str, tuple[float, float]], str, int]:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(POSTAL_REFERENCE_URL, timeout=60, verify=False)
    response.raise_for_status()
    raw = response.content
    reference_sha256 = hashlib.sha256(raw).hexdigest()
    rows = 0
    by_postal: dict[str, list[tuple[float, float]]] = {}
    for line in response.text.splitlines():
        parts = line.split("\t")
        if len(parts) < 11:
            continue
        try:
            postal = parts[1].strip().upper()
            latitude = float(parts[9])
            longitude = float(parts[10])
        except (TypeError, ValueError):
            continue
        if not postal:
            continue
        rows += 1
        by_postal.setdefault(postal, []).append((latitude, longitude))
    centroids = {
        postal: (
            sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points),
        )
        for postal, points in by_postal.items()
    }
    return centroids, reference_sha256, rows


def haversine_km(latitude: float, longitude: float) -> float:
    earth_radius_km = 6371.0088
    lat1, lon1, lat2, lon2 = map(
        math.radians, (latitude, longitude, OFFICE_LAT, OFFICE_LON)
    )
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * earth_radius_km * math.asin(math.sqrt(a))


def candidate_bands(distances: list[tuple[float, int]]) -> list[tuple[float, float | None, int]]:
    limits: list[tuple[float, float | None]] = [(0.0, 5.0), (5.0, 10.0), (10.0, 20.0), (20.0, None)]
    bands = []
    for lower, upper in limits:
        count = sum(
            employees
            for distance, employees in distances
            if distance >= lower and (upper is None or distance < upper)
        )
        bands.append([lower, upper, count])

    while len(bands) > 1 and any(int(band[2]) < MINIMUM_COHORT for band in bands):
        smallest_index = min(range(len(bands)), key=lambda index: int(bands[index][2]))
        if smallest_index == 0:
            merge_index = 1
        elif smallest_index == len(bands) - 1:
            merge_index = smallest_index - 1
        else:
            left_count = int(bands[smallest_index - 1][2])
            right_count = int(bands[smallest_index + 1][2])
            merge_index = smallest_index - 1 if left_count <= right_count else smallest_index + 1
        first = min(smallest_index, merge_index)
        second = max(smallest_index, merge_index)
        bands[first][1] = bands[second][1]
        bands[first][2] = int(bands[first][2]) + int(bands[second][2])
        del bands[second]
    return [(float(lower), upper, int(count)) for lower, upper, count in bands]


def band_label(lower: float, upper: float | None) -> str:
    if upper is None:
        return f"{lower:g}+ km"
    return f"{lower:g}–<{upper:g} km"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    query_payload, query_result_sha256 = query_zip_hash_counts()
    query_rows = query_payload.get("rows", [])
    if not isinstance(query_rows, list):
        raise ValueError("La respuesta de Redshift no contiene filas agregadas.")
    centroids, reference_sha256, reference_rows = download_postal_reference()

    distances: list[tuple[float, int]] = []
    matched_employees = 0
    unmatched_employees = 0
    unmatched_hashes = 0
    for row in query_rows:
        postal_hash = str(row["postal_hash"])
        employee_count = int(row["employee_count"])
        # The reference is keyed by a hash so the residential ZIP itself never
        # leaves the local process or enters the evidence artifact.
        matched = None
        for postal, centroid in centroids.items():
            if hashlib.md5(postal.encode("utf-8")).hexdigest() == postal_hash:
                matched = centroid
                break
        if matched is None:
            unmatched_hashes += 1
            unmatched_employees += employee_count
            continue
        distances.append((haversine_km(*matched), employee_count))
        matched_employees += employee_count

    if not distances:
        raise ValueError("No se encontró ningún centroid matching para Mexico City.")
    bands = candidate_bands(distances)
    distribution = [
        {"category": band_label(lower, upper), "employee_count": count}
        for lower, upper, count in bands
    ]
    published_count = sum(item["employee_count"] for item in distribution)
    min_published = min(item["employee_count"] for item in distribution)
    coverage_percent = 100.0 * matched_employees / 90
    outcome = (
        "pass"
        if coverage_percent >= 95.0
        and published_count == matched_employees
        and min_published >= MINIMUM_COHORT
        else "fail"
    )

    evidence = {
        "artifact": "internal_analysis",
        "variable": "Commute distance",
        "snapshot_date": SNAPSHOT,
        "population": "Regular active employees in Mexico City",
        "grain": "Distinct employee snapshot",
        "office_reference": {
            "source_url": "https://www.qualcomm.com/company/facilities/offices",
            "model_url": "https://www.qualcomm.com/company/facilities/offices.model.json",
            "location": "Mexico City",
            "postal_code": "11000",
            "latitude": OFFICE_LAT,
            "longitude": OFFICE_LON,
            "retrieved_date": "2026-09-08",
        },
        "residential_reference": {
            "source_url": POSTAL_REFERENCE_URL,
            "dataset": "GeoNames postal-code coordinates mirrored by symerio",
            "retrieved_date": "2026-09-08",
            "reference_sha256": reference_sha256,
            "source_rows_read": reference_rows,
        },
        "method": {
            "distance": "Haversine distance between residential ZIP centroid and Qualcomm office coordinate",
            "unit": "kilometers",
            "interpretation": "Geographic approximation; not route distance, travel time, or actual commute",
            "residential_zip_handling": "ZIP values are queried as MD5 hashes and never written to the artifact",
        },
        "distribution": distribution,
        "metrics": {
            "eligible_employees": 90,
            "postal_observable_employees": 90,
            "postal_missing_employees": 0,
            "matched_centroid_employees": matched_employees,
            "unmatched_centroid_employees": unmatched_employees,
            "unmatched_postal_hashes": unmatched_hashes,
            "centroid_coverage_percent": round(coverage_percent, 4),
            "published_employee_count": published_count,
            "minimum_published_category": min_published,
            "query_result_sha256": query_result_sha256,
            "minimum_cohort": MINIMUM_COHORT,
            "outcome": outcome,
        },
        "acceptance_rule": "La cobertura de centroides debe ser >=95%; las bandas publicadas suman la cohorte cubierta y cada banda tiene n>=30. Los empleados sin match no se imputan ni se publican como bucket.",
        "query_reference": "queries/profiles/commute_distance_mexico_city_zip_hash_distribution_20260908.sql",
        "coverage_audit_reference": "queries/audits/commute_distance_mexico_city_input_coverage_20260908.sql",
    }
    if outcome != "pass":
        raise ValueError(json.dumps(evidence["metrics"], ensure_ascii=False))
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "metrics": evidence["metrics"], "distribution": distribution}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
