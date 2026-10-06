-- Análisis interno autorizado: attrition de la cohorte del primer corte disponible.
-- Agregados únicamente. Sin anualizar; no se calcula tasa con cero seguimiento.
-- VOLUNTARY exacto normalizado; una salida por empleado en (inicio, 2026-08-23].
WITH targets AS (
    SELECT 'AQUA'::VARCHAR(256) AS category_key, 'Aqua'::VARCHAR(256) AS category_label, 1 AS category_order
    UNION ALL SELECT 'NAPS', 'NAPS', 2
    UNION ALL SELECT 'MOONSHOT', 'Moonshot', 3
    UNION ALL SELECT 'ARDUINO', 'Arduino', 4
    UNION ALL SELECT 'AUGENTIX INC.', 'Augentix Inc.', 5
),
eligible_rows AS (
    SELECT
        CAST(employee_id AS VARCHAR(256)) AS employee_key,
        fis_mo_end_dt AS snapshot_date,
        UPPER(NULLIF(TRIM(acquisition), '')) AS category_key
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND employee_id IS NOT NULL
      AND fis_mo_end_dt <= DATE '2026-08-23'
),
category_months AS (
    SELECT
        t.category_key,
        e.snapshot_date,
        COUNT(DISTINCT e.employee_key) AS employee_count
    FROM eligible_rows e
    INNER JOIN targets t ON t.category_key = e.category_key
    GROUP BY t.category_key, e.snapshot_date
),
first_dates AS (
    SELECT category_key, MIN(snapshot_date) AS start_snapshot_date
    FROM category_months
    GROUP BY category_key
),
periods AS (
    SELECT
        f.category_key,
        f.start_snapshot_date,
        DATE '2026-08-23' AS end_snapshot_date,
        DATEDIFF(day, f.start_snapshot_date, DATE '2026-08-23') AS followup_days,
        COUNT(DISTINCT CASE WHEN m.snapshot_date > f.start_snapshot_date THEN m.snapshot_date END) AS postbaseline_snapshot_count,
        MAX(CASE WHEN m.snapshot_date = DATE '2026-08-23' THEN m.employee_count ELSE 0 END) AS current_employee_count
    FROM first_dates f
    INNER JOIN category_months m ON m.category_key = f.category_key
    GROUP BY f.category_key, f.start_snapshot_date
),
baseline_employees AS (
    SELECT
        f.category_key,
        f.start_snapshot_date,
        e.employee_key,
        COUNT(*) AS raw_baseline_row_count
    FROM first_dates f
    INNER JOIN eligible_rows e
      ON e.snapshot_date = f.start_snapshot_date AND e.category_key = f.category_key
    GROUP BY f.category_key, f.start_snapshot_date, e.employee_key
),
baseline_quality_employee AS (
    SELECT
        b.category_key,
        b.employee_key,
        COUNT(DISTINCT COALESCE(e.category_key, '__BLANK__')) AS category_value_count
    FROM baseline_employees b
    INNER JOIN eligible_rows e
      ON e.employee_key = b.employee_key AND e.snapshot_date = b.start_snapshot_date
    GROUP BY b.category_key, b.employee_key
),
baseline_quality AS (
    SELECT
        category_key,
        SUM(CASE WHEN category_value_count > 1 THEN 1 ELSE 0 END) AS contradictory_baseline_employee_count
    FROM baseline_quality_employee
    GROUP BY category_key
),
voluntary_events AS (
    SELECT
        CAST(employee_id AS VARCHAR(256)) AS employee_key,
        term_date,
        COUNT(*) AS raw_event_row_count
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date > DATE '2025-08-24'
      AND term_date <= DATE '2026-08-23'
      AND employee_id IS NOT NULL
    GROUP BY CAST(employee_id AS VARCHAR(256)), term_date
),
baseline_followup AS (
    SELECT
        b.category_key,
        b.employee_key,
        b.raw_baseline_row_count,
        COUNT(e.term_date) AS voluntary_event_count,
        COALESCE(SUM(e.raw_event_row_count), 0) AS raw_voluntary_event_row_count
    FROM baseline_employees b
    LEFT JOIN voluntary_events e
      ON e.employee_key = b.employee_key
     AND e.term_date > b.start_snapshot_date
     AND e.term_date <= DATE '2026-08-23'
    GROUP BY b.category_key, b.employee_key, b.raw_baseline_row_count
),
cohort_counts AS (
    SELECT
        category_key,
        COUNT(*) AS baseline_employee_count,
        SUM(CASE WHEN voluntary_event_count > 0 THEN 1 ELSE 0 END) AS voluntary_exit_count,
        SUM(voluntary_event_count) AS unique_employee_date_event_count,
        SUM(CASE WHEN voluntary_event_count > 1 THEN 1 ELSE 0 END) AS multiple_exit_employee_count,
        SUM(raw_voluntary_event_row_count) AS raw_voluntary_event_row_count,
        SUM(raw_baseline_row_count - 1) AS duplicate_baseline_excess_row_count
    FROM baseline_followup
    GROUP BY category_key
),
independent_numerator AS (
    SELECT
        b.category_key,
        COUNT(DISTINCT CAST(s.employee_id AS VARCHAR(256))) AS independent_voluntary_exit_count
    FROM baseline_employees b
    LEFT JOIN hrda.post_hire_monthly_worker_dtls s
      ON CAST(s.employee_id AS VARCHAR(256)) = b.employee_key
     AND UPPER(NULLIF(TRIM(CAST(s.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
     AND s.term_date > b.start_snapshot_date
     AND s.term_date <= DATE '2026-08-23'
    GROUP BY b.category_key
),
current_cohort_context AS (
    SELECT
        p.category_key,
        COUNT(DISTINCT e.employee_key) AS current_employee_count,
        COUNT(DISTINCT b.employee_key) AS current_members_of_starting_cohort,
        COUNT(DISTINCT CASE WHEN b.employee_key IS NULL THEN e.employee_key END) AS current_employees_outside_starting_cohort
    FROM periods p
    INNER JOIN eligible_rows e
      ON e.category_key = p.category_key AND e.snapshot_date = p.end_snapshot_date
    LEFT JOIN baseline_employees b
      ON b.category_key = p.category_key AND b.employee_key = e.employee_key
    GROUP BY p.category_key
)
SELECT
    t.category_label,
    p.start_snapshot_date,
    p.end_snapshot_date,
    p.followup_days,
    p.postbaseline_snapshot_count,
    c.baseline_employee_count,
    c.voluntary_exit_count,
    i.independent_voluntary_exit_count,
    CASE WHEN p.followup_days > 0 AND p.postbaseline_snapshot_count > 0
         THEN 100.0 * c.voluntary_exit_count / NULLIF(c.baseline_employee_count, 0)
         ELSE NULL END AS observed_attrition_rate_percent,
    p.current_employee_count,
    k.current_members_of_starting_cohort,
    k.current_employees_outside_starting_cohort,
    c.unique_employee_date_event_count,
    c.multiple_exit_employee_count,
    c.raw_voluntary_event_row_count,
    c.duplicate_baseline_excess_row_count,
    q.contradictory_baseline_employee_count,
    CASE WHEN p.followup_days = 0 OR p.postbaseline_snapshot_count = 0
         THEN 'no_followup' ELSE 'partial_period' END AS rate_status
FROM targets t
INNER JOIN periods p ON p.category_key = t.category_key
INNER JOIN cohort_counts c ON c.category_key = t.category_key
INNER JOIN independent_numerator i ON i.category_key = t.category_key
INNER JOIN baseline_quality q ON q.category_key = t.category_key
INNER JOIN current_cohort_context k ON k.category_key = t.category_key
ORDER BY t.category_order;
