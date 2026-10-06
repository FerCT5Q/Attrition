"""Render the requested Time in job profile / Time in role slide revision.

This is intentionally a targeted renderer: the V7 deck contains many unrelated
slides, so it replaces only stage 29 from newly executed aggregate evidence.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"
EVIDENCE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.time-in-job-profile-time-in-role-evidence-20260918.json"
)
MANIFEST = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.time-in-job-profile-time-in-role-revision-20260918.json"
)
BANDS = ("<1 year", "1–<2 years", "2–<3 years", "3–<5 years", "5–<10 years", "10+ years")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def card(heading: str, rows: list[dict[str, Any]]) -> str:
    by_band = {str(row["category"]): row for row in rows}
    require(set(by_band) == set(BANDS), f"{heading} does not have the expected six bands.")
    ordered = [by_band[band] for band in BANDS]
    total = sum(int(row["employee_count"]) for row in ordered)
    maximum = max(int(row["employee_count"]) for row in ordered)
    require(total > 0 and maximum > 0, f"{heading} has an empty distribution.")
    bar_rows = []
    for row in ordered:
        label = str(row["category"])
        count = int(row["employee_count"])
        share = round(100 * count / total)
        width = 100 * count / maximum
        escaped_label = html.escape(label)
        bar_rows.append(
            '<div class="bar-row">'
            f'<div class="bar-label" title="{escaped_label}">{escaped_label}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div>'
            f'<div class="bar-value">{share}% · {count:,}</div>'
            "</div>"
        )
    return (
        '<article class="card chart-card v6-distribution-only role-level-tenure-card">'
        f'<div class="v6-panel-heading"><span>{html.escape(heading)}</span><span>Current distribution</span></div>'
        '<div class="bar-list">' + "".join(bar_rows) + "</div>"
        "</article>"
    )


def build_stage(evidence: dict[str, Any]) -> str:
    display = evidence["display_rows"]
    job_profile_rows = display["time_in_job_profile"]
    time_in_role_rows = display["time_in_role"]
    snapshot_dates = {str(row["snapshot_date"]) for row in job_profile_rows + time_in_role_rows}
    require(len(snapshot_dates) == 1, "The two displayed measures must use the same snapshot.")
    snapshot_date = date.fromisoformat(snapshot_dates.pop()).strftime("%d %b %Y")
    return (
        '<div class="slide-stage" id="slide-29" data-v6-playbook="true">'
        '<div class="slide-heading"><div>'
        '<h2 class="slide-title-text">Time in job profile and time in role</h2>'
        '<p class="slide-subtitle">These two measures describe time in the current job differently; read each chart separately</p>'
        '</div><span class="badge badge-info">Current distribution</span></div>'
        '<article class="card card-full v6-playbook-card">'
        '<div class="v6-definition-strip">'
        '<div><span class="v6-mini-label">Definition</span><strong>Each chart measures time in the current job in a different way</strong></div>'
        '<div><span class="v6-mini-label">Population</span><strong>Active regular employees, excluding RF360</strong></div>'
        '</div><div class="v6-chart-area"><div class="two-pane"><div class="two-chart">'
        + card("Time in job profile", job_profile_rows)
        + card("Time in role", time_in_role_rows)
        + '</div></div></div>'
        '<div class="v6-source-line"><strong>Source:</strong> HRDA - hrda.post_hire_monthly_worker_dtls. '
        f'Current distribution: active regular employees at {snapshot_date}. '
        'Annual attrition will be added once enough comparable monthly history is available.</div>'
        '</article></div>'
    )


def stage_fragment(deck: str) -> str:
    match = re.search(
        r'(<div class="slide-stage" id="slide-29".*?)(?=\n\s*<div class="slide-stage"|\n\s*<script|\Z)',
        deck,
        flags=re.S,
    )
    require(match is not None, "The V7 tenure slide (slide-29) is missing.")
    return match.group(1)


def main() -> None:
    require(DECK.exists(), f"Missing deck: {DECK}")
    require(EVIDENCE.exists(), f"Missing evidence: {EVIDENCE}")
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    require(evidence.get("outcome") == "pass", "The revised tenure evidence did not pass safe-display validation.")
    require(evidence.get("annual_attrition_status") == "not_estimable_insufficient_longitudinal_coverage", "The annual-rate limitation is missing.")
    require(all(not status["annual_attrition_displayable"] for status in evidence["coverage"].values()), "No annual rate may be rendered for this revision.")

    deck = DECK.read_text(encoding="utf-8")
    original = stage_fragment(deck)
    replacement = build_stage(evidence)
    require(deck.count(original) == 1, "The V7 tenure slide is not uniquely replaceable.")
    updated = deck.replace(original, replacement, 1)
    updated_stage = stage_fragment(updated)
    require("Time in job profile and time in role" in updated_stage, "The revised title is missing.")
    require("field proxy" not in updated_stage and "detailed level" not in updated_stage.lower(), "Removed technical terminology remains in the revised slide.")
    require("v7-annual-attrition" not in updated_stage, "The revised slide must not imply that annual attrition is available.")
    require("employee_id" not in updated_stage.lower(), "The revised slide must not expose employee IDs.")
    DECK.write_text(updated, encoding="utf-8")

    manifest = {
        "artifact_type": "slide_revision_manifest",
        "generated_on": date.today().isoformat(),
        "parent_deck": str(DECK.relative_to(ROOT)).replace("\\", "/"),
        "parent_deck_deliverable_mode": "internal_analysis",
        "revised_slide": {"stage_id": "slide-29", "navigation_slide": 27, "title": "Time in job profile and time in role"},
        "slide_data_mode": "presentation",
        "evidence": {
            "path": str(EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(EVIDENCE.read_bytes()).hexdigest(),
            "annual_attrition_status": evidence["annual_attrition_status"],
            "coverage": evidence["coverage"],
        },
        "changes": [
            "Removed Time at current detailed level.",
            "Removed field proxy terminology.",
            "Added current distributions for Time in job profile and Time in role.",
            "Withheld annual attrition values from the graph because longitudinal coverage is not yet sufficient.",
        ],
        "output_sha256": hashlib.sha256(DECK.read_bytes()).hexdigest(),
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(DECK)
    print(MANIFEST)


if __name__ == "__main__":
    main()
