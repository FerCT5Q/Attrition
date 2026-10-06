/*
  Presentation | aggregate-only | slide revision evidence

  Claim: The revised career-tenure slide may display only (1) Time in job
  profile, calculated from the stored profile-start date adjusted to the later
  hire/rehire date, and (2) the stored numeric time_in_role field. It must not
  use levelentrydate or job_level_primary_position.

  Population and grain: one active Regular Employee at each monthly snapshot
  (worker_type='Employee', employee_type='Regular', active_status=1).

  Outcome: strict VOLUNTARY termination in (snapshot_date,
  snapshot_date + 12 months]. The annual-rate window is the latest 24 monthly
  snapshots that have complete 12-month follow-up. The display distribution is
  the latest available monthly snapshot.

  Acceptance rule:
  - no duplicate or conflicting employee-snapshot values for either displayed
    field;
  - no future job-profile start or rehire dates and no negative time_in_role;
  - every visible distribution and annual-rate band has at least 30 employee
    snapshots; an annual rate also requires at least 30 voluntary exits.

  The query returns aggregate rows only. Employee IDs remain inside CTEs solely
  to establish the employee-snapshot grain and the time-safe outcome join.
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
    ) AS ranked
    WHERE recency_rank <= 24
),
selected_snapshot_dates AS (
    SELECT 'history' AS scope, snapshot_date
    FROM complete_snapshot_dates
    UNION ALL
    SELECT 'display' AS scope, latest_snapshot_date
    FROM source_bounds
),
active_snapshot_raw AS (
    SELECT
        d.scope,
        d.snapshot_date,
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.time_in_job_profile_start_date AS DATE)) AS job_profile_start_date,
        MAX(CAST(w.max_hire_rehire_date AS DATE)) AS latest_hire_rehire_date,
        MAX(w.time_in_role) AS time_in_role_years,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.time_in_job_profile_start_date AS VARCHAR(32)), '<NULL>')) AS job_profile_start_variants,
        COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS latest_hire_rehire_variants,
        COUNT(DISTINCT COALESCE(CAST(w.time_in_role AS VARCHAR(64)), '<NULL>')) AS time_in_role_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN selected_snapshot_dates AS d
      ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2, 3
),
source_quality AS (
    SELECT
        scope,
        COUNT(DISTINCT snapshot_date) AS snapshot_count,
        COUNT(*) AS employee_snapshot_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN job_profile_start_variants > 1
                   OR latest_hire_rehire_variants > 1
                   OR time_in_role_variants > 1
                 THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count,
        SUM(CASE WHEN job_profile_start_date IS NULL
                   OR latest_hire_rehire_date IS NULL
                   OR job_profile_start_date > snapshot_date
                   OR latest_hire_rehire_date > snapshot_date
                 THEN 1 ELSE 0 END) AS invalid_or_missing_job_profile_count,
        SUM(CASE WHEN time_in_role_years IS NULL OR time_in_role_years < 0 THEN 1 ELSE 0 END) AS invalid_or_missing_time_in_role_count
    FROM active_snapshot_raw
    GROUP BY 1
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
history_cohort AS (
    SELECT
        s.snapshot_date,
        s.employee_id,
        s.job_profile_start_date,
        s.latest_hire_rehire_date,
        s.time_in_role_years,
        MAX(CASE WHEN e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS annual_voluntary_attrition_target
    FROM active_snapshot_raw AS s
    LEFT JOIN voluntary_events AS e
      ON e.employee_id = s.employee_id
     AND e.term_date > s.snapshot_date
     AND e.term_date <= DATEADD(month, 12, s.snapshot_date)
    WHERE s.scope = 'history'
    GROUP BY 1, 2, 3, 4, 5
),
display_cohort AS (
    SELECT
        snapshot_date,
        employee_id,
        job_profile_start_date,
        latest_hire_rehire_date,
        time_in_role_years
    FROM active_snapshot_raw
    WHERE scope = 'display'
),
classified_history AS (
    SELECT
        snapshot_date,
        employee_id,
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
          WHEN time_in_role_years IS NULL OR time_in_role_years < 0 THEN NULL
          WHEN time_in_role_years < 1 THEN '<1 year'
          WHEN time_in_role_years < 2 THEN '1–<2 years'
          WHEN time_in_role_years < 3 THEN '2–<3 years'
          WHEN time_in_role_years < 5 THEN '3–<5 years'
          WHEN time_in_role_years < 10 THEN '5–<10 years'
          ELSE '10+ years'
        END AS time_in_role_band
    FROM history_cohort
),
classified_display AS (
    SELECT
        snapshot_date,
        employee_id,
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
          WHEN time_in_role_years IS NULL OR time_in_role_years < 0 THEN NULL
          WHEN time_in_role_years < 1 THEN '<1 year'
          WHEN time_in_role_years < 2 THEN '1–<2 years'
          WHEN time_in_role_years < 3 THEN '2–<3 years'
          WHEN time_in_role_years < 5 THEN '3–<5 years'
          WHEN time_in_role_years < 10 THEN '5–<10 years'
          ELSE '10+ years'
        END AS time_in_role_band
    FROM display_cohort
),
annual_category_rows AS (
    SELECT 'time_in_job_profile' AS metric, job_profile_tenure_band AS category, snapshot_date, employee_id, annual_voluntary_attrition_target
    FROM classified_history
    WHERE job_profile_tenure_band IS NOT NULL
    UNION ALL
    SELECT 'time_in_role' AS metric, time_in_role_band AS category, snapshot_date, employee_id, annual_voluntary_attrition_target
    FROM classified_history
    WHERE time_in_role_band IS NOT NULL
),
display_category_rows AS (
    SELECT 'time_in_job_profile' AS metric, job_profile_tenure_band AS category, snapshot_date, employee_id
    FROM classified_display
    WHERE job_profile_tenure_band IS NOT NULL
    UNION ALL
    SELECT 'time_in_role' AS metric, time_in_role_band AS category, snapshot_date, employee_id
    FROM classified_display
    WHERE time_in_role_band IS NOT NULL
),
annual_category_metrics AS (
    SELECT
        metric,
        category,
        MIN(snapshot_date) AS first_snapshot_date,
        MAX(snapshot_date) AS last_snapshot_date,
        COUNT(DISTINCT employee_id) AS distinct_employee_count,
        COUNT(*) AS employee_snapshot_count,
        SUM(annual_voluntary_attrition_target) AS voluntary_exits,
        ROUND(100.0 * SUM(annual_voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS annual_attrition_rate_percent
    FROM annual_category_rows
    GROUP BY 1, 2
),
display_category_metrics AS (
    SELECT
        metric,
        category,
        MIN(snapshot_date) AS snapshot_date,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM display_category_rows
    GROUP BY 1, 2
),
history_baseline AS (
    SELECT
        COUNT(*) AS employee_snapshot_count,
        SUM(annual_voluntary_attrition_target) AS voluntary_exits
    FROM history_cohort
)
SELECT
    'annual_category' AS row_type,
    metric,
    category,
    first_snapshot_date,
    last_snapshot_date,
    distinct_employee_count,
    employee_snapshot_count,
    voluntary_exits,
    annual_attrition_rate_percent,
    CAST(NULL AS DATE) AS display_snapshot_date,
    CAST(NULL AS BIGINT) AS display_employee_count,
    CAST(NULL AS BIGINT) AS diagnostic_value
FROM annual_category_metrics
UNION ALL
SELECT
    'display_category' AS row_type,
    metric,
    category,
    CAST(NULL AS DATE),
    CAST(NULL AS DATE),
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    snapshot_date,
    employee_count,
    CAST(NULL AS BIGINT)
FROM display_category_metrics
UNION ALL
SELECT
    'diagnostic' AS row_type,
    metric,
    CAST(NULL AS VARCHAR(64)) AS category,
    CAST(NULL AS DATE),
    CAST(NULL AS DATE),
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    CAST(NULL AS DATE),
    CAST(NULL AS BIGINT),
    diagnostic_value
FROM (
    SELECT 'history_snapshot_count' AS metric, snapshot_count::BIGINT AS diagnostic_value FROM source_quality WHERE scope = 'history'
    UNION ALL SELECT 'history_employee_snapshot_count', employee_snapshot_count::BIGINT FROM source_quality WHERE scope = 'history'
    UNION ALL SELECT 'history_duplicate_employee_snapshot_count', duplicate_employee_snapshot_count::BIGINT FROM source_quality WHERE scope = 'history'
    UNION ALL SELECT 'history_conflicting_employee_snapshot_count', conflicting_employee_snapshot_count::BIGINT FROM source_quality WHERE scope = 'history'
    UNION ALL SELECT 'history_invalid_or_missing_job_profile_count', invalid_or_missing_job_profile_count::BIGINT FROM source_quality WHERE scope = 'history'
    UNION ALL SELECT 'history_invalid_or_missing_time_in_role_count', invalid_or_missing_time_in_role_count::BIGINT FROM source_quality WHERE scope = 'history'
    UNION ALL SELECT 'history_baseline_voluntary_exit_count', voluntary_exits::BIGINT FROM history_baseline
    UNION ALL SELECT 'display_snapshot_count', snapshot_count::BIGINT FROM source_quality WHERE scope = 'display'
    UNION ALL SELECT 'display_employee_snapshot_count', employee_snapshot_count::BIGINT FROM source_quality WHERE scope = 'display'
    UNION ALL SELECT 'display_duplicate_employee_snapshot_count', duplicate_employee_snapshot_count::BIGINT FROM source_quality WHERE scope = 'display'
    UNION ALL SELECT 'display_conflicting_employee_snapshot_count', conflicting_employee_snapshot_count::BIGINT FROM source_quality WHERE scope = 'display'
    UNION ALL SELECT 'display_invalid_or_missing_job_profile_count', invalid_or_missing_job_profile_count::BIGINT FROM source_quality WHERE scope = 'display'
    UNION ALL SELECT 'display_invalid_or_missing_time_in_role_count', invalid_or_missing_time_in_role_count::BIGINT FROM source_quality WHERE scope = 'display'
) AS diagnostics
ORDER BY row_type, metric, category;
