WITH required AS (
  SELECT 'compa_ratio' AS column_name
  UNION ALL SELECT 'annual_base_pay'
  UNION ALL SELECT 'base_pay_rate'
  UNION ALL SELECT 'total_base_pay_amount'
  UNION ALL SELECT 'fte_annual_base_pay'
  UNION ALL SELECT 'fte_annual_base_pay_currency_code'
  UNION ALL SELECT 'base_pay_frequency'
  UNION ALL SELECT 'compensation_grade'
  UNION ALL SELECT 'compensation_grade_profile'
  UNION ALL SELECT 'mid_payrange'
  UNION ALL SELECT 'midpoint'
  UNION ALL SELECT 'min_payrange'
  UNION ALL SELECT 'max_payrange'
  UNION ALL SELECT 'base_pay_anualized_amt'
  UNION ALL SELECT 'base_pay_amount'
), available AS (
  SELECT
    column_name,
    data_type,
    numeric_precision,
    numeric_scale,
    is_nullable
  FROM information_schema.columns
  WHERE table_schema = 'hrda'
    AND table_name = 'post_hire_monthly_worker_dtls'
)
SELECT
  required.column_name,
  available.data_type,
  available.numeric_precision,
  available.numeric_scale,
  available.is_nullable,
  CASE WHEN available.column_name IS NULL THEN 1 ELSE 0 END AS missing_from_target_table
FROM required
LEFT JOIN available
  ON available.column_name = required.column_name
ORDER BY required.column_name;
