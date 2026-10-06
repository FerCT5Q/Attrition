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
    'pre_hire_flat_and_wide_summary_mvw',
    'post_hire_monthly_worker_dtls',
    'worker_details_latest',
    'worker_snapshot_vw'
  )
ORDER BY cols.table_name, cols.ordinal_position;
