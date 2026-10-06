"""Record the V7 annual-attrition update without altering the V6 lineage."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "output" / "distribution" / "json" / "attrition-43-variable-distributions-v7-manifest.json"
DECK = ROOT / "output" / "distribution" / "attrition-43-variable-distributions-v7.html"

FILES = (
    "output/distribution/json/attrition-43-variable-distributions-v7.annual-attrition-evidence-20260917.json",
    "output/distribution/json/comp-ratio-annual-attrition-trend-evidence-20260917.json",
    "output/distribution/json/team-turnover-annual-evidence-20260917.json",
    "output/distribution/json/team-post-exit-annual-attrition-evidence-20260917.json",
    "output/distribution/json/commute-distance-onsite-annual-attrition-evidence-20260917.json",
    "queries/audits/annual_voluntary_attrition_segment_rates_20260917.sql",
    "queries/audits/comp_ratio_annual_attrition_trend_20260917.sql",
    "queries/audits/team_turnover_annual_scenarios_20260917.sql",
    "queries/audits/team_post_exit_attrition_annual_calendar_20260917.sql",
    "queries/audits/team_post_exit_attrition_annual_static_cohort_20260917.sql",
    "queries/audits/commute_distance_onsite_annual_attrition_audit_20260917.sql",
    "queries/audits/v7_critical_tech_non_rf360_scope_preflight_20260917.sql",
    "queries/audits/v7_scoped_latest_distribution_20260917.sql",
    "queries/audits/ios_business_process_reason_ytd_attrition_20260917.sql",
    "output/distribution/json/attrition-43-variable-distributions-v7.scoped-latest-distribution-evidence-20260917.json",
    "output/distribution/json/attrition-43-variable-distributions-v7.ios-movement-reasons-ytd-evidence-20260917.json",
)


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing = [relative for relative in FILES if not (ROOT / relative).exists()]
    if missing:
        raise FileNotFoundError("Missing annual evidence: " + ", ".join(missing))
    document["generated_on"] = date.today().isoformat()
    document["objective"] = "Render V7 only with the approved Critical Tech, non-RF360 population; replace all six-month attrition outcomes with validated annual attrition while preserving non-outcome feature windows only where they are explicitly scoped."
    document["annual_attrition_update"] = {
        "outcome_window": "Strict voluntary termination in the 12 months after the monthly snapshot, except measures explicitly defined as retrospective annual team exposure.",
        "updated_slides": [1, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 31, 35, 38, 39, 48],
        "unchanged_six_month_feature_windows": [3, 4, 47, 49],
        "evidence_and_sql": [{"path": relative, "sha256": hash_file(ROOT / relative)} for relative in FILES],
        "privacy": "presentation mode; aggregate-only; protected gender labels remain anonymized; visible cohorts and event cells meet n >= 30.",
    }
    document["population_scope_refresh"] = {
        "population": "worker_type='Employee' AND employee_type='Regular' AND active_status=1 AND is_rf360_yes_no=0; inner join to hrda.critical_tech on normalized job_family=extended_job_family; exclude seg='Other Eng'.",
        "current_snapshot": "2026-09-27",
        "scoped_employee_count": 11544,
        "directly_refreshed_slides": [5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 31, 35, 38, 39, 48],
        "suppressed_pending_scoped_recalculation": [3, 4, 9, 10, 20, 21, 22, 23, 24, 25, 26, 27, 29, 32, 33, 34, 36, 37, 40, 41, 42, 43, 44, 45, 46, 47, 49, 50, 51, 52],
        "scope_preflight": "queries/audits/v7_critical_tech_non_rf360_scope_preflight_20260917.sql",
        "current_distribution_evidence": "output/distribution/json/attrition-43-variable-distributions-v7.scoped-latest-distribution-evidence-20260917.json",
        "policy": "No historical Qualcomm-wide value is retained under the scoped population label. Unsupported source-specific calculations render a transparent non-publication state.",
    }
    document["output_deck"] = {"path": str(DECK.relative_to(ROOT)).replace("\\", "/"), "sha256": hash_file(DECK)}
    MANIFEST.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(MANIFEST)


if __name__ == "__main__":
    main()
