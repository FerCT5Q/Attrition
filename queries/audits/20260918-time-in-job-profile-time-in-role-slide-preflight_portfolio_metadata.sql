SELECT
  c.table_schema,
  c.table_name,
  c.column_name,
  c.data_type,
  c.ordinal_position,
  CASE
    WHEN ((c.table_schema = 'hrda' AND c.table_name = 'post_hire_monthly_worker_dtls')) THEN 'requested_table'
    ELSE 'semantic_synonym'
  END AS discovery_reason
FROM information_schema.columns c
WHERE ((c.table_schema = 'hrda' AND c.table_name = 'post_hire_monthly_worker_dtls'))
   OR (
      c.table_schema IN ('hrda')
      AND (LOWER(c.column_name) LIKE '%level%' OR
      LOWER(c.column_name) LIKE '%levelentrydate%' OR
      LOWER(c.column_name) LIKE '%position%' OR
      LOWER(c.column_name) LIKE '%profile%' OR
      LOWER(c.column_name) LIKE '%role%' OR
      LOWER(c.column_name) LIKE '%start%' OR
      LOWER(c.column_name) LIKE '%time%')
   )
ORDER BY discovery_reason, c.table_schema, c.table_name, c.ordinal_position
LIMIT 10000
