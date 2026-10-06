/*
  Descubrimiento de posibles fuentes de vacantes/requisiciones.
  Entregable: internal_analysis exploratorio.
  Sólo metadata; no lee filas de empleados.
*/
WITH candidate_objects AS (
    SELECT DISTINCT
        table_schema,
        table_name
    FROM information_schema.columns
    WHERE table_schema = 'hrda'
      AND (
          table_name ILIKE '%req%'
          OR table_name ILIKE '%vacan%'
          OR table_name ILIKE '%open%'
          OR table_name ILIKE '%posit%'
          OR table_name ILIKE '%post%'
          OR table_name ILIKE '%pre_hire%'
          OR column_name ILIKE '%req%'
          OR column_name ILIKE '%vacan%'
          OR column_name ILIKE '%open%'
          OR column_name ILIKE '%posit%'
          OR column_name ILIKE '%post%'
          OR column_name ILIKE '%job%id%'
      )
)
SELECT
    c.table_schema,
    c.table_name,
    COUNT(*) AS matching_column_count,
    MIN(ic.ordinal_position) AS first_matching_column_position
FROM candidate_objects c
JOIN information_schema.columns ic
  ON ic.table_schema = c.table_schema
 AND ic.table_name = c.table_name
GROUP BY 1, 2
ORDER BY matching_column_count DESC, c.table_name;
