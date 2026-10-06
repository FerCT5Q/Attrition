/*
  Inicio de fuente por mes para variables con historia corta (2026-10-03).
  Engineering, Employee/Regular activos, sin RF360. Sólo agregados.

  Pregunta: ¿desde qué foto mensual cada fuente tiene cobertura >= 90%
  (o, para IOS, desde cuándo hay movimientos registrados)?
  Regla: antes de esa foto la variable se codifica como "(antes de la fuente)".
*/
WITH pop AS (
  SELECT
    CAST(p.fis_mo_end_dt AS DATE) AS snapshot_date,
    p.employee_id,
    MAX(p.is_rehire) AS is_rehire,
    MAX(CAST(p.rehire_date AS DATE)) AS rehire_date,
    MAX(CAST(p.original_hire_date AS DATE)) AS original_hire,
    MAX(CAST(p.max_hire_rehire_date AS DATE)) AS latest_hire,
    MAX(CAST(p.levelentrydate AS DATE)) AS level_entry,
    MAX(p.worker_supervisory_organization_level_from_top) AS layers,
    MAX(NULLIF(TRIM(p.work_arrangement), '')) AS work_arrangement
  FROM hrda.post_hire_monthly_worker_dtls p
  WHERE CAST(p.fis_mo_end_dt AS DATE) >= DATE '2021-06-01'
    AND p.worker_type = 'Employee' AND p.employee_type = 'Regular' AND p.active_status = 1
    AND p.is_rf360_yes_no = 0 AND TRIM(p.eng_or_noneng) = 'Engineering' AND p.employee_id IS NOT NULL
  GROUP BY 1, 2
),
ios_month AS (
  SELECT DATE_TRUNC('month', effective_date) AS month_start, COUNT(DISTINCT employee_id) AS ios_people
  FROM hrda.workers_ios_transfers
  WHERE NULLIF(TRIM(business_process_reason), '') IS NOT NULL
  GROUP BY 1
)
SELECT
  p.snapshot_date,
  COUNT(*) AS people,
  ROUND(100.0 * SUM(CASE WHEN p.is_rehire = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS rehire_flag_pct,
  ROUND(100.0 * SUM(CASE WHEN p.rehire_date IS NOT NULL AND p.rehire_date <= p.snapshot_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS rehire_date_pct,
  ROUND(100.0 * SUM(CASE WHEN p.latest_hire IS NOT NULL AND p.original_hire IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS hire_dates_pct,
  ROUND(100.0 * SUM(CASE WHEN p.latest_hire > p.original_hire THEN 1 ELSE 0 END) / COUNT(*), 1) AS rehire_by_dates_pct,
  ROUND(100.0 * SUM(CASE WHEN p.level_entry IS NOT NULL AND p.level_entry <= p.snapshot_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS level_entry_pct,
  ROUND(100.0 * SUM(CASE WHEN p.layers IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS layers_pct,
  ROUND(100.0 * SUM(CASE WHEN p.work_arrangement IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS work_arrangement_pct,
  MAX(i.ios_people) AS ios_people_in_month
FROM pop p
LEFT JOIN ios_month i ON i.month_start = DATE_TRUNC('month', p.snapshot_date)
GROUP BY 1
ORDER BY 1
