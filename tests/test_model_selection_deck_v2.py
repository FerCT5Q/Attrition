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


deck = _load("build_model_selection_deck_v2", ROOT / "tools" / "presentations" / "build_model_selection_deck_v2.py")
verify = _load("verify_deck", ROOT / ".agents" / "skills" / "build-html-presentation" / "scripts" / "verify_deck.py")


class ModelSelectionDeckV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = deck.load_data()
        cls.html = deck.render()

    def test_figures_match_rolling_comparison(self):
        self.assertEqual(self.data["params"], 33)
        self.assertIn("16.6", self.html)
        self.assertIn("14.6", self.html)
        self.assertIn("17.6", self.html)

    def test_format_rule(self):
        self.assertEqual(deck.fmt(10.0), "10")
        self.assertEqual(deck.fmt(3.1588), "3.2")
        self.assertEqual(deck.pct_change(1.670), "+67%")
        self.assertEqual(deck.pct_change(0.774), "−23%")

    def test_structure(self):
        self.assertEqual(len(re.findall(r'class="slide-stage\b', self.html)), 9)

    def test_verify_deck_passes(self):
        errors, _ = verify.check(self.html, "presentation")
        self.assertEqual(errors, [])

    def test_no_individual_identifiers(self):
        visible = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", self.html, flags=re.DOTALL)
        visible = re.sub(r"<!--.*?-->|<[^>]+>", " ", visible, flags=re.DOTALL)
        for term in ("employee_id", "emplid", "@qualcomm.com", "cloglog", "Brier"):
            self.assertNotIn(term.lower(), visible.lower(), term)


if __name__ == "__main__":
    unittest.main()
