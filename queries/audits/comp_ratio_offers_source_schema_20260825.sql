SELECT
  cols.table_schema,
  cols.table_name,
  tabs.table_type,
  cols.ordinal_position,
  cols.column_name,
  cols.data_type,
  cols.numeric_precision,
  cols.numeric_scale,
  cols.is_nullable
FROM information_schema.columns AS cols
LEFT JOIN information_schema.tables AS tabs
  ON tabs.table_schema = cols.table_schema
 AND tabs.table_name = cols.table_name
WHERE cols.table_schema = 'hrda'
  AND cols.table_name = 'offers'
  AND (
    LOWER(cols.column_name) IN (
      'employee_id',
      'candidate_id',
      'offer_id',
      'base_pay_anualized_amt',
      'base_pay_anualized_amt_currency_code',
      'compa_ratio_base_pay',
      'min_payrange',
      'mid_payrange',
      'max_payrange',
      'compensation_grade',
      'job_code',
      'job_code_current',
      'offer_accept_date',
      'hire_date',
      'last_updated_date',
      'latest_offer_approved_date',
      'final_offer_approved_date',
      'effective_date'
    )
    OR LOWER(cols.column_name) LIKE '%payrange%'
    OR LOWER(cols.column_name) LIKE '%compa%'
    OR LOWER(cols.column_name) LIKE '%base_pay%'
  )
ORDER BY cols.ordinal_position;
