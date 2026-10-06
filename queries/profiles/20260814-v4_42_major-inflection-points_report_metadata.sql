SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN ('manager_change', 'manager_change_date', 'cost_center_change', 'cost_center_change_date', 'job_family_change', 'job_family_change_date', 'location_change', 'location_change_date', 'is_transferred', 'transfer_date')
ORDER BY ordinal_position
