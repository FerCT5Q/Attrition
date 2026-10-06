-- Claim: quantify, but do not assume away, differences between the primary
-- monthly source and hrda.all_terminations for strict Voluntary event keys.
-- Output is one aggregate row; no employee identifiers are selected.
WITH closure_dates AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  GROUP BY 1
), last_nineteen AS (
  SELECT snapshot_date
  FROM (
    SELECT snapshot_date, ROW_NUMBER() OVER (ORDER BY snapshot_date DESC) AS reverse_sequence
    FROM closure_dates
  ) AS ranked
  WHERE reverse_sequence <= 19
), bounds AS (
  SELECT MIN(snapshot_date) AS window_start, MAX(snapshot_date) AS cutoff_date
  FROM last_nineteen
), primary_events AS (
  SELECT w.employee_id::BIGINT AS employee_key, CAST(w.term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN bounds AS b
  WHERE CAST(w.term_date AS DATE) > b.window_start
    AND CAST(w.term_date AS DATE) <= b.cutoff_date
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
), termination_events AS (
  SELECT t.employeeid::BIGINT AS employee_key, CAST(t.term_date AS DATE) AS term_date
  FROM hrda.all_terminations AS t
  CROSS JOIN bounds AS b
  WHERE CAST(t.term_date AS DATE) > b.window_start
    AND CAST(t.term_date AS DATE) <= b.cutoff_date
    AND UPPER(NULLIF(TRIM(CAST(t.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
), comparison AS (
  SELECT COALESCE(p.employee_key, a.employee_key) AS employee_key,
    COALESCE(p.term_date, a.term_date) AS term_date,
    CASE WHEN p.employee_key IS NOT NULL AND a.employee_key IS NOT NULL THEN 'matched'
         WHEN p.employee_key IS NOT NULL THEN 'primary_only'
         ELSE 'all_terminations_only' END AS reconciliation_status
  FROM primary_events AS p
  FULL OUTER JOIN termination_events AS a
    ON a.employee_key = p.employee_key
   AND a.term_date = p.term_date
)
SELECT
  (SELECT COUNT(*) FROM primary_events)::BIGINT AS primary_event_count,
  (SELECT COUNT(*) FROM termination_events)::BIGINT AS all_terminations_event_count,
  SUM(CASE WHEN reconciliation_status = 'matched' THEN 1 ELSE 0 END)::BIGINT AS matched_event_count,
  SUM(CASE WHEN reconciliation_status = 'primary_only' THEN 1 ELSE 0 END)::BIGINT AS primary_only_event_count,
  SUM(CASE WHEN reconciliation_status = 'all_terminations_only' THEN 1 ELSE 0 END)::BIGINT AS all_terminations_only_event_count,
  SUM(CASE WHEN reconciliation_status <> 'matched' THEN 1 ELSE 0 END)::BIGINT AS discrepancy_count,
  CASE WHEN (SELECT COUNT(*) FROM primary_events) > 0
       THEN SUM(CASE WHEN reconciliation_status = 'matched' THEN 1 ELSE 0 END)::DECIMAL(30,12)
          / (SELECT COUNT(*) FROM primary_events) * 100
       ELSE NULL END AS primary_match_rate_percent,
  1::BIGINT AS reconciliation_executed
FROM comparison;
