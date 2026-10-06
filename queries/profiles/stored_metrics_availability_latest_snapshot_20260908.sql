-- Pregunta: ¿compa_ratio y prior_qc_work_years existen y tienen valores
-- observables en el último snapshot de empleados regulares activos?
-- Población: worker_type='Employee', employee_type='Regular', active_status=1.
-- Grain: empleado-snapshot; los conteos usan empleados distintos.
-- Regla de aceptación: ambos campos deben tener al menos un empleado poblado.
-- Alcance: prueba almacenamiento y observabilidad, no fórmula, lineage ni
-- significado de negocio de ninguna métrica precalculada.

WITH latest_snapshot AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
base AS (
  SELECT
    employee_id,
    compa_ratio,
    prior_qc_work_years
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND CAST(fis_mo_end_dt AS DATE) = (SELECT snapshot_date FROM latest_snapshot)
)
SELECT
  (SELECT snapshot_date FROM latest_snapshot) AS snapshot_date,
  COUNT(DISTINCT employee_id) AS eligible_employees,
  COUNT(DISTINCT CASE WHEN compa_ratio IS NOT NULL THEN employee_id END)
    AS compa_ratio_populated_employees,
  COUNT(DISTINCT CASE WHEN compa_ratio <= 0 THEN employee_id END)
    AS compa_ratio_nonpositive_employees,
  COUNT(DISTINCT CASE WHEN compa_ratio > 3 THEN employee_id END)
    AS compa_ratio_above_three_employees,
  COUNT(DISTINCT CASE WHEN prior_qc_work_years IS NOT NULL THEN employee_id END)
    AS prior_experience_populated_employees,
  COUNT(DISTINCT CASE WHEN prior_qc_work_years < 0 THEN employee_id END)
    AS prior_experience_negative_employees,
  COUNT(DISTINCT CASE WHEN prior_qc_work_years > 80 THEN employee_id END)
    AS prior_experience_above_eighty_employees
FROM base;
