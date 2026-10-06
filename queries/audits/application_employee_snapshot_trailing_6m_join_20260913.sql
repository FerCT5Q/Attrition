-- Claim: the source can be linked to regular active employee snapshots at
-- employee-date grain without duplicate snapshot keys; absence of a prior
-- qualified event remains Unknown rather than an asserted zero.
-- Semantic type: time-safe employee-date join reconciliation.
-- Population: regular active employees in monthly snapshots whose six-month
-- lookback is available and whose snapshot date is <= 2026-09-10.
-- Grain: distinct employee_id + snapshot_date.
-- Acceptance rule: snapshot_duplicate_rows=0 and the aggregated linkage is
-- one row per employee; matched/unmatched and future-only coverage are shown
-- as separate diagnostics.
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
employee_linkage AS (
  SELECT
    employee_id,
    MIN(application_date) AS first_qualified_application_date,
    COUNT(*) AS qualified_event_key_count
  FROM qualified_events
  GROUP BY 1
),
linked_snapshots AS (
  SELECT
    s.snapshot_date,
    s.employee_id,
    l.first_qualified_application_date,
    l.qualified_event_key_count
  FROM eligible_snapshots AS s
  LEFT JOIN employee_linkage AS l
    ON l.employee_id = s.employee_id
),
linkage_stats AS (
  SELECT
    COUNT(*) AS eligible_employee_snapshots,
    SUM(CASE WHEN first_qualified_application_date IS NOT NULL
              AND first_qualified_application_date <= snapshot_date THEN 1 ELSE 0 END) AS matched_time_safe_snapshots,
    SUM(CASE WHEN first_qualified_application_date IS NULL THEN 1 ELSE 0 END) AS unmatched_snapshots,
    SUM(CASE WHEN first_qualified_application_date > snapshot_date THEN 1 ELSE 0 END) AS future_only_snapshots,
    SUM(CASE WHEN qualified_event_key_count > 1
              AND first_qualified_application_date <= snapshot_date THEN 1 ELSE 0 END) AS multi_event_linked_snapshots,
    COUNT(DISTINCT CASE WHEN first_qualified_application_date IS NOT NULL
                          AND first_qualified_application_date <= snapshot_date THEN employee_id END) AS matched_distinct_employees,
    COUNT(DISTINCT CASE WHEN first_qualified_application_date IS NULL
                          OR first_qualified_application_date > snapshot_date THEN employee_id END) AS unmatched_distinct_employees
  FROM linked_snapshots
)
SELECT
  (SELECT COUNT(*) FROM raw_snapshots) - (SELECT COUNT(*) FROM snapshots) AS snapshot_duplicate_rows,
  linkage_stats.eligible_employee_snapshots,
  linkage_stats.matched_time_safe_snapshots,
  linkage_stats.unmatched_snapshots,
  linkage_stats.future_only_snapshots,
  linkage_stats.multi_event_linked_snapshots,
  linkage_stats.matched_distinct_employees,
  linkage_stats.unmatched_distinct_employees,
  MIN(e.snapshot_date) AS first_snapshot_date,
  MAX(e.snapshot_date) AS last_snapshot_date,
  COUNT(DISTINCT e.snapshot_date) AS snapshot_dates_checked
FROM eligible_snapshots AS e
CROSS JOIN linkage_stats
GROUP BY
  linkage_stats.eligible_employee_snapshots,
  linkage_stats.matched_time_safe_snapshots,
  linkage_stats.unmatched_snapshots,
  linkage_stats.future_only_snapshots,
  linkage_stats.multi_event_linked_snapshots,
  linkage_stats.matched_distinct_employees,
  linkage_stats.unmatched_distinct_employees;
