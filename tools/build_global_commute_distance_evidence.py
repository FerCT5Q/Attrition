"""Build global one-kilometre commute-distance evidence without exporting ZIPs.

Employee ZIPs and office-site codes are queried only as hashes. Public office
and postal-centroid catalogs are joined locally in memory. The persisted output
contains aggregate bands, coverage metrics, and source hashes only.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import unicodedata
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import urllib3


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "queries" / "profiles" / "commute_distance_global_zip_hash_distribution_20260908.sql"
COVERAGE_SQL_PATH = ROOT / "queries" / "audits" / "commute_distance_global_input_coverage_20260908.sql"
OFFICE_CATALOG = ROOT / "output" / "distribution" / "json" / "qualcomm-office-locations-catalog-20260908.json"
SNAPSHOT = "2026-09-27"
MINIMUM_COHORT = 30
QUERY_HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
ELIGIBLE_EMPLOYEES = 50_218
POSTAL_BASE_URL = "https://symerio.github.io/postal-codes-data/data/geonames/{country}.txt"
POSTAL_CACHE_DIR = ROOT / "references" / "geonames-postal-centroids"

COUNTRY_ISO_RAW = {
    "AUSTRALIA": "AU", "AUSTRIA": "AT", "BELGIUM": "BE", "BRAZIL": "BR",
    "CANADA": "CA", "CHINA": "CN", "FINLAND": "FI", "FRANCE": "FR",
    "GERMANY": "DE", "GREECE": "GR", "INDIA": "IN", "INDONESIA": "ID",
    "IRELAND": "IE", "ITALY": "IT", "JAPAN": "JP", "MEXICO": "MX",
    "NETHERLANDS": "NL", "NORWAY": "NO", "PEOPLES REPUBLIC OF CHINA": "CN",
    "ROMANIA": "RO", "SINGAPORE": "SG", "SOUTH KOREA": "KR", "SPAIN": "ES",
    "SWEDEN": "SE", "SWITZERLAND": "CH", "UNITED KINGDOM": "GB", "USA": "US",
    "VIETNAM": "VN",
}


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]+", "", text.upper())


COUNTRY_ISO = {normalize(country): code for country, code in COUNTRY_ISO_RAW.items()}

# HRDA and the official Qualcomm catalog use different country labels for a
# few countries. Normalize those labels before matching city/country pairs.
COUNTRY_ALIASES = {
    normalize("United States of America"): normalize("USA"),
    normalize("China"): normalize("Peoples Republic of China"),
    normalize("Korea, Republic of"): normalize("South Korea"),
}


def canonical_country(value: object) -> str:
    normalized = normalize(value)
    return COUNTRY_ALIASES.get(normalized, normalized)


def md5(value: object) -> str:
    return hashlib.md5(str(value).strip().upper().encode("utf-8")).hexdigest()


def load_offices() -> tuple[list[dict[str, object]], str]:
    raw = OFFICE_CATALOG.read_bytes()
    catalog_sha256 = hashlib.sha256(raw).hexdigest()
    offices = json.loads(raw.decode("utf-8"))
    cleaned: list[dict[str, object]] = []
    for office in offices:
        latitude = float(office["latitude"])
        longitude = float(office["longitude"])
        if not (-90 <= latitude <= 90) and -90 <= longitude <= 90 and -180 <= latitude <= 180:
            latitude, longitude = longitude, latitude
        # The page contains a duplicate TIJNA.Z record with longitude -110,
        # although the same office is listed at -117.0439505. Use the valid
        # Tijuana coordinate and retain the anomaly in the source evidence.
        if str(office.get("officeCode", "")).upper() == "TIJNA.Z":
            latitude, longitude = 32.4373533, -117.0439505
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue
        record = dict(office)
        record["latitude"] = latitude
        record["longitude"] = longitude
        record["country_norm"] = canonical_country(office.get("country"))
        record["locality_norm"] = normalize(office.get("locality"))
        cleaned.append(record)
    return cleaned, catalog_sha256


def query_employee_hashes(
    sql_path: Path = SQL_PATH,
    coverage_sql_path: Path = COVERAGE_SQL_PATH,
) -> tuple[list[dict[str, object]], str, dict[str, int]]:
    def run_aggregate(sql_source: Path | str, max_rows: int) -> list[dict[str, object]]:
        source_args = ["--sql-file", str(sql_source)] if isinstance(sql_source, Path) else ["--sql", sql_source]
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(QUERY_HELPER),
                *source_args,
                "--max-rows",
                str(max_rows),
                "--reporting-mode",
                "internal_analysis",
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
        if payload.get("truncated"):
            raise ValueError("La consulta agregada de commute fue truncada.")
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise ValueError("La consulta agregada de commute no devolvio filas.")
        return [dict(row) for row in rows]

    profile_sql = sql_path.read_text(encoding="utf-8")
    partition_anchor = "      AND active_status = 1\n),\neligible AS"
    if partition_anchor not in profile_sql:
        raise ValueError("La consulta de commute no tiene el ancla esperada para particionar hashes.")

    def partition_sql(bucket: int) -> str:
        predicate = (
            "      AND active_status = 1\n"
            "      AND MOD(MOD(FNV_HASH(CAST(employee_id AS VARCHAR(64))), 32) + 32, 32) = "
            f"{bucket}\n),\neligible AS"
        )
        return profile_sql.replace(partition_anchor, predicate, 1)

    # The protected query helper caps a single result at 1,000 aggregate
    # rows. Hash partitions keep the retained SQL aggregate-only and sum to
    # the same snapshot without exporting postal or employee values.
    with ThreadPoolExecutor(max_workers=8) as executor:
        partition_rows = list(executor.map(lambda bucket: run_aggregate(partition_sql(bucket), max_rows=1000), range(32)))
    rows = [row for partition in partition_rows for row in partition]
    coverage_rows = run_aggregate(coverage_sql_path, max_rows=2)
    if len(coverage_rows) != 1:
        raise ValueError("La auditoria de cobertura de commute debe devolver una sola fila agregada.")
    coverage_row = coverage_rows[0]
    result_sha256 = hashlib.sha256(
        json.dumps(rows, sort_keys=True, default=str, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    coverage = {key: int(value or 0) for key, value in coverage_row.items()}
    return rows, result_sha256, coverage


def postal_variants(value: str, country_code: str) -> set[str]:
    raw = str(value).strip().upper()
    compact = re.sub(r"[^A-Z0-9]", "", raw)
    variants = {raw, compact}
    if country_code == "US":
        variants.add(raw.split("-")[0])
        variants.add(re.sub(r"[^0-9]", "", raw)[:5])
    if country_code in {"CA", "IE"} and len(compact) >= 3:
        variants.add(compact[:3])
    if country_code == "GB":
        variants.update(compact[:length] for length in (2, 3, 4) if len(compact) >= length)
    if country_code == "NL" and len(compact) >= 4:
        variants.add(compact[:4])
    numeric = compact.isdigit()
    zero_pad_width = {
        "CN": 6,
        "DE": 5,
        "FR": 5,
        "IN": 6,
        "JP": 7,
        "KR": 5,
        "SG": 6,
    }.get(country_code)
    if numeric and zero_pad_width and len(compact) <= zero_pad_width:
        variants.add(compact.zfill(zero_pad_width))
    return {variant for variant in variants if variant}


def query_postal_hashes(row: dict[str, object], country_code: str) -> list[str]:
    """Return only precomputed hash variants; raw postal values never leave SQL."""
    fields = ["postal_hash", "postal_hash_compact"]
    if country_code in {"CA", "IE"}:
        fields.append("postal_hash_prefix_3")
    elif country_code == "GB":
        fields.extend(["postal_hash_prefix_2", "postal_hash_prefix_3", "postal_hash_prefix_4"])
    elif country_code == "NL":
        fields.append("postal_hash_prefix_4")
    zero_pad_width = {
        "CN": "postal_hash_zero_pad_6",
        "DE": "postal_hash_zero_pad_5",
        "FR": "postal_hash_zero_pad_5",
        "IN": "postal_hash_zero_pad_6",
        "JP": "postal_hash_zero_pad_7",
        "KR": "postal_hash_zero_pad_5",
        "SG": "postal_hash_zero_pad_6",
    }.get(country_code)
    if zero_pad_width:
        fields.append(zero_pad_width)
    return [str(row[field]) for field in fields if row.get(field)]


def download_centroids(country_code: str) -> tuple[dict[str, tuple[float, float]], str, int]:
    archive = POSTAL_CACHE_DIR / f"{country_code}.zip"
    if archive.exists():
        raw_archive = archive.read_bytes()
        with zipfile.ZipFile(io.BytesIO(raw_archive)) as package:
            members = [name for name in package.namelist() if name.upper().endswith(f"{country_code}.TXT")]
            if len(members) != 1:
                raise ValueError(f"El cache GeoNames de {country_code} no contiene un unico archivo de datos.")
            raw = package.read(members[0])
        source_hash = hashlib.sha256(raw_archive).hexdigest()
        text = raw.decode("utf-8", errors="replace")
    else:
        # Kept as a fallback for a newly introduced office country. Existing
        # V7 countries use the repository's versioned GeoNames cache.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(POSTAL_BASE_URL.format(country=country_code), timeout=120, verify=False)
        response.raise_for_status()
        raw = response.content
        source_hash = hashlib.sha256(raw).hexdigest()
        text = response.text
    by_hash: dict[str, list[tuple[float, float]]] = defaultdict(list)
    source_rows = 0
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 11:
            continue
        try:
            postal = parts[1].strip().upper()
            latitude = float(parts[9])
            longitude = float(parts[10])
        except (TypeError, ValueError):
            continue
        if not postal or not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue
        source_rows += 1
        for variant in postal_variants(postal, country_code):
            by_hash[md5(variant)].append((latitude, longitude))
    centroids = {
        postal_hash: (
            sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points),
        )
        for postal_hash, points in by_hash.items()
    }
    return centroids, source_hash, source_rows


def office_candidates(offices: list[dict[str, object]]) -> tuple[dict[str, list[dict[str, object]]], dict[tuple[str, str], list[dict[str, object]]]]:
    by_alias: dict[str, list[dict[str, object]]] = defaultdict(list)
    by_city: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for office in offices:
        aliases = {office.get("officeCode", ""), office.get("name", "")}
        for alias in aliases:
            if str(alias).strip():
                by_alias[md5(alias)].append(office)
        by_city[(str(office["country_norm"]), str(office["locality_norm"]))].append(office)
    return by_alias, by_city


def choose_offices(row: dict[str, object], by_alias, by_city, offices) -> tuple[list[dict[str, object]], str]:
    alias_matches = by_alias.get(str(row["office_hash"]), [])
    if alias_matches:
        return alias_matches, "office_site"
    country_norm = canonical_country(row["country_label"])
    city_norm = normalize(row["city_label"])
    direct = by_city.get((country_norm, city_norm), [])
    if direct:
        return direct, "city_country"
    # Conservative locality fallback for labels such as "San Jose, CA" or
    # "Guangzhou" versus "Guangzhou City". It is only used when unique.
    candidates = [
        office for office in offices
        if office["country_norm"] == country_norm
        and (city_norm in office["locality_norm"] or office["locality_norm"] in city_norm)
    ]
    return candidates, "city_country_fuzzy" if candidates else "unmatched"


def haversine_km(latitude: float, longitude: float, office: dict[str, object]) -> float:
    radius = 6371.0088
    lat1, lon1, lat2, lon2 = map(
        math.radians,
        (latitude, longitude, float(office["latitude"]), float(office["longitude"])),
    )
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def privacy_bands(distances: list[tuple[float, int]]) -> list[tuple[int, int | None, int]]:
    if not distances:
        return []
    highest = max(int(math.floor(distance)) for distance, _ in distances)
    counts = [0] * (highest + 1)
    for distance, employee_count in distances:
        counts[int(math.floor(distance))] += employee_count
    bands: list[list[int | None]] = [
        [index, index + 1, count] for index, count in enumerate(counts) if count > 0
    ]
    while len(bands) > 1 and any(int(band[2]) < MINIMUM_COHORT for band in bands):
        smallest = min(range(len(bands)), key=lambda index: int(bands[index][2]))
        if smallest == 0:
            neighbor = 1
        elif smallest == len(bands) - 1:
            neighbor = smallest - 1
        else:
            neighbor = smallest - 1 if int(bands[smallest - 1][2]) <= int(bands[smallest + 1][2]) else smallest + 1
        first, second = sorted((smallest, neighbor))
        bands[first][1] = bands[second][1]
        bands[first][2] = int(bands[first][2]) + int(bands[second][2])
        del bands[second]
    return [(int(lower), int(upper) if upper is not None else None, int(count)) for lower, upper, count in bands]


def band_label(lower: int, upper: int | None) -> str:
    return f"{lower}–<{upper} km" if upper is not None else f"{lower}+ km"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--sql-file", default=str(SQL_PATH))
    parser.add_argument("--coverage-sql-file", default=str(COVERAGE_SQL_PATH))
    parser.add_argument("--snapshot", default=SNAPSHOT, help="Fiscal monthly snapshot (YYYY-MM-DD).")
    parser.add_argument("--allow-warning", action="store_true")
    args = parser.parse_args()

    sql_path = Path(args.sql_file).resolve()
    coverage_sql_path = Path(args.coverage_sql_file).resolve()
    snapshot = str(args.snapshot)
    if snapshot != SNAPSHOT:
        audit_dir = ROOT / "queries" / "audits"
        audit_dir.mkdir(parents=True, exist_ok=True)
        sql_target = audit_dir / f"v7_commute_distance_global_zip_hash_distribution_{snapshot.replace('-', '')}.sql"
        coverage_target = audit_dir / f"v7_commute_distance_global_input_coverage_{snapshot.replace('-', '')}.sql"
        for source, target in ((sql_path, sql_target), (coverage_sql_path, coverage_target)):
            text = source.read_text(encoding="utf-8")
            required = "DATE '2026-09-27'"
            if required not in text:
                raise ValueError(f"La fuente {source.name} no tiene el corte esperado para materializar {snapshot}.")
            target.write_text(text.replace(required, f"DATE '{snapshot}'"), encoding="utf-8")
        sql_path, coverage_sql_path = sql_target, coverage_target
    rows, query_result_sha256, coverage = query_employee_hashes(sql_path, coverage_sql_path)
    offices, office_catalog_sha256 = load_offices()
    by_alias, by_city = office_candidates(offices)

    destination_by_row: list[tuple[dict[str, object], list[dict[str, object]], str]] = []
    needed_countries: set[str] = set()
    for row in rows:
        candidates, resolution = choose_offices(row, by_alias, by_city, offices)
        destination_by_row.append((row, candidates, resolution))
        for candidate in candidates:
            code = COUNTRY_ISO.get(canonical_country(candidate["country"]))
            if code:
                needed_countries.add(code)

    centroid_by_country: dict[str, dict[str, tuple[float, float]]] = {}
    source_manifest: dict[str, dict[str, object]] = {}
    for country_code in sorted(needed_countries):
        try:
            centroids, source_hash, source_rows = download_centroids(country_code)
        except requests.RequestException:
            continue
        centroid_by_country[country_code] = centroids
        source_manifest[country_code] = {
            "source_url": POSTAL_BASE_URL.format(country=country_code),
            "sha256": source_hash,
            "source_rows_read": source_rows,
        }

    has_work_arrangement = "onsite_flag" in rows[0] if rows else False
    distances: list[tuple[float, int]] = []
    onsite_distances: list[tuple[float, int]] = []
    matched_employees = 0
    onsite_matched_employees = 0
    office_site_resolved_employees = 0
    fallback_resolved_employees = 0
    unmatched_office_employees = 0
    unmatched_centroid_employees = 0
    onsite_unmatched_office_employees = 0
    onsite_unmatched_centroid_employees = 0
    unresolved_rows = 0
    country_coverage: dict[str, dict[str, int]] = defaultdict(
        lambda: {"eligible": 0, "matched": 0, "unmatched_office": 0, "unmatched_centroid": 0}
    )
    for row, candidates, resolution in destination_by_row:
        count = int(row["employee_count"])
        onsite_flag = int(row.get("onsite_flag", 0) or 0)
        country_name = str(row["country_label"])
        country_coverage[country_name]["eligible"] += count
        if not candidates:
            unresolved_rows += 1
            unmatched_office_employees += count
            if onsite_flag:
                onsite_unmatched_office_employees += count
            country_coverage[country_name]["unmatched_office"] += count
            continue
        centroid_candidates: list[tuple[float, dict[str, object]]] = []
        for office in candidates:
            country_code = COUNTRY_ISO.get(canonical_country(office["country"]))
            postal_hashes = query_postal_hashes(row, country_code or "")
            centroid_map = centroid_by_country.get(country_code or "", {})
            for postal_hash in postal_hashes:
                centroid = centroid_map.get(postal_hash)
                if centroid is not None:
                    centroid_candidates.append((haversine_km(*centroid, office), office))
                    break
        if not centroid_candidates:
            unmatched_centroid_employees += count
            if onsite_flag:
                onsite_unmatched_centroid_employees += count
            country_coverage[country_name]["unmatched_centroid"] += count
            continue
        distance, _ = min(centroid_candidates, key=lambda item: item[0])
        distances.append((distance, count))
        if onsite_flag:
            onsite_distances.append((distance, count))
            onsite_matched_employees += count
        matched_employees += count
        country_coverage[country_name]["matched"] += count
        if resolution == "office_site":
            office_site_resolved_employees += count
        else:
            fallback_resolved_employees += count

    bands = privacy_bands(distances)
    distribution = [
        {
            "category": band_label(lower, upper),
            "lower_km": lower,
            "upper_km": upper,
            "employee_count": count,
        }
        for lower, upper, count in bands
    ]
    onsite_distribution = None
    onsite_metrics = None
    if has_work_arrangement:
        onsite_bands = privacy_bands(onsite_distances)
        onsite_distribution = [
            {
                "category": band_label(lower, upper),
                "lower_km": lower,
                "upper_km": upper,
                "employee_count": count,
            }
            for lower, upper, count in onsite_bands
        ]
        onsite_eligible = int(coverage.get("onsite_employee_groups", 0))
        onsite_published_count = sum(item["employee_count"] for item in onsite_distribution)
        onsite_unavailable_count = onsite_eligible - onsite_matched_employees
        onsite_coverage_percent = 100.0 * onsite_matched_employees / onsite_eligible if onsite_eligible else 0.0
        onsite_complete_location = int(coverage.get("onsite_complete_location_employees", 0))
        onsite_complete_coverage_percent = (
            100.0 * onsite_matched_employees / onsite_complete_location
            if onsite_complete_location else 0.0
        )
        onsite_outcome = "pass" if (
            onsite_unavailable_count >= MINIMUM_COHORT
            and onsite_published_count == onsite_matched_employees
            and onsite_matched_employees + onsite_unavailable_count == onsite_eligible
            and onsite_distribution
            and all(item["employee_count"] >= MINIMUM_COHORT for item in onsite_distribution)
        ) else "warning"
        onsite_metrics = {
            "eligible_employees": onsite_eligible,
            "postal_observable_employees": int(coverage.get("onsite_postal_observable_employees", 0)),
            "office_observable_employees": int(coverage.get("onsite_office_observable_employees", 0)),
            "complete_location_employees": onsite_complete_location,
            "matched_distance_employees": onsite_matched_employees,
            "unmatched_office_employees": onsite_unmatched_office_employees,
            "unmatched_centroid_employees": onsite_unmatched_centroid_employees,
            "coverage_percent_of_eligible": round(onsite_coverage_percent, 4),
            "coverage_percent_of_complete_location": round(onsite_complete_coverage_percent, 4),
            "published_employee_count": onsite_published_count,
            "unavailable_employee_count": onsite_unavailable_count,
            "minimum_published_category": min((item["employee_count"] for item in onsite_distribution), default=0),
            "published_categories": len(onsite_distribution),
            "minimum_cohort": MINIMUM_COHORT,
            "outcome": onsite_outcome,
        }
    published_count = sum(item["employee_count"] for item in distribution)
    denominator = coverage["eligible_employees"]
    coverage_percent = 100.0 * matched_employees / denominator if denominator else 0.0
    complete_location_estimate = coverage["complete_location_employees"]
    complete_coverage_percent = 100.0 * matched_employees / complete_location_estimate if complete_location_estimate else 0.0
    unavailable_employee_count = denominator - matched_employees
    overall_outcome = "pass" if (
        unavailable_employee_count >= MINIMUM_COHORT
        and published_count == matched_employees
        and matched_employees + unavailable_employee_count == denominator
        and all(item["employee_count"] >= MINIMUM_COHORT for item in distribution)
    ) else "warning"
    outcome = "pass" if overall_outcome == "pass" and (onsite_metrics is None or onsite_metrics["outcome"] == "pass") else "warning"
    evidence = {
        "artifact": "internal_analysis",
        "variable": "Commute distance",
        "snapshot_date": snapshot,
        "population": "All regular active employees",
        "grain": "Distinct employee snapshot",
        "office_reference": {
            "source_url": "https://www.qualcomm.com/company/facilities/offices",
            "model_url": "https://www.qualcomm.com/company/facilities/offices.model.json",
            "retrieved_date": "2026-09-08",
            "catalog_locations": len(offices),
            "catalog_sha256": office_catalog_sha256,
            "destination_rule": "office_site hash first; city/country fallback only when office_site is not in the catalog; nearest candidate office used when a city has multiple records",
        },
        "residential_reference": {
            "dataset": "GeoNames postal-code coordinates mirrored by symerio",
            "retrieved_date": "2026-09-08",
            "country_sources": source_manifest,
        },
        "method": {
            "distance": "Haversine distance between residential postal centroid and Qualcomm office coordinate",
            "unit": "kilometers",
            "binning": "floor(distance_km) into one-kilometre intervals before privacy coalescing",
            "interpretation": "Geographic approximation; not route distance, travel time, or actual commute",
            "residential_zip_handling": "postal_code queried as MD5 hash and never written to the artifact",
        },
        "distribution": distribution,
        "onsite_distribution": onsite_distribution,
        "work_arrangement": {
            "onsite_definition": "UPPER(TRIM(work_arrangement)) = 'ONSITE'",
            "onsite_employee_count": int(coverage.get("onsite_employee_groups", 0)),
            "not_onsite_or_unknown_employee_count": int(coverage.get("not_onsite_or_unknown_groups", 0)),
            "missing_work_arrangement_employee_count": int(coverage.get("missing_work_arrangement_groups", 0)),
            "population_reconciliation_gap": int(coverage.get("eligible_employee_groups", 0)) - int(coverage.get("onsite_employee_groups", 0)) - int(coverage.get("not_onsite_or_unknown_groups", 0)),
        },
        "metrics": {
            "eligible_employees": coverage["eligible_employees"],
            "postal_observable_employees": coverage["postal_observable_employees"],
            "office_observable_employees": coverage["office_observable_employees"],
            "postal_missing_employees": coverage["postal_missing_employees"],
            "office_missing_employees": coverage["office_missing_employees"],
            "multirow_employees": coverage["multirow_employees"],
            "max_postal_values_per_employee": coverage["max_postal_values_per_employee"],
            "max_office_values_per_employee": coverage["max_office_values_per_employee"],
            "complete_location_employees": complete_location_estimate,
            "matched_distance_employees": matched_employees,
            "office_site_resolved_employees": office_site_resolved_employees,
            "fallback_resolved_employees": fallback_resolved_employees,
            "unmatched_office_employees": unmatched_office_employees,
            "unmatched_centroid_employees": unmatched_centroid_employees,
            "unresolved_query_groups": unresolved_rows,
            "coverage_percent_of_eligible": round(coverage_percent, 4),
            "coverage_percent_of_complete_location": round(complete_coverage_percent, 4),
            "published_employee_count": published_count,
            "unavailable_employee_count": unavailable_employee_count,
            "minimum_published_category": min((item["employee_count"] for item in distribution), default=0),
            "published_categories": len(distribution),
            "minimum_cohort": MINIMUM_COHORT,
            "query_result_sha256": query_result_sha256,
            "outcome": outcome,
            "onsite": onsite_metrics,
            "country_coverage": [
                {"country": country, **values}
                for country, values in sorted(country_coverage.items())
                if values["eligible"] >= MINIMUM_COHORT
            ],
        },
        "acceptance_rule": "Las bandas de distancia suman la población cubierta; el remanente se reporta como No calculable; cada categoría visible tiene n>=30; no se imputan ZIPs ni oficinas sin match.",
        "query_reference": str(sql_path.relative_to(ROOT)).replace("\\", "/"),
        "coverage_audit_reference": str(coverage_sql_path.relative_to(ROOT)).replace("\\", "/"),
    }
    if outcome != "pass" and not args.allow_warning:
        raise ValueError(json.dumps(evidence["metrics"], ensure_ascii=False))
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "snapshot_date": snapshot,
        "eligible_employees": evidence["metrics"]["eligible_employees"],
        "matched_distance_employees": evidence["metrics"]["matched_distance_employees"],
        "unavailable_employee_count": evidence["metrics"]["unavailable_employee_count"],
        "onsite_matched_distance_employees": (evidence["metrics"].get("onsite") or {}).get("matched_distance_employees"),
        "outcome": evidence["metrics"]["outcome"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
