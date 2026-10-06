/*
  Ventana retrospectiva de 12 meses para el slide 26 de QVoice.

  Claim
  -----
  La cohorte heartbeat se evalua contra attrition voluntario en la ventana
  movil que termina en el ultimo snapshot de agosto de 2026. La cohorte de
  referencia se fija en el snapshot activo Regular anterior a la wave Jan-2026.

  Regla de aceptacion
  -------------------
  El corte de agosto debe existir, la ventana debe tener 12 meses, el snapshot
  baseline debe tener una sola fila por empleado y la tasa agregada debe
  reconciliar como salidas voluntarias distintas entre el denominador.

  Las membresias del grupo heartbeat se unen en memoria y no se persisten.
*/
WITH august_cutoff AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS august_cutoff_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fiscal_year AS INTEGER) = 2026
    AND EXTRACT(MONTH FROM CAST(fis_mo_end_dt AS DATE)) = 8
),
parameters AS (
  SELECT
    DATEADD(month, -12, august_cutoff_date) AS window_start,
    august_cutoff_date,
    DATE '2025-12-28' AS baseline_snapshot
  FROM august_cutoff
),
baseline_rows AS (
  SELECT
    w.employee_id,
    COUNT(*) AS baseline_row_count
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
    AND CAST(w.term_date AS DATE) > p.window_start
    AND CAST(w.term_date AS DATE) <= p.august_cutoff_date
  GROUP BY 1
)
SELECT
  p.window_start,
  p.august_cutoff_date,
  p.baseline_snapshot,
  COUNT(*) AS baseline_distinct_employee_count,
  SUM(CASE WHEN b.baseline_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_baseline_employee_count,
  SUM(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count,
  SUM(CASE WHEN v.event_date_count > 1 THEN 1 ELSE 0 END) AS multiple_voluntary_event_date_count,
  ROUND(
    100.0 * SUM(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END)
      / NULLIF(COUNT(*), 0),
    4
  ) AS trailing_12m_voluntary_attrition_rate_percent
FROM baseline_rows AS b
CROSS JOIN parameters AS p
LEFT JOIN voluntary_events AS v
  ON v.employee_id = b.employee_id
GROUP BY 1, 2, 3;
