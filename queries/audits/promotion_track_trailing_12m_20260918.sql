/*
  Evidencia agregada para la lamina 30: promotion story by compensation track.

  Corte fijo: 2026-08-23. Baseline exclusivo: 2025-08-24.
  Ventana: doce snapshots mensuales en (baseline, cutoff].

  Track: primera letra de un compensation grade cuyo inicio cumple letra +
  digito. M10, M20 y M30 se colapsan a M; textos como N/A son Unknown.

  Distribucion: Employee + Regular + active_status=1 + no RF360 en agosto.
  Promotion rate: promotion_yes_no='Yes' / participantes AR25 elegibles.
  Attrition rate: exits strict VOLUNTARY / headcount mensual promedio del track.

  El track del exit usa el ultimo snapshot activo anterior dentro de 45 dias;
  si no existe, usa el grade unico y valido almacenado en la fila de
  terminacion, validado por la auditoria complementaria.

  Salida: agregados por track y diagnosticos; ningun identificador se publica.
*/
WITH bounds AS (
    SELECT
        DATE '2026-08-23' AS latest_snapshot_date,
        DATE '2025-08-24' AS baseline_snapshot_date
),
available_snapshot_dates AS (
    SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
window_dates AS (
    SELECT dates.snapshot_date
    FROM available_snapshot_dates AS dates
    CROSS JOIN bounds AS b
    WHERE dates.snapshot_date > b.baseline_snapshot_date
      AND dates.snapshot_date <= b.latest_snapshot_date
),
review_snapshot AS (
    SELECT MAX(dates.snapshot_date) AS review_snapshot_date
    FROM available_snapshot_dates AS dates
    WHERE EXTRACT(year FROM dates.snapshot_date) = 2025
      AND EXTRACT(month FROM dates.snapshot_date) = 11
),
monthly_grouped AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        w.employee_id,
        MAX(CASE WHEN w.worker_type = 'Employee' AND w.employee_type = 'Regular' THEN 1 ELSE 0 END) AS regular_employee_flag,
        MAX(COALESCE(w.active_status, 0)) AS active_status,
        MAX(COALESCE(w.is_rf360_yes_no, 0)) AS is_rf360_yes_no,
        MAX(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), '')) AS grade_value,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(80))), ''), '<NULL>')) AS grade_variant_count
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN bounds AS b
    WHERE CAST(w.fis_mo_end_dt AS DATE) >= DATEADD(day, -45, b.baseline_snapshot_date)
      AND CAST(w.fis_mo_end_dt AS DATE) <= b.latest_snapshot_date
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2
),
monthly_active AS (
    SELECT
        m.snapshot_date,
        m.employee_id,
        m.source_row_count,
        m.grade_variant_count,
        m.grade_value,
        CASE
            WHEN m.grade_value IS NOT NULL
             AND REGEXP_INSTR(UPPER(m.grade_value), '^[A-Z][0-9]') = 1
              THEN LEFT(UPPER(m.grade_value), 1)
            ELSE 'Unknown'
        END AS track
    FROM monthly_grouped AS m
    WHERE m.regular_employee_flag = 1
      AND m.active_status = 1
      AND m.is_rf360_yes_no = 0
),
current_population AS (
    SELECT
        m.snapshot_date,
        m.employee_id,
        m.source_row_count,
        m.grade_variant_count,
        m.grade_value,
        m.track
    FROM monthly_active AS m
    CROSS JOIN bounds AS b
    WHERE m.snapshot_date = b.latest_snapshot_date
),
current_distribution AS (
    SELECT track, COUNT(*)::BIGINT AS current_employee_count
    FROM current_population
    GROUP BY 1
),
current_total AS (
    SELECT COUNT(*)::BIGINT AS current_employee_count
    FROM current_population
),
window_population AS (
    SELECT
        m.snapshot_date,
        m.employee_id,
        m.source_row_count,
        m.grade_variant_count,
        m.grade_value,
        m.track
    FROM monthly_active AS m
    INNER JOIN window_dates AS d ON d.snapshot_date = m.snapshot_date
),
window_tracks AS (
    SELECT DISTINCT track FROM window_population
),
monthly_headcount AS (
    SELECT snapshot_date, track, COUNT(*)::BIGINT AS monthly_headcount
    FROM window_population
    GROUP BY 1, 2
),
track_month_grid AS (
    SELECT d.snapshot_date, t.track
    FROM window_dates AS d
    CROSS JOIN window_tracks AS t
),
track_exposure AS (
    SELECT
        grid.track,
        COUNT(*)::BIGINT AS monthly_snapshot_count,
        AVG(COALESCE(headcount.monthly_headcount, 0)::DECIMAL(18,6)) AS average_monthly_headcount,
        MIN(COALESCE(headcount.monthly_headcount, 0))::BIGINT AS minimum_monthly_headcount,
        MAX(COALESCE(headcount.monthly_headcount, 0))::BIGINT AS maximum_monthly_headcount
    FROM track_month_grid AS grid
    LEFT JOIN monthly_headcount AS headcount
      ON headcount.snapshot_date = grid.snapshot_date
     AND headcount.track = grid.track
    GROUP BY 1
),
review_raw AS (
    SELECT
        NULLIF(TRIM(CAST(ar.employee_id AS VARCHAR(80))), '') AS employee_key,
        NULLIF(TRIM(CAST(ar.grade AS VARCHAR(80))), '') AS grade_value,
        UPPER(NULLIF(TRIM(CAST(ar.promotion_yes_no AS VARCHAR(40))), '')) AS promotion_flag
    FROM hrda.annual_review_report AS ar
    WHERE UPPER(TRIM(CAST(ar.cycle_name AS VARCHAR(160)))) = 'AR25'
),
review_grouped AS (
    SELECT
        employee_key,
        MAX(grade_value) AS grade_value,
        MAX(CASE WHEN promotion_flag = 'YES' THEN 1 ELSE 0 END) AS promoted,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(grade_value, '<NULL>')) AS grade_variant_count,
        COUNT(DISTINCT COALESCE(promotion_flag, '<NULL>')) AS promotion_flag_variant_count,
        MAX(CASE WHEN promotion_flag NOT IN ('YES', 'NO') OR promotion_flag IS NULL THEN 1 ELSE 0 END) AS invalid_promotion_flag
    FROM review_raw
    WHERE employee_key IS NOT NULL
    GROUP BY 1
),
review_joined AS (
    SELECT
        review.employee_key,
        review.grade_value,
        review.promoted,
        review.source_row_count,
        review.grade_variant_count,
        review.promotion_flag_variant_count,
        review.invalid_promotion_flag,
        monthly.employee_id AS matched_employee_id,
        monthly.regular_employee_flag,
        monthly.active_status,
        monthly.is_rf360_yes_no,
        CASE
            WHEN review.grade_value IS NOT NULL
             AND REGEXP_INSTR(UPPER(review.grade_value), '^[A-Z][0-9]') = 1
              THEN LEFT(UPPER(review.grade_value), 1)
            ELSE 'Unknown'
        END AS review_track
    FROM review_grouped AS review
    CROSS JOIN review_snapshot AS review_date
    LEFT JOIN monthly_grouped AS monthly
      ON CAST(monthly.employee_id AS VARCHAR(80)) = review.employee_key
     AND monthly.snapshot_date = review_date.review_snapshot_date
),
review_eligible AS (
    SELECT
        employee_key,
        grade_value,
        promoted,
        source_row_count,
        grade_variant_count,
        promotion_flag_variant_count,
        invalid_promotion_flag,
        matched_employee_id,
        regular_employee_flag,
        active_status,
        is_rf360_yes_no,
        review_track
    FROM review_joined
    WHERE matched_employee_id IS NOT NULL
      AND regular_employee_flag = 1
      AND active_status = 1
      AND is_rf360_yes_no = 0
),
promotion_by_track AS (
    SELECT
        review_track AS track,
        COUNT(*)::BIGINT AS promotion_participant_count,
        SUM(promoted)::BIGINT AS promoted_employee_count,
        ROUND(100.0 * SUM(promoted) / NULLIF(COUNT(*), 0), 4) AS promotion_rate_percent
    FROM review_eligible
    GROUP BY 1
),
voluntary_event_rows AS (
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
      AND CAST(w.term_date AS DATE) <= b.latest_snapshot_date
),
voluntary_event_source AS (
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
    FROM voluntary_event_rows
    GROUP BY 1, 2
),
voluntary_event_candidates AS (
    SELECT
        event.employee_id,
        event.term_date,
        event.termination_track,
        history.track AS prior_track,
        history.snapshot_date,
        ROW_NUMBER() OVER (
            PARTITION BY event.employee_id, event.term_date
            ORDER BY history.snapshot_date DESC
        ) AS recency_rank
    FROM voluntary_event_source AS event
    LEFT JOIN monthly_active AS history
      ON history.employee_id = event.employee_id
     AND history.snapshot_date < event.term_date
     AND DATEDIFF(day, history.snapshot_date, event.term_date) BETWEEN 0 AND 45
),
voluntary_event_assignment AS (
    SELECT
        employee_id,
        term_date,
        prior_track,
        termination_track,
        COALESCE(prior_track, termination_track) AS track,
        CASE
            WHEN prior_track IS NOT NULL THEN 'prior_active_snapshot'
            WHEN termination_track IS NOT NULL THEN 'termination_row_fallback'
            ELSE 'unassigned'
        END AS assignment_source
    FROM voluntary_event_candidates
    WHERE recency_rank = 1
),
attrition_by_track AS (
    SELECT track, COUNT(*)::BIGINT AS voluntary_exit_count
    FROM voluntary_event_assignment
    WHERE track IS NOT NULL
    GROUP BY 1
),
all_tracks AS (
    SELECT track FROM current_distribution
    UNION SELECT track FROM promotion_by_track
    UNION SELECT track FROM track_exposure
    UNION SELECT track FROM attrition_by_track
),
track_rows AS (
    SELECT
        tracks.track,
        COALESCE(current.current_employee_count, 0)::BIGINT AS current_employee_count,
        ROUND(100.0 * COALESCE(current.current_employee_count, 0) / NULLIF(total.current_employee_count, 0), 4) AS current_distribution_percent,
        COALESCE(promotion.promotion_participant_count, 0)::BIGINT AS promotion_participant_count,
        COALESCE(promotion.promoted_employee_count, 0)::BIGINT AS promoted_employee_count,
        CASE WHEN COALESCE(promotion.promotion_participant_count, 0) > 0 THEN promotion.promotion_rate_percent END AS promotion_rate_percent,
        COALESCE(exposure.average_monthly_headcount, 0)::DECIMAL(18,6) AS average_monthly_headcount,
        COALESCE(attrition.voluntary_exit_count, 0)::BIGINT AS voluntary_exit_count,
        CASE
            WHEN COALESCE(exposure.average_monthly_headcount, 0) > 0
              THEN ROUND(100.0 * COALESCE(attrition.voluntary_exit_count, 0) / exposure.average_monthly_headcount, 4)
        END AS attrition_rate_percent
    FROM all_tracks AS tracks
    CROSS JOIN current_total AS total
    LEFT JOIN current_distribution AS current ON current.track = tracks.track
    LEFT JOIN promotion_by_track AS promotion ON promotion.track = tracks.track
    LEFT JOIN track_exposure AS exposure ON exposure.track = tracks.track
    LEFT JOIN attrition_by_track AS attrition ON attrition.track = tracks.track
),
diagnostics AS (
    SELECT 'latest_snapshot_date' AS metric, CAST(latest_snapshot_date AS VARCHAR(64)) AS metric_value FROM bounds
    UNION ALL SELECT 'baseline_snapshot_date', CAST(baseline_snapshot_date AS VARCHAR(64)) FROM bounds
    UNION ALL SELECT 'latest_snapshot_exists', CAST(COUNT(*) AS VARCHAR(64)) FROM available_snapshot_dates CROSS JOIN bounds WHERE snapshot_date = latest_snapshot_date
    UNION ALL SELECT 'baseline_snapshot_exists', CAST(COUNT(*) AS VARCHAR(64)) FROM available_snapshot_dates CROSS JOIN bounds WHERE snapshot_date = baseline_snapshot_date
    UNION ALL SELECT 'window_snapshot_count', CAST(COUNT(*) AS VARCHAR(64)) FROM window_dates
    UNION ALL SELECT 'review_snapshot_date', CAST(review_snapshot_date AS VARCHAR(64)) FROM review_snapshot
    UNION ALL SELECT 'current_population_count', CAST(COUNT(*) AS VARCHAR(64)) FROM current_population
    UNION ALL SELECT 'current_missing_grade_count', CAST(COALESCE(SUM(CASE WHEN grade_value IS NULL THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM current_population
    UNION ALL SELECT 'current_invalid_grade_pattern_count', CAST(COALESCE(SUM(CASE WHEN grade_value IS NOT NULL AND REGEXP_INSTR(UPPER(grade_value), '^[A-Z][0-9]') <> 1 THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM current_population
    UNION ALL SELECT 'current_duplicate_employee_count', CAST(COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM current_population
    UNION ALL SELECT 'current_conflicting_grade_count', CAST(COALESCE(SUM(CASE WHEN grade_variant_count > 1 THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM current_population
    UNION ALL SELECT 'window_employee_snapshot_count', CAST(COUNT(*) AS VARCHAR(64)) FROM window_population
    UNION ALL SELECT 'window_duplicate_employee_snapshot_count', CAST(COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM window_population
    UNION ALL SELECT 'window_conflicting_grade_count', CAST(COALESCE(SUM(CASE WHEN grade_variant_count > 1 THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM window_population
    UNION ALL SELECT 'annual_review_source_row_count', CAST(COUNT(*) AS VARCHAR(64)) FROM review_raw
    UNION ALL SELECT 'annual_review_unique_employee_count', CAST(COUNT(*) AS VARCHAR(64)) FROM review_grouped
    UNION ALL SELECT 'annual_review_duplicate_employee_count', CAST(COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM review_grouped
    UNION ALL SELECT 'annual_review_conflicting_grade_count', CAST(COALESCE(SUM(CASE WHEN grade_variant_count > 1 THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM review_grouped
    UNION ALL SELECT 'annual_review_conflicting_promotion_flag_count', CAST(COALESCE(SUM(CASE WHEN promotion_flag_variant_count > 1 THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM review_grouped
    UNION ALL SELECT 'annual_review_invalid_promotion_flag_count', CAST(COALESCE(SUM(invalid_promotion_flag), 0) AS VARCHAR(64)) FROM review_grouped
    UNION ALL SELECT 'annual_review_missing_grade_count', CAST(COALESCE(SUM(CASE WHEN grade_value IS NULL THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM review_grouped
    UNION ALL SELECT 'annual_review_scope_eligible_count', CAST(COUNT(*) AS VARCHAR(64)) FROM review_eligible
    UNION ALL SELECT 'annual_review_snapshot_unmatched_count', CAST(COALESCE(SUM(CASE WHEN matched_employee_id IS NULL THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM review_joined
    UNION ALL SELECT 'annual_review_scope_excluded_count', CAST(COALESCE(SUM(CASE WHEN matched_employee_id IS NOT NULL AND NOT (regular_employee_flag = 1 AND active_status = 1 AND is_rf360_yes_no = 0) THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM review_joined
    UNION ALL SELECT 'annual_review_promoted_employee_count', CAST(COALESCE(SUM(promoted), 0) AS VARCHAR(64)) FROM review_eligible
    UNION ALL SELECT 'voluntary_event_count', CAST(COUNT(*) AS VARCHAR(64)) FROM voluntary_event_source
    UNION ALL SELECT 'voluntary_event_prior_track_count', CAST(COALESCE(SUM(CASE WHEN assignment_source = 'prior_active_snapshot' THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM voluntary_event_assignment
    UNION ALL SELECT 'voluntary_event_fallback_track_count', CAST(COALESCE(SUM(CASE WHEN assignment_source = 'termination_row_fallback' THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM voluntary_event_assignment
    UNION ALL SELECT 'voluntary_event_unassigned_count', CAST(COALESCE(SUM(CASE WHEN assignment_source = 'unassigned' THEN 1 ELSE 0 END), 0) AS VARCHAR(64)) FROM voluntary_event_assignment
    UNION ALL SELECT 'voluntary_event_track_total', CAST(COALESCE(SUM(voluntary_exit_count), 0) AS VARCHAR(64)) FROM attrition_by_track
    UNION ALL SELECT 'track_count', CAST(COUNT(*) AS VARCHAR(64)) FROM track_rows
)
SELECT
    'track' AS row_type,
    track,
    (SELECT latest_snapshot_date FROM bounds) AS snapshot_date,
    (SELECT baseline_snapshot_date FROM bounds) AS window_start_exclusive,
    (SELECT latest_snapshot_date FROM bounds) AS window_end_inclusive,
    current_employee_count,
    current_distribution_percent,
    promotion_participant_count,
    promoted_employee_count,
    promotion_rate_percent,
    average_monthly_headcount,
    voluntary_exit_count,
    attrition_rate_percent,
    CAST(NULL AS VARCHAR(128)) AS diagnostic_metric,
    CAST(NULL AS VARCHAR(64)) AS diagnostic_value
FROM track_rows
UNION ALL
SELECT
    'diagnostic', CAST(NULL AS VARCHAR(32)), CAST(NULL AS DATE), CAST(NULL AS DATE), CAST(NULL AS DATE),
    CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)), CAST(NULL AS DECIMAL(18,6)), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)),
    metric, metric_value
FROM diagnostics
ORDER BY row_type DESC, current_employee_count DESC, track, diagnostic_metric;
