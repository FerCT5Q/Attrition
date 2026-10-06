-- Claim: all technical components for the candidate's read-only derivation exist.
-- Output is metadata-only and aggregate-only.
WITH required_items AS (
  SELECT 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS column_name
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'manager_employee_id'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'fis_mo_end_dt'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'fiscal_year'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'worker_type'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'employee_type'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'active_status'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'term_date'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'term_type'
  UNION ALL SELECT 'hrda', 'all_terminations', 'employeeid'
  UNION ALL SELECT 'hrda', 'all_terminations', 'term_date'
  UNION ALL SELECT 'hrda', 'all_terminations', 'term_type'
), available_items AS (
  SELECT table_schema, table_name, column_name
  FROM information_schema.columns
  WHERE table_schema = 'hrda'
    AND table_name IN ('post_hire_monthly_worker_dtls', 'all_terminations')
)
SELECT
  COUNT(*)::BIGINT AS required_items,
  SUM(CASE WHEN a.column_name IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS found_items,
  SUM(CASE WHEN a.column_name IS NULL THEN 1 ELSE 0 END)::BIGINT AS missing_items
FROM required_items AS r
LEFT JOIN available_items AS a
  ON a.table_schema = r.table_schema
 AND a.table_name = r.table_name
 AND a.column_name = r.column_name;
