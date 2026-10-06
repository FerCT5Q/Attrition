/*
  Slide 3: observed voluntary attrition in the 12 months ending at each
  available August workforce-snapshot cutoff.

  Definition
  - Application population: distinct linked applicants with cand_applied=1,
    employee_id, req_id and application_date populated. Requisitions are
    unique by employee within (cutoff - 12 months, cutoff].
  - Bucket: 1 / 2 / 3 / 4+ unique requisitions in the same rolling window.
  - Outcome: strict VOLUNTARY termination after the employee's first qualifying
    application in that window and no later than the August cutoff.
  - Rate: 100 * employees with that outcome / distinct linked applicants in
    the corresponding August-window bucket.

  This is a realised trailing-12-month observed attrition rate, not a
  prospective 12-month follow-up rate. It does not impute missing outcomes.

  Grain: aggregate August-cutoff x application bucket.
  Deliverable mode: internal_analysis; employee identifiers are used only in
  joins and COUNT(DISTINCT ...) and never returned.

  Acceptance rule:
  - exactly five August cutoffs (2022-2026) x four buckets are returned;
  - the four bucket denominators reconcile to total distinct applicants at
    every cutoff;
  - every counted exit occurs after the first qualifying application and on or
    before its cutoff.
*/
WITH august_cutoffs AS (
  SELECT
    CAST(fiscal_year AS INTEGER) AS cutoff_year,
    MAX(CAST(fis_mo_end_dt AS DATE)) AS august_cutoff_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fiscal_year BETWEEN 2022 AND 2026
    AND fis_mo_end_dt IS NOT NULL
    AND EXTRACT(MONTH FROM CAST(fis_mo_end_dt AS DATE)) = 8
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
  GROUP BY 1, 2, 3
),
applicant_windows AS (
  SELECT
    c.cutoff_year,
    c.august_cutoff_date,
    DATEADD(month, -12, c.august_cutoff_date) AS window_start_date,
    e.employee_id,
    MIN(e.application_date) AS first_qualifying_application_date,
    COUNT(DISTINCT e.req_id) AS unique_requisitions
  FROM august_cutoffs c
  INNER JOIN source_events e
    ON e.application_date > DATEADD(month, -12, c.august_cutoff_date)
   AND e.application_date <= c.august_cutoff_date
  GROUP BY 1, 2, 3, 4
),
bucketed_applicants AS (
  SELECT
    cutoff_year,
    august_cutoff_date,
    window_start_date,
    employee_id,
    first_qualifying_application_date,
    CASE
      WHEN unique_requisitions = 1 THEN '1'
      WHEN unique_requisitions = 2 THEN '2'
      WHEN unique_requisitions = 3 THEN '3'
      ELSE '4+'
    END AS application_bucket
  FROM applicant_windows
),
expected_buckets AS (
  SELECT '1' AS application_bucket, 1 AS bucket_order
  UNION ALL SELECT '2', 2
  UNION ALL SELECT '3', 3
  UNION ALL SELECT '4+', 4
),
voluntary_events AS (
  SELECT
    employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
  GROUP BY 1, 2
),
bucket_counts AS (
  SELECT
    b.cutoff_year,
    b.august_cutoff_date,
    b.window_start_date,
    b.application_bucket,
    COUNT(DISTINCT b.employee_id) AS distinct_applicant_count,
    COUNT(DISTINCT CASE
      WHEN v.term_date > b.first_qualifying_application_date
       AND v.term_date <= b.august_cutoff_date
      THEN b.employee_id
    END) AS voluntary_exit_count
  FROM bucketed_applicants b
  LEFT JOIN voluntary_events v
    ON v.employee_id = b.employee_id
  GROUP BY 1, 2, 3, 4
),
period_totals AS (
  SELECT
    cutoff_year,
    COUNT(DISTINCT employee_id) AS total_distinct_applicants
  FROM bucketed_applicants
  GROUP BY 1
)
SELECT
  c.cutoff_year,
  c.august_cutoff_date,
  DATEADD(month, -12, c.august_cutoff_date) AS window_start_date,
  b.application_bucket,
  b.bucket_order,
  COALESCE(x.distinct_applicant_count, 0) AS distinct_applicant_count,
  COALESCE(t.total_distinct_applicants, 0) AS total_distinct_applicants,
  COALESCE(x.voluntary_exit_count, 0) AS voluntary_exit_count,
  CASE
    WHEN COALESCE(x.distinct_applicant_count, 0) = 0 THEN NULL
    ELSE ROUND(100.0 * x.voluntary_exit_count / x.distinct_applicant_count, 2)
  END AS trailing_12m_voluntary_attrition_percent
FROM august_cutoffs c
CROSS JOIN expected_buckets b
LEFT JOIN bucket_counts x
  ON x.cutoff_year = c.cutoff_year
 AND x.application_bucket = b.application_bucket
LEFT JOIN period_totals t
  ON t.cutoff_year = c.cutoff_year
ORDER BY c.cutoff_year, b.bucket_order;
