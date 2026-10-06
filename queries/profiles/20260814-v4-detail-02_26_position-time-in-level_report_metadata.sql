SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN ('levelentrydate', 'time_in_role', 'time_in_job_profile_start_date')
ORDER BY ordinal_position
