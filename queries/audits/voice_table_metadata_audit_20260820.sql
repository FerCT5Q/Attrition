WITH voice_tables AS (
  SELECT
    table_schema,
    table_name
  FROM information_schema.tables
  WHERE table_schema = 'hrda'
    AND (
      LOWER(table_name) LIKE '%voice%'
      OR LOWER(table_name) LIKE '%qvoice%'
      OR LOWER(table_name) LIKE '%wvoice%'
    )
),
qvoice_columns AS (
  SELECT
    column_name
  FROM information_schema.columns
  WHERE table_schema = 'hrda'
    AND table_name = 'qvoice_survey_data'
),
comment_columns AS (
  SELECT
    COUNT(*) AS comment_column_count
  FROM qvoice_columns
  WHERE LOWER(column_name) LIKE '%comment%'
    OR LOWER(column_name) LIKE '%text%'
    OR LOWER(column_name) LIKE '%verbatim%'
),
table_counts AS (
  SELECT
    COUNT(*) AS voice_table_count,
    SUM(CASE WHEN LOWER(table_name) LIKE '%qvoice%' THEN 1 ELSE 0 END) AS qvoice_table_count,
    SUM(CASE WHEN LOWER(table_name) LIKE '%wvoice%' THEN 1 ELSE 0 END) AS wvoice_table_count
  FROM voice_tables
)
SELECT
  'voice_table_counts' AS section,
  'hrda' AS scope,
  voice_table_count AS metric_1,
  qvoice_table_count AS metric_2,
  wvoice_table_count AS metric_3,
  NULL::BIGINT AS metric_4,
  NULL::BIGINT AS metric_5,
  NULL::VARCHAR(256) AS notes
FROM table_counts
UNION ALL
SELECT
  'voice_table_name' AS section,
  table_schema || '.' || table_name AS scope,
  NULL::BIGINT AS metric_1,
  NULL::BIGINT AS metric_2,
  NULL::BIGINT AS metric_3,
  NULL::BIGINT AS metric_4,
  NULL::BIGINT AS metric_5,
  'voice-like table present in information_schema' AS notes
FROM voice_tables
UNION ALL
SELECT
  'qvoice_comment_column_metadata' AS section,
  'hrda.qvoice_survey_data' AS scope,
  comment_column_count AS metric_1,
  NULL::BIGINT AS metric_2,
  NULL::BIGINT AS metric_3,
  NULL::BIGINT AS metric_4,
  NULL::BIGINT AS metric_5,
  'metric_1=comment/text/verbatim column count, no comment values returned' AS notes
FROM comment_columns
ORDER BY section, scope
