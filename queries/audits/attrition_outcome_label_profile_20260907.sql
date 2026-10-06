/*
  Attrition model preflight: outcome-label profile.

  Claim:
    The voluntary attrition outcome can be identified from dated termination
    records for the regular Employee population without exposing employee rows.

  Population:
    worker_type = 'Employee' and employee_type = 'Regular'.

  Grain:
    Distinct employee / term_date / term_type termination event.

  Acceptance rule:
    At least 95% of termination events have a nonblank term_type and the
    Voluntary category has at least 30 events. This is a label-readiness check,
    not evidence of causal validity.

  Privacy:
    employee_id is used only inside COUNT(DISTINCT ...) and GROUP BY needed to
    deduplicate events. No employee-level values are returned.
*/
WITH termination_events AS (
  SELECT
    employee_id,
    CAST(term_date AS DATE) AS term_date,
    NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '') AS term_type
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND is_termed = 1
    AND term_date IS NOT NULL
  GROUP BY 1, 2, 3
),
summary AS (
  SELECT
    COUNT(*) AS total_termination_events,
    COUNT(CASE WHEN term_type IS NOT NULL THEN 1 END)
      AS labeled_termination_events,
    COUNT(CASE WHEN UPPER(term_type) = 'VOLUNTARY' THEN 1 END)
      AS voluntary_termination_events
  FROM termination_events
),
by_type AS (
  SELECT
    COALESCE(term_type, '(sin term_type)') AS term_type_label,
    COUNT(*) AS termination_event_rows,
    COUNT(DISTINCT employee_id) AS employees_with_termination,
    MIN(term_date) AS first_term_date,
    MAX(term_date) AS last_term_date
  FROM termination_events
  GROUP BY 1
)
SELECT
  by_type.term_type_label,
  by_type.termination_event_rows,
  CASE
    WHEN by_type.termination_event_rows >= 30
    THEN by_type.employees_with_termination
  END AS employees_with_termination_reportable,
  by_type.first_term_date,
  by_type.last_term_date,
  summary.total_termination_events,
  summary.labeled_termination_events,
  ROUND(
    100.0 * summary.labeled_termination_events
      / NULLIF(summary.total_termination_events, 0),
    4
  ) AS nonblank_term_type_percent,
  summary.voluntary_termination_events,
  CASE
    WHEN summary.labeled_termination_events::DECIMAL(18, 4)
      / NULLIF(summary.total_termination_events, 0) >= 0.95
     AND summary.voluntary_termination_events >= 30
    THEN 'pass'
    ELSE 'review'
  END AS label_readiness_outcome
FROM by_type
CROSS JOIN summary
ORDER BY by_type.termination_event_rows DESC;
