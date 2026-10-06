-- Claim: determine whether hrda.job_applications_vw technically reconciles
-- with the historical hrda.applications feed for the candidate event used by
-- the "Applied to a job" feature.
-- Semantic type: derived_feature input-event reconciliation.
-- Population: rows with cand_applied = 1 and non-null employee_id, req_id,
-- and application_date; this is an application-event population, not the
-- active workforce population.
-- Grain: deduplicated employee_id + application_date + req_id event key.
-- Common window: 2019-06-17 through 2025-02-11, inclusive. It begins at the
-- later source start and ends at the older source's latest observed date.
-- Acceptance rule: both directional exact-key match rates must be >= 95%.
-- Passing this technical reconciliation would not confirm source ownership,
-- internal-applicant scope, event semantics, or suitability for a time-safe
-- employee-snapshot feature; those require separate validation.
WITH old_events AS (
  SELECT
    employee_id,
    application_date,
    TRIM(req_id) AS req_id
  FROM hrda.applications
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date BETWEEN DATE '2019-06-17' AND DATE '2025-02-11'
  GROUP BY 1, 2, 3
),
new_events AS (
  SELECT
    employee_id,
    application_date,
    TRIM(req_id) AS req_id
  FROM hrda.job_applications_vw
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date BETWEEN DATE '2019-06-17' AND DATE '2025-02-11'
  GROUP BY 1, 2, 3
),
old_stats AS (
  SELECT
    COUNT(*) AS old_event_keys,
    COUNT(DISTINCT employee_id) AS old_distinct_employees,
    COUNT(DISTINCT req_id) AS old_distinct_requisitions
  FROM old_events
),
new_stats AS (
  SELECT
    COUNT(*) AS new_event_keys,
    COUNT(DISTINCT employee_id) AS new_distinct_employees,
    COUNT(DISTINCT req_id) AS new_distinct_requisitions
  FROM new_events
),
overlap AS (
  SELECT
    SUM(CASE WHEN old_events.employee_id IS NOT NULL AND new_events.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_event_keys,
    SUM(CASE WHEN old_events.employee_id IS NOT NULL AND new_events.employee_id IS NULL THEN 1 ELSE 0 END) AS old_only_event_keys,
    SUM(CASE WHEN old_events.employee_id IS NULL AND new_events.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS new_only_event_keys
  FROM old_events
  FULL OUTER JOIN new_events
    ON old_events.employee_id = new_events.employee_id
   AND old_events.application_date = new_events.application_date
   AND old_events.req_id = new_events.req_id
)
SELECT
  DATE '2019-06-17' AS common_window_start,
  DATE '2025-02-11' AS common_window_end,
  old_stats.old_event_keys,
  new_stats.new_event_keys,
  overlap.matched_event_keys,
  overlap.old_only_event_keys,
  overlap.new_only_event_keys,
  old_stats.old_distinct_employees,
  new_stats.new_distinct_employees,
  old_stats.old_distinct_requisitions,
  new_stats.new_distinct_requisitions,
  ROUND(100.0 * overlap.matched_event_keys / NULLIF(old_stats.old_event_keys, 0), 4) AS old_to_new_match_rate_percent,
  ROUND(100.0 * overlap.matched_event_keys / NULLIF(new_stats.new_event_keys, 0), 4) AS new_to_old_match_rate_percent
FROM old_stats
CROSS JOIN new_stats
CROSS JOIN overlap;
