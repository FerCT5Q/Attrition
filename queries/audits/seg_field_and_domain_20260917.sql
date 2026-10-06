-- Purpose: confirm whether `seg` is stored in the employee snapshot and
-- profile its aggregate domain in the governed Critical Tech catalogue.
-- Deliverable mode: presentation. No employee-level fields are returned.
-- Population for the optional coverage metric: active Regular Employees at
-- the latest monthly snapshot, joined to the current Critical Tech catalogue.
-- Acceptance rule: report `seg` only if it is found in a source table and
-- each displayed employee cohort is at least 30.

WITH latest_snapshot AS (
    SELECT MAX(fis_mo_end_dt) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
),
catalogue AS (
    SELECT
        COALESCE(NULLIF(TRIM(seg), ''), '[missing]') AS seg,
        LOWER(TRIM(extended_job_family)) AS normalized_job_family
    FROM hrda.critical_tech
    WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
),
latest_active_regular AS (
    SELECT
        employee_id,
        LOWER(TRIM(job_family)) AS normalized_job_family
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM latest_snapshot)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
segment_coverage AS (
    SELECT
        c.seg,
        COUNT(DISTINCT c.normalized_job_family) AS catalogued_job_families,
        COUNT(DISTINCT a.employee_id) AS active_regular_employees
    FROM catalogue c
    LEFT JOIN latest_active_regular a
      ON a.normalized_job_family = c.normalized_job_family
    GROUP BY c.seg
)
SELECT
    'hrda.critical_tech' AS source_table,
    seg AS seg_value,
    catalogued_job_families,
    active_regular_employees
FROM segment_coverage
WHERE active_regular_employees >= 30

ORDER BY seg_value;
