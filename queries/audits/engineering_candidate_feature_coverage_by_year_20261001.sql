/*
  Pregunta: ¿qué cobertura histórica tienen las variables candidatas del bloque
  de selección en la población Engineering?
  Población: Employee, Regular, active_status=1, is_rf360_yes_no=0,
  eng_or_noneng='Engineering'; una foto por año (la última de julio, o la más
  reciente en 2026).
  Regla de aceptación: una variable es candidata en los 4 folds rolling si su
  cobertura no nula es >= 90% desde 2021; si sólo existe desde una fecha
  posterior se trata con categoría explícita "sin fuente" y se documenta.
  Sólo porcentajes agregados; employee_id sólo en COUNT(DISTINCT).
*/
WITH fotos AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) >= DATE '2020-07-01'
    AND (EXTRACT(month FROM CAST(fis_mo_end_dt AS DATE)) = 7
         OR CAST(fis_mo_end_dt AS DATE) >= DATE '2026-08-01')
  GROUP BY EXTRACT(year FROM CAST(fis_mo_end_dt AS DATE))
),
base AS (
  SELECT f.snapshot_date, p.*
  FROM fotos f
  INNER JOIN hrda.post_hire_monthly_worker_dtls p
    ON CAST(p.fis_mo_end_dt AS DATE) = f.snapshot_date
  WHERE p.worker_type = 'Employee' AND p.employee_type = 'Regular'
    AND p.active_status = 1 AND p.is_rf360_yes_no = 0
    AND TRIM(p.eng_or_noneng) = 'Engineering'
)
SELECT
  snapshot_date,
  COUNT(DISTINCT employee_id) AS personas,
  COUNT(*) AS filas,
  ROUND(100.0 * SUM(CASE WHEN levelentrydate IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_levelentrydate,
  ROUND(100.0 * SUM(CASE WHEN time_in_job_profile_start_date IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_job_profile_start,
  ROUND(100.0 * SUM(CASE WHEN max_hire_rehire_date IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_max_hire_rehire,
  ROUND(100.0 * SUM(CASE WHEN max_hire_rehire_date > original_hire_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_recontratado,
  ROUND(100.0 * SUM(CASE WHEN prior_qc_work_years IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_prior_qc_years,
  ROUND(100.0 * SUM(CASE WHEN prior_qc_work_years > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_prior_qc_years_pos,
  ROUND(100.0 * SUM(CASE WHEN NULLIF(TRIM(new_hire_type), '') IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_new_hire_type,
  ROUND(100.0 * SUM(CASE WHEN promotion_date IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_promotion_date,
  ROUND(100.0 * SUM(CASE WHEN manager_employee_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_manager_id,
  ROUND(100.0 * SUM(CASE WHEN worker_supervisory_organization_level_from_top IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_layers,
  ROUND(100.0 * SUM(CASE WHEN reg_non_intern_dir_reports IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_dir_reports,
  ROUND(100.0 * SUM(CASE WHEN reg_non_intern_dir_reports > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_con_reportes,
  ROUND(100.0 * SUM(CASE WHEN NULLIF(TRIM(region), '') IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_region,
  COUNT(DISTINCT NULLIF(TRIM(region), '')) AS n_region,
  ROUND(100.0 * SUM(CASE WHEN NULLIF(TRIM(labor_market), '') IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_labor_market,
  COUNT(DISTINCT NULLIF(TRIM(labor_market), '')) AS n_labor_market,
  ROUND(100.0 * SUM(CASE WHEN NULLIF(TRIM(work_arrangement), '') IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_work_arrangement,
  ROUND(100.0 * SUM(CASE WHEN compa_ratio IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_compa_ratio,
  ROUND(100.0 * SUM(CASE WHEN NULLIF(TRIM(compensation_grade), '') IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_grade,
  ROUND(100.0 * SUM(CASE WHEN transfer_date IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_transfer_date,
  ROUND(100.0 * SUM(CASE WHEN transfer_date > DATEADD(month, -12, snapshot_date) AND transfer_date <= snapshot_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_transfer_12m,
  ROUND(100.0 * SUM(CASE WHEN is_transferred = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_is_transferred
FROM base
GROUP BY 1
ORDER BY 1
