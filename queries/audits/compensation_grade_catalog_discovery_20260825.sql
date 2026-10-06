-- Descubrimiento de posibles catalogos o mappings para Compensation grade.
-- Solo consulta metadatos de tablas y columnas; no devuelve filas de empleados.
SELECT
    c.table_schema,
    c.table_name,
    t.table_type,
    c.column_name,
    c.data_type
FROM information_schema.columns AS c
LEFT JOIN information_schema.tables AS t
  ON t.table_schema = c.table_schema
 AND t.table_name = c.table_name
WHERE c.table_schema = 'hrda'
  AND (
      LOWER(c.table_name) LIKE '%grade%'
      OR LOWER(c.table_name) LIKE '%level%'
      OR LOWER(c.table_name) LIKE '%comp%'
      OR LOWER(c.column_name) LIKE '%grade%'
      OR LOWER(c.column_name) LIKE '%level%'
      OR LOWER(c.column_name) LIKE '%comp%'
  )
ORDER BY c.table_name, c.ordinal_position;
