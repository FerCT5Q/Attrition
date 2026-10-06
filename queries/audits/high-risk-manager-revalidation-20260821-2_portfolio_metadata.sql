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
      AND (LOWER(c.column_name) LIKE '%active%' OR
      LOWER(c.column_name) LIKE '%family%' OR
      LOWER(c.column_name) LIKE '%fiscal%' OR
      LOWER(c.column_name) LIKE '%group%' OR
      LOWER(c.column_name) LIKE '%grouped%' OR
      LOWER(c.column_name) LIKE '%high%' OR
      LOWER(c.column_name) LIKE '%hire%' OR
      LOWER(c.column_name) LIKE '%level%' OR
      LOWER(c.column_name) LIKE '%original%' OR
      LOWER(c.column_name) LIKE '%position%' OR
      LOWER(c.column_name) LIKE '%primary%' OR
      LOWER(c.column_name) LIKE '%region%' OR
      LOWER(c.column_name) LIKE '%rehire%' OR
      LOWER(c.column_name) LIKE '%risk%' OR
      LOWER(c.column_name) LIKE '%service%' OR
      LOWER(c.column_name) LIKE '%term%' OR
      LOWER(c.column_name) LIKE '%termed%' OR
      LOWER(c.column_name) LIKE '%type%' OR
      LOWER(c.column_name) LIKE '%worker%' OR
      LOWER(c.column_name) LIKE '%year%')
   )
ORDER BY discovery_reason, c.table_schema, c.table_name, c.ordinal_position
LIMIT 10000
