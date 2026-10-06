/*
  Exploratory distribution for Number of manager changes.

  Assumption for this visual: the feature is the number of distinct
  manager_change_date event keys observed in the trailing six months before
  the latest eligible monthly snapshot. A positive manager_change flag is
  required for the event key. Repeated monthly observations of the same
  employee/event date count once.

  Output is aggregate-only. Employee IDs are used inside the CTEs for
  COUNT(DISTINCT ...) and are never selected in the result.
*/
WITH population_rows AS (
    SELECT
        employee_id,
        fis_mo_beg_dt,
        fis_mo_end_dt,
        manager_change,
        manager_change_date
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
event_keys AS (
    SELECT
        employee_id,
        manager_change_date AS event_date,
        MAX(CASE WHEN manager_change = 1 THEN 1 ELSE 0 END) AS has_positive_flag,
        MIN(CASE WHEN manager_change = 1 THEN fis_mo_end_dt END) AS first_positive_snapshot,
        COUNT(*) AS observation_rows,
        SUM(CASE WHEN manager_change = 1 THEN 1 ELSE 0 END) AS positive_flag_rows
    FROM population_rows
    WHERE employee_id IS NOT NULL
      AND manager_change_date IS NOT NULL
    GROUP BY 1, 2
),
canonical_events AS (
    SELECT
        e.employee_id,
        e.event_date,
        e.observation_rows,
        e.positive_flag_rows
    FROM event_keys e
    CROSS JOIN anchor a
    WHERE e.has_positive_flag = 1
      AND e.first_positive_snapshot <= a.snapshot_date
      AND e.event_date > DATEADD(month, -6, a.snapshot_date)
      AND e.event_date <= a.snapshot_date
),
employee_counts AS (
    SELECT
        s.employee_id,
        COUNT(DISTINCT c.event_date) AS event_count
    FROM eligible_snapshot s
    LEFT JOIN canonical_events c
      ON c.employee_id = s.employee_id
    GROUP BY 1
),
buckets AS (
    SELECT
        CASE
            WHEN event_count >= 3 THEN '3+'
            ELSE CAST(event_count AS VARCHAR(10))
        END AS bucket,
        COUNT(*) AS employee_count
    FROM employee_counts
    GROUP BY 1
),
diagnostics AS (
    SELECT
        (SELECT COUNT(*) FROM eligible_snapshot) AS eligible_employees,
        (SELECT COUNT(*) FROM canonical_events) AS distinct_event_keys_in_window,
        (SELECT COALESCE(SUM(CASE WHEN observation_rows > 1 THEN observation_rows - 1 ELSE 0 END), 0)
         FROM canonical_events) AS repeated_event_observation_rows,
        (SELECT COUNT(*)
         FROM population_rows
         WHERE manager_change = 1
           AND manager_change_date IS NULL) AS flagged_without_date_rows,
        (SELECT COUNT(*)
         FROM population_rows
         WHERE manager_change IS NOT NULL
           AND manager_change NOT IN (0, 1)) AS invalid_flag_rows
)
SELECT
    'distribution' AS metric_type,
    b.bucket,
    b.employee_count,
    d.eligible_employees,
    100.0 * b.employee_count / NULLIF(d.eligible_employees, 0) AS employee_percent,
    a.snapshot_date,
    DATEADD(month, -6, a.snapshot_date) AS window_start_exclusive,
    d.distinct_event_keys_in_window,
    d.repeated_event_observation_rows,
    d.flagged_without_date_rows,
    d.invalid_flag_rows
FROM buckets b
CROSS JOIN diagnostics d
CROSS JOIN anchor a
ORDER BY CASE b.bucket WHEN '0' THEN 0 WHEN '1' THEN 1 WHEN '2' THEN 2 ELSE 3 END;
