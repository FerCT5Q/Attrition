SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN ('job_family', 'job_family_group', 'job_family_short', 'job_family_group_short')
ORDER BY ordinal_position
