"""Pruebas del deck de evolución B → CQ (build_model_evolution_b_cq.py)."""
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools/presentations/build_model_evolution_b_cq.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_model_evolution_b_cq", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B = load_builder()


class FormatTests(unittest.TestCase):
    def test_fmt_integers_and_one_decimal(self):
        self.assertEqual(B.fmt(45.0), "45")
        self.assertEqual(B.fmt(43.14), "43.1")
        self.assertEqual(B.fmt(0.04), "<0.1")
        self.assertEqual(B.pct(10.98, 0), "11%")

    def test_get_missing_field_raises(self):
        with self.assertRaises(KeyError):
            B.get({"a": {}}, "a.b")


class DeckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(B.CONFIG.read_text(encoding="utf-8"))
        cls.ev = B.Evidence(cls.cfg)
        cls.f = B.compute(cls.ev)
        reg = json.loads((ROOT / cls.cfg["base_registry"]).read_text(encoding="utf-8"))
        base = (ROOT / reg["source_html"]).read_text(encoding="utf-8")
        cls.html = B.assemble(base, cls.cfg, B.slides(cls.f, cls.cfg))

    def test_key_figures_match_sources(self):
        f = self.f
        self.assertEqual(f["bc_red"], "11%")
        self.assertEqual(f["cq_red"], "2.3%")
        self.assertEqual(f["gain"], "+0.7")
        self.assertEqual([r["gap_s"] for r in f["rows"][1:]], ["4.1% larger", "0.8% smaller", "10.3% larger"])
        self.assertEqual([p["reading"] for p in f["periods"].values()], ["better", "tied"])
        self.assertEqual((f["groups"], f["combos"]), ("22", "36"))

    def test_cq_identical_in_s11_and_s12(self):
        s11 = self.ev.field("S11", 'summary.CQ.scenarios["30"]')
        s12 = self.ev.field("S12", 'summary.CQ.scenarios["30"]')
        for key in ("capture_percent", "group_snapshot_mae_pp"):
            self.assertAlmostEqual(s11[key], s12[key], delta=B.CQ_TOLERANCE)

    def test_visible_numbers_have_at_most_one_decimal(self):
        text = B.visible_text(self.html)
        self.assertEqual(re.findall(r"\d+\.\d{2,}", text), [])

    def test_structure_and_no_legacy_assets(self):
        self.assertEqual(self.html.count('class="slide-stage'), 9)
        self.assertEqual(len(re.findall(r'class="nav-pill[^"]*" data-slide="\d"', self.html)), 9)
        self.assertNotIn("d3.", self.html)
        body = self.html[self.html.index("<body"):]
        self.assertNotIn("wt-plane", body)  # el CSS heredado de la base puede mencionarlo
        self.assertNotIn("http://", self.html.replace("http://www.w3.org", ""))

    def test_no_jargon(self):
        self.assertEqual(B.jargon_hits(self.html), [])

    def test_verifier_only_language_exception(self):
        errors, _ = B.load_verifier().check(self.html, "presentation")
        self.assertEqual(errors, ['El elemento <html> debe declarar lang="es".'])

    def test_build_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                B.build(Path(tmp))


if __name__ == "__main__":
    unittest.main()
