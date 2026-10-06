/*
  V7 scoped-population preflight.

  Claim: all V7 workforce calculations can use a reproducible employee-snapshot
  population that excludes RF360 and the `Other Eng` Critical Tech segment.

  Population rule at every employee snapshot:
    worker_type = 'Employee'
    employee_type = 'Regular'
    active_status = 1
    is_rf360_yes_no = 0
    normalized job_family matches exactly one normalized
      hrda.critical_tech.extended_job_family
    critical_tech.seg <> 'Other Eng'

  Output is aggregate-only. The first section validates catalogue uniqueness;
  the second profiles the scoped population for every complete annual-follow-up
  snapshot. No employee identifiers or row-level values are returned.

  Acceptance rule:
    1. zero catalogue family-to-seg contradictions;
    2. every eligible snapshot has a positive scoped population;
    3. only `is_rf360_yes_no = 0` enters the scoped population.
*/
WITH source_bounds AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
complete_snapshot_dates AS (
    SELECT snapshot_date
    FROM (
        SELECT
            CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
            ROW_NUMBER() OVER (ORDER BY CAST(fis_mo_end_dt AS DATE) DESC) AS recency_rank
        FROM hrda.post_hire_monthly_worker_dtls
        CROSS JOIN source_bounds
        WHERE fis_mo_end_dt IS NOT NULL
          AND CAST(fis_mo_end_dt AS DATE) <= DATEADD(month, -12, latest_snapshot_date)
        GROUP BY 1
    ) dates
    WHERE recency_rank <= 24
),
catalogue_raw AS (
    SELECT
        LOWER(TRIM(extended_job_family)) AS normalized_job_family,
        NULLIF(TRIM(seg), '') AS seg
    FROM hrda.critical_tech
    WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
),
catalogue_mapping AS (
    SELECT
        normalized_job_family,
        MAX(seg) AS seg,
        COUNT(DISTINCT seg) AS distinct_seg_count
    FROM catalogue_raw
    GROUP BY 1
),
catalogue_quality AS (
    SELECT
        COUNT(*) AS catalogue_job_families,
        SUM(CASE WHEN seg IS NULL THEN 1 ELSE 0 END) AS catalogue_missing_seg_families,
        SUM(CASE WHEN distinct_seg_count > 1 THEN 1 ELSE 0 END) AS catalogue_conflicting_seg_families
    FROM catalogue_mapping
),
regular_snapshots AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        w.employee_id,
        MAX(w.is_rf360_yes_no) AS is_rf360_yes_no,
        MAX(LOWER(TRIM(w.job_family))) AS normalized_job_family
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN complete_snapshot_dates AS d
        ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
    GROUP BY 1, 2
),
scoped_snapshots AS (
    SELECT
        r.snapshot_date,
        r.employee_id
    FROM regular_snapshots AS r
    INNER JOIN catalogue_mapping AS c
        ON c.normalized_job_family = r.normalized_job_family
       AND c.distinct_seg_count = 1
       AND c.seg <> 'Other Eng'
    WHERE r.is_rf360_yes_no = 0
),
rf360_domain AS (
    SELECT
        CASE
            WHEN is_rf360_yes_no = 0 THEN '0'
            WHEN is_rf360_yes_no = 1 THEN '1'
            WHEN is_rf360_yes_no IS NULL THEN 'NULL'
            ELSE 'other integer'
        END AS value_label,
        COUNT(*) AS employee_snapshot_count
    FROM regular_snapshots
    GROUP BY 1
),
snapshot_counts AS (
    SELECT
        r.snapshot_date,
        COUNT(*) AS active_regular_employee_snapshots,
        SUM(CASE WHEN r.is_rf360_yes_no = 0 THEN 1 ELSE 0 END) AS non_rf360_employee_snapshots,
        COUNT(s.employee_id) AS scoped_critical_tech_employee_snapshots
    FROM regular_snapshots AS r
    LEFT JOIN scoped_snapshots AS s
        ON s.snapshot_date = r.snapshot_date
       AND s.employee_id = r.employee_id
    GROUP BY 1
)
SELECT
    'catalogue_quality' AS result_group,
    'all_complete_snapshots' AS result_key,
    catalogue_job_families AS metric_1,
    catalogue_missing_seg_families AS metric_2,
    catalogue_conflicting_seg_families AS metric_3
FROM catalogue_quality

UNION ALL

SELECT
    'rf360_domain' AS result_group,
    value_label AS result_key,
    employee_snapshot_count AS metric_1,
    CAST(NULL AS BIGINT) AS metric_2,
    CAST(NULL AS BIGINT) AS metric_3
FROM rf360_domain

UNION ALL

SELECT
    'snapshot_scope' AS result_group,
    CAST(snapshot_date AS VARCHAR(32)) AS result_key,
    active_regular_employee_snapshots AS metric_1,
    non_rf360_employee_snapshots AS metric_2,
    scoped_critical_tech_employee_snapshots AS metric_3
FROM snapshot_counts

ORDER BY result_group, result_key;
