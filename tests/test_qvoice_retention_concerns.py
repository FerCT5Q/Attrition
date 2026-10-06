"""Unit and publication-gate coverage for QVoice retention-concerns slide 19."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_BUILDER = ROOT / "tools" / "build_qvoice_retention_concerns_evidence.py"
DECK_BUILDER = ROOT / "tools" / "build_distribution_html_v2.py"

EVIDENCE_SPEC = importlib.util.spec_from_file_location("qvoice_retention_evidence_test", EVIDENCE_BUILDER)
assert EVIDENCE_SPEC is not None and EVIDENCE_SPEC.loader is not None
EVIDENCE = importlib.util.module_from_spec(EVIDENCE_SPEC)
EVIDENCE_SPEC.loader.exec_module(EVIDENCE)

DECK_SPEC = importlib.util.spec_from_file_location("qvoice_retention_deck_test", DECK_BUILDER)
assert DECK_SPEC is not None and DECK_SPEC.loader is not None
DECK = importlib.util.module_from_spec(DECK_SPEC)
DECK_SPEC.loader.exec_module(DECK)


def published_metric(count: int, denominator: int = 100) -> dict[str, object]:
    return {
        "participant_count": count,
        "percent_of_improvement_comment_participants": round(100 * count / denominator, 2),
        "publication_status": "published",
    }


def valid_evidence() -> dict[str, object]:
    themes = list(EVIDENCE.TAXONOMY)
    waves = []
    for index, config in enumerate(EVIDENCE.WAVES):
        counts = {theme: 90 - position * 6 - index for position, theme in enumerate(themes)}
        wave_themes = {theme: published_metric(count) for theme, count in counts.items()}
        waves.append(
            {
                "wave": config["wave"],
                "source_file": config["file"],
                "sheet": "Raw data",
                "prompt_availability": {
                    "can_improve": True,
                    "processes_to_improve": bool(config["processes_expected"]),
                },
                "selected_prompt_rule": "fixture",
                "participant_rows": 100,
                "distinct_participant_keys": 100,
                "improvement_comment_participants": 100,
                "rows_with_improvement_comment": 100,
                "improvement_comments_without_key": 0,
                "duplicate_participant_rows": 0,
                "themes": wave_themes,
                "explicit_intent_to_leave": EVIDENCE.publication_metric(2, 100),
            }
        )
    ranked = EVIDENCE.rank_publishable_themes(waves[-1]["themes"])
    return {
        "artifact": "internal_analysis",
        "evidence_type": "aggregate-only QVoice improvement themes relevant to retention",
        "generated_on": "2026-09-10",
        "outcome": "pass",
        "minimum_cohort": EVIDENCE.MINIMUM_COHORT,
        "scope": "Descriptive only; no attrition join.",
        "source_rule": "Original prompts only.",
        "denominator_rule": "Distinct participants with selected improvement comments.",
        "grain": "Distinct participant-wave-theme; themes are non-exclusive.",
        "deduplication_rule": "One participant per wave and theme.",
        "comment_text_persisted": False,
        "identifiers_persisted": False,
        "employee_rows_persisted": False,
        "taxonomy": {theme: {"alignment": "fixture"} for theme in themes},
        "explicit_intent_to_leave_rule": "fixture",
        "waves": waves,
        "jan_2026_display": {
            "ranked_themes": ranked,
            "trend_themes": ranked[: EVIDENCE.TREND_THEME_COUNT],
            "explicit_intent_to_leave": waves[-1]["explicit_intent_to_leave"],
            "trend_comparability_note": "fixture",
        },
        "acceptance_rule": {"fixture": True},
    }


class QVoiceRetentionConcernsTests(unittest.TestCase):
    def test_fixed_taxonomy_matches_expected_concepts(self):
        self.assertEqual(
            list(EVIDENCE.TAXONOMY),
            [
                "Rewards",
                "Career growth and promotion",
                "Manager, leadership and respect",
                "Workload, staffing and work-life",
                "Work arrangement/RTO/commute",
                "Tools, processes and bureaucracy",
                "Organizational confidence/job security",
            ],
        )
        self.assertEqual(
            EVIDENCE.classify_themes("A salary increase, career path and hybrid work policy would help."),
            {"Rewards", "Career growth and promotion", "Work arrangement/RTO/commute"},
        )

    def test_deduplicates_one_participant_per_wave_theme(self):
        aggregate = EVIDENCE._aggregate_records(
            [
                {"participant_key": "A", "can_improve": "salary and benefits", "processes_to_improve": ""},
                {"participant_key": "A", "can_improve": "a pay raise", "processes_to_improve": ""},
                {"participant_key": "B", "can_improve": "career path", "processes_to_improve": ""},
            ]
        )
        self.assertEqual(aggregate["duplicate_participant_rows"], 1)
        self.assertEqual(aggregate["improvement_comment_participants"], 2)
        self.assertEqual(aggregate["themes"]["Rewards"]["publication_status"], "suppressed_below_n_30")

    def test_explicit_leave_intent_requires_multiword_nonnegated_phrase(self):
        self.assertTrue(EVIDENCE.contains_explicit_intent_to_leave("I am looking for another job because of the workload."))
        self.assertTrue(EVIDENCE.contains_explicit_intent_to_leave("Estoy buscando otro trabajo."))
        self.assertFalse(EVIDENCE.contains_explicit_intent_to_leave("I am not planning to leave the company."))
        self.assertFalse(EVIDENCE.contains_explicit_intent_to_leave("No quiero dejar la empresa."))
        self.assertFalse(EVIDENCE.contains_explicit_intent_to_leave("People leave sometimes."))

    def test_low_cohort_suppression_and_deterministic_ties(self):
        self.assertEqual(EVIDENCE.publication_metric(29, 100)["participant_count"], None)
        self.assertEqual(
            EVIDENCE.publication_metric(29, 100)["publication_status"],
            "suppressed_below_n_30",
        )
        metrics = {
            theme: published_metric(50)
            for theme in list(EVIDENCE.TAXONOMY)[:6]
        }
        self.assertEqual(
            EVIDENCE.rank_publishable_themes(metrics),
            list(EVIDENCE.TAXONOMY)[: EVIDENCE.TOP_THEME_COUNT],
        )

    def test_prompt_contract_and_private_payload_gates(self):
        fixture = valid_evidence()
        self.assertEqual(EVIDENCE.validate_evidence(fixture)["outcome"], "pass")

        wrong_prompt = copy.deepcopy(fixture)
        wrong_prompt["waves"][0]["prompt_availability"]["processes_to_improve"] = True
        with self.assertRaisesRegex(ValueError, "Prompt contract"):
            EVIDENCE.validate_evidence(wrong_prompt)

        private_payload = copy.deepcopy(fixture)
        private_payload["waves"][0]["comment_text"] = "not allowed"
        with self.assertRaisesRegex(ValueError, "private payload"):
            EVIDENCE.validate_evidence(private_payload)

    def test_slide_renders_top_five_trend_and_suppressed_intent(self):
        fixture = valid_evidence()
        slide = DECK.qvoice_retention_concerns_slide(19, fixture)
        self.assertIn("Retention concerns in QVoice comments", slide)
        self.assertIn("Explicit intent-to-leave wording", slide)
        self.assertIn("Not publishable (&lt;30)", slide)
        self.assertIn("2025–2026 also include the processes-to-improve prompt", slide)
        self.assertIn("slide 18 retains the detailed RTO/hybrid view", slide)
        self.assertNotIn("comment_text", slide)
        self.assertNotIn("participant_key", slide)

    def test_focused_refresh_injects_retention_styles_once(self):
        bare_deck = "<html><head><style>body{}</style></head><body></body></html>"
        refreshed = DECK.inject_retention_concerns_focused_css(bare_deck)
        self.assertIn('id="qvoice-retention-concerns-css"', refreshed)
        self.assertIn(".retention-theme-fill", refreshed)
        self.assertEqual(
            refreshed,
            DECK.inject_retention_concerns_focused_css(refreshed),
        )


if __name__ == "__main__":
    unittest.main()
