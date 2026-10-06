/* Aggregate-only execution probe for the manager time-zone YTD cohort. */
WITH baseline AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS baseline_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
      AND CAST(fis_mo_end_dt AS DATE) < DATE '2026-01-01'
),
source_rows AS (
    SELECT
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.manager_employee_id AS BIGINT)) AS manager_employee_id,
        MAX(MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''))) AS office_site_key,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN baseline AS b
    WHERE CAST(w.fis_mo_end_dt AS DATE) = b.baseline_snapshot_date
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1
),
pairs AS (
    SELECT
        employee.employee_id,
        CASE
          WHEN employee.office_site_key IS NOT NULL AND employee.office_site_key = manager.office_site_key THEN 'same_office_site'
          ELSE 'different_or_unmapped_site'
        END AS category
    FROM source_rows AS employee
    INNER JOIN source_rows AS manager
      ON manager.employee_id = employee.manager_employee_id
    WHERE employee.source_row_count = 1
      AND employee.manager_id_variants = 1
      AND manager.source_row_count = 1
)
SELECT category, COUNT(DISTINCT employee_id) AS employee_count
FROM pairs
GROUP BY 1
ORDER BY category;
