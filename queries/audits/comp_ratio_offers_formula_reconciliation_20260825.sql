WITH eligible AS (
  SELECT
    employee_id,
    candidate_id,
    base_pay_amount,
    base_pay_anualized_amt,
    compa_ratio_base_pay,
    min_payrange,
    mid_payrange,
    max_payrange,
    base_pay_amount_currency_code,
    base_pay_anualized_amt_currency_code
  FROM hrda.offers
  WHERE last_updated_date <= DATE '2026-08-25'
    AND employee_id IS NOT NULL
), metrics AS (
  SELECT
    COUNT(*) AS source_rows,
    COUNT(DISTINCT employee_id) AS source_employees,
    SUM(CASE WHEN compa_ratio_base_pay IS NOT NULL THEN 1 ELSE 0 END) AS ratio_populated_rows,
    COUNT(DISTINCT CASE WHEN compa_ratio_base_pay IS NOT NULL THEN employee_id END) AS ratio_populated_employees,
    SUM(CASE WHEN base_pay_amount IS NOT NULL AND mid_payrange > 0 THEN 1 ELSE 0 END) AS amount_comparable_rows,
    COUNT(DISTINCT CASE WHEN base_pay_amount IS NOT NULL AND mid_payrange > 0 THEN employee_id END) AS amount_comparable_employees,
    SUM(CASE WHEN base_pay_anualized_amt IS NOT NULL AND mid_payrange > 0 THEN 1 ELSE 0 END) AS annualized_comparable_rows,
    COUNT(DISTINCT CASE WHEN base_pay_anualized_amt IS NOT NULL AND mid_payrange > 0 THEN employee_id END) AS annualized_comparable_employees,
    SUM(CASE
      WHEN compa_ratio_base_pay IS NOT NULL
       AND base_pay_amount IS NOT NULL
       AND mid_payrange > 0
       AND ABS(compa_ratio_base_pay - (base_pay_amount / NULLIF(mid_payrange, 0))) <= 0.01
      THEN 1 ELSE 0 END) AS amount_match_within_001_rows,
    SUM(CASE
      WHEN compa_ratio_base_pay IS NOT NULL
       AND base_pay_amount IS NOT NULL
       AND mid_payrange > 0
       AND compa_ratio_base_pay = ROUND(base_pay_amount / NULLIF(mid_payrange, 0), 2)
      THEN 1 ELSE 0 END) AS amount_match_after_rounding_rows,
    SUM(CASE
      WHEN compa_ratio_base_pay IS NOT NULL
       AND base_pay_anualized_amt IS NOT NULL
       AND mid_payrange > 0
       AND ABS(compa_ratio_base_pay - (base_pay_anualized_amt / NULLIF(mid_payrange, 0))) <= 0.01
      THEN 1 ELSE 0 END) AS annualized_match_within_001_rows,
    SUM(CASE
      WHEN compa_ratio_base_pay IS NOT NULL
       AND base_pay_amount IS NOT NULL
       AND mid_payrange > 0
       AND ABS(compa_ratio_base_pay - (base_pay_amount / NULLIF(mid_payrange, 0))) > 0.01
      THEN 1 ELSE 0 END) AS amount_mismatch_rows,
    SUM(CASE
      WHEN compa_ratio_base_pay IS NOT NULL
       AND base_pay_anualized_amt IS NOT NULL
       AND mid_payrange > 0
       AND ABS(compa_ratio_base_pay - (base_pay_anualized_amt / NULLIF(mid_payrange, 0))) > 0.01
      THEN 1 ELSE 0 END) AS annualized_mismatch_rows,
    SUM(CASE
      WHEN base_pay_amount IS NOT NULL
       AND base_pay_anualized_amt IS NOT NULL
       AND base_pay_amount_currency_code IS NOT NULL
       AND base_pay_anualized_amt_currency_code IS NOT NULL
      THEN 1 ELSE 0 END) AS both_pay_fields_populated_rows,
    SUM(CASE WHEN min_payrange IS NOT NULL AND mid_payrange IS NOT NULL AND max_payrange IS NOT NULL THEN 1 ELSE 0 END) AS complete_range_rows,
    SUM(CASE WHEN mid_payrange IS NULL OR mid_payrange <= 0 THEN 1 ELSE 0 END) AS missing_or_nonpositive_midpoint_rows
  FROM eligible
)
SELECT
  source_rows,
  source_employees,
  ratio_populated_rows,
  ratio_populated_employees,
  amount_comparable_rows,
  amount_comparable_employees,
  annualized_comparable_rows,
  annualized_comparable_employees,
  amount_match_within_001_rows,
  amount_match_after_rounding_rows,
  annualized_match_within_001_rows,
  amount_mismatch_rows,
  annualized_mismatch_rows,
  both_pay_fields_populated_rows,
  complete_range_rows,
  missing_or_nonpositive_midpoint_rows,
  ROUND(100.0 * amount_match_within_001_rows / NULLIF(amount_comparable_rows, 0), 2) AS amount_match_rate_percent,
  ROUND(100.0 * annualized_match_within_001_rows / NULLIF(annualized_comparable_rows, 0), 2) AS annualized_match_rate_percent
FROM metrics
WHERE source_employees >= 30;
