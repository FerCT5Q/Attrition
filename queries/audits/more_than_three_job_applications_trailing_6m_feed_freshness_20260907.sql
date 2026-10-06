/*
  Pregunta: ¿Hasta qué fecha llegan los eventos de solicitudes frente a los
  snapshots de fuerza laboral? Regla de aceptación para uso actual: la última
  application_date debe ser igual o posterior al último snapshot publicable.
  Si falla, la distribución queda limitada al periodo observado.
*/
WITH application_bounds AS (
  SELECT
    MIN(CAST(application_date AS DATE)) AS first_application_date,
    MAX(CAST(application_date AS DATE)) AS last_application_date,
    COUNT(*) AS cand_applied_rows
  FROM hrda.applications
  WHERE employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
    AND cand_applied = 1
),
snapshot_bounds AS (
  SELECT
    MIN(CAST(fis_mo_end_dt AS DATE)) AS first_snapshot_date,
    MAX(CAST(fis_mo_end_dt AS DATE)) AS last_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
)
SELECT
  a.first_application_date,
  a.last_application_date,
  s.first_snapshot_date,
  s.last_snapshot_date,
  DATEDIFF(day, a.last_application_date, s.last_snapshot_date) AS feed_lag_days,
  a.cand_applied_rows
FROM application_bounds AS a
CROSS JOIN snapshot_bounds AS s;
