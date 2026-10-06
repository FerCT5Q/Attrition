/*
  Ventanas de outcome para attrition de cohortes QVoice por wave.

  Claim
  -----
  Para cada wave QVoice, el denominador de workforce se fija en el último
  snapshot mensual anterior al inicio del mes de la wave. Para Mar-2023,
  Jan-2024 y Jan-2025, el outcome es una salida cuyo term_type es exactamente
  VOLUNTARY en los 12 meses posteriores al inicio del mes de la wave.
  Jan-2026 conserva su inicio de wave exacto y el corte YTD ya validado.

  Regla de aceptación
  -------------------
  Cada wave debe tener un único snapshot de baseline por empleado, una cohorte
  de al menos 30 y, para las waves históricas, 12 meses completos de follow-up
  disponibles. Esta consulta valida sólo las ventanas y la cohorte de
  workforce; el cruce de participantes del archivo QVoice se realiza en
  memoria y únicamente devuelve agregados.
*/
WITH source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
),
waves AS (
  SELECT 'Mar-2023'::VARCHAR AS wave, DATE '2023-03-01' AS wave_month_start, DATE '2023-03-01' AS outcome_start, 'annual_12m'::VARCHAR AS outcome_type
  UNION ALL SELECT 'Jan-2024', DATE '2024-01-01', DATE '2024-01-01', 'annual_12m'
  UNION ALL SELECT 'Jan-2025', DATE '2025-01-01', DATE '2025-01-01', 'annual_12m'
  UNION ALL SELECT 'Jan-2026', DATE '2026-01-01', DATE '2026-01-07', 'ytd'
),
wave_windows AS (
  SELECT
    wave,
    wave_month_start,
    outcome_start,
    outcome_type,
    (
      SELECT MAX(CAST(w.fis_mo_end_dt AS DATE))
      FROM hrda.post_hire_monthly_worker_dtls AS w
      WHERE CAST(w.fis_mo_end_dt AS DATE) < waves.wave_month_start
    ) AS baseline_snapshot,
    source_bounds.latest_snapshot_date
  FROM waves
  CROSS JOIN source_bounds
),
parameters AS (
  SELECT
    wave,
    wave_month_start,
    outcome_start,
    outcome_type,
    baseline_snapshot,
    CASE
      WHEN outcome_type = 'annual_12m' THEN DATEADD(month, 12, outcome_start)
      ELSE latest_snapshot_date
    END AS outcome_end,
    latest_snapshot_date
  FROM wave_windows
),
baseline_rows AS (
  SELECT
    p.wave,
    w.employee_id,
    COUNT(*) AS snapshot_row_count
  FROM parameters AS p
  JOIN hrda.post_hire_monthly_worker_dtls AS w
    ON CAST(w.fis_mo_end_dt AS DATE) = p.baseline_snapshot
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2
),
voluntary_events AS (
  SELECT
    p.wave,
    w.employee_id,
    COUNT(DISTINCT CAST(w.term_date AS DATE)) AS event_date_count
  FROM parameters AS p
  JOIN hrda.post_hire_monthly_worker_dtls AS w
    ON CAST(w.term_date AS DATE) > p.outcome_start
   AND CAST(w.term_date AS DATE) <= p.outcome_end
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
)
SELECT
  p.wave,
  p.wave_month_start,
  p.outcome_start,
  p.outcome_type,
  p.baseline_snapshot,
  p.outcome_end,
  p.latest_snapshot_date,
  CASE WHEN p.outcome_end <= p.latest_snapshot_date THEN 1 ELSE 0 END AS followup_complete,
  COUNT(*) AS baseline_distinct_employee_count,
  SUM(CASE WHEN b.snapshot_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_baseline_employee_count,
  SUM(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count,
  SUM(CASE WHEN v.event_date_count > 1 THEN 1 ELSE 0 END) AS multiple_voluntary_event_date_count,
  ROUND(
    100.0 * SUM(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END)
      / NULLIF(COUNT(*), 0),
    4
  ) AS workforce_voluntary_attrition_rate_percent
FROM parameters AS p
JOIN baseline_rows AS b
  ON b.wave = p.wave
LEFT JOIN voluntary_events AS v
  ON v.wave = b.wave
 AND v.employee_id = b.employee_id
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
ORDER BY wave_month_start;
