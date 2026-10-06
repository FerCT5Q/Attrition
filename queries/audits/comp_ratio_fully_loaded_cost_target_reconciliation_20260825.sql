WITH target AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    annual_base_pay,
    fte_annual_base_pay,
    compa_ratio,
    compensation_grade_profile,
    labor_market,
    compensation_grade,
    fte_annual_base_pay_currency_code,
    country,
    job_code,
    job_title,
    job_family
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt <= DATE '2026-08-25'
), flc AS (
  SELECT
    compensation_grade_profile,
    labor_market,
    compensation_grade,
    currency,
    country,
    job_code,
    job_title,
    job_family,
    midpoint_usd,
    data_as_of
  FROM hrda.fully_loaded_cost
  WHERE data_as_of <= DATE '2026-08-25'
    AND midpoint_usd > 0
), candidate_matches AS (
  SELECT
    target.employee_id,
    target.fis_mo_end_dt,
    target.annual_base_pay,
    target.fte_annual_base_pay,
    target.compa_ratio,
    flc.midpoint_usd,
    flc.data_as_of,
    COUNT(*) OVER (
      PARTITION BY target.employee_id, target.fis_mo_end_dt
    ) AS temporal_candidate_rows,
    ROW_NUMBER() OVER (
      PARTITION BY target.employee_id, target.fis_mo_end_dt
      ORDER BY flc.data_as_of DESC
    ) AS recency_rank
  FROM target
  JOIN flc
    ON flc.compensation_grade_profile = target.compensation_grade_profile
   AND flc.labor_market = target.labor_market
   AND flc.compensation_grade = target.compensation_grade
   AND flc.currency = target.fte_annual_base_pay_currency_code
   AND flc.country = target.country
   AND CAST(flc.job_code AS VARCHAR(100)) = target.job_code
   AND flc.job_title = target.job_title
   AND flc.job_family = target.job_family
   AND flc.data_as_of <= target.fis_mo_end_dt
), first_matches AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    annual_base_pay,
    fte_annual_base_pay,
    compa_ratio,
    midpoint_usd,
    data_as_of,
    temporal_candidate_rows
  FROM candidate_matches
  WHERE recency_rank = 1
), target_keys AS (
  SELECT DISTINCT employee_id, fis_mo_end_dt
  FROM target
), match_summary AS (
  SELECT
    COUNT(*) AS target_rows,
    COUNT(DISTINCT target_keys.employee_id) AS target_employees,
    COUNT(first_matches.employee_id) AS matched_rows,
    COUNT(DISTINCT first_matches.employee_id || ':' || CAST(first_matches.fis_mo_end_dt AS VARCHAR(30))) AS matched_employee_date_keys,
    SUM(CASE WHEN temporal_candidate_rows > 1 THEN 1 ELSE 0 END) AS rows_with_multiple_temporal_candidates,
    SUM(CASE WHEN compa_ratio IS NOT NULL AND annual_base_pay IS NOT NULL AND midpoint_usd > 0 THEN 1 ELSE 0 END) AS annual_comparable_rows,
    SUM(CASE WHEN compa_ratio IS NOT NULL AND fte_annual_base_pay IS NOT NULL AND midpoint_usd > 0 THEN 1 ELSE 0 END) AS fte_comparable_rows,
    SUM(CASE
      WHEN compa_ratio IS NOT NULL
       AND annual_base_pay IS NOT NULL
       AND midpoint_usd > 0
       AND ABS(compa_ratio - (annual_base_pay / NULLIF(midpoint_usd, 0))) <= 0.01
      THEN 1 ELSE 0 END) AS annual_formula_matches,
    SUM(CASE
      WHEN compa_ratio IS NOT NULL
       AND fte_annual_base_pay IS NOT NULL
       AND midpoint_usd > 0
       AND ABS(compa_ratio - (fte_annual_base_pay / NULLIF(midpoint_usd, 0))) <= 0.01
      THEN 1 ELSE 0 END) AS fte_formula_matches
  FROM target_keys
  LEFT JOIN first_matches
    ON first_matches.employee_id = target_keys.employee_id
   AND first_matches.fis_mo_end_dt = target_keys.fis_mo_end_dt
)
SELECT
  target_rows,
  target_employees,
  matched_rows,
  target_rows - matched_rows AS unmatched_rows,
  rows_with_multiple_temporal_candidates,
  ROUND(100.0 * matched_rows / NULLIF(target_rows, 0), 2) AS matched_row_rate_percent,
  annual_comparable_rows,
  annual_formula_matches,
  ROUND(100.0 * annual_formula_matches / NULLIF(annual_comparable_rows, 0), 2) AS annual_formula_match_rate_percent,
  fte_comparable_rows,
  fte_formula_matches,
  ROUND(100.0 * fte_formula_matches / NULLIF(fte_comparable_rows, 0), 2) AS fte_formula_match_rate_percent
FROM match_summary
WHERE target_employees >= 30;
