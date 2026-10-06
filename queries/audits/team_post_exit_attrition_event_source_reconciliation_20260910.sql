/*
  Reconciliación agregada de la fuente de eventos para el estudio de salidas
  secuenciales. Compara employee_id + term_date + term_type normalizado entre
  el historial mensual y all_terminations, sólo para eventos del tramo reciente
  y personas que tuvieron un snapshot Employee/Regular. No expone llaves.
*/
WITH bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
),
eligible_employee_ids AS (
  SELECT DISTINCT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  CROSS JOIN bounds
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND CAST(fis_mo_end_dt AS DATE) >= DATEADD(month, -37, bounds.latest_snapshot_date)
),
monthly_events AS (
  SELECT employee_id, CAST(term_date AS DATE) AS term_date,
    UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) AS term_type,
    COUNT(*) AS source_rows
  FROM hrda.post_hire_monthly_worker_dtls
  CROSS JOIN bounds
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND term_date IS NOT NULL
    AND CAST(term_date AS DATE) >= DATEADD(month, -36, bounds.latest_snapshot_date)
  GROUP BY 1, 2, 3
),
termination_events AS (
  SELECT t.employeeid AS employee_id, t.term_date,
    UPPER(NULLIF(TRIM(CAST(t.term_type AS VARCHAR(256))), '')) AS term_type,
    COUNT(*) AS source_rows
  FROM hrda.all_terminations AS t
  CROSS JOIN bounds
  INNER JOIN eligible_employee_ids AS e ON e.employee_id = t.employeeid
  WHERE t.term_date IS NOT NULL
    AND t.term_date >= DATEADD(month, -36, bounds.latest_snapshot_date)
    AND t.term_date <= bounds.latest_snapshot_date
  GROUP BY 1, 2, 3
),
comparison AS (
  SELECT
    CASE WHEN m.employee_id IS NOT NULL THEN 1 ELSE 0 END AS in_monthly,
    CASE WHEN a.employee_id IS NOT NULL THEN 1 ELSE 0 END AS in_all_terminations,
    CASE WHEN COALESCE(m.term_type, a.term_type) = 'VOLUNTARY' THEN 1 ELSE 0 END AS is_voluntary,
    COALESCE(m.source_rows, 0) AS monthly_source_rows,
    COALESCE(a.source_rows, 0) AS all_terminations_source_rows
  FROM monthly_events AS m
  FULL OUTER JOIN termination_events AS a
    ON a.employee_id = m.employee_id
   AND a.term_date = m.term_date
   AND COALESCE(a.term_type, '__NULL__') = COALESCE(m.term_type, '__NULL__')
)
SELECT 'event_keys_monthly' AS metric, SUM(in_monthly)::DECIMAL(18,4) AS metric_value FROM comparison
UNION ALL SELECT 'event_keys_all_terminations', SUM(in_all_terminations)::DECIMAL(18,4) FROM comparison
UNION ALL SELECT 'event_keys_exact_match', SUM(CASE WHEN in_monthly = 1 AND in_all_terminations = 1 THEN 1 ELSE 0 END)::DECIMAL(18,4) FROM comparison
UNION ALL SELECT 'event_keys_only_monthly', SUM(CASE WHEN in_monthly = 1 AND in_all_terminations = 0 THEN 1 ELSE 0 END)::DECIMAL(18,4) FROM comparison
UNION ALL SELECT 'event_keys_only_all_terminations', SUM(CASE WHEN in_monthly = 0 AND in_all_terminations = 1 THEN 1 ELSE 0 END)::DECIMAL(18,4) FROM comparison
UNION ALL SELECT 'voluntary_exact_match', SUM(CASE WHEN is_voluntary = 1 AND in_monthly = 1 AND in_all_terminations = 1 THEN 1 ELSE 0 END)::DECIMAL(18,4) FROM comparison
UNION ALL SELECT 'voluntary_only_monthly', SUM(CASE WHEN is_voluntary = 1 AND in_monthly = 1 AND in_all_terminations = 0 THEN 1 ELSE 0 END)::DECIMAL(18,4) FROM comparison
UNION ALL SELECT 'voluntary_only_all_terminations', SUM(CASE WHEN is_voluntary = 1 AND in_monthly = 0 AND in_all_terminations = 1 THEN 1 ELSE 0 END)::DECIMAL(18,4) FROM comparison
UNION ALL SELECT 'voluntary_monthly_match_percent', ROUND(
  100.0 * SUM(CASE WHEN is_voluntary = 1 AND in_monthly = 1 AND in_all_terminations = 1 THEN 1 ELSE 0 END)
  / NULLIF(SUM(CASE WHEN is_voluntary = 1 AND in_monthly = 1 THEN 1 ELSE 0 END), 0), 4
)::DECIMAL(18,4) FROM comparison
UNION ALL SELECT 'monthly_repeated_source_rows', SUM(CASE WHEN monthly_source_rows > 1 THEN monthly_source_rows - 1 ELSE 0 END)::DECIMAL(18,4) FROM comparison
UNION ALL SELECT 'all_terminations_repeated_source_rows', SUM(CASE WHEN all_terminations_source_rows > 1 THEN all_terminations_source_rows - 1 ELSE 0 END)::DECIMAL(18,4) FROM comparison
ORDER BY metric;
