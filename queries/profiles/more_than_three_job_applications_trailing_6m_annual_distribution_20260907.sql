/*
  Distribución anual publicable del flag candidato de seis meses. Sólo se
  devuelve un año fiscal cuando la cohorte positiva acumulada es >=30; evita
  publicar conteos mensuales pequeños. El denominador de vínculo es time-safe
  y no convierte no-vinculados en ceros confirmados.
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
eligible_snapshots AS (
  SELECT s.snapshot_date, s.fiscal_year, s.employee_id
  FROM snapshots AS s
  CROSS JOIN source_bounds AS b
  WHERE s.snapshot_date > DATEADD(month, 6, b.first_application_date)
    AND s.snapshot_date <= b.last_application_date
),
time_safe_linkage AS (
  SELECT employee_id, MIN(CAST(application_date AS DATE)) AS first_linked_application_date
  FROM hrda.applications
  WHERE employee_id IS NOT NULL
    AND application_date IS NOT NULL
  GROUP BY 1
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
employee_snapshot_flags AS (
  SELECT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id,
    CASE WHEN linked.first_linked_application_date <= s.snapshot_date THEN 1 ELSE 0 END AS time_safe_linked_flag,
    CASE WHEN COUNT(DISTINCT e.req_id) >= 4 THEN 1 ELSE 0 END AS positive_flag
  FROM eligible_snapshots AS s
  LEFT JOIN time_safe_linkage AS linked
    ON linked.employee_id = s.employee_id
  LEFT JOIN events AS e
    ON e.employee_id = s.employee_id
   AND e.application_date > DATEADD(month, -6, s.snapshot_date)
   AND e.application_date <= s.snapshot_date
  GROUP BY 1, 2, 3, 4
),
annual AS (
  SELECT
    fiscal_year,
    COUNT(*) AS eligible_employee_snapshots,
    SUM(time_safe_linked_flag) AS time_safe_linked_employee_snapshots,
    SUM(CASE WHEN time_safe_linked_flag = 1 AND positive_flag = 1 THEN 1 ELSE 0 END) AS flagged_employee_snapshots
  FROM employee_snapshot_flags
  GROUP BY 1
)
SELECT
  fiscal_year,
  eligible_employee_snapshots,
  time_safe_linked_employee_snapshots,
  flagged_employee_snapshots,
  ROUND(
    100.0 * flagged_employee_snapshots / NULLIF(time_safe_linked_employee_snapshots, 0),
    4
  ) AS flag_prevalence_percent
FROM annual
WHERE flagged_employee_snapshots >= 30
ORDER BY fiscal_year;
