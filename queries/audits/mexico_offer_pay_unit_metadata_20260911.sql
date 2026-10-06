-- Propósito: verificar las columnas de unidad/frecuencia asociadas a
-- min_payrange, mid_payrange y max_payrange; sólo metadatos.
SELECT
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('offers', 'offers_new', 'pre_hire_flat_and_wide_summary_mvw')
  AND (
      LOWER(column_name) LIKE '%pay%'
      OR LOWER(column_name) LIKE '%salary%'
      OR LOWER(column_name) LIKE '%frequency%'
      OR LOWER(column_name) LIKE '%currency%'
  )
ORDER BY table_name, ordinal_position;
