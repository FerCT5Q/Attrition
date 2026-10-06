/*
  Presentation-safe sensitivity for Number of manager changes.

  The query returns the established all-event distribution and a second
  distribution that excludes only manager-change events with a positive
  transfer or promotion event for the same employee on the identical effective
  date. It evaluates trailing six- and twelve-month windows at the same
  2026-08-23 monthly snapshot. This is a technical overlap test, not an
  approved replacement for the primary feature definition.
*/
WITH population_rows AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        manager_change,
        manager_change_date,
        is_transferred,
        transfer_date,
        is_promo,
        promotion_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
anchor AS (
    SELECT MAX(fis_mo_end_dt) AS snapshot_date
    FROM population_rows
    WHERE fis_mo_end_dt <= DATE '2026-08-23'
),
windows AS (
    SELECT 6 AS window_months
    UNION ALL
    SELECT 12 AS window_months
),
eligible_snapshot AS (
    SELECT DISTINCT p.employee_id
    FROM population_rows p
    CROSS JOIN anchor a
    WHERE p.employee_id IS NOT NULL
      AND p.fis_mo_end_dt = a.snapshot_date
),
manager_event_keys AS (
    SELECT
        employee_id,
        manager_change_date AS event_date,
        MAX(CASE WHEN manager_change = 1 THEN 1 ELSE 0 END) AS has_positive_flag,
        MIN(CASE WHEN manager_change = 1 THEN fis_mo_end_dt END) AS first_positive_snapshot
    FROM population_rows
    WHERE employee_id IS NOT NULL
      AND manager_change_date IS NOT NULL
    GROUP BY 1, 2
),
transfer_event_keys AS (
    SELECT
        employee_id,
        transfer_date AS event_date,
        MIN(CASE WHEN is_transferred = 1 THEN fis_mo_end_dt END) AS first_positive_snapshot
    FROM population_rows
    WHERE employee_id IS NOT NULL
      AND transfer_date IS NOT NULL
    GROUP BY 1, 2
    HAVING MAX(CASE WHEN is_transferred = 1 THEN 1 ELSE 0 END) = 1
),
promotion_event_keys AS (
    SELECT
        employee_id,
        promotion_date AS event_date,
        MIN(CASE WHEN is_promo = 1 THEN fis_mo_end_dt END) AS first_positive_snapshot
    FROM population_rows
    WHERE employee_id IS NOT NULL
      AND promotion_date IS NOT NULL
    GROUP BY 1, 2
    HAVING MAX(CASE WHEN is_promo = 1 THEN 1 ELSE 0 END) = 1
),
canonical_manager_events AS (
    SELECT
        m.employee_id,
        m.event_date,
        CASE WHEN t.employee_id IS NOT NULL THEN 1 ELSE 0 END AS overlaps_transfer,
        CASE WHEN p.employee_id IS NOT NULL THEN 1 ELSE 0 END AS overlaps_promotion
    FROM manager_event_keys m
    CROSS JOIN anchor a
    LEFT JOIN transfer_event_keys t
      ON t.employee_id = m.employee_id
     AND t.event_date = m.event_date
     AND t.first_positive_snapshot <= a.snapshot_date
    LEFT JOIN promotion_event_keys p
      ON p.employee_id = m.employee_id
     AND p.event_date = m.event_date
     AND p.first_positive_snapshot <= a.snapshot_date
    WHERE m.has_positive_flag = 1
      AND m.first_positive_snapshot <= a.snapshot_date
      AND m.event_date > DATEADD(month, -12, a.snapshot_date)
      AND m.event_date <= a.snapshot_date
),
window_events AS (
    SELECT
        w.window_months,
        e.employee_id,
        e.event_date,
        e.overlaps_transfer,
        e.overlaps_promotion
    FROM windows w
    CROSS JOIN anchor a
    JOIN canonical_manager_events e
      ON e.event_date > DATEADD(month, -w.window_months, a.snapshot_date)
),
employee_counts AS (
    SELECT
        w.window_months,
        s.employee_id,
        COUNT(DISTINCT e.event_date) AS baseline_event_count,
        COUNT(DISTINCT CASE
            WHEN e.overlaps_transfer = 0 AND e.overlaps_promotion = 0 THEN e.event_date
        END) AS excluding_same_date_mobility_count
    FROM windows w
    CROSS JOIN eligible_snapshot s
    LEFT JOIN window_events e
      ON e.window_months = w.window_months
     AND e.employee_id = s.employee_id
    GROUP BY 1, 2
),
annual_vs_six_month AS (
    SELECT COUNT(*) AS annual_count_less_than_six_month_count
    FROM (
        SELECT
            employee_id,
            MAX(CASE WHEN window_months = 6 THEN baseline_event_count END) AS six_month_event_count,
            MAX(CASE WHEN window_months = 12 THEN baseline_event_count END) AS annual_event_count
        FROM employee_counts
        GROUP BY 1
    ) comparison
    WHERE annual_event_count < six_month_event_count
),
distribution AS (
    SELECT
        window_months,
        'baseline' AS comparison,
        CASE WHEN baseline_event_count >= 3 THEN '3+' ELSE CAST(baseline_event_count AS VARCHAR(10)) END AS bucket,
        COUNT(*) AS employee_count
    FROM employee_counts
    GROUP BY 1, 2, 3
    UNION ALL
    SELECT
        window_months,
        'excluding_same_date_transfer_or_promotion' AS comparison,
        CASE WHEN excluding_same_date_mobility_count >= 3 THEN '3+' ELSE CAST(excluding_same_date_mobility_count AS VARCHAR(10)) END AS bucket,
        COUNT(*) AS employee_count
    FROM employee_counts
    GROUP BY 1, 2, 3
),
window_diagnostics AS (
    SELECT
        window_months,
        COUNT(*) AS baseline_event_keys,
        SUM(overlaps_transfer) AS transfer_overlap_event_keys,
        SUM(overlaps_promotion) AS promotion_overlap_event_keys,
        SUM(CASE WHEN overlaps_transfer = 1 OR overlaps_promotion = 1 THEN 1 ELSE 0 END) AS excluded_overlap_event_keys
    FROM window_events
    GROUP BY 1
),
quality_diagnostics AS (
    SELECT
        (SELECT COUNT(*) FROM eligible_snapshot) AS eligible_employees,
        (SELECT COUNT(*) FROM employee_counts WHERE excluding_same_date_mobility_count > baseline_event_count) AS invalid_employee_count_order,
        (SELECT COUNT(*) FROM population_rows WHERE manager_change = 1 AND manager_change_date IS NULL) AS manager_flag_without_date_rows,
        (SELECT COUNT(*) FROM population_rows WHERE is_transferred = 1 AND transfer_date IS NULL) AS transfer_flag_without_date_rows,
        (SELECT COUNT(*) FROM population_rows WHERE is_promo = 1 AND promotion_date IS NULL) AS promotion_flag_without_date_rows
)
SELECT
    d.window_months,
    d.comparison,
    d.bucket,
    d.employee_count,
    q.eligible_employees,
    CAST(100.0 * d.employee_count / NULLIF(q.eligible_employees, 0) AS DECIMAL(18, 6)) AS employee_percent,
    a.snapshot_date,
    DATEADD(month, -d.window_months, a.snapshot_date) AS window_start_exclusive,
    w.baseline_event_keys,
    w.transfer_overlap_event_keys,
    w.promotion_overlap_event_keys,
    w.excluded_overlap_event_keys,
    v.annual_count_less_than_six_month_count,
    q.invalid_employee_count_order,
    q.manager_flag_without_date_rows,
    q.transfer_flag_without_date_rows,
    q.promotion_flag_without_date_rows
FROM distribution d
JOIN window_diagnostics w
  ON w.window_months = d.window_months
CROSS JOIN quality_diagnostics q
CROSS JOIN annual_vs_six_month v
CROSS JOIN anchor a
ORDER BY
    d.window_months,
    CASE d.comparison WHEN 'baseline' THEN 1 ELSE 2 END,
    CASE d.bucket WHEN '0' THEN 0 WHEN '1' THEN 1 WHEN '2' THEN 2 ELSE 3 END;
