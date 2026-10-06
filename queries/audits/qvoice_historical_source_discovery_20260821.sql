WITH candidate_tables AS (
  SELECT DISTINCT
    table_schema,
    table_name
  FROM information_schema.tables
  WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
    AND (
      LOWER(table_name) LIKE '%qvoice%'
      OR LOWER(table_name) LIKE '%voice%'
      OR LOWER(table_name) LIKE '%qualtrics%'
      OR LOWER(table_name) LIKE '%survey%'
      OR LOWER(table_name) LIKE '%engagement%'
      OR LOWER(table_name) LIKE '%experience%'
      OR LOWER(table_name) LIKE '%pulse%'
    )
  UNION
  SELECT DISTINCT
    table_schema,
    table_name
  FROM information_schema.columns
  WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
    AND (
      LOWER(column_name) LIKE '%qvoice%'
      OR LOWER(column_name) LIKE '%voice%'
      OR LOWER(column_name) LIKE '%qualtrics%'
      OR LOWER(column_name) LIKE '%survey%'
      OR LOWER(column_name) LIKE '%engagement%'
      OR LOWER(column_name) LIKE '%experience%'
      OR LOWER(column_name) LIKE '%pulse%'
    )
),
candidate_column_summary AS (
  SELECT
    candidate_tables.table_schema,
    candidate_tables.table_name,
    COUNT(columns.column_name) AS total_column_count,
    SUM(CASE
      WHEN LOWER(columns.column_name) LIKE '%qvoice%'
        OR LOWER(columns.column_name) LIKE '%voice%'
        OR LOWER(columns.column_name) LIKE '%qualtrics%'
        OR LOWER(columns.column_name) LIKE '%survey%'
        OR LOWER(columns.column_name) LIKE '%engagement%'
        OR LOWER(columns.column_name) LIKE '%experience%'
        OR LOWER(columns.column_name) LIKE '%pulse%'
      THEN 1 ELSE 0 END) AS matching_column_count,
    SUM(CASE
      WHEN LOWER(columns.column_name) LIKE '%date%'
        OR LOWER(columns.column_name) LIKE '%year%'
        OR LOWER(columns.column_name) LIKE '%period%'
        OR LOWER(columns.column_name) LIKE '%wave%'
      THEN 1 ELSE 0 END) AS date_like_column_count,
    MAX(CASE WHEN LOWER(columns.column_name) = 'emp_id' THEN 1 ELSE 0 END) AS has_emp_id,
    MAX(CASE WHEN LOWER(columns.column_name) = 'employee_id' THEN 1 ELSE 0 END) AS has_employee_id,
    MAX(CASE WHEN LOWER(columns.column_name) LIKE '%survey_launch_date%' THEN 1 ELSE 0 END) AS has_survey_launch_date
  FROM candidate_tables
  LEFT JOIN information_schema.columns columns
    ON candidate_tables.table_schema = columns.table_schema
   AND candidate_tables.table_name = columns.table_name
  GROUP BY 1, 2
)
SELECT
  table_schema,
  table_name,
  total_column_count,
  matching_column_count,
  date_like_column_count,
  has_emp_id,
  has_employee_id,
  has_survey_launch_date
FROM candidate_column_summary
ORDER BY
  CASE WHEN LOWER(table_name) LIKE '%qvoice%' THEN 0 ELSE 1 END,
  table_schema,
  table_name
