/*
  Vista agregada de attrition Voluntary por tenure y vía observable de entrada
  al compensation grade actual.

  Modo de entrega: presentation. La consulta no devuelve IDs, nombres ni filas
  de empleados.

  Población: worker_type='Employee', employee_type='Regular', active_status=1.
  Ventana: FY2021-FY2025, con doce snapshots mensuales por año.
  Grain del denominador: empleado-snapshot mensual activo.

  Derivación temporal:
    1. Se reconstruye la última transición observada al grade del snapshot,
       dentro de max_hire_rehire_date.
    2. La transición es válida sólo si tiene snapshot previo completo y el
       hueco entre snapshots no supera 45 días.
    3. La promoción sólo confirma la vía cuando is_promo=1, promotion_date es
       válida, cae después del snapshot previo y hasta el snapshot de entrada,
       y el snapshot del evento conserva el grade de entrada.
    4. El tenure usa
       GREATEST(time_in_job_profile_start_date, max_hire_rehire_date),
       expresado como DATEDIFF(day) / 365.25 y asignado a bandas fijas.
    5. Cada evento Voluntary se asigna al último snapshot activo válido anterior
       a term_date. Si ese snapshot no tiene una de las dos vías observables o
       un tenure válido, el evento queda fuera del numerador publicado.

  Tasa: salidas Voluntary atribuidas / promedio mensual de headcount activo de
  la banda * 100. Los resultados se publican sólo con doce meses y cohortes
  mínimas de 30 empleados distintos y 30 en el mínimo headcount mensual.
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
        MOD(CAST(worker.fiscal_month AS INTEGER), 100) AS fiscal_month_of_year
    FROM hrda.post_hire_monthly_worker_dtls AS worker
    CROSS JOIN parameters
    WHERE worker.fis_mo_end_dt IS NOT NULL
      AND CAST(worker.fis_mo_end_dt AS DATE) <= parameters.cutoff_date
    GROUP BY 1, 2, 3, 4
),
calendar_by_year AS (
    SELECT
        raw_calendar.fiscal_year,
        COUNT(DISTINCT snapshot_date)::BIGINT AS snapshot_count,
        COUNT(DISTINCT fiscal_month_of_year)::BIGINT AS fiscal_month_count,
        MIN(fiscal_month_of_year)::INTEGER AS min_fiscal_month,
        MAX(fiscal_month_of_year)::INTEGER AS max_fiscal_month,
        MIN(period_begin) AS first_period_begin,
        MAX(snapshot_date) AS last_snapshot_date
    FROM raw_calendar
    INNER JOIN year_domain AS years
      ON years.fiscal_year = raw_calendar.fiscal_year
    GROUP BY 1
),
selected_periods AS (
    SELECT
        calendar.period_begin,
        calendar.snapshot_date,
        calendar.fiscal_year,
        calendar.fiscal_month_of_year AS fiscal_month
    FROM raw_calendar AS calendar
    INNER JOIN year_domain AS years USING (fiscal_year)
),
selected_period_summary AS (
    SELECT
        COUNT(*)::BIGINT AS selected_period_count,
        COUNT(DISTINCT snapshot_date)::BIGINT AS selected_snapshot_count,
        COUNT(DISTINCT fiscal_year)::BIGINT AS selected_fiscal_year_count,
        MIN(snapshot_date) AS first_selected_snapshot,
        MAX(snapshot_date) AS last_selected_snapshot,
        SUM(CASE WHEN snapshot_date > DATE '2026-09-11' THEN 1 ELSE 0 END)::BIGINT AS future_selected_periods
    FROM selected_periods
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
        LAG(history.snapshot_date) OVER (
            PARTITION BY history.employee_id ORDER BY history.snapshot_date
        ) AS raw_previous_snapshot_date,
        LAG(history.compensation_grade) OVER (
            PARTITION BY history.employee_id ORDER BY history.snapshot_date
        ) AS raw_previous_snapshot_grade
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
        CASE
            WHEN timeline.episode_start IS NOT NULL
             AND timeline.raw_previous_snapshot_date >= timeline.episode_start
            THEN timeline.raw_previous_snapshot_date
            ELSE NULL
        END AS previous_snapshot_date,
        CASE
            WHEN timeline.episode_start IS NOT NULL
             AND timeline.raw_previous_snapshot_date >= timeline.episode_start
            THEN timeline.raw_previous_snapshot_grade
            ELSE NULL
        END AS previous_snapshot_grade
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
        CASE
            WHEN previous_snapshot_date IS NOT NULL
             AND DATEDIFF(day, previous_snapshot_date, snapshot_date) <= 45
            THEN 1 ELSE 0
        END AS valid_entry_window
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
        ROW_NUMBER() OVER (
            PARTITION BY target.employee_id, target.snapshot_date
            ORDER BY entry.entry_snapshot_date DESC
        ) AS entry_rank
    FROM target_active_snapshots AS target
    LEFT JOIN observed_entries AS entry
      ON entry.employee_id = target.employee_id
     AND entry.entry_grade = target.compensation_grade
     AND entry.episode_start = target.episode_start
     AND entry.entry_snapshot_date <= target.snapshot_date
),
selected_target_entries AS (
    SELECT
        employee_id,
        snapshot_date,
        compensation_grade,
        episode_start,
        entry_snapshot_date,
        previous_snapshot_date,
        previous_snapshot_grade,
        valid_entry_window
    FROM target_entry_candidates
    WHERE entry_rank = 1
),
candidate_promotion_rows AS (
    SELECT
        history.employee_id,
        history.snapshot_date AS event_snapshot_date,
        history.compensation_grade AS event_snapshot_grade,
        history.promotion_date,
        history.episode_start
    FROM canonical_history AS history
    WHERE history.is_promo = 1
      AND history.promotion_date IS NOT NULL
      AND history.promotion_date <= history.snapshot_date
      AND history.episode_start IS NOT NULL
      AND history.promotion_date >= history.episode_start
),
valid_target_promotion_matches AS (
    SELECT DISTINCT
        entry.employee_id,
        entry.snapshot_date
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
        classified.compensation_grade,
        classified.episode_start,
        classified.profile_start_date,
        classified.entry_snapshot_date,
        classified.previous_snapshot_date,
        classified.valid_entry_window,
        classified.entry_path,
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
            WHEN tenure.adjusted_profile_start_date IS NULL
              OR tenure.adjusted_profile_start_date > tenure.snapshot_date
            THEN NULL
            ELSE DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25
        END AS tenure_years,
        CASE
            WHEN tenure.adjusted_profile_start_date IS NULL
              OR tenure.adjusted_profile_start_date > tenure.snapshot_date
            THEN NULL
            WHEN DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) < 0
            THEN NULL
            WHEN tenure.entry_path = 'promotion_confirmed_into_current_grade'
             AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 1
            THEN '<1'
            WHEN tenure.entry_path = 'promotion_confirmed_into_current_grade'
             AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 2
            THEN '1–<2'
            WHEN tenure.entry_path = 'promotion_confirmed_into_current_grade'
             AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 4
            THEN '2–<4'
            WHEN tenure.entry_path = 'promotion_confirmed_into_current_grade'
             AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 5
            THEN '4–<5'
            WHEN tenure.entry_path = 'promotion_confirmed_into_current_grade'
            THEN '≥5'
            WHEN tenure.entry_path = 'observed_entry_without_registered_promotion'
             AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 2
            THEN '<2'
            WHEN tenure.entry_path = 'observed_entry_without_registered_promotion'
             AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 3
            THEN '2–<3'
            WHEN tenure.entry_path = 'observed_entry_without_registered_promotion'
             AND DATEDIFF(day, tenure.adjusted_profile_start_date, tenure.snapshot_date) / 365.25 < 4
            THEN '3–<4'
            WHEN tenure.entry_path = 'observed_entry_without_registered_promotion'
            THEN '≥4'
            ELSE NULL
        END AS tenure_band
    FROM tenure_dates AS tenure
),
active_valid_snapshots AS (
    SELECT
        classified.employee_id,
        classified.snapshot_date,
        classified.fiscal_year,
        classified.fiscal_month,
        classified.period_begin,
        classified.entry_path,
        classified.tenure_years,
        classified.tenure_band
    FROM classified_snapshots AS classified
    INNER JOIN target_active_snapshots AS target
      ON target.employee_id = classified.employee_id
     AND target.snapshot_date = classified.snapshot_date
),
selected_active_snapshots AS (
    SELECT
        classified.employee_id,
        classified.snapshot_date,
        classified.fiscal_year,
        classified.fiscal_month,
        classified.entry_path,
        classified.tenure_band
    FROM active_valid_snapshots AS classified
    INNER JOIN selected_periods AS periods
      ON periods.snapshot_date = classified.snapshot_date
     AND periods.fiscal_year = classified.fiscal_year
     AND periods.fiscal_month = classified.fiscal_month
    INNER JOIN tenure_domain AS bands
      ON bands.entry_path = classified.entry_path
     AND bands.tenure_band = classified.tenure_band
),
monthly_band_counts AS (
    SELECT
        fiscal_year,
        fiscal_month,
        snapshot_date,
        entry_path,
        tenure_band,
        COUNT(DISTINCT employee_id)::BIGINT AS monthly_headcount
    FROM selected_active_snapshots
    GROUP BY 1, 2, 3, 4, 5
),
band_month_grid AS (
    SELECT
        periods.fiscal_year,
        periods.fiscal_month,
        periods.snapshot_date,
        paths.entry_path,
        paths.path_order,
        bands.tenure_band,
        bands.band_order,
        COALESCE(counts.monthly_headcount, 0)::BIGINT AS monthly_headcount
    FROM selected_periods AS periods
    CROSS JOIN tenure_domain AS bands
    INNER JOIN path_domain AS paths
      ON paths.entry_path = bands.entry_path
    LEFT JOIN monthly_band_counts AS counts
      ON counts.fiscal_year = periods.fiscal_year
     AND counts.fiscal_month = periods.fiscal_month
     AND counts.snapshot_date = periods.snapshot_date
     AND counts.entry_path = paths.entry_path
     AND counts.tenure_band = bands.tenure_band
),
annual_band_exposure AS (
    SELECT
        fiscal_year,
        entry_path,
        MAX(path_order) AS path_order,
        tenure_band,
        MAX(band_order) AS band_order,
        COUNT(DISTINCT snapshot_date)::BIGINT AS months_checked,
        COUNT(DISTINCT CASE WHEN monthly_headcount > 0 THEN snapshot_date END)::BIGINT AS months_with_headcount,
        MIN(monthly_headcount)::BIGINT AS min_monthly_headcount,
        MAX(monthly_headcount)::BIGINT AS max_monthly_headcount,
        AVG(monthly_headcount::DECIMAL(18,6)) AS average_monthly_headcount
    FROM band_month_grid
    GROUP BY 1, 2, 4
),
annual_distinct_population AS (
    SELECT
        fiscal_year,
        entry_path,
        tenure_band,
        COUNT(DISTINCT employee_id)::BIGINT AS annual_distinct_employees
    FROM selected_active_snapshots
    GROUP BY 1, 2, 3
),
voluntary_events AS (
    SELECT
        source.employee_id,
        source.term_date,
        periods.fiscal_year
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
        ROW_NUMBER() OVER (
            PARTITION BY event.employee_id, event.term_date, event.fiscal_year
            ORDER BY snap.snapshot_date DESC
        ) AS snapshot_rank
    FROM voluntary_events AS event
    LEFT JOIN active_valid_snapshots AS snap
      ON snap.employee_id = event.employee_id
     AND snap.snapshot_date < event.term_date
),
selected_event_snapshots AS (
    SELECT
        employee_id,
        term_date,
        fiscal_year,
        snapshot_date,
        entry_path,
        tenure_band
    FROM event_snapshot_candidates
    WHERE snapshot_rank = 1
),
attributed_events AS (
    SELECT
        selected.employee_id,
        selected.term_date,
        selected.fiscal_year,
        selected.entry_path,
        selected.tenure_band
    FROM selected_event_snapshots AS selected
    INNER JOIN tenure_domain AS domain
      ON domain.entry_path = selected.entry_path
     AND domain.tenure_band = selected.tenure_band
),
annual_exit_counts AS (
    SELECT
        fiscal_year,
        entry_path,
        tenure_band,
        COUNT(*)::BIGINT AS voluntary_exit_events
    FROM attributed_events
    GROUP BY 1, 2, 3
),
annual_total_events AS (
    SELECT fiscal_year, COUNT(*)::BIGINT AS total_voluntary_events
    FROM voluntary_events
    GROUP BY 1
),
annual_attributed_events AS (
    SELECT fiscal_year, COUNT(*)::BIGINT AS attributed_voluntary_events
    FROM attributed_events
    GROUP BY 1
),
annual_selected_event_states AS (
    SELECT
        selected.fiscal_year,
        COUNT(CASE WHEN selected.snapshot_date IS NULL THEN 1 END)::BIGINT AS no_prior_active_valid_snapshot_events,
        COUNT(CASE WHEN selected.snapshot_date IS NOT NULL AND selected.entry_path = 'current_grade_entry_not_observable' THEN 1 END)::BIGINT AS selected_not_observable_path_events,
        COUNT(CASE WHEN selected.snapshot_date IS NOT NULL AND paths.entry_path IS NOT NULL AND selected.tenure_band IS NULL THEN 1 END)::BIGINT AS selected_missing_tenure_events,
        COUNT(CASE WHEN selected.snapshot_date IS NOT NULL
                        AND paths.entry_path IS NOT NULL
                        AND selected.tenure_band IS NOT NULL
                        AND domains.entry_path IS NULL
                   THEN 1 END)::BIGINT AS selected_invalid_tenure_band_events
    FROM selected_event_snapshots AS selected
    LEFT JOIN path_domain AS paths
      ON paths.entry_path = selected.entry_path
    LEFT JOIN tenure_domain AS domains
      ON domains.entry_path = selected.entry_path
     AND domains.tenure_band = selected.tenure_band
    GROUP BY selected.fiscal_year
),
annual_reconciliation AS (
    SELECT
        years.fiscal_year,
        COALESCE(total.total_voluntary_events, 0)::BIGINT AS total_voluntary_events,
        COALESCE(attributed.attributed_voluntary_events, 0)::BIGINT AS attributed_voluntary_events,
        COALESCE(total.total_voluntary_events, 0)::BIGINT - COALESCE(attributed.attributed_voluntary_events, 0)::BIGINT AS unattributed_voluntary_events,
        COALESCE(SUM(exits.voluntary_exit_events), 0)::BIGINT AS sum_of_band_events,
        COALESCE(SUM(CASE WHEN exposure.months_checked = 12 AND exposure.months_with_headcount = 12 AND COALESCE(population.annual_distinct_employees, 0) >= 30 AND exposure.min_monthly_headcount >= 30 THEN exits.voluntary_exit_events ELSE 0 END), 0)::BIGINT AS sum_of_published_band_events,
        COALESCE(states.no_prior_active_valid_snapshot_events, 0)::BIGINT AS no_prior_active_valid_snapshot_events,
        COALESCE(states.selected_not_observable_path_events, 0)::BIGINT AS selected_not_observable_path_events,
        COALESCE(states.selected_missing_tenure_events, 0)::BIGINT AS selected_missing_tenure_events,
        COALESCE(states.selected_invalid_tenure_band_events, 0)::BIGINT AS selected_invalid_tenure_band_events
    FROM year_domain AS years
    LEFT JOIN annual_total_events AS total
      ON total.fiscal_year = years.fiscal_year
    LEFT JOIN annual_attributed_events AS attributed
      ON attributed.fiscal_year = years.fiscal_year
    LEFT JOIN annual_selected_event_states AS states
      ON states.fiscal_year = years.fiscal_year
    LEFT JOIN annual_band_exposure AS exposure
      ON exposure.fiscal_year = years.fiscal_year
    LEFT JOIN annual_distinct_population AS population
      ON population.fiscal_year = exposure.fiscal_year
     AND population.entry_path = exposure.entry_path
     AND population.tenure_band = exposure.tenure_band
    LEFT JOIN annual_exit_counts AS exits
      ON exits.fiscal_year = exposure.fiscal_year
     AND exits.entry_path = exposure.entry_path
     AND exits.tenure_band = exposure.tenure_band
    GROUP BY 1, 2, 3, 4, 7, 8, 9, 10
),
annual_metrics AS (
    SELECT
        exposure.fiscal_year,
        exposure.entry_path,
        exposure.path_order,
        exposure.tenure_band,
        exposure.band_order,
        exposure.months_checked,
        exposure.months_with_headcount,
        exposure.min_monthly_headcount,
        exposure.max_monthly_headcount,
        exposure.average_monthly_headcount,
        COALESCE(population.annual_distinct_employees, 0)::BIGINT AS annual_distinct_employees,
        COALESCE(exits.voluntary_exit_events, 0)::BIGINT AS voluntary_exit_events,
        COALESCE(reconciliation.total_voluntary_events, 0)::BIGINT AS total_voluntary_events,
        COALESCE(reconciliation.attributed_voluntary_events, 0)::BIGINT AS attributed_voluntary_events,
        CASE
            WHEN exposure.months_checked = 12
             AND exposure.months_with_headcount = 12
             AND COALESCE(population.annual_distinct_employees, 0) >= 30
             AND exposure.min_monthly_headcount >= 30
            THEN 1 ELSE 0
        END AS privacy_eligible,
        CASE
            WHEN exposure.average_monthly_headcount > 0
            THEN ROUND(100.0 * COALESCE(exits.voluntary_exit_events, 0) / exposure.average_monthly_headcount, 4)
            ELSE NULL
        END AS annual_voluntary_attrition_percent
    FROM annual_band_exposure AS exposure
    LEFT JOIN annual_distinct_population AS population
      ON population.fiscal_year = exposure.fiscal_year
     AND population.entry_path = exposure.entry_path
     AND population.tenure_band = exposure.tenure_band
    LEFT JOIN annual_exit_counts AS exits
      ON exits.fiscal_year = exposure.fiscal_year
     AND exits.entry_path = exposure.entry_path
     AND exits.tenure_band = exposure.tenure_band
    LEFT JOIN annual_reconciliation AS reconciliation
      ON reconciliation.fiscal_year = exposure.fiscal_year
),
selected_target_quality AS (
    SELECT
        COUNT(*)::BIGINT AS target_active_snapshot_count,
        SUM(CASE WHEN grade_variant_count > 1 OR episode_variant_count > 1 OR profile_start_variant_count > 1 THEN 1 ELSE 0 END)::BIGINT AS target_active_conflicting_snapshot_count,
        SUM(CASE WHEN compensation_grade IS NULL THEN 1 ELSE 0 END)::BIGINT AS target_missing_grade_count,
        SUM(CASE WHEN episode_start IS NULL THEN 1 ELSE 0 END)::BIGINT AS target_missing_episode_start_count,
        SUM(CASE WHEN profile_start_date IS NULL THEN 1 ELSE 0 END)::BIGINT AS target_missing_profile_start_count,
        SUM(CASE WHEN target.profile_start_date > target.snapshot_date THEN 1 ELSE 0 END)::BIGINT AS target_future_profile_start_count,
        SUM(CASE WHEN classified.entry_path = 'promotion_confirmed_into_current_grade' THEN 1 ELSE 0 END)::BIGINT AS target_promotion_path_count,
        SUM(CASE WHEN classified.entry_path = 'observed_entry_without_registered_promotion' THEN 1 ELSE 0 END)::BIGINT AS target_observed_path_count,
        SUM(CASE WHEN classified.entry_path = 'current_grade_entry_not_observable' THEN 1 ELSE 0 END)::BIGINT AS target_not_observable_path_count,
        SUM(CASE WHEN paths.entry_path IS NOT NULL AND classified.tenure_band IS NULL THEN 1 ELSE 0 END)::BIGINT AS target_invalid_tenure_count
    FROM classified_snapshots AS classified
    INNER JOIN selected_periods AS periods
      ON periods.snapshot_date = classified.snapshot_date
     AND periods.fiscal_year = classified.fiscal_year
     AND periods.fiscal_month = classified.fiscal_month
    INNER JOIN target_active_snapshots AS target
      ON target.employee_id = classified.employee_id
     AND target.snapshot_date = classified.snapshot_date
    LEFT JOIN path_domain AS paths
      ON paths.entry_path = classified.entry_path
),
selected_source_quality AS (
    SELECT
        SUM(CASE WHEN grouped.source_row_count > 1 THEN 1 ELSE 0 END)::BIGINT AS source_duplicate_employee_snapshot_dates,
        SUM(CASE WHEN grouped.grade_variant_count > 1 OR grouped.episode_variant_count > 1 OR grouped.profile_start_variant_count > 1 OR grouped.promo_flag_variant_count > 1 OR grouped.promo_date_variant_count > 1 THEN 1 ELSE 0 END)::BIGINT AS source_conflicting_employee_snapshot_dates
    FROM snapshot_grouped AS grouped
    INNER JOIN selected_periods AS periods
      ON periods.snapshot_date = grouped.snapshot_date
     AND periods.fiscal_year = grouped.fiscal_year
     AND periods.fiscal_month = grouped.fiscal_month
),
final_rows AS (
    SELECT
        'calendar' AS row_type,
        years.fiscal_year,
        CAST(NULL AS VARCHAR(80)) AS entry_path,
        CAST(NULL AS VARCHAR(80)) AS tenure_band,
        COALESCE(calendar.snapshot_count, 0)::BIGINT AS snapshot_count,
        COALESCE(calendar.fiscal_month_count, 0)::BIGINT AS fiscal_month_count,
        calendar.min_fiscal_month,
        calendar.max_fiscal_month,
        calendar.first_period_begin,
        calendar.last_snapshot_date,
        CAST(NULL AS BIGINT) AS months_checked,
        CAST(NULL AS BIGINT) AS months_with_headcount,
        CAST(NULL AS BIGINT) AS min_monthly_headcount,
        CAST(NULL AS BIGINT) AS max_monthly_headcount,
        CAST(NULL AS DECIMAL(18,6)) AS average_monthly_headcount,
        CAST(NULL AS BIGINT) AS annual_distinct_employees,
        CAST(NULL AS BIGINT) AS voluntary_exit_events,
        CAST(NULL AS BIGINT) AS total_voluntary_events,
        CAST(NULL AS BIGINT) AS attributed_voluntary_events,
        CAST(NULL AS BIGINT) AS unattributed_voluntary_events,
        CAST(NULL AS BIGINT) AS sum_of_band_events,
        CAST(NULL AS BIGINT) AS sum_of_published_band_events,
        CAST(NULL AS DECIMAL(18,4)) AS annual_voluntary_attrition_percent,
        CAST(NULL AS INTEGER) AS privacy_eligible,
        CAST(NULL AS BIGINT) AS selected_period_count,
        CAST(NULL AS BIGINT) AS selected_snapshot_count,
        CAST(NULL AS BIGINT) AS selected_fiscal_year_count,
        CAST(NULL AS BIGINT) AS future_selected_periods,
        CAST(NULL AS BIGINT) AS no_prior_active_valid_snapshot_events,
        CAST(NULL AS BIGINT) AS selected_not_observable_path_events,
        CAST(NULL AS BIGINT) AS selected_missing_tenure_events,
        CAST(NULL AS BIGINT) AS selected_invalid_tenure_band_events,
        CAST(NULL AS BIGINT) AS source_duplicate_employee_snapshot_dates,
        CAST(NULL AS BIGINT) AS source_conflicting_employee_snapshot_dates,
        CAST(NULL AS BIGINT) AS target_active_snapshot_count,
        CAST(NULL AS BIGINT) AS target_active_conflicting_snapshot_count,
        CAST(NULL AS BIGINT) AS target_missing_grade_count,
        CAST(NULL AS BIGINT) AS target_missing_episode_start_count,
        CAST(NULL AS BIGINT) AS target_missing_profile_start_count,
        CAST(NULL AS BIGINT) AS target_future_profile_start_count,
        CAST(NULL AS BIGINT) AS target_promotion_path_count,
        CAST(NULL AS BIGINT) AS target_observed_path_count,
        CAST(NULL AS BIGINT) AS target_not_observable_path_count,
        CAST(NULL AS BIGINT) AS target_invalid_tenure_count
    FROM year_domain AS years
    LEFT JOIN calendar_by_year AS calendar
      ON calendar.fiscal_year = years.fiscal_year

    UNION ALL

    SELECT
        'band_year',
        metrics.fiscal_year,
        metrics.entry_path,
        metrics.tenure_band,
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS INTEGER), CAST(NULL AS INTEGER),
        CAST(NULL AS DATE), CAST(NULL AS DATE),
        metrics.months_checked,
        metrics.months_with_headcount,
        metrics.min_monthly_headcount,
        metrics.max_monthly_headcount,
        metrics.average_monthly_headcount,
        metrics.annual_distinct_employees,
        metrics.voluntary_exit_events,
        metrics.total_voluntary_events,
        metrics.attributed_voluntary_events,
        CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT),
        metrics.annual_voluntary_attrition_percent,
        metrics.privacy_eligible,
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT)
    FROM annual_metrics AS metrics

    UNION ALL

    SELECT
        'reconciliation',
        reconciliation.fiscal_year,
        CAST(NULL AS VARCHAR(80)),
        CAST(NULL AS VARCHAR(80)),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS INTEGER), CAST(NULL AS INTEGER),
        CAST(NULL AS DATE), CAST(NULL AS DATE), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,6)), CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT),
        reconciliation.total_voluntary_events,
        reconciliation.attributed_voluntary_events,
        reconciliation.unattributed_voluntary_events,
        reconciliation.sum_of_band_events,
        reconciliation.sum_of_published_band_events,
        CAST(NULL AS DECIMAL(18,4)), CAST(NULL AS INTEGER),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
        reconciliation.no_prior_active_valid_snapshot_events,
        reconciliation.selected_not_observable_path_events,
        reconciliation.selected_missing_tenure_events,
        reconciliation.selected_invalid_tenure_band_events,
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT)
        ,CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT)
    FROM annual_reconciliation AS reconciliation

    UNION ALL

    SELECT
        'source_domain',
        CAST(NULL AS INTEGER),
        CAST(NULL AS VARCHAR(80)),
        CAST(NULL AS VARCHAR(80)),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS INTEGER), CAST(NULL AS INTEGER),
        CAST(NULL AS DATE), CAST(NULL AS DATE), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,6)), CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), CAST(NULL AS INTEGER),
        summary.selected_period_count,
        summary.selected_snapshot_count,
        summary.selected_fiscal_year_count,
        summary.future_selected_periods,
        CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT),
        quality.source_duplicate_employee_snapshot_dates,
        quality.source_conflicting_employee_snapshot_dates,
        target_quality.target_active_snapshot_count,
        target_quality.target_active_conflicting_snapshot_count,
        target_quality.target_missing_grade_count,
        target_quality.target_missing_episode_start_count,
        target_quality.target_missing_profile_start_count,
        target_quality.target_future_profile_start_count,
        target_quality.target_promotion_path_count,
        target_quality.target_observed_path_count,
        target_quality.target_not_observable_path_count,
        target_quality.target_invalid_tenure_count
    FROM selected_period_summary AS summary
    CROSS JOIN selected_source_quality AS quality
    CROSS JOIN selected_target_quality AS target_quality
)
SELECT
    row_type,
    fiscal_year,
    entry_path,
    tenure_band,
    snapshot_count,
    fiscal_month_count,
    min_fiscal_month,
    max_fiscal_month,
    first_period_begin,
    last_snapshot_date,
    months_checked,
    months_with_headcount,
    min_monthly_headcount,
    max_monthly_headcount,
    average_monthly_headcount,
    annual_distinct_employees,
    voluntary_exit_events,
    total_voluntary_events,
    attributed_voluntary_events,
    unattributed_voluntary_events,
    sum_of_band_events,
    sum_of_published_band_events,
    annual_voluntary_attrition_percent,
    privacy_eligible,
    selected_period_count,
    selected_snapshot_count,
    selected_fiscal_year_count,
    future_selected_periods,
    no_prior_active_valid_snapshot_events,
    selected_not_observable_path_events,
    selected_missing_tenure_events,
    selected_invalid_tenure_band_events,
    source_duplicate_employee_snapshot_dates,
    source_conflicting_employee_snapshot_dates,
    target_active_snapshot_count,
    target_active_conflicting_snapshot_count,
    target_missing_grade_count,
    target_missing_episode_start_count,
    target_missing_profile_start_count,
    target_future_profile_start_count,
    target_promotion_path_count,
    target_observed_path_count,
    target_not_observable_path_count,
    target_invalid_tenure_count
FROM final_rows
ORDER BY
    CASE row_type WHEN 'calendar' THEN 1 WHEN 'band_year' THEN 2 WHEN 'reconciliation' THEN 3 ELSE 4 END,
    fiscal_year,
    entry_path,
    tenure_band;
