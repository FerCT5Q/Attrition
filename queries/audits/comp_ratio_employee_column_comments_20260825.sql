SELECT
  ns.nspname AS table_schema,
  cls.relname AS table_name,
  att.attname AS column_name,
  pg_catalog.col_description(cls.oid, att.attnum) AS column_comment
FROM pg_catalog.pg_attribute AS att
JOIN pg_catalog.pg_class AS cls
  ON cls.oid = att.attrelid
JOIN pg_catalog.pg_namespace AS ns
  ON ns.oid = cls.relnamespace
WHERE ns.nspname = 'hrda'
  AND cls.relname = 'post_hire_monthly_worker_dtls'
  AND att.attnum > 0
  AND NOT att.attisdropped
  AND att.attname IN (
    'compa_ratio',
    'annual_base_pay',
    'base_pay_rate',
    'total_base_pay_amount',
    'fte_annual_base_pay',
    'base_pay_frequency',
    'fte_annual_base_pay_currency_code',
    'compensation_grade',
    'compensation_grade_profile',
    'cf_ee_rf360_comp_grade',
    'labor_market'
  )
ORDER BY att.attnum;
