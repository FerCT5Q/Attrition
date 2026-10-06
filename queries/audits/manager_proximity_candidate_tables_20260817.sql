-- Metadata-only shortlist for manager-proximity sources.
-- This intentionally returns table and column names, never employee values.

WITH candidate_tables AS (
  SELECT
    table_schema,
    table_name,
    table_type
  FROM information_schema.tables
  WHERE table_schema = 'hrda'
    AND (
      LOWER(table_name) LIKE '%location%'
      OR LOWER(table_name) LIKE '%site%'
      OR LOWER(table_name) LIKE '%geo%'
      OR LOWER(table_name) LIKE '%facility%'
      OR LOWER(table_name) LIKE '%workplace%'
      OR LOWER(table_name) LIKE '%travel%'
      OR LOWER(table_name) LIKE '%distance%'
      OR LOWER(table_name) LIKE '%timezone%'
      OR LOWER(table_name) LIKE '%time_zone%'
    )
),
coordinate_tables AS (
  SELECT DISTINCT
    table_schema,
    table_name,
    CAST(NULL AS VARCHAR(32)) AS table_type
  FROM information_schema.columns
  WHERE table_schema = 'hrda'
    AND (
      LOWER(column_name) LIKE '%latitude%'
      OR LOWER(column_name) LIKE '%longitude%'
      OR LOWER(column_name) LIKE '%time_zone%'
      OR LOWER(column_name) LIKE '%timezone%'
    )
),
all_candidates AS (
  SELECT table_schema, table_name, table_type FROM candidate_tables
  UNION
  SELECT table_schema, table_name, table_type FROM coordinate_tables
)
SELECT
  c.table_name,
  COALESCE(c.table_type, t.table_type) AS table_type,
  col.column_name,
  col.data_type
FROM all_candidates c
JOIN information_schema.columns col
  ON col.table_schema = c.table_schema
 AND col.table_name = c.table_name
LEFT JOIN information_schema.tables t
  ON t.table_schema = c.table_schema
 AND t.table_name = c.table_name
WHERE (
  LOWER(col.column_name) LIKE '%office%'
  OR LOWER(col.column_name) LIKE '%site%'
  OR LOWER(col.column_name) LIKE '%location%'
  OR LOWER(col.column_name) LIKE '%postal%'
  OR LOWER(col.column_name) LIKE '%zip%'
  OR LOWER(col.column_name) LIKE '%latitude%'
  OR LOWER(col.column_name) LIKE '%longitude%'
  OR LOWER(col.column_name) LIKE '%geocode%'
  OR LOWER(col.column_name) LIKE '%time_zone%'
  OR LOWER(col.column_name) LIKE '%timezone%'
  OR LOWER(col.column_name) LIKE '%travel%'
  OR LOWER(col.column_name) LIKE '%commute%'
  OR LOWER(col.column_name) LIKE '%distance%'
  OR LOWER(col.column_name) LIKE '%employee%'
  OR LOWER(col.column_name) LIKE '%effective%'
  OR LOWER(col.column_name) LIKE '%snapshot%'
)
ORDER BY c.table_name, col.column_name;
