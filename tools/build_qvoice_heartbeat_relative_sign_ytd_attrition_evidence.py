"""Build aggregate-only post-survey YTD attrition for QVoice heartbeat signs.

The Jan-2026 workbook is scanned only in memory. The slide retains the top
three +1 and top three -1 items, then displays every selected item's +1, 0,
and -1 response groups. Employee keys remain inside the read-only join and
are never printed or persisted.
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
WINDOW_AUDIT = ROOT / "queries" / "audits" / "qvoice_heartbeat_relative_sign_ytd_window_audit_20260923.sql"
RUNTIME_TEMPLATE = ROOT / "queries" / "audits" / "qvoice_heartbeat_relative_sign_ytd_attrition_runtime_template_20260923.sql"
DISPLAY_EVIDENCE = ROOT / "output" / "distribution" / "json" / "qvoice-heartbeat-evidence-20260911.json"
OUTPUT = ROOT / "output" / "distribution" / "json" / "qvoice-2026-august-post-survey-ytd-heartbeat-relative-sign-attrition-evidence-20260923.json"
SURVEY_WAVE = "Jan-2026"
SURVEY_LAUNCH_DATE = "2026-01-07"
BASELINE_SNAPSHOT = "2025-12-28"
AUGUST_CUTOFF_DATE = "2026-08-23"
TOP_N = 3

SIGN_SPECS = (
    (1, "+1", "above personal mean", "upvote_count", "upvote_percent"),
    (0, "0", "equal to personal mean", "stable_count", "stable_percent"),
    (-1, "-1", "below personal mean", "downvote_count", "downvote_percent"),
)


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


def build_runtime_sql(records: list[dict[str, int]]) -> str:
    source_json = json.dumps(records, separators=(",", ":")).replace("'", "''")
    template = RUNTIME_TEMPLATE.read_text(encoding="utf-8")
    return (
        template.replace("{{SOURCE_JSON}}", source_json)
        .replace("{{BASELINE_SNAPSHOT}}", BASELINE_SNAPSHOT)
        .replace("{{SURVEY_LAUNCH_DATE}}", SURVEY_LAUNCH_DATE)
        .replace("{{AUGUST_CUTOFF_DATE}}", AUGUST_CUTOFF_DATE)
    )


def aggregate_groups(groups: list[tuple[int, str, set[int]]]) -> tuple[dict[int, dict[str, int | float]], list[dict[str, Any]]]:
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
        payload = json_query(
            build_runtime_sql(
                [{"employee_id": row["employee_key"], "group_code": row["group_code"]} for row in batch]
            ),
            max_rows=100,
        )
        rows = payload.get("rows")
        require(isinstance(rows, list), "The runtime heartbeat query did not return aggregate rows.")
        for row in rows:
            code = int(row["group_code"])
            require(code in totals, f"Unexpected heartbeat group code {code}.")
            for column in ("source_employee_count", "matched_employee_count", "voluntary_exit_count"):
                totals[code][column] += int(row.get(column) or 0)
        print(f"  heartbeat relative-sign YTD batch {start + 1:,}-{min(start + batch_size, len(records)):,}", flush=True)

    results: dict[int, dict[str, int | float]] = {}
    for code, label, employee_ids in ordered:
        row = totals[code]
        source = int(row["source_employee_count"])
        matched = int(row["matched_employee_count"])
        exits = int(row["voluntary_exit_count"])
        require(source == len(employee_ids), f"The runtime source count is invalid for {label}.")
        require(MINIMUM_COHORT <= matched <= source and 0 <= exits <= matched, f"The runtime cohort is invalid for {label}.")
        results[code] = {
            "source_employee_count": source,
            "matched_employee_count": matched,
            "unmatched_employee_count": source - matched,
            "voluntary_exit_count": exits,
            "ytd_voluntary_attrition_rate_percent": round(100.0 * exits / matched, 4),
        }
    return results, [{"group_code": code, "label": label, **results[code]} for code, label, _ in ordered]


def sign_metadata(sign: int) -> tuple[str, str, str, str]:
    for candidate, symbol, label, count_key, percent_key in SIGN_SPECS:
        if candidate == sign:
            return symbol, label, count_key, percent_key
    raise ValueError(f"Unsupported heartbeat sign: {sign}")


def main() -> None:
    window, window_sql_hash = one_row_query(WINDOW_AUDIT)
    require(str(window["survey_launch_date"]) == SURVEY_LAUNCH_DATE, "Unexpected QVoice survey launch date.")
    require(str(window["baseline_snapshot"]) == BASELINE_SNAPSHOT, "Unexpected QVoice baseline snapshot.")
    require(str(window["august_cutoff_date"]) == AUGUST_CUTOFF_DATE, "Unexpected QVoice August cutoff.")
    require(int(window["duplicate_baseline_employee_count"]) == 0, "The pre-wave baseline contains duplicate employees.")
    require(int(window["baseline_distinct_employee_count"]) >= MINIMUM_COHORT, "The pre-wave baseline is below n=30.")

    display_evidence = json.loads(DISPLAY_EVIDENCE.read_text(encoding="utf-8"))
    require(display_evidence.get("artifact") == "presentation" and display_evidence.get("outcome") == "pass", "The frozen heartbeat display evidence did not pass validation.")
    display_items = {str(item["question_id"]): item for item in display_evidence["items"]}
    top_panels = (
        (1, "+1", "above personal mean", list(display_evidence["top_upvotes"])[:TOP_N]),
        (-1, "-1", "below personal mean", list(display_evidence["top_downvotes"])[:TOP_N]),
    )
    require(all(len(items) == TOP_N for _, _, _, items in top_panels), "Each heartbeat ranking must have three items.")

    structure = read_structure()
    scanned = scan_source(structure)
    personal_rows = scanned.pop("personal_rows")
    require(isinstance(personal_rows, list), "The heartbeat source did not return personal rows.")
    index_by_question = {str(item["question_id"]): index for index, item in enumerate(structure)}
    employee_ids_by_item_sign: dict[tuple[str, int], set[int]] = defaultdict(set)
    for row in personal_rows:
        if not bool(row["eligible"]):
            continue
        employee_id = int(row["employee_id"])
        signs = row["signs"]
        for question_id, index in index_by_question.items():
            sign = int(signs[index])
            if sign in (-1, 0, 1):
                employee_ids_by_item_sign[(question_id, sign)].add(employee_id)

    segment_specs: list[tuple[int, int, str, dict[str, Any], int]] = []
    code = 0
    for panel_index, (_, _, _, panel_items) in enumerate(top_panels):
        for rank, panel_item in enumerate(panel_items, start=1):
            question_id = str(panel_item["question_id"])
            item = display_items[question_id]
            for sign, _, _, _, _ in SIGN_SPECS:
                segment_specs.append((code, panel_index, question_id, item, sign))
                code += 1

    runtime_groups = []
    for group_code, _, question_id, _, sign in segment_specs:
        symbol, label, _, _ = sign_metadata(sign)
        runtime_groups.append((group_code, f"{question_id} {symbol} {label}", set(employee_ids_by_item_sign[(question_id, sign)])))
    runtime, runtime_rows = aggregate_groups(runtime_groups)

    panels: list[dict[str, Any]] = []
    expected_by_question = {question_id: item for question_id, item in display_items.items()}
    for panel_index, (ranking_sign, ranking_symbol, ranking_label, panel_items) in enumerate(top_panels):
        question_rows: list[dict[str, Any]] = []
        for rank, panel_item in enumerate(panel_items, start=1):
            question_id = str(panel_item["question_id"])
            item = expected_by_question[question_id]
            valid = int(item["valid_employee_count"])
            segments: list[dict[str, Any]] = []
            for sign, symbol, label, count_key, percent_key in SIGN_SPECS:
                group_code = next(
                    code
                    for code, candidate_panel, candidate_question, _, candidate_sign in segment_specs
                    if candidate_panel == panel_index and candidate_question == question_id and candidate_sign == sign
                )
                metric = runtime[group_code]
                # The frozen heartbeat ranking is built after joining the
                # workbook to the active-Regular HRDA snapshot.  Reconcile
                # response shares against that same matched population; the
                # workbook-source count is retained only as a join-quality
                # diagnostic and is intentionally not the chart denominator.
                expected_count = int(item[count_key])
                require(
                    int(metric["matched_employee_count"]) == expected_count,
                    f"The matched count does not reconcile for {question_id} {symbol}.",
                )
                segments.append(
                    {
                        "sign": sign,
                        "sign_symbol": symbol,
                        "sign_label": label,
                        "source_workbook_response_count": int(metric["source_employee_count"]),
                        "matched_response_count": expected_count,
                        "share_of_valid_responses_percent": float(item[percent_key]),
                        **metric,
                    }
                )
            require(sum(int(segment["matched_response_count"]) for segment in segments) == valid, f"Heartbeat signs do not reconcile for {question_id}.")
            require(abs(sum(float(segment["share_of_valid_responses_percent"]) for segment in segments) - 100.0) < 0.0002, f"Heartbeat shares do not sum to 100% for {question_id}.")
            question_rows.append(
                {
                    "rank": rank,
                    "question_id": question_id,
                    "question_label": str(item["group"]),
                    "valid_response_count": valid,
                    "ranking_sign": ranking_sign,
                    "ranking_signal_percent": float(item["upvote_percent"] if ranking_sign == 1 else item["downvote_percent"]),
                    "segments": segments,
                }
            )
        panels.append(
            {
                "ranking_sign": ranking_sign,
                "ranking_symbol": ranking_symbol,
                "ranking_label": ranking_label,
                "questions": question_rows,
            }
        )

    all_segments = [segment for panel in panels for question in panel["questions"] for segment in question["segments"]]
    require(len(panels) == 2 and all(len(panel["questions"]) == TOP_N for panel in panels), "Heartbeat requires two top-three panels.")
    require(len(all_segments) == 18, "Heartbeat requires eighteen displayed sign segments.")
    for segment in all_segments:
        require(
            abs(float(segment["ytd_voluntary_attrition_rate_percent"]) - 100.0 * int(segment["voluntary_exit_count"]) / int(segment["matched_employee_count"])) < 0.00011,
            "A heartbeat relative-sign YTD rate does not reconcile.",
        )

    template_sql = RUNTIME_TEMPLATE.read_text(encoding="utf-8")
    evidence = {
        "artifact": "presentation",
        "evidence_type": "aggregate-only QVoice heartbeat relative-sign attrition after the Jan-2026 survey through fiscal August 2026",
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
            "baseline_snapshot": BASELINE_SNAPSHOT,
            "survey_launch_date": SURVEY_LAUNCH_DATE,
            "august_cutoff_date": AUGUST_CUTOFF_DATE,
            "window": f"({SURVEY_LAUNCH_DATE}, {AUGUST_CUTOFF_DATE}]",
            "label": "Post-survey voluntary attrition YTD through fiscal August 2026; not annualized",
            "target": "At least one term_type exactly VOLUNTARY after the Jan-2026 QVoice launch and on or before the fiscal-August cutoff.",
            "population": "Each displayed response-sign segment is matched to worker_type='Employee'; employee_type='Regular'; active_status=1 at the 2025-12-28 pre-wave snapshot.",
            "grain": "Distinct employee in each question/sign segment; a person can appear in more than one question but exactly one sign within a question.",
        },
        "definition": {
            "heartbeat_rule": f"At least {int(ITEM_COUNT * 0.70 + 0.9999)} of {ITEM_COUNT} valid 1-5 answers; +1 means item > personal mean, 0 means item = personal mean, and -1 means item < personal mean.",
            "ranking_rule": "Three items with the largest +1 share and three items with the largest -1 share; ties use question_id.",
            "segment_rule": "Every displayed question contains its mutually exclusive +1, 0, and -1 response-sign groups.",
            "attrition_formula": "Distinct voluntary exits after the survey launch through 23-Aug-2026 divided by matched active-Regular employees in that same question/sign group.",
            "overlap": "Question/sign groups do not overlap within a question; employees can appear in multiple questions, so rates are calculated independently per row.",
        },
        "slide": {
            "number": 24,
            "technical_stage": 26,
            "group": "Heartbeat top-three relative-sign questions",
            "panels": panels,
        },
        "validation": {
            "outcome": "pass",
            "window_row": window,
            "source_quality": {key: value for key, value in scanned.items() if isinstance(value, int)},
            "panel_count": len(panels),
            "questions_displayed": sum(len(panel["questions"]) for panel in panels),
            "segments_displayed": len(all_segments),
            "all_displayed_segments_have_n_at_least": MINIMUM_COHORT,
            "all_question_sign_shares_reconcile_to_100_percent": True,
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
    encoded = json.dumps(evidence, ensure_ascii=False)
    require('"employee_id"' not in encoded and '"emp_id"' not in encoded, "Employee identifiers must not persist in evidence.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "questions": 6, "segments": len(all_segments), "outcome": "pass"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
