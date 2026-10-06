/* Calendario público (sin datos de personas) para el estudio de 24 cohortes. */
WITH source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) <= DATE '2026-08-23'
),
critical_tech_catalog AS (
  SELECT LOWER(TRIM(extended_job_family)) AS normalized_job_family
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
  GROUP BY 1
  HAVING COUNT(DISTINCT NULLIF(TRIM(seg), '')) = 1
     AND MAX(NULLIF(TRIM(seg), '')) <> 'Other Eng'
),
snapshot_dates AS (
  SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls AS w
  INNER JOIN critical_tech_catalog AS c
    ON c.normalized_job_family = LOWER(TRIM(w.job_family))
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.is_rf360_yes_no = 0
    AND w.fis_mo_end_dt IS NOT NULL
),
calendar AS (
  SELECT snapshot_date,
    LAG(snapshot_date, 1) OVER (ORDER BY snapshot_date) AS p1,
    LAG(snapshot_date, 6) OVER (ORDER BY snapshot_date) AS p6,
    LEAD(snapshot_date, 1) OVER (ORDER BY snapshot_date) AS f1,
    LEAD(snapshot_date, 2) OVER (ORDER BY snapshot_date) AS f2,
    LEAD(snapshot_date, 3) OVER (ORDER BY snapshot_date) AS f3,
    LEAD(snapshot_date, 4) OVER (ORDER BY snapshot_date) AS f4,
    LEAD(snapshot_date, 5) OVER (ORDER BY snapshot_date) AS f5,
    LEAD(snapshot_date, 6) OVER (ORDER BY snapshot_date) AS f6
    , LEAD(snapshot_date, 7) OVER (ORDER BY snapshot_date) AS f7
    , LEAD(snapshot_date, 8) OVER (ORDER BY snapshot_date) AS f8
    , LEAD(snapshot_date, 9) OVER (ORDER BY snapshot_date) AS f9
    , LEAD(snapshot_date, 10) OVER (ORDER BY snapshot_date) AS f10
    , LEAD(snapshot_date, 11) OVER (ORDER BY snapshot_date) AS f11
    , LEAD(snapshot_date, 12) OVER (ORDER BY snapshot_date) AS f12
  FROM snapshot_dates
)
SELECT c.snapshot_date, c.p1, c.p6, c.f1, c.f2, c.f3, c.f4, c.f5, c.f6, c.f7, c.f8, c.f9, c.f10, c.f11, c.f12
FROM calendar AS c
CROSS JOIN source_bounds AS bounds
WHERE c.p6 IS NOT NULL
  AND c.f12 IS NOT NULL
  AND c.f12 <= bounds.latest_snapshot_date
  AND c.snapshot_date >= DATEADD(month, -35, bounds.latest_snapshot_date)
  AND DATEDIFF(day, c.p6, c.p1) BETWEEN 100 AND 260
  AND DATEDIFF(day, c.p1, c.snapshot_date) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.snapshot_date, c.f1) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f1, c.f2) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f2, c.f3) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f3, c.f4) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f4, c.f5) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f5, c.f6) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f6, c.f7) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f7, c.f8) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f8, c.f9) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f9, c.f10) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f10, c.f11) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f11, c.f12) BETWEEN 20 AND 45
ORDER BY c.snapshot_date;
