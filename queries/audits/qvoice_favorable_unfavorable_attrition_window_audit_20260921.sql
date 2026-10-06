/*
  Ventanas de outcome para las cohortes Favorable / No favorable de QVoice.

  Claim
  -----
  Para las waves Jan-2024 y Jan-2025, la cohorte se fija en el último
  snapshot mensual activo Regular anterior al inicio de la wave y el outcome
  es una terminación con term_type exactamente VOLUNTARY en los 12 meses
  posteriores. Jan-2026 conserva el snapshot pre-wave y mide sólo YTD hasta
  el último snapshot disponible; no se anualiza.

  Regla de aceptación
  -------------------
  Cada ventana debe tener una única fila baseline por employee_id, una cohorte
  de workforce >= 30 y follow-up completo para 2024 y 2025. El cruce de
  participantes y grupos se hace en memoria; las llaves no se guardan en SQL
  ni en los artefactos publicados.
*/
WITH source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
),
waves AS (
  SELECT 2024::INTEGER AS survey_year, DATE '2024-01-01' AS wave_month_start,
         DATE '2024-01-01' AS outcome_start, 'annual_12m'::VARCHAR AS outcome_type
  UNION ALL
  SELECT 2025, DATE '2025-01-01', DATE '2025-01-01', 'annual_12m'
  UNION ALL
  SELECT 2026, DATE '2026-01-01', DATE '2026-01-07', 'ytd'
),
windows AS (
  SELECT
    w.survey_year,
    w.outcome_type,
    w.outcome_start,
    (
      SELECT MAX(CAST(m.fis_mo_end_dt AS DATE))
      FROM hrda.post_hire_monthly_worker_dtls AS m
      WHERE CAST(m.fis_mo_end_dt AS DATE) < w.wave_month_start
    ) AS baseline_snapshot,
    CASE
      WHEN w.outcome_type = 'annual_12m' THEN DATEADD(month, 12, w.outcome_start)
      ELSE s.latest_snapshot_date
    END AS outcome_end,
    s.latest_snapshot_date
  FROM waves AS w
  CROSS JOIN source_bounds AS s
),
baseline AS (
  SELECT
    win.survey_year,
    m.employee_id,
    COUNT(*) AS baseline_row_count
  FROM windows AS win
  JOIN hrda.post_hire_monthly_worker_dtls AS m
    ON CAST(m.fis_mo_end_dt AS DATE) = win.baseline_snapshot
  WHERE m.worker_type = 'Employee'
    AND m.employee_type = 'Regular'
    AND m.active_status = 1
    AND m.employee_id IS NOT NULL
  GROUP BY 1, 2
)
SELECT
  win.survey_year,
  win.outcome_type,
  win.baseline_snapshot,
  win.outcome_start,
  win.outcome_end,
  win.latest_snapshot_date,
  CASE WHEN win.outcome_end <= win.latest_snapshot_date THEN 1 ELSE 0 END AS followup_complete,
  COUNT(*) AS baseline_distinct_employee_count,
  SUM(CASE WHEN b.baseline_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_baseline_employee_count
FROM windows AS win
JOIN baseline AS b
  ON b.survey_year = win.survey_year
GROUP BY 1, 2, 3, 4, 5, 6, 7
ORDER BY survey_year;
