-- Propósito: comprobar si Talent Index tiene una fecha/versionado que permita
-- atribuir cada valor al snapshot laboral de agosto de 2025.
-- Modo de entrega: presentation. Sólo metadata; no devuelve datos de empleados.
SELECT
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('master_talent_index', 'post_hire_monthly_worker_dtls')
ORDER BY table_name, ordinal_position;
