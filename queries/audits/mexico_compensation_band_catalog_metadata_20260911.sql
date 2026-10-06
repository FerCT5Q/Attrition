-- Propósito: localizar catálogos internos de bandas, midpoint o límites
-- salariales por grade; sólo metadatos.
-- Modo de entrega: presentation.
SELECT
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
      LOWER(column_name) LIKE '%salary%'
      OR LOWER(column_name) LIKE '%pay%range%'
      OR LOWER(column_name) LIKE '%pay%band%'
      OR LOWER(column_name) LIKE '%compensation%range%'
      OR LOWER(column_name) LIKE '%compensation%band%'
      OR LOWER(column_name) LIKE '%midpoint%'
      OR LOWER(column_name) LIKE '%market%reference%'
      OR LOWER(column_name) LIKE '%grade%profile%'
      OR LOWER(column_name) LIKE '%compensation%grade%'
  )
ORDER BY table_name, ordinal_position;
