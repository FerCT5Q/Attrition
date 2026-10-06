/*
  Calendario de snapshots completos para el frame mensual de Critical Tech.
  Salida agregada y sin identificadores.
*/
WITH dates AS (
  SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) <= DATE '2026-09-07'
),
calendar AS (
  SELECT
    snapshot_date,
    LEAD(snapshot_date) OVER (ORDER BY snapshot_date) AS next_snapshot_date
  FROM dates
)
SELECT snapshot_date, next_snapshot_date
FROM calendar
WHERE next_snapshot_date IS NOT NULL
  AND next_snapshot_date <= DATE '2026-09-07'
ORDER BY snapshot_date;
