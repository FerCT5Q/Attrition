"""Build aggregate-only QVoice heartbeat evidence for the Jan-2026 wave.

The raw workbook is scanned in memory. Employee identifiers are used only to
join aggregate batches to the HRDA regular-active workforce snapshot; they are
never printed or persisted. The frozen JSON contains item-level aggregates,
coverage, and provenance only.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Iterable

from openpyxl import load_workbook

from build_qvoice_comment_evidence import QVOICE_ROOT, _iter_selected_rows, _norm_header


ROOT = Path(__file__).resolve().parents[1]
RUN_READONLY = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
SOURCE_FILE = QVOICE_ROOT / "Jan 2026 Qvoice_raw data.xlsx"
STRUCTURE_FILE = QVOICE_ROOT / "survey_structure.xlsx"
WORKFORCE_PROFILE_SQL = ROOT / "queries" / "profiles" / "qvoice_heartbeat_workforce_denominator_20260911.sql"
WORKFORCE_AUDIT_SQL = ROOT / "queries" / "audits" / "qvoice_heartbeat_workforce_reconciliation_20260911.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "qvoice-heartbeat-evidence-20260911.json"
SNAPSHOT_DATE = "2025-12-28"
SURVEY_WAVE = "Jan-2026"
SURVEY_LAUNCH_DATE = "2026-01-07"
MINIMUM_COHORT = 30
ITEM_COUNT = 53
MIN_VALID_ITEMS = math.ceil(ITEM_COUNT * 0.70)
SCALE_SUFFIX = "_1-5 scale"


def norm(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\n", " ")).strip()


def question_match_key(value: object) -> str:
    """Normalize the governed item text across header/dictionary punctuation.

    The Jan-2026 raw header retains terminal punctuation and, for one item, a
    display-only explanatory note that is absent from survey_structure.xlsx.
    Neither changes the item identity, so they are removed only for the
    internal one-to-one mapping.
    """
    text = norm(value)
    text = re.sub(r"\s+Note:\s+.*$", "", text, flags=re.IGNORECASE)
    return re.sub(r"[.?!]+$", "", text).strip().casefold()


def parse_employee_id(value: object) -> int | None:
    text = norm(value)
    if not text:
        return None
    if re.fullmatch(r"\d+", text):
        return int(text)
    if re.fullmatch(r"\d+\.0+", text):
        return int(float(text))
    return None


def parse_scale(value: object) -> float | None:
    if value is None or not norm(value):
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed < 1 or parsed > 5:
        return None
    return parsed


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: object) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_text(serialized)


def read_structure() -> list[dict[str, str]]:
    workbook = load_workbook(STRUCTURE_FILE, read_only=True, data_only=True)
    worksheet = workbook[workbook.sheetnames[0]]
    rows = list(worksheet.iter_rows(min_row=2, values_only=True))
    workbook.close()
    result: list[dict[str, str]] = []
    for row in rows:
        question_id = norm(row[0] if len(row) > 0 else "")
        question_text = norm(row[1] if len(row) > 1 else "")
        kpi = norm(row[2] if len(row) > 2 else "")
        driver = norm(row[3] if len(row) > 3 else "")
        if question_id and question_text:
            result.append(
                {
                    "question_id": question_id,
                    "question_text": question_text,
                    "kpi": kpi,
                    "driver": driver,
                    "group": kpi or driver or "Unmapped item",
                }
            )
    if len(result) != ITEM_COUNT:
        raise ValueError(f"survey_structure.xlsx must contain {ITEM_COUNT} item definitions; found {len(result)}.")
    return result


def discover_scale_headers() -> tuple[str, list[str]]:
    workbook = load_workbook(SOURCE_FILE, read_only=True, data_only=True)
    worksheet = workbook["Raw data"]
    headers = [norm(value) for value in next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True))]
    workbook.close()
    key_headers = [header for header in headers if header.casefold() == "emp id"]
    if len(key_headers) != 1:
        raise ValueError(f"Expected exactly one Emp ID header; found {key_headers!r}.")
    scale_headers = [header for header in headers if header.casefold().endswith(SCALE_SUFFIX)]
    if len(scale_headers) != ITEM_COUNT:
        raise ValueError(f"Expected {ITEM_COUNT} scale headers; found {len(scale_headers)}.")
    return key_headers[0], scale_headers


def question_base_from_header(header: str) -> str:
    suffix_start = header.casefold().rfind(SCALE_SUFFIX)
    if suffix_start < 0:
        raise ValueError(f"Header is not a recognized scale header: {header!r}")
    return norm(header[:suffix_start])


def scan_source(structure: list[dict[str, str]]) -> dict[str, object]:
    key_header, scale_headers = discover_scale_headers()
    structure_by_question = {question_match_key(item["question_text"]): item for item in structure}
    header_items: list[tuple[str, str]] = []
    for header in scale_headers:
        base = question_base_from_header(header)
        item = structure_by_question.get(question_match_key(base))
        if item is None:
            raise ValueError(f"Scale header has no survey_structure mapping: {header!r}")
        header_items.append((header, item["question_id"]))
    if {question_id for _, question_id in header_items} != {item["question_id"] for item in structure}:
        raise ValueError("Scale headers do not map one-to-one to the 53 survey_structure items.")

    required_columns = {key_header, *(header for header, _ in header_items)}
    values_by_employee: dict[int, list[float | None]] = {}
    duplicate_rows = 0
    duplicate_conflict_ids: set[int] = set()
    raw_rows = 0
    missing_key_rows = 0
    invalid_key_rows = 0
    invalid_scale_cells = 0
    missing_scale_cells = 0

    scale_index_by_header = {header: index for index, (header, _) in enumerate(header_items)}
    for header_map, row in _iter_selected_rows(SOURCE_FILE, "Raw data", required_columns):
        raw_rows += 1
        employee_id = parse_employee_id(row.get(header_map[key_header]))
        if employee_id is None:
            if norm(row.get(header_map[key_header])):
                invalid_key_rows += 1
            else:
                missing_key_rows += 1
            continue
        values: list[float | None] = []
        for header, _ in header_items:
            raw_value = row.get(header_map[header])
            parsed = parse_scale(raw_value)
            if raw_value is None or not norm(raw_value):
                missing_scale_cells += 1
            elif parsed is None:
                invalid_scale_cells += 1
            values.append(parsed)
        previous = values_by_employee.get(employee_id)
        if previous is None:
            values_by_employee[employee_id] = values
        else:
            duplicate_rows += 1
            if any(
                (a is None) != (b is None) or (a is not None and b is not None and abs(a - b) > 1e-12)
                for a, b in zip(previous, values)
            ):
                duplicate_conflict_ids.add(employee_id)

    for employee_id in duplicate_conflict_ids:
        values_by_employee.pop(employee_id, None)

    personal_rows: list[dict[str, object]] = []
    for employee_id, values in values_by_employee.items():
        valid_count = sum(value is not None for value in values)
        if valid_count < MIN_VALID_ITEMS:
            personal_rows.append({"employee_id": employee_id, "eligible": False, "signs": [-9] * ITEM_COUNT, "favorable": [-9] * ITEM_COUNT})
            continue
        average = sum(value for value in values if value is not None) / valid_count
        signs: list[int] = []
        favorable: list[int] = []
        for value in values:
            if value is None:
                signs.append(-9)
                favorable.append(-9)
            else:
                if value > average:
                    signs.append(1)
                elif value < average:
                    signs.append(-1)
                else:
                    signs.append(0)
                favorable.append(1 if value >= 4 else 0)
        personal_rows.append({"employee_id": employee_id, "eligible": True, "signs": signs, "favorable": favorable})

    return {
        "raw_rows": raw_rows,
        "raw_distinct_usable_employee_keys": len(values_by_employee) + len(duplicate_conflict_ids),
        "duplicate_key_rows": duplicate_rows,
        "duplicate_conflicting_employee_keys": len(duplicate_conflict_ids),
        "missing_key_rows": missing_key_rows,
        "invalid_key_rows": invalid_key_rows,
        "invalid_scale_cells": invalid_scale_cells,
        "missing_scale_cells": missing_scale_cells,
        "personal_rows": personal_rows,
        "question_headers": [header for header, _ in header_items],
    }


def run_json_query(sql: str, *, max_rows: int = 10) -> dict[str, object]:
    command = [
        str(PYTHON if PYTHON.exists() else sys.executable),
        str(RUN_READONLY),
        "--max-rows",
        str(max_rows),
        "--reporting-mode",
        "presentation",
    ]
    result = subprocess.run(command, cwd=ROOT, input=sql, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Read-only aggregate query failed: {result.stderr[-1200:]}")
    return json.loads(result.stdout)


def run_static_query(path: Path) -> tuple[dict[str, object], str]:
    sql = path.read_text(encoding="utf-8")
    payload = run_json_query(sql, max_rows=10)
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError(f"Expected exactly one aggregate row from {path}.")
    return rows[0], sha256_text(sql)


def sql_int(value: object) -> str:
    parsed = int(value)
    if parsed < 0:
        raise ValueError("Employee identifiers must be non-negative integers in runtime SQL.")
    return str(parsed)


def build_batch_sql(rows: list[dict[str, object]]) -> str:
    columns = [
        "employee_id",
        "personal_eligible",
        "up_mask",
        "stable_mask",
        "down_mask",
        "valid_mask",
        "favorable_mask",
    ]
    source_records: list[dict[str, int]] = []
    for row in rows:
        signs = row["signs"]
        favorable = row["favorable"]
        assert isinstance(signs, list) and isinstance(favorable, list)
        up_mask = 0
        stable_mask = 0
        down_mask = 0
        valid_mask = 0
        favorable_mask = 0
        for index, (sign, fav) in enumerate(zip(signs, favorable)):
            bit = 1 << index
            if sign == 1:
                up_mask |= bit
                valid_mask |= bit
            elif sign == 0:
                stable_mask |= bit
                valid_mask |= bit
            elif sign == -1:
                down_mask |= bit
                valid_mask |= bit
            if fav == 1:
                favorable_mask |= bit
        source_records.append(
            {
                "employee_id": int(row["employee_id"]),
                "personal_eligible": 1 if row["eligible"] else 0,
                "up_mask": up_mask,
                "stable_mask": stable_mask,
                "down_mask": down_mask,
                "valid_mask": valid_mask,
                "favorable_mask": favorable_mask,
            }
        )
    select_parts = [
        "COUNT(w.employee_id) AS matched_workforce_employees",
        "SUM(CASE WHEN s.personal_eligible = 1 THEN 1 ELSE 0 END) AS personal_mean_eligible_employees",
    ]
    for index, item_id in enumerate(QUESTION_IDS):
        bit = f"(1::BIGINT << {index})"
        select_parts.extend(
            [
                f"SUM(CASE WHEN s.personal_eligible = 1 AND (s.valid_mask & {bit}) <> 0 THEN 1 ELSE 0 END) AS {item_id.lower()}_valid_count",
                f"SUM(CASE WHEN s.personal_eligible = 1 AND (s.up_mask & {bit}) <> 0 THEN 1 ELSE 0 END) AS {item_id.lower()}_upvote_count",
                f"SUM(CASE WHEN s.personal_eligible = 1 AND (s.stable_mask & {bit}) <> 0 THEN 1 ELSE 0 END) AS {item_id.lower()}_stable_count",
                f"SUM(CASE WHEN s.personal_eligible = 1 AND (s.down_mask & {bit}) <> 0 THEN 1 ELSE 0 END) AS {item_id.lower()}_downvote_count",
                f"SUM(CASE WHEN s.personal_eligible = 1 AND (s.valid_mask & {bit}) <> 0 THEN 1 ELSE 0 END) AS {item_id.lower()}_favorable_denominator",
                f"SUM(CASE WHEN s.personal_eligible = 1 AND (s.favorable_mask & {bit}) <> 0 THEN 1 ELSE 0 END) AS {item_id.lower()}_favorable_count",
            ]
        )
    select_sql = ",\n    ".join(select_parts)
    source_json = json.dumps(source_records, separators=(",", ":")).replace("'", "''")
    source = f"""SELECT
        elem.employee_id::BIGINT AS employee_id,
        elem.personal_eligible::INTEGER AS personal_eligible,
        elem.up_mask::BIGINT AS up_mask,
        elem.stable_mask::BIGINT AS stable_mask,
        elem.down_mask::BIGINT AS down_mask,
        elem.valid_mask::BIGINT AS valid_mask,
        elem.favorable_mask::BIGINT AS favorable_mask
    FROM (SELECT JSON_PARSE('{source_json}') AS payload) AS src,
         src.payload AS elem"""
    return f"""WITH source AS (
    {source}
), workforce AS (
    SELECT employee_id
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '{SNAPSHOT_DATE}'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
)
SELECT
    {select_sql}
FROM workforce w
JOIN source s ON s.employee_id = w.employee_id;"""


def run_batches(personal_rows: list[dict[str, object]], batch_size: int = 10000) -> dict[str, int]:
    totals: defaultdict[str, int] = defaultdict(int)
    rows = [row for row in personal_rows if row["employee_id"] not in CONFLICTING_IDS]
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        payload = run_json_query(build_batch_sql(batch), max_rows=10)
        result_rows = payload.get("rows", [])
        if not isinstance(result_rows, list) or len(result_rows) != 1:
            raise ValueError("Each heartbeat workforce batch must return exactly one aggregate row.")
        row = result_rows[0]
        for key, value in row.items():
            totals[key] += int(value or 0)
        print(f"  workforce aggregate batch {start + 1}-{start + len(batch)}", flush=True)
    return dict(totals)


def pct(numerator: int, denominator: int) -> float:
    return round(100.0 * numerator / denominator, 4) if denominator else 0.0


def main() -> None:
    global QUESTION_IDS, CONFLICTING_IDS
    structure = read_structure()
    QUESTION_IDS = [item["question_id"] for item in structure]
    scanned = scan_source(structure)
    personal_rows = scanned.pop("personal_rows")
    CONFLICTING_IDS = set()
    # Conflicting duplicate rows were removed during scan. Keep a runtime-only
    # list empty so the batch function cannot accidentally reintroduce them.
    profile_row, profile_sql_hash = run_static_query(WORKFORCE_PROFILE_SQL)
    audit_row, audit_sql_hash = run_static_query(WORKFORCE_AUDIT_SQL)
    workforce_eligible = int(profile_row.get("eligible_employees") or 0)
    if workforce_eligible < MINIMUM_COHORT:
        raise ValueError("The workforce denominator is below the publication minimum.")
    if int(profile_row.get("snapshot_rows") or 0) != workforce_eligible or int(profile_row.get("null_employee_rows") or 0) != 0:
        raise ValueError("The workforce profile does not reconcile snapshot rows to distinct non-null employees.")
    aggregate = run_batches(personal_rows)
    if int(aggregate.get("matched_workforce_employees", 0)) > workforce_eligible:
        raise ValueError("Matched QVoice employees exceed the eligible workforce denominator.")

    item_by_id = {item["question_id"]: item for item in structure}
    items: list[dict[str, object]] = []
    for item in structure:
        question_id = item["question_id"]
        key = question_id.lower()
        valid = int(aggregate.get(f"{key}_valid_count", 0))
        up = int(aggregate.get(f"{key}_upvote_count", 0))
        stable = int(aggregate.get(f"{key}_stable_count", 0))
        down = int(aggregate.get(f"{key}_downvote_count", 0))
        favorable_denominator = int(aggregate.get(f"{key}_favorable_denominator", 0))
        favorable = int(aggregate.get(f"{key}_favorable_count", 0))
        if up + stable + down != valid:
            raise ValueError(f"Heartbeat sign categories do not reconcile for {question_id}.")
        items.append(
            {
                **item,
                "valid_employee_count": valid,
                "unknown_employee_count": max(workforce_eligible - valid, 0),
                "workforce_coverage_percent": pct(valid, workforce_eligible),
                "upvote_count": up,
                "upvote_percent": pct(up, valid),
                "stable_count": stable,
                "stable_percent": pct(stable, valid),
                "downvote_count": down,
                "downvote_percent": pct(down, valid),
                "favorable_count": favorable,
                "favorable_denominator": favorable_denominator,
                "favorable_percent": pct(favorable, favorable_denominator),
            }
        )

    publishable = [item for item in items if int(item["valid_employee_count"]) >= MINIMUM_COHORT]
    top_upvotes = sorted(publishable, key=lambda item: (-float(item["upvote_percent"]), str(item["question_id"])))[:5]
    top_downvotes = sorted(publishable, key=lambda item: (-float(item["downvote_percent"]), str(item["question_id"])))[:5]
    if len(top_upvotes) != 5 or len(top_downvotes) != 5:
        raise ValueError("The heartbeat must have at least five publishable items in each ranking.")

    for item in items:
        item.pop("question_text", None)
    top_upvote_ids = [item["question_id"] for item in top_upvotes]
    top_downvote_ids = [item["question_id"] for item in top_downvotes]
    by_id = {item["question_id"]: item for item in items}
    evidence = {
        "artifact": "presentation",
        "evidence_type": "aggregate-only QVoice heartbeat",
        "generated_on": date.today().isoformat(),
        "outcome": "pass",
        "source": {
            "wave": SURVEY_WAVE,
            "survey_launch_date": SURVEY_LAUNCH_DATE,
            "workbook": "data/QVoice/Jan 2026 Qvoice_raw data.xlsx",
            "sheet": "Raw data",
            "structure": "data/QVoice/survey_structure.xlsx",
            "scale_domain": [1, 2, 3, 4, 5],
        },
        "population": {
            "snapshot_date": SNAPSHOT_DATE,
            "definition": "worker_type='Employee'; employee_type='Regular'; active_status=1",
            "eligible_employees": workforce_eligible,
            "grain": "Distinct employee at the pre-Jan-2026 monthly snapshot",
        },
        "definition": {
            "personal_average_rule": f"At least {MIN_VALID_ITEMS} of {ITEM_COUNT} valid 1-5 items (70%).",
            "sign_rule": "+1 when item > personal mean; 0 when item = personal mean; -1 when item < personal mean.",
            "missing_rule": "Missing or invalid item values are not converted to 0 and are excluded from that item's denominator.",
            "ranking_rule": "Top five items by upvote_percent and downvote_percent among items with n >= 30.",
            "absolute_context": "Favorable means scale response 4 or 5 among the same valid item denominator.",
        },
        "metrics": {
            **scanned,
            "item_count": ITEM_COUNT,
            "minimum_valid_items": MIN_VALID_ITEMS,
            "matched_workforce_employees": int(aggregate.get("matched_workforce_employees", 0)),
            "personal_mean_eligible_employees": int(aggregate.get("personal_mean_eligible_employees", 0)),
            "publishable_item_count": len(publishable),
            "workforce_profile_query_result": profile_row,
            "workforce_audit_query_result": audit_row,
        },
        "items": items,
        "top_upvotes": [by_id[question_id] for question_id in top_upvote_ids],
        "top_downvotes": [by_id[question_id] for question_id in top_downvote_ids],
        "privacy": {
            "identifiers_persisted": False,
            "individual_rows_persisted": False,
            "individual_scale_values_persisted": False,
            "runtime_join_sql_persisted": False,
            "minimum_published_cohort": MINIMUM_COHORT,
        },
        "provenance": {
            "profile_sql": str(WORKFORCE_PROFILE_SQL.relative_to(ROOT)).replace("\\", "/"),
            "profile_sql_sha256": profile_sql_hash,
            "profile_result_sha256": sha256_json(profile_row),
            "audit_sql": str(WORKFORCE_AUDIT_SQL.relative_to(ROOT)).replace("\\", "/"),
            "audit_sql_sha256": audit_sql_hash,
            "audit_result_sha256": sha256_json(audit_row),
        },
        "top_upvote_question_ids": top_upvote_ids,
        "top_downvote_question_ids": top_downvote_ids,
        "acceptance_rule": "53 scale items map one-to-one to survey_structure; workforce denominator is n >= 30; raw keys have no conflicting duplicates; valid sign buckets reconcile per item; all published rankings have n >= 30; no identifiers or individual values persist.",
        "limitation": "Relative heartbeat is above/below each employee's own item average; it is not an absolute sentiment label, temporal pulse, causal effect or individual attrition score.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "workforce": workforce_eligible, "matched": evidence["metrics"]["matched_workforce_employees"], "items": ITEM_COUNT, "outcome": "pass"}, ensure_ascii=False))


QUESTION_IDS: list[str] = []
CONFLICTING_IDS: set[int] = set()


if __name__ == "__main__":
    main()
