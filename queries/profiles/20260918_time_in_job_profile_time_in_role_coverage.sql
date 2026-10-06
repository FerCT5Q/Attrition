/*
  Presentation | aggregate-only | focused coverage follow-up

  Purpose: determine whether Time in job profile and time_in_role have enough
  consecutive historical coverage to support an annual attrition comparison.

  Population/grain: one active Regular Employee per monthly snapshot. The
  output contains only date-level aggregate metrics for the most recent 37
  monthly snapshots. Employee IDs remain inside the CTE used to check the
  employee-snapshot grain.

  Acceptance rule: a series needs coverage >=95% in at least three consecutive
  monthly snapshots with no duplicate or conflicting employee-snapshot values
  before its annual attrition rate can be displayed as longitudinally
  comparable to the latest distribution.
*/
WITH source_bounds AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
recent_snapshots AS (
    SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    CROSS JOIN source_bounds
    WHERE fis_mo_end_dt IS NOT NULL
      AND CAST(fis_mo_end_dt AS DATE) >= DATEADD(month, -36, latest_snapshot_date)
    GROUP BY 1
),
employee_snapshot AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.time_in_job_profile_start_date AS DATE)) AS job_profile_start_date,
        MAX(CAST(w.max_hire_rehire_date AS DATE)) AS latest_hire_rehire_date,
        MAX(w.time_in_role) AS time_in_role_years,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.time_in_job_profile_start_date AS VARCHAR(32)), '<NULL>')) AS job_profile_start_variants,
        COUNT(DISTINCT COALESCE(CAST(w.max_hire_rehire_date AS VARCHAR(32)), '<NULL>')) AS latest_hire_rehire_variants,
        COUNT(DISTINCT COALESCE(CAST(w.time_in_role AS VARCHAR(64)), '<NULL>')) AS time_in_role_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN recent_snapshots AS d
      ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2
)
SELECT
    snapshot_date,
    COUNT(*) AS eligible_employees,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
    SUM(CASE WHEN job_profile_start_variants > 1
               OR latest_hire_rehire_variants > 1
               OR time_in_role_variants > 1
             THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count,
    SUM(CASE WHEN job_profile_start_date IS NOT NULL
               AND latest_hire_rehire_date IS NOT NULL
               AND job_profile_start_date <= snapshot_date
               AND latest_hire_rehire_date <= snapshot_date
             THEN 1 ELSE 0 END) AS time_in_job_profile_observable_employees,
    ROUND(
        100.0 * SUM(CASE WHEN job_profile_start_date IS NOT NULL
                            AND latest_hire_rehire_date IS NOT NULL
                            AND job_profile_start_date <= snapshot_date
                            AND latest_hire_rehire_date <= snapshot_date
                          THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        4
    ) AS time_in_job_profile_coverage_percent,
    SUM(CASE WHEN time_in_role_years IS NOT NULL AND time_in_role_years >= 0 THEN 1 ELSE 0 END) AS time_in_role_observable_employees,
    ROUND(
        100.0 * SUM(CASE WHEN time_in_role_years IS NOT NULL AND time_in_role_years >= 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        4
    ) AS time_in_role_coverage_percent,
    SUM(CASE WHEN time_in_role_years < 0 THEN 1 ELSE 0 END) AS negative_time_in_role_count
FROM employee_snapshot
GROUP BY 1
ORDER BY snapshot_date;
