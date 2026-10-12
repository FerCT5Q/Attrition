"""Regresiones del contrato temporal y estadístico; todos los datos son sintéticos."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from openpyxl import Workbook
from sklearn.metrics import average_precision_score, brier_score_loss

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import qvoice_model_data as data
import qvoice_model_evidence as evidence
import qvoice_model_experiment as experiment
import qvoice_model_validation as validation


class TemporalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.reference = Path(self.temp.name) / "availability.md"
        self.reference.write_text("Fechas sintéticas para la prueba.", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def wave(self, year, available):
        return {"year": year, "descriptive_anchor": f"{year}-01-01", "availability": {"date": available, "status": "verified", "evidence_reference": str(self.reference)}}

    def test_publication_and_expiration_boundaries(self):
        wave = self.wave(2024, "2024-02-15")
        self.assertIsNone(data.select_wave([wave], "2024-02-14", "2020-01-01"))
        self.assertEqual(data.select_wave([wave], "2024-02-15", "2020-01-01")["year"], 2024)
        self.assertEqual(data.select_wave([wave], "2025-02-14", "2020-01-01")["year"], 2024)
        self.assertIsNone(data.select_wave([wave], "2025-02-15", "2020-01-01"))

    def test_unknown_date_is_not_inferred_from_year(self):
        wave = self.wave(2024, "2024-02-15")
        wave["availability"]["status"] = "pending"
        self.assertIsNone(data.select_wave([wave], "2024-08-01", "2020-01-01"))
        wave["availability"]["status"] = "verified"
        wave["availability"]["evidence_reference"] = None
        with self.assertRaises(ValueError):
            data.availability_date(wave)

    def test_new_wave_replaces_even_without_response(self):
        waves = [self.wave(2024, "2024-03-01"), self.wave(2025, "2025-02-01")]
        selected = data.select_wave(waves, "2025-02-02", "2020-01-01")
        responses = {2024: {"Q4": 1}, 2025: {}}
        self.assertEqual(selected["year"], 2025)
        self.assertIsNone(responses[selected["year"]].get("Q4"))

    def test_rehire_and_unknown_episode_do_not_inherit_old_answers(self):
        wave = self.wave(2024, "2024-02-15")
        self.assertIsNone(data.select_wave([wave], "2024-06-30", "2024-04-01"))
        self.assertIsNone(data.select_wave([wave], "2024-06-30", pd.NaT))

    def test_training_uses_label_end_instead_of_snapshot_alone(self):
        dates = pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01", "2024-06-01"])
        frame = pd.DataFrame({"snapshot_date": dates, "label_end": pd.to_datetime(["2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01", "2024-06-01", "2024-08-01"])})
        inner, held, final = validation.monthly_split(frame, "2024-07-01", 3)
        self.assertEqual(len(final), 5)
        self.assertEqual(len(inner), 2)
        self.assertEqual(held["snapshot_date"].min(), pd.Timestamp("2024-03-01"))
        self.assertLessEqual(inner["label_end"].max(), held["snapshot_date"].min())
        self.assertNotIn(pd.Timestamp("2024-06-01"), final["snapshot_date"].tolist())

    def test_partial_six_month_followup_excluded(self):
        frame = pd.DataFrame({"snapshot_date": pd.to_datetime(["2026-02-22", "2026-03-22"]), "value": [1, 2]})
        selected = validation.period_frame(frame, {"start": "2026-02-01", "end": "2026-03-31"}, "2026-09-07")
        self.assertEqual(selected["value"].tolist(), [1])

    def test_attached_features_replace_missing_wave_and_respect_episodes(self):
        config = data.load_config()
        config["candidates"] = [config["candidates"][0]]
        config["combinations"] = []
        config["sources"]["waves"] = [self.wave(2024, "2024-02-15"), self.wave(2025, "2025-02-01")]
        for wave in config["sources"]["waves"]:
            wave["file"] = str(self.reference)
        metadata = {"waves": [{"year": y, "sha256": data.sha256_file(self.reference)} for y in (2024, 2025)]}
        salt = "a" * 64
        key = hashlib.md5(("101" + salt).encode()).hexdigest()
        frame = pd.DataFrame({"snapshot_date": pd.to_datetime(["2024-02-14", "2024-02-15", "2025-01-31", "2025-02-01", "2025-03-01", "2026-02-01"]),
                              "person_key": [key] * 6, "same_episode_2024": [1] * 6, "same_episode_2025": [1, 1, 1, 1, 0, 1]})
        sources = {2024: data.WaveRows(2024, {101: {"Q4": (1, "valid"), "Q12": (0, "valid")}}, set(), {}, {}),
                   2025: data.WaveRows(2025, {}, set(), {}, {})}
        with patch.object(experiment, "scan_wave", side_effect=lambda wave, *_: sources[wave["year"]]):
            result = experiment.attach_qvoice(frame, config, metadata, salt)
        self.assertEqual(result["qv_Q4"].tolist(), ["no_available_wave", "v1", "v1", "no_linked_row", "different_employment_episode", "no_available_wave"])
        self.assertEqual(result["av_qv_Q12"].iloc[1], "available")
        self.reference.write_text("La fuente sintética cambió.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cambió"):
            experiment.attach_qvoice(frame, config, metadata, salt)

    def test_pending_publication_never_runs_prediction(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tools/.tmp") as directory:
            root = Path(directory)
            with patch.object(experiment, "DEFAULT_MODEL_QUERY", root / "query.sql"), patch.object(experiment, "read_model_frame") as reader:
                result = experiment.compare(data.load_config(), root)
            reader.assert_not_called()
            self.assertEqual(result["available_wave_count"], 0)
            self.assertTrue(all(v["decision"]["status"] == "evidencia temporal insuficiente" for v in result["variants"]))


class ResponseTests(unittest.TestCase):
    def test_retrospective_heartbeat_events_do_not_replace_cutoff_results(self):
        config = data.load_config()
        candidate = next(c for c in config["candidates"] if c["id"] == "heartbeat")
        values = {f"scale_Q{i}": (4, "valid") for i in range(1, 54)}
        source = data.WaveRows(year=2026, rows={key: values.copy() for key in range(100, 200)}, duplicate_keys=set(),
                               mapping={f"Q{i}": {"scale_indices": [i]} for i in range(1, 54)},
                               source_quality={"missing_key_rows": 0, "invalid_key_rows": 0, "distinct_duplicate_keys": 0})
        wave_config = next(w for w in config["sources"]["waves"] if w["year"] == 2026)
        def joined_rows(events):
            return [{"scope": scope, "group_code": 0, "baseline_snapshot": "2025-12-28", "outcome_end": "2026-08-23",
                     "eligible_count": 100, "source_count": 100, "matched_count": 100, "event_count": events, "multi_match_count": 0}
                    for scope in ("Engineering", "workforce")]
        with patch.object(evidence, "query_join", side_effect=[(joined_rows(40), []), (joined_rows(45), [])]) as query, \
             patch.object(evidence, "reconcile_wave", return_value={"status": "not_applicable", "checks": []}):
            result, _, _ = evidence.summarize_wave(candidate, wave_config, source, config)
        self.assertEqual(query.call_count, 2)
        self.assertEqual(query.call_args.kwargs["query_path"], evidence.HEARTBEAT_RETROSPECTIVE_QUERY)
        for scope in ("Engineering", "workforce"):
            self.assertTrue(all(group["events"] == 40 for group in result["scopes"][scope]["groups"]))
        retrospective = result["scopes"]["workforce_historical_reconciliation"]
        self.assertFalse(retrospective["predictive_use_allowed"])
        self.assertTrue(all(group["events"] == 45 for group in retrospective["groups"]))

    def test_heartbeat_domain_audits_unselected_denominator_items(self):
        candidate = next(c for c in data.load_config()["candidates"] if c["id"] == "heartbeat")
        values = {f"scale_Q{i}": (4, "valid") for i in range(1, 54)}
        self.assertNotIn("Q20", candidate["components"])
        values["scale_Q20"] = data.cell_value(9, form="scale")
        source = data.WaveRows(2026, {101: values}, set(), {}, {})
        _, signatures, counts = evidence.group_wave(candidate, source)
        self.assertEqual(counts["invalid"], 1)
        self.assertEqual(counts["valid"], 52)
        self.assertEqual(counts["status_reconciliation_difference"], 0)
        self.assertTrue(signatures[0]["full_complete"])
        self.assertEqual(signatures[0]["comparable"], 6)
        self.assertEqual(signatures[0]["mismatch"], 0)

    def test_missing_invalid_and_absent_remain_distinct(self):
        self.assertEqual(data.cell_value(0), (0, "valid"))
        self.assertEqual(data.cell_value(255), (None, "sentinel_255"))
        self.assertEqual(data.cell_value(None), (None, "missing"))
        self.assertEqual(data.cell_value("bad"), (None, "invalid"))
        self.assertEqual(data.cell_value(1, present=False), (None, "question_absent"))
        self.assertEqual(data.cell_value(1.5), (None, "invalid"))

    def test_all_score_boundaries_against_independent_formula(self):
        for count in range(34):
            expected = data.BANDS[int(np.searchsorted([50, 70, 80, 90, 100], 100 * count / 33, side="right"))]
            self.assertEqual(data.favorable_band([1] * count + [0] * (33 - count), required_count=33), expected)
        self.assertIsNone(data.favorable_band([1] * 32 + [None], required_count=33))

    def test_intent_and_mean_have_independent_missingness(self):
        config = data.load_config()
        values = {f"M{i:02d}": (1, "valid") for i in range(1, 34)}
        values.update({"Q4": (1, "valid"), "Q12": (None, "missing")})
        intent = evidence.compact_signature(config["candidates"][0], values)
        self.assertTrue(intent["primary_available"])
        self.assertFalse(intent["primary_complete"])
        self.assertNotIn("intent_both", intent["states"])
        values["M01"] = (None, "missing")
        self.assertFalse(evidence.compact_signature(config["candidates"][2], values)["primary_available"])

    def test_mean31_does_not_expand_the_33_item_cohort(self):
        config = data.load_config()
        values = {f"M{i:02d}": (1, "valid") for i in range(1, 34)}
        values["M14"] = (None, "missing")
        feature = experiment.wave_feature_values(values, config["sources"]["waves"][1], config)
        self.assertEqual(feature["qv_mean33"], "missing")
        self.assertEqual(feature["qv_mean31"], "missing")

    def test_mean31_removes_exact_intent_questions(self):
        self.assertEqual(data.EXPECTED_COMMON_BASES[13], "i rarely think about looking for a new job with another company")
        self.assertEqual(data.EXPECTED_COMMON_BASES[15], "i see myself working at qualcomm in a few years")
        config = data.load_config()
        values = {f"M{i:02d}": (int(i not in (14, 16)), "valid") for i in range(1, 34)}
        feature = experiment.wave_feature_values(values, config["sources"]["waves"][1], config)
        self.assertEqual(feature["qv_mean33"], "90–99")
        self.assertEqual(feature["qv_mean31"], "100")

    def test_heartbeat_minimum_itemset_and_ties(self):
        self.assertEqual(data.relative_sign(3, [3] * 38 + [None] * 15), 0)
        self.assertEqual(data.relative_sign(5, [3] * 53), 1)
        self.assertEqual(data.relative_sign(1, [3] * 53), -1)
        self.assertIsNone(data.relative_sign(3, [3] * 37 + [None] * 16))
        self.assertIsNone(data.relative_sign(3, [3] * 52))

    def test_duplicate_keys_are_excluded_and_stream_matches_structured_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Raw data"
            sheet.append(["Emp ID", "Item_favorable", "Item alt_favorable", "Response Type"])
            sheet.append([101, 1, 0, "EX"])
            sheet.append([101, 0, 1, "EX"])
            sheet.append([102, 255, 1, "EX"])
            sheet.append([103, 1, 1, "EX"])
            workbook.save(path)
            metadata = {"headers": ["Emp ID", "Item_favorable", "Item alt_favorable", "Response Type"], "mapping": {"Q1": {"binary_indices": [1], "alternative_binary_indices": [2], "scale_indices": []}}}
            wave = {"year": 2026, "file": str(path), "sheet": "Raw data", "key_column": "Emp ID"}
            result = data.scan_wave(wave, metadata, {"Q1"})
            self.assertEqual(set(result.rows), {102, 103})
            self.assertEqual(result.rows[102]["Q1"], (None, "sentinel_255"))
            self.assertEqual(result.rows[103]["alternate_Q1_0"], (1, "valid"))
            self.assertEqual(result.source_quality["conflicting_rows"], 1)


class StatisticalTests(unittest.TestCase):
    def test_tied_metrics_match_sklearn_and_ignore_row_order(self):
        y = np.array([1, 0, 1, 0, 0, 1])
        p = np.array([0.4, 0.4, 0.8, 0.1, 0.1, 0.4])
        result = validation.weighted_metrics(y, p)
        self.assertAlmostEqual(result["pr_auc"], average_precision_score(y, p))
        self.assertAlmostEqual(result["brier_score"], brier_score_loss(y, p))
        reverse = validation.weighted_metrics(y[::-1], p[::-1])
        for metric in validation.DECISION_METRICS:
            self.assertAlmostEqual(result[metric], reverse[metric])

    def test_aggregated_binomial_brier_matches_individual_loss(self):
        individual = validation.weighted_metrics(np.array([1, 0, 0, 1, 1]), np.array([.2, .2, .2, .7, .7]))
        aggregate = validation.weighted_metrics(np.array([1/3, 1]), np.array([.2, .7]), np.array([3, 2]))
        self.assertAlmostEqual(individual["brier_score"], aggregate["brier_score"])
        self.assertAlmostEqual(individual["pr_auc"], aggregate["pr_auc"])

    def test_paired_cluster_bootstrap_keeps_identical_models_equal(self):
        keys = np.repeat(np.arange(15), 3)
        y = np.tile([0, 0, 1], 15)
        p = np.linspace(.01, .3, len(y))
        result = validation.bootstrap_paired(keys, y, {"control": p, "response": p.copy()}, repetitions=30)
        self.assertEqual(result["people"], 15)
        for interval in result["paired_differences"]["response__minus__control"].values():
            self.assertEqual(interval, {"lower": 0.0, "upper": 0.0})

    def test_new_component_unavailable_in_inner_training_blocks_fold(self):
        inner = pd.DataFrame({"qv_Q6": ["question_absent"] * 3})
        held = pd.DataFrame({"qv_Q6": ["v1", "v0"]})
        self.assertTrue(validation.component_gate(inner, held, ["qv_Q6"]))

    def test_promising_requires_two_main_periods_and_availability_control(self):
        base = dict(pr_auc=.1, lift_at_10_percent=2, brier_score=.04, calibration_error_pp=.4, top_quintile_calibration_error_pp=.6)
        better = dict(pr_auc=.12, lift_at_10_percent=2.2, brier_score=.03, calibration_error_pp=.3, top_quintile_calibration_error_pp=.5)
        period = {"main": True, "complete": True, "status": "evaluated", "control": base, "availability": base, "response": better}
        self.assertEqual(validation.decision([period])["status"], "evidencia temporal insuficiente")
        self.assertEqual(validation.decision([period, copy.deepcopy(period)])["status"], "prometedora")
        second = copy.deepcopy(period)
        second["availability"] = better
        self.assertEqual(validation.decision([period, second])["status"], "sin mejora demostrada")

    def test_cloglog_fit_recovers_a_synthetic_response_effect(self):
        rows = []
        for snapshot in pd.date_range("2024-01-31", periods=12, freq="ME"):
            for response, events in (("v0", 40), ("v1", 5)):
                rows.append({"snapshot_date": snapshot, "level_grouped": "L1", "tenure_playbook_band": "3-5 years", "manager_changes_12m": "0", "qv_Q4": response, "exposure_count": 500, "event_count": events})
        frame = pd.DataFrame(rows)
        model = validation.fit_model(frame, ["level_grouped", "tenure_playbook_band", "calendar_month", "manager_changes_12m", "level_x_tenure", "tenure_x_manager_changes", "qv_Q4"], .1)
        self.assertTrue(model.fitted.converged)
        predicted = model.predict(frame.iloc[:2])
        self.assertGreater(predicted[0], predicted[1] * 6)
        self.assertAlmostEqual(predicted[0], .08, delta=.003)
        self.assertAlmostEqual(predicted[1], .01, delta=.003)

    def test_variant_pipeline_keeps_missing_people_and_honors_calendar_cutoff(self):
        config = data.load_config()
        config["validation"]["l2_grid"] = [.1]
        config["validation"]["bootstrap_repetitions"] = 8
        rows = []
        for snapshot in pd.date_range("2024-01-31", "2025-07-31", freq="ME"):
            for person in range(80):
                response = "missing" if person % 10 == 0 else "v0" if person < 40 else "v1"
                rows.append({"snapshot_date": snapshot, "label_end": snapshot + pd.offsets.MonthEnd(1), "person_key": f"synthetic-{person}",
                             "level_grouped": "L1", "tenure_playbook_band": "3-5 years", "manager_changes_12m": "0", "team_exits_12m": "0",
                             "direct_reports_band": "0", "time_since_promotion_band": "promo 1-2 years", "rehire": "no",
                             "qv_Q4": response, "av_qv_Q4": "missing" if response == "missing" else "available", "qvoice_wave": "2024",
                             "exposure_count": 1, "event_count": int(person % (8 if person < 40 else 20) == 1)})
        monthly = pd.DataFrame(rows)
        direct = monthly.copy()
        direct["event_count"] = direct["person_key"].str.rsplit("-", n=1).str[-1].astype(int).lt(40).astype(int)
        result = experiment.run_variant(config, {"id": "synthetic_q4", "columns": ["qv_Q4"]}, monthly, direct,
                                        [{**config["validation"]["main_periods"][0], "main": True}], {})
        period = result["periods"][0]
        self.assertEqual(period["status"], "evaluated")
        self.assertTrue(period["cohort_equality_verified"])
        self.assertLessEqual(period["maximum_fit_label_end"], "2025-02-01")
        self.assertEqual(period["snapshot_count"], 6)
        self.assertEqual(period["people"], 80)
        for model in ("control", "availability", "response"):
            self.assertEqual(period[model]["exposures"], 480)
            self.assertEqual(period["response_available_cohort"]["metrics"][model]["exposures"], 432)


if __name__ == "__main__":
    unittest.main()
