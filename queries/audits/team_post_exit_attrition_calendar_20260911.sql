/* Calendario público (sin datos de personas) para el estudio de 24 cohortes. */
WITH source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
),
snapshot_dates AS (
  SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
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
  FROM snapshot_dates
)
SELECT c.snapshot_date, c.p1, c.p6, c.f1, c.f2, c.f3, c.f4, c.f5, c.f6
FROM calendar AS c
CROSS JOIN source_bounds AS bounds
WHERE c.p6 IS NOT NULL
  AND c.f6 IS NOT NULL
  AND c.snapshot_date >= DATEADD(month, -29, bounds.latest_snapshot_date)
  AND DATEDIFF(day, c.p6, c.p1) BETWEEN 100 AND 260
  AND DATEDIFF(day, c.p1, c.snapshot_date) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.snapshot_date, c.f1) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f1, c.f2) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f2, c.f3) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f3, c.f4) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f4, c.f5) BETWEEN 20 AND 45
  AND DATEDIFF(day, c.f5, c.f6) BETWEEN 20 AND 45
ORDER BY c.snapshot_date;
