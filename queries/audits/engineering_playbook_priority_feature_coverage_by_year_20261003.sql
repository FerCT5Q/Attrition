/*
  Cobertura por año de las variables prioritarias del playbook candidatas al
  modelo v2 de Engineering (2026-10-03). Sólo agregados.

  Población: Employee, Regular, active_status=1, is_rf360_yes_no=0,
  eng_or_noneng='Engineering', foto de enero de cada año (y la última de 2026).

  Pregunta: ¿qué variables tienen cobertura estable en toda la ventana de
  entrenamiento (2021-07 a 2026-07) y cuáles sólo en parte?
  Regla de aceptación: una variable se usa en todos los folds si su cobertura
  es >= 90% en cada año desde 2021; si no, se marca como historia corta.
*/
WITH snaps AS (
  SELECT EXTRACT(year FROM CAST(fis_mo_end_dt AS DATE)) AS yr, MIN(CAST(fis_mo_end_dt AS DATE)) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) >= DATE '2021-01-01'
  GROUP BY 1
),
pop AS (
  SELECT
    s.yr,
    s.snapshot_date,
    p.employee_id,
    MAX(p.prior_qc_work_years) AS prior_years,
    MAX(p.is_rehire) AS is_rehire,
    MAX(CAST(p.rehire_date AS DATE)) AS rehire_date,
    MAX(CAST(p.original_hire_date AS DATE)) AS original_hire,
    MAX(CAST(p.max_hire_rehire_date AS DATE)) AS latest_hire,
    MAX(CAST(p.levelentrydate AS DATE)) AS level_entry,
    MAX(p.worker_supervisory_organization_level_from_top) AS layers,
    MAX(NULLIF(TRIM(p.work_arrangement), '')) AS work_arrangement
  FROM snaps s
  INNER JOIN hrda.post_hire_monthly_worker_dtls p ON CAST(p.fis_mo_end_dt AS DATE) = s.snapshot_date
  WHERE p.worker_type = 'Employee' AND p.employee_type = 'Regular' AND p.active_status = 1
    AND p.is_rf360_yes_no = 0 AND TRIM(p.eng_or_noneng) = 'Engineering' AND p.employee_id IS NOT NULL
  GROUP BY 1, 2, 3
),
ios AS (
  SELECT p.yr, COUNT(DISTINCT p.employee_id) AS people_with_ios_12m
  FROM pop p
  INNER JOIN hrda.workers_ios_transfers t
    ON t.employee_id = p.employee_id
   AND t.effective_date > DATEADD(month, -12, p.snapshot_date)
   AND t.effective_date <= p.snapshot_date
   AND NULLIF(TRIM(t.business_process_reason), '') IS NOT NULL
  GROUP BY 1
),
promo_history AS (
  SELECT MIN(CAST(fis_mo_end_dt AS DATE)) AS first_snapshot,
         MIN(CASE WHEN is_promo = 1 AND promotion_date IS NOT NULL THEN CAST(promotion_date AS DATE) END) AS first_promotion_date
  FROM hrda.post_hire_monthly_worker_dtls
)
SELECT
  p.yr,
  p.snapshot_date,
  COUNT(DISTINCT p.employee_id) AS people,
  ROUND(100.0 * SUM(CASE WHEN p.prior_years >= 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS prior_years_valid_pct,
  ROUND(100.0 * SUM(CASE WHEN p.is_rehire = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS rehire_flag_pct,
  ROUND(100.0 * SUM(CASE WHEN p.latest_hire > p.original_hire THEN 1 ELSE 0 END) / COUNT(*), 1) AS rehire_by_dates_pct,
  ROUND(100.0 * SUM(CASE WHEN p.latest_hire IS NOT NULL AND p.original_hire IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS hire_dates_valid_pct,
  ROUND(100.0 * SUM(CASE WHEN p.level_entry IS NOT NULL AND p.level_entry <= p.snapshot_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS level_entry_valid_pct,
  ROUND(100.0 * SUM(CASE WHEN p.layers IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS layers_pct,
  ROUND(100.0 * SUM(CASE WHEN p.work_arrangement IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS work_arrangement_pct,
  ROUND(100.0 * MAX(i.people_with_ios_12m) / COUNT(DISTINCT p.employee_id), 1) AS ios_12m_pct,
  MAX(h.first_snapshot) AS table_first_snapshot,
  MAX(h.first_promotion_date) AS first_promotion_date
FROM pop p
LEFT JOIN ios i ON i.yr = p.yr
CROSS JOIN promo_history h
GROUP BY 1, 2
ORDER BY 1
