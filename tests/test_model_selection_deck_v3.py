import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deck = _load("build_model_selection_deck_v3", ROOT / "tools" / "presentations" / "build_model_selection_deck_v3.py")
verify = _load("verify_deck", ROOT / ".agents" / "skills" / "build-html-presentation" / "scripts" / "verify_deck.py")


def _visible(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL)
    return re.sub(r"<!--.*?-->|<[^>]+>", " ", text, flags=re.DOTALL)


class ModelSelectionDeckV3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = deck.load_data()
        cls.html = deck.render()
        cls.visible = _visible(cls.html)

    def test_figures_match_noseg_comparison(self):
        self.assertEqual(self.data["params"], 25)
        for figure in ("17.1", "16.4", "10.9%", "5,420"):
            self.assertIn(figure, self.visible)

    def test_groups_are_published_with_minimum_size(self):
        self.assertEqual(len(self.data["groups_now"]), 24)
        self.assertTrue(all(g["people_per_snapshot"] >= 30 for g in self.data["groups_now"]))
        self.assertTrue(all(g["events"] >= 30 for g in self.data["test_groups"]))
        self.assertEqual(self.html.count('class="empty"'), 4)

    def test_segment_is_not_a_model_signal(self):
        self.assertNotIn("Segmento", re.findall(r'<div class="side-head">([^<]+)</div>', self.html))
        self.assertIn("sin segmento ni job family", self.visible)

    def test_structure(self):
        self.assertEqual(len(re.findall(r'class="slide-stage\b', self.html)), 13)
        self.assertEqual(len(re.findall(r'class="nav-pill[^"]*" data-slide="\d+"', self.html)), 13)

    def test_verify_deck_passes(self):
        errors, _ = verify.check(self.html, "presentation")
        self.assertEqual(errors, [])

    def test_no_individual_identifiers(self):
        for term in ("employee_id", "emplid", "@qualcomm.com", "cloglog", "Brier"):
            self.assertNotIn(term.lower(), self.visible.lower(), term)


if __name__ == "__main__":
    unittest.main()
