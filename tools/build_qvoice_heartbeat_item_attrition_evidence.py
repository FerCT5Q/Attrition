"""Build aggregate-only August trailing-12-month attrition for heartbeat bars.

The Jan-2026 QVoice workbook is scanned in memory to rebuild the same
item/sign segments displayed on slide 24. Employee keys are used only inside
the read-only Redshift join and are never printed or persisted. The output
contains one aggregate attrition result per displayed item/sign segment.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from build_qvoice_heartbeat_evidence import (
    ITEM_COUNT,
    MINIMUM_COHORT,
    SOURCE_FILE,
    read_structure,
    scan_source,
)


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
RUN_READONLY = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
WINDOW_AUDIT = ROOT / "queries" / "audits" / "qvoice_heartbeat_item_august_trailing_12m_window_audit_20260921.sql"
RUNTIME_TEMPLATE = ROOT / "queries" / "audits" / "qvoice_heartbeat_item_august_trailing_12m_attrition_runtime_template_20260921.sql"
DISPLAY_EVIDENCE = ROOT / "output" / "distribution" / "json" / "qvoice-heartbeat-evidence-20260911.json"
OUTPUT = ROOT / "output" / "distribution" / "json" / "qvoice-2026-august-trailing-12m-heartbeat-item-attrition-evidence-20260921.json"
SURVEY_WAVE = "Jan-2026"
SURVEY_LAUNCH_DATE = "2026-01-07"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: object) -> str:
    return sha256_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def json_query(sql: str, *, max_rows: int = 100) -> dict[str, Any]:
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
        raise RuntimeError(f"Read-only aggregate query failed: {result.stderr[-1600:]}")
    return json.loads(result.stdout)


def one_row_query(path: Path) -> tuple[dict[str, Any], str]:
    sql = path.read_text(encoding="utf-8")
    payload = json_query(sql, max_rows=10)
    rows = payload.get("rows")
    require(isinstance(rows, list) and len(rows) == 1, f"Expected one aggregate row from {path}.")
    return dict(rows[0]), sha256_text(sql)


def build_runtime_sql(records: list[dict[str, int]], display_snapshot: str, baseline_snapshot: str, august_cutoff: str) -> str:
    source_json = json.dumps(records, separators=(",", ":")).replace("'", "''")
    template = RUNTIME_TEMPLATE.read_text(encoding="utf-8")
    return (
        template.replace("{{SOURCE_JSON}}", source_json)
        .replace("{{DISPLAY_SNAPSHOT}}", display_snapshot)
        .replace("{{BASELINE_SNAPSHOT}}", baseline_snapshot)
        .replace("{{AUGUST_CUTOFF_DATE}}", august_cutoff)
    )


def aggregate_groups(
    groups: list[tuple[int, str, set[int]]],
    display_snapshot: str,
    baseline_snapshot: str,
    august_cutoff: str,
) -> tuple[dict[int, dict[str, int | float]], list[dict[str, Any]]]:
    ordered: list[tuple[int, str, set[int]]] = []
    records: list[dict[str, int]] = []
    for code, label, employee_ids in groups:
        require(len(employee_ids) >= MINIMUM_COHORT, f"The cohort {label} is below n=30.")
        ordered.append((code, label, employee_ids))
        records.extend({"employee_key": employee_id, "group_code": code} for employee_id in sorted(employee_ids))

    totals: dict[int, dict[str, int]] = {code: defaultdict(int) for code, _, _ in ordered}
    batch_size = 10_000
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        # The runtime template uses employee_key only as an internal alias for
        # the restricted join key; it is never returned or persisted.
        batch_sql = build_runtime_sql(
            [
                {"employee_id": row["employee_key"], "group_code": row["group_code"]}
                for row in batch
            ],
            display_snapshot,
            baseline_snapshot,
            august_cutoff,
        )
        payload = json_query(batch_sql, max_rows=100)
        rows = payload.get("rows")
        require(isinstance(rows, list), "The runtime heartbeat query did not return aggregate rows.")
        for row in rows:
            code = int(row["group_code"])
            require(code in totals, f"Unexpected heartbeat group code {code}.")
            for column in ("source_employee_count", "matched_employee_count", "voluntary_exit_count"):
                totals[code][column] += int(row.get(column) or 0)
        print(f"  heartbeat attrition batch {start + 1:,}-{min(start + batch_size, len(records)):,}", flush=True)

    results: dict[int, dict[str, int | float]] = {}
    for code, label, employee_ids in ordered:
        row = totals[code]
        source = int(row["source_employee_count"])
        matched = int(row["matched_employee_count"])
        exits = int(row["voluntary_exit_count"])
        require(0 <= source <= len(employee_ids), f"The runtime source count is invalid for {label}.")
        require(MINIMUM_COHORT <= matched <= source and 0 <= exits <= matched, f"The runtime cohort is invalid for {label}.")
        results[code] = {
            "source_employee_count": source,
            "matched_employee_count": matched,
            "unmatched_employee_count": source - matched,
            "voluntary_exit_count": exits,
            "trailing_12m_voluntary_attrition_rate_percent": round(100.0 * exits / matched, 4),
        }
    return results, [{"group_code": code, "label": label, **results[code]} for code, label, _ in ordered]


def main() -> None:
    window, window_sql_hash = one_row_query(WINDOW_AUDIT)
    baseline_snapshot = str(window["baseline_snapshot"])
    august_cutoff = str(window["august_cutoff_date"])
    window_start = str(window["window_start"])
    display_snapshot = "2025-12-28"
    require(window_start == baseline_snapshot == "2025-08-24", "The August 2025 baseline snapshot is not the governed snapshot.")
    require(august_cutoff == "2026-08-23", "The August 2026 cutoff is not the governed snapshot.")
    require(int(window["duplicate_baseline_employee_count"]) == 0, "The baseline snapshot contains duplicate employees.")
    require(int(window["baseline_distinct_employee_count"]) >= MINIMUM_COHORT, "The baseline cohort is below n=30.")

    display_evidence = json.loads(DISPLAY_EVIDENCE.read_text(encoding="utf-8"))
    require(display_evidence.get("outcome") == "pass", "The frozen heartbeat display evidence did not pass validation.")
    display_items = {str(item["question_id"]): item for item in display_evidence["items"]}
    display_top_up = [str(item["question_id"]) for item in display_evidence["top_upvotes"]]
    display_top_down = [str(item["question_id"]) for item in display_evidence["top_downvotes"]]
    require(display_top_up == ["Q38", "Q37", "Q32", "Q30", "Q33"], "The visible heartbeat +1 ranking changed unexpectedly.")
    require(display_top_down == ["Q53", "Q10", "Q11", "Q47", "Q27"], "The visible heartbeat -1 ranking changed unexpectedly.")

    structure = read_structure()
    scanned = scan_source(structure)
    personal_rows = scanned.pop("personal_rows")
    require(isinstance(personal_rows, list), "The heartbeat source did not return personal rows.")
    item_by_id = {item["question_id"]: item for item in structure}
    employee_ids_by_item_sign: dict[tuple[str, int], set[int]] = defaultdict(set)
    for index, item in enumerate(structure):
        question_id = str(item["question_id"])
        for row in personal_rows:
            if not bool(row["eligible"]):
                continue
            signs = row["signs"]
            sign = int(signs[index])
            if sign not in (-1, 0, 1):
                continue
            employee_id = int(row["employee_id"])
            employee_ids_by_item_sign[(question_id, sign)].add(employee_id)

    segment_specs: list[tuple[int, str, dict[str, Any], int]] = []
    code = 0
    for direction, rows in ((1, display_top_up), (-1, display_top_down)):
        for question_id in rows:
            item = display_items[question_id]
            direction_label = "+1 · above personal mean" if direction == 1 else "−1 · below personal mean"
            segment_specs.append((code, f"{item['question_id']} {direction_label}", item, direction))
            code += 1

    reference_ids = {int(row["employee_id"]) for row in personal_rows if bool(row["eligible"])}
    runtime_groups = [
        (group_code, label, set(employee_ids_by_item_sign[(str(item["question_id"]), direction)]))
        for group_code, label, item, direction in segment_specs
    ]
    runtime_groups.append((code, "Heartbeat eligible reference cohort", reference_ids))
    runtime, runtime_rows = aggregate_groups(runtime_groups, display_snapshot, baseline_snapshot, august_cutoff)

    segments: list[dict[str, Any]] = []
    for group_code, label, item, direction in segment_specs:
        metric = runtime[group_code]
        expected_source = int(item["upvote_count"] if direction == 1 else item["downvote_count"])
        require(int(metric["source_employee_count"]) == expected_source, f"The visible source count does not reconcile for {item['question_id']}.")
        segments.append(
            {
                "question_id": str(item["question_id"]),
                "question_label": str(item["group"]),
                "direction": direction,
                "direction_label": "+1 · above personal mean" if direction == 1 else "−1 · below personal mean",
                "signal_percent": float(item["upvote_percent"] if direction == 1 else item["downvote_percent"]),
                "valid_employee_count": int(item["valid_employee_count"]),
                "favorable_percent": float(item["favorable_percent"]),
                **metric,
            }
        )

    reference = runtime[code]
    require(
        int(reference["source_employee_count"]) == int(display_evidence["metrics"]["personal_mean_eligible_employees"]),
        "The heartbeat reference source count does not reconcile to the visible cohort.",
    )
    for row in segments:
        require(abs(float(row["trailing_12m_voluntary_attrition_rate_percent"]) - 100.0 * int(row["voluntary_exit_count"]) / int(row["matched_employee_count"])) < 0.00011, "A heartbeat segment rate does not reconcile.")

    template_sql = RUNTIME_TEMPLATE.read_text(encoding="utf-8")
    evidence = {
        "artifact": "internal_analysis",
        "evidence_type": "aggregate-only QVoice heartbeat item/sign attrition trailing 12 months through August 2026",
        "generated_on": date.today().isoformat(),
        "outcome": "pass",
        "minimum_shared_cohort": MINIMUM_COHORT,
        "source": {
            "wave": SURVEY_WAVE,
            "survey_launch_date": SURVEY_LAUNCH_DATE,
            "workbook": "data/QVoice/Jan 2026 Qvoice_raw data.xlsx",
            "sheet": "Raw data",
            "structure": "data/QVoice/survey_structure.xlsx",
        },
        "outcome_contract": {
            "baseline_snapshot": baseline_snapshot,
            "august_cutoff_date": august_cutoff,
            "window": f"({baseline_snapshot}, {august_cutoff}]",
            "label": "Trailing 12-month voluntary attrition through August 2026",
            "target": "At least one term_type exactly VOLUNTARY after the August 2025 baseline snapshot and on or before the August 2026 cutoff.",
            "population": "Each displayed item/sign segment is matched to worker_type='Employee'; employee_type='Regular'; active_status=1 at the August 2025 baseline snapshot.",
            "grain": "Distinct employee in each item/sign segment; employees may appear in multiple item segments because items are separate dimensions.",
        },
        "definition": {
            "heartbeat_rule": f"At least {int(ITEM_COUNT * 0.70 + 0.9999)} of {ITEM_COUNT} valid 1-5 answers; +1 means item > personal mean and -1 means item < personal mean.",
            "segment_rule": "Each displayed bar is the item-specific +1 or -1 group used by the distribution bar.",
            "attrition_formula": "Distinct voluntary exits in the trailing window divided by the matched active-regular baseline employees in that same item/sign group.",
            "overlap": "Item/sign groups are not mutually exclusive across questions; rates are calculated independently per bar.",
        },
        "slide": {
            "number": 24,
            "technical_stage": 26,
            "group": "Heartbeat item/sign segments",
            "reference_cohort": reference,
            "segments": segments,
        },
        "validation": {
            "outcome": "pass",
            "window_row": window,
            "source_quality": {key: value for key, value in scanned.items() if isinstance(value, int)},
            "segment_count": len(segments),
            "all_displayed_segments_have_n_at_least": MINIMUM_COHORT,
            "all_rates_reconcile_to_exits_and_matched_cohort": True,
            "runtime_join_sql_persisted": False,
            "employee_keys_persisted": False,
            "individual_rows_persisted": False,
            "runtime_aggregate_rows": len(runtime_rows),
        },
        "provenance": {
            "window_audit": str(WINDOW_AUDIT.relative_to(ROOT)).replace("\\", "/"),
            "window_audit_sha256": window_sql_hash,
            "display_evidence": str(DISPLAY_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "display_evidence_sha256": hashlib.sha256(DISPLAY_EVIDENCE.read_bytes()).hexdigest(),
            "runtime_template": str(RUNTIME_TEMPLATE.relative_to(ROOT)).replace("\\", "/"),
            "runtime_template_sha256": sha256_text(template_sql),
            "source_file": str(SOURCE_FILE.relative_to(ROOT)).replace("\\", "/"),
            "source_file_sha256": hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest(),
            "aggregate_result_sha256": sha256_json(runtime_rows),
        },
        "privacy": {
            "identifiers_persisted": False,
            "individual_rows_persisted": False,
            "minimum_published_cohort": MINIMUM_COHORT,
        },
    }
    # Remove any accidental internal-only sets before persistence.
    encoded = json.dumps(evidence, ensure_ascii=False)
    require('"employee_id"' not in encoded and '"emp_id"' not in encoded, "Employee identifiers must not persist in evidence.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "segments": len(segments), "reference_rate": reference["trailing_12m_voluntary_attrition_rate_percent"], "outcome": "pass"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
