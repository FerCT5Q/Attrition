/*
  Pregunta: ¿Dos cálculos agregados equivalentes producen el mismo flag y se
  aplican las fronteras (snapshot - 6 meses, snapshot] sin eventos futuros?

  Regla de aceptación para la implementación candidata: mismatch_count=0 y
  future_event_rows=0. Las métricas de frontera se reportan para revisión; no
  convierten por sí solas la semántica de cand_applied en definición aprobada.
*/
WITH snapshots AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS VARCHAR(32)) AS fiscal_year,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY 1, 2, 3
),
source_bounds AS (
  SELECT
    MIN(CAST(application_date AS DATE)) AS first_application_date,
    MAX(CAST(application_date AS DATE)) AS last_application_date
  FROM hrda.applications
  WHERE employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
    AND cand_applied = 1
),
scoped_snapshots AS (
  SELECT s.snapshot_date, s.fiscal_year, s.employee_id
  FROM snapshots AS s
  CROSS JOIN source_bounds AS b
  WHERE s.snapshot_date > DATEADD(month, 6, b.first_application_date)
    AND s.snapshot_date <= b.last_application_date
),
events AS (
  SELECT employee_id, req_id, CAST(application_date AS DATE) AS application_date
  FROM hrda.applications
  WHERE employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
    AND cand_applied = 1
  GROUP BY 1, 2, 3
),
implementation_a AS (
  SELECT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id,
    CASE WHEN COUNT(DISTINCT e.req_id) >= 4 THEN 1 ELSE 0 END AS flag_a,
    SUM(CASE WHEN e.application_date = DATEADD(month, -6, s.snapshot_date) THEN 1 ELSE 0 END) AS start_boundary_event_rows,
    SUM(CASE WHEN e.application_date = s.snapshot_date THEN 1 ELSE 0 END) AS end_boundary_event_rows
  FROM scoped_snapshots AS s
  LEFT JOIN events AS e
    ON e.employee_id = s.employee_id
   AND e.application_date > DATEADD(month, -6, s.snapshot_date)
   AND e.application_date <= s.snapshot_date
  GROUP BY 1, 2, 3
),
window_events_b AS (
  SELECT DISTINCT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id,
    e.req_id
  FROM scoped_snapshots AS s
  JOIN events AS e
    ON e.employee_id = s.employee_id
   AND e.application_date > DATEADD(month, -6, s.snapshot_date)
   AND e.application_date <= s.snapshot_date
),
implementation_b AS (
  SELECT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id,
    CASE WHEN COUNT(w.req_id) >= 4 THEN 1 ELSE 0 END AS flag_b
  FROM scoped_snapshots AS s
  LEFT JOIN window_events_b AS w
    ON w.snapshot_date = s.snapshot_date
   AND w.employee_id = s.employee_id
  GROUP BY 1, 2, 3
),
future_events AS (
  SELECT COUNT(*) AS future_event_rows
  FROM scoped_snapshots AS s
  JOIN events AS e
    ON e.employee_id = s.employee_id
   AND e.application_date > s.snapshot_date
)
SELECT
  a.fiscal_year,
  COUNT(*) AS comparable_employee_snapshots,
  SUM(a.flag_a) AS flags_implementation_a,
  SUM(b.flag_b) AS flags_implementation_b,
  SUM(CASE WHEN a.flag_a <> b.flag_b THEN 1 ELSE 0 END) AS mismatch_count,
  SUM(a.start_boundary_event_rows) AS start_boundary_event_rows_excluded,
  SUM(a.end_boundary_event_rows) AS end_boundary_event_rows_included,
  (SELECT future_event_rows FROM future_events) AS future_event_rows
FROM implementation_a AS a
JOIN implementation_b AS b
  ON b.snapshot_date = a.snapshot_date
 AND b.employee_id = a.employee_id
GROUP BY 1
ORDER BY 1;
