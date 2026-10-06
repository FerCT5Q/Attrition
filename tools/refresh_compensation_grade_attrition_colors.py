"""Apply relative low/middle/high attrition colors to V7 slide 34."""

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
        r'(<div class="slide-stage" id="slide-38".*?)(?=\n\s*<div class="slide-stage"|\n\s*<script|\Z)',
        deck,
        flags=re.S,
    )
    require(match is not None, "Could not locate the compensation-grade slide.")
    return match.group(1)


def relative_class(rate: float, rates: list[float]) -> str:
    ordered = sorted(rates)
    low_threshold = ordered[len(ordered) // 3]
    high_threshold = ordered[(2 * len(ordered)) // 3]
    if rate <= low_threshold:
        return "attr-low"
    if rate >= high_threshold:
        return "attr-high"
    return "attr-mid"


def main() -> None:
    deck = DECK.read_text(encoding="utf-8")
    original_stage = stage_fragment(deck)
    pill_pattern = re.compile(
        r'(?P<prefix><span class="v7-annual-attrition v6-rate-pill )'
        r'(?P<class>attr-(?:low|mid|high))'
        r'(?P<suffix>[^" ]*(?: [^"]*)?"[^>]*>[^<]*</span>)',
        flags=re.S,
    )
    rates = [
        float(rate)
        for rate in re.findall(
            r'title="Annual voluntary attrition for [^"]+: (\d+(?:\.\d+)?)%"',
            original_stage,
        )
    ]
    require(len(rates) == 37, f"Expected 37 publishable compensation-grade pills, found {len(rates)}.")

    rate_iter = iter(rates)

    def replace_pill(match: re.Match[str]) -> str:
        rate = next(rate_iter)
        return match.group("prefix") + relative_class(rate, rates) + match.group("suffix")

    updated_stage, replacements = pill_pattern.subn(replace_pill, original_stage)
    require(replacements == 37, f"Expected to recolor 37 pills, changed {replacements}.")
    updated = deck.replace(original_stage, updated_stage, 1)
    require(updated != deck, "The compensation-grade slide did not change.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["updated_slide_34_compensation_grade_color_encoding"] = {
        "navigation_slide_number": 34,
        "stage_id": "slide-38",
        "method": "Relative tertile bands across publishable compensation-grade annual attrition rates.",
        "low": "Green: lower third",
        "middle": "Blue: middle third",
        "high": "Orange: upper third",
        "publishable_pill_count": replacements,
        "stage_sha256": hashlib.sha256(updated_stage.encode("utf-8")).hexdigest(),
        "outcome": "pass",
    }

    DECK.write_text(updated, encoding="utf-8")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(DECK)
    print(MANIFEST)


if __name__ == "__main__":
    main()
