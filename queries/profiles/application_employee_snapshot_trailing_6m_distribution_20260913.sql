-- Descriptive employee-snapshot distribution proposed by Julia.
-- Reporting mode: presentation; aggregate rows only.
-- Population: regular active employees in each monthly snapshot, limited to
-- snapshots no later than source cutoff 2026-09-10 and with at least six
-- months of source history.
-- Grain: employee-snapshot monthly, published as snapshot-date x category.
-- Window: (snapshot_date - 6 months, snapshot_date].
-- Classification:
--   0 = zero unique requisitions and time-safe source coverage exists;
--   1 = one unique requisition;
--   2+ = two or more unique requisitions;
--   Unknown = no usable qualified event is observable by the snapshot.
-- A missing linkage is never imputed to zero.
WITH raw_snapshots AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS VARCHAR(32)) AS fiscal_year,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) <= DATE '2026-09-10'
),
snapshots AS (
  SELECT snapshot_date, fiscal_year, employee_id
  FROM raw_snapshots
  GROUP BY 1, 2, 3
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
  SELECT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id
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
    MIN(application_date) AS first_qualified_application_date
  FROM qualified_events
  GROUP BY 1
),
employee_snapshot_counts AS (
  SELECT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id,
    CASE
      WHEN l.first_qualified_application_date IS NULL
        OR l.first_qualified_application_date > s.snapshot_date
        THEN 'Unknown'
      WHEN COUNT(DISTINCT e.req_id) = 0 THEN '0'
      WHEN COUNT(DISTINCT e.req_id) = 1 THEN '1'
      ELSE '2+'
    END AS application_bucket,
    CASE
      WHEN l.first_qualified_application_date IS NOT NULL
        AND l.first_qualified_application_date <= s.snapshot_date THEN 1
      ELSE 0
    END AS coverage_observed
  FROM eligible_snapshots AS s
  LEFT JOIN employee_linkage AS l
    ON l.employee_id = s.employee_id
  LEFT JOIN qualified_events AS e
    ON e.employee_id = s.employee_id
   AND e.application_date > DATEADD(month, -6, s.snapshot_date)
   AND e.application_date <= s.snapshot_date
  GROUP BY 1, 2, 3, l.first_qualified_application_date
),
snapshot_summary AS (
  SELECT
    snapshot_date,
    fiscal_year,
    COUNT(*) AS eligible_employee_snapshots,
    SUM(CASE WHEN application_bucket <> 'Unknown' THEN 1 ELSE 0 END) AS observed_employee_snapshots,
    SUM(CASE WHEN application_bucket = 'Unknown' THEN 1 ELSE 0 END) AS unknown_employee_snapshots
  FROM employee_snapshot_counts
  GROUP BY 1, 2
),
bucket_counts AS (
  SELECT
    snapshot_date,
    fiscal_year,
    application_bucket,
    COUNT(*) AS employee_snapshots
  FROM employee_snapshot_counts
  GROUP BY 1, 2, 3
),
expected_buckets AS (
  SELECT '0' AS application_bucket
  UNION ALL SELECT '1'
  UNION ALL SELECT '2+'
  UNION ALL SELECT 'Unknown'
)
SELECT
  s.snapshot_date,
  s.fiscal_year,
  b.application_bucket,
  COALESCE(c.employee_snapshots, 0) AS employee_snapshots,
  s.eligible_employee_snapshots,
  s.observed_employee_snapshots,
  s.unknown_employee_snapshots,
  ROUND(100.0 * COALESCE(c.employee_snapshots, 0) / NULLIF(s.eligible_employee_snapshots, 0), 4) AS percent_of_eligible_snapshots,
  ROUND(100.0 * s.observed_employee_snapshots / NULLIF(s.eligible_employee_snapshots, 0), 4) AS coverage_percent,
  ROUND(100.0 * s.unknown_employee_snapshots / NULLIF(s.eligible_employee_snapshots, 0), 4) AS unknown_percent,
  'Qualified cand_applied=1 event, deduplicated employee_id + req_id + application_date, no event after snapshot.' AS source_rule
FROM snapshot_summary AS s
CROSS JOIN expected_buckets AS b
LEFT JOIN bucket_counts AS c
  ON c.snapshot_date = s.snapshot_date
 AND c.fiscal_year = s.fiscal_year
 AND c.application_bucket = b.application_bucket
ORDER BY s.snapshot_date, CASE b.application_bucket WHEN '0' THEN 1 WHEN '1' THEN 2 WHEN '2+' THEN 3 ELSE 4 END;
