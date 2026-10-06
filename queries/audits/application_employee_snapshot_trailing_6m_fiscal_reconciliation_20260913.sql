-- Claim: the annual view of unique requisitions per applicant reconciles to
-- the fiscal calendar and is independent from the employee-snapshot rolling
-- distribution.
-- Semantic type: fiscal temporal reconciliation.
-- Population: qualified cand_applied=1 events with non-null employee_id,
-- req_id and application_date.
-- Acceptance rule: every qualified event maps to exactly one fiscal year;
-- every fiscal year has one annual distinct-applicant total equal to the sum
-- of its four bucket counts; and the published set applies the n>=30 rule.
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
event_mapping AS (
  SELECT
    e.employee_id,
    e.req_id,
    e.application_date,
    COUNT(c.fiscal_year) AS fiscal_year_matches,
    MIN(c.fiscal_year) AS fiscal_year
  FROM source_events AS e
  LEFT JOIN fiscal_calendar AS c
    ON e.application_date BETWEEN c.fiscal_year_start AND c.fiscal_year_end
  GROUP BY 1, 2, 3
),
applicant_year AS (
  SELECT
    fiscal_year,
    employee_id,
    COUNT(DISTINCT req_id) AS unique_requisitions
  FROM event_mapping
  WHERE fiscal_year_matches = 1
  GROUP BY 1, 2
),
bucketed AS (
  SELECT
    fiscal_year,
    employee_id,
    CASE
      WHEN unique_requisitions = 1 THEN '1'
      WHEN unique_requisitions = 2 THEN '2'
      WHEN unique_requisitions = 3 THEN '3'
      ELSE '4+'
    END AS application_bucket
  FROM applicant_year
),
year_totals AS (
  SELECT
    fiscal_year,
    COUNT(*) AS annual_distinct_applicants,
    COUNT(DISTINCT employee_id) AS bucket_sum
  FROM bucketed
  GROUP BY 1
),
expected_buckets AS (
  SELECT fiscal_year, '1' AS application_bucket FROM year_totals
  UNION ALL SELECT fiscal_year, '2' FROM year_totals
  UNION ALL SELECT fiscal_year, '3' FROM year_totals
  UNION ALL SELECT fiscal_year, '4+' FROM year_totals
),
bucket_counts AS (
  SELECT fiscal_year, application_bucket, COUNT(*) AS bucket_count
  FROM bucketed
  GROUP BY 1, 2
),
year_publishability AS (
  SELECT
    y.fiscal_year,
    y.annual_distinct_applicants,
    y.bucket_sum,
    MIN(COALESCE(bc.bucket_count, 0)) AS minimum_bucket_count,
    SUM(CASE WHEN COALESCE(bc.bucket_count, 0) >= 30 THEN 1 ELSE 0 END) AS buckets_at_or_above_minimum
  FROM year_totals AS y
  INNER JOIN expected_buckets AS eb
    ON eb.fiscal_year = y.fiscal_year
  LEFT JOIN bucket_counts AS bc
    ON bc.fiscal_year = eb.fiscal_year
   AND bc.application_bucket = eb.application_bucket
  GROUP BY 1, 2, 3
),
mapping_stats AS (
  SELECT
    COUNT(*) AS qualified_event_keys,
    SUM(CASE WHEN fiscal_year_matches = 1 THEN 1 ELSE 0 END) AS exactly_mapped_event_keys,
    SUM(CASE WHEN fiscal_year_matches = 0 THEN 1 ELSE 0 END) AS unmapped_event_keys,
    SUM(CASE WHEN fiscal_year_matches > 1 THEN 1 ELSE 0 END) AS multi_mapped_event_keys,
    COUNT(DISTINCT fiscal_year) AS fiscal_years_checked
  FROM event_mapping
),
year_stats AS (
  SELECT
    COUNT(*) AS fiscal_years_reconciled,
    SUM(CASE WHEN annual_distinct_applicants <> bucket_sum THEN 1 ELSE 0 END) AS fiscal_year_total_mismatches,
    SUM(CASE WHEN buckets_at_or_above_minimum = 4 THEN 1 ELSE 0 END) AS publishable_fiscal_years,
    SUM(CASE WHEN buckets_at_or_above_minimum < 4 THEN 1 ELSE 0 END) AS suppressed_fiscal_years,
    MIN(minimum_bucket_count) AS minimum_bucket_count_observed
  FROM year_publishability
)
SELECT
  mapping_stats.qualified_event_keys,
  mapping_stats.exactly_mapped_event_keys,
  mapping_stats.unmapped_event_keys,
  mapping_stats.multi_mapped_event_keys,
  mapping_stats.fiscal_years_checked,
  year_stats.fiscal_years_reconciled,
  year_stats.fiscal_year_total_mismatches,
  year_stats.publishable_fiscal_years,
  year_stats.suppressed_fiscal_years,
  year_stats.minimum_bucket_count_observed
FROM mapping_stats
CROSS JOIN year_stats;
