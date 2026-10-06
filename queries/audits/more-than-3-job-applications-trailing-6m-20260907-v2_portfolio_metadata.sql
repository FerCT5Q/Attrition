SELECT
  c.table_schema,
  c.table_name,
  c.column_name,
  c.data_type,
  c.ordinal_position,
  CASE
    WHEN ((c.table_schema = 'hrda' AND c.table_name = 'applications')) THEN 'requested_table'
    ELSE 'semantic_synonym'
  END AS discovery_reason
FROM information_schema.columns c
WHERE ((c.table_schema = 'hrda' AND c.table_name = 'applications'))
   OR (
      c.table_schema IN ('hrda')
      AND (LOWER(c.column_name) LIKE '%application%' OR
      LOWER(c.column_name) LIKE '%applications%' OR
      LOWER(c.column_name) LIKE '%applied%' OR
      LOWER(c.column_name) LIKE '%cand%' OR
      LOWER(c.column_name) LIKE '%candidate%' OR
      LOWER(c.column_name) LIKE '%more%')
   )
ORDER BY discovery_reason, c.table_schema, c.table_name, c.ordinal_position
LIMIT 10000
