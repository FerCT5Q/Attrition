/*
  Cobertura por mes de los campos de fecha de contratación antes y después del
  cambio de fuente de 2022-10 (2026-10-03). Engineering, Employee/Regular
  activos, sin RF360. Sólo agregados.

  Pregunta: ¿qué campo de fecha permite derivar recontratación y tiempo desde
  la última contratación en toda la ventana 2021-07 a 2026-07?
  Regla: un campo sirve para todos los folds si su cobertura es >= 90% en cada
  foto; si un derivado (rehire por fechas) cambia más de 2 puntos al cruzar
  2022-10, se trata como fuente con historia corta.
*/
WITH pop AS (
  SELECT
    CAST(p.fis_mo_end_dt AS DATE) AS snapshot_date,
    p.employee_id,
    MAX(CAST(p.original_hire_date AS DATE)) AS original_hire,
    MAX(CAST(p.max_hire_rehire_date AS DATE)) AS latest_hire,
    MAX(CAST(p.hire_date_o_ea AS DATE)) AS hire_o_ea,
    MAX(CAST(p.service_date AS DATE)) AS service_dt,
    MAX(p.time_in_role) AS time_in_role,
    MAX(p.prior_qc_work_years) AS prior_years
  FROM hrda.post_hire_monthly_worker_dtls p
  WHERE CAST(p.fis_mo_end_dt AS DATE) BETWEEN DATE '2021-06-01' AND DATE '2023-06-30'
    AND p.worker_type = 'Employee' AND p.employee_type = 'Regular' AND p.active_status = 1
    AND p.is_rf360_yes_no = 0 AND TRIM(p.eng_or_noneng) = 'Engineering' AND p.employee_id IS NOT NULL
  GROUP BY 1, 2
)
SELECT
  snapshot_date,
  COUNT(*) AS people,
  ROUND(100.0 * SUM(CASE WHEN original_hire IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS original_hire_pct,
  ROUND(100.0 * SUM(CASE WHEN latest_hire IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS latest_hire_pct,
  ROUND(100.0 * SUM(CASE WHEN hire_o_ea IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS hire_o_ea_pct,
  ROUND(100.0 * SUM(CASE WHEN service_dt IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS service_date_pct,
  ROUND(100.0 * SUM(CASE WHEN time_in_role IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS time_in_role_pct,
  ROUND(100.0 * SUM(CASE WHEN service_dt > original_hire THEN 1 ELSE 0 END) / COUNT(*), 1) AS service_after_original_pct,
  ROUND(100.0 * SUM(CASE WHEN hire_o_ea > original_hire THEN 1 ELSE 0 END) / COUNT(*), 1) AS hire_o_ea_after_original_pct,
  ROUND(100.0 * SUM(CASE WHEN prior_years >= 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS prior_years_pct
FROM pop
GROUP BY 1
ORDER BY 1
