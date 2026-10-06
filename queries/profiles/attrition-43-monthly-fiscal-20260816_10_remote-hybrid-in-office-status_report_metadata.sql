SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN ('work_arrangement', 'work_arrangement_start_date', 'work_arrangement_end_date')
ORDER BY ordinal_position
