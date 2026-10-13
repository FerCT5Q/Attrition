/*
  BU L3: disponibilidad de la fuente y columnas del mapping.
  Sólo devuelve metadatos agregados; no contiene filas de empleados.
*/
SELECT
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('d_department', 'post_hire_monthly_worker_dtls')
  AND (
    (table_name = 'd_department' AND column_name IN (
      'nk_dept_id', 'ude_bu_reporting_l3', 'edw_effective_dt',
      'edw_end_dt', 'edw_cur_indicator'
    ))
    OR (table_name = 'post_hire_monthly_worker_dtls'
      AND column_name IN ('employee_id', 'cost_centerid', 'fis_mo_end_dt'))
  )
ORDER BY table_name, ordinal_position;
