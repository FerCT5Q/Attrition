"""Deck-side tests for the normalized-within-region QVoice slide."""

from __future__ import annotations

import importlib.util
import html
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
DECK_BUILDER = ROOT / "tools" / "build_distribution_html_v2.py"
EVIDENCE_TEST = ROOT / "tests" / "test_qvoice_normalized_region_evidence.py"

DECK_SPEC = importlib.util.spec_from_file_location("distribution_builder_qvoice_normalized_test", DECK_BUILDER)
assert DECK_SPEC is not None and DECK_SPEC.loader is not None
DECK = importlib.util.module_from_spec(DECK_SPEC)
DECK_SPEC.loader.exec_module(DECK)

EVIDENCE_SPEC = importlib.util.spec_from_file_location("qvoice_normalized_evidence_fixture", EVIDENCE_TEST)
assert EVIDENCE_SPEC is not None and EVIDENCE_SPEC.loader is not None
FIXTURE = importlib.util.module_from_spec(EVIDENCE_SPEC)
EVIDENCE_SPEC.loader.exec_module(FIXTURE)


class QVoiceNormalizedRegionSlideTests(unittest.TestCase):
    def test_loader_accepts_safe_frozen_evidence_and_renders_low_to_high_bands(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "qvoice-normalized.json"
            path.write_text(json.dumps(FIXTURE.valid_evidence()), encoding="utf-8")
            evidence = DECK.qvoice_normalized_region_evidence(path)

        slide = DECK.qvoice_normalized_region_slide(24, evidence)
        band_labels = [label for label, _, _ in FIXTURE.MODULE.Z_BANDS]
        positions = [slide.index(html.escape(label)) for label in band_labels]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Within-region standardized-score distribution", slide)
        self.assertIn("no regional labels or individual scores are displayed", slide)
        self.assertNotIn("employee_id", slide)

    def test_failed_evidence_keeps_the_support_state(self):
        with mock.patch.object(DECK, "qvoice_normalized_region_evidence", side_effect=ValueError("bad evidence")):
            label, slide = DECK.qvoice_normalized_region_slide_or_support(24)
        self.assertEqual(label, "Standardized within region")
        self.assertIn("No unverified standardized distribution is published", slide)

    def test_hides_a_too_narrow_segment_label_without_hiding_its_tooltip(self):
        bands = [
            {"band": label, "participant_count": 100, "percent_of_normalized": percent}
            for (label, _, _), percent in zip(
                FIXTURE.MODULE.Z_BANDS, [16.0, 8.0, 32.0, 42.0, 2.0]
            )
        ]
        rendered = DECK.qvoice_normalized_region_stack_segments(bands)
        self.assertIn(">8%</span>", rendered)
        self.assertNotIn(">2%</span>", rendered)
        self.assertIn("2.0000%", rendered)


if __name__ == "__main__":
    unittest.main()
