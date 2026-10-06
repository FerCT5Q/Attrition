-- Claim: the six-month employee-snapshot calculation excludes future events,
-- includes the snapshot date, excludes the open boundary, and reconciles its
-- unique-requisition count after source-key deduplication.
-- Semantic type: derived_feature boundary and leakage audit.
-- Population/grain: regular active employee snapshots and qualified source
-- event keys through the source cutoff 2026-09-10.
-- Acceptance rule: future_event_keys_included=0, duplicate_snapshot_rows=0,
-- and count_reconciliation_mismatch_snapshots=0.
WITH raw_snapshots AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) <= DATE '2026-09-10'
),
snapshots AS (
  SELECT snapshot_date, employee_id
  FROM raw_snapshots
  GROUP BY 1, 2
),
source_bounds AS (
  SELECT
    MIN(CAST(application_date AS DATE)) AS first_application_date,
    MAX(CAST(application_date AS DATE)) AS last_application_date
  FROM hrda.job_applications_vw
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
    AND CAST(application_date AS DATE) <= DATE '2026-09-10'
),
eligible_snapshots AS (
  SELECT s.snapshot_date, s.employee_id
  FROM snapshots AS s
  CROSS JOIN source_bounds AS b
  WHERE s.snapshot_date > DATEADD(month, 6, b.first_application_date)
    AND s.snapshot_date <= b.last_application_date
),
qualified_events AS (
  SELECT
    employee_id,
    TRIM(req_id) AS req_id,
    CAST(application_date AS DATE) AS application_date
  FROM hrda.job_applications_vw
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
    AND CAST(application_date AS DATE) <= DATE '2026-09-10'
  GROUP BY 1, 2, 3
),
window_event_pairs AS (
  SELECT
    s.snapshot_date,
    s.employee_id,
    e.req_id,
    e.application_date
  FROM eligible_snapshots AS s
  INNER JOIN qualified_events AS e
    ON e.employee_id = s.employee_id
   AND e.application_date > DATEADD(month, -6, s.snapshot_date)
   AND e.application_date <= s.snapshot_date
),
direct_counts AS (
  SELECT
    snapshot_date,
    employee_id,
    COUNT(DISTINCT req_id) AS direct_unique_req_count,
    SUM(CASE WHEN application_date > snapshot_date THEN 1 ELSE 0 END) AS future_event_keys_included
  FROM window_event_pairs
  GROUP BY 1, 2
),
window_req_keys AS (
  SELECT snapshot_date, employee_id, req_id
  FROM window_event_pairs
  GROUP BY 1, 2, 3
),
deduplicated_counts AS (
  SELECT snapshot_date, employee_id, COUNT(*) AS deduplicated_unique_req_count
  FROM window_req_keys
  GROUP BY 1, 2
),
reconciliation AS (
  SELECT
    s.snapshot_date,
    s.employee_id,
    COALESCE(d.direct_unique_req_count, 0) AS direct_unique_req_count,
    COALESCE(c.deduplicated_unique_req_count, 0) AS deduplicated_unique_req_count,
    COALESCE(d.future_event_keys_included, 0) AS future_event_keys_included,
    CASE
      WHEN COALESCE(d.direct_unique_req_count, 0) = COALESCE(c.deduplicated_unique_req_count, 0)
        THEN 0
      ELSE 1
    END AS count_reconciliation_mismatch
  FROM eligible_snapshots AS s
  LEFT JOIN direct_counts AS d
    ON d.snapshot_date = s.snapshot_date
   AND d.employee_id = s.employee_id
  LEFT JOIN deduplicated_counts AS c
    ON c.snapshot_date = s.snapshot_date
   AND c.employee_id = s.employee_id
)
SELECT
  (SELECT COUNT(*) FROM raw_snapshots) - (SELECT COUNT(*) FROM snapshots) AS duplicate_snapshot_rows,
  COUNT(*) AS eligible_employee_snapshots,
  SUM(future_event_keys_included) AS future_event_keys_included,
  SUM(count_reconciliation_mismatch) AS count_reconciliation_mismatch_snapshots,
  SUM(CASE WHEN direct_unique_req_count = 0 THEN 1 ELSE 0 END) AS zero_count_snapshots,
  SUM(CASE WHEN direct_unique_req_count = 1 THEN 1 ELSE 0 END) AS one_count_snapshots,
  SUM(CASE WHEN direct_unique_req_count >= 2 THEN 1 ELSE 0 END) AS two_plus_count_snapshots,
  MIN(snapshot_date) AS first_snapshot_date,
  MAX(snapshot_date) AS last_snapshot_date,
  COUNT(DISTINCT snapshot_date) AS snapshot_dates_checked
FROM reconciliation;
