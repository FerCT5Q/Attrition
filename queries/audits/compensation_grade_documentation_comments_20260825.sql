-- Busca comentarios oficiales de tabla/columna para Compensation grade y
-- campos de nivel relacionados.
-- No devuelve filas de empleados.
SELECT
    n.nspname AS table_schema,
    c.relname AS table_name,
    a.attname AS column_name,
    d.description
FROM pg_catalog.pg_description AS d
JOIN pg_catalog.pg_attribute AS a
  ON a.attrelid = d.objoid
 AND a.attnum = d.objsubid
JOIN pg_catalog.pg_class AS c
  ON c.oid = d.objoid
JOIN pg_catalog.pg_namespace AS n
  ON n.oid = c.relnamespace
WHERE n.nspname = 'hrda'
  AND c.relname IN (
      'post_hire_monthly_worker_dtls',
      'compgrade_benefitsusd_mapping',
      'annual_review_report'
  )
  AND LOWER(a.attname) IN (
      'compensation_grade',
      'compensation_grade_profile',
      'grade',
      'grade_profile',
      'job_level',
      'job_level_primary_position',
      'level_grouped',
      'management_level'
  )
ORDER BY table_name, column_name;
