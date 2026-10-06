/*
  Critical Tech mapping audit.

  Claim:
    hrda.critical_tech is a reproducible grouped mapping from
    extended_job_family to seg and can be joined to the monthly workforce
    snapshot through job_family.

  Semantic type: grouped_mapping.
  Population for the workforce comparison:
    worker_type='Employee', employee_type='Regular', active_status=1.
  Grain:
    One distinct mapping family and one distinct workforce job-family value.

  Acceptance rule:
    - no blank mapping key or segment;
    - every mapping key maps to exactly one segment;
    - every mapping key has a normalized exact match to job_family;
    - no contradictory detailed-to-group mapping remains.

  Privacy:
    No employee-level rows or identifiers are returned. Employee identifiers
    are not selected by this audit.
*/
WITH critical_map AS (
  SELECT
    TRIM(LOWER(extended_job_family)) AS family_key,
    COUNT(*) AS mapping_rows,
    COUNT(DISTINCT NULLIF(TRIM(seg), '')) AS segment_count
  FROM hrda.critical_tech
  GROUP BY 1
),
workforce_family_domain AS (
  SELECT DISTINCT
    TRIM(LOWER(job_family)) AS family_key
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND job_family IS NOT NULL
    AND TRIM(job_family) <> ''
),
mapping_metrics AS (
  SELECT
    COUNT(*) AS detailed_values_checked,
    COUNT(*) AS comparable_count,
    SUM(
      CASE WHEN c.family_key IS NOT NULL AND c.family_key <> ''
             AND c.segment_count = 1
           THEN 1 ELSE 0 END
    ) AS mapped_values_count,
    SUM(CASE WHEN c.segment_count > 1 THEN 1 ELSE 0 END)
      AS contradiction_count,
    SUM(
      CASE WHEN c.family_key IS NULL OR c.family_key = '' OR c.segment_count = 0
           THEN 1 ELSE 0 END
    ) AS blank_mapping_count,
    SUM(CASE WHEN w.family_key IS NULL THEN 1 ELSE 0 END)
      AS unmapped_count,
    ROUND(
      100.0 * SUM(CASE WHEN c.segment_count = 1 THEN 1 ELSE 0 END)
      / NULLIF(COUNT(*), 0),
      4
    ) AS mapping_stability_percent,
    ROUND(
      100.0 * SUM(CASE WHEN w.family_key IS NOT NULL THEN 1 ELSE 0 END)
      / NULLIF(COUNT(*), 0),
      4
    ) AS match_rate_percent
  FROM critical_map c
  LEFT JOIN workforce_family_domain w
    ON w.family_key = c.family_key
)
SELECT
  detailed_values_checked,
  comparable_count,
  mapped_values_count,
  contradiction_count,
  blank_mapping_count,
  unmapped_count,
  mapping_stability_percent,
  match_rate_percent,
  CASE
    WHEN blank_mapping_count = 0
     AND contradiction_count = 0
     AND unmapped_count = 0
     AND mapping_stability_percent = 100
    THEN 'pass'
    ELSE 'review'
  END AS outcome
FROM mapping_metrics;
