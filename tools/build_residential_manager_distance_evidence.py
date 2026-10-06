"""Freeze aggregate-only employee-manager residential distance evidence.

The Redshift profile returns only aggregate counts grouped by one-way hashes of
postal-code variants.  Those hashes, the country labels needed to select a
GeoNames file, and public centroids exist only in this process.  The JSON
artifact contains bands, aggregate diagnostics, and SHA-256 provenance only.
It never contains employee records, identifiers, postal codes, pair hashes,
or public-centroid match keys.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import re
import unicodedata
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
import requests
import urllib3
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
PROFILE_SQL = ROOT / "queries" / "profiles" / "residential_manager_distance_postal_pair_hash_distribution_20260909.sql"
AUDIT_SQL = ROOT / "queries" / "audits" / "residential_manager_distance_snapshot_reconciliation_20260909.sql"
COUNTRY_MAPPING_AUDIT_SQL = ROOT / "queries" / "audits" / "residential_manager_distance_country_mapping_20260910.sql"
SNAPSHOT_DATE = "2026-08-23"
MINIMUM_COHORT = 30
EXPECTED_ACTIVE_REGULAR_EMPLOYEES = 50_043
EXPECTED_FEATURE_ELIGIBLE_PAIRS = 49_556
GEONAMES_URL = "https://download.geonames.org/export/zip/{country}.zip"
GEONAMES_MIRROR_URL = "https://symerio.github.io/postal-codes-data/data/geonames/{country}.txt"
CENTROID_CACHE = ROOT / "references" / "geonames-postal-centroids"


class PublicCentroidReferenceUnavailable(RuntimeError):
    """No public GeoNames postal centroid file is available for a country."""


COUNTRY_ISO_RAW = {
    "AUSTRALIA": "AU", "AUSTRIA": "AT", "BELGIUM": "BE", "BRAZIL": "BR",
    "CANADA": "CA", "CHINA": "CN", "FINLAND": "FI", "FRANCE": "FR",
    "GERMANY": "DE", "GREECE": "GR", "INDIA": "IN", "INDONESIA": "ID",
    "IRELAND": "IE", "ITALY": "IT", "JAPAN": "JP", "MEXICO": "MX",
    "NETHERLANDS": "NL", "NORWAY": "NO", "PEOPLES REPUBLIC OF CHINA": "CN",
    "ROMANIA": "RO", "SAUDI ARABIA": "SA", "SINGAPORE": "SG", "SOUTH KOREA": "KR", "SPAIN": "ES",
    "SWEDEN": "SE", "SWITZERLAND": "CH", "UNITED KINGDOM": "GB",
    "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US", "USA": "US",
    "US": "US", "TAIWAN": "TW", "ISRAEL": "IL", "VIETNAM": "VN",
}


def normalized(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^A-Z0-9]+", "", text.upper())


COUNTRY_ISO = {normalized(name): code for name, code in COUNTRY_ISO_RAW.items()}
COUNTRY_ALIASES = {
    normalized("China"): normalized("Peoples Republic of China"),
    normalized("Korea, Republic of"): normalized("South Korea"),
}


def country_code(value: object) -> str | None:
    key = COUNTRY_ALIASES.get(normalized(value), normalized(value))
    if key in COUNTRY_ISO:
        return COUNTRY_ISO[key]
    return key if key in set(COUNTRY_ISO.values()) else None


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_json(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8"))


def connect():
    env_path = os.getenv("ATTRITION_REDSHIFT_ENV")
    load_dotenv(env_path if env_path else Path(r"C:\Dev\Python\Slides\.env"))
    return psycopg2.connect(
        host=os.environ["REDSHIFT_HOST"],
        port=int(os.getenv("REDSHIFT_PORT", "5439")),
        dbname=os.environ["REDSHIFT_DATABASE"],
        user=os.environ["REDSHIFT_USER"],
        password=os.environ["REDSHIFT_PASSWORD"],
        sslmode=os.getenv("REDSHIFT_SSLMODE", "require"),
        connect_timeout=int(os.getenv("REDSHIFT_CONNECT_TIMEOUT", "30")),
    )


def query_rows(sql_path: Path) -> tuple[list[dict[str, Any]], str, str]:
    """Execute saved read-only SQL without printing the in-memory hash rows."""
    sql = sql_path.read_text(encoding="utf-8")
    with connect() as connection:
        connection.autocommit = True
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(sql)
            rows = [dict(row) for row in cursor.fetchall()]
    return rows, sha256_bytes(sql.encode("utf-8")), hash_json(rows)


def check_audit(audit: dict[str, Any]) -> dict[str, int]:
    required = {
        "active_regular_employees",
        "employee_duplicate_source_rows",
        "employee_manager_conflicts",
        "employees_without_one_manager",
        "employee_postal_code_conflicts",
        "employee_country_conflicts",
        "unmatched_managers",
        "manager_duplicate_source_rows",
        "manager_postal_code_conflicts",
        "manager_country_conflicts",
        "feature_eligible_pairs",
        "key_unavailable_employees",
    }
    missing = sorted(required - set(audit))
    if missing:
        raise ValueError(f"Reconciliation audit is missing fields: {', '.join(missing)}")
    if str(audit.get("snapshot_date")) != SNAPSHOT_DATE:
        raise ValueError("Reconciliation audit did not return the fixed 2026-08-23 snapshot.")
    metrics = {key: int(audit[key] or 0) for key in required}
    if metrics["active_regular_employees"] != EXPECTED_ACTIVE_REGULAR_EMPLOYEES:
        raise ValueError("The fixed active-regular workforce does not match the approved 23-Aug-2026 population.")
    if metrics["feature_eligible_pairs"] != EXPECTED_FEATURE_ELIGIBLE_PAIRS:
        raise ValueError("The fixed feature-eligible pair count does not match the availability-audit precondition.")
    if metrics["active_regular_employees"] != metrics["feature_eligible_pairs"] + metrics["key_unavailable_employees"]:
        raise ValueError("Feature eligibility and unavailable keys do not reconcile to the active regular workforce.")
    safeguards = (
        "employee_duplicate_source_rows",
        "employee_manager_conflicts",
        "employee_postal_code_conflicts",
        "employee_country_conflicts",
        "unmatched_managers",
        "manager_duplicate_source_rows",
        "manager_postal_code_conflicts",
        "manager_country_conflicts",
    )
    failed = [metric for metric in safeguards if metrics[metric] != 0]
    if failed:
        raise ValueError(f"Same-snapshot manager safeguards failed: {', '.join(failed)}")
    if metrics["feature_eligible_pairs"] < MINIMUM_COHORT:
        raise ValueError("The feature-eligible employee-manager population is below the privacy minimum.")
    return metrics


def postal_variants(postal: str, country: str) -> set[str]:
    raw = postal.strip().upper()
    compact = re.sub(r"[^A-Z0-9]", "", raw)
    variants = {raw, compact}
    if country == "US":
        variants.add(raw.split("-")[0])
        variants.add(re.sub(r"[^0-9]", "", raw)[:5])
    if country in {"CA", "IE"} and len(compact) >= 3:
        variants.add(compact[:3])
    if country == "GB":
        variants.update(compact[:length] for length in (2, 3, 4) if len(compact) >= length)
    if country == "NL" and len(compact) >= 4:
        variants.add(compact[:4])
    zero_pad_width = {
        "CN": 6, "DE": 5, "FR": 5, "IN": 6, "JP": 7, "KR": 5, "SG": 6,
    }.get(country)
    if compact.isdigit() and zero_pad_width and len(compact) <= zero_pad_width:
        variants.add(compact.zfill(zero_pad_width))
    return {variant for variant in variants if variant}


def md5(value: str) -> str:
    return hashlib.md5(value.strip().upper().encode("utf-8")).hexdigest()


def download_centroid_source(country: str) -> tuple[bytes, dict[str, str]]:
    """Download one public postal-centroid source without any HR data in the request."""
    # The managed corporate proxy terminates TLS with an internal certificate
    # unavailable to this local virtual environment. This GET contains only a
    # public country-code URL; no HR value, postal proxy, or pair hash leaves
    # the process. Preserve the downloaded-source SHA-256 in the evidence.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    source_url = GEONAMES_URL.format(country=country)
    response = requests.get(source_url, timeout=120, verify=False)
    if response.status_code == 200:
        raw_source = response.content
        source_format = "GeoNames country ZIP"
        filename = f"{country}.zip"
    elif response.status_code == 404:
        # A small number of country ZIPs are not published at the official
        # endpoint. The fallback is a public static mirror of the same
        # GeoNames postal-coordinate file; its source URL and hash are frozen.
        source_url = GEONAMES_MIRROR_URL.format(country=country)
        mirror_response = requests.get(source_url, timeout=120, verify=False)
        if mirror_response.status_code == 404:
            raise PublicCentroidReferenceUnavailable(
                f"No public GeoNames postal-centroid file is available for {country}."
            )
        mirror_response.raise_for_status()
        raw_source = mirror_response.content
        source_format = "Public GeoNames postal-data mirror"
        filename = f"{country}.txt"
    else:
        response.raise_for_status()
        raise AssertionError("Unexpected GeoNames response status.")
    return raw_source, {
        "source_url": source_url,
        "sha256": sha256_bytes(raw_source),
        "source_format": source_format,
        "filename": filename,
    }


def source_text(country: str, raw_source: bytes, source_format: str) -> str:
    if source_format == "GeoNames country ZIP":
        with zipfile.ZipFile(io.BytesIO(raw_source)) as archive:
            member = next((name for name in archive.namelist() if name.upper().endswith(f"{country}.TXT")), None)
            if member is None:
                raise ValueError(f"GeoNames ZIP for {country} has no {country}.txt data file.")
            return archive.read(member).decode("utf-8", errors="replace")
    return raw_source.decode("utf-8", errors="replace")


def unavailable_marker_path(country: str, cache_dir: Path) -> Path:
    return cache_dir / f"{country}.unavailable.json"


def load_cached_source(country: str, cache_dir: Path) -> tuple[bytes, dict[str, str]] | None:
    unavailable_path = unavailable_marker_path(country, cache_dir)
    if unavailable_path.exists():
        marker = json.loads(unavailable_path.read_text(encoding="utf-8"))
        if marker.get("status") != "unavailable_public_geonames_reference":
            raise ValueError(f"Cached unavailable-source marker is invalid for {country}.")
        raise PublicCentroidReferenceUnavailable(
            f"Cached public GeoNames postal-centroid source is unavailable for {country}."
        )
    metadata_path = cache_dir / f"{country}.json"
    if not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    filename = metadata.get("filename")
    source_path = cache_dir / str(filename)
    if not source_path.exists():
        raise ValueError(f"Cached GeoNames source is missing for {country}.")
    raw_source = source_path.read_bytes()
    if sha256_bytes(raw_source) != metadata.get("sha256"):
        raise ValueError(f"Cached GeoNames source hash does not match metadata for {country}.")
    required = {"source_url", "sha256", "source_format", "filename"}
    if not required <= set(metadata):
        raise ValueError(f"Cached GeoNames metadata is incomplete for {country}.")
    return raw_source, {key: str(metadata[key]) for key in required}


def prefetch_centroid_sources(countries: list[str], cache_dir: Path) -> None:
    """Persist only public GeoNames source files; never any HR-derived values."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    for country in sorted(set(countries)):
        try:
            raw_source, metadata = download_centroid_source(country)
        except PublicCentroidReferenceUnavailable:
            # Persist only the public-source availability result.  This is not
            # HR-derived information and prevents a later evidence build from
            # attempting public network access for a known absent country file.
            unavailable_marker_path(country, cache_dir).write_text(
                json.dumps(
                    {
                        "status": "unavailable_public_geonames_reference",
                        "checked_on": date.today().isoformat(),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            print(f"No public GeoNames source available: {country}")
            continue
        (cache_dir / metadata["filename"]).write_bytes(raw_source)
        (cache_dir / f"{country}.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Cached public GeoNames source: {country}")


def load_centroids(country: str, cache_dir: Path) -> tuple[dict[str, tuple[float, float]], dict[str, object]]:
    """Load a public GeoNames source from cache, or download only if absent."""
    cached = load_cached_source(country, cache_dir)
    if cached is None:
        raw_source, source_metadata = download_centroid_source(country)
    else:
        raw_source, source_metadata = cached
    raw_text = source_text(country, raw_source, source_metadata["source_format"])

    source_rows = 0
    candidate_points: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for line in raw_text.splitlines():
        fields = line.split("\t")
        if len(fields) < 11:
            continue
        try:
            postal = fields[1]
            latitude = float(fields[9])
            longitude = float(fields[10])
        except (TypeError, ValueError):
            continue
        if not postal or not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue
        source_rows += 1
        for variant in postal_variants(postal, country):
            candidate_points[md5(variant)].append((latitude, longitude))

    centroids = {
        postal_hash: (
            sum(latitude for latitude, _ in points) / len(points),
            sum(longitude for _, longitude in points) / len(points),
        )
        for postal_hash, points in candidate_points.items()
    }
    if not centroids:
        raise ValueError(f"GeoNames ZIP for {country} yielded no usable postal centroids.")
    return centroids, {
        "source_url": source_metadata["source_url"],
        "sha256": source_metadata["sha256"],
        "source_format": source_metadata["source_format"],
        "source_rows_read": source_rows,
    }


def row_hash_candidates(row: dict[str, Any], party: str, country: str) -> list[str]:
    fields = [f"{party}_postal_hash", f"{party}_postal_hash_compact"]
    if country in {"CA", "IE"}:
        fields.append(f"{party}_postal_hash_prefix_3")
    elif country == "GB":
        fields.extend(f"{party}_postal_hash_prefix_{length}" for length in (2, 3, 4))
    elif country == "NL":
        fields.append(f"{party}_postal_hash_prefix_4")
    zero_pad_width = {
        "CN": 6, "DE": 5, "FR": 5, "IN": 6, "JP": 7, "KR": 5, "SG": 6,
    }.get(country)
    if zero_pad_width:
        fields.append(f"{party}_postal_hash_zero_pad_{zero_pad_width}")
    return [str(row[field]) for field in fields if row.get(field)]


def match_centroid(row: dict[str, Any], party: str, country: str, centroids: dict[str, tuple[float, float]]) -> tuple[float, float] | None:
    for postal_hash in row_hash_candidates(row, party, country):
        centroid = centroids.get(postal_hash)
        if centroid is not None:
            return centroid
    return None


def haversine_km(origin: tuple[float, float], destination: tuple[float, float]) -> float:
    latitude_1, longitude_1, latitude_2, longitude_2 = map(
        math.radians, (*origin, *destination)
    )
    delta_latitude = latitude_2 - latitude_1
    delta_longitude = longitude_2 - longitude_1
    a_value = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(latitude_1) * math.cos(latitude_2) * math.sin(delta_longitude / 2) ** 2
    )
    return 2 * 6371.0088 * math.asin(math.sqrt(a_value))


def privacy_bands(distances: list[tuple[float, int]]) -> list[tuple[int, int | None, int]]:
    """Coalesce adjacent 0-<30 km bins until every displayed band has n >= 30."""
    bins = [[lower, lower + 1, 0] for lower in range(30)]
    long_tail = 0
    for distance, employee_count in distances:
        bucket = int(math.floor(distance))
        if bucket >= 30:
            long_tail += employee_count
        else:
            bins[bucket][2] += employee_count

    while len(bins) > 1 and any(int(band[2]) < MINIMUM_COHORT for band in bins):
        candidate = min(range(len(bins)), key=lambda index: (int(bins[index][2]), index))
        if candidate == 0:
            neighbor = 1
        elif candidate == len(bins) - 1:
            neighbor = candidate - 1
        else:
            left = int(bins[candidate - 1][2])
            right = int(bins[candidate + 1][2])
            neighbor = candidate - 1 if left <= right else candidate + 1
        first, second = sorted((candidate, neighbor))
        bins[first][1] = bins[second][1]
        bins[first][2] = int(bins[first][2]) + int(bins[second][2])
        del bins[second]

    published = [(int(lower), int(upper), int(count)) for lower, upper, count in bins if int(count) > 0]
    if long_tail < MINIMUM_COHORT:
        raise ValueError("The 30+ km tail is below the privacy minimum and cannot be displayed safely.")
    published.append((30, None, long_tail))
    if not published or any(count < MINIMUM_COHORT for _, _, count in published):
        raise ValueError("At least one published residential-distance band is below n=30.")
    return published


def band_label(lower: int, upper: int | None) -> str:
    return f"{lower}+ km" if upper is None else f"{lower}\u2013<{upper} km"


def ensure_no_sensitive_keys(value: object) -> None:
    """Reject accidental persistence of restricted pair data or raw pair hashes."""
    prohibited_exact = {
        "employee_id",
        "manager_employee_id",
        "postal_code",
        "employee_postal_code",
        "manager_postal_code",
        "postal_hash",
        "employee_postal_hash",
        "manager_postal_hash",
        "pair_hash",
        "employee_name",
        "manager_name",
        "address",
        "home_address",
    }
    prohibited_prefixes = (
        "postal_hash_",
        "employee_postal_hash_",
        "manager_postal_hash_",
        "pair_hash_",
    )
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            # Aggregate safeguards such as manager_postal_code_conflicts are
            # allowed: they contain no postal value.  Reject actual raw-value
            # field names and hash variants instead of matching substrings.
            if lowered in prohibited_exact or lowered.startswith(prohibited_prefixes):
                raise ValueError(f"Frozen evidence attempted to persist prohibited field {key!r}.")
            ensure_no_sensitive_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            ensure_no_sensitive_keys(nested)


def build_evidence(cache_dir: Path = CENTROID_CACHE) -> dict[str, object]:
    audit_rows, audit_sql_sha256, audit_result_sha256 = query_rows(AUDIT_SQL)
    if len(audit_rows) != 1:
        raise ValueError("The reconciliation audit must return exactly one aggregate snapshot row.")
    audit_metrics = check_audit(audit_rows[0])

    country_mapping_rows, country_mapping_sql_sha256, country_mapping_result_sha256 = query_rows(COUNTRY_MAPPING_AUDIT_SQL)
    if not country_mapping_rows or any(country_code(row.get("country")) is None for row in country_mapping_rows):
        raise ValueError("A publishable country label is not mapped to an ISO country code for centroid matching.")

    pair_rows, query_sql_sha256, query_result_sha256 = query_rows(PROFILE_SQL)
    if not pair_rows:
        raise ValueError("The hashed postal-pair profile returned no feature-eligible aggregates.")
    if sum(int(row["employee_count"] or 0) for row in pair_rows) != audit_metrics["feature_eligible_pairs"]:
        raise ValueError("The hashed postal-pair profile does not reconcile to feature-eligible pairs.")

    requested_countries = {
        code
        for row in pair_rows
        for code in (country_code(row.get("employee_country")), country_code(row.get("manager_country")))
        if code
    }
    centroids_by_country: dict[str, dict[str, tuple[float, float]]] = {}
    reference_sources: dict[str, dict[str, object]] = {}
    unavailable_reference_countries: set[str] = set()
    for code in sorted(requested_countries):
        try:
            centroids, source = load_centroids(code, cache_dir)
        except PublicCentroidReferenceUnavailable:
            # The missing public reference is an observability limitation, not
            # a fallback to office data or another snapshot.  Such pairs stay
            # outside the distance distribution and are counted below.
            unavailable_reference_countries.add(code)
            continue
        centroids_by_country[code] = centroids
        reference_sources[code] = source

    distances: list[tuple[float, int]] = []
    employee_centroid_matched_pairs = 0
    manager_centroid_matched_pairs = 0
    observable_pairs = 0
    unrecognized_country_pairs = 0
    unavailable_reference_pairs = 0
    employee_centroid_unmatched_pairs = 0
    manager_centroid_unmatched_pairs = 0
    for row in pair_rows:
        employee_count = int(row["employee_count"] or 0)
        employee_country = country_code(row.get("employee_country"))
        manager_country = country_code(row.get("manager_country"))
        if not employee_country or not manager_country:
            unrecognized_country_pairs += employee_count
            continue
        if employee_country not in centroids_by_country or manager_country not in centroids_by_country:
            unavailable_reference_pairs += employee_count
            continue
        employee_centroid = match_centroid(row, "employee", employee_country, centroids_by_country[employee_country])
        manager_centroid = match_centroid(row, "manager", manager_country, centroids_by_country[manager_country])
        if employee_centroid is not None:
            employee_centroid_matched_pairs += employee_count
        else:
            employee_centroid_unmatched_pairs += employee_count
        if manager_centroid is not None:
            manager_centroid_matched_pairs += employee_count
        else:
            manager_centroid_unmatched_pairs += employee_count
        if employee_centroid is None or manager_centroid is None:
            continue
        distances.append((haversine_km(employee_centroid, manager_centroid), employee_count))
        observable_pairs += employee_count

    not_observable_pairs = audit_metrics["feature_eligible_pairs"] - observable_pairs
    if observable_pairs < MINIMUM_COHORT:
        raise ValueError("Fewer than 30 employee-manager pairs have calculable centroid distance.")
    if observable_pairs + not_observable_pairs != audit_metrics["feature_eligible_pairs"]:
        raise ValueError("Centroid observability does not reconcile to feature-eligible pairs.")
    bands = privacy_bands(distances)
    if sum(count for _, _, count in bands) != observable_pairs:
        raise ValueError("Published distance bands do not reconcile to calculable employee-manager pairs.")

    distribution = [
        {
            "category": band_label(lower, upper),
            "lower_km": lower,
            "upper_km": upper,
            "employee_count": count,
            "percent_of_calculable_pairs": round(100 * count / observable_pairs, 8),
        }
        for lower, upper, count in bands
    ]
    if not math.isclose(sum(row["percent_of_calculable_pairs"] for row in distribution), 100.0, abs_tol=1e-6):
        raise ValueError("Published distance percentages do not sum to 100% of calculable pairs.")

    active_regular_employees = audit_metrics["active_regular_employees"]
    total_unavailable = active_regular_employees - observable_pairs
    evidence: dict[str, object] = {
        "artifact": "internal_analysis",
        "variable": "Residential distance from manager",
        "execution_date": date.today().isoformat(),
        "snapshot_date": SNAPSHOT_DATE,
        "population": "Active regular employees with active same-snapshot manager matching",
        "grain": "Aggregate employee-manager pair at one monthly snapshot",
        "method": {
            "distance": "Haversine kilometers between employee and same-snapshot manager public postal-code centroids",
            "unit": "kilometers",
            "binning": "One-kilometer intervals through 30 km, dynamically coalesced with adjacent intervals until every displayed band has n >= 30; all remaining calculable pairs are 30+ km",
            "postal_proxy_handling": "Employee and manager postal-code variants are one-way hashed in Redshift, matched locally in memory, and never persisted in this evidence",
            "not_measured": ["travel time", "route distance", "office distance", "actual home address", "commute burden"],
        },
        "references": {
            "geonames_postal_centroids": {
                "dataset": "GeoNames postal-code coordinates",
                "access": "Public country ZIP downloads; source content used only in process memory",
            "country_sources": reference_sources,
            "unavailable_country_source_count": len(unavailable_reference_countries),
            },
        },
        "distribution": distribution,
        "metrics": {
            **audit_metrics,
            "observable_pairs": observable_pairs,
            "not_observable_pairs": not_observable_pairs,
            "total_unavailable_employees": total_unavailable,
            "employee_centroid_matched_pairs": employee_centroid_matched_pairs,
            "manager_centroid_matched_pairs": manager_centroid_matched_pairs,
            "employee_centroid_unmatched_pairs": employee_centroid_unmatched_pairs,
            "manager_centroid_unmatched_pairs": manager_centroid_unmatched_pairs,
            "unrecognized_country_pairs": unrecognized_country_pairs,
            "unavailable_reference_pairs": unavailable_reference_pairs,
            "calculable_coverage_percent_of_feature_eligible": round(100 * observable_pairs / audit_metrics["feature_eligible_pairs"], 8),
            "calculable_coverage_percent_of_active_workforce": round(100 * observable_pairs / active_regular_employees, 8),
            "published_pair_count": sum(row["employee_count"] for row in distribution),
            "published_band_count": len(distribution),
            "minimum_published_band_count": min(row["employee_count"] for row in distribution),
            "minimum_cohort": MINIMUM_COHORT,
            "country_mapping_categories_checked": len(country_mapping_rows),
        },
        "provenance": {
            "profile_sql": str(PROFILE_SQL.relative_to(ROOT)).replace("\\", "/"),
            "profile_sql_sha256": query_sql_sha256,
            "profile_result_sha256": query_result_sha256,
            "audit_sql": str(AUDIT_SQL.relative_to(ROOT)).replace("\\", "/"),
            "audit_sql_sha256": audit_sql_sha256,
            "audit_result_sha256": audit_result_sha256,
            "country_mapping_audit_sql": str(COUNTRY_MAPPING_AUDIT_SQL.relative_to(ROOT)).replace("\\", "/"),
            "country_mapping_audit_sql_sha256": country_mapping_sql_sha256,
            "country_mapping_audit_result_sha256": country_mapping_result_sha256,
        },
        "acceptance_rule": "Fixed active-workforce and feature-eligible counts reconcile; duplicate/conflict safeguards are zero; all publishable stored country labels map to an ISO centroid source; unrecognized or unavailable country references remain not observable rather than falling forward or using office data; observable + not observable equals feature eligible; every shown band has n >= 30; shown bands and percentages reconcile to calculable employee-manager pairs; no raw postal, employee, manager, address, or pair-hash value is persisted.",
        "outcome": "pass",
    }
    ensure_no_sensitive_keys(evidence)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Build frozen aggregate residential manager-distance evidence.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--centroid-cache", type=Path, default=CENTROID_CACHE)
    parser.add_argument("--prefetch-centroids", action="store_true")
    parser.add_argument("--countries", nargs="+", help="ISO country codes for public-source prefetch only.")
    args = parser.parse_args()

    if args.prefetch_centroids:
        if not args.countries:
            parser.error("--prefetch-centroids requires at least one --countries value.")
        prefetch_centroid_sources([country.upper() for country in args.countries], args.centroid_cache)
        return
    if args.output is None:
        parser.error("--output is required unless --prefetch-centroids is used.")

    evidence = build_evidence(args.centroid_cache)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metrics = evidence["metrics"]
    print(f"Wrote aggregate-only evidence: {args.output}")
    print(
        "Snapshot 2026-08-23; "
        f"calculable pairs={metrics['observable_pairs']:,}; "
        f"feature eligible={metrics['feature_eligible_pairs']:,}; "
        f"bands={metrics['published_band_count']}"
    )


if __name__ == "__main__":
    main()
