WITH voice_tables AS (
  SELECT
    table_schema,
    table_name
  FROM information_schema.tables
  WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
    AND (
      LOWER(table_name) LIKE '%voice%'
      OR LOWER(table_name) LIKE '%qvoice%'
      OR LOWER(table_name) LIKE '%wvoice%'
      OR LOWER(table_name) LIKE '%workvoice%'
    )
),
table_counts AS (
  SELECT
    COUNT(*) AS voice_table_count,
    SUM(CASE WHEN LOWER(table_name) LIKE '%qvoice%' THEN 1 ELSE 0 END) AS qvoice_table_count,
    SUM(CASE WHEN LOWER(table_name) LIKE '%wvoice%' THEN 1 ELSE 0 END) AS wvoice_table_count,
    SUM(CASE WHEN LOWER(table_name) LIKE '%workvoice%' THEN 1 ELSE 0 END) AS workvoice_table_count
  FROM voice_tables
)
SELECT
  'voice_table_counts_all_schemas' AS section,
  'accessible_non_catalog_schemas' AS scope,
  voice_table_count AS metric_1,
  qvoice_table_count AS metric_2,
  wvoice_table_count AS metric_3,
  workvoice_table_count AS metric_4,
  NULL::BIGINT AS metric_5,
  'metric_1=voice-like tables, metric_2=qvoice tables, metric_3=wvoice tables, metric_4=workvoice tables' AS notes
FROM table_counts
UNION ALL
SELECT
  'voice_table_name' AS section,
  table_schema || '.' || table_name AS scope,
  CASE WHEN LOWER(table_name) LIKE '%qvoice%' THEN 1 ELSE 0 END AS metric_1,
  CASE WHEN LOWER(table_name) LIKE '%wvoice%' THEN 1 ELSE 0 END AS metric_2,
  CASE WHEN LOWER(table_name) LIKE '%workvoice%' THEN 1 ELSE 0 END AS metric_3,
  NULL::BIGINT AS metric_4,
  NULL::BIGINT AS metric_5,
  'metric_1=qvoice flag, metric_2=wvoice flag, metric_3=workvoice flag' AS notes
FROM voice_tables
ORDER BY section, scope
