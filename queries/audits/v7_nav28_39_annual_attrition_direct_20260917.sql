/*
  V7 navigation slides 28–39: annual voluntary-attrition evidence for
  categories that are direct fields or bounded date derivations.

  Deliverable: internal_analysis, aggregate-only.
  Population: active regular employees at each historical monthly
  snapshot.  The category is assigned at the snapshot and the outcome is one
  or more strict VOLUNTARY terminations in the following 12 months.

  Publication rule applied by the evidence builder: >=30 historical employee
  snapshots and >=30 voluntary exits for each displayed category.  Rows below
  either threshold remain available only as aggregate diagnostics and render
  as "Not estimable"; no rate is imputed.

  This query deliberately excludes promotion-history, current-grade-entry,
  CEO-chain and within-team-spread features.  Those definitions need their
  own time-safe reconstruction rather than a direct-field proxy.
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
    ) ranked
    WHERE recency_rank <= 24
),
active_snapshot_raw AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.time_in_job_profile_start_date AS DATE)) AS job_profile_start_date,
        MAX(CAST(w.levelentrydate AS DATE)) AS detailed_level_start_date,
        MAX(CAST(w.original_hire_date AS DATE)) AS original_hire_date,
        MAX(CAST(w.max_hire_rehire_date AS DATE)) AS latest_hire_rehire_date,
        MAX(NULLIF(TRIM(CAST(w.level_grouped AS VARCHAR(128))), '')) AS level_grouped,
        MAX(NULLIF(TRIM(CAST(w.management_level AS VARCHAR(128))), '')) AS management_level,
        MAX(NULLIF(TRIM(CAST(w.job_level_primary_position AS VARCHAR(128))), '')) AS job_level,
        MAX(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(128))), '')) AS compensation_grade,
        MAX(w.compa_ratio) AS compa_ratio,
        MAX(w.worker_supervisory_organization_level_from_top) AS stored_manager_layer,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.time_in_job_profile_start_date AS VARCHAR(32)), '<NULL>')) AS job_profile_date_variants,
        COUNT(DISTINCT COALESCE(CAST(w.levelentrydate AS VARCHAR(32)), '<NULL>')) AS detailed_level_date_variants,
        COUNT(DISTINCT COALESCE(CAST(w.original_hire_date AS VARCHAR(32)), '<NULL>')) AS original_hire_date_variants,
        COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS latest_hire_date_variants,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.level_grouped AS VARCHAR(128))), ''), '<NULL>')) AS level_variants,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.management_level AS VARCHAR(128))), ''), '<NULL>')) AS management_level_variants,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.job_level_primary_position AS VARCHAR(128))), ''), '<NULL>')) AS job_level_variants,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(128))), ''), '<NULL>')) AS grade_variants,
        COUNT(DISTINCT COALESCE(CAST(w.compa_ratio AS VARCHAR(64)), '<NULL>')) AS compa_ratio_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN complete_snapshot_dates AS d
      ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2
),
source_quality AS (
    SELECT
        COUNT(*) AS active_employee_snapshot_count,
        COUNT(DISTINCT snapshot_date) AS snapshot_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN job_profile_date_variants > 1
                   OR detailed_level_date_variants > 1
                   OR original_hire_date_variants > 1
                   OR latest_hire_date_variants > 1
                   OR level_variants > 1
                   OR management_level_variants > 1
                   OR job_level_variants > 1
                   OR grade_variants > 1
                   OR compa_ratio_variants > 1
                 THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count
    FROM active_snapshot_raw
),
voluntary_events AS (
    SELECT
        CAST(employee_id AS BIGINT) AS employee_id,
        CAST(term_date AS DATE) AS term_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date IS NOT NULL
    GROUP BY 1, 2
),
cohort AS (
    SELECT
        s.snapshot_date,
        s.employee_id,
        s.job_profile_start_date,
        s.detailed_level_start_date,
        s.original_hire_date,
        s.latest_hire_rehire_date,
        s.level_grouped,
        s.management_level,
        s.job_level,
        s.compensation_grade,
        s.compa_ratio,
        s.stored_manager_layer,
        s.source_row_count,
        s.job_profile_date_variants,
        s.detailed_level_date_variants,
        s.original_hire_date_variants,
        s.latest_hire_date_variants,
        s.level_variants,
        s.management_level_variants,
        s.job_level_variants,
        s.grade_variants,
        s.compa_ratio_variants,
        MAX(CASE WHEN e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS annual_voluntary_attrition_target
    FROM active_snapshot_raw AS s
    LEFT JOIN voluntary_events AS e
      ON e.employee_id = s.employee_id
     AND e.term_date > s.snapshot_date
     AND e.term_date <= DATEADD(month, 12, s.snapshot_date)
    GROUP BY
        s.snapshot_date, s.employee_id, s.job_profile_start_date, s.detailed_level_start_date,
        s.original_hire_date, s.latest_hire_rehire_date, s.level_grouped, s.management_level,
        s.job_level, s.compensation_grade, s.compa_ratio, s.stored_manager_layer,
        s.source_row_count, s.job_profile_date_variants, s.detailed_level_date_variants,
        s.original_hire_date_variants, s.latest_hire_date_variants, s.level_variants,
        s.management_level_variants, s.job_level_variants, s.grade_variants, s.compa_ratio_variants
),
classified AS (
    SELECT
        snapshot_date,
        employee_id,
        job_profile_start_date,
        detailed_level_start_date,
        original_hire_date,
        latest_hire_rehire_date,
        level_grouped,
        management_level,
        job_level,
        compensation_grade,
        compa_ratio,
        stored_manager_layer,
        annual_voluntary_attrition_target,
        CASE
          WHEN job_profile_start_date IS NULL OR latest_hire_rehire_date IS NULL
            OR job_profile_start_date > snapshot_date OR latest_hire_rehire_date > snapshot_date THEN NULL
          WHEN DATEADD(year, 1, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > snapshot_date THEN '<1 year'
          WHEN DATEADD(year, 2, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > snapshot_date THEN '1–<2 years'
          WHEN DATEADD(year, 3, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > snapshot_date THEN '2–<3 years'
          WHEN DATEADD(year, 5, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > snapshot_date THEN '3–<5 years'
          WHEN DATEADD(year, 10, GREATEST(job_profile_start_date, latest_hire_rehire_date)) > snapshot_date THEN '5–<10 years'
          ELSE '10+ years'
        END AS job_profile_tenure_band,
        CASE
          WHEN detailed_level_start_date IS NULL OR latest_hire_rehire_date IS NULL OR job_level IS NULL
            OR detailed_level_start_date > snapshot_date OR latest_hire_rehire_date > snapshot_date THEN NULL
          WHEN DATEADD(year, 1, GREATEST(detailed_level_start_date, latest_hire_rehire_date)) > snapshot_date THEN '<1 year'
          WHEN DATEADD(year, 2, GREATEST(detailed_level_start_date, latest_hire_rehire_date)) > snapshot_date THEN '1–<2 years'
          WHEN DATEADD(year, 3, GREATEST(detailed_level_start_date, latest_hire_rehire_date)) > snapshot_date THEN '2–<3 years'
          WHEN DATEADD(year, 5, GREATEST(detailed_level_start_date, latest_hire_rehire_date)) > snapshot_date THEN '3–<5 years'
          WHEN DATEADD(year, 10, GREATEST(detailed_level_start_date, latest_hire_rehire_date)) > snapshot_date THEN '5–<10 years'
          ELSE '10+ years'
        END AS detailed_level_tenure_band,
        CASE
          WHEN original_hire_date IS NULL OR original_hire_date > snapshot_date THEN NULL
          WHEN DATEADD(year, 1, original_hire_date) > snapshot_date THEN '<1 year'
          WHEN DATEADD(year, 2, original_hire_date) > snapshot_date THEN '1–<2 years'
          WHEN DATEADD(year, 3, original_hire_date) > snapshot_date THEN '2–<3 years'
          WHEN DATEADD(year, 5, original_hire_date) > snapshot_date THEN '3–<5 years'
          WHEN DATEADD(year, 10, original_hire_date) > snapshot_date THEN '5–<10 years'
          ELSE '10+ years'
        END AS original_hire_tenure_band,
        CASE
          WHEN latest_hire_rehire_date IS NULL OR latest_hire_rehire_date > snapshot_date THEN NULL
          WHEN DATEADD(year, 1, latest_hire_rehire_date) > snapshot_date THEN '<1 year'
          WHEN DATEADD(year, 2, latest_hire_rehire_date) > snapshot_date THEN '1–<2 years'
          WHEN DATEADD(year, 3, latest_hire_rehire_date) > snapshot_date THEN '2–<3 years'
          WHEN DATEADD(year, 5, latest_hire_rehire_date) > snapshot_date THEN '3–<5 years'
          WHEN DATEADD(year, 10, latest_hire_rehire_date) > snapshot_date THEN '5–<10 years'
          ELSE '10+ years'
        END AS latest_hire_tenure_band,
        CASE
          WHEN compa_ratio IS NULL THEN NULL
          WHEN compa_ratio <= 0 THEN '≤ 0'
          WHEN compa_ratio < 0.8 THEN '> 0–< 0.8'
          WHEN compa_ratio < 0.9 THEN '0.8–< 0.9'
          WHEN compa_ratio < 1.0 THEN '0.9–< 1.0'
          WHEN compa_ratio < 1.1 THEN '1.0–< 1.1'
          WHEN compa_ratio < 1.2 THEN '1.1–< 1.2'
          ELSE '≥ 1.2'
        END AS comp_ratio_band,
        CASE
          WHEN compensation_grade LIKE 'M%' THEN 'M'
          WHEN compensation_grade LIKE 'P%' THEN 'P'
          WHEN compensation_grade LIKE 'R%' THEN 'R'
          WHEN compensation_grade LIKE 'S%' THEN 'S'
          WHEN compensation_grade LIKE 'T%' THEN 'T'
          ELSE 'V / other grade families'
        END AS grade_family,
        CASE
          WHEN stored_manager_layer <= 2 THEN '0–2 layers'
          WHEN stored_manager_layer BETWEEN 3 AND 10 THEN CAST(stored_manager_layer AS VARCHAR(32)) || ' layers'
          WHEN stored_manager_layer >= 11 THEN '11+ layers'
          ELSE NULL
        END AS stored_manager_layer_band
    FROM cohort
),
category_rows AS (
    SELECT 'job_profile_tenure' AS metric, job_profile_tenure_band AS category, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE job_profile_tenure_band IS NOT NULL
    UNION ALL SELECT 'detailed_level_tenure', detailed_level_tenure_band, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE detailed_level_tenure_band IS NOT NULL
    UNION ALL SELECT 'original_hire_tenure', original_hire_tenure_band, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE original_hire_tenure_band IS NOT NULL
    UNION ALL SELECT 'latest_hire_tenure', latest_hire_tenure_band, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE latest_hire_tenure_band IS NOT NULL
    UNION ALL SELECT 'level_grouped', level_grouped, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE level_grouped IS NOT NULL
    UNION ALL SELECT 'management_level', management_level, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE management_level IS NOT NULL
    UNION ALL SELECT 'job_level', job_level, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE job_level IS NOT NULL
    UNION ALL SELECT 'compensation_grade', compensation_grade, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE compensation_grade IS NOT NULL
    UNION ALL SELECT 'comp_ratio_band', comp_ratio_band, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE comp_ratio_band IS NOT NULL
    UNION ALL SELECT 'level_grade_family', level_grouped || '|' || grade_family, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE level_grouped IS NOT NULL AND grade_family IS NOT NULL
    UNION ALL SELECT 'stored_manager_layer_proxy', stored_manager_layer_band, snapshot_date, employee_id, annual_voluntary_attrition_target FROM classified WHERE stored_manager_layer_band IS NOT NULL
),
category_metrics AS (
    SELECT
        metric,
        category,
        MIN(snapshot_date) AS first_snapshot_date,
        MAX(snapshot_date) AS last_snapshot_date,
        COUNT(DISTINCT employee_id) AS distinct_employee_count,
        COUNT(*) AS employee_snapshot_count,
        SUM(annual_voluntary_attrition_target) AS voluntary_exits,
        ROUND(100.0 * SUM(annual_voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS annual_attrition_rate_percent
    FROM category_rows
    GROUP BY 1, 2
),
baseline AS (
    SELECT
        COUNT(*) AS employee_snapshot_count,
        SUM(annual_voluntary_attrition_target) AS voluntary_exits,
        ROUND(100.0 * SUM(annual_voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS annual_attrition_rate_percent
    FROM cohort
)
SELECT
    'category' AS row_type,
    metric,
    category,
    first_snapshot_date,
    last_snapshot_date,
    distinct_employee_count,
    employee_snapshot_count,
    voluntary_exits,
    annual_attrition_rate_percent,
    CAST(NULL AS BIGINT) AS diagnostic_value
FROM category_metrics
UNION ALL
SELECT
    'diagnostic',
    metric,
    CAST(NULL AS VARCHAR(256)),
    CAST(NULL AS DATE), CAST(NULL AS DATE),
    CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    diagnostic_value
FROM (
    SELECT 'snapshot_count' AS metric, snapshot_count::BIGINT AS diagnostic_value FROM source_quality
    UNION ALL SELECT 'active_employee_snapshot_count', active_employee_snapshot_count::BIGINT FROM source_quality
    UNION ALL SELECT 'duplicate_employee_snapshot_count', duplicate_employee_snapshot_count::BIGINT FROM source_quality
    UNION ALL SELECT 'conflicting_employee_snapshot_count', conflicting_employee_snapshot_count::BIGINT FROM source_quality
    UNION ALL SELECT 'baseline_employee_snapshot_count', employee_snapshot_count::BIGINT FROM baseline
    UNION ALL SELECT 'baseline_voluntary_exit_count', voluntary_exits::BIGINT FROM baseline
) diagnostics
ORDER BY row_type, metric, category;
