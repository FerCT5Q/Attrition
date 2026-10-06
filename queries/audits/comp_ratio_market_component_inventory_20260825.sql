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
      'midpoint',
      'midpoint_usd',
      'mid_payrange',
      'min_payrange',
      'max_payrange',
      'market_rate',
      'market_midpoint',
      'salary_range',
      'salary_range_midpoint',
      'pay_range',
      'pay_range_midpoint'
    )
    OR LOWER(cols.column_name) LIKE '%payrange%'
    OR LOWER(cols.column_name) LIKE '%midpoint%'
    OR LOWER(cols.column_name) LIKE '%market_rate%'
    OR LOWER(cols.column_name) LIKE '%market_mid%'
    OR LOWER(cols.column_name) LIKE '%salary_range%'
    OR LOWER(cols.column_name) LIKE '%pay_range%'
  )
ORDER BY cols.table_name, cols.ordinal_position;
