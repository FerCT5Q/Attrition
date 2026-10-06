/*
  Propuesta de feature: More than 3 job applications, ventana móvil de 6 meses.

  Población: employee_type='Regular', worker_type='Employee', active_status=1.
  Grain: empleado-snapshot mensual; el CTE snapshots elimina duplicados antes
  de unir eventos. Flag=1 si hay >=4 req_id únicos con cand_applied=1 en
  (snapshot_date - 6 meses, snapshot_date].

  Publicación: el resultado es agregado por snapshot. observable_employees
  requiere que el vínculo al feed ya exista al cierre del snapshot; no
  interpreta automáticamente a los no vinculados como cero. Los snapshots se
  limitan al periodo en que el feed contiene observaciones y a ventanas con al
  menos seis meses desde el primer evento observado.
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
    AND application_date IS NOT NULL
    AND cand_applied = 1
),
eligible_snapshots AS (
  SELECT s.snapshot_date, s.fiscal_year, s.employee_id
  FROM snapshots AS s
  CROSS JOIN source_bounds AS b
  WHERE s.snapshot_date > DATEADD(month, 6, b.first_application_date)
    AND s.snapshot_date <= b.last_application_date
),
time_safe_linkage AS (
  SELECT
    employee_id,
    MIN(CAST(application_date AS DATE)) AS first_linked_application_date
  FROM hrda.applications
  WHERE employee_id IS NOT NULL
    AND application_date IS NOT NULL
  GROUP BY 1
),
deduplicated_events AS (
  SELECT
    employee_id,
    req_id,
    CAST(application_date AS DATE) AS application_date
  FROM hrda.applications
  WHERE employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
    AND cand_applied = 1
  GROUP BY 1, 2, 3
),
employee_snapshot_counts AS (
  SELECT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id,
    CASE
      WHEN linked.first_linked_application_date <= s.snapshot_date THEN 1
      ELSE 0
    END AS observable_flag,
    COUNT(DISTINCT e.req_id) AS trailing_unique_requisitions
  FROM eligible_snapshots AS s
  LEFT JOIN time_safe_linkage AS linked
    ON linked.employee_id = s.employee_id
  LEFT JOIN deduplicated_events AS e
    ON e.employee_id = s.employee_id
   AND e.application_date > DATEADD(month, -6, s.snapshot_date)
   AND e.application_date <= s.snapshot_date
  GROUP BY 1, 2, 3, 4
),
monthly_aggregates AS (
  SELECT
    snapshot_date,
    fiscal_year,
    COUNT(*) AS eligible_employees,
    SUM(observable_flag) AS observable_employees,
    SUM(CASE WHEN observable_flag = 1 AND trailing_unique_requisitions >= 4 THEN 1 ELSE 0 END) AS raw_event_employees
  FROM employee_snapshot_counts
  GROUP BY 1, 2
)
SELECT
  snapshot_date,
  fiscal_year,
  eligible_employees,
  observable_employees,
  CASE WHEN raw_event_employees >= 30 THEN raw_event_employees ELSE NULL END AS event_employees,
  'Flag candidato: >=4 req_id únicos con cand_applied=1 en los seis meses previos. Positivos mensuales menores de 30 se suprimen. El denominador observable es vínculo al feed existente al cierre del snapshot, no prueba por sí solo un cero definitivo.' AS notes
FROM monthly_aggregates
ORDER BY 1;
