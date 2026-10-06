/*
  Pregunta añadida tras el join v1: ¿cuántos empleados-snapshot sólo se
  vincularían al feed mediante una fila futura? El vínculo de cobertura debe
  existir a más tardar en el cierre del snapshot.

  Regla: time_safe_linked_employee_snapshots es el único denominador de
  enlace que puede mostrarse. Aun así, representa presencia histórica en el
  feed, no confirmación de que una persona sin evento tenga un cero definitivo.
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
all_time_linkage AS (
  SELECT employee_id, MIN(CAST(application_date AS DATE)) AS first_linked_application_date
  FROM hrda.applications
  WHERE employee_id IS NOT NULL
    AND application_date IS NOT NULL
  GROUP BY 1
)
SELECT
  s.fiscal_year,
  COUNT(*) AS eligible_employee_snapshots,
  SUM(CASE WHEN linked.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS all_time_linked_employee_snapshots,
  SUM(CASE WHEN linked.first_linked_application_date <= s.snapshot_date THEN 1 ELSE 0 END) AS time_safe_linked_employee_snapshots,
  SUM(CASE WHEN linked.first_linked_application_date > s.snapshot_date THEN 1 ELSE 0 END) AS future_only_linked_employee_snapshots,
  SUM(CASE WHEN linked.employee_id IS NULL THEN 1 ELSE 0 END) AS never_linked_employee_snapshots
FROM scoped_snapshots AS s
LEFT JOIN all_time_linkage AS linked
  ON linked.employee_id = s.employee_id
GROUP BY 1
ORDER BY 1;
