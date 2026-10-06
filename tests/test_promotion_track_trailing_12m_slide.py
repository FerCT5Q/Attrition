import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"


def stage(deck: str, stage_id: str) -> str:
    match = re.search(
        rf'(<div class="slide-stage" id="{re.escape(stage_id)}".*?)(?=\n\s*<div class="slide-stage"|\n\s*<script|\Z)',
        deck,
        re.S,
    )
    if not match:
        raise AssertionError(stage_id)
    return match.group(1)


class PromotionTrackSlideTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deck = DECK.read_text(encoding="utf-8")
        cls.target = stage(cls.deck, "slide-34")

    def test_slide_and_navigation_integrity(self):
        stage_count = len(re.findall(r'<div class="slide-stage" id="[^"]+"', self.deck))
        self.assertGreaterEqual(stage_count, 30)
        nav = [int(value) for value in re.findall(r'<button class="nav-pill(?: pill-active)?" data-slide="(\d+)">', self.deck)]
        self.assertEqual(nav, list(range(stage_count)))
        self.assertGreaterEqual(self.deck.count('data-evidence-run="promotion-track-trailing-12m-20260918"'), 1)

    def test_old_matrix_removed_and_new_rows_present(self):
        self.assertNotIn("promotion-grade-matrix", self.target)
        self.assertEqual(self.target.count('class="track-story-row"'), 6)
        self.assertNotIn("track-story-mini-bar", self.target)
        self.assertEqual(self.target.count("v6-rate-pill attr-"), 6)
        self.assertEqual(self.target.count("track-story-rate-value"), 6)
        self.assertEqual(self.target.count("attr-low"), 1)
        self.assertEqual(self.target.count("attr-high"), 1)
        for track in ("R", "T", "P", "M", "S", "V"):
            self.assertIn(f'aria-label="Track {track}"', self.target)
        self.assertIn("Promotion and attrition by pay track", self.target)
        self.assertIn("M10, M20 and M30 appear as M", self.target)
        self.assertIn("latest annual review", self.target)
        self.assertIn("99.96%", self.target)
        self.assertNotIn("employee_id", self.target.lower())
        for spanish_text in ("Promoción", "Distribución", "Cómo leerlo", "Ventana", "Fuente"):
            self.assertNotIn(spanish_text, self.target)

    def test_theme_and_navigation_contract_remains(self):
        self.assertIn('id="theme-selector"', self.deck)
        self.assertIn('theme-light-classic', self.deck)
        self.assertIn('theme-light-soft', self.deck)
        self.assertIn('theme-dark-royal', self.deck)
        self.assertIn('theme-dark-carbon', self.deck)
        self.assertIn('id="slide-nav"', self.deck)


if __name__ == "__main__":
    unittest.main()
