SELECT
  c.table_schema,
  c.table_name,
  c.column_name,
  c.data_type,
  c.ordinal_position,
  CASE
    WHEN ((c.table_schema = 'hrda' AND c.table_name = 'master_talent_index')) THEN 'requested_table'
    ELSE 'semantic_synonym'
  END AS discovery_reason
FROM information_schema.columns c
WHERE ((c.table_schema = 'hrda' AND c.table_name = 'master_talent_index'))
   OR (
      c.table_schema IN ('hrda')
      AND (LOWER(c.column_name) LIKE '%bonus%' OR
      LOWER(c.column_name) LIKE '%cycle%' OR
      LOWER(c.column_name) LIKE '%eligibility%' OR
      LOWER(c.column_name) LIKE '%empl%' OR
      LOWER(c.column_name) LIKE '%index%' OR
      LOWER(c.column_name) LIKE '%name%' OR
      LOWER(c.column_name) LIKE '%number%' OR
      LOWER(c.column_name) LIKE '%perf%' OR
      LOWER(c.column_name) LIKE '%promo%' OR
      LOWER(c.column_name) LIKE '%quartile%' OR
      LOWER(c.column_name) LIKE '%stock%' OR
      LOWER(c.column_name) LIKE '%talent%')
   )
ORDER BY discovery_reason, c.table_schema, c.table_name, c.ordinal_position
LIMIT 10000
