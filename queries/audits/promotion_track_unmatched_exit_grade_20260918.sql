/*
  Auditoria agregada del fallback de compensation track para salidas
  voluntarias sin snapshot activo en los 45 dias anteriores al evento.

  No devuelve employee_id, grades, tracks ni filas individuales.
*/
WITH bounds AS (
    SELECT
        DATE '2025-08-24' AS baseline_snapshot_date,
        DATE '2026-08-23' AS cutoff_snapshot_date
),
monthly_grouped AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        w.employee_id,
        MAX(CASE WHEN w.worker_type = 'Employee' AND w.employee_type = 'Regular' THEN 1 ELSE 0 END) AS regular_employee_flag,
        MAX(COALESCE(w.active_status, 0)) AS active_status,
        MAX(COALESCE(w.is_rf360_yes_no, 0)) AS is_rf360_yes_no,
        MAX(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), '')) AS grade_value,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), ''), '<NULL>')) AS grade_variant_count
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
            WHEN grade_value IS NOT NULL
             AND REGEXP_INSTR(UPPER(grade_value), '^[A-Z][0-9]') = 1
              THEN LEFT(UPPER(grade_value), 1)
            ELSE NULL
        END AS track
    FROM monthly_grouped
    WHERE regular_employee_flag = 1
      AND active_status = 1
      AND is_rf360_yes_no = 0
      AND grade_variant_count = 1
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
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(grade_value, '<NULL>')) AS grade_variant_count,
        CASE
            WHEN COUNT(DISTINCT COALESCE(grade_value, '<NULL>')) = 1
             AND MAX(grade_value) IS NOT NULL
             AND REGEXP_INSTR(UPPER(MAX(grade_value)), '^[A-Z][0-9]') = 1
              THEN LEFT(UPPER(MAX(grade_value)), 1)
            ELSE NULL
        END AS termination_track
    FROM termination_rows
    GROUP BY 1, 2
),
candidates AS (
    SELECT
        event.employee_id,
        event.term_date,
        event.source_row_count,
        event.grade_variant_count,
        event.termination_track,
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
    SELECT
        source_row_count,
        grade_variant_count,
        termination_track,
        prior_track,
        COALESCE(prior_track, termination_track) AS final_track
    FROM candidates
    WHERE recency_rank = 1
)
SELECT
    COUNT(*)::BIGINT AS voluntary_event_count,
    SUM(CASE WHEN prior_track IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS prior_active_track_count,
    SUM(CASE WHEN prior_track IS NULL THEN 1 ELSE 0 END)::BIGINT AS no_prior_active_track_count,
    SUM(CASE WHEN prior_track IS NULL AND termination_track IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS fallback_resolved_count,
    SUM(CASE WHEN prior_track IS NULL AND termination_track IS NULL THEN 1 ELSE 0 END)::BIGINT AS unresolved_after_fallback_count,
    SUM(CASE WHEN prior_track IS NULL AND grade_variant_count > 1 THEN 1 ELSE 0 END)::BIGINT AS unmatched_conflicting_term_grade_count,
    SUM(CASE WHEN prior_track IS NOT NULL AND termination_track IS NOT NULL AND prior_track = termination_track THEN 1 ELSE 0 END)::BIGINT AS matched_same_term_track_count,
    SUM(CASE WHEN prior_track IS NOT NULL AND termination_track IS NOT NULL AND prior_track <> termination_track THEN 1 ELSE 0 END)::BIGINT AS matched_different_term_track_count,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END)::BIGINT AS multirow_termination_event_count
FROM assigned;
