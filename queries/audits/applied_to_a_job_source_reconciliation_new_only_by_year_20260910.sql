-- Follow-up to applied_to_a_job_source_reconciliation_20260910.sql.
-- Claim: locate the historical timing of event keys present in
-- hrda.job_applications_vw but absent from hrda.applications.
-- Reporting mode: presentation (aggregate event counts only).
-- Population, grain, common window, and deduplication are identical to the
-- parent reconciliation query.
-- Acceptance rule: diagnostic only. If unmatched events concentrate in a
-- period, retain that period as a source-definition/coverage investigation;
-- do not infer an application-rate trend from the difference.
WITH old_events AS (
  SELECT employee_id, application_date, TRIM(req_id) AS req_id
  FROM hrda.applications
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date BETWEEN DATE '2019-06-17' AND DATE '2025-02-11'
  GROUP BY 1, 2, 3
),
new_events AS (
  SELECT employee_id, application_date, TRIM(req_id) AS req_id
  FROM hrda.job_applications_vw
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date BETWEEN DATE '2019-06-17' AND DATE '2025-02-11'
  GROUP BY 1, 2, 3
)
SELECT
  EXTRACT(YEAR FROM new_events.application_date)::INTEGER AS calendar_year,
  COUNT(*) AS new_event_keys,
  SUM(CASE WHEN old_events.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_event_keys,
  SUM(CASE WHEN old_events.employee_id IS NULL THEN 1 ELSE 0 END) AS new_only_event_keys,
  ROUND(100.0 * SUM(CASE WHEN old_events.employee_id IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS new_only_rate_percent
FROM new_events
LEFT JOIN old_events
  ON old_events.employee_id = new_events.employee_id
 AND old_events.application_date = new_events.application_date
 AND old_events.req_id = new_events.req_id
GROUP BY 1
ORDER BY 1;
