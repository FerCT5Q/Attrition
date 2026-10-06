/*
  Aggregate-only preflight for stage 42's 2026 YTD time-zone categories.
  It exposes no office label, worker identifier, manager identifier, or row.
  The normalized MD5 keys are used only in this local builder to select the
  matching IANA mappings from the approved public office catalog.
*/
WITH baseline AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS baseline_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
      AND CAST(fis_mo_end_dt AS DATE) < DATE '2026-01-01'
)
SELECT
    b.baseline_snapshot_date,
    MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '')) AS office_site_key,
    CASE
      WHEN NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
       AND NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
      THEN MD5(
          REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', '')
          || '|' ||
          REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', '')
      )
    END AS city_country_key,
    COUNT(DISTINCT w.employee_id) AS employee_count
FROM hrda.post_hire_monthly_worker_dtls AS w
CROSS JOIN baseline AS b
WHERE CAST(w.fis_mo_end_dt AS DATE) = b.baseline_snapshot_date
  AND w.worker_type = 'Employee'
  AND w.employee_type = 'Regular'
  AND w.active_status = 1
  AND w.employee_id IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY employee_count DESC;
