-- Propósito: localizar campos relacionados con Compensation Grade / PA en
-- job_applications_vw y en fuentes comparables de requisición y empleado.
-- Modo de entrega: presentation; metadatos solamente.

SELECT
  table_schema,
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    LOWER(column_name) LIKE '%compensation%grade%'
    OR LOWER(column_name) LIKE '%grade%pa%'
    OR LOWER(column_name) LIKE '%comp%pa%'
  )
ORDER BY table_name, ordinal_position;
