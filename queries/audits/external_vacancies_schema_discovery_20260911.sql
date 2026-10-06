-- Propósito: localizar activos tabulares que podrían describir vacantes o
-- reclutamiento externo. Sólo inspecciona metadatos; no recupera filas.
-- Modo de entrega: presentation.
-- Regla de aceptación: una tabla candidata debe tener al menos una columna
-- relacionada con requisición, publicación, candidato externo o título de puesto.

SELECT
  table_schema,
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
  AND (
    LOWER(table_name) LIKE '%recruit%'
    OR LOWER(table_name) LIKE '%requisition%'
    OR LOWER(table_name) LIKE '%vacan%'
    OR LOWER(table_name) LIKE '%posting%'
    OR LOWER(table_name) LIKE '%candidate%'
    OR LOWER(table_name) LIKE '%applicant%'
    OR LOWER(table_name) LIKE '%pre_hire%'
    OR LOWER(column_name) LIKE '%requisition%'
    OR LOWER(column_name) LIKE '%posting%'
    OR LOWER(column_name) LIKE '%external%'
    OR LOWER(column_name) LIKE '%applicant%'
    OR LOWER(column_name) LIKE '%candidate%'
    OR LOWER(column_name) IN (
      'job_title', 'job_name', 'job_posting_title', 'position_title',
      'recruiting_type', 'recruitment_type', 'hire_type'
    )
  )
ORDER BY table_schema, table_name, ordinal_position;
