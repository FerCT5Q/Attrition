/*
  Concordancia entre service_date y la fuente de recontratación desde 2022-10
  (2026-10-03). Engineering, Employee/Regular activos, sin RF360. Sólo agregados.

  Pregunta: ¿service_date > original_hire_date reproduce is_rehire y
  service_date coincide con max_hire_rehire_date, para usarlo como sustituto
  antes de 2022-10?
  Regla: se acepta como sustituto si la concordancia del indicador es >= 95% y
  las fechas coinciden (±31 días) en >= 90% en cada foto de enero.
*/
WITH pop AS (
  SELECT
    CAST(p.fis_mo_end_dt AS DATE) AS snapshot_date,
    p.employee_id,
    MAX(p.is_rehire) AS is_rehire,
    MAX(CAST(p.original_hire_date AS DATE)) AS original_hire,
    MAX(CAST(p.max_hire_rehire_date AS DATE)) AS latest_hire,
    MAX(CAST(p.service_date AS DATE)) AS service_dt
  FROM hrda.post_hire_monthly_worker_dtls p
  WHERE CAST(p.fis_mo_end_dt AS DATE) IN (DATE '2022-10-23', DATE '2023-01-22', DATE '2024-01-21', DATE '2025-01-26', DATE '2026-01-25')
    AND p.worker_type = 'Employee' AND p.employee_type = 'Regular' AND p.active_status = 1
    AND p.is_rf360_yes_no = 0 AND TRIM(p.eng_or_noneng) = 'Engineering' AND p.employee_id IS NOT NULL
  GROUP BY 1, 2
)
SELECT
  snapshot_date,
  COUNT(*) AS people,
  SUM(CASE WHEN is_rehire = 1 AND service_dt > original_hire THEN 1 ELSE 0 END) AS both_rehire,
  SUM(CASE WHEN is_rehire = 1 AND NOT (service_dt > original_hire) THEN 1 ELSE 0 END) AS flag_only,
  SUM(CASE WHEN COALESCE(is_rehire, 0) = 0 AND service_dt > original_hire THEN 1 ELSE 0 END) AS service_only,
  ROUND(100.0 * SUM(CASE WHEN (is_rehire = 1) = (service_dt > original_hire) THEN 1 ELSE 0 END) / COUNT(*), 1) AS indicator_agreement_pct,
  ROUND(100.0 * SUM(CASE WHEN ABS(DATEDIFF(day, service_dt, latest_hire)) <= 31 THEN 1 ELSE 0 END) / COUNT(*), 1) AS date_match_31d_pct,
  ROUND(100.0 * SUM(CASE WHEN ABS(DATEDIFF(day, service_dt, latest_hire)) <= 31 THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN is_rehire = 1 THEN 1 ELSE 0 END), 0), 1) AS date_match_among_rehire_pct_raw
FROM pop
GROUP BY 1
ORDER BY 1
