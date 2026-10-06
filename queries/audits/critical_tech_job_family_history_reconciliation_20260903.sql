-- Pregunta: ¿Los valores de critical_tech que no aparecen en el ultimo snapshot
-- de job_family se encuentran en algun snapshot mensual historico?
-- Poblacion: empleados regulares; el ultimo snapshot usa activos, el historico
-- incluye estados disponibles para distinguir ausencia actual de ausencia total.
-- Regla de aceptacion para equivalencia completa: las 62 categorias deben aparecer
-- en el ultimo snapshot y no debe haber valores de mapeo duplicados. Si solo aparecen
-- en historia o nunca aparecen, el mapping no es una equivalencia actual completa.
WITH critical_mapping AS (
  SELECT
    UPPER(TRIM(extended_job_family)) AS normalized_value,
    COUNT(*) AS mapping_rows
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
  GROUP BY 1
),
latest_snapshot AS (
  SELECT MAX(fis_mo_end_dt) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
latest_values AS (
  SELECT DISTINCT UPPER(TRIM(m.job_family)) AS normalized_value
  FROM hrda.post_hire_monthly_worker_dtls AS m
  CROSS JOIN latest_snapshot AS l
  WHERE m.fis_mo_end_dt = l.snapshot_date
    AND m.worker_type = 'Employee'
    AND m.employee_type = 'Regular'
    AND m.active_status = 1
    AND NULLIF(TRIM(m.job_family), '') IS NOT NULL
),
historical_values AS (
  SELECT DISTINCT UPPER(TRIM(job_family)) AS normalized_value
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND NULLIF(TRIM(job_family), '') IS NOT NULL
)
SELECT
  (SELECT snapshot_date FROM latest_snapshot) AS latest_snapshot_date,
  COUNT(*) AS mapping_values,
  SUM(CASE WHEN l.normalized_value IS NOT NULL THEN 1 ELSE 0 END) AS values_in_latest_snapshot,
  SUM(CASE WHEN l.normalized_value IS NULL AND h.normalized_value IS NOT NULL THEN 1 ELSE 0 END) AS historical_only_values,
  SUM(CASE WHEN h.normalized_value IS NULL THEN 1 ELSE 0 END) AS never_observed_in_job_family,
  SUM(CASE WHEN c.mapping_rows > 1 THEN 1 ELSE 0 END) AS duplicate_mapping_values
FROM critical_mapping AS c
LEFT JOIN latest_values AS l
  ON l.normalized_value = c.normalized_value
LEFT JOIN historical_values AS h
  ON h.normalized_value = c.normalized_value;
