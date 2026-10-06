-- Pregunta: ¿Que columnas de la tabla mensual pueden representar una familia o agrupacion de trabajo?
-- Regla de aceptacion: identificar las columnas candidatas por metadata antes de probar cualquier join.
SELECT
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND (
    column_name ILIKE '%job_family%'
    OR column_name ILIKE '%critical%'
    OR column_name ILIKE '%tech%'
  )
ORDER BY ordinal_position;
