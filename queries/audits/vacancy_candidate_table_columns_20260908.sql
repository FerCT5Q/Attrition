/*
  Columnas de las dos candidatas iniciales.
  Entregable: internal_analysis exploratorio.
  Sólo metadata; no lee filas de empleados.
*/
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('pre_hire_flat_and_wide_summary_mvw', 'req_hire_type_mapping')
ORDER BY table_name, ordinal_position;
