/*
  Continuidad por persona de service_date, original_hire_date y
  prior_qc_work_years al cruzar el cambio de fuente (2022-09-25 -> 2022-10-23)
  y en un año sin cambio (2023-09-24 -> 2023-10-22) como control (2026-10-03).
  Engineering, Employee/Regular activos, sin RF360. Sólo agregados.

  Pregunta: ¿los valores previos a 2022-10 son los mismos que después, para
  usarlos en toda la ventana de entrenamiento?
  Regla: se aceptan si coinciden en >= 95% de las personas presentes en ambas
  fotos y la diferencia con el control es < 3 puntos.
*/
WITH pairs AS (
  SELECT 'switch' AS pair, DATE '2022-09-25' AS d0, DATE '2022-10-23' AS d1
  UNION ALL SELECT 'control', DATE '2023-09-24', DATE '2023-10-22'
),
rows_ AS (
  SELECT r.pair, p.employee_id,
         MAX(CASE WHEN CAST(p.fis_mo_end_dt AS DATE) = r.d0 THEN CAST(p.service_date AS DATE) END) AS s0,
         MAX(CASE WHEN CAST(p.fis_mo_end_dt AS DATE) = r.d1 THEN CAST(p.service_date AS DATE) END) AS s1,
         MAX(CASE WHEN CAST(p.fis_mo_end_dt AS DATE) = r.d0 THEN CAST(p.original_hire_date AS DATE) END) AS o0,
         MAX(CASE WHEN CAST(p.fis_mo_end_dt AS DATE) = r.d1 THEN CAST(p.original_hire_date AS DATE) END) AS o1,
         MAX(CASE WHEN CAST(p.fis_mo_end_dt AS DATE) = r.d0 THEN p.prior_qc_work_years END) AS y0,
         MAX(CASE WHEN CAST(p.fis_mo_end_dt AS DATE) = r.d1 THEN p.prior_qc_work_years END) AS y1
  FROM pairs r
  INNER JOIN hrda.post_hire_monthly_worker_dtls p
    ON CAST(p.fis_mo_end_dt AS DATE) IN (r.d0, r.d1)
  WHERE p.worker_type = 'Employee' AND p.employee_type = 'Regular' AND p.active_status = 1
    AND p.is_rf360_yes_no = 0 AND TRIM(p.eng_or_noneng) = 'Engineering' AND p.employee_id IS NOT NULL
  GROUP BY 1, 2
)
SELECT pair,
       SUM(CASE WHEN s0 IS NOT NULL AND s1 IS NOT NULL THEN 1 ELSE 0 END) AS both_present,
       ROUND(100.0 * SUM(CASE WHEN s0 = s1 THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN s0 IS NOT NULL AND s1 IS NOT NULL THEN 1 ELSE 0 END), 0), 1) AS service_date_equal_pct,
       ROUND(100.0 * SUM(CASE WHEN o0 = o1 THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN o0 IS NOT NULL AND o1 IS NOT NULL THEN 1 ELSE 0 END), 0), 1) AS original_hire_equal_pct,
       ROUND(100.0 * SUM(CASE WHEN ABS(y0 - y1) < 0.05 THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN y0 IS NOT NULL AND y1 IS NOT NULL THEN 1 ELSE 0 END), 0), 1) AS prior_years_equal_pct,
       ROUND(100.0 * SUM(CASE WHEN FLOOR(y0) = FLOOR(y1) THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN y0 IS NOT NULL AND y1 IS NOT NULL THEN 1 ELSE 0 END), 0), 1) AS prior_years_same_floor_pct
FROM rows_
GROUP BY 1
ORDER BY 1
