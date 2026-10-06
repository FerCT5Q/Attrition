WITH eligible AS (
  SELECT
    annual_base_pay,
    base_pay_rate,
    total_base_pay_amount,
    fte_annual_base_pay,
    fte
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt <= DATE '2026-08-25'
), comparisons AS (
  SELECT
    COUNT(*) AS eligible_rows,
    COUNT(CASE WHEN annual_base_pay IS NOT NULL AND fte_annual_base_pay IS NOT NULL THEN 1 END) AS annual_vs_fte_comparable_rows,
    COUNT(CASE WHEN annual_base_pay IS NOT NULL AND base_pay_rate IS NOT NULL THEN 1 END) AS annual_vs_rate_comparable_rows,
    COUNT(CASE WHEN annual_base_pay IS NOT NULL AND total_base_pay_amount IS NOT NULL THEN 1 END) AS annual_vs_total_comparable_rows,
    COUNT(CASE WHEN annual_base_pay IS NOT NULL AND fte_annual_base_pay IS NOT NULL AND fte IS NOT NULL AND fte > 0 THEN 1 END) AS annual_vs_fte_times_fte_comparable_rows,
    SUM(CASE
      WHEN annual_base_pay IS NOT NULL
       AND fte_annual_base_pay IS NOT NULL
       AND ABS(annual_base_pay - fte_annual_base_pay) <= 0.01
      THEN 1 ELSE 0 END) AS annual_equals_fte_rows,
    SUM(CASE
      WHEN annual_base_pay IS NOT NULL
       AND base_pay_rate IS NOT NULL
       AND ABS(annual_base_pay - base_pay_rate) <= 0.01
      THEN 1 ELSE 0 END) AS annual_equals_rate_rows,
    SUM(CASE
      WHEN annual_base_pay IS NOT NULL
       AND total_base_pay_amount IS NOT NULL
       AND ABS(annual_base_pay - total_base_pay_amount) <= 0.01
      THEN 1 ELSE 0 END) AS annual_equals_total_rows,
    SUM(CASE
      WHEN annual_base_pay IS NOT NULL
       AND fte_annual_base_pay IS NOT NULL
       AND fte IS NOT NULL
       AND fte > 0
       AND ABS(annual_base_pay - (fte_annual_base_pay * fte)) <= 0.01
      THEN 1 ELSE 0 END) AS annual_equals_fte_times_fte_rows,
    SUM(CASE
      WHEN annual_base_pay IS NOT NULL
       AND fte_annual_base_pay IS NOT NULL
       AND fte IS NOT NULL
       AND fte > 0
       AND ABS(fte_annual_base_pay - (annual_base_pay / NULLIF(fte, 0))) <= 0.01
      THEN 1 ELSE 0 END) AS fte_equals_annual_divided_by_fte_rows
  FROM eligible
)
SELECT
  eligible_rows,
  annual_vs_fte_comparable_rows,
  annual_equals_fte_rows,
  ROUND(100.0 * annual_equals_fte_rows / NULLIF(annual_vs_fte_comparable_rows, 0), 2) AS annual_equals_fte_rate_percent,
  annual_vs_rate_comparable_rows,
  annual_equals_rate_rows,
  ROUND(100.0 * annual_equals_rate_rows / NULLIF(annual_vs_rate_comparable_rows, 0), 2) AS annual_equals_rate_percent,
  annual_vs_total_comparable_rows,
  annual_equals_total_rows,
  ROUND(100.0 * annual_equals_total_rows / NULLIF(annual_vs_total_comparable_rows, 0), 2) AS annual_equals_total_rate_percent,
  annual_vs_fte_times_fte_comparable_rows,
  annual_equals_fte_times_fte_rows,
  ROUND(100.0 * annual_equals_fte_times_fte_rows / NULLIF(annual_vs_fte_times_fte_comparable_rows, 0), 2) AS annual_equals_fte_times_fte_rate_percent,
  fte_equals_annual_divided_by_fte_rows,
  ROUND(100.0 * fte_equals_annual_divided_by_fte_rows / NULLIF(annual_vs_fte_times_fte_comparable_rows, 0), 2) AS fte_equals_annual_divided_by_fte_rate_percent
FROM comparisons;
