/*
  Gap audit for the historical current-grade entry-path attrition view.

  Modo de entrega: presentation. Todos los resultados son agregados; no se
  devuelven IDs ni filas de empleados.

  La consulta separa cobertura del campo de tenure, calidad del snapshot,
  estados de atribucion Voluntary y el dominio fijo de bandas. No imputa
  time_in_job_profile_start_date desde tablas antiguas.
*/
WITH
parameters AS (
    SELECT DATE '2026-09-11' AS cutoff_date, 45::INTEGER AS maximum_snapshot_gap_days
),
year_domain AS (
    SELECT 2021::INTEGER AS fiscal_year
    UNION ALL SELECT 2022::INTEGER
    UNION ALL SELECT 2023::INTEGER
    UNION ALL SELECT 2024::INTEGER
    UNION ALL SELECT 2025::INTEGER
),
raw_calendar AS (
    SELECT
        CAST(worker.fis_mo_beg_dt AS DATE) AS period_begin,
        CAST(worker.fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(worker.fiscal_year AS INTEGER) AS fiscal_year,
        MOD(CAST(worker.fiscal_month AS INTEGER), 100) AS fiscal_month
    FROM hrda.post_hire_monthly_worker_dtls AS worker
    CROSS JOIN parameters
    WHERE worker.fis_mo_end_dt IS NOT NULL
      AND CAST(worker.fis_mo_end_dt AS DATE) <= parameters.cutoff_date
    GROUP BY 1, 2, 3, 4
),
selected_periods AS (
    SELECT calendar.period_begin, calendar.snapshot_date, calendar.fiscal_year, calendar.fiscal_month
    FROM raw_calendar AS calendar
    INNER JOIN year_domain AS years USING (fiscal_year)
),
path_domain AS (
    SELECT 'promotion_confirmed_into_current_grade' AS entry_path, 1 AS path_order
    UNION ALL SELECT 'observed_entry_without_registered_promotion', 2
),
tenure_domain AS (
    SELECT 'promotion_confirmed_into_current_grade' AS entry_path, '<1' AS tenure_band, 1 AS band_order
    UNION ALL SELECT 'promotion_confirmed_into_current_grade', '1–<2', 2
    UNION ALL SELECT 'promotion_confirmed_into_current_grade', '2–<4', 3
    UNION ALL SELECT 'promotion_confirmed_into_current_grade', '4–<5', 4
    UNION ALL SELECT 'promotion_confirmed_into_current_grade', '≥5', 5
    UNION ALL SELECT 'observed_entry_without_registered_promotion', '<2', 1
    UNION ALL SELECT 'observed_entry_without_registered_promotion', '2–<3', 2
    UNION ALL SELECT 'observed_entry_without_registered_promotion', '3–<4', 3
    UNION ALL SELECT 'observed_entry_without_registered_promotion', '≥4', 4
),
source_rows AS (
    SELECT
        worker.employee_id,
        CAST(worker.fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(worker.fiscal_year AS INTEGER) AS fiscal_year,
        MOD(CAST(worker.fiscal_month AS INTEGER), 100) AS fiscal_month,
        CAST(worker.fis_mo_beg_dt AS DATE) AS period_begin,
        NULLIF(TRIM(CAST(worker.compensation_grade AS VARCHAR(80))), '') AS compensation_grade,
        CAST(worker.max_hire_rehire_date AS DATE) AS episode_start,
        CAST(worker.time_in_job_profile_start_date AS DATE) AS profile_start_date,
        worker.worker_type,
        worker.employee_type,
        worker.active_status,
        worker.is_promo,
        CAST(worker.promotion_date AS DATE) AS promotion_date,
        CAST(worker.term_date AS DATE) AS term_date,
        UPPER(NULLIF(TRIM(CAST(worker.term_type AS VARCHAR(256))), '')) AS normalized_term_type
    FROM hrda.post_hire_monthly_worker_dtls AS worker
    CROSS JOIN parameters
    WHERE worker.fis_mo_end_dt IS NOT NULL
      AND CAST(worker.fis_mo_end_dt AS DATE) <= parameters.cutoff_date
),
snapshot_grouped AS (
    SELECT
        employee_id,
        snapshot_date,
        MAX(fiscal_year) AS fiscal_year,
        MAX(fiscal_month) AS fiscal_month,
        MAX(period_begin) AS period_begin,
        COUNT(*)::BIGINT AS source_row_count,
        COUNT(DISTINCT COALESCE(worker_type, '<null>'))::BIGINT AS worker_type_variant_count,
        COUNT(DISTINCT COALESCE(employee_type, '<null>'))::BIGINT AS employee_type_variant_count,
        COUNT(DISTINCT COALESCE(CAST(active_status AS VARCHAR(20)), '<null>'))::BIGINT AS active_status_variant_count,
        COUNT(DISTINCT COALESCE(compensation_grade, '<null>'))::BIGINT AS grade_variant_count,
        COUNT(DISTINCT COALESCE(CAST(episode_start AS VARCHAR(32)), '<null>'))::BIGINT AS episode_variant_count,
        COUNT(DISTINCT COALESCE(CAST(profile_start_date AS VARCHAR(32)), '<null>'))::BIGINT AS profile_start_variant_count,
        COUNT(DISTINCT COALESCE(CAST(is_promo AS VARCHAR(20)), '<null>'))::BIGINT AS promo_flag_variant_count,
        COUNT(DISTINCT COALESCE(CAST(promotion_date AS VARCHAR(32)), '<null>'))::BIGINT AS promo_date_variant_count,
        MAX(worker_type) AS snapshot_worker_type,
        MAX(employee_type) AS snapshot_employee_type,
        MAX(active_status) AS snapshot_active_status,
        MAX(compensation_grade) AS snapshot_compensation_grade,
        MAX(episode_start) AS snapshot_episode_start,
        MAX(profile_start_date) AS snapshot_profile_start_date,
        MAX(is_promo) AS snapshot_is_promo,
        MAX(promotion_date) AS snapshot_promotion_date
    FROM source_rows
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
    GROUP BY 1, 2
),
canonical_history AS (
    SELECT
        employee_id,
        snapshot_date,
        fiscal_year,
        fiscal_month,
        period_begin,
        snapshot_compensation_grade AS compensation_grade,
        snapshot_episode_start AS episode_start,
        snapshot_is_promo AS is_promo,
        snapshot_promotion_date AS promotion_date,
        source_row_count,
        grade_variant_count,
        episode_variant_count,
        promo_flag_variant_count,
        promo_date_variant_count
    FROM snapshot_grouped
    WHERE worker_type_variant_count = 1
      AND employee_type_variant_count = 1
      AND grade_variant_count = 1
      AND episode_variant_count = 1
      AND promo_flag_variant_count = 1
      AND promo_date_variant_count = 1
),
target_active_snapshots AS (
    SELECT
        grouped.employee_id,
        grouped.snapshot_date,
        grouped.fiscal_year,
        grouped.fiscal_month,
        grouped.period_begin,
        grouped.snapshot_compensation_grade AS compensation_grade,
        grouped.snapshot_episode_start AS episode_start,
        grouped.snapshot_profile_start_date AS profile_start_date,
        grouped.source_row_count,
        grouped.grade_variant_count,
        grouped.episode_variant_count,
        grouped.profile_start_variant_count,
        grouped.worker_type_variant_count,
        grouped.employee_type_variant_count,
        grouped.active_status_variant_count
    FROM snapshot_grouped AS grouped
    WHERE grouped.worker_type_variant_count = 1
      AND grouped.employee_type_variant_count = 1
      AND grouped.active_status_variant_count = 1
      AND grouped.snapshot_worker_type = 'Employee'
      AND grouped.snapshot_employee_type = 'Regular'
      AND grouped.snapshot_active_status = 1
),
timeline_with_lag AS (
    SELECT
        history.employee_id,
        history.snapshot_date,
        history.compensation_grade,
        history.episode_start,
        history.is_promo,
        history.promotion_date,
        LAG(history.snapshot_date) OVER (PARTITION BY history.employee_id ORDER BY history.snapshot_date) AS raw_previous_snapshot_date,
        LAG(history.compensation_grade) OVER (PARTITION BY history.employee_id ORDER BY history.snapshot_date) AS raw_previous_snapshot_grade
    FROM canonical_history AS history
),
timeline AS (
    SELECT
        timeline.employee_id,
        timeline.snapshot_date,
        timeline.compensation_grade,
        timeline.episode_start,
        timeline.is_promo,
        timeline.promotion_date,
        CASE WHEN timeline.episode_start IS NOT NULL AND timeline.raw_previous_snapshot_date >= timeline.episode_start THEN timeline.raw_previous_snapshot_date END AS previous_snapshot_date,
        CASE WHEN timeline.episode_start IS NOT NULL AND timeline.raw_previous_snapshot_date >= timeline.episode_start THEN timeline.raw_previous_snapshot_grade END AS previous_snapshot_grade
    FROM timeline_with_lag AS timeline
),
observed_entries AS (
    SELECT
        employee_id,
        compensation_grade AS entry_grade,
        episode_start,
        snapshot_date AS entry_snapshot_date,
        previous_snapshot_date,
        previous_snapshot_grade,
        CASE WHEN previous_snapshot_date IS NOT NULL AND DATEDIFF(day, previous_snapshot_date, snapshot_date) <= 45 THEN 1 ELSE 0 END AS valid_entry_window
    FROM timeline
    WHERE compensation_grade IS NOT NULL
      AND previous_snapshot_grade IS NOT NULL
      AND previous_snapshot_grade <> compensation_grade
),
target_entry_candidates AS (
    SELECT
        target.employee_id,
        target.snapshot_date,
        target.compensation_grade,
        target.episode_start,
        entry.entry_snapshot_date,
        entry.previous_snapshot_date,
        entry.previous_snapshot_grade,
        entry.valid_entry_window,
        ROW_NUMBER() OVER (PARTITION BY target.employee_id, target.snapshot_date ORDER BY entry.entry_snapshot_date DESC) AS entry_rank
    FROM target_active_snapshots AS target
    LEFT JOIN observed_entries AS entry
      ON entry.employee_id = target.employee_id
     AND entry.entry_grade = target.compensation_grade
     AND entry.episode_start = target.episode_start
     AND entry.entry_snapshot_date <= target.snapshot_date
),
selected_target_entries AS (
    SELECT employee_id, snapshot_date, compensation_grade, episode_start, entry_snapshot_date, previous_snapshot_date, previous_snapshot_grade, valid_entry_window
    FROM target_entry_candidates
    WHERE entry_rank = 1
),
candidate_promotion_rows AS (
    SELECT history.employee_id, history.snapshot_date AS event_snapshot_date, history.compensation_grade AS event_snapshot_grade, history.promotion_date, history.episode_start
    FROM canonical_history AS history
    WHERE history.is_promo = 1
      AND history.promotion_date IS NOT NULL
      AND history.promotion_date <= history.snapshot_date
      AND history.episode_start IS NOT NULL
      AND history.promotion_date >= history.episode_start
),
valid_target_promotion_matches AS (
    SELECT DISTINCT entry.employee_id, entry.snapshot_date
    FROM selected_target_entries AS entry
    INNER JOIN candidate_promotion_rows AS event
      ON event.employee_id = entry.employee_id
     AND event.episode_start = entry.episode_start
    WHERE entry.entry_snapshot_date IS NOT NULL
      AND entry.valid_entry_window = 1
      AND event.promotion_date > entry.previous_snapshot_date
      AND event.promotion_date <= entry.entry_snapshot_date
      AND event.event_snapshot_grade = entry.compensation_grade
),
classified_targets AS (
    SELECT
        target.employee_id,
        target.snapshot_date,
        target.fiscal_year,
        target.fiscal_month,
        target.period_begin,
        target.compensation_grade,
        target.episode_start,
        target.profile_start_date,
        entry.entry_snapshot_date,
        entry.previous_snapshot_date,
        entry.valid_entry_window,
        CASE
            WHEN target.compensation_grade IS NULL OR target.episode_start IS NULL THEN 'current_grade_entry_not_observable'
            WHEN entry.entry_snapshot_date IS NULL OR entry.valid_entry_window <> 1 THEN 'current_grade_entry_not_observable'
            WHEN promotion.employee_id IS NOT NULL THEN 'promotion_confirmed_into_current_grade'
            ELSE 'observed_entry_without_registered_promotion'
        END AS entry_path
    FROM target_active_snapshots AS target
    LEFT JOIN selected_target_entries AS entry
      ON entry.employee_id = target.employee_id
     AND entry.snapshot_date = target.snapshot_date
    LEFT JOIN valid_target_promotion_matches AS promotion
      ON promotion.employee_id = target.employee_id
     AND promotion.snapshot_date = target.snapshot_date
),
tenure_dates AS (
    SELECT
        classified.employee_id,
        classified.snapshot_date,
        classified.fiscal_year,
        classified.fiscal_month,
        classified.period_begin,
        classified.entry_path,
        classified.episode_start,
        classified.profile_start_date,
        CASE
            WHEN classified.episode_start IS NULL OR classified.profile_start_date IS NULL THEN NULL
            WHEN classified.profile_start_date >= classified.episode_start THEN classified.profile_start_date
            ELSE classified.episode_start
        END AS adjusted_profile_start_date
    FROM classified_targets AS classified
),
classified_snapshots AS (
    SELECT
        tenure.employee_id,
        tenure.snapshot_date,
        tenure.fiscal_year,
        tenure.fiscal_month,
        tenure.period_begin,
        tenure.entry_path,
        CASE
            WHEN tenure.adjusted_profile_start_date IS NULL OR tenure.adjusted_profile_start_date > tenure.snapshot_date THEN NULL
            ELSE DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25
        END AS tenure_years,
        CASE
            WHEN tenure.adjusted_profile_start_date IS NULL OR tenure.adjusted_profile_start_date > tenure.snapshot_date THEN NULL
            WHEN tenure.entry_path = 'promotion_confirmed_into_current_grade' AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 1 THEN '<1'
            WHEN tenure.entry_path = 'promotion_confirmed_into_current_grade' AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 2 THEN '1–<2'
            WHEN tenure.entry_path = 'promotion_confirmed_into_current_grade' AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 4 THEN '2–<4'
            WHEN tenure.entry_path = 'promotion_confirmed_into_current_grade' AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 5 THEN '4–<5'
            WHEN tenure.entry_path = 'promotion_confirmed_into_current_grade' THEN '≥5'
            WHEN tenure.entry_path = 'observed_entry_without_registered_promotion' AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 2 THEN '<2'
            WHEN tenure.entry_path = 'observed_entry_without_registered_promotion' AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 3 THEN '2–<3'
            WHEN tenure.entry_path = 'observed_entry_without_registered_promotion' AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 4 THEN '3–<4'
            WHEN tenure.entry_path = 'observed_entry_without_registered_promotion' THEN '≥4'
            ELSE NULL
        END AS tenure_band
    FROM tenure_dates AS tenure
),
active_valid_snapshots AS (
    SELECT classified.employee_id, classified.snapshot_date, classified.fiscal_year, classified.fiscal_month, classified.period_begin, classified.entry_path, classified.tenure_years, classified.tenure_band
    FROM classified_snapshots AS classified
    INNER JOIN target_active_snapshots AS target
      ON target.employee_id = classified.employee_id
     AND target.snapshot_date = classified.snapshot_date
),
voluntary_events AS (
    SELECT source.employee_id, source.term_date, periods.fiscal_year
    FROM source_rows AS source
    INNER JOIN selected_periods AS periods
      ON source.term_date >= periods.period_begin
     AND source.term_date <= periods.snapshot_date
    WHERE source.worker_type = 'Employee'
      AND source.employee_type = 'Regular'
      AND source.normalized_term_type = 'VOLUNTARY'
      AND source.term_date IS NOT NULL
    GROUP BY 1, 2, 3
),
event_snapshot_candidates AS (
    SELECT
        event.employee_id,
        event.term_date,
        event.fiscal_year,
        snap.snapshot_date,
        snap.entry_path,
        snap.tenure_band,
        ROW_NUMBER() OVER (PARTITION BY event.employee_id, event.term_date, event.fiscal_year ORDER BY snap.snapshot_date DESC) AS snapshot_rank
    FROM voluntary_events AS event
    LEFT JOIN active_valid_snapshots AS snap
      ON snap.employee_id = event.employee_id
     AND snap.snapshot_date < event.term_date
),
selected_event_snapshots AS (
    SELECT employee_id, term_date, fiscal_year, snapshot_date, entry_path, tenure_band
    FROM event_snapshot_candidates
    WHERE snapshot_rank = 1
),
event_reasons AS (
    SELECT
        selected.fiscal_year,
        CASE
            WHEN selected.snapshot_date IS NULL THEN 'no_prior_active_valid_snapshot'
            WHEN selected.entry_path = 'current_grade_entry_not_observable' THEN 'selected_not_observable_path'
            WHEN selected.tenure_band IS NULL THEN 'selected_missing_tenure'
            WHEN domain.entry_path IS NULL THEN 'selected_invalid_tenure_band'
            ELSE 'attributed_to_published_band'
        END AS metric
    FROM selected_event_snapshots AS selected
    LEFT JOIN tenure_domain AS domain
      ON domain.entry_path = selected.entry_path
     AND domain.tenure_band = selected.tenure_band
),
target_quality AS (
    SELECT
        target.fiscal_year,
        COUNT(*)::BIGINT AS active_snapshot_count,
        SUM(CASE WHEN target.profile_start_date IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS profile_start_populated_count,
        SUM(CASE WHEN target.profile_start_date IS NULL THEN 1 ELSE 0 END)::BIGINT AS profile_start_missing_count,
        SUM(CASE WHEN target.profile_start_date > target.snapshot_date THEN 1 ELSE 0 END)::BIGINT AS profile_start_future_count,
        SUM(CASE WHEN classified.entry_path = 'promotion_confirmed_into_current_grade' THEN 1 ELSE 0 END)::BIGINT AS promotion_path_count,
        SUM(CASE WHEN classified.entry_path = 'observed_entry_without_registered_promotion' THEN 1 ELSE 0 END)::BIGINT AS observed_path_count,
        SUM(CASE WHEN classified.entry_path = 'current_grade_entry_not_observable' THEN 1 ELSE 0 END)::BIGINT AS not_observable_path_count
    FROM target_active_snapshots AS target
    INNER JOIN classified_snapshots AS classified
      ON classified.employee_id = target.employee_id
     AND classified.snapshot_date = target.snapshot_date
    GROUP BY 1
),
source_quality AS (
    SELECT
        SUM(CASE WHEN grouped.source_row_count > 1 THEN 1 ELSE 0 END)::BIGINT AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN grouped.grade_variant_count > 1 OR grouped.episode_variant_count > 1 OR grouped.profile_start_variant_count > 1 OR grouped.promo_flag_variant_count > 1 OR grouped.promo_date_variant_count > 1 THEN 1 ELSE 0 END)::BIGINT AS conflicting_employee_snapshot_count
    FROM snapshot_grouped AS grouped
    INNER JOIN selected_periods AS periods
      ON periods.snapshot_date = grouped.snapshot_date
     AND periods.fiscal_year = grouped.fiscal_year
     AND periods.fiscal_month = grouped.fiscal_month
),
domain_counts AS (
    SELECT active.entry_path, active.tenure_band, COUNT(*)::BIGINT AS classified_active_snapshot_count
    FROM active_valid_snapshots AS active
    INNER JOIN tenure_domain AS domain
      ON domain.entry_path = active.entry_path
     AND domain.tenure_band = active.tenure_band
    INNER JOIN selected_periods AS periods
      ON periods.snapshot_date = active.snapshot_date
     AND periods.fiscal_year = active.fiscal_year
     AND periods.fiscal_month = active.fiscal_month
    GROUP BY 1, 2
),
calendar_counts AS (
    SELECT fiscal_year, COUNT(DISTINCT snapshot_date)::BIGINT AS snapshot_count, COUNT(DISTINCT fiscal_month)::BIGINT AS fiscal_month_count
    FROM selected_periods
    GROUP BY 1
),
final_rows AS (
    SELECT 'calendar' AS row_type, calendar.fiscal_year, CAST(NULL AS VARCHAR(80)) AS entry_path, CAST(NULL AS VARCHAR(80)) AS tenure_band, 'snapshot_count' AS metric, calendar.snapshot_count AS metric_value
    FROM calendar_counts AS calendar
    UNION ALL
    SELECT 'calendar', calendar.fiscal_year, NULL, NULL, 'fiscal_month_count', calendar.fiscal_month_count
    FROM calendar_counts AS calendar
    UNION ALL
    SELECT 'snapshot_quality', quality.fiscal_year, NULL, NULL, 'active_snapshot_count', quality.active_snapshot_count
    FROM target_quality AS quality
    UNION ALL
    SELECT 'snapshot_quality', quality.fiscal_year, NULL, NULL, 'profile_start_populated_count', quality.profile_start_populated_count
    FROM target_quality AS quality
    UNION ALL
    SELECT 'snapshot_quality', quality.fiscal_year, NULL, NULL, 'profile_start_missing_count', quality.profile_start_missing_count
    FROM target_quality AS quality
    UNION ALL
    SELECT 'snapshot_quality', quality.fiscal_year, NULL, NULL, 'profile_start_future_count', quality.profile_start_future_count
    FROM target_quality AS quality
    UNION ALL
    SELECT 'snapshot_quality', quality.fiscal_year, 'promotion_confirmed_into_current_grade', NULL, 'path_snapshot_count', quality.promotion_path_count
    FROM target_quality AS quality
    UNION ALL
    SELECT 'snapshot_quality', quality.fiscal_year, 'observed_entry_without_registered_promotion', NULL, 'path_snapshot_count', quality.observed_path_count
    FROM target_quality AS quality
    UNION ALL
    SELECT 'snapshot_quality', quality.fiscal_year, 'current_grade_entry_not_observable', NULL, 'path_snapshot_count', quality.not_observable_path_count
    FROM target_quality AS quality
    UNION ALL
    SELECT 'source_quality', NULL, NULL, NULL, 'duplicate_employee_snapshot_count', quality.duplicate_employee_snapshot_count
    FROM source_quality AS quality
    UNION ALL
    SELECT 'source_quality', NULL, NULL, NULL, 'conflicting_employee_snapshot_count', quality.conflicting_employee_snapshot_count
    FROM source_quality AS quality
    UNION ALL
    SELECT 'event_reason', reasons.fiscal_year, NULL, NULL, reasons.metric, COUNT(*)::BIGINT
    FROM event_reasons AS reasons
    GROUP BY 1, 2, 5
    UNION ALL
    SELECT 'domain_definition', NULL, domain.entry_path, domain.tenure_band, 'fixed_band', 1::BIGINT
    FROM tenure_domain AS domain
    UNION ALL
    SELECT 'domain_observed', NULL, counts.entry_path, counts.tenure_band, 'classified_active_snapshot_count', counts.classified_active_snapshot_count
    FROM domain_counts AS counts
)
SELECT row_type, fiscal_year, entry_path, tenure_band, metric, metric_value
FROM final_rows
ORDER BY
    CASE row_type WHEN 'calendar' THEN 1 WHEN 'snapshot_quality' THEN 2 WHEN 'source_quality' THEN 3 WHEN 'event_reason' THEN 4 WHEN 'domain_definition' THEN 5 ELSE 6 END,
    fiscal_year,
    entry_path,
    tenure_band,
    metric;
