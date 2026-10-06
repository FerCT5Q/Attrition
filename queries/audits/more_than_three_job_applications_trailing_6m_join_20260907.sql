/*
  Pregunta: ¿El snapshot activo tiene un grain único empleado-fecha y cuál es
  la relación con el feed de solicitudes? Un no-match sólo significa que no
  hay evento vinculado; no se publica ni se interpreta como cero confirmado.

  Regla de aceptación para el join estructural: snapshot_duplicate_rows=0.
  Los no-matches se informan como límite de observabilidad y no como falla de
  integridad del employee_id.
*/
WITH raw_snapshot_rows AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
snapshots AS (
  SELECT snapshot_date, employee_id
  FROM raw_snapshot_rows
  GROUP BY 1, 2
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
  SELECT s.snapshot_date, s.employee_id
  FROM snapshots AS s
  CROSS JOIN source_bounds AS b
  WHERE s.snapshot_date > DATEADD(month, 6, b.first_application_date)
    AND s.snapshot_date <= b.last_application_date
),
linked_employees AS (
  SELECT employee_id
  FROM hrda.applications
  WHERE employee_id IS NOT NULL
  GROUP BY 1
)
SELECT
  COUNT(*) AS eligible_employee_snapshots,
  (SELECT COUNT(*) FROM raw_snapshot_rows) - (SELECT COUNT(*) FROM snapshots) AS snapshot_duplicate_rows,
  SUM(CASE WHEN linked.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_employee_snapshots,
  SUM(CASE WHEN linked.employee_id IS NULL THEN 1 ELSE 0 END) AS unmatched_employee_snapshots,
  COUNT(DISTINCT CASE WHEN linked.employee_id IS NOT NULL THEN s.employee_id END) AS distinct_matched_employees,
  COUNT(DISTINCT CASE WHEN linked.employee_id IS NULL THEN s.employee_id END) AS distinct_unmatched_employees
FROM scoped_snapshots AS s
LEFT JOIN linked_employees AS linked
  ON linked.employee_id = s.employee_id;
