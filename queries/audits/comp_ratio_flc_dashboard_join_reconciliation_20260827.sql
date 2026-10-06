-- Comp ratio: diagnostic based on the Tableau FLC dashboard lineage.
--
-- Tableau uses hrda.fully_loaded_cost filtered to the latest
-- last_modified_date and joins it to the employee feed only by
-- compensation_grade_profile and job_code. This audit tests that exact
-- structural hypothesis against the monthly employee target.
--
-- This is not a time-safe formula confirmation. The dashboard join does not
-- constrain data_as_of to the employee snapshot date. Results are aggregate
-- only; employee identifiers remain internal to the join.

WITH target AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    annual_base_pay,
    fte_annual_base_pay,
    compa_ratio,
    compensation_grade_profile,
    job_code
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt <= DATE '2026-08-26'
),
flc_latest_load AS (
  SELECT
    compensation_grade_profile,
    job_code,
    midpoint_usd,
    data_as_of,
    last_modified_date,
    COUNT(*) OVER (
      PARTITION BY compensation_grade_profile, job_code
    ) AS flc_rows_per_dashboard_key,
    ROW_NUMBER() OVER (
      PARTITION BY compensation_grade_profile, job_code
      ORDER BY data_as_of DESC, midpoint_usd DESC
    ) AS flc_key_rank
  FROM hrda.fully_loaded_cost
  WHERE last_modified_date = (
    SELECT MAX(last_modified_date)
    FROM hrda.fully_loaded_cost
  )
    AND midpoint_usd > 0
),
flc_one_per_key AS (
  SELECT
    compensation_grade_profile,
    job_code,
    midpoint_usd,
    data_as_of,
    last_modified_date,
    flc_rows_per_dashboard_key
  FROM flc_latest_load
  WHERE flc_key_rank = 1
),
matched AS (
  SELECT
    target.employee_id,
    target.fis_mo_end_dt,
    target.annual_base_pay,
    target.fte_annual_base_pay,
    target.compa_ratio,
    flc.midpoint_usd,
    flc.data_as_of,
    flc.last_modified_date,
    flc.flc_rows_per_dashboard_key
  FROM target
  LEFT JOIN flc_one_per_key AS flc
    ON flc.compensation_grade_profile = target.compensation_grade_profile
   AND flc.job_code = target.job_code
),
target_summary AS (
  SELECT
    COUNT(*) AS target_rows,
    COUNT(DISTINCT employee_id || ':' || CAST(fis_mo_end_dt AS VARCHAR(30))) AS target_employee_date_keys
  FROM target
),
match_summary AS (
  SELECT
    COUNT(CASE WHEN midpoint_usd IS NOT NULL THEN 1 END) AS matched_rows,
    COUNT(CASE WHEN midpoint_usd IS NULL THEN 1 END) AS unmatched_rows,
    COUNT(CASE WHEN midpoint_usd IS NOT NULL AND flc_rows_per_dashboard_key > 1 THEN 1 END) AS rows_with_multiple_flc_matches,
    COUNT(CASE
      WHEN midpoint_usd IS NOT NULL
       AND compa_ratio IS NOT NULL
       AND annual_base_pay IS NOT NULL
      THEN 1 END) AS annual_comparable_rows,
    COUNT(CASE
      WHEN midpoint_usd IS NOT NULL
       AND compa_ratio IS NOT NULL
       AND annual_base_pay IS NOT NULL
       AND ABS(compa_ratio - annual_base_pay / NULLIF(midpoint_usd, 0)) <= 0.01
      THEN 1 END) AS annual_formula_matches,
    COUNT(CASE
      WHEN midpoint_usd IS NOT NULL
       AND compa_ratio IS NOT NULL
       AND fte_annual_base_pay IS NOT NULL
      THEN 1 END) AS fte_comparable_rows,
    COUNT(CASE
      WHEN midpoint_usd IS NOT NULL
       AND compa_ratio IS NOT NULL
       AND fte_annual_base_pay IS NOT NULL
       AND ABS(compa_ratio - fte_annual_base_pay / NULLIF(midpoint_usd, 0)) <= 0.01
      THEN 1 END) AS fte_formula_matches,
    MAX(last_modified_date) AS flc_latest_last_modified_date,
    MAX(data_as_of) AS max_selected_data_as_of
  FROM matched
)
SELECT
  target_summary.target_rows,
  target_summary.target_employee_date_keys,
  match_summary.matched_rows,
  match_summary.unmatched_rows,
  ROUND(100.0 * match_summary.matched_rows / NULLIF(target_summary.target_rows, 0), 2) AS matched_rate_percent,
  match_summary.rows_with_multiple_flc_matches,
  match_summary.annual_comparable_rows,
  match_summary.annual_formula_matches,
  ROUND(100.0 * match_summary.annual_formula_matches / NULLIF(match_summary.annual_comparable_rows, 0), 2) AS annual_formula_match_rate_percent,
  match_summary.fte_comparable_rows,
  match_summary.fte_formula_matches,
  ROUND(100.0 * match_summary.fte_formula_matches / NULLIF(match_summary.fte_comparable_rows, 0), 2) AS fte_formula_match_rate_percent,
  match_summary.flc_latest_last_modified_date,
  match_summary.max_selected_data_as_of
FROM target_summary
CROSS JOIN match_summary;
