WITH base AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    job_family,
    job_family_group
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
overall AS (
  SELECT
    COUNT(*) AS eligible_rows,
    SUM(CASE
      WHEN NULLIF(TRIM(job_family), '') IS NOT NULL
       AND NULLIF(TRIM(job_family_group), '') IS NOT NULL
      THEN 1 ELSE 0
    END) AS populated_rows,
    COUNT(DISTINCT UPPER(TRIM(job_family))) AS distinct_values,
    COUNT(DISTINCT fis_mo_end_dt) AS months_checked,
    SUM(CASE
      WHEN employee_id IS NULL OR fis_mo_end_dt IS NULL
      THEN 1 ELSE 0
    END) AS unmatched_rows,
    SUM(CASE
      WHEN job_family IS NOT NULL AND job_family <> TRIM(job_family)
      THEN 1 ELSE 0
    END)
    + SUM(CASE
      WHEN job_family_group IS NOT NULL
       AND job_family_group <> TRIM(job_family_group)
      THEN 1 ELSE 0
    END) AS whitespace_rows,
    COUNT(DISTINCT job_family)
      - COUNT(DISTINCT UPPER(TRIM(job_family))) AS family_normalization_delta,
    COUNT(DISTINCT job_family_group)
      - COUNT(DISTINCT UPPER(TRIM(job_family_group))) AS group_normalization_delta
  FROM base
),
key_counts AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    COUNT(*) AS key_rows
  FROM base
  WHERE employee_id IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY employee_id, fis_mo_end_dt
),
key_quality AS (
  SELECT
    COALESCE(SUM(CASE WHEN key_rows > 1 THEN key_rows - 1 ELSE 0 END), 0)
      AS duplicate_rows
  FROM key_counts
),
mapping_variants AS (
  SELECT
    UPPER(TRIM(job_family)) AS normalized_job_family,
    COUNT(DISTINCT UPPER(TRIM(job_family_group))) AS mapped_group_count
  FROM base
  WHERE NULLIF(TRIM(job_family), '') IS NOT NULL
    AND NULLIF(TRIM(job_family_group), '') IS NOT NULL
  GROUP BY UPPER(TRIM(job_family))
),
mapping_quality AS (
  SELECT
    COALESCE(SUM(CASE WHEN mapped_group_count > 1 THEN 1 ELSE 0 END), 0)
      AS mapping_anomaly_count
  FROM mapping_variants
)
SELECT
  overall.eligible_rows,
  overall.populated_rows,
  overall.distinct_values,
  overall.months_checked,
  overall.whitespace_rows
    + overall.family_normalization_delta
    + overall.group_normalization_delta
    + mapping_quality.mapping_anomaly_count AS anomaly_count,
  overall.eligible_rows AS join_eligible_rows,
  overall.eligible_rows - overall.unmatched_rows AS matched_rows,
  overall.unmatched_rows,
  key_quality.duplicate_rows
FROM overall
CROSS JOIN key_quality
CROSS JOIN mapping_quality
