WITH target_managers AS (
  SELECT DISTINCT CAST(manager_employee_id AS BIGINT) AS manager_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND manager_employee_id IS NOT NULL
), term_rows AS (
  SELECT
    t.is_termed,
    t.term_date,
    t.fis_mo_end_dt
  FROM hrda.post_hire_monthly_worker_dtls_term t
  INNER JOIN target_managers tm
    ON tm.manager_id = t.employee_id
)
SELECT
  'Manager leaving' AS variable_name,
  COUNT(*) AS term_table_rows_checked,
  SUM(CASE WHEN COALESCE(is_termed, 0) = 1 THEN 1 ELSE 0 END) AS positive_flag_rows,
  SUM(CASE WHEN term_date IS NOT NULL THEN 1 ELSE 0 END) AS populated_term_date_rows,
  SUM(CASE WHEN COALESCE(is_termed, 0) = 1 AND term_date IS NOT NULL THEN 1 ELSE 0 END) AS usable_event_rows,
  SUM(CASE WHEN COALESCE(is_termed, 0) = 1 AND term_date IS NULL THEN 1 ELSE 0 END) AS flagged_without_date_rows,
  SUM(CASE WHEN term_date IS NOT NULL AND term_date > fis_mo_end_dt THEN 1 ELSE 0 END) AS future_dated_rows
FROM term_rows;

