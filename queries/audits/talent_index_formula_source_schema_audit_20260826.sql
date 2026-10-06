-- Talent index: tipos de las columnas usadas en la reconciliacion.
-- Resultado agregado de metadata; no devuelve datos de empleados.

SELECT
  column_name,
  data_type,
  numeric_precision,
  numeric_scale,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'master_talent_index'
  AND column_name IN ('empl_id', 'cycle_number', 'stock', 'perf', 'talent_index')
ORDER BY ordinal_position;
