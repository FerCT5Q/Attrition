/*
  Valida el fallback temporal para exits sin snapshot activo previo.
  Devuelve una sola fila de diagnosticos agregados; no expone IDs, grades ni tracks.
*/
WITH bounds AS (
    SELECT DATE '2025-08-24' AS baseline_snapshot_date, DATE '2026-08-23' AS cutoff_snapshot_date
),
snapshot_grouped AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        w.employee_id,
        MAX(CASE WHEN w.worker_type = 'Employee' AND w.employee_type = 'Regular' THEN 1 ELSE 0 END) AS regular_employee_flag,
        MAX(COALESCE(w.active_status, 0)) AS active_status,
        MAX(COALESCE(w.is_rf360_yes_no, 0)) AS is_rf360_yes_no,
        MAX(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), '')) AS grade_value,
        COUNT(DISTINCT NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), '')) AS nonnull_grade_variant_count
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN bounds AS b
    WHERE CAST(w.fis_mo_end_dt AS DATE) >= DATEADD(day, -45, b.baseline_snapshot_date)
      AND CAST(w.fis_mo_end_dt AS DATE) <= b.cutoff_snapshot_date
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2
),
event_source AS (
    SELECT w.employee_id, CAST(w.term_date AS DATE) AS term_date
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN bounds AS b
    WHERE w.employee_id IS NOT NULL
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND COALESCE(w.is_rf360_yes_no, 0) = 0
      AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND CAST(w.term_date AS DATE) > b.baseline_snapshot_date
      AND CAST(w.term_date AS DATE) <= b.cutoff_snapshot_date
    GROUP BY 1, 2
),
active_candidates AS (
    SELECT
        event.employee_id,
        event.term_date,
        history.snapshot_date,
        CASE
            WHEN history.nonnull_grade_variant_count = 1
             AND history.grade_value IS NOT NULL
             AND REGEXP_INSTR(UPPER(history.grade_value), '^[A-Z][0-9]') = 1
              THEN LEFT(UPPER(history.grade_value), 1)
        END AS track,
        ROW_NUMBER() OVER (
            PARTITION BY event.employee_id, event.term_date
            ORDER BY history.snapshot_date DESC
        ) AS recency_rank
    FROM event_source AS event
    LEFT JOIN snapshot_grouped AS history
      ON history.employee_id = event.employee_id
     AND history.snapshot_date < event.term_date
     AND DATEDIFF(day, history.snapshot_date, event.term_date) BETWEEN 0 AND 45
     AND history.regular_employee_flag = 1
     AND history.active_status = 1
     AND history.is_rf360_yes_no = 0
),
active_assignment AS (
    SELECT employee_id, term_date, track
    FROM active_candidates
    WHERE recency_rank = 1
),
fallback_candidates AS (
    SELECT
        event.employee_id,
        event.term_date,
        history.snapshot_date,
        history.grade_value,
        history.nonnull_grade_variant_count,
        CASE
            WHEN history.nonnull_grade_variant_count = 1
             AND history.grade_value IS NOT NULL
             AND REGEXP_INSTR(UPPER(history.grade_value), '^[A-Z][0-9]') = 1
              THEN LEFT(UPPER(history.grade_value), 1)
        END AS track,
        ROW_NUMBER() OVER (
            PARTITION BY event.employee_id, event.term_date
            ORDER BY history.snapshot_date DESC
        ) AS recency_rank
    FROM event_source AS event
    INNER JOIN active_assignment AS active
      ON active.employee_id = event.employee_id
     AND active.term_date = event.term_date
     AND active.track IS NULL
    LEFT JOIN snapshot_grouped AS history
      ON history.employee_id = event.employee_id
     AND history.snapshot_date <= event.term_date
     AND DATEDIFF(day, history.snapshot_date, event.term_date) BETWEEN 0 AND 45
     AND history.regular_employee_flag = 1
     AND history.is_rf360_yes_no = 0
),
fallback_assignment AS (
    SELECT employee_id, term_date, snapshot_date, grade_value, nonnull_grade_variant_count, track
    FROM fallback_candidates
    WHERE recency_rank = 1
)
SELECT
    (SELECT COUNT(*) FROM event_source)::BIGINT AS voluntary_event_count,
    (SELECT COUNT(*) FROM active_assignment WHERE track IS NOT NULL)::BIGINT AS prior_active_track_count,
    COUNT(*)::BIGINT AS fallback_candidate_event_count,
    SUM(CASE WHEN snapshot_date IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS fallback_snapshot_found_count,
    SUM(CASE WHEN nonnull_grade_variant_count = 1 THEN 1 ELSE 0 END)::BIGINT AS fallback_unique_nonnull_grade_count,
    SUM(CASE WHEN nonnull_grade_variant_count > 1 THEN 1 ELSE 0 END)::BIGINT AS fallback_conflicting_grade_count,
    SUM(CASE WHEN track IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS fallback_valid_track_count,
    SUM(CASE WHEN track IS NULL THEN 1 ELSE 0 END)::BIGINT AS unresolved_after_contemporaneous_fallback_count,
    MAX(CASE WHEN snapshot_date IS NOT NULL THEN DATEDIFF(day, snapshot_date, term_date) END)::BIGINT AS maximum_fallback_age_days
FROM fallback_assignment;
