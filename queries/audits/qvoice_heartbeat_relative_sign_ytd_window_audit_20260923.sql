/*
  Ventana post-encuesta para attrition por señal relativa QVoice heartbeat.

  Claim
  -----
  Los segmentos +1, 0 y -1 de la wave Jan-2026 se comparan con salidas
  voluntarias posteriores al inicio de la encuesta y hasta el cierre fiscal
  de agosto de 2026. La cohorte se fija antes de la encuesta, en el snapshot
  activo Regular del 28-Dec-2025.

  Regla de aceptación
  -------------------
  Debe haber una fila por empleado en la cohorte, el cierre debe ser posterior
  a la encuesta, y las salidas voluntarias distintas no pueden exceder la
  cohorte. No se devuelven empleados ni respuestas individuales.
*/
WITH parameters AS (
  SELECT
    DATE '2026-01-07' AS survey_launch_date,
    DATE '2025-12-28' AS baseline_snapshot,
    DATE '2026-08-23' AS august_cutoff_date
),
baseline_rows AS (
  SELECT
    w.employee_id,
    COUNT(*) AS snapshot_row_count
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN parameters AS p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_snapshot
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
  GROUP BY 1
),
voluntary_events AS (
  SELECT
    w.employee_id,
    COUNT(DISTINCT CAST(w.term_date AS DATE)) AS event_date_count
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN parameters AS p
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > p.survey_launch_date
    AND CAST(w.term_date AS DATE) <= p.august_cutoff_date
  GROUP BY 1
)
SELECT
  p.survey_launch_date,
  p.baseline_snapshot,
  p.august_cutoff_date,
  COUNT(*) AS baseline_distinct_employee_count,
  SUM(CASE WHEN b.snapshot_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_baseline_employee_count,
  SUM(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS ytd_voluntary_exit_count,
  SUM(CASE WHEN v.event_date_count > 1 THEN 1 ELSE 0 END) AS multiple_ytd_voluntary_event_date_count,
  ROUND(
    100.0 * SUM(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END)
      / NULLIF(COUNT(*), 0),
    4
  ) AS ytd_voluntary_attrition_rate_percent
FROM baseline_rows AS b
CROSS JOIN parameters AS p
LEFT JOIN voluntary_events AS v
  ON v.employee_id = b.employee_id
GROUP BY 1, 2, 3;
