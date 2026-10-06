"""Build aggregate-only August trailing-12-month attrition for QVoice themes.

Jan-2026 improvement-theme membership and comment text are processed only in
memory. Redshift receives short-lived aggregate-query inputs containing the
internal join keys; the expanded SQL and employee keys are never persisted.
The output JSON contains only distribution counts, matched cohort counts,
voluntary exits, rates, and provenance.
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

from build_qvoice_ytd_attrition_evidence import (
    RETENTION_EVIDENCE,
    ROOT,
    MINIMUM_COHORT,
    PYTHON,
    HELPER,
    QVOICE_ROOT,
    json_query as _unused_json_query,
    require,
    scan_comment_groups,
)


WINDOW_AUDIT = ROOT / "queries" / "audits" / "qvoice_retention_theme_august_trailing_12m_window_audit_20260922.sql"
RUNTIME_TEMPLATE = ROOT / "queries" / "audits" / "qvoice_retention_theme_august_trailing_12m_attrition_runtime_template_20260922.sql"
OUTPUT = ROOT / "output" / "distribution" / "json" / "qvoice-retention-theme-august-trailing-12m-attrition-evidence-20260922.json"

DISPLAY_SNAPSHOT = "2025-12-28"


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_query(*, sql: str, max_rows: int = 100) -> dict[str, Any]:
    command = [
        str(PYTHON if PYTHON.exists() else sys.executable),
        str(HELPER),
        "--max-rows",
        str(max_rows),
        "--reporting-mode",
        "presentation",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        input=sql,
        text=True,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1600:] or result.stdout[-1600:])
    payload = json.loads(result.stdout)
    require(not payload.get("truncated"), "The aggregate query was truncated.")
    return payload


def one_row_query(path: Path) -> dict[str, Any]:
    command = [
        str(PYTHON if PYTHON.exists() else sys.executable),
        str(HELPER),
        "--sql-file",
        str(path),
        "--max-rows",
        "20",
        "--reporting-mode",
        "presentation",
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1600:] or result.stdout[-1600:])
    payload = json.loads(result.stdout)
    rows = payload.get("rows")
    require(isinstance(rows, list) and len(rows) == 1, "The window audit must return one aggregate row.")
    return dict(rows[0])


def runtime_sql(records: list[dict[str, int]], baseline_snapshot: str, cutoff_date: str) -> str:
    source_json = json.dumps(records, separators=(",", ":")).replace("'", "''")
    template = RUNTIME_TEMPLATE.read_text(encoding="utf-8")
    return (
        template.replace("SOURCE_JSON", source_json)
        .replace("DISPLAY_SNAPSHOT", DISPLAY_SNAPSHOT)
        .replace("BASELINE_SNAPSHOT", baseline_snapshot)
        .replace("AUGUST_CUTOFF_DATE", cutoff_date)
    )


def main() -> None:
    require(WINDOW_AUDIT.exists() and RUNTIME_TEMPLATE.exists() and RETENTION_EVIDENCE.exists(), "Missing QVoice retention evidence input.")
    window = one_row_query(WINDOW_AUDIT)
    baseline_snapshot = str(window["baseline_snapshot"])
    cutoff_date = str(window["august_cutoff_date"])
    baseline_count = int(window["baseline_distinct_employee_count"])
    baseline_exits = int(window["voluntary_exit_count"])
    require(baseline_snapshot == "2025-08-24" and cutoff_date == "2026-08-23", "The August window is not the expected complete 12-month window.")
    require(baseline_count >= MINIMUM_COHORT and int(window["duplicate_baseline_employee_count"]) == 0, "The August baseline failed the uniqueness rule.")
    require(0 <= baseline_exits <= baseline_count, "The August voluntary-exit count is invalid.")

    _, retention_groups, source_quality = scan_comment_groups()
    retention_display = [str(value) for value in json.loads(RETENTION_EVIDENCE.read_text(encoding="utf-8"))["jan_2026_display"]["ranked_themes"]]
    require(all(label in retention_groups for label in retention_display), "A displayed theme was not reconstructed from the Jan-2026 workbook.")

    ordered: list[tuple[str, str]] = []
    records: list[dict[str, int]] = []
    for label in retention_display:
        members = retention_groups[label]
        require(len(members) >= MINIMUM_COHORT, f"Theme {label} is below the publication threshold.")
        code = len(ordered)
        ordered.append((label, label))
        records.extend({"employee_id": int(employee_id), "group_code": code} for employee_id in sorted(members))

    # The rows displayed in the chart are intentionally non-exclusive.  A
    # color reference therefore cannot be made by summing the five rows: that
    # would count a commenter (and potentially that person's exit) more than
    # once.  Add one separately deduplicated union cohort to the runtime
    # aggregate query.  Its only purpose is the common reference for the five
    # displayed pills; no employee identifiers leave this process.
    reference_code = len(ordered)
    reference_member_ids = set().union(*(retention_groups[label] for label, _ in ordered))
    require(len(reference_member_ids) >= MINIMUM_COHORT, "The QVoice theme reference cohort is below the publication threshold.")
    records.extend(
        {"employee_id": int(employee_id), "group_code": reference_code}
        for employee_id in sorted(reference_member_ids)
    )

    totals: dict[int, dict[str, int]] = {code: defaultdict(int) for code in range(reference_code + 1)}
    batch_size = 16_000
    for start in range(0, len(records), batch_size):
        payload = json_query(sql=runtime_sql(records[start : start + batch_size], baseline_snapshot, cutoff_date), max_rows=100)
        rows = payload.get("rows")
        require(isinstance(rows, list), "The runtime join did not return aggregate rows.")
        for row in rows:
            code = int(row["group_code"])
            for column in (
                "source_employee_count",
                "source_duplicate_employee_count",
                "matched_employee_count",
                "voluntary_exit_count",
            ):
                totals[code][column] += int(row.get(column) or 0)

    retention_source = json.loads(RETENTION_EVIDENCE.read_text(encoding="utf-8"))["waves"][-1]
    latest_themes = retention_source["themes"]
    rows: list[dict[str, Any]] = []
    for code, (label, _) in enumerate(ordered):
        aggregate = totals[code]
        source_count = int(aggregate["source_employee_count"])
        matched = int(aggregate["matched_employee_count"])
        exits = int(aggregate["voluntary_exit_count"])
        require(source_count == len(retention_groups[label]), f"Runtime source count does not reconcile for {label}.")
        require(MINIMUM_COHORT <= matched <= source_count and 0 <= exits <= matched, f"Runtime attrition cohort is invalid for {label}.")
        rate = round(100.0 * exits / matched, 4)
        require(abs(rate - 100.0 * exits / matched) < 0.00011, f"Attrition rate does not reconcile for {label}.")
        distribution_count = int(latest_themes[label]["participant_count"])
        distribution_pct = float(latest_themes[label]["percent_of_improvement_comment_participants"])
        require(distribution_count == source_count, f"Distribution count does not reconcile for {label}.")
        rows.append(
            {
                "theme": label,
                "distribution_count": distribution_count,
                "distribution_percent": distribution_pct,
                "source_employee_count": source_count,
                "matched_employee_count": matched,
                "unmatched_employee_count": source_count - matched,
                "voluntary_exit_count": exits,
                "trailing_12m_voluntary_attrition_rate_percent": rate,
                "publication_status": "publishable" if matched >= MINIMUM_COHORT and exits >= MINIMUM_COHORT else "suppressed_below_n_30",
            }
        )

    reference = totals[reference_code]
    reference_source = int(reference["source_employee_count"])
    reference_matched = int(reference["matched_employee_count"])
    reference_exits = int(reference["voluntary_exit_count"])
    reference_duplicates = int(reference["source_duplicate_employee_count"])
    require(reference_source == len(reference_member_ids), "The QVoice theme reference source count does not reconcile to the deduplicated union.")
    require(reference_duplicates == 0, "The QVoice theme reference union contains duplicate employee keys.")
    require(
        MINIMUM_COHORT <= reference_matched <= reference_source and MINIMUM_COHORT <= reference_exits <= reference_matched,
        "The QVoice theme reference cohort cannot support a publishable attrition rate.",
    )
    reference_rate = round(100.0 * reference_exits / reference_matched, 4)

    evidence = {
        "artifact": "presentation",
        "evidence_type": "aggregate-only Jan-2026 QVoice improvement-theme distribution with August trailing-12-month voluntary attrition",
        "generated_on": date.today().isoformat(),
        "outcome": "pass",
        "minimum_shared_cohort": MINIMUM_COHORT,
        "outcome_contract": {
            "display_snapshot": DISPLAY_SNAPSHOT,
            "baseline_snapshot": baseline_snapshot,
            "august_cutoff_date": cutoff_date,
            "window": f"({baseline_snapshot}, {cutoff_date}]",
            "label": "Trailing 12-month voluntary attrition through August 2026",
            "target": "Distinct term_type exactly VOLUNTARY after the August-2025 baseline and on or before the August-2026 cutoff.",
            "population": "Jan-2026 QVoice improvement-theme members matched to worker_type='Employee'; employee_type='Regular'; active_status=1 at the December-2025 display snapshot and August-2025 attrition baseline.",
            "grain": "Distinct employee in each non-exclusive Jan-2026 improvement-theme group.",
            "formula": "Distinct voluntary exits in the trailing window divided by the matched active-regular baseline employees in the same theme.",
        },
        "window_audit": window,
        "distribution_denominator": int(retention_source["improvement_comment_participants"]),
        "rows": rows,
        "reference_cohort": {
            "reference_id": "qvoice-theme-union",
            "label": "Unique employees in any displayed theme",
            "definition": "Distinct union of the five displayed Jan-2026 improvement themes; a person is counted once even when they match multiple themes.",
            "source_employee_count": reference_source,
            "matched_employee_count": reference_matched,
            "unmatched_employee_count": reference_source - reference_matched,
            "voluntary_exit_count": reference_exits,
            "trailing_12m_voluntary_attrition_rate_percent": reference_rate,
            "publication_status": "publishable",
        },
        "definition": {
            "distribution": "Jan-2026 selected improvement comments; denominator is 13,862 employees with at least one selected improvement comment.",
            "overlap": "Themes are non-exclusive; counts and percentages do not sum to 100%.",
            "explicit_intent_to_leave": "Suppressed below n=30 and not assigned an attrition rate.",
        },
        "validation": {
            "outcome": "pass",
            "source_quality": source_quality,
            "all_displayed_groups_have_n_at_least": MINIMUM_COHORT,
            "all_rates_reconcile_to_exits_and_matched_cohort": True,
            "reference_cohort_is_deduplicated_union": True,
            "reference_cohort_source_duplicate_employee_count": reference_duplicates,
            "reference_cohort_reconciles_to_exits_and_matched_cohort": True,
            "runtime_join_sql_persisted": False,
            "reason_runtime_join_sql_not_persisted": "The expanded query contains in-memory employee identifiers and returns aggregate counts only.",
            "themes_non_exclusive": True,
        },
        "privacy": {
            "employee_identifiers_persisted": False,
            "employee_rows_persisted": False,
            "raw_comment_text_persisted": False,
        },
        "provenance": {
            "window_audit": str(WINDOW_AUDIT.relative_to(ROOT)).replace("\\", "/"),
            "window_audit_sha256": sha256_path(WINDOW_AUDIT),
            "runtime_template": str(RUNTIME_TEMPLATE.relative_to(ROOT)).replace("\\", "/"),
            "runtime_template_sha256": sha256_path(RUNTIME_TEMPLATE),
            "source_evidence": str(RETENTION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "source_evidence_sha256": sha256_path(RETENTION_EVIDENCE),
            "raw_workbook": "data/QVoice/Jan 2026 Qvoice_raw data.xlsx, read in memory only",
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "window": evidence["outcome_contract"]["window"], "rows": len(rows), "outcome": "pass"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
