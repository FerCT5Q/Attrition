SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN ('is_rehire', 'rehire_date', 'original_hire_date', 'max_hire_rehire_date', 'job_family', 'job_level_primary_position')
ORDER BY ordinal_position
