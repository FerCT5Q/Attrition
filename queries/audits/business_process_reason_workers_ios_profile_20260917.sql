SELECT
    COUNT(*) AS event_rows,
    COUNT(DISTINCT employee_id) AS distinct_employees,
    COUNT(business_process_reason) AS populated_rows,
    SUM(CASE WHEN business_process_reason IS NULL THEN 1 ELSE 0 END) AS null_rows,
    SUM(CASE WHEN business_process_reason IS NOT NULL
                  AND TRIM(business_process_reason) = '' THEN 1 ELSE 0 END) AS blank_rows,
    COUNT(DISTINCT NULLIF(TRIM(business_process_reason), '')) AS distinct_nonblank_values,
    MIN(effective_date) AS first_effective_date,
    MAX(effective_date) AS last_effective_date
FROM hrda.workers_ios_transfers
