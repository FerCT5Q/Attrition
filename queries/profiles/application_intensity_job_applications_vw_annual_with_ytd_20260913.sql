-- Annual and partial-year descriptive distribution from hrda.job_applications_vw.
-- Reporting mode: internal_analysis under the named 2026-09-13 collaboration
-- authorization. The query returns aggregate rows for all periods so the
-- internal artifact can inspect sub-threshold buckets; presentation consumers
-- must still apply the standard n>=30 gate. FY2026 is partial through the
-- source cutoff.
-- Population: distinct linked applicants with cand_applied=1 and non-null
-- employee_id, req_id and application_date.
-- Grain: employee + fiscal period, deduplicated by employee_id + req_id.
-- This distribution is not a rate over the regular-employee workforce.
WITH fiscal_calendar AS (
  SELECT
    CAST(fiscal_year AS VARCHAR(32)) AS fiscal_year,
    MIN(CAST(fis_mo_beg_dt AS DATE)) AS fiscal_year_start,
    MAX(CAST(fis_mo_end_dt AS DATE)) AS fiscal_year_end
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fiscal_year IS NOT NULL
    AND fis_mo_beg_dt IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY 1
),
source_events AS (
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
source_bounds AS (
  SELECT
    MIN(application_date) AS source_first_application_date,
    MAX(application_date) AS source_last_application_date
  FROM source_events
),
periods AS (
  SELECT
    c.fiscal_year,
    c.fiscal_year_start,
    c.fiscal_year_end,
    b.source_first_application_date,
    b.source_last_application_date,
    CASE
      WHEN c.fiscal_year_start >= b.source_first_application_date
       AND c.fiscal_year_end <= b.source_last_application_date
        THEN 'complete'
      ELSE 'partial'
    END AS period_status,
    LEAST(c.fiscal_year_end, b.source_last_application_date) AS observed_period_end
  FROM fiscal_calendar AS c
  CROSS JOIN source_bounds AS b
  WHERE c.fiscal_year_end >= b.source_first_application_date
    AND c.fiscal_year_start <= b.source_last_application_date
),
applicant_period AS (
  SELECT
    p.fiscal_year,
    p.fiscal_year_start,
    p.fiscal_year_end,
    p.observed_period_end,
    p.period_status,
    e.employee_id,
    COUNT(DISTINCT e.req_id) AS unique_requisitions
  FROM periods AS p
  INNER JOIN source_events AS e
    ON e.application_date >= p.fiscal_year_start
   AND e.application_date <= p.observed_period_end
  GROUP BY 1, 2, 3, 4, 5, 6
),
bucketed AS (
  SELECT
    fiscal_year,
    fiscal_year_start,
    fiscal_year_end,
    observed_period_end,
    period_status,
    employee_id,
    unique_requisitions,
    CASE
      WHEN unique_requisitions = 1 THEN '1'
      WHEN unique_requisitions = 2 THEN '2'
      WHEN unique_requisitions = 3 THEN '3'
      ELSE '4+'
    END AS application_bucket
  FROM applicant_period
),
period_summary AS (
  SELECT
    fiscal_year,
    fiscal_year_start,
    fiscal_year_end,
    observed_period_end,
    period_status,
    COUNT(*) AS annual_distinct_applicants,
    ROUND(AVG(unique_requisitions::DECIMAL(18, 4)), 2) AS mean_unique_requisitions_per_applicant,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY unique_requisitions), 2) AS median_unique_requisitions_per_applicant
  FROM bucketed
  GROUP BY 1, 2, 3, 4, 5
),
expected_buckets AS (
  SELECT '1' AS application_bucket, 1 AS bucket_order
  UNION ALL SELECT '2', 2
  UNION ALL SELECT '3', 3
  UNION ALL SELECT '4+', 4
),
bucket_counts AS (
  SELECT fiscal_year, application_bucket, COUNT(*) AS distinct_applicants
  FROM bucketed
  GROUP BY 1, 2
),
period_bucket_counts AS (
  SELECT
    p.fiscal_year,
    p.fiscal_year_start,
    p.fiscal_year_end,
    p.observed_period_end,
    p.period_status,
    b.application_bucket,
    b.bucket_order,
    COALESCE(c.distinct_applicants, 0) AS distinct_applicants
  FROM periods AS p
  CROSS JOIN expected_buckets AS b
  LEFT JOIN bucket_counts AS c
    ON c.fiscal_year = p.fiscal_year
   AND c.application_bucket = b.application_bucket
),
publication AS (
  SELECT
    fiscal_year,
    MIN(distinct_applicants) AS minimum_bucket_n,
    CASE WHEN MIN(distinct_applicants) >= 30 THEN 'publishable' ELSE 'suppressed_below_n30' END AS publication_status
  FROM period_bucket_counts
  GROUP BY 1
)
SELECT
  y.fiscal_year,
  y.fiscal_year_start,
  y.fiscal_year_end,
  y.observed_period_end,
  y.period_status,
  y.application_bucket,
  y.bucket_order,
  y.distinct_applicants,
  s.annual_distinct_applicants,
  ROUND(100.0 * y.distinct_applicants / NULLIF(s.annual_distinct_applicants, 0), 2) AS percent_of_period_applicants,
  s.mean_unique_requisitions_per_applicant,
  s.median_unique_requisitions_per_applicant,
  p.minimum_bucket_n,
  p.publication_status
FROM period_bucket_counts AS y
INNER JOIN period_summary AS s
  ON s.fiscal_year = y.fiscal_year
INNER JOIN publication AS p
  ON p.fiscal_year = y.fiscal_year
ORDER BY y.fiscal_year, y.bucket_order;
