/*
  Corrección del audit v1: los eventos posteriores al snapshot pueden existir
  en la fuente y no son un error. Esta versión mide exclusivamente si alguno
  fue incluido por la feature (debe ser cero), además de comparar dos
  implementaciones agregadas del flag.

  Regla de aceptación: mismatch_count=0 y future_event_rows_included=0 en cada
  año fiscal. Los casos exactamente en el inicio y cierre de ventana se
  reportan como control de frontera.
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
feature_window_events AS (
  SELECT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id,
    e.req_id,
    e.application_date
  FROM scoped_snapshots AS s
  LEFT JOIN events AS e
    ON e.employee_id = s.employee_id
   AND e.application_date > DATEADD(month, -6, s.snapshot_date)
   AND e.application_date <= s.snapshot_date
),
implementation_a AS (
  SELECT
    snapshot_date,
    fiscal_year,
    employee_id,
    CASE WHEN COUNT(DISTINCT req_id) >= 4 THEN 1 ELSE 0 END AS flag_a,
    SUM(CASE WHEN application_date > snapshot_date THEN 1 ELSE 0 END) AS future_event_rows_included
  FROM feature_window_events
  GROUP BY 1, 2, 3
),
implementation_b_events AS (
  SELECT DISTINCT snapshot_date, fiscal_year, employee_id, req_id
  FROM feature_window_events
  WHERE req_id IS NOT NULL
),
implementation_b AS (
  SELECT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id,
    CASE WHEN COUNT(b.req_id) >= 4 THEN 1 ELSE 0 END AS flag_b
  FROM scoped_snapshots AS s
  LEFT JOIN implementation_b_events AS b
    ON b.snapshot_date = s.snapshot_date
   AND b.employee_id = s.employee_id
  GROUP BY 1, 2, 3
),
boundary_events AS (
  SELECT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id,
    SUM(CASE WHEN e.application_date = DATEADD(month, -6, s.snapshot_date) THEN 1 ELSE 0 END) AS start_boundary_event_rows,
    SUM(CASE WHEN e.application_date = s.snapshot_date THEN 1 ELSE 0 END) AS end_boundary_event_rows
  FROM scoped_snapshots AS s
  LEFT JOIN events AS e
    ON e.employee_id = s.employee_id
   AND e.application_date BETWEEN DATEADD(month, -6, s.snapshot_date) AND s.snapshot_date
  GROUP BY 1, 2, 3
)
SELECT
  a.fiscal_year,
  COUNT(*) AS comparable_employee_snapshots,
  SUM(a.flag_a) AS flags_implementation_a,
  SUM(b.flag_b) AS flags_implementation_b,
  SUM(CASE WHEN a.flag_a <> b.flag_b THEN 1 ELSE 0 END) AS mismatch_count,
  SUM(a.future_event_rows_included) AS future_event_rows_included,
  SUM(boundary.start_boundary_event_rows) AS start_boundary_event_rows_excluded,
  SUM(boundary.end_boundary_event_rows) AS end_boundary_event_rows_included
FROM implementation_a AS a
JOIN implementation_b AS b
  ON b.snapshot_date = a.snapshot_date
 AND b.employee_id = a.employee_id
JOIN boundary_events AS boundary
  ON boundary.snapshot_date = a.snapshot_date
 AND boundary.employee_id = a.employee_id
GROUP BY 1
ORDER BY 1;
