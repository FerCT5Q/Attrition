/*
  Claim: the latest Rehire comparison can be shown as two mutually exclusive
  baseline groups: Rehire and the complement, Not a rehire.

  Internal aggregate analysis only. The baseline is the active Regular cohort
  at the 24-Aug-2025 fiscal-August snapshot and the outcome is strict
  VOLUNTARY termination through 23-Aug-2026. One baseline row is reconstructed
  per employee before calculating the two group rates.
*/
WITH parameters AS (
  SELECT DATE '2025-08-24' AS baseline_snapshot_date,
         DATE '2026-08-23' AS outcome_cutoff_date
),
baseline AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    MAX(COALESCE(w.is_rehire, 0)) AS is_rehire,
    COUNT(*) AS source_row_count
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN parameters AS p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_snapshot_date
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
  GROUP BY 1
),
voluntary_events AS (
  SELECT
    CAST(employee_id AS BIGINT) AS employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
  GROUP BY 1, 2
),
outcomes AS (
  SELECT
    CASE WHEN baseline.is_rehire = 1 THEN 'Rehire' ELSE 'Not a rehire' END AS rehire_group,
    baseline.employee_id,
    baseline.source_row_count,
    MAX(CASE WHEN voluntary_events.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
  FROM baseline
  CROSS JOIN parameters AS p
  LEFT JOIN voluntary_events
    ON voluntary_events.employee_id = baseline.employee_id
   AND voluntary_events.term_date > p.baseline_snapshot_date
   AND voluntary_events.term_date <= p.outcome_cutoff_date
  GROUP BY 1, 2, 3
)
SELECT
  rehire_group,
  COUNT(*) AS baseline_employee_count,
  COUNT(DISTINCT employee_id) AS distinct_employee_count,
  SUM(voluntary_attrition_target) AS voluntary_exit_count,
  ROUND(100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS trailing_12m_voluntary_attrition_rate_percent,
  SUM(CASE WHEN source_row_count <> 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count
FROM outcomes
GROUP BY 1
ORDER BY CASE WHEN rehire_group = 'Rehire' THEN 1 ELSE 2 END;
