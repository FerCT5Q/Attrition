-- Purpose: aggregate-only evidence for category-display decisions in the attrition deck.
-- Population/grain: active regular employees, one monthly workforce snapshot per employee.
-- Knowledge boundaries: the deck's frozen 2026-08-23 snapshot and the latest
-- available fis_mo_end_dt, returned separately so they are never mixed.
-- Acceptance rule: each reviewed field must return its current total, populated,
-- missing, distinct-category, safe-category, and top-N counts. A missing bucket
-- is displayable only when its aggregate count is at least 30; all category
-- labels, including compensation_grade, remain internal to the query.
WITH latest_snapshot AS (
    SELECT MAX(fis_mo_end_dt) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
    UNION
    SELECT DATE '2026-08-23' AS snapshot_date
),
cohort AS (
    SELECT
        s.snapshot_date,
        employee_id,
        NULLIF(TRIM(CAST(country AS VARCHAR(512))), '') AS country,
        NULLIF(TRIM(CAST(office_site AS VARCHAR(512))), '') AS office_site,
        NULLIF(TRIM(CAST(job_family AS VARCHAR(512))), '') AS job_family,
        NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(512))), '') AS work_arrangement,
        NULLIF(TRIM(CAST(job_level_primary_position AS VARCHAR(512))), '') AS job_level_primary_position,
        NULLIF(TRIM(CAST(compensation_grade AS VARCHAR(512))), '') AS compensation_grade
    FROM latest_snapshot AS s
    JOIN hrda.post_hire_monthly_worker_dtls AS w
      ON w.fis_mo_end_dt = s.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
),
field_values AS (
    SELECT snapshot_date, employee_id, 'country' AS field_name, country AS value_label FROM cohort
    UNION ALL SELECT snapshot_date, employee_id, 'office_site', office_site FROM cohort
    UNION ALL SELECT snapshot_date, employee_id, 'job_family', job_family FROM cohort
    UNION ALL SELECT snapshot_date, employee_id, 'work_arrangement', work_arrangement FROM cohort
    UNION ALL SELECT snapshot_date, employee_id, 'job_level_primary_position', job_level_primary_position FROM cohort
    UNION ALL SELECT snapshot_date, employee_id, 'compensation_grade', compensation_grade FROM cohort
),
field_totals AS (
    SELECT
        snapshot_date,
        field_name,
        COUNT(DISTINCT employee_id) AS eligible_employees,
        COUNT(DISTINCT CASE WHEN value_label IS NOT NULL THEN employee_id END) AS populated_employees,
        COUNT(DISTINCT CASE WHEN value_label IS NULL THEN employee_id END) AS missing_employees,
        COUNT(DISTINCT value_label) AS distinct_values
    FROM field_values
    GROUP BY snapshot_date, field_name
),
category_counts AS (
    SELECT
        snapshot_date,
        field_name,
        value_label,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM field_values
    WHERE value_label IS NOT NULL
    GROUP BY snapshot_date, field_name, value_label
),
ranked_categories AS (
    SELECT
        snapshot_date,
        field_name,
        employee_count,
        ROW_NUMBER() OVER (PARTITION BY snapshot_date, field_name ORDER BY employee_count DESC, value_label) AS category_rank
    FROM category_counts
),
rank_summary AS (
    SELECT
        snapshot_date,
        field_name,
        SUM(CASE WHEN employee_count >= 30 THEN 1 ELSE 0 END) AS categories_at_least_30,
        SUM(CASE WHEN category_rank <= 10 THEN employee_count ELSE 0 END) AS top_10_employees,
        SUM(CASE WHEN category_rank <= 15 THEN employee_count ELSE 0 END) AS top_15_employees,
        SUM(CASE WHEN category_rank <= 20 THEN employee_count ELSE 0 END) AS top_20_employees
    FROM ranked_categories
    GROUP BY snapshot_date, field_name
)
SELECT
    t.snapshot_date,
    t.field_name,
    t.eligible_employees,
    t.populated_employees,
    t.missing_employees,
    t.distinct_values,
    r.categories_at_least_30,
    r.top_10_employees,
    r.top_15_employees,
    r.top_20_employees
FROM field_totals AS t
JOIN rank_summary AS r
  ON t.snapshot_date = r.snapshot_date
 AND t.field_name = r.field_name
ORDER BY t.snapshot_date, t.field_name;
