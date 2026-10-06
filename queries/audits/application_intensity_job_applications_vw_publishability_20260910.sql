/*
  Diagnóstico de publicación para la distribución de solicitudes por
  solicitante-año fiscal usando hrda.job_applications_vw.

  Devuelve sólo el estado agregado de cada año fiscal completo: no expone
  conteos de buckets que no alcanzan n >= 30. La regla de aceptación es que
  buckets_below_minimum = 0 para publicar los cuatro buckets 1/2/3/4+.
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
  SELECT employee_id, req_id, CAST(application_date AS DATE) AS application_date
  FROM hrda.job_applications_vw
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
),
source_bounds AS (
  SELECT MIN(application_date) AS source_first_application_date,
         MAX(application_date) AS source_last_application_date
  FROM source_events
),
scoped_fiscal_years AS (
  SELECT c.fiscal_year, c.fiscal_year_start, c.fiscal_year_end
  FROM fiscal_calendar AS c
  CROSS JOIN source_bounds AS b
  WHERE c.fiscal_year_start >= b.source_first_application_date
    AND c.fiscal_year_end <= b.source_last_application_date
),
applicant_year AS (
  SELECT
    y.fiscal_year,
    e.employee_id,
    COUNT(DISTINCT e.req_id) AS unique_requisitions
  FROM source_events AS e
  INNER JOIN scoped_fiscal_years AS y
    ON e.application_date BETWEEN y.fiscal_year_start AND y.fiscal_year_end
  GROUP BY 1, 2
),
bucket_counts AS (
  SELECT
    fiscal_year,
    CASE
      WHEN unique_requisitions = 1 THEN '1'
      WHEN unique_requisitions = 2 THEN '2'
      WHEN unique_requisitions = 3 THEN '3'
      ELSE '4+'
    END AS application_bucket,
    COUNT(*) AS distinct_applicants
  FROM applicant_year
  GROUP BY 1, 2
),
expected_buckets AS (
  SELECT '1' AS application_bucket
  UNION ALL SELECT '2'
  UNION ALL SELECT '3'
  UNION ALL SELECT '4+'
),
year_bucket_status AS (
  SELECT
    y.fiscal_year,
    b.application_bucket,
    COALESCE(c.distinct_applicants, 0) AS distinct_applicants
  FROM scoped_fiscal_years AS y
  CROSS JOIN expected_buckets AS b
  LEFT JOIN bucket_counts AS c
    ON c.fiscal_year = y.fiscal_year
   AND c.application_bucket = b.application_bucket
)
SELECT
  fiscal_year,
  SUM(CASE WHEN distinct_applicants < 30 THEN 1 ELSE 0 END) AS buckets_below_minimum,
  CASE
    WHEN SUM(CASE WHEN distinct_applicants < 30 THEN 1 ELSE 0 END) = 0 THEN 'publishable'
    ELSE 'suppressed_below_n30'
  END AS publication_status
FROM year_bucket_status
GROUP BY 1
ORDER BY 1;
