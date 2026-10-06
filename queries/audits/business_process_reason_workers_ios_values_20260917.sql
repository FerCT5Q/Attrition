WITH reason_counts AS (
    SELECT
        TRIM(business_process_reason) AS reason_value,
        COUNT(*) AS event_rows,
        COUNT(DISTINCT employee_id) AS distinct_employees,
        MIN(effective_date) AS first_effective_date,
        MAX(effective_date) AS last_effective_date
    FROM hrda.workers_ios_transfers
    WHERE business_process_reason IS NOT NULL
      AND TRIM(business_process_reason) <> ''
    GROUP BY 1
)
SELECT
    reason_value,
    event_rows,
    distinct_employees,
    first_effective_date,
    last_effective_date
FROM reason_counts
WHERE distinct_employees >= 30
ORDER BY event_rows DESC, reason_value
