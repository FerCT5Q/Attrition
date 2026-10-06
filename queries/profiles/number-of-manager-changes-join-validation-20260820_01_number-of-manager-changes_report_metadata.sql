SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN ('employee_id', 'fis_mo_beg_dt', 'fis_mo_end_dt', 'worker_type', 'employee_type', 'active_status', 'manager_change', 'manager_change_date')
ORDER BY ordinal_position
