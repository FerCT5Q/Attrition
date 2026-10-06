-- Propósito: inventario de tablas y vistas de reclutamiento/vacantes.
-- Modo de entrega: presentation. Sólo devuelve metadatos.

SELECT
  table_schema,
  table_name,
  table_type
FROM information_schema.tables
WHERE table_schema = 'hrda'
  AND (
    LOWER(table_name) LIKE '%requisition%'
    OR LOWER(table_name) LIKE '%vacan%'
    OR LOWER(table_name) LIKE '%posting%'
    OR LOWER(table_name) LIKE '%job%'
    OR LOWER(table_name) LIKE '%applicat%'
    OR LOWER(table_name) LIKE '%candidate%'
    OR LOWER(table_name) LIKE '%recruit%'
  )
ORDER BY table_name;
