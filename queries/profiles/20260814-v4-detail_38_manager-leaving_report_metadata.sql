SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN ('manager_employee_id', 'employee_id', 'is_termed', 'term_date', 'term_type')
ORDER BY ordinal_position
