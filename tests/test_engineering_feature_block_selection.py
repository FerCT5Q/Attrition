import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import engineering_feature_block_selection as fs  # noqa: E402


def spec(blocks, pr, lift, parameters):
    return {"blocks": blocks, "parameters": parameters, "summary": {"pr_auc": pr, "lift_at_10_percent": lift}}


class FeatureBlockSelectionTest(unittest.TestCase):
    def test_sql_never_outputs_restricted_columns(self):
        with self.assertRaises(RuntimeError):
            fs.check_output_columns(fs.OUTPUT_COLUMNS[:-1] + ["employee_id"])
        fs.check_output_columns(list(fs.OUTPUT_COLUMNS))

    def test_parsimony_picks_fewest_blocks_within_tolerance(self):
        evaluated = {
            (): spec([], 0.040, 1.60, 20),
            ("carrera",): spec(["carrera"], 0.0455, 1.72, 21),
            ("carrera", "geografia"): spec(["carrera", "geografia"], 0.0460, 1.75, 24),
        }
        chosen, rule = fs.parsimonious_choice(evaluated)
        self.assertEqual(chosen["blocks"], ["carrera"])
        self.assertEqual(len(rule["eligible"]), 2)

    def test_parsimony_requires_both_metrics(self):
        evaluated = {
            ("carrera",): spec(["carrera"], 0.0459, 1.60, 21),
            ("carrera", "geografia"): spec(["carrera", "geografia"], 0.0460, 1.75, 24),
        }
        chosen, _ = fs.parsimonious_choice(evaluated)
        self.assertEqual(chosen["blocks"], ["carrera", "geografia"])

    def test_query_does_not_select_identifiers(self):
        sql = fs.FRAME_QUERY.read_text(encoding="utf-8")
        final_select = sql.rsplit("\nSELECT", 1)[1].split("\nFROM pop p")[0]
        for column in ["employee_id", "manager_id", "compa_ratio", " cr,"]:
            self.assertNotIn(f"p.{column.strip(' ,')} AS", final_select)
        self.assertNotIn("p.employee_id,", final_select)


if __name__ == "__main__":
    unittest.main()
