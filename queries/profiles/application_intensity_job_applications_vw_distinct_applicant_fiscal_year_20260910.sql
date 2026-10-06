/*
  Distribución descriptiva de intensidad de solicitudes por solicitante-año
  fiscal usando hrda.job_applications_vw.

  Población: solicitantes distintos con cand_applied = 1 y employee_id, req_id
  y application_date presentes. Grain: solicitante-año fiscal; se deduplica
  por employee_id + fiscal_year + req_id. No es una tasa de workforce ni
  confirma ceros de solicitud.

  Regla de publicación: publicar sólo años fiscales completos dentro de los
  límites de eventos observados y cuando cada bucket 1/2/3/4+ tenga n >= 30.
*/
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
    req_id,
    CAST(application_date AS DATE) AS application_date
  FROM hrda.job_applications_vw
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
),
source_bounds AS (
  SELECT
    MIN(application_date) AS source_first_application_date,
    MAX(application_date) AS source_last_application_date
  FROM source_events
),
scoped_fiscal_years AS (
  SELECT
    c.fiscal_year,
    c.fiscal_year_start,
    c.fiscal_year_end,
    b.source_first_application_date,
    b.source_last_application_date
  FROM fiscal_calendar AS c
  CROSS JOIN source_bounds AS b
  WHERE c.fiscal_year_start >= b.source_first_application_date
    AND c.fiscal_year_end <= b.source_last_application_date
),
deduplicated_applications AS (
  SELECT
    y.fiscal_year,
    e.employee_id,
    e.req_id
  FROM source_events AS e
  INNER JOIN scoped_fiscal_years AS y
    ON e.application_date BETWEEN y.fiscal_year_start AND y.fiscal_year_end
  GROUP BY 1, 2, 3
),
applicant_year AS (
  SELECT
    fiscal_year,
    employee_id,
    COUNT(DISTINCT req_id) AS unique_requisitions
  FROM deduplicated_applications
  GROUP BY 1, 2
),
bucketed_applicants AS (
  SELECT
    fiscal_year,
    employee_id,
    unique_requisitions,
    CASE
      WHEN unique_requisitions = 1 THEN '1'
      WHEN unique_requisitions = 2 THEN '2'
      WHEN unique_requisitions = 3 THEN '3'
      ELSE '4+'
    END AS application_bucket
  FROM applicant_year
),
year_summary AS (
  SELECT
    fiscal_year,
    COUNT(*) AS annual_distinct_applicants,
    ROUND(AVG(unique_requisitions::DECIMAL(18, 4)), 2) AS mean_unique_requisitions_per_applicant,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY unique_requisitions), 2) AS median_unique_requisitions_per_applicant
  FROM bucketed_applicants
  GROUP BY 1
),
expected_buckets AS (
  SELECT '1' AS application_bucket, 1 AS bucket_order
  UNION ALL SELECT '2', 2
  UNION ALL SELECT '3', 3
  UNION ALL SELECT '4+', 4
),
bucket_counts AS (
  SELECT
    fiscal_year,
    application_bucket,
    COUNT(*) AS distinct_applicants
  FROM bucketed_applicants
  GROUP BY 1, 2
),
year_bucket_counts AS (
  SELECT
    y.fiscal_year,
    y.fiscal_year_start,
    y.fiscal_year_end,
    y.source_first_application_date,
    y.source_last_application_date,
    b.application_bucket,
    b.bucket_order,
    COALESCE(c.distinct_applicants, 0) AS distinct_applicants
  FROM scoped_fiscal_years AS y
  CROSS JOIN expected_buckets AS b
  LEFT JOIN bucket_counts AS c
    ON c.fiscal_year = y.fiscal_year
   AND c.application_bucket = b.application_bucket
),
publishable_years AS (
  SELECT fiscal_year
  FROM year_bucket_counts
  GROUP BY 1
  HAVING MIN(distinct_applicants) >= 30
)
SELECT
  y.fiscal_year,
  y.fiscal_year_start,
  y.fiscal_year_end,
  y.source_first_application_date,
  y.source_last_application_date,
  y.application_bucket,
  y.bucket_order,
  y.distinct_applicants,
  s.annual_distinct_applicants,
  ROUND(100.0 * y.distinct_applicants / NULLIF(s.annual_distinct_applicants, 0), 2) AS percent_of_annual_applicants,
  s.mean_unique_requisitions_per_applicant,
  s.median_unique_requisitions_per_applicant
FROM year_bucket_counts AS y
INNER JOIN publishable_years AS p
  ON p.fiscal_year = y.fiscal_year
INNER JOIN year_summary AS s
  ON s.fiscal_year = y.fiscal_year
ORDER BY y.fiscal_year, y.bucket_order;
