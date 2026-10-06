-- Metadatos de origen de Compensation grade y de su grain temporal.
-- No devuelve datos de empleados.
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN (
      'compensation_grade',
      'fis_mo_end_dt',
      'fiscal_year',
      'employee_id',
      'worker_type',
      'employee_type',
      'active_status'
  )
ORDER BY ordinal_position;
