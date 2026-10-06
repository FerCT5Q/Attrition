SELECT
  c.table_schema,
  c.table_name,
  c.column_name,
  c.data_type,
  c.ordinal_position,
  CASE
    WHEN ((c.table_schema = 'hrda' AND c.table_name = 'critical_tech')) THEN 'requested_table'
    ELSE 'semantic_synonym'
  END AS discovery_reason
FROM information_schema.columns c
WHERE ((c.table_schema = 'hrda' AND c.table_name = 'critical_tech'))
   OR (
      c.table_schema IN ('hrda')
      AND (LOWER(c.column_name) LIKE '%critical%' OR
      LOWER(c.column_name) LIKE '%extended%' OR
      LOWER(c.column_name) LIKE '%families%' OR
      LOWER(c.column_name) LIKE '%family%' OR
      LOWER(c.column_name) LIKE '%tech%')
   )
ORDER BY discovery_reason, c.table_schema, c.table_name, c.ordinal_position
LIMIT 10000
