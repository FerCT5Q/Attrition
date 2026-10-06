SELECT
  cols.table_schema,
  cols.table_name,
  tabs.table_type,
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
  AND (
    LOWER(cols.column_name) IN (
      'compa_ratio',
      'compensation_ratio',
      'current_compa_ratio',
      'new_compa_ratio',
      'base_pay_amount',
      'base_pay',
      'base_pay_current',
      'base_pay_proposed',
      'mid_payrange',
      'midpoint',
      'mid_point'
    )
    OR LOWER(cols.column_name) LIKE '%midpoint%'
    OR LOWER(cols.column_name) LIKE '%payrange%'
    OR LOWER(cols.column_name) LIKE '%compa%'
  )
ORDER BY cols.table_name, cols.ordinal_position;
