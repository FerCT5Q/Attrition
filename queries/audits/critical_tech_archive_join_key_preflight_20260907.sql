/*
  Preflight del join histórico Critical Tech.

  Claim:
    El archive debe tener una llave común y gobernada con el catálogo vigente
    antes de reconstruir membership histórica por family.

  Regla de aceptación:
    Debe existir una columna de family común, o un crosswalk autoritativo
    explícito, y la llave debe poder reconciliarse en forma agregada. La
    presencia de tech/dept_id por sí sola no prueba equivalencia con
    extended_job_family.

  Privacidad:
    Sólo se devuelve metadata y conteos agregados; no se devuelven valores de
    empleados ni filas de catálogo.
*/
WITH archive_columns AS (
  SELECT
    COUNT(CASE WHEN column_name = 'extended_job_family' THEN 1 END) AS archive_has_extended_job_family,
    COUNT(CASE WHEN column_name = 'dept_id' THEN 1 END) AS archive_has_dept_id,
    COUNT(CASE WHEN column_name = 'tech' THEN 1 END) AS archive_has_tech,
    COUNT(*) AS archive_column_count
  FROM information_schema.columns
  WHERE table_schema = 'hrda'
    AND table_name = 'critical_tech_archive'
),
current_columns AS (
  SELECT
    COUNT(CASE WHEN column_name = 'extended_job_family' THEN 1 END) AS current_has_extended_job_family,
    COUNT(CASE WHEN column_name = 'seg' THEN 1 END) AS current_has_seg
  FROM information_schema.columns
  WHERE table_schema = 'hrda'
    AND table_name = 'critical_tech'
)
SELECT
  a.archive_column_count,
  a.archive_has_extended_job_family,
  a.archive_has_dept_id,
  a.archive_has_tech,
  c.current_has_extended_job_family,
  c.current_has_seg,
  CASE
    WHEN a.archive_has_extended_job_family = 1
      AND c.current_has_extended_job_family = 1
      THEN 'review_aggregate_reconciliation'
    ELSE 'blocked_missing_common_family_key'
  END AS historical_join_outcome
FROM archive_columns a
CROSS JOIN current_columns c;
