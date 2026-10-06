-- Propósito: describir prior_qc_work_years por año individual en el snapshot
-- 2026-09-27. No prueba la fórmula, el lineage ni la definición de negocio.
-- Población: empleados regulares activos; grain: empleado distinto.
-- Regla de publicación: cada categoría visible debe tener n >= 30.
WITH base AS (
    SELECT
        employee_id,
        prior_qc_work_years
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-09-27'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
employee_value_cardinality AS (
    SELECT
        employee_id,
        COUNT(DISTINCT prior_qc_work_years) AS distinct_value_count
    FROM base
    GROUP BY employee_id
),
classified AS (
    SELECT
        employee_id,
        CASE
            WHEN prior_qc_work_years IS NULL THEN NULL
            WHEN prior_qc_work_years < 0 THEN NULL
            WHEN prior_qc_work_years < 1 THEN '<1'
            WHEN prior_qc_work_years < 32 THEN FLOOR(prior_qc_work_years)::INT::VARCHAR(10)
            ELSE '32+'
        END AS category,
        CASE
            WHEN prior_qc_work_years IS NULL OR prior_qc_work_years < 0 THEN NULL
            WHEN prior_qc_work_years < 1 THEN 0
            WHEN prior_qc_work_years < 32 THEN FLOOR(prior_qc_work_years)::INT + 1
            ELSE 34
        END AS category_order
    FROM base
),
category_counts AS (
    SELECT
        category,
        category_order,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM classified
    WHERE category IS NOT NULL
    GROUP BY 1, 2
),
category_quality AS (
    SELECT
        COUNT(*) AS published_category_count,
        COALESCE(SUM(employee_count), 0) AS published_employee_count,
        COALESCE(MIN(employee_count), 0) AS minimum_category_employee_count,
        SUM(CASE WHEN employee_count < 30 THEN 1 ELSE 0 END) AS categories_below_minimum
    FROM category_counts
),
summary AS (
    SELECT
        DATE '2026-09-27' AS snapshot_date,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT employee_id) AS eligible_employees,
        COUNT(DISTINCT CASE WHEN prior_qc_work_years IS NOT NULL THEN employee_id END) AS observable_employees,
        COUNT(DISTINCT CASE WHEN prior_qc_work_years IS NULL THEN employee_id END) AS null_employees,
        COUNT(DISTINCT CASE WHEN prior_qc_work_years < 0 THEN employee_id END) AS negative_employees,
        COUNT(DISTINCT CASE WHEN prior_qc_work_years >= 0 THEN employee_id END) AS non_negative_employees,
        COUNT(DISTINCT CASE WHEN prior_qc_work_years >= 0 AND prior_qc_work_years < 1 THEN employee_id END) AS below_one_employees,
        COUNT(DISTINCT CASE WHEN prior_qc_work_years >= 32 THEN employee_id END) AS tail_32_plus_employees,
        COUNT(DISTINCT CASE WHEN prior_qc_work_years >= 32 AND prior_qc_work_years < 33 THEN employee_id END) AS year_32_employees,
        COUNT(DISTINCT CASE WHEN prior_qc_work_years >= 31 AND prior_qc_work_years < 32 THEN employee_id END) AS year_31_employees,
        COUNT(DISTINCT CASE WHEN prior_qc_work_years IS NULL OR prior_qc_work_years < 0 THEN employee_id END) AS excluded_employees,
        SUM(CASE WHEN c.distinct_value_count > 1 THEN 1 ELSE 0 END) AS multi_valued_employees
    FROM base b
    LEFT JOIN employee_value_cardinality c USING (employee_id)
)
SELECT
    cc.category,
    cc.category_order,
    cc.employee_count,
    s.snapshot_date,
    s.source_rows,
    s.eligible_employees,
    s.observable_employees,
    s.null_employees,
    s.negative_employees,
    s.non_negative_employees,
    s.below_one_employees,
    s.tail_32_plus_employees,
    s.year_32_employees,
    s.year_31_employees,
    s.excluded_employees,
    s.multi_valued_employees,
    q.published_category_count,
    q.published_employee_count,
    q.minimum_category_employee_count,
    q.categories_below_minimum
FROM category_counts cc
CROSS JOIN summary s
CROSS JOIN category_quality q
ORDER BY cc.category_order;
