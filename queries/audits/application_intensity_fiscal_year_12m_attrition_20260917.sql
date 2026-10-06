/*
  Slide 3 V7: distribución anual de aplicaciones y attrition voluntario a 12 meses.

  Población de distribución:
    applicant-fiscal year, con cand_applied=1, employee_id, req_id y
    application_date completos; se deduplica por employee_id + req_id + fecha.

  Población de attrition:
    aplicantes del mismo applicant-fiscal year que tienen un snapshot de cierre
    como Employee / Regular / active_status=1. El bucket de aplicaciones es el
    número de req_id únicos durante el periodo fiscal.

  Target:
    al menos una terminación con term_type='VOLUNTARY' en
    (fiscal_year_end, fiscal_year_end + 12 meses].

  Reglas:
    - No se publica una tasa si el seguimiento de 12 meses no está completo.
    - Si el denominador elegible es cero, la tasa es NULL y el estado es
      'not_estimable_zero_denominator'; nunca se imputa 0%.
    - El resultado contiene sólo agregados; no devuelve filas de empleados ni
      identificadores.
  Reporting mode: internal_analysis para el artefacto V7 autorizado.
*/
WITH fiscal_calendar AS (
  SELECT
    CAST(fiscal_year AS INTEGER) AS fiscal_year,
    MIN(CAST(fis_mo_beg_dt AS DATE)) AS fiscal_year_start,
    MAX(CAST(fis_mo_end_dt AS DATE)) AS fiscal_year_end
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fiscal_year IS NOT NULL
    AND fis_mo_beg_dt IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY 1
),
periods AS (
  SELECT
    fiscal_year,
    fiscal_year_start,
    fiscal_year_end,
    CASE
      WHEN fiscal_year_end <= DATE '2026-09-10' THEN 'complete'
      ELSE 'partial'
    END AS period_status,
    LEAST(fiscal_year_end, DATE '2026-09-10') AS observed_period_end
  FROM fiscal_calendar
  WHERE fiscal_year BETWEEN 2022 AND 2026
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
applicant_year AS (
  SELECT
    p.fiscal_year,
    p.fiscal_year_start,
    p.fiscal_year_end,
    p.observed_period_end,
    p.period_status,
    e.employee_id,
    COUNT(DISTINCT e.req_id) AS unique_requisitions
  FROM periods p
  INNER JOIN source_events e
    ON e.application_date >= p.fiscal_year_start
   AND e.application_date <= p.observed_period_end
  GROUP BY 1, 2, 3, 4, 5, 6
),
bucketed_applicants AS (
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
  FROM applicant_year
),
expected_buckets AS (
  SELECT '1' AS application_bucket, 1 AS bucket_order
  UNION ALL SELECT '2', 2
  UNION ALL SELECT '3', 3
  UNION ALL SELECT '4+', 4
),
distribution_counts AS (
  SELECT
    fiscal_year,
    application_bucket,
    COUNT(DISTINCT employee_id) AS distinct_applicants
  FROM bucketed_applicants
  GROUP BY 1, 2
),
distribution_totals AS (
  SELECT fiscal_year, COUNT(DISTINCT employee_id) AS annual_distinct_applicants
  FROM bucketed_applicants
  GROUP BY 1
),
period_end_worker_snapshot AS (
  SELECT
    p.fiscal_year,
    p.fiscal_year_end,
    w.employee_id,
    w.active_status,
    w.worker_type,
    w.employee_type,
    ROW_NUMBER() OVER (
      PARTITION BY p.fiscal_year, w.employee_id
      ORDER BY CAST(w.fis_mo_end_dt AS DATE) DESC
    ) AS snapshot_rank
  FROM periods p
  INNER JOIN hrda.post_hire_monthly_worker_dtls w
    ON CAST(w.fis_mo_end_dt AS DATE) <= p.fiscal_year_end
  WHERE w.fis_mo_end_dt IS NOT NULL
    AND CAST(w.fis_mo_end_dt AS DATE) <= DATE '2026-09-10'
),
active_period_end_applicants AS (
  SELECT
    b.fiscal_year,
    b.fiscal_year_end,
    b.employee_id,
    b.application_bucket
  FROM bucketed_applicants b
  INNER JOIN period_end_worker_snapshot w
    ON w.fiscal_year = b.fiscal_year
   AND w.employee_id = b.employee_id
   AND w.snapshot_rank = 1
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
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
attrition_bucket_counts AS (
  SELECT
    a.fiscal_year,
    a.application_bucket,
    COUNT(DISTINCT a.employee_id) AS attrition_eligible_applicants,
    COUNT(DISTINCT CASE
      WHEN v.employee_id IS NOT NULL
       AND v.term_date > a.fiscal_year_end
       AND v.term_date <= DATEADD(month, 12, a.fiscal_year_end)
      THEN a.employee_id END
    ) AS voluntary_exits
  FROM active_period_end_applicants a
  LEFT JOIN voluntary_events v
    ON v.employee_id = a.employee_id
  GROUP BY 1, 2
),
followup AS (
  SELECT
    p.fiscal_year,
    p.fiscal_year_start,
    p.fiscal_year_end,
    p.observed_period_end,
    p.period_status,
    MAX(CAST(w.fis_mo_end_dt AS DATE)) AS latest_observed_snapshot,
    CASE
      WHEN MAX(CAST(w.fis_mo_end_dt AS DATE)) >= DATEADD(month, 12, p.fiscal_year_end)
        THEN 'complete_12m_followup'
      ELSE 'not_estimable_incomplete_12m_followup'
    END AS followup_status
  FROM periods p
  CROSS JOIN hrda.post_hire_monthly_worker_dtls w
  WHERE w.fis_mo_end_dt IS NOT NULL
    AND CAST(w.fis_mo_end_dt AS DATE) <= DATE '2026-09-10'
  GROUP BY 1, 2, 3, 4, 5
),
period_bucket_matrix AS (
  SELECT
    p.fiscal_year,
    p.fiscal_year_start,
    p.fiscal_year_end,
    p.observed_period_end,
    p.period_status,
    p.latest_observed_snapshot,
    p.followup_status,
    b.application_bucket,
    b.bucket_order,
    COALESCE(d.distinct_applicants, 0) AS distinct_applicants,
    t.annual_distinct_applicants,
    COALESCE(a.attrition_eligible_applicants, 0) AS attrition_eligible_applicants,
    CASE
      WHEN p.followup_status = 'complete_12m_followup'
        THEN COALESCE(a.voluntary_exits, 0)
      ELSE NULL
    END AS voluntary_exits
  FROM followup p
  CROSS JOIN expected_buckets b
  LEFT JOIN distribution_counts d
    ON d.fiscal_year = p.fiscal_year
   AND d.application_bucket = b.application_bucket
  INNER JOIN distribution_totals t
    ON t.fiscal_year = p.fiscal_year
  LEFT JOIN attrition_bucket_counts a
    ON a.fiscal_year = p.fiscal_year
   AND a.application_bucket = b.application_bucket
)
SELECT
  fiscal_year,
  fiscal_year_start,
  fiscal_year_end,
  observed_period_end,
  period_status,
  latest_observed_snapshot,
  followup_status,
  application_bucket,
  bucket_order,
  distinct_applicants,
  annual_distinct_applicants,
  ROUND(100.0 * distinct_applicants / NULLIF(annual_distinct_applicants, 0), 2) AS distribution_percent,
  attrition_eligible_applicants,
  voluntary_exits,
  CASE
    WHEN followup_status <> 'complete_12m_followup' THEN NULL
    WHEN attrition_eligible_applicants = 0 THEN NULL
    ELSE ROUND(100.0 * voluntary_exits / NULLIF(attrition_eligible_applicants, 0), 2)
  END AS attrition_rate_percent,
  CASE
    WHEN followup_status <> 'complete_12m_followup' THEN 'not_estimable_incomplete_12m_followup'
    WHEN attrition_eligible_applicants = 0 THEN 'not_estimable_zero_denominator'
    ELSE 'publish'
  END AS publication_status
FROM period_bucket_matrix
ORDER BY fiscal_year, bucket_order;
