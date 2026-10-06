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
  AND cols.table_name IN (
    'fully_loaded_cost',
    'flc_20251006',
    'flc_bkp_20251104'
  )
ORDER BY cols.table_name, cols.ordinal_position;
