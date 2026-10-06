WITH flc AS (
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
), key_date_counts AS (
  SELECT
    compensation_grade_profile,
    labor_market,
    compensation_grade,
    currency,
    country,
    job_code,
    job_title,
    job_family,
    data_as_of,
    COUNT(*) AS rows_at_key_date,
    COUNT(DISTINCT midpoint_usd) AS distinct_midpoints_at_key_date
  FROM flc
  GROUP BY
    compensation_grade_profile,
    labor_market,
    compensation_grade,
    currency,
    country,
    job_code,
    job_title,
    job_family,
    data_as_of
), summary AS (
  SELECT
    COUNT(*) AS flc_rows,
    COUNT(DISTINCT data_as_of) AS data_as_of_dates,
    MIN(data_as_of) AS min_data_as_of,
    MAX(data_as_of) AS max_data_as_of,
    COUNT(CASE WHEN midpoint_usd IS NOT NULL THEN 1 END) AS midpoint_populated_rows,
    COUNT(CASE WHEN midpoint_usd IS NOT NULL AND midpoint_usd > 0 THEN 1 END) AS midpoint_positive_rows,
    COUNT(DISTINCT compensation_grade_profile) AS grade_profile_values,
    COUNT(DISTINCT labor_market) AS labor_market_values,
    COUNT(DISTINCT compensation_grade) AS compensation_grade_values,
    COUNT(DISTINCT currency) AS currency_values,
    COUNT(DISTINCT country) AS country_values,
    COUNT(DISTINCT job_code) AS job_code_values,
    COUNT(DISTINCT job_title) AS job_title_values,
    COUNT(DISTINCT job_family) AS job_family_values
  FROM flc
), key_summary AS (
  SELECT
    COUNT(*) AS key_date_groups,
    SUM(CASE WHEN rows_at_key_date > 1 THEN 1 ELSE 0 END) AS duplicate_key_date_groups,
    SUM(CASE WHEN distinct_midpoints_at_key_date > 1 THEN 1 ELSE 0 END) AS conflicting_midpoint_key_date_groups,
    SUM(CASE WHEN rows_at_key_date = 1 THEN 1 ELSE 0 END) AS unique_key_date_groups
  FROM key_date_counts
)
SELECT
  summary.flc_rows,
  summary.data_as_of_dates,
  summary.min_data_as_of,
  summary.max_data_as_of,
  summary.midpoint_populated_rows,
  summary.midpoint_positive_rows,
  summary.grade_profile_values,
  summary.labor_market_values,
  summary.compensation_grade_values,
  summary.currency_values,
  summary.country_values,
  summary.job_code_values,
  summary.job_title_values,
  summary.job_family_values,
  key_summary.key_date_groups,
  key_summary.duplicate_key_date_groups,
  key_summary.conflicting_midpoint_key_date_groups,
  key_summary.unique_key_date_groups
FROM summary
CROSS JOIN key_summary;
