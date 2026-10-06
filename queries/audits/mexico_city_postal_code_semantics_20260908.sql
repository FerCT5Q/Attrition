-- Claim: en la cohorte de Mexico City, postal_code se comporta como dato
-- residencial del empleado y no como una lista de sólo dos oficinas.
-- Regla conservadora: la cardinalidad y concentración de postal_code deben
-- diferir materialmente de office_site; la consulta no prueba por sí sola el
-- lineage oficial.
WITH base AS (
    SELECT
        employee_id,
        NULLIF(TRIM(CAST(postal_code AS VARCHAR)), '') AS postal_code_value,
        NULLIF(TRIM(CAST(office_site AS VARCHAR)), '') AS office_site_value
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-09-27'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND UPPER(TRIM(city)) = 'MEXICO CITY'
),
postal_counts AS (
    SELECT postal_code_value, COUNT(DISTINCT employee_id) AS employee_count
    FROM base
    WHERE postal_code_value IS NOT NULL
    GROUP BY 1
),
office_counts AS (
    SELECT office_site_value, COUNT(DISTINCT employee_id) AS employee_count
    FROM base
    WHERE office_site_value IS NOT NULL
    GROUP BY 1
),
employee_cardinality AS (
    SELECT
        employee_id,
        COUNT(DISTINCT postal_code_value) AS postal_code_value_count,
        COUNT(DISTINCT office_site_value) AS office_site_value_count
    FROM base
    GROUP BY 1
),
summary AS (
    SELECT
        COUNT(*) AS source_rows,
        COUNT(DISTINCT employee_id) AS eligible_employees,
        COUNT(DISTINCT CASE WHEN postal_code_value IS NOT NULL THEN employee_id END) AS postal_code_observable_employees,
        COUNT(DISTINCT CASE WHEN office_site_value IS NOT NULL THEN employee_id END) AS office_site_observable_employees,
        COUNT(DISTINCT CASE WHEN postal_code_value IS NOT NULL AND office_site_value IS NOT NULL THEN employee_id END) AS both_observable_employees,
        COUNT(DISTINCT CASE WHEN postal_code_value IS NULL THEN employee_id END) AS postal_code_missing_employees,
        COUNT(DISTINCT CASE WHEN office_site_value IS NULL THEN employee_id END) AS office_site_missing_employees,
        SUM(CASE WHEN c.postal_code_value_count > 1 THEN 1 ELSE 0 END) AS postal_code_multi_valued_employees,
        SUM(CASE WHEN c.office_site_value_count > 1 THEN 1 ELSE 0 END) AS office_site_multi_valued_employees
    FROM base b
    LEFT JOIN employee_cardinality c USING (employee_id)
),
value_summary AS (
    SELECT
        (SELECT COUNT(*) FROM postal_counts) AS distinct_postal_code_values,
        (SELECT COUNT(*) FROM office_counts) AS distinct_office_site_values,
        (SELECT COUNT(*) FROM postal_counts WHERE employee_count >= 30) AS postal_code_values_n_ge_30,
        (SELECT COUNT(*) FROM postal_counts WHERE employee_count < 30) AS postal_code_values_n_lt_30,
        (SELECT COALESCE(MAX(employee_count), 0) FROM postal_counts) AS largest_postal_code_cohort,
        (SELECT COALESCE(MAX(employee_count), 0) FROM office_counts) AS largest_office_site_cohort,
        (SELECT COUNT(*) FROM (SELECT DISTINCT postal_code_value, office_site_value FROM base WHERE postal_code_value IS NOT NULL AND office_site_value IS NOT NULL) pairs) AS distinct_postal_code_office_pairs
)
SELECT
    DATE '2026-09-27' AS snapshot_date,
    'MEXICO CITY' AS city_label,
    s.source_rows,
    s.eligible_employees,
    s.postal_code_observable_employees,
    s.office_site_observable_employees,
    s.both_observable_employees,
    s.postal_code_missing_employees,
    s.office_site_missing_employees,
    s.postal_code_multi_valued_employees,
    s.office_site_multi_valued_employees,
    v.distinct_postal_code_values,
    v.distinct_office_site_values,
    v.postal_code_values_n_ge_30,
    v.postal_code_values_n_lt_30,
    v.largest_postal_code_cohort,
    v.largest_office_site_cohort,
    v.distinct_postal_code_office_pairs
FROM summary s
CROSS JOIN value_summary v;
