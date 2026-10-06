/*
  Sensitivity analysis for Number of manager changes.

  It compares the established six-month count with an alternative that excludes
  a manager-change event only when a positive promotion or transfer event for
  the same employee has the identical effective date.  This is a technical
  overlap test, not an approved business definition.  Output is aggregate-only.
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
      AND m.event_date > DATEADD(month, -6, a.snapshot_date)
      AND m.event_date <= a.snapshot_date
),
employee_counts AS (
    SELECT
        s.employee_id,
        COUNT(DISTINCT m.event_date) AS baseline_event_count,
        COUNT(DISTINCT CASE
            WHEN m.overlaps_transfer = 0 AND m.overlaps_promotion = 0 THEN m.event_date
        END) AS excluded_mobility_event_count
    FROM eligible_snapshot s
    LEFT JOIN canonical_manager_events m
      ON m.employee_id = s.employee_id
    GROUP BY 1
),
distribution AS (
    SELECT
        'baseline' AS comparison,
        CASE WHEN baseline_event_count >= 3 THEN '3+' ELSE CAST(baseline_event_count AS VARCHAR(10)) END AS bucket,
        COUNT(*) AS employee_count
    FROM employee_counts
    GROUP BY 1, 2
    UNION ALL
    SELECT
        'excluding_same_date_transfer_or_promotion' AS comparison,
        CASE WHEN excluded_mobility_event_count >= 3 THEN '3+' ELSE CAST(excluded_mobility_event_count AS VARCHAR(10)) END AS bucket,
        COUNT(*) AS employee_count
    FROM employee_counts
    GROUP BY 1, 2
),
diagnostics AS (
    SELECT
        (SELECT COUNT(*) FROM eligible_snapshot) AS eligible_employees,
        (SELECT COUNT(*) FROM canonical_manager_events) AS baseline_event_keys,
        (SELECT COUNT(*) FROM canonical_manager_events WHERE overlaps_transfer = 1) AS transfer_overlap_event_keys,
        (SELECT COUNT(*) FROM canonical_manager_events WHERE overlaps_promotion = 1) AS promotion_overlap_event_keys,
        (SELECT COUNT(*) FROM canonical_manager_events WHERE overlaps_transfer = 1 OR overlaps_promotion = 1) AS excluded_overlap_event_keys,
        (SELECT COUNT(*) FROM employee_counts WHERE excluded_mobility_event_count > baseline_event_count) AS invalid_employee_count_order,
        (SELECT COUNT(*) FROM population_rows WHERE manager_change = 1 AND manager_change_date IS NULL) AS manager_flag_without_date_rows,
        (SELECT COUNT(*) FROM population_rows WHERE is_transferred = 1 AND transfer_date IS NULL) AS transfer_flag_without_date_rows,
        (SELECT COUNT(*) FROM population_rows WHERE is_promo = 1 AND promotion_date IS NULL) AS promotion_flag_without_date_rows
)
SELECT
    d.comparison,
    d.bucket,
    d.employee_count,
    g.eligible_employees,
    CAST(100.0 * d.employee_count / NULLIF(g.eligible_employees, 0) AS DECIMAL(18, 6)) AS employee_percent,
    a.snapshot_date,
    DATEADD(month, -6, a.snapshot_date) AS window_start_exclusive,
    g.baseline_event_keys,
    g.transfer_overlap_event_keys,
    g.promotion_overlap_event_keys,
    g.excluded_overlap_event_keys,
    g.invalid_employee_count_order,
    g.manager_flag_without_date_rows,
    g.transfer_flag_without_date_rows,
    g.promotion_flag_without_date_rows
FROM distribution d
CROSS JOIN diagnostics g
CROSS JOIN anchor a
ORDER BY
    CASE d.comparison WHEN 'baseline' THEN 1 ELSE 2 END,
    CASE d.bucket WHEN '0' THEN 0 WHEN '1' THEN 1 WHEN '2' THEN 2 ELSE 3 END;
