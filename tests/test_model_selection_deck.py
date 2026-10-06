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


deck = _load("build_model_selection_deck", ROOT / "tools" / "presentations" / "build_model_selection_deck.py")
verify = _load("verify_deck", ROOT / ".agents" / "skills" / "build-html-presentation" / "scripts" / "verify_deck.py")


class ModelSelectionDeckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = deck.load_data()
        cls.html = deck.render("es")

    def test_figures_match_sources(self):
        self.assertEqual(deck.fmt(self.data["base_ct"]), "3.2")
        self.assertEqual(deck.fmt(self.data["hazard_top10"]), "15.1")
        self.assertEqual(deck.fmt(self.data["logistic_top10"]), "15.6")
        self.assertEqual(deck.fmt(self.data["season_ratio"]), "1.7")
        self.assertEqual([deck.fmt(v) for _, v in self.data["tenure"]], ["2.7", "3.7", "4.2", "3.2", "2.3", "1.3"])

    def test_format_rule(self):
        self.assertEqual(deck.fmt(10.0), "10")
        self.assertEqual(deck.fmt(3.1588), "3.2")
        self.assertEqual(deck.fmt(9296), "9,296")

    def test_structure(self):
        self.assertEqual(len(re.findall(r'class="slide-stage\b', self.html)), 8)
        self.assertEqual(sorted(int(i) for i in re.findall(r'nav-pill[^"]*" data-slide="(\d+)"', self.html)), list(range(8)))

    def test_verify_deck_passes(self):
        errors, _ = verify.check(self.html, "presentation")
        self.assertEqual(errors, [])

    def test_no_technical_jargon_visible(self):
        visible = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", self.html, flags=re.DOTALL)
        visible = re.sub(r"<!--.*?-->|<[^>]+>", " ", visible, flags=re.DOTALL)
        for term in ("lift", "PR-AUC", "hazard", "LightGBM", "cloglog", "Brier"):
            self.assertNotIn(term.lower(), visible.lower(), term)


if __name__ == "__main__":
    unittest.main()
