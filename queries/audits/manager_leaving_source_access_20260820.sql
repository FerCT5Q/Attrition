WITH required AS (
  SELECT 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS required_column
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'manager_employee_id'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'manager_effective_date'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'fis_mo_beg_dt'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'fis_mo_end_dt'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'worker_type'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'employee_type'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'active_status'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'is_termed'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'term_date'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'term_type'
  UNION ALL SELECT 'hrda', 'post_hire_monthly_worker_dtls', 'max_hire_rehire_date'
  UNION ALL SELECT 'hrda', 'all_terminations', 'employeeid'
  UNION ALL SELECT 'hrda', 'all_terminations', 'term_date'
  UNION ALL SELECT 'hrda', 'all_terminations', 'term_type'
), checked AS (
  SELECT
    r.table_schema,
    r.table_name,
    r.required_column,
    CASE WHEN t.table_name IS NOT NULL THEN 1 ELSE 0 END AS table_exists,
    CASE WHEN c.column_name IS NOT NULL THEN 1 ELSE 0 END AS column_exists
  FROM required r
  LEFT JOIN information_schema.tables t
    ON t.table_schema = r.table_schema
   AND t.table_name = r.table_name
  LEFT JOIN information_schema.columns c
    ON c.table_schema = r.table_schema
   AND c.table_name = r.table_name
   AND c.column_name = r.required_column
)
SELECT
  'Manager leaving' AS variable_name,
  COUNT(*) AS required_items,
  SUM(table_exists) AS table_items_found,
  SUM(column_exists) AS column_items_found,
  SUM(CASE WHEN table_exists = 0 OR column_exists = 0 THEN 1 ELSE 0 END) AS missing_items
FROM checked;

