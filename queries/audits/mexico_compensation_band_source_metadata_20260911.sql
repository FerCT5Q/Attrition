-- Propósito: inspeccionar metadatos de fuentes internas que contienen
-- min/mid/max pay range o midpoint por grade; sólo metadatos.
-- Modo de entrega: presentation.
SELECT
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('offers', 'offers_new', 'pre_hire_flat_and_wide_summary_mvw', 'flc_20251006', 'fully_loaded_cost')
  AND (
      LOWER(column_name) LIKE '%compensation%'
      OR LOWER(column_name) LIKE '%grade%'
      OR LOWER(column_name) LIKE '%pay%range%'
      OR LOWER(column_name) LIKE '%midpoint%'
      OR LOWER(column_name) LIKE '%salary%'
      OR LOWER(column_name) LIKE '%currency%'
      OR LOWER(column_name) LIKE '%country%'
      OR LOWER(column_name) LIKE '%city%'
      OR LOWER(column_name) LIKE '%location%'
      OR LOWER(column_name) LIKE '%job%title%'
      OR LOWER(column_name) LIKE '%req%'
      OR LOWER(column_name) LIKE '%date%'
  )
ORDER BY table_name, ordinal_position;
