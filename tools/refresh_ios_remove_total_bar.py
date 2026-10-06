"""Remove the redundant IOS total row from the rendered V7 chart."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"
MANIFEST = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7-manifest.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def stage_fragment(deck: str) -> str:
    match = re.search(
        r'(<div class="slide-stage" id="slide-5".*?)(?=\n\s*<div class="slide-stage"|\n\s*<script|\Z)',
        deck,
        flags=re.S,
    )
    require(match is not None, "Could not locate the IOS movement slide.")
    return match.group(1)


def main() -> None:
    deck = DECK.read_text(encoding="utf-8")
    stage = stage_fragment(deck)
    row_marker = '<div class="bar-row v4-inline-attrition-row ios-ytd-bar-row">'
    row_starts = [match.start() for match in re.finditer(re.escape(row_marker), stage)]
    require(len(row_starts) == 7, f"Expected seven IOS rows before refresh, found {len(row_starts)}.")
    require("All IOS movements" in stage, "The total IOS row is already absent.")

    first_start, second_start = row_starts[0], row_starts[1]
    stage = stage[:first_start] + stage[second_start:]
    stage = stage.replace("IOS movements represent 14.7%", "IOS movements represent 11.4%", 1)
    stage = stage.replace(
        "each bar is the share of the average active regular workforce; n and observed voluntary attrition are shown at right.",
        "each bar is the share of the average active regular workforce, scaled to the largest reason shown; n and observed voluntary attrition are shown at right.",
        1,
    )
    stage = stage.replace('style="width:86.0%"', 'style="width:100.0%"', 1)
    require("All IOS movements" not in stage, "The redundant IOS total row remains after refresh.")
    require(stage.count("ios-ytd-bar-row") == 6, "The refreshed slide must contain six reason rows.")
    require('style="width:100.0%"' in stage, "The largest visible reason is not scaled to the full track.")

    original = stage_fragment(deck)
    updated_deck = deck.replace(original, stage, 1)
    require(updated_deck != deck, "The IOS slide did not change.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["updated_slide"]["title"] = "IOS movements represent 11.4% of the active regular workforce in 2026 YTD"
    manifest["updated_slide"]["visual"] = (
        "One 2026 YTD horizontal-bar panel showing six IOS movement reasons, workforce share, cohort n, "
        "and observed voluntary-attrition pills; the redundant overall bar is removed."
    )
    manifest["validation"]["rendered_group_year_rows"] = 6
    manifest["validation"]["ios_total_bar_removed"] = True
    manifest["validation"]["ios_reason_bars_visible"] = 6
    manifest["output_deck"]["sha256"] = hashlib.sha256(updated_deck.encode("utf-8")).hexdigest()
    DECK.write_text(updated_deck, encoding="utf-8")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(DECK)
    print(MANIFEST)


if __name__ == "__main__":
    main()
