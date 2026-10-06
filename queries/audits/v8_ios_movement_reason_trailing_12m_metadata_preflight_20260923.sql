/*
  Preflight de metadatos para la visual V8 de motivos IOS trailing 12 months.
  No consulta registros de empleados ni resultados de la variable.
*/
SELECT
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    (table_name = 'workers_ios_transfers' AND column_name IN ('employee_id', 'effective_date', 'business_process_reason'))
    OR (table_name = 'post_hire_monthly_worker_dtls' AND column_name IN ('employee_id', 'fis_mo_end_dt', 'worker_type', 'employee_type', 'active_status'))
    OR (table_name = 'all_terminations' AND column_name IN ('employeeid', 'term_date', 'term_type'))
  )
ORDER BY table_name, ordinal_position;
