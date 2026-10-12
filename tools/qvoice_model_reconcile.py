"""Conciliar agregados actuales con la evidencia descriptiva del playbook v11."""

from __future__ import annotations

import json

from qvoice_model_data import ROOT, sha256_file

ANNUAL = ROOT / "output/distribution/json/qvoice-favorable-unfavorable-question-attrition-evidence-20260923.json"
MEAN33 = ROOT / "output/distribution/json/qvoice-comparable-favorable-evidence-20260909.json"
HEARTBEAT = ROOT / "output/distribution/json/qvoice-2026-august-post-survey-ytd-heartbeat-relative-sign-attrition-evidence-20260923.json"


def reconcile_wave(candidate: dict, current: dict, config: dict) -> dict:
    """La fuente histórica es contexto; cada observado proviene de la ejecución actual."""
    checks = []

    def check(name, observed, expected, tolerance=0):
        passed = abs(observed - expected) <= tolerance if isinstance(observed, (int, float)) and isinstance(expected, (int, float)) else observed == expected
        checks.append({"check": name, "observed": observed, "expected": expected, "tolerance": tolerance, "pass": bool(passed)})

    year = current["year"]
    reference = None
    cutoff_comparison = []
    note = "No se reutiliza una cifra previa para puntuar este concepto."
    if candidate["id"] in ("intent", "career"):
        reference = ANNUAL
        historical = json.loads(reference.read_text(encoding="utf-8"))
        key = "intent_to_stay" if candidate["id"] == "intent" else "career_goals"
        previous = next(w for w in historical["variables"][key] if w["year"] == year)
        scope = current["scopes"]["workforce"]
        raw = {(g["feature"], g["response"]): g for g in current["raw_summary"]["groups"]}
        joined = {(g["feature"], g["response"]): g for g in scope["groups"]}
        expected = {"intent_both" if candidate["id"] == "intent" else "career": previous["groups"]}
        if candidate["id"] == "intent":
            expected.update({q: previous["components"][q]["groups"] for q in ("Q4", "Q12")})
        check("baseline_snapshot", scope["baseline_snapshot"], previous["baseline_snapshot"])
        check("outcome_start", scope["outcome_start"], previous["outcome_start"])
        if year < 2026:
            check("outcome_end", scope["outcome_end"], previous["outcome_end"])
        for feature, groups in expected.items():
            for response, values in groups.items():
                observed = joined.get((feature, response), {})
                check(f"{feature}/{response}/source", raw.get((feature, response), {}).get("people"), values["source_employee_count"])
                check(f"{feature}/{response}/linked", observed.get("people"), values["matched_employee_count"])
                if year < 2026:
                    check(f"{feature}/{response}/events", observed.get("events"), values["voluntary_exit_count"])
                    check(f"{feature}/{response}/rate", observed.get("attrition_percent"), values["voluntary_attrition_rate_percent"], 0.000051)
        note = "2024/2025: mismos denominadores y ventanas anuales. 2026: sólo se concilian fuente y enlace; el playbook termina el 27 de septiembre y esta ejecución respeta el corte conocido al 7 de septiembre."
    elif candidate["id"] == "mean33":
        reference = MEAN33
        historical = json.loads(reference.read_text(encoding="utf-8"))
        previous = next(w for w in historical["waves"] if w["year"] == year)
        raw = current["raw_summary"]
        check("source_participants", raw["participants"], previous["participant_rows"])
        check("complete_33", raw["complete_primary"], previous["complete_comparable_participants"])
        check("mean_favorable_percent", raw["mean_favorable_percent"], previous["mean_favorable_percent"], 0.000051)
        bands = {g["response"]: g["people"] for g in raw["groups"] if g["feature"] == "mean33"}
        for band in previous["score_bands"]:
            check(f"band/{band['band']}", bands.get(band["band"]), band["participant_count"])
        note = "Misma lista estricta de 33 textos, mismas seis bandas y cohorte raw completa. La cobertura Engineering se calcula aparte y no debe igualar el total raw."
    elif candidate["id"] == "heartbeat" and year == 2026:
        reference = HEARTBEAT
        historical = json.loads(reference.read_text(encoding="utf-8"))
        scope = current["scopes"].get("workforce_historical_reconciliation", current["scopes"]["workforce"])
        contract = historical["outcome_contract"]
        check("baseline_snapshot", scope["baseline_snapshot"], contract["baseline_snapshot"])
        check("outcome_start", scope["outcome_start"], contract["survey_launch_date"])
        check("outcome_end", scope["outcome_end"], contract["august_cutoff_date"])
        raw = {(g["feature"], g["response"]): g for g in current["raw_summary"]["groups"]}
        joined = {(g["feature"], g["response"]): g for g in scope["groups"]}
        known = {(g["feature"], g["response"]): g for g in current["scopes"]["workforce"]["groups"]}
        labels = {-1: "Por debajo de su promedio", 0: "Igual a su promedio", 1: "Por encima de su promedio"}
        for panel in historical["slide"]["panels"]:
            for question in panel["questions"]:
                feature = f"heartbeat_{question['question_id']}"
                for segment in question["segments"]:
                    response = labels[segment["sign"]]
                    observed = joined.get((feature, response), {})
                    check(f"{feature}/{response}/source", raw.get((feature, response), {}).get("people"), segment["source_employee_count"])
                    check(f"{feature}/{response}/linked", observed.get("people"), segment["matched_employee_count"])
                    check(f"{feature}/{response}/events", observed.get("events"), segment["voluntary_exit_count"])
                    check(f"{feature}/{response}/rate", observed.get("attrition_percent"), segment["ytd_voluntary_attrition_rate_percent"], 0.000051)
                    at_boundary = known.get((feature, response), {})
                    check(f"{feature}/{response}/cutoff_cohort", at_boundary.get("people"), observed.get("people"))
                    cutoff_comparison.append({"feature": feature, "response": response,
                                              "people_at_boundary": at_boundary.get("people"), "people_retrospective": observed.get("people"),
                                              "events_at_boundary": at_boundary.get("events"), "events_retrospective": observed.get("events")})
        note = "Se concilian los 18 segmentos de 2026 con la plantilla y ventana originales hasta el 23 de agosto, reproduciendo el SQL histórico sin límite de snapshot de registro de eventos. La tabla cutoff_comparison muestra el efecto de limitar esos snapshots al 7 de septiembre. Engineering conserva ese límite; el contraste retrospectivo no acredita publicación ni entra al modelo."
    return {"status": "pass" if checks and all(c["pass"] for c in checks) else "requires_review" if checks else "not_applicable",
            "checks": checks, "reference": str(reference.relative_to(ROOT)) if reference else None,
            "reference_sha256": sha256_file(reference) if reference else None, "note": note,
            "cutoff_comparison": cutoff_comparison}
