-- Análisis interno autorizado: diagnóstico de las cinco bases anuales vacías.
-- Consulta read-only; devuelve sólo agregados por categoría.
-- Cohorte: Employee / Regular activos; baseline 2025-08-24, actual 2026-08-23.
-- La primera observación del campo no establece la fecha legal de adquisición.
WITH targets AS (
    SELECT 'AQUA'::VARCHAR(256) AS category_key, 'Aqua'::VARCHAR(256) AS category_label, 1 AS category_order
    UNION ALL SELECT 'NAPS', 'NAPS', 2
    UNION ALL SELECT 'MOONSHOT', 'Moonshot', 3
    UNION ALL SELECT 'ARDUINO', 'Arduino', 4
    UNION ALL SELECT 'AUGENTIX INC.', 'Augentix Inc.', 5
),
source_rows AS (
    SELECT
        CAST(employee_id AS VARCHAR(256)) AS employee_key,
        fis_mo_end_dt AS snapshot_date,
        UPPER(NULLIF(TRIM(acquisition), '')) AS category_key,
        CASE WHEN worker_type = 'Employee'
                   AND employee_type = 'Regular'
                   AND active_status = 1
             THEN 1 ELSE 0 END AS eligible_flag
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt <= DATE '2026-08-23'
      AND employee_id IS NOT NULL
),
category_months AS (
    SELECT
        t.category_key,
        s.snapshot_date,
        COUNT(DISTINCT s.employee_key) AS any_population_count,
        COUNT(DISTINCT CASE WHEN s.eligible_flag = 1 THEN s.employee_key END) AS eligible_employee_count
    FROM source_rows s
    INNER JOIN targets t ON t.category_key = s.category_key
    GROUP BY t.category_key, s.snapshot_date
),
category_history AS (
    SELECT
        category_key,
        MIN(snapshot_date) AS first_any_category_snapshot,
        MIN(CASE WHEN eligible_employee_count > 0 THEN snapshot_date END) AS first_eligible_category_snapshot,
        COUNT(*) AS observed_category_month_count,
        MAX(CASE WHEN snapshot_date = DATE '2025-08-24' THEN any_population_count ELSE 0 END) AS baseline_category_any_population_count,
        MAX(CASE WHEN snapshot_date = DATE '2025-08-24' THEN eligible_employee_count ELSE 0 END) AS baseline_category_eligible_count
    FROM category_months
    GROUP BY category_key
),
current_snapshot_employee AS (
    SELECT
        employee_key,
        MAX(category_key) AS category_key,
        COUNT(*) AS raw_row_count,
        COUNT(DISTINCT COALESCE(category_key, '__BLANK__')) AS category_value_count
    FROM source_rows
    WHERE snapshot_date = DATE '2026-08-23'
      AND eligible_flag = 1
    GROUP BY employee_key
),
current_target_employees AS (
    SELECT
        c.employee_key,
        c.category_key,
        c.raw_row_count,
        c.category_value_count
    FROM current_snapshot_employee c
    INNER JOIN targets t ON t.category_key = c.category_key
),
current_employee_history AS (
    SELECT
        c.category_key,
        c.employee_key,
        c.raw_row_count,
        c.category_value_count,
        MIN(s.snapshot_date) AS first_person_snapshot,
        MAX(CASE WHEN s.snapshot_date = DATE '2025-08-24' THEN 1 ELSE 0 END) AS present_baseline_any_population,
        MAX(CASE WHEN s.snapshot_date = DATE '2025-08-24' AND s.eligible_flag = 1 THEN 1 ELSE 0 END) AS present_baseline_eligible,
        MAX(CASE WHEN s.snapshot_date = DATE '2025-08-24' AND s.eligible_flag = 1 AND s.category_key = c.category_key THEN 1 ELSE 0 END) AS baseline_same_label,
        MAX(CASE WHEN s.snapshot_date = DATE '2025-08-24' AND s.eligible_flag = 1 AND s.category_key IS NULL THEN 1 ELSE 0 END) AS baseline_blank_label,
        MAX(CASE WHEN s.snapshot_date = DATE '2025-08-24' AND s.eligible_flag = 1 AND s.category_key IS NOT NULL AND s.category_key <> c.category_key THEN 1 ELSE 0 END) AS baseline_other_label,
        COUNT(DISTINCT CASE WHEN s.snapshot_date = DATE '2025-08-24' AND s.eligible_flag = 1 THEN COALESCE(s.category_key, '__BLANK__') END) AS baseline_eligible_label_count
    FROM current_target_employees c
    INNER JOIN source_rows s ON s.employee_key = c.employee_key
    GROUP BY c.category_key, c.employee_key, c.raw_row_count, c.category_value_count
),
current_summary AS (
    SELECT
        category_key,
        COUNT(*) AS current_employee_count,
        SUM(raw_row_count - 1) AS current_duplicate_excess_row_count,
        SUM(CASE WHEN category_value_count > 1 THEN 1 ELSE 0 END) AS current_contradictory_employee_count,
        SUM(present_baseline_any_population) AS current_present_at_baseline_any_population_count,
        SUM(present_baseline_eligible) AS current_present_at_baseline_eligible_count,
        SUM(baseline_same_label) AS current_baseline_same_label_count,
        SUM(baseline_blank_label) AS current_baseline_blank_label_count,
        SUM(baseline_other_label) AS current_baseline_other_label_count,
        SUM(CASE WHEN baseline_eligible_label_count > 1 THEN 1 ELSE 0 END) AS current_baseline_contradictory_label_count,
        SUM(CASE WHEN present_baseline_any_population = 1 AND present_baseline_eligible = 0 THEN 1 ELSE 0 END) AS current_baseline_excluded_population_count,
        SUM(CASE WHEN present_baseline_any_population = 0 THEN 1 ELSE 0 END) AS current_absent_from_baseline_count,
        SUM(CASE WHEN first_person_snapshot > DATE '2025-08-24' THEN 1 ELSE 0 END) AS current_first_record_after_baseline_count,
        SUM(CASE WHEN first_person_snapshot < DATE '2025-08-24' THEN 1 ELSE 0 END) AS current_seen_before_baseline_count
    FROM current_employee_history
    GROUP BY category_key
)
SELECT
    t.category_label,
    h.first_any_category_snapshot,
    h.first_eligible_category_snapshot,
    fm.any_population_count AS first_category_snapshot_any_population_count,
    fe.eligible_employee_count AS first_category_snapshot_eligible_count,
    h.observed_category_month_count,
    h.baseline_category_any_population_count,
    h.baseline_category_eligible_count,
    c.current_employee_count,
    c.current_duplicate_excess_row_count,
    c.current_contradictory_employee_count,
    c.current_present_at_baseline_any_population_count,
    c.current_present_at_baseline_eligible_count,
    c.current_baseline_same_label_count,
    c.current_baseline_blank_label_count,
    c.current_baseline_other_label_count,
    c.current_baseline_contradictory_label_count,
    c.current_baseline_excluded_population_count,
    c.current_absent_from_baseline_count,
    c.current_first_record_after_baseline_count,
    c.current_seen_before_baseline_count
FROM targets t
LEFT JOIN category_history h ON h.category_key = t.category_key
LEFT JOIN category_months fm ON fm.category_key = h.category_key AND fm.snapshot_date = h.first_any_category_snapshot
LEFT JOIN category_months fe ON fe.category_key = h.category_key AND fe.snapshot_date = h.first_eligible_category_snapshot
LEFT JOIN current_summary c ON c.category_key = t.category_key
ORDER BY t.category_order;
