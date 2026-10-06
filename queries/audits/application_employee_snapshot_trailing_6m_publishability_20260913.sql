-- Publication gate for the employee-snapshot rolling distribution.
-- The query is an aggregate diagnostic: exact bucket counts are used only to
-- decide whether a snapshot is publishable. A snapshot is publishable only
-- when 0, 1, 2+ and Unknown each have n >= 30 and the four buckets reconcile
-- to the eligible employee-snapshot denominator.
WITH raw_snapshots AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id
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
  SELECT employee_id, TRIM(req_id) AS req_id, CAST(application_date AS DATE) AS application_date
  FROM hrda.job_applications_vw
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
    AND CAST(application_date AS DATE) <= DATE '2026-09-10'
  GROUP BY 1, 2, 3
),
employee_linkage AS (
  SELECT employee_id, MIN(application_date) AS first_qualified_application_date
  FROM qualified_events
  GROUP BY 1
),
employee_snapshot_counts AS (
  SELECT
    s.snapshot_date,
    s.employee_id,
    CASE
      WHEN l.first_qualified_application_date IS NULL
        OR l.first_qualified_application_date > s.snapshot_date THEN 'Unknown'
      WHEN COUNT(DISTINCT e.req_id) = 0 THEN '0'
      WHEN COUNT(DISTINCT e.req_id) = 1 THEN '1'
      ELSE '2+'
    END AS application_bucket
  FROM eligible_snapshots AS s
  LEFT JOIN employee_linkage AS l
    ON l.employee_id = s.employee_id
  LEFT JOIN qualified_events AS e
    ON e.employee_id = s.employee_id
   AND e.application_date > DATEADD(month, -6, s.snapshot_date)
   AND e.application_date <= s.snapshot_date
  GROUP BY 1, 2, l.first_qualified_application_date
),
bucket_counts AS (
  SELECT
    snapshot_date,
    SUM(CASE WHEN application_bucket = '0' THEN 1 ELSE 0 END) AS zero_count,
    SUM(CASE WHEN application_bucket = '1' THEN 1 ELSE 0 END) AS one_count,
    SUM(CASE WHEN application_bucket = '2+' THEN 1 ELSE 0 END) AS two_plus_count,
    SUM(CASE WHEN application_bucket = 'Unknown' THEN 1 ELSE 0 END) AS unknown_count,
    COUNT(*) AS eligible_count
  FROM employee_snapshot_counts
  GROUP BY 1
),
ranked AS (
  SELECT
    snapshot_date,
    eligible_count,
    zero_count,
    one_count,
    two_plus_count,
    unknown_count,
    COUNT(*) OVER (ORDER BY snapshot_date DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS recency_rank
  FROM bucket_counts
)
SELECT
  snapshot_date,
  eligible_count,
  zero_count,
  one_count,
  two_plus_count,
  unknown_count,
  CASE
    WHEN zero_count >= 30
     AND one_count >= 30
     AND two_plus_count >= 30
     AND unknown_count >= 30
     AND zero_count + one_count + two_plus_count + unknown_count = eligible_count
      THEN 'publishable'
    ELSE 'suppressed_below_n30_or_reconciliation'
  END AS publication_status,
  recency_rank
FROM ranked
WHERE recency_rank <= 12
ORDER BY snapshot_date;
