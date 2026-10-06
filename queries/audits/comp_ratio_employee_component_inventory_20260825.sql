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
  AND cols.table_name = 'post_hire_monthly_worker_dtls'
  AND (
    LOWER(cols.column_name) LIKE '%pay%'
    OR LOWER(cols.column_name) LIKE '%salary%'
    OR LOWER(cols.column_name) LIKE '%wage%'
    OR LOWER(cols.column_name) LIKE '%comp%'
    OR LOWER(cols.column_name) LIKE '%rate%'
    OR LOWER(cols.column_name) LIKE '%market%'
    OR LOWER(cols.column_name) LIKE '%mid%'
    OR LOWER(cols.column_name) LIKE '%range%'
    OR LOWER(cols.column_name) LIKE '%grade%'
    OR LOWER(cols.column_name) LIKE '%fte%'
    OR LOWER(cols.column_name) LIKE '%hour%'
    OR LOWER(cols.column_name) LIKE '%currency%'
  )
ORDER BY cols.ordinal_position;
