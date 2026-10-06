-- Pregunta: ¿Las dos tablas hrda con "critical" representan el mismo concepto?
-- Regla de aceptacion: la evidencia debe distinguir la estructura de la tabla vigente
-- (familias y segmentos) de la tabla archivada (tecnologia, departamentos y vigencia).
SELECT
  'critical_tech' AS table_name,
  COUNT(*) AS row_count,
  COUNT(DISTINCT extended_job_family) AS category_count,
  COUNT(DISTINCT seg) AS related_value_count,
  SUM(CASE WHEN extended_job_family IS NULL THEN 1 ELSE 0 END) AS null_category_rows,
  MIN(last_modified_date) AS first_observed_date,
  MAX(last_modified_date) AS last_observed_date
FROM hrda.critical_tech

UNION ALL

SELECT
  'critical_tech_archive' AS table_name,
  COUNT(*) AS row_count,
  COUNT(DISTINCT tech) AS category_count,
  COUNT(DISTINCT dept_id) AS related_value_count,
  SUM(CASE WHEN tech IS NULL THEN 1 ELSE 0 END) AS null_category_rows,
  MIN(effective_begin_date) AS first_observed_date,
  MAX(effective_end_date) AS last_observed_date
FROM hrda.critical_tech_archive;
