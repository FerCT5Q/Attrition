/*
  Validación agregada para el slide físico 6 de V8: Engineering vs.
  non-engineering.

  Claim:
    El catálogo Critical Tech (hrda.critical_tech) no es necesariamente
    equivalente a la etiqueta almacenada eng_or_noneng. Esta consulta separa
    el universo que usa un match exacto y único al catálogo Critical Tech del
    universo de empleados regulares activos sin RF360.

  Población y grain:
    Snapshot 2026-08-23; worker_type='Employee'; employee_type='Regular';
    active_status=1; is_rf360_yes_no=0; una fila agregada por employee_id.

  Regla de aceptación:
    El catálogo Critical Tech debe conservar sólo job families con un único
    seg no vacío y distinto de 'Other Eng'. La suma de sus categorías
    eng_or_noneng debe reconciliar al total Critical Tech y no debe haber
    empleados duplicados ni etiquetas eng_or_noneng contradictorias en el
    snapshot. Si existen filas Non_Engineering, se reportan las cinco job
    families Critical Tech más numerosas.

  Salida: sólo métricas y categorías agregadas; no expone empleados, IDs ni
  datos de compensación.
*/
WITH parameters AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
critical_tech_catalog_raw AS (
    SELECT
        LOWER(TRIM(extended_job_family)) AS normalized_job_family,
        NULLIF(TRIM(seg), '') AS critical_tech_segment
    FROM hrda.critical_tech
    WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
),
critical_tech_catalog AS (
    SELECT
        normalized_job_family,
        MIN(critical_tech_segment) AS critical_tech_segment
    FROM critical_tech_catalog_raw
    GROUP BY 1
    HAVING COUNT(DISTINCT critical_tech_segment) = 1
       AND MAX(critical_tech_segment) <> 'Other Eng'
),
active_snapshot_rows AS (
    SELECT
        w.employee_id,
        NULLIF(TRIM(w.job_family), '') AS job_family,
        LOWER(TRIM(w.job_family)) AS normalized_job_family,
        NULLIF(TRIM(w.eng_or_noneng), '') AS eng_or_noneng
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN parameters AS p
    WHERE w.fis_mo_end_dt = p.snapshot_date
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.is_rf360_yes_no = 0
      AND w.employee_id IS NOT NULL
),
active_snapshot_employee AS (
    SELECT
        employee_id,
        MAX(job_family) AS job_family,
        MAX(normalized_job_family) AS normalized_job_family,
        MAX(eng_or_noneng) AS eng_or_noneng,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT eng_or_noneng) AS eng_or_noneng_value_count
    FROM active_snapshot_rows
    GROUP BY 1
),
critical_tech_snapshot AS (
    SELECT
        e.employee_id,
        e.job_family,
        e.eng_or_noneng,
        e.source_row_count,
        e.eng_or_noneng_value_count,
        c.critical_tech_segment
    FROM active_snapshot_employee AS e
    INNER JOIN critical_tech_catalog AS c
        ON c.normalized_job_family = e.normalized_job_family
),
scope_totals AS (
    SELECT
        'All active Regular, non-RF360 employees' AS category,
        COUNT(*) AS employee_count
    FROM active_snapshot_employee
    UNION ALL
    SELECT
        'Exact-match Critical Tech employees' AS category,
        COUNT(*) AS employee_count
    FROM critical_tech_snapshot
    UNION ALL
    SELECT
        'Critical Tech employees labelled Non_Engineering' AS category,
        COUNT(*) AS employee_count
    FROM critical_tech_snapshot
    WHERE eng_or_noneng = 'Non_Engineering'
),
critical_tech_eng_distribution AS (
    SELECT
        COALESCE(eng_or_noneng, '[blank]') AS category,
        COUNT(*) AS employee_count
    FROM critical_tech_snapshot
    GROUP BY 1
),
critical_tech_total AS (
    SELECT COUNT(*) AS employee_count
    FROM critical_tech_snapshot
),
non_engineering_job_families AS (
    SELECT
        job_family,
        critical_tech_segment,
        COUNT(*) AS employee_count,
        ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, job_family, critical_tech_segment) AS rank_within_non_engineering
    FROM critical_tech_snapshot
    WHERE eng_or_noneng = 'Non_Engineering'
    GROUP BY 1, 2
    HAVING COUNT(*) >= 30
),
quality_metrics AS (
    SELECT
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_count,
        SUM(CASE WHEN eng_or_noneng_value_count > 1 THEN 1 ELSE 0 END) AS conflicting_eng_or_noneng_employee_count
    FROM active_snapshot_employee
)
SELECT
    'scope_total' AS result_group,
    NULL::INTEGER AS rank_within_group,
    category,
    NULL::VARCHAR(128) AS critical_tech_segment,
    employee_count,
    NULL::DECIMAL(18, 4) AS percent_of_critical_tech_scope
FROM scope_totals

UNION ALL

SELECT
    'critical_tech_eng_or_noneng_distribution' AS result_group,
    NULL::INTEGER AS rank_within_group,
    category,
    NULL::VARCHAR(128) AS critical_tech_segment,
    employee_count,
    100.0 * employee_count / NULLIF(SUM(employee_count) OVER (), 0) AS percent_of_critical_tech_scope
FROM critical_tech_eng_distribution

UNION ALL

SELECT
    'critical_tech_non_engineering_top_5_job_families' AS result_group,
    rank_within_non_engineering AS rank_within_group,
    job_family AS category,
    critical_tech_segment,
    non_engineering_job_families.employee_count,
    100.0 * non_engineering_job_families.employee_count
        / NULLIF(critical_tech_total.employee_count, 0) AS percent_of_critical_tech_scope
FROM non_engineering_job_families
CROSS JOIN critical_tech_total
WHERE rank_within_non_engineering <= 5

UNION ALL

SELECT
    'snapshot_quality' AS result_group,
    NULL::INTEGER AS rank_within_group,
    'Duplicate employee IDs in active snapshot' AS category,
    NULL::VARCHAR(128) AS critical_tech_segment,
    duplicate_employee_count AS employee_count,
    NULL::DECIMAL(18, 4) AS percent_of_critical_tech_scope
FROM quality_metrics

UNION ALL

SELECT
    'snapshot_quality' AS result_group,
    NULL::INTEGER AS rank_within_group,
    'Employees with conflicting eng_or_noneng labels' AS category,
    NULL::VARCHAR(128) AS critical_tech_segment,
    conflicting_eng_or_noneng_employee_count AS employee_count,
    NULL::DECIMAL(18, 4) AS percent_of_critical_tech_scope
FROM quality_metrics

ORDER BY result_group, rank_within_group NULLS FIRST, employee_count DESC, category;
