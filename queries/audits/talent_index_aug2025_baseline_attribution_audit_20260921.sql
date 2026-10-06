-- Propósito: verificar si los registros actualmente recuperables de Talent
-- Index pueden atribuirse de forma time-safe al cohort de 2025-08-24.
-- Regla de aceptación: se requiere una fecha efectiva/de ciclo de negocio o
-- un snapshot histórico que vincule inequívocamente el valor con el baseline.
-- Modo: presentation; sólo resultados agregados.
WITH august_2025_cohort AS (
  SELECT DISTINCT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt = DATE '2025-08-24'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND COALESCE(is_rf360_yes_no, 0) = 0
),
cohort_join AS (
  SELECT
    COUNT(DISTINCT c.employee_id) AS baseline_employee_count,
    COUNT(DISTINCT CASE WHEN t.empl_id IS NOT NULL THEN c.employee_id END) AS employees_with_any_current_talent_row,
    COUNT(DISTINCT CASE WHEN t.talent_index IS NOT NULL THEN c.employee_id END) AS employees_with_any_current_talent_value,
    MIN(t.cycle_number) AS minimum_observed_cycle_number,
    MAX(t.cycle_number) AS maximum_observed_cycle_number,
    COUNT(DISTINCT t.cycle_number) AS distinct_observed_cycle_count,
    MIN(t.last_modified_date) AS minimum_technical_last_modified_date,
    MAX(t.last_modified_date) AS maximum_technical_last_modified_date,
    MIN(t.airflow_execution_date) AS minimum_technical_airflow_execution_date,
    MAX(t.airflow_execution_date) AS maximum_technical_airflow_execution_date
  FROM august_2025_cohort c
  LEFT JOIN hrda.master_talent_index t
    ON t.empl_id = c.employee_id
),
cycle_profile AS (
  SELECT
    cycle_number,
    COUNT(DISTINCT empl_id) AS employees_with_current_cycle_row,
    COUNT(DISTINCT CASE WHEN talent_index IS NOT NULL THEN empl_id END) AS employees_with_current_cycle_value,
    MIN(last_modified_date) AS minimum_technical_last_modified_date,
    MAX(last_modified_date) AS maximum_technical_last_modified_date,
    MIN(airflow_execution_date) AS minimum_technical_airflow_execution_date,
    MAX(airflow_execution_date) AS maximum_technical_airflow_execution_date
  FROM hrda.master_talent_index
  GROUP BY cycle_number
)
SELECT
  'august_2025_cohort_join' AS result_type,
  NULL::INTEGER AS cycle_number,
  baseline_employee_count AS employee_count,
  employees_with_any_current_talent_row AS talent_row_employee_count,
  employees_with_any_current_talent_value AS talent_value_employee_count,
  minimum_observed_cycle_number AS minimum_cycle_number,
  maximum_observed_cycle_number AS maximum_cycle_number,
  distinct_observed_cycle_count AS distinct_cycle_count,
  minimum_technical_last_modified_date,
  maximum_technical_last_modified_date,
  minimum_technical_airflow_execution_date,
  maximum_technical_airflow_execution_date
FROM cohort_join
UNION ALL
SELECT
  'current_cycle_profile' AS result_type,
  cycle_number,
  NULL::BIGINT AS employee_count,
  employees_with_current_cycle_row AS talent_row_employee_count,
  employees_with_current_cycle_value AS talent_value_employee_count,
  cycle_number AS minimum_cycle_number,
  cycle_number AS maximum_cycle_number,
  1 AS distinct_cycle_count,
  minimum_technical_last_modified_date,
  maximum_technical_last_modified_date,
  minimum_technical_airflow_execution_date,
  maximum_technical_airflow_execution_date
FROM cycle_profile
ORDER BY result_type, cycle_number;
