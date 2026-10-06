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


deck = _load("build_model_selection_deck_v4", ROOT / "tools" / "presentations" / "build_model_selection_deck_v4.py")
verify = _load("verify_deck", ROOT / ".agents" / "skills" / "build-html-presentation" / "scripts" / "verify_deck.py")


def _visible(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL)
    return re.sub(r"<!--.*?-->|<[^>]+>", " ", text, flags=re.DOTALL)


class ModelSelectionDeckV4Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = deck.load_data()
        cls.html = deck.render()
        cls.visible = _visible(cls.html)

    def test_literature_counts(self):
        self.assertEqual(self.data["lit"]["count"], 43)
        self.assertEqual(self.data["lit"]["years"], (1972, 2026))
        self.assertIn("revisamos 43 trabajos en 5 temas", self.visible)

    def test_final_model_figures(self):
        self.assertEqual(self.data["final"]["parameters"], 53)
        for figure in ("20.1", "contra 20 de cada 100", "10.9%", "53 coeficientes", "5.3%", "37,221"):
            self.assertIn(figure, self.visible)

    def test_groups_respect_minimums(self):
        groups = self.data["groups"]["groups"]
        self.assertEqual(len(groups), 8)
        self.assertTrue(all(g["people"] >= 300 and g["last_fold_events"] >= 30 for g in groups))
        self.assertEqual(self.html.count('class="grp-row'), 8)

    def test_structure(self):
        self.assertEqual(len(re.findall(r'class="slide-stage\b', self.html)), 15)
        self.assertEqual(len(re.findall(r'class="nav-pill[^"]*" data-slide="\d+"', self.html)), 15)

    def test_verify_deck_passes(self):
        errors, _ = verify.check(self.html, "presentation")
        self.assertEqual(errors, [])

    def test_no_individual_identifiers_or_jargon(self):
        for term in ("employee_id", "emplid", "@qualcomm.com", "cloglog", "Brier", "Segmento</div>"):
            self.assertNotIn(term.lower(), self.visible.lower(), term)

    def test_no_decimals_beyond_one(self):
        self.assertEqual(re.findall(r"\d+\.\d{2,}", self.visible), [])


if __name__ == "__main__":
    unittest.main()
