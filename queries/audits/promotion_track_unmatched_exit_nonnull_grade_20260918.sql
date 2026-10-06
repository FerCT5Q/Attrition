/*
  Ultima validacion agregada del fallback: para exits sin snapshot activo
  previo, ignora copias nulas pero exige exactamente un grade no nulo y valido
  en todas las filas que registran el evento.
*/
WITH bounds AS (
    SELECT DATE '2025-08-24' AS baseline_snapshot_date, DATE '2026-08-23' AS cutoff_snapshot_date
),
monthly_grouped AS (
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
monthly_active AS (
    SELECT
        snapshot_date,
        employee_id,
        CASE
            WHEN nonnull_grade_variant_count = 1
             AND grade_value IS NOT NULL
             AND REGEXP_INSTR(UPPER(grade_value), '^[A-Z][0-9]') = 1
              THEN LEFT(UPPER(grade_value), 1)
        END AS track
    FROM monthly_grouped
    WHERE regular_employee_flag = 1
      AND active_status = 1
      AND is_rf360_yes_no = 0
),
termination_rows AS (
    SELECT
        w.employee_id,
        CAST(w.term_date AS DATE) AS term_date,
        NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), '') AS grade_value
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN bounds AS b
    WHERE w.employee_id IS NOT NULL
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND COALESCE(w.is_rf360_yes_no, 0) = 0
      AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND CAST(w.term_date AS DATE) > b.baseline_snapshot_date
      AND CAST(w.term_date AS DATE) <= b.cutoff_snapshot_date
),
termination_events AS (
    SELECT
        employee_id,
        term_date,
        MAX(grade_value) AS grade_value,
        COUNT(DISTINCT grade_value) AS nonnull_grade_variant_count,
        SUM(CASE WHEN grade_value IS NULL THEN 1 ELSE 0 END) AS null_grade_row_count,
        CASE
            WHEN COUNT(DISTINCT grade_value) = 1
             AND MAX(grade_value) IS NOT NULL
             AND REGEXP_INSTR(UPPER(MAX(grade_value)), '^[A-Z][0-9]') = 1
              THEN LEFT(UPPER(MAX(grade_value)), 1)
        END AS fallback_track
    FROM termination_rows
    GROUP BY 1, 2
),
candidates AS (
    SELECT
        event.employee_id,
        event.term_date,
        event.nonnull_grade_variant_count,
        event.null_grade_row_count,
        event.fallback_track,
        history.track AS prior_track,
        history.snapshot_date,
        ROW_NUMBER() OVER (
            PARTITION BY event.employee_id, event.term_date
            ORDER BY history.snapshot_date DESC
        ) AS recency_rank
    FROM termination_events AS event
    LEFT JOIN monthly_active AS history
      ON history.employee_id = event.employee_id
     AND history.snapshot_date < event.term_date
     AND DATEDIFF(day, history.snapshot_date, event.term_date) BETWEEN 0 AND 45
),
assigned AS (
    SELECT nonnull_grade_variant_count, null_grade_row_count, prior_track, fallback_track
    FROM candidates
    WHERE recency_rank = 1
)
SELECT
    COUNT(*)::BIGINT AS voluntary_event_count,
    SUM(CASE WHEN prior_track IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS prior_active_track_count,
    SUM(CASE WHEN prior_track IS NULL THEN 1 ELSE 0 END)::BIGINT AS fallback_candidate_event_count,
    SUM(CASE WHEN prior_track IS NULL AND nonnull_grade_variant_count = 1 THEN 1 ELSE 0 END)::BIGINT AS fallback_unique_nonnull_grade_count,
    SUM(CASE WHEN prior_track IS NULL AND nonnull_grade_variant_count > 1 THEN 1 ELSE 0 END)::BIGINT AS fallback_conflicting_nonnull_grade_count,
    SUM(CASE WHEN prior_track IS NULL AND null_grade_row_count > 0 THEN 1 ELSE 0 END)::BIGINT AS fallback_with_null_copies_count,
    SUM(CASE WHEN prior_track IS NULL AND fallback_track IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS fallback_valid_track_count,
    SUM(CASE WHEN prior_track IS NULL AND fallback_track IS NULL THEN 1 ELSE 0 END)::BIGINT AS unresolved_after_stable_nonnull_fallback_count
FROM assigned;
