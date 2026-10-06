/*
Claim: the proposed prior-month December 15 snapshot exists as a workforce
snapshot for each January QVoice wave.
Mode: internal_analysis; aggregate-only.
Population: worker_type='Employee', employee_type='Regular', active_status=1.
Acceptance rule: list the stored fis_mo_end_dt values around each proposed
prior-month date and their distinct eligible employee counts. Use an exact
date only when it exists; otherwise document the selected stored date.
*/
WITH target_dates AS (
    SELECT 'Mar-2023' AS wave, DATE '2023-02-15' AS proposed_snapshot
    UNION ALL SELECT 'Jan-2024', DATE '2023-12-15'
    UNION ALL SELECT 'Jan-2025', DATE '2024-12-15'
    UNION ALL SELECT 'Jan-2026', DATE '2025-12-15'
)
SELECT
    t.wave,
    t.proposed_snapshot,
    w.fis_mo_end_dt AS stored_snapshot_date,
    COUNT(*) AS worker_month_rows,
    COUNT(DISTINCT w.employee_id) AS eligible_distinct_employees
FROM target_dates AS t
LEFT JOIN hrda.post_hire_monthly_worker_dtls AS w
  ON w.fis_mo_end_dt BETWEEN t.proposed_snapshot - INTERVAL '31 days'
                          AND t.proposed_snapshot + INTERVAL '31 days'
 AND w.worker_type = 'Employee'
 AND w.employee_type = 'Regular'
 AND w.active_status = 1
GROUP BY 1, 2, 3
ORDER BY 1, 3;
