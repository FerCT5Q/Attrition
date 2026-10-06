-- Claim: the current view contains the legacy qualified event keys in the
-- common comparison window and may contain additional keys.
-- Semantic type: source reconciliation for a derived event input.
-- Reporting mode: presentation; aggregate counts only.
-- Common window: 2019-06-17 through 2025-02-11, the overlap used by the
-- historical source audit. Acceptance rule: report both directional exact-key
-- match rates; the legacy-to-new direction is expected to be complete, while
-- additional new events require lineage confirmation.
WITH old_events AS (
  SELECT employee_id, CAST(application_date AS DATE) AS application_date, TRIM(req_id) AS req_id
  FROM hrda.applications
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
    AND CAST(application_date AS DATE) BETWEEN DATE '2019-06-17' AND DATE '2025-02-11'
  GROUP BY 1, 2, 3
),
new_events AS (
  SELECT employee_id, CAST(application_date AS DATE) AS application_date, TRIM(req_id) AS req_id
  FROM hrda.job_applications_vw
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
    AND CAST(application_date AS DATE) BETWEEN DATE '2019-06-17' AND DATE '2025-02-11'
  GROUP BY 1, 2, 3
),
old_stats AS (
  SELECT COUNT(*) AS old_event_keys FROM old_events
),
new_stats AS (
  SELECT COUNT(*) AS new_event_keys FROM new_events
),
overlap AS (
  SELECT
    SUM(CASE WHEN o.employee_id IS NOT NULL AND n.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_event_keys,
    SUM(CASE WHEN o.employee_id IS NOT NULL AND n.employee_id IS NULL THEN 1 ELSE 0 END) AS old_only_event_keys,
    SUM(CASE WHEN o.employee_id IS NULL AND n.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS new_only_event_keys
  FROM old_events AS o
  FULL OUTER JOIN new_events AS n
    ON o.employee_id = n.employee_id
   AND o.application_date = n.application_date
   AND o.req_id = n.req_id
)
SELECT
  DATE '2019-06-17' AS common_window_start,
  DATE '2025-02-11' AS common_window_end,
  old_stats.old_event_keys,
  new_stats.new_event_keys,
  overlap.matched_event_keys,
  overlap.old_only_event_keys,
  overlap.new_only_event_keys,
  ROUND(100.0 * overlap.matched_event_keys / NULLIF(old_stats.old_event_keys, 0), 4) AS old_to_new_match_rate_percent,
  ROUND(100.0 * overlap.matched_event_keys / NULLIF(new_stats.new_event_keys, 0), 4) AS new_to_old_match_rate_percent
FROM old_stats
CROSS JOIN new_stats
CROSS JOIN overlap;
