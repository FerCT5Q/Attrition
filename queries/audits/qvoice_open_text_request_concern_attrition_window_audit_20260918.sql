/*
  Ventanas para cohortes QVoice de comentarios abiertos sobre trabajo remoto,
  híbrido y política onsite.

  Claim
  -----
  Cada cohorte se fija en el último snapshot mensual previo a la wave. Para
  Mar-2023, Jan-2024 y Jan-2025 se mide una terminación con term_type
  estrictamente VOLUNTARY durante los doce meses posteriores al inicio de la
  wave. Para Jan-2026 se mide desde el lanzamiento de la encuesta (07 Jan)
  hasta el snapshot de 23 Aug 2026; es una ventana YTD parcial, no anualizada.

  Regla de aceptación
  -------------------
  Cada baseline debe contener un único registro por empleado, al menos 30
  empleados activos Regular, y el snapshot de 23 Aug 2026 debe existir. Las
  waves históricas requieren los doce meses completos disponibles. Esta
  consulta sólo produce agregados de workforce; las membresías procedentes
  de QVoice se unen en memoria y nunca se guardan en SQL ni en resultados.
*/
WITH source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_available_snapshot
  FROM hrda.post_hire_monthly_worker_dtls
),
waves AS (
  SELECT 'Mar-2023'::VARCHAR AS wave, DATE '2023-03-01' AS wave_start,
         DATE '2023-03-01' AS outcome_start, DATE '2024-03-01' AS outcome_end,
         'annual_12m'::VARCHAR AS outcome_type
  UNION ALL
  SELECT 'Jan-2024', DATE '2024-01-01', DATE '2024-01-01', DATE '2025-01-01', 'annual_12m'
  UNION ALL
  SELECT 'Jan-2025', DATE '2025-01-01', DATE '2025-01-01', DATE '2026-01-01', 'annual_12m'
  UNION ALL
  SELECT 'Jan-2026', DATE '2026-01-01', DATE '2026-01-07', DATE '2026-08-23', 'ytd_partial'
),
baseline_dates AS (
  SELECT
    w.wave,
    w.wave_start,
    w.outcome_start,
    w.outcome_end,
    w.outcome_type,
    MAX(CAST(m.fis_mo_end_dt AS DATE)) AS baseline_snapshot
  FROM waves AS w
  JOIN hrda.post_hire_monthly_worker_dtls AS m
    ON CAST(m.fis_mo_end_dt AS DATE) < w.wave_start
  GROUP BY 1, 2, 3, 4, 5
),
august_presence AS (
  SELECT CASE
    WHEN MAX(CASE WHEN CAST(fis_mo_end_dt AS DATE) = DATE '2026-08-23' THEN 1 ELSE 0 END) = 1
      THEN 1
    ELSE 0
  END AS august_snapshot_exists
  FROM hrda.post_hire_monthly_worker_dtls
),
parameters AS (
  SELECT
    b.wave,
    b.wave_start,
    b.outcome_start,
    b.outcome_end,
    b.outcome_type,
    b.baseline_snapshot,
    s.latest_available_snapshot,
    a.august_snapshot_exists
  FROM baseline_dates AS b
  CROSS JOIN source_bounds AS s
  CROSS JOIN august_presence AS a
),
baseline_rows AS (
  SELECT
    p.wave,
    m.employee_id,
    COUNT(*) AS snapshot_row_count
  FROM parameters AS p
  JOIN hrda.post_hire_monthly_worker_dtls AS m
    ON CAST(m.fis_mo_end_dt AS DATE) = p.baseline_snapshot
  WHERE m.worker_type = 'Employee'
    AND m.employee_type = 'Regular'
    AND m.active_status = 1
    AND m.employee_id IS NOT NULL
  GROUP BY 1, 2
),
voluntary_events AS (
  SELECT
    p.wave,
    m.employee_id,
    COUNT(DISTINCT CAST(m.term_date AS DATE)) AS voluntary_event_date_count
  FROM parameters AS p
  JOIN hrda.post_hire_monthly_worker_dtls AS m
    ON CAST(m.term_date AS DATE) > p.outcome_start
   AND CAST(m.term_date AS DATE) <= p.outcome_end
  WHERE m.worker_type = 'Employee'
    AND m.employee_type = 'Regular'
    AND m.employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(m.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
)
SELECT
  p.wave,
  p.wave_start,
  p.outcome_type,
  p.baseline_snapshot,
  p.outcome_start,
  p.outcome_end,
  p.latest_available_snapshot,
  p.august_snapshot_exists,
  CASE
    WHEN p.outcome_type = 'annual_12m'
      AND p.outcome_end <= p.latest_available_snapshot THEN 1
    WHEN p.outcome_type = 'ytd_partial'
      AND p.august_snapshot_exists = 1
      AND p.outcome_end <= p.latest_available_snapshot THEN 1
    ELSE 0
  END AS followup_or_cutoff_available,
  COUNT(*) AS baseline_distinct_employee_count,
  SUM(CASE WHEN b.snapshot_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_baseline_employee_count,
  SUM(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count,
  SUM(CASE WHEN v.voluntary_event_date_count > 1 THEN 1 ELSE 0 END) AS multiple_voluntary_event_date_count,
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
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
ORDER BY p.wave_start;
