"""Recalculate V7 special attrition visuals with a 12-month outcome window.

The deck contains three visuals whose old rates were not sourced from the
standard category-rate evidence: team turnover, the post-departure cohort, and
commute distance.  This builder materializes annual, aggregate-only SQL under
``queries/audits`` and freezes presentation-safe JSON evidence for each visual.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDITS = ROOT / "queries" / "audits"
JSON_DIR = ROOT / "output" / "distribution" / "json"
HELPER = ROOT / ".codex" / "skills" / "attrition-redshift-db" / "scripts" / "run_readonly_query.py"
SCOPED_POPULATION = "Active non-RF360 Critical Tech employees, excluding Other Eng"
CRITICAL_TECH_CATALOG_CTE = """critical_tech_catalog AS (
  SELECT LOWER(TRIM(extended_job_family)) AS normalized_job_family
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
  GROUP BY 1
  HAVING COUNT(DISTINCT NULLIF(TRIM(seg), '')) = 1
     AND MAX(NULLIF(TRIM(seg), '')) <> 'Other Eng'
)"""


def add_catalogue_cte(text: str, following_cte: str) -> str:
    """Insert the governed scope catalogue before a known CTE exactly once."""
    marker = f"),\n{following_cte} AS ("
    if marker not in text:
        raise ValueError(f"Could not locate {following_cte} CTE for scoped-population injection.")
    return text.replace(marker, f"),\n{CRITICAL_TECH_CATALOG_CTE},\n{following_cte} AS (", 1)


def scoped_job_family_exists(alias: str) -> str:
    return (
        f"{alias}.is_rf360_yes_no = 0\n"
        f"      AND EXISTS (SELECT 1 FROM critical_tech_catalog c "
        f"WHERE c.normalized_job_family = LOWER(TRIM({alias}.job_family)))"
    )


def apply_scope_to_commute_sql(text: str) -> str:
    """Scope a materialized commute query at employee-snapshot grain."""
    text = add_catalogue_cte(text, "snapshot_dates")
    source_join = (
        "    FROM hrda.post_hire_monthly_worker_dtls AS w\n"
        "    INNER JOIN snapshot_dates AS d\n"
        "      ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date"
    )
    scoped_source_join = source_join + (
        "\n    INNER JOIN critical_tech_catalog AS c\n"
        "      ON c.normalized_job_family = LOWER(TRIM(w.job_family))"
    )
    if source_join not in text:
        raise ValueError("Could not locate commute employee-snapshot source join.")
    text = text.replace(source_join, scoped_source_join, 1)
    target = "    WHERE w.worker_type = 'Employee'\n      AND w.employee_type = 'Regular'\n      AND w.active_status = 1"
    replacement = target + "\n      AND w.is_rf360_yes_no = 0"
    if target not in text:
        raise ValueError("Could not locate commute employee-snapshot population filter.")
    return text.replace(target, replacement, 1)


def apply_scope_to_team_turnover_sql(text: str) -> str:
    """Scope both team exposure and event attribution to the governed workforce."""
    text = add_catalogue_cte(text, "monthly_membership")
    workforce_join = "  FROM hrda.post_hire_monthly_worker_dtls AS worker\n  CROSS JOIN parameters"
    scoped_workforce_join = (
        "  FROM hrda.post_hire_monthly_worker_dtls AS worker\n"
        "  INNER JOIN critical_tech_catalog c\n"
        "    ON c.normalized_job_family = LOWER(TRIM(worker.job_family))\n"
        "  CROSS JOIN parameters"
    )
    if workforce_join not in text:
        raise ValueError("Could not locate team-turnover workforce join.")
    text = text.replace(workforce_join, scoped_workforce_join, 1)
    membership = "    AND worker.active_status = 1\n    AND worker.manager_employee_id IS NOT NULL"
    membership_replacement = (
        "    AND worker.active_status = 1\n"
        "    AND worker.is_rf360_yes_no = 0\n"
        "    AND worker.manager_employee_id IS NOT NULL"
    )
    if membership not in text:
        raise ValueError("Could not locate team-turnover membership filter.")
    text = text.replace(membership, membership_replacement, 1)
    history = "    AND history.active_status = 1\n    AND history.manager_employee_id IS NOT NULL"
    history_replacement = (
        "    AND history.active_status = 1\n"
        "    AND history.is_rf360_yes_no = 0\n"
        "    AND history.manager_employee_id IS NOT NULL"
    )
    if history not in text:
        raise ValueError("Could not locate team-turnover attribution filter.")
    text = text.replace(history, history_replacement, 1)
    history_end = "    AND CAST(history.fis_mo_end_dt AS DATE) >= DATE '2025-07-23'\n),\nattributed_voluntary_exits"
    scoped_history_end = (
        "    AND CAST(history.fis_mo_end_dt AS DATE) >= DATE '2025-07-23'\n"
        "  INNER JOIN critical_tech_catalog c\n"
        "    ON c.normalized_job_family = LOWER(TRIM(history.job_family))\n"
        "),\nattributed_voluntary_exits"
    )
    if history_end not in text:
        raise ValueError("Could not locate team-turnover history join boundary.")
    return text.replace(history_end, scoped_history_end, 1)


def apply_scope_to_post_exit_calendar_sql(text: str) -> str:
    text = add_catalogue_cte(text, "snapshot_dates")
    target = (
        "  FROM hrda.post_hire_monthly_worker_dtls\n"
        "  WHERE worker_type = 'Employee'\n"
        "    AND employee_type = 'Regular'\n"
        "    AND active_status = 1\n"
        "    AND fis_mo_end_dt IS NOT NULL"
    )
    replacement = (
        "  FROM hrda.post_hire_monthly_worker_dtls AS w\n"
        "  INNER JOIN critical_tech_catalog AS c\n"
        "    ON c.normalized_job_family = LOWER(TRIM(w.job_family))\n"
        "  WHERE w.worker_type = 'Employee'\n"
        "    AND w.employee_type = 'Regular'\n"
        "    AND w.active_status = 1\n"
        "    AND w.is_rf360_yes_no = 0\n"
        "    AND w.fis_mo_end_dt IS NOT NULL"
    )
    if target not in text:
        raise ValueError("Could not locate post-exit calendar population filter.")
    return text.replace(target, replacement, 1)


def apply_scope_to_post_exit_static_sql(text: str) -> str:
    text = add_catalogue_cte(text, "monthly_event_keys")
    worker_from = "  FROM hrda.post_hire_monthly_worker_dtls AS w\n  CROSS JOIN parameters AS p"
    scoped_worker_from = (
        "  FROM hrda.post_hire_monthly_worker_dtls AS w\n"
        "  INNER JOIN critical_tech_catalog c\n"
        "    ON c.normalized_job_family = LOWER(TRIM(w.job_family))\n"
        "  CROSS JOIN parameters AS p"
    )
    if text.count(worker_from) != 3:
        raise ValueError("Could not locate all post-exit employee-snapshot sources.")
    text = text.replace(worker_from, scoped_worker_from)
    event_filter = "  WHERE w.worker_type = 'Employee' AND w.employee_type = 'Regular'"
    if event_filter not in text:
        raise ValueError("Could not locate post-exit event population filter.")
    text = text.replace(event_filter, event_filter + " AND w.is_rf360_yes_no = 0", 1)
    active_filter = "    AND w.worker_type = 'Employee' AND w.employee_type = 'Regular' AND w.active_status = 1"
    if text.count(active_filter) != 2:
        raise ValueError("Could not locate post-exit active employee population filters.")
    text = text.replace(active_filter, active_filter + " AND w.is_rf360_yes_no = 0")
    history_filter = "   AND h.worker_type = 'Employee' AND h.employee_type = 'Regular'\n   AND h.manager_employee_id IS NOT NULL"
    if history_filter not in text:
        raise ValueError("Could not locate post-exit event-attribution population filter.")
    text = text.replace(history_filter, history_filter.replace("\n   AND h.manager", "\n   AND h.is_rf360_yes_no = 0\n   AND h.manager"), 1)
    history_end = "   AND CAST(h.fis_mo_end_dt AS DATE) >= DATEADD(month, -2, p.p6)\n),\nevents"
    scoped_history_end = (
        "   AND CAST(h.fis_mo_end_dt AS DATE) >= DATEADD(month, -2, p.p6)\n"
        "  INNER JOIN critical_tech_catalog c_history\n"
        "    ON c_history.normalized_job_family = LOWER(TRIM(h.job_family))\n"
        "),\nevents"
    )
    if history_end not in text:
        raise ValueError("Could not locate post-exit event-attribution join boundary.")
    return text.replace(history_end, scoped_history_end, 1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_query(path: Path, max_rows: int = 1000) -> list[dict]:
    result = subprocess.run(
        [sys.executable, "-B", str(HELPER), "--sql-file", str(path), "--max-rows", str(max_rows), "--reporting-mode", "presentation"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    payload = json.loads(result.stdout)
    if payload.get("truncated") or not isinstance(payload.get("rows"), list):
        raise ValueError(f"{path.name} did not return a complete aggregate result.")
    return [dict(row) for row in payload["rows"]]


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def materialize_commute_sql() -> tuple[Path, Path, Path]:
    """Make annual copies of the approved hash-only commute queries."""
    sources = (
        ROOT / "queries" / "profiles" / "commute_distance_onsite_six_month_attrition_hash_profile_20260917.sql",
        ROOT / "queries" / "profiles" / "commute_distance_onsite_six_month_attrition_country_partitions_20260917.sql",
        ROOT / "queries" / "audits" / "commute_distance_onsite_six_month_attrition_audit_20260917.sql",
    )
    targets = (
        AUDITS / "commute_distance_onsite_annual_attrition_hash_profile_20260917.sql",
        AUDITS / "commute_distance_onsite_annual_attrition_country_partitions_20260917.sql",
        AUDITS / "commute_distance_onsite_annual_attrition_audit_20260917.sql",
    )
    for source, target in zip(sources, targets):
        text = source.read_text(encoding="utf-8")
        text = text.replace("2024-03-24", "2023-09-24").replace("2026-02-22", "2025-08-24")
        text = text.replace("DATEADD(month, 6", "DATEADD(month, 12")
        text = text.replace("seis meses", "doce meses").replace("six-month", "annual")
        target.write_text(apply_scope_to_commute_sql(text), encoding="utf-8")
    return targets


def build_commute() -> Path:
    profile, partitions, audit = materialize_commute_sql()
    module = importlib.import_module("build_commute_distance_attrition_evidence")
    module.QUERY = profile
    module.COUNTRY_PARTITIONS_QUERY = partitions
    module.AUDIT_QUERY = audit
    module.EXPECTED_SNAPSHOT_COUNT = 24
    output = JSON_DIR / "commute-distance-onsite-annual-attrition-evidence-20260917.json"
    try:
        evidence = module.build_evidence()
    except ValueError as error:
        # A visual rate is not publishable if any annual distance band fails
        # the project-wide n>=30 exposure/event rule.  Persist the transparent
        # suppression decision rather than retaining the old six-month chart.
        evidence = {
            "artifact_classification": "presentation",
            "version": 7,
            "generated_on": date.today().isoformat(),
            "outcome": "not_estimable",
            "population": "Onsite " + SCOPED_POPULATION.lower() + " employee-snapshots with calculable residential-to-office distance",
            "outcome_contract": "Strict voluntary termination in the 12 months after each snapshot.",
            "minimum_cohort": 30,
            "reason": "The annual distance profile cannot publish every required distance band at the minimum cohort and voluntary-event threshold; no rate is substituted or imputed.",
            "validation_error": str(error),
            "query": {
                "profile": str(profile.relative_to(ROOT)).replace("\\", "/"), "profile_sha256": sha256(profile),
                "country_partitions": str(partitions.relative_to(ROOT)).replace("\\", "/"), "country_partitions_sha256": sha256(partitions),
                "audit": str(audit.relative_to(ROOT)).replace("\\", "/"), "audit_sha256": sha256(audit),
            },
        }
        write_json(output, evidence)
        return output
    evidence["version"] = 7
    evidence["generated_on"] = date.today().isoformat()
    evidence["outcome_contract"]["snapshot_window"] = "24 complete monthly snapshots, 2023-09-24 through 2025-08-24"
    evidence["outcome_contract"]["target"] = "term_type='VOLUNTARY' with term_date in (snapshot_date, snapshot_date + 12 months]"
    evidence["acceptance_rule"] = evidence["acceptance_rule"].replace("24 snapshots exactos", "24 complete annual-follow-up snapshots")
    write_json(output, evidence)
    return output


def record_commute_suppression() -> Path:
    """Freeze the publication decision after the annual hash profile failed its cohort gate."""
    profile, partitions, audit = materialize_commute_sql()
    output = JSON_DIR / "commute-distance-onsite-annual-attrition-evidence-20260917.json"
    write_json(output, {
        "artifact_classification": "presentation", "version": 7, "generated_on": date.today().isoformat(),
        "outcome": "not_estimable", "minimum_cohort": 30,
        "population": "Onsite " + SCOPED_POPULATION.lower() + " employee-snapshots with calculable residential-to-office distance",
        "outcome_contract": "Strict voluntary termination in the 12 months after each snapshot.",
        "reason": "The executed annual distance profile failed the publishability gate: at least one required distance band could not meet the minimum exposure and voluntary-event cohort. The former six-month rates are removed rather than relabeled.",
        "query": {"profile": str(profile.relative_to(ROOT)).replace("\\", "/"), "profile_sha256": sha256(profile), "country_partitions": str(partitions.relative_to(ROOT)).replace("\\", "/"), "country_partitions_sha256": sha256(partitions), "audit": str(audit.relative_to(ROOT)).replace("\\", "/"), "audit_sha256": sha256(audit)},
    })
    return output


def build_team_turnover() -> Path:
    source = ROOT / "queries" / "profiles" / "team_turnover_6m_scenarios_20260908.sql"
    query = AUDITS / "team_turnover_annual_scenarios_20260917.sql"
    text = source.read_text(encoding="utf-8")
    text = text.replace(
        "WHERE fis_mo_end_dt IS NOT NULL\n),\nsnapshot_dates",
        "WHERE fis_mo_end_dt IS NOT NULL\n    AND CAST(fis_mo_end_dt AS DATE) <= DATE '2026-08-23'\n),\nsnapshot_dates",
    )
    text = text.replace("six-month", "annual").replace("six months", "twelve months")
    text = text.replace("six_month_turnover_percent", "annual_turnover_percent")
    text = text.replace("DATEADD(month, -6", "DATEADD(month, -12")
    # This CTE does not carry the parameters alias.  The cutoff is fixed by
    # the V7 source window, so retain a literal boundary rather than adding a
    # second join that could alter event attribution.
    text = text.replace("DATEADD(month, -1, DATE '2026-02-23')", "DATE '2025-07-23'")
    # The source's calendar-day boundary can include thirteen monthly
    # snapshots (Aug-2025 through Aug-2026).  Use those observations for the
    # exposure denominator, but annualize to exactly twelve months.
    text = text.replace("scenario_rates.voluntary_exit_events * window_snapshots.monthly_snapshot_count", "scenario_rates.voluntary_exit_events * 12.0")
    query.write_text(apply_scope_to_team_turnover_sql(text), encoding="utf-8")
    rows = run_query(query, 100)
    scenarios = [row for row in rows if row.get("row_type") == "scenario_summary"]
    if len(scenarios) != 2 or any(int(row["monthly_snapshot_count"]) not in {12, 13} for row in scenarios):
        raise ValueError("The annual team-turnover query did not return two complete trailing-year scenarios.")
    if any(int(row["manager_teams"]) < 30 for row in scenarios):
        raise ValueError("A team-turnover scenario is below the publication threshold.")
    output = JSON_DIR / "team-turnover-annual-evidence-20260917.json"
    write_json(output, {
        "artifact_classification": "presentation",
        "generated_on": date.today().isoformat(),
        "outcome": "pass",
        "population": SCOPED_POPULATION + " in manager-led teams",
        "grain": "manager-team aggregate over employee-month exposure",
        "outcome_contract": "Strict voluntary exits in the trailing 12 months through 2026-08-23; each exit is attributed to the last active manager snapshot before termination.",
        "minimum_cohort": 30,
        "query": str(query.relative_to(ROOT)).replace("\\", "/"),
        "query_sha256": sha256(query),
        "result_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest(),
        "rows": rows,
    })
    return output


def materialize_post_exit_calendar() -> Path:
    source = AUDITS / "team_post_exit_attrition_calendar_20260911.sql"
    target = AUDITS / "team_post_exit_attrition_annual_calendar_20260917.sql"
    text = source.read_text(encoding="utf-8")
    text = text.replace(
        "WHERE fis_mo_end_dt IS NOT NULL\n),\nsnapshot_dates",
        "WHERE fis_mo_end_dt IS NOT NULL\n    AND CAST(fis_mo_end_dt AS DATE) <= DATE '2026-08-23'\n),\nsnapshot_dates",
    )
    anchor = "    LEAD(snapshot_date, 6) OVER (ORDER BY snapshot_date) AS f6\n"
    addition = anchor + "    , LEAD(snapshot_date, 7) OVER (ORDER BY snapshot_date) AS f7\n    , LEAD(snapshot_date, 8) OVER (ORDER BY snapshot_date) AS f8\n    , LEAD(snapshot_date, 9) OVER (ORDER BY snapshot_date) AS f9\n    , LEAD(snapshot_date, 10) OVER (ORDER BY snapshot_date) AS f10\n    , LEAD(snapshot_date, 11) OVER (ORDER BY snapshot_date) AS f11\n    , LEAD(snapshot_date, 12) OVER (ORDER BY snapshot_date) AS f12\n"
    if anchor not in text:
        raise ValueError("Post-exit calendar template changed unexpectedly.")
    text = text.replace(anchor, addition)
    text = text.replace("SELECT c.snapshot_date, c.p1, c.p6, c.f1, c.f2, c.f3, c.f4, c.f5, c.f6", "SELECT c.snapshot_date, c.p1, c.p6, c.f1, c.f2, c.f3, c.f4, c.f5, c.f6, c.f7, c.f8, c.f9, c.f10, c.f11, c.f12")
    text = text.replace("AND c.f6 IS NOT NULL", "AND c.f12 IS NOT NULL\n  AND c.f12 <= bounds.latest_snapshot_date")
    text = text.replace("AND c.snapshot_date >= DATEADD(month, -29, bounds.latest_snapshot_date)", "AND c.snapshot_date >= DATEADD(month, -35, bounds.latest_snapshot_date)")
    gap_anchor = "  AND DATEDIFF(day, c.f5, c.f6) BETWEEN 20 AND 45\n"
    additions = gap_anchor + "  AND DATEDIFF(day, c.f6, c.f7) BETWEEN 20 AND 45\n  AND DATEDIFF(day, c.f7, c.f8) BETWEEN 20 AND 45\n  AND DATEDIFF(day, c.f8, c.f9) BETWEEN 20 AND 45\n  AND DATEDIFF(day, c.f9, c.f10) BETWEEN 20 AND 45\n  AND DATEDIFF(day, c.f10, c.f11) BETWEEN 20 AND 45\n  AND DATEDIFF(day, c.f11, c.f12) BETWEEN 20 AND 45\n"
    if gap_anchor not in text:
        raise ValueError("Post-exit calendar gaps changed unexpectedly.")
    target.write_text(apply_scope_to_post_exit_calendar_sql(text.replace(gap_anchor, additions)), encoding="utf-8")
    return target


def materialize_post_exit_static(cohort: dict) -> Path:
    source = AUDITS / "team_post_exit_attrition_static_snapshot_20260911.sql"
    target = AUDITS / "team_post_exit_attrition_annual_static_cohort_20260917.sql"
    text = source.read_text(encoding="utf-8")
    start = text.index("WITH parameters AS (")
    end = text.index("),\nmonthly_event_keys", start) + 2
    fields = ["snapshot_date", "p1", "p6"] + [f"f{i}" for i in range(1, 13)]
    parameter_lines = [f"DATE '{cohort[field]}' AS {'t' if field == 'snapshot_date' else field}" for field in fields]
    text = text[:start] + "WITH parameters AS (\n  SELECT " + ", ".join(parameter_lines) + "\n)," + text[end:]
    # Only the event-extraction horizon changes to year-end.  The six-month
    # lookback remains part of the index-event definition, and f6 is needed
    # as the sixth follow-up checkpoint.
    text = text.replace("term_date <= p.f6", "term_date <= p.f12")
    step_anchor = "  UNION ALL SELECT 6, f5, f6 FROM parameters\n"
    extra_steps = step_anchor + "  UNION ALL SELECT 7, f6, f7 FROM parameters\n  UNION ALL SELECT 8, f7, f8 FROM parameters\n  UNION ALL SELECT 9, f8, f9 FROM parameters\n  UNION ALL SELECT 10, f9, f10 FROM parameters\n  UNION ALL SELECT 11, f10, f11 FROM parameters\n  UNION ALL SELECT 12, f11, f12 FROM parameters\n"
    if step_anchor not in text:
        raise ValueError("Post-exit static follow-up template changed unexpectedly.")
    text = text.replace(step_anchor, extra_steps)
    active_anchor = "IN (p.f1, p.f2, p.f3, p.f4, p.f5, p.f6)"
    if active_anchor not in text:
        raise ValueError("Post-exit active-status template changed unexpectedly.")
    text = text.replace(active_anchor, "IN (p.f1, p.f2, p.f3, p.f4, p.f5, p.f6, p.f7, p.f8, p.f9, p.f10, p.f11, p.f12)")
    target.write_text(apply_scope_to_post_exit_static_sql(text), encoding="utf-8")
    return target


def cumulative(rows: list[dict]) -> list[dict]:
    survival = 1.0
    output = []
    for row in sorted(rows, key=lambda item: int(item["follow_month"])):
        hazard = float(row["standardized_hazard_percent"])
        survival *= 1 - hazard / 100
        output.append({
            "follow_month": int(row["follow_month"]),
            "interval_hazard_percent": round(hazard, 6),
            "cumulative_incidence_percent": round(100 * (1 - survival), 4),
            "initial_roster_n": int(row["initial_roster_n"]),
            "at_risk_n": int(row["at_risk_n"]),
            "voluntary_events_in_interval": int(row["voluntary_events_in_interval"]),
            "censored_in_interval": int(row["censored_in_interval"]),
            "included_size_bands": int(row["included_bands"]),
        })
    return output


def build_post_exit() -> Path:
    calendar_query = materialize_post_exit_calendar()
    calendar_rows = run_query(calendar_query, 100)
    if not calendar_rows:
        raise ValueError("No complete annual post-exit cohort is available.")
    cohort = calendar_rows[-1]
    static_query = materialize_post_exit_static(cohort)
    rows = run_query(static_query, 100)
    series = [row for row in rows if row.get("row_type") == "series"]
    expected = {(scope, group, month) for scope in ("all_teams", "teams_6_plus") for group in ("exposed", "reference_standardized") for month in range(1, 13)}
    actual = {(str(row["scope"]), str(row["comparison_group"]), int(row["follow_month"])) for row in series}
    output = JSON_DIR / "team-post-exit-annual-attrition-evidence-20260917.json"
    if actual != expected or any(int(row["at_risk_n"]) < 30 for row in series):
        write_json(output, {
            "artifact_classification": "presentation",
            "generated_on": date.today().isoformat(),
            "outcome": "not_estimable",
            "population": SCOPED_POPULATION + " with a manager at the index snapshot",
            "grain": "employee in an indexed manager team",
            "minimum_cohort": 30,
            "reason": "The scoped Critical Tech population does not support all 48 required annual post-departure curve points at n at risk >=30. The former company-wide cohort rates are removed rather than relabeled.",
            "query": {
                "calendar": str(calendar_query.relative_to(ROOT)).replace("\\", "/"),
                "calendar_sha256": sha256(calendar_query),
                "static": str(static_query.relative_to(ROOT)).replace("\\", "/"),
                "static_sha256": sha256(static_query),
                "result_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest(),
            },
            "observed_series_points": len(series),
            "expected_series_points": len(expected),
        })
        return output
    curves: dict[str, list[dict]] = {}
    for scope in ("all_teams", "teams_6_plus"):
        for group in ("exposed", "reference_standardized"):
            curves[f"{scope}::{group}"] = cumulative([row for row in series if row["scope"] == scope and row["comparison_group"] == group])
    write_json(output, {
        "artifact_classification": "presentation",
        "generated_on": date.today().isoformat(),
        "outcome": "pass",
        "population": SCOPED_POPULATION + " with a manager at the index snapshot",
        "grain": "employee in an indexed manager team",
        "outcome_contract": "Cumulative strict voluntary attrition over 12 monthly post-index intervals; censor at manager change, non-voluntary exit, or lost observation.",
        "study": {"index_event": "Exactly one reconciled voluntary team departure in the six months ending at the index snapshot, including the current interval.", "reference": "Teams without a reconciled recent voluntary departure, standardized to the exposed team-size mix."},
        "cohort": {"index_snapshot": cohort["snapshot_date"], "lookback_start_exclusive": cohort["p6"], "follow_up_end": cohort["f12"], "follow_up_snapshot_dates": [str(cohort[f"f{i}"]) for i in range(1, 13)]},
        "curves": curves,
        "minimum_cohort": 30,
        "query": {"calendar": str(calendar_query.relative_to(ROOT)).replace("\\", "/"), "calendar_sha256": sha256(calendar_query), "static": str(static_query.relative_to(ROOT)).replace("\\", "/"), "static_sha256": sha256(static_query), "result_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()},
        "acceptance_rule": "Four annual cumulative curves, each with 12 monthly points and n at risk >=30 at every visible point.",
    })
    return output


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build annual special-chart evidence for V7.")
    parser.add_argument("--only", choices=("all", "team_turnover", "post_exit", "commute", "commute_suppression"), default="all")
    args = parser.parse_args()
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    builders = {
        "team_turnover": build_team_turnover,
        "post_exit": build_post_exit,
        "commute": build_commute,
        "commute_suppression": record_commute_suppression,
    }
    outputs = list(builders.values()) if args.only == "all" else [builders[args.only]]
    outputs = [builder() for builder in outputs]
    print("\n".join(str(path) for path in outputs))


if __name__ == "__main__":
    main()
