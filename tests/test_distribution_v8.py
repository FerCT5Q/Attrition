"""Structural and privacy checks for the V8 internal exploratory deck."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v8.html"
MANIFEST = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v8-manifest.json"
COLOR_POLICY = ROOT / "config" / "attrition_color_policy_v8.json"
COLOR_EVIDENCE = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v8.attrition-color-reference-evidence-20260924.json"
ACQUISITION_EVIDENCE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v8.acquisition-entry-evidence-20260929.json"
)
V7_DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"
COMPARABLE_PROMOTION_EVIDENCE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "attrition-43-variable-distributions-v7.time-since-last-promotion-comparable-cohorts-evidence-20260924.json"
)
QVOICE_THEME_EVIDENCE = (
    ROOT
    / "output"
    / "distribution"
    / "json"
    / "qvoice-retention-theme-august-trailing-12m-attrition-evidence-20260922.json"
)
BUILDER_PATH = ROOT / "tools" / "build_distribution_html_v8.py"
FROZEN_V7_SHA256 = "f08bfd9a43b73f75f5fe80184a71f9945e86f352962f8b38ff0249d640cee967"

BUILDER_SPEC = importlib.util.spec_from_file_location("distribution_v8_builder", BUILDER_PATH)
if BUILDER_SPEC is None or BUILDER_SPEC.loader is None:  # pragma: no cover - import setup failure
    raise RuntimeError("Could not import the V8 deck builder for formatter tests.")
V8_BUILDER = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(V8_BUILDER)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_html(deck: str, stage_id: str) -> str:
    pattern = rf'<div class="slide-stage" id="{re.escape(stage_id)}".*?(?=\n\s*<div class="slide-stage"|\n\s*<div class="nav-ctrl")'
    match = re.search(pattern, deck, flags=re.S)
    if match is None:
        raise AssertionError(f"Missing stage {stage_id}.")
    return match.group(0)


def visible_decimal_tokens(deck: str) -> list[str]:
    """Collect non-rate reader-visible decimal text while excluding code and geometry."""
    values: list[str] = []
    segments = V8_BUILDER.READER_PROTECTED_BLOCK.split(deck)
    for index in range(0, len(segments), 2):
        for token in V8_BUILDER.HTML_TAG_TOKEN.split(segments[index]):
            if token.startswith("<"):
                values.extend(match.group("value") for match in V8_BUILDER.DISPLAY_ATTRIBUTE_TOKEN.finditer(token))
            else:
                values.append(token)
    decimals: list[str] = []
    for value in values:
        masked, _ = V8_BUILDER.protect_semantic_cutoffs(value)
        decimals.extend(match.group("number") for match in V8_BUILDER.DISPLAY_NUMBER_TOKEN.finditer(masked))
    return decimals


class DistributionV8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.deck = DECK.read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_stage_and_navigation_counts_are_contiguous(self) -> None:
        stages = re.findall(r'<div class="slide-stage" id="([^"]+)"', self.deck)
        nav = [int(value) for value in re.findall(r'class="nav-pill[^\"]*" data-slide="(\d+)"', self.deck)]
        self.assertEqual(len(stages), 44)
        self.assertEqual(len(nav), 44)
        self.assertEqual(nav, list(range(44)))
        self.assertEqual([row["source_stage_id"] for row in self.manifest["ordered_stages"]], stages)

    def test_reader_groups_and_physical_order_match_the_reviewer_selection(self) -> None:
        rows = self.manifest["ordered_stages"]
        self.assertEqual([row["slide_number"] for row in rows], list(range(1, 45)))
        self.assertTrue(all(row["group"].startswith("Prioritized") for row in rows[2:23]))
        self.assertTrue(all(row["group"].startswith("Other reviewed") for row in rows[23:]))
        self.assertEqual(rows[2]["title"], "IOS movement events")
        self.assertEqual(rows[7], {"slide_number": 8, "source_stage_id": "slide-acquisition", "group": "Prioritized · workforce and mobility", "title": "Acquisitions and attrition"})
        self.assertEqual(rows[19]["title"], "Direct team size (span)")
        self.assertEqual(rows[20]["title"], "Comp ratio")
        self.assertEqual(rows[21]["title"], "Recent team exits under the current manager")
        cover = stage_html(self.deck, "slide-1")
        v7_cover = stage_html(V7_DECK.read_text(encoding="utf-8"), "slide-1")
        self.assertEqual(cover, V8_BUILDER.normalize_visible_display_numbers(v7_cover))
        self.assertIn("What may be related", cover)
        self.assertIn("2026 annual context", cover)
        self.assertIn("6%", cover)
        index_stage = stage_html(self.deck, "slide-2")
        self.assertEqual(rows[1]["title"], "Index")
        self.assertIn(">Índice<", index_stage)
        self.assertNotIn(">Agenda<", index_stage)
        self.assertIn("Otras variables revisadas", index_stage)
        self.assertEqual(index_stage.count("v8-agenda-row--other"), 1)
        self.assertIn('class="v8-agenda-row v8-agenda-row--other"', index_stage)
        self.assertIn("#slide-2 .v8-agenda-row--other", self.deck)
        self.assertIn("1&ndash;2", self.deck)
        self.assertIn("3&ndash;10", self.deck)
        self.assertIn("38&ndash;44", self.deck)

    def test_removed_and_updated_content(self) -> None:
        self.assertNotIn("QVoice scores standardized within region", self.deck)
        application = stage_html(self.deck, "slide-3")
        self.assertIn("Not recorded", application)
        self.assertNotIn(">Unknown<", application)

        ios = stage_html(self.deck, "slide-5")
        for expected in ("trailing 12 months", "50,043", "9,575", "7%", "<0.1%"):
            self.assertIn(expected, ios)
        self.assertNotIn("YTD", ios)
        self.assertIn("8.4%", ios)
        self.assertIn("55 exits", ios)
        self.assertNotIn("annual ·", ios)

        promotion = stage_html(self.deck, "slide-32")
        for expected in (
            'data-v7-promotion-comparable-cohorts="true"',
            "Time since latest recorded promotion",
            "People with no recorded promotion",
            "excluding RF360",
            "never promoted",
            "n=19,093",
            "n=15,812",
            "n=790",
            "n=7",
            ">0.0%*</span>",
        ):
            self.assertIn(expected, promotion)
        self.assertEqual(promotion.count("v7-promotion-comparable-row"), 10)
        self.assertNotIn("v8-promotion-review", promotion)
        self.assertNotIn("No promotion recorded in current episode", promotion)
        self.assertNotEqual(promotion, stage_html(V7_DECK.read_text(encoding="utf-8"), "slide-32"))
        self.assertIn('data-v8-rate-precision="one-decimal"', promotion)

    def test_acquisition_slide_uses_validated_aggregate_evidence_and_suppresses_small_events(self) -> None:
        evidence = json.loads(ACQUISITION_EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["artifact_type"], "acquisition_entry_distribution_attrition_evidence")
        self.assertEqual(evidence["artifact_classification"], "presentation")
        self.assertEqual(evidence["deliverable_mode"], "presentation")
        self.assertEqual(evidence["outcome"], "pass")
        self.assertTrue(evidence["population"]["rf360_included"])
        self.assertEqual(evidence["dates"]["current_snapshot"], "2026-08-23")
        self.assertEqual(evidence["dates"]["baseline_snapshot"], "2025-08-24")
        self.assertEqual(evidence["dates"]["outcome_window"], "(2025-08-24, 2026-08-23]")
        self.assertEqual(evidence["totals"], {
            "current_active_regular_employee_count": 50_043,
            "baseline_active_regular_employee_count": 45_002,
            "baseline_voluntary_exit_count": 2_484,
        })
        overall = evidence["overall_distribution"]
        self.assertEqual(
            [(row["label"], row["current_employee_count"], row["baseline_employee_count"], row["voluntary_exit_count"])
            for row in overall],
            [
                ("Con adquisición registrada", 7_711, 6_148, 193),
                ("Sin adquisición registrada", 42_332, 38_854, 2_291),
            ],
        )
        self.assertEqual(sum(row["current_employee_count"] for row in overall), 50_043)
        self.assertEqual(sum(row["baseline_employee_count"] for row in overall), 45_002)
        self.assertEqual(sum(row["voluntary_exit_count"] for row in overall), 2_484)
        self.assertAlmostEqual(float(overall[0]["annual_attrition_rate_percent"]), 100 * 193 / 6_148, places=12)
        self.assertAlmostEqual(float(overall[1]["annual_attrition_rate_percent"]), 100 * 2_291 / 38_854, places=12)

        top = evidence["top_acquisitions"]
        self.assertEqual(len(top), 11)
        self.assertEqual(top[0]["label"], "RF360")
        self.assertEqual(top[-1]["label"], "Otras adquisiciones")
        self.assertEqual(sum(row["current_employee_count"] for row in top), 7_711)
        self.assertEqual(
            [row["annual_attrition"]["publication_status"] for row in top],
            [
                "publishable",
                "no_annual_comparable_cohort",
                "suppressed_voluntary_events_lt_30",
                "suppressed_voluntary_events_lt_30",
                "suppressed_voluntary_events_lt_30",
                "suppressed_voluntary_events_lt_30",
                "no_annual_comparable_cohort",
                "no_annual_comparable_cohort",
                "no_annual_comparable_cohort",
                "no_annual_comparable_cohort",
                "publishable",
            ],
        )
        for row in top:
            attrition = row["annual_attrition"]
            if attrition["publication_status"] == "suppressed_voluntary_events_lt_30":
                self.assertIsNone(attrition["annual_attrition_rate_percent"])
                self.assertNotIn("voluntary_exit_count", attrition)
            if attrition["publication_status"] == "no_annual_comparable_cohort":
                self.assertEqual(attrition["baseline_employee_count"], 0)
                self.assertIsNone(attrition["annual_attrition_rate_percent"])

        references = evidence["color_references"]
        self.assertEqual(references["overall_distribution"]["voluntary_exits"], 2_484)
        self.assertEqual(references["overall_distribution"]["eligible_baseline_count"], 45_002)
        self.assertEqual(references["acquisition_panel"]["voluntary_exits"], 193)
        self.assertEqual(references["acquisition_panel"]["eligible_baseline_count"], 6_148)
        self.assertEqual(evidence["historical_baseline_reconciliation"]["difference"], -1)
        self.assertEqual(evidence["historical_baseline_reconciliation"]["status"], "requires_data_owner_reconciliation")
        self.assertEqual(
            evidence["source_provenance"]["distribution_query"]["sql_sha256"],
            "4c0bef229458d3cce31edbb26e74a6863012eec853eba1a4a30cccacbb5b6af8",
        )
        self.assertEqual(
            evidence["source_provenance"]["distribution_query"]["result_sha256"],
            "3567cc86914e6ddb2947c08c92a5db0939382ac1dc7ebf91c70df6c249651930",
        )
        encoded = json.dumps(evidence, ensure_ascii=False).lower()
        for prohibited in ('"employee_id"', '"employeeid"', '"manager_employee_id"', '"manager_name"'):
            self.assertNotIn(prohibited, encoded)

        acquisition = stage_html(self.deck, "slide-acquisition")
        self.assertNotIn('id="slide-acquisition"', V7_DECK.read_text(encoding="utf-8"))
        for expected in (
            'lang="en"',
            "Acquisitions and attrition",
            "Acquisition recorded",
            "No acquisition recorded",
            "Current workforce",
            "Current employees",
            "Annual voluntary attrition",
            "Baseline: 6,148 employees",
            "Baseline: 38,854 employees",
            "50,043",
            "45,002",
            "45,003",
            "RF360",
            "Other acquisitions",
            "Rate suppressed: fewer than 30 voluntary exits",
            "No comparable annual cohort",
            "15.4%",
            "84.6%",
            "31.4%",
            "19.7%",
            "Color references: overall workforce 5.5%",
            "does not establish causality",
            "does not confirm hiring route",
            "Baseline reconciliation pending",
        ):
            self.assertIn(expected, acquisition)
        difference = 100 * 2_291 / 38_854 - 100 * 193 / 6_148
        self.assertIn(f"{difference:.1f} percentage points lower", acquisition)
        self.assertEqual(acquisition.count('data-acquisition-label="'), 11)
        self.assertEqual(acquisition.count(">No cohort</span>"), 5)
        self.assertEqual(acquisition.count(">Suppressed</span>"), 4)
        for old_copy in ("Adquisiciones", "adquisición", "adquisiciones", "cohorte basal", "salidas voluntarias", "Comparación"):
            self.assertNotIn(old_copy, acquisition)
        self.assertEqual(acquisition.count("v8-reference-unavailable"), 9)
        self.assertNotIn(">0.0%</span>", acquisition)
        pills = V8_BUILDER.source_rate_pills(acquisition)
        self.assertEqual([pill.group("value").strip() for pill in pills], ["3.1%", "5.9%", "2.2%", "5.4%"])
        self.assertEqual(
            [
                next(
                    item
                    for item in re.search(r'class="([^"]+)"', pill.group("attrs")).group(1).split()
                    if item.startswith("attr-")
                )
                for pill in pills
            ],
            ["attr-low", "attr-mid", "attr-low", "attr-high"],
        )
        self.assertEqual(
            [re.search(r'data-v8-color-reference="([^"]+)"', pill.group("attrs")).group(1) for pill in pills],
            [
                "acquisition_overall_annual",
                "acquisition_overall_annual",
                "acquisition_registered_annual",
                "acquisition_registered_annual",
            ],
        )

        policy = json.loads(COLOR_POLICY.read_text(encoding="utf-8"))
        self.assertEqual(policy["reference_sources"]["acquisition_overall_annual"]["baseline_employee_count"], 45_002)
        self.assertEqual(policy["reference_sources"]["acquisition_registered_annual"]["baseline_employee_count"], 6_148)
        self.assertNotEqual(policy["stage_default_reference"]["slide-acquisition"], "annual_august_2025")
        color_audit = json.loads(COLOR_EVIDENCE.read_text(encoding="utf-8"))["stage_color_audit"]["slide-acquisition"]
        self.assertEqual(color_audit["status"], "comparable")
        self.assertEqual(color_audit["pills"], 4)
        self.assertEqual(color_audit["validated_rate_pills"], 4)
        self.assertEqual([reference["id"] for reference in color_audit["references"]], ["acquisition_overall_annual", "acquisition_registered_annual"])

    def test_manifest_hashes_and_frozen_v7_source_match(self) -> None:
        self.assertEqual(self.manifest["output"]["deck_sha256"], sha256(DECK))
        self.assertEqual(self.manifest["source"]["deck_sha256"], sha256(V7_DECK))
        self.assertEqual(sha256(V7_DECK), FROZEN_V7_SHA256)
        ios = self.manifest["ios_trailing_12m_evidence"]
        ios_path = ROOT / ios["path"]
        self.assertEqual(ios["sha256"], sha256(ios_path))
        self.assertEqual(ios["current_active_regular_employees"], 50_043)
        self.assertEqual(ios["baseline_active_regular_employees"], 45_003)
        self.assertEqual(ios["current_all_ios_movement_count"], 9_575)

        promotion = self.manifest["promotion_comparable_cohorts_evidence"]
        self.assertEqual(promotion["path"], str(COMPARABLE_PROMOTION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"))
        self.assertEqual(promotion["sha256"], sha256(COMPARABLE_PROMOTION_EVIDENCE))
        self.assertEqual(promotion["baseline_snapshot"], "2025-08-24")
        self.assertEqual(promotion["outcome_window"], "(2025-08-24, 2026-08-23]")
        self.assertEqual(promotion["cohort_totals"], {"baseline_population": 41_757, "recorded_promotion": 19_093, "no_recorded_promotion_role_tenure_proxy": 15_812, "declared_exclusions": 6_852})
        self.assertEqual(promotion["small_cohort_display"], [{"cohort": "recorded_promotion", "label": "5+ years", "employee_count": 7}])

        display_policy = self.manifest["display_number_policy"]
        self.assertEqual(display_policy["version"], "v8-integer-first-with-one-decimal-attrition-rates")
        self.assertEqual(display_policy["rounding"], "half_up")
        self.assertIn("category band", display_policy["semantic_cutoffs"].lower())

        color_policy = self.manifest["attrition_color_policy"]
        self.assertEqual(color_policy["path"], str(COLOR_POLICY.relative_to(ROOT)).replace("\\", "/"))
        self.assertEqual(color_policy["sha256"], sha256(COLOR_POLICY))
        self.assertEqual(color_policy["rate_display_decimal_places"], 1)
        self.assertEqual(set(color_policy["class_counts"]), {"below_reference", "within_reference", "above_reference", "not_comparable"})
        self.assertEqual(json.loads(COLOR_POLICY.read_text(encoding="utf-8"))["version"], 3)

        color_evidence = self.manifest["attrition_color_reference_evidence"]
        self.assertEqual(color_evidence["path"], str(COLOR_EVIDENCE.relative_to(ROOT)).replace("\\", "/"))
        self.assertEqual(color_evidence["sha256"], sha256(COLOR_EVIDENCE))
        self.assertEqual(color_evidence["artifact_classification"], "internal_analysis")
        self.assertEqual(color_evidence["outcome"], "pass")

        acquisition = self.manifest["acquisition_entry_evidence"]
        self.assertEqual(acquisition["path"], str(ACQUISITION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"))
        self.assertEqual(acquisition["sha256"], sha256(ACQUISITION_EVIDENCE))
        self.assertEqual(acquisition["artifact_classification"], "presentation")
        self.assertEqual(acquisition["outcome"], "pass")
        self.assertEqual(acquisition["current_snapshot"], "2026-08-23")
        self.assertEqual(acquisition["baseline_snapshot"], "2025-08-24")
        self.assertEqual(acquisition["outcome_window"], "(2025-08-24, 2026-08-23]")
        self.assertEqual(acquisition["current_active_regular_employees"], 50_043)
        self.assertEqual(acquisition["baseline_active_regular_employees"], 45_002)
        self.assertEqual(acquisition["baseline_voluntary_exits"], 2_484)
        self.assertEqual(acquisition["reader_language"], "en")
        self.assertEqual(acquisition["historical_baseline_reconciliation"]["status"], "requires_data_owner_reconciliation")

    def test_backup_registry_is_referenced_and_searchable(self) -> None:
        policy = self.manifest["backup_policy"]
        self.assertTrue(policy["archive_before_overwrite"])
        self.assertTrue(policy["deduplicate_by_deck_sha256"])
        registry_path = ROOT / policy["registry"]
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertIn("search_instruction", registry)
        self.assertGreaterEqual(len(registry["backups"]), 1)
        for backup in registry["backups"]:
            self.assertTrue((registry_path.parent / backup["deck"]).is_file())
            if backup["manifest"] is not None:
                self.assertTrue((registry_path.parent / backup["manifest"]).is_file())

    def test_historical_v1_v7_registry_preserves_available_versions(self) -> None:
        archive = self.manifest["historical_version_archive"]
        registry_path = ROOT / archive["registry"]
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        versions = {row["version"]: row for row in registry["versions"]}
        self.assertEqual(set(versions), set(range(1, 8)))
        self.assertEqual(versions[1]["status"], "not_found")
        for version in range(2, 8):
            row = versions[version]
            self.assertEqual(row["status"], "archived")
            self.assertTrue(row["deck_available"])
            self.assertTrue(row["manifest_available"])
            for artifact in row["files"]:
                self.assertTrue((ROOT / artifact["archived"]).is_file())

    def test_ios_trailing_window_evidence_reconciles(self) -> None:
        evidence_path = ROOT / self.manifest["ios_trailing_12m_evidence"]["path"]
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertIn("(2025-08-23, 2026-08-23]", evidence["definition"]["current_distribution"])
        self.assertIn("(2025-08-24, 2026-08-23]", evidence["definition"]["annual_attrition"])
        rows = evidence["rows"]
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[0]["group_key"], "total")
        self.assertEqual(rows[0]["current_cohort_n"], 9_575)
        self.assertEqual(rows[0]["annual_voluntary_exit_n"], 610)
        for row in rows:
            self.assertLessEqual(row["annual_voluntary_exit_n"], row["baseline_cohort_n"])
            self.assertAlmostEqual(
                row["annual_voluntary_attrition_percent"],
                round(100 * row["annual_voluntary_exit_n"] / row["baseline_cohort_n"], 2),
            )
        encoded = json.dumps(evidence, ensure_ascii=False).lower()
        for prohibited in ('"employee_id"', '"employeeid"', '"manager_employee_id"', '"manager_name"'):
            self.assertNotIn(prohibited, encoded)

    def test_qvoice_color_references_use_valid_panel_cohorts(self) -> None:
        """QVoice rates are colored only after a cohort-specific pooled reference exists."""
        theme = json.loads(QVOICE_THEME_EVIDENCE.read_text(encoding="utf-8"))
        reference = theme["reference_cohort"]
        self.assertEqual(reference["reference_id"], "qvoice-theme-union")
        self.assertEqual(reference["source_employee_count"], 7_284)
        self.assertEqual(reference["matched_employee_count"], 7_108)
        self.assertEqual(reference["voluntary_exit_count"], 240)
        self.assertEqual(reference["publication_status"], "publishable")
        self.assertTrue(theme["validation"]["reference_cohort_is_deduplicated_union"])
        self.assertEqual(theme["validation"]["reference_cohort_source_duplicate_employee_count"], 0)
        self.assertAlmostEqual(
            reference["trailing_12m_voluntary_attrition_rate_percent"],
            100 * reference["voluntary_exit_count"] / reference["matched_employee_count"],
            places=4,
        )
        self.assertNotIn('"employee_id"', json.dumps(theme, ensure_ascii=False))

        color = json.loads(COLOR_EVIDENCE.read_text(encoding="utf-8"))["stage_color_audit"]
        for stage_id, expected_pills in {"slide-21": 5, "slide-23": 18, "slide-24": 12, "slide-25": 6}.items():
            with self.subTest(stage=stage_id):
                self.assertEqual(color[stage_id]["status"], "comparable")
                self.assertEqual(color[stage_id]["pills"], expected_pills)
                self.assertEqual(color[stage_id]["validated_rate_pills"], expected_pills)
                stage = stage_html(self.deck, stage_id)
                self.assertNotIn("v8-reference-unavailable", stage)

        theme_stage = stage_html(self.deck, "slide-21")
        self.assertIn('data-v8-color-reference="qvoice-theme-union"', theme_stage)
        self.assertIn("Color reference(s): Any shown theme 3.4%", theme_stage)

    def test_published_numeric_rates_without_a_common_cohort_use_within_panel_rank(self) -> None:
        """Fallback colors rank only a panel's visible rates and retain small cells in gray."""
        evidence = json.loads(COLOR_EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(evidence["version"], 3)
        self.assertIn("fallback_within_panel_rule", evidence["policy"])
        self.assertEqual(
            evidence["validation"]["within_panel_rank_pills_use_published_numeric_rates_only"],
            "pass",
        )

        expected = {
            "slide-20": (12, 0),
            "slide-37-followup": (2, 16),
            "slide-40": (11, 0),
            "slide-42": (3, 0),
        }
        for stage_id, (ranked, gray) in expected.items():
            with self.subTest(stage=stage_id):
                audit = evidence["stage_color_audit"][stage_id]
                self.assertEqual(audit["status"], "within_panel_rank")
                self.assertEqual(audit["validated_rate_pills"], ranked)
                self.assertEqual(audit["uncolored_rate_pills"], gray)
                stage = stage_html(self.deck, stage_id)
                pills = V8_BUILDER.source_rate_pills(stage)
                self.assertEqual(
                    sum("data-v8-color-method=\"within-panel-rank\"" in pill.group("attrs") for pill in pills),
                    ranked,
                )
                self.assertEqual(
                    sum("v8-reference-unavailable" in pill.group("attrs") for pill in pills),
                    gray,
                )
                self.assertIn("Color scale: within each chart panel", stage)

        office_site = stage_html(self.deck, "slide-42")
        self.assertIn("attr-low", office_site)
        self.assertIn("attr-high", office_site)
        self.assertEqual(
            [pill.group("value").strip() for pill in V8_BUILDER.source_rate_pills(office_site)],
            ["5.5%", "7.2%", "4.1%"],
        )
        self.assertNotIn("\naria-label=", office_site)

    def test_v8_display_number_policy_covers_static_and_dynamic_content(self) -> None:
        expected = {
            "5.5": "6",
            "0.84": "0.8",
            "0.04": "<0.1",
            "0.0": "0",
            "0.95": "1",
            "-0.04": ">-0.1",
            "1,234.5": "1,235",
        }
        for raw, rendered in expected.items():
            self.assertEqual(V8_BUILDER.format_display_token(raw), rendered)
        self.assertEqual(V8_BUILDER.fmt_pct(0.04), "<0.1%")

        self.assertIn("<!-- V8 DISPLAY NUMBER FORMATTER -->", self.deck)
        self.assertIn('data-v8-display-number-formatter="true"', self.deck)
        self.assertNotIn('data-v7-display-number-formatter="true"', self.deck)
        self.assertIn("new MutationObserver", self.deck)
        self.assertIn("roundHalfUp", self.deck)

        for raw_cutoff in V8_BUILDER.REQUIRED_SEMANTIC_CUTOFFS:
            self.assertIn(raw_cutoff, self.deck)

        for raw_decimal in visible_decimal_tokens(self.deck):
            value = Decimal(raw_decimal.replace(",", ""))
            self.assertNotEqual(value, 0, raw_decimal)
            self.assertLess(abs(value), 1, raw_decimal)
            self.assertEqual(len(raw_decimal.rsplit(".", 1)[1]), 1, raw_decimal)

        stages, _, _ = V8_BUILDER.stage_map(self.deck)
        rate_pills = [pill for html_stage in stages.values() for pill in V8_BUILDER.source_rate_pills(html_stage)]
        self.assertGreater(len(rate_pills), 400)
        self.assertTrue(all('data-v8-rate-precision="one-decimal"' in pill.group("attrs") for pill in rate_pills))
        ios_rate_elements = re.findall(r'<div class="v8-ios-rate[^>]*>', stages["slide-5"])
        self.assertEqual(len(ios_rate_elements), 6)
        self.assertTrue(all('data-v8-rate-precision="one-decimal"' in element for element in ios_rate_elements))

    def test_comparable_color_policy_is_consistent_and_auditable(self) -> None:
        policy = json.loads(COLOR_POLICY.read_text(encoding="utf-8"))
        color_evidence = json.loads(COLOR_EVIDENCE.read_text(encoding="utf-8"))
        for css_class in policy["states"].values():
            self.assertIn(css_class, self.deck)
        self.assertTrue(all(value > 0 for value in color_evidence["class_counts"].values()))

        stages, _, _ = V8_BUILDER.stage_map(self.deck)
        for stage_id in color_evidence["stage_color_audit"]:
            self.assertIn(f'data-v8-color-footer="{stage_id}"', stages[stage_id])
        self.assertIn("Recorded promotion", stages["slide-32"])
        self.assertIn("No recorded promotion proxy", stages["slide-32"])
        self.assertIn("All IOS movements", stages["slide-5"])

    def test_no_identity_fields_are_rendered(self) -> None:
        lowered = self.deck.lower()
        for prohibited in ("employee_id", "manager_employee_id", "manager_name", "employee_name", "@qualcomm.com"):
            self.assertNotIn(prohibited, lowered)


if __name__ == "__main__":
    unittest.main()
