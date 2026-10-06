-- Claim: the six-month Team turnover numerator can be operationalized from a
-- documented term_type domain before calculating the derived feature.
-- Semantic type: derived-feature input / event-domain audit.
-- Population: distinct termination events dated in (2026-02-23, 2026-08-23].
-- Deliverable mode: internal_analysis; aggregate categories only, n >= 30.
-- Acceptance rule: identify an explicit source value or value set that maps
-- to voluntary terminations; no inference from a column name is allowed.
WITH distinct_termination_events AS (
  SELECT
    employee_id,
    term_date,
    NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '') AS term_type
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE term_date > DATE '2026-02-23'
    AND term_date <= DATE '2026-08-23'
  GROUP BY 1, 2, 3
)
SELECT
  COALESCE(term_type, 'Missing term type') AS term_type,
  COUNT(DISTINCT employee_id) AS terminated_employees,
  COUNT(*) AS distinct_termination_events
FROM distinct_termination_events
GROUP BY 1
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY terminated_employees DESC, term_type;
