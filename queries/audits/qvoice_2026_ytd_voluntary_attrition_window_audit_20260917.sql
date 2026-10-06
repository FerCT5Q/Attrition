/*
  Ventana común para los resultados de attrition de QVoice Jan-2026.

  Claim
  -----
  La cohorte se fija antes de conocer la respuesta de la wave (snapshot
  2025-12-28) y el outcome es una salida con term_type estrictamente
  VOLUNTARY posterior a 2026-01-07 y hasta el último snapshot disponible.

  Regla de aceptación
  -------------------
  Debe existir un único registro por empleado en la cohorte activa Regular,
  la fecha de corte debe ser posterior a la wave y las salidas voluntarias no
  pueden exceder la cohorte. La consulta es sólo de control agregado: las
  membresías de cada visual se unen en memoria y nunca se persisten aquí.
*/
WITH source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
),
parameters AS (
  SELECT
    DATE '2026-01-07' AS survey_launch_date,
    DATE '2025-12-28' AS baseline_snapshot,
    latest_snapshot_date
  FROM source_bounds
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
    AND CAST(w.term_date AS DATE) <= p.latest_snapshot_date
  GROUP BY 1
)
SELECT
  p.survey_launch_date,
  p.baseline_snapshot,
  p.latest_snapshot_date,
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
