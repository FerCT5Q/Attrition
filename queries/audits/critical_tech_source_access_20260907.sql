/*
  Critical Tech source access audit.

  Claim:
    The current and archived Critical Tech mapping tables and their required
    columns are accessible in hrda.

  Acceptance rule:
    All required table/column pairs must be present in information_schema.
*/
WITH expected AS (
  SELECT 'hrda' AS table_schema, 'critical_tech' AS table_name,
         'extended_job_family' AS column_name
  UNION ALL SELECT 'hrda', 'critical_tech', 'seg'
  UNION ALL SELECT 'hrda', 'critical_tech', 'last_modified_date'
  UNION ALL SELECT 'hrda', 'critical_tech_archive', 'tech'
  UNION ALL SELECT 'hrda', 'critical_tech_archive', 'effective_begin_date'
  UNION ALL SELECT 'hrda', 'critical_tech_archive', 'effective_end_date'
  UNION ALL SELECT 'hrda', 'critical_tech_archive', 'current_indicator'
),
checked AS (
  SELECT
    e.table_schema,
    e.table_name,
    e.column_name,
    c.column_name IS NOT NULL AS found
  FROM expected e
  LEFT JOIN information_schema.columns c
    ON c.table_schema = e.table_schema
   AND c.table_name = e.table_name
   AND c.column_name = e.column_name
)
SELECT
  COUNT(*) AS required_columns,
  SUM(CASE WHEN found THEN 1 ELSE 0 END) AS found_columns,
  SUM(CASE WHEN NOT found THEN 1 ELSE 0 END) AS missing_columns,
  CASE WHEN SUM(CASE WHEN NOT found THEN 1 ELSE 0 END) = 0
       THEN 'pass' ELSE 'fail' END AS outcome
FROM checked;
