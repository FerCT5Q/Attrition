/*
  Auditoria agregada de alternativas para el tenure de la lamina de
  attrition por via observable de entrada al compensation grade.

  Modo: presentation. El resultado es agregado; los employee_id se usan
  unicamente dentro de COUNT(DISTINCT ...) y joins temporales.

  Este focused run prueba company_tenure_from_original_hire_date dentro de la
  derivacion vigente de la via al grade. Los demas campos candidatos se
  perfilan en current_grade_entry_path_tenure_date_candidates_20260911.sql.
  original_hire_date mide tiempo desde la contratacion original: no es una
  fecha de entrada al compensation grade y no sustituye el ajuste de rehire.

  Regla previa:
    - FY2021-FY2025 debe contener 12 snapshots por anio.
    - La cobertura del candidato debe ser >=95% para ser una sustitucion
      tecnica viable de cobertura.
    - Las bandas del candidato deben mantener minimo mensual y minimo de
      empleados distintos >=30 durante los cinco anios.
    - Los eventos Voluntary se atribuyen al ultimo snapshot activo anterior a
      term_date; no se usa informacion posterior al evento.

  Importante: pasar cobertura no aprueba la semantica. La alineacion de
  levelentrydate con el nivel detallado y su uso como proxy de grade debe
  mantenerse caveatada hasta obtener lineage HRIS.
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
calendar_source AS (
    SELECT
        CAST(fis_mo_beg_dt AS DATE) AS period_begin,
        CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(fiscal_year AS INTEGER) AS fiscal_year,
        MOD(CAST(fiscal_month AS INTEGER), 100) AS fiscal_month
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
    GROUP BY 1, 2, 3, 4
),
selected_periods AS (
    SELECT
        calendar_source.period_begin,
        calendar_source.snapshot_date,
        calendar_source.fiscal_year,
        calendar_source.fiscal_month
    FROM calendar_source
    INNER JOIN year_domain USING (fiscal_year)
),
source_rows AS (
    SELECT
        worker.employee_id,
        CAST(worker.fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(worker.fiscal_year AS INTEGER) AS fiscal_year,
        MOD(CAST(worker.fiscal_month AS INTEGER), 100) AS fiscal_month,
        CAST(worker.fis_mo_beg_dt AS DATE) AS period_begin,
        NULLIF(TRIM(CAST(worker.compensation_grade AS VARCHAR(80))), '') AS compensation_grade,
        NULLIF(TRIM(CAST(worker.job_level_primary_position AS VARCHAR(120))), '') AS detailed_level,
        CAST(worker.max_hire_rehire_date AS DATE) AS episode_start,
        CAST(worker.original_hire_date AS DATE) AS original_hire_date,
        CAST(worker.levelentrydate AS DATE) AS levelentrydate,
        CAST(worker.time_in_role AS DECIMAL(18,6)) AS time_in_role,
        worker.worker_type,
        worker.employee_type,
        worker.active_status,
        worker.is_promo,
        CAST(worker.promotion_date AS DATE) AS promotion_date,
        CAST(worker.term_date AS DATE) AS term_date,
        UPPER(NULLIF(TRIM(CAST(worker.term_type AS VARCHAR(256))), '')) AS normalized_term_type
    FROM hrda.post_hire_monthly_worker_dtls AS worker
    WHERE worker.fis_mo_end_dt IS NOT NULL
      AND CAST(worker.fis_mo_end_dt AS DATE) <= (SELECT cutoff_date FROM parameters)
      AND worker.worker_type = 'Employee'
      AND worker.employee_type = 'Regular'
),
snapshot_grouped AS (
    SELECT
        employee_id,
        snapshot_date,
        MAX(fiscal_year) AS fiscal_year,
        MAX(fiscal_month) AS fiscal_month,
        MAX(period_begin) AS period_begin,
        COUNT(*)::BIGINT AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(active_status AS VARCHAR(20)), '<null>'))::BIGINT AS active_status_variant_count,
        COUNT(DISTINCT COALESCE(compensation_grade, '<null>'))::BIGINT AS grade_variant_count,
        COUNT(DISTINCT COALESCE(detailed_level, '<null>'))::BIGINT AS detailed_level_variant_count,
        COUNT(DISTINCT COALESCE(CAST(episode_start AS VARCHAR(32)), '<null>'))::BIGINT AS episode_variant_count,
        COUNT(DISTINCT COALESCE(CAST(original_hire_date AS VARCHAR(32)), '<null>'))::BIGINT AS original_hire_variant_count,
        COUNT(DISTINCT COALESCE(CAST(levelentrydate AS VARCHAR(32)), '<null>'))::BIGINT AS levelentrydate_variant_count,
        COUNT(DISTINCT COALESCE(CAST(time_in_role AS VARCHAR(64)), '<null>'))::BIGINT AS time_in_role_variant_count,
        COUNT(DISTINCT COALESCE(CAST(is_promo AS VARCHAR(20)), '<null>'))::BIGINT AS promo_flag_variant_count,
        COUNT(DISTINCT COALESCE(CAST(promotion_date AS VARCHAR(32)), '<null>'))::BIGINT AS promotion_date_variant_count,
        MAX(active_status) AS snapshot_active_status,
        MAX(compensation_grade) AS snapshot_compensation_grade,
        MAX(detailed_level) AS snapshot_detailed_level,
        MAX(episode_start) AS snapshot_episode_start,
        MAX(original_hire_date) AS snapshot_original_hire_date,
        MAX(levelentrydate) AS snapshot_levelentrydate,
        MAX(time_in_role) AS snapshot_time_in_role,
        MAX(is_promo) AS snapshot_is_promo,
        MAX(promotion_date) AS snapshot_promotion_date,
        MAX(term_date) AS snapshot_term_date,
        MAX(normalized_term_type) AS snapshot_term_type
    FROM source_rows
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
        snapshot_detailed_level AS detailed_level,
        snapshot_episode_start AS episode_start,
        snapshot_levelentrydate AS levelentrydate,
        snapshot_time_in_role AS time_in_role,
        snapshot_active_status AS active_status,
        snapshot_is_promo AS is_promo,
        snapshot_promotion_date AS promotion_date,
        snapshot_term_date AS term_date,
        snapshot_term_type AS normalized_term_type
    FROM snapshot_grouped
    WHERE grade_variant_count = 1
      AND episode_variant_count = 1
      AND promo_flag_variant_count = 1
      AND promotion_date_variant_count = 1
),
target_active_snapshots AS (
    SELECT
        grouped.employee_id,
        grouped.snapshot_date,
        grouped.fiscal_year,
        grouped.fiscal_month,
        grouped.period_begin,
        grouped.snapshot_compensation_grade AS compensation_grade,
        grouped.snapshot_detailed_level AS detailed_level,
        grouped.snapshot_episode_start AS episode_start,
        grouped.snapshot_original_hire_date AS original_hire_date,
        grouped.snapshot_levelentrydate AS levelentrydate,
        grouped.snapshot_time_in_role AS time_in_role,
        grouped.snapshot_active_status AS active_status,
        grouped.snapshot_is_promo AS is_promo,
        grouped.snapshot_promotion_date AS promotion_date,
        grouped.snapshot_term_date AS term_date,
        grouped.snapshot_term_type AS normalized_term_type
    FROM snapshot_grouped AS grouped
    INNER JOIN selected_periods AS periods
      ON periods.snapshot_date = grouped.snapshot_date
     AND periods.fiscal_year = grouped.fiscal_year
     AND periods.fiscal_month = grouped.fiscal_month
    WHERE grouped.active_status_variant_count = 1
      AND grouped.snapshot_active_status = 1
),
timeline_with_lag AS (
    SELECT
        history.employee_id,
        history.snapshot_date,
        history.fiscal_year,
        history.fiscal_month,
        history.period_begin,
        history.compensation_grade,
        history.detailed_level,
        history.episode_start,
        history.levelentrydate,
        history.time_in_role,
        history.active_status,
        history.is_promo,
        history.promotion_date,
        history.term_date,
        history.normalized_term_type,
        LAG(history.snapshot_date) OVER (PARTITION BY history.employee_id ORDER BY history.snapshot_date) AS previous_snapshot_date,
        LAG(history.compensation_grade) OVER (PARTITION BY history.employee_id ORDER BY history.snapshot_date) AS previous_compensation_grade,
        LAG(history.episode_start) OVER (PARTITION BY history.employee_id ORDER BY history.snapshot_date) AS previous_episode_start
    FROM canonical_history AS history
),
timeline AS (
    SELECT
        timeline_with_lag.employee_id,
        timeline_with_lag.snapshot_date,
        timeline_with_lag.compensation_grade,
        timeline_with_lag.episode_start,
        timeline_with_lag.is_promo,
        timeline_with_lag.promotion_date,
        CASE
            WHEN timeline_with_lag.episode_start IS NOT NULL
             AND timeline_with_lag.previous_snapshot_date >= timeline_with_lag.episode_start
            THEN timeline_with_lag.previous_snapshot_date
            ELSE NULL
        END AS previous_snapshot_date,
        CASE
            WHEN timeline_with_lag.episode_start IS NOT NULL
             AND timeline_with_lag.previous_snapshot_date >= timeline_with_lag.episode_start
            THEN timeline_with_lag.previous_compensation_grade
            ELSE NULL
        END AS previous_compensation_grade
    FROM timeline_with_lag
),
observed_entries AS (
    SELECT
        timeline.employee_id,
        timeline.snapshot_date AS entry_snapshot_date,
        timeline.compensation_grade AS entry_grade,
        timeline.episode_start,
        timeline.previous_snapshot_date,
        timeline.is_promo,
        timeline.promotion_date,
        CASE
            WHEN timeline.previous_snapshot_date IS NOT NULL
             AND DATEDIFF(day, timeline.previous_snapshot_date, timeline.snapshot_date) <= (SELECT maximum_snapshot_gap_days FROM parameters)
             AND timeline.previous_compensation_grade IS NOT NULL
             AND timeline.compensation_grade IS NOT NULL
             AND timeline.previous_compensation_grade <> timeline.compensation_grade
            THEN 1 ELSE 0
        END AS valid_entry_window
    FROM timeline AS timeline
),
target_entry_candidates AS (
    SELECT
        target.employee_id,
        target.snapshot_date,
        target.fiscal_year,
        target.fiscal_month,
        target.period_begin,
        target.compensation_grade,
        target.episode_start,
        target.original_hire_date,
        target.levelentrydate,
        target.time_in_role,
        entry.entry_snapshot_date,
        entry.previous_snapshot_date,
        entry.valid_entry_window,
        entry.is_promo AS entry_is_promo,
        entry.promotion_date AS entry_promotion_date,
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
        fiscal_year,
        fiscal_month,
        period_begin,
        compensation_grade,
        episode_start,
        original_hire_date,
        levelentrydate,
        time_in_role,
        entry_snapshot_date,
        previous_snapshot_date,
        valid_entry_window,
        entry_is_promo,
        entry_promotion_date
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
        target.original_hire_date,
        target.levelentrydate,
        target.time_in_role,
        target.entry_snapshot_date,
        target.previous_snapshot_date,
        target.valid_entry_window,
        target.entry_is_promo,
        target.entry_promotion_date,
        CASE
            WHEN target.compensation_grade IS NULL OR target.episode_start IS NULL THEN 'current_grade_entry_not_observable'
            WHEN target.entry_snapshot_date IS NULL OR target.valid_entry_window <> 1 THEN 'current_grade_entry_not_observable'
            WHEN promotion.employee_id IS NOT NULL
            THEN 'promotion_confirmed_into_current_grade'
            ELSE 'observed_entry_without_registered_promotion'
        END AS entry_path
    FROM selected_target_entries AS target
    LEFT JOIN valid_target_promotion_matches AS promotion
      ON promotion.employee_id = target.employee_id
     AND promotion.snapshot_date = target.snapshot_date
),
candidate_tenure AS (
    SELECT
        classified.employee_id,
        classified.snapshot_date,
        classified.fiscal_year,
        classified.fiscal_month,
        classified.period_begin,
        classified.entry_path,
        'company_tenure_from_original_hire_date' AS candidate,
        classified.original_hire_date AS candidate_start_date,
        CAST(NULL AS DECIMAL(18,6)) AS candidate_years_numeric
    FROM classified_targets AS classified
),
candidate_tenure_banded AS (
    SELECT
        candidate.employee_id,
        candidate.snapshot_date,
        candidate.fiscal_year,
        candidate.fiscal_month,
        candidate.period_begin,
        candidate.entry_path,
        candidate.candidate,
        candidate.candidate_start_date,
        candidate.candidate_years_numeric,
        CASE
            WHEN candidate.candidate = 'company_tenure_from_original_hire_date'
             AND candidate.candidate_start_date IS NOT NULL
             AND candidate.candidate_start_date <= candidate.snapshot_date
            THEN DATEDIFF(day, candidate.candidate_start_date, candidate.snapshot_date) / 365.25
            ELSE NULL
        END AS tenure_years
    FROM candidate_tenure AS candidate
),
candidate_bands AS (
    SELECT
        candidate.employee_id,
        candidate.snapshot_date,
        candidate.fiscal_year,
        candidate.fiscal_month,
        candidate.period_begin,
        candidate.entry_path,
        candidate.candidate,
        candidate.candidate_start_date,
        candidate.candidate_years_numeric,
        candidate.tenure_years,
        CASE
            WHEN candidate.entry_path NOT IN ('promotion_confirmed_into_current_grade', 'observed_entry_without_registered_promotion') THEN NULL
            WHEN candidate.tenure_years IS NULL THEN NULL
            WHEN candidate.entry_path = 'promotion_confirmed_into_current_grade' AND candidate.tenure_years < 1 THEN '<1'
            WHEN candidate.entry_path = 'promotion_confirmed_into_current_grade' AND candidate.tenure_years < 2 THEN '1_to_lt_2'
            WHEN candidate.entry_path = 'promotion_confirmed_into_current_grade' AND candidate.tenure_years < 4 THEN '2_to_lt_4'
            WHEN candidate.entry_path = 'promotion_confirmed_into_current_grade' AND candidate.tenure_years < 5 THEN '4_to_lt_5'
            WHEN candidate.entry_path = 'promotion_confirmed_into_current_grade' THEN 'ge_5'
            WHEN candidate.entry_path = 'observed_entry_without_registered_promotion' AND candidate.tenure_years < 2 THEN '<2'
            WHEN candidate.entry_path = 'observed_entry_without_registered_promotion' AND candidate.tenure_years < 3 THEN '2_to_lt_3'
            WHEN candidate.entry_path = 'observed_entry_without_registered_promotion' AND candidate.tenure_years < 4 THEN '3_to_lt_4'
            WHEN candidate.entry_path = 'observed_entry_without_registered_promotion' THEN 'ge_4'
            ELSE NULL
        END AS tenure_band
    FROM candidate_tenure_banded AS candidate
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
    WHERE source.normalized_term_type = 'VOLUNTARY'
      AND source.term_date IS NOT NULL
    GROUP BY 1, 2, 3
),
event_snapshot_candidates AS (
    SELECT
        event.employee_id,
        event.term_date,
        event.fiscal_year,
        candidate.candidate,
        candidate.snapshot_date,
        candidate.entry_path,
        candidate.tenure_band,
        ROW_NUMBER() OVER (
            PARTITION BY event.employee_id, event.term_date, event.fiscal_year, candidate.candidate
            ORDER BY candidate.snapshot_date DESC
        ) AS snapshot_rank
    FROM voluntary_events AS event
    LEFT JOIN candidate_bands AS candidate
      ON candidate.employee_id = event.employee_id
     AND candidate.snapshot_date < event.term_date
),
selected_event_snapshots AS (
    SELECT
        employee_id,
        term_date,
        fiscal_year,
        candidate,
        snapshot_date,
        entry_path,
        tenure_band
    FROM event_snapshot_candidates
    WHERE snapshot_rank = 1
),
event_reasons AS (
    SELECT
        selected.fiscal_year,
        selected.candidate,
        CASE
            WHEN selected.snapshot_date IS NULL THEN 'no_prior_active_snapshot'
            WHEN selected.entry_path = 'current_grade_entry_not_observable' THEN 'entry_path_not_observable'
            WHEN selected.tenure_band IS NULL THEN 'candidate_tenure_missing_or_invalid'
            ELSE 'attributed_to_candidate_band'
        END AS event_reason,
        COUNT(*)::BIGINT AS event_count
    FROM selected_event_snapshots AS selected
    GROUP BY 1, 2, 3
),
calendar_summary AS (
    SELECT
        'calendar' AS row_type,
        periods.fiscal_year,
        CAST(NULL AS VARCHAR(80)) AS candidate,
        CAST(NULL AS VARCHAR(80)) AS entry_path,
        CAST(NULL AS VARCHAR(80)) AS tenure_band,
        COUNT(DISTINCT periods.snapshot_date)::BIGINT AS snapshot_count,
        COUNT(DISTINCT periods.fiscal_month)::BIGINT AS fiscal_month_count,
        CAST(NULL AS BIGINT) AS eligible_snapshot_count,
        CAST(NULL AS BIGINT) AS populated_snapshot_count,
        CAST(NULL AS BIGINT) AS distinct_employee_count,
        CAST(NULL AS BIGINT) AS minimum_monthly_headcount,
        CAST(NULL AS DECIMAL(18,6)) AS average_monthly_headcount,
        CAST(NULL AS BIGINT) AS voluntary_event_count,
        CAST(NULL AS VARCHAR(80)) AS event_reason
    FROM selected_periods AS periods
    GROUP BY 1, 2
),
source_coverage AS (
    SELECT
        'source_coverage' AS row_type,
        target.fiscal_year,
        candidates.candidate,
        CAST(NULL AS VARCHAR(80)) AS entry_path,
        CAST(NULL AS VARCHAR(80)) AS tenure_band,
        CAST(NULL AS BIGINT) AS snapshot_count,
        CAST(NULL AS BIGINT) AS fiscal_month_count,
        COUNT(*)::BIGINT AS eligible_snapshot_count,
        SUM(CASE
            WHEN candidates.candidate = 'levelentrydate_adjusted'
             AND candidates.candidate_start_date IS NOT NULL
             AND candidates.candidate_start_date <= candidates.snapshot_date THEN 1
            WHEN candidates.candidate IN ('company_tenure_from_max_hire_rehire_date', 'company_tenure_from_original_hire_date')
             AND candidates.candidate_start_date IS NOT NULL
             AND candidates.candidate_start_date <= candidates.snapshot_date THEN 1
            WHEN candidates.candidate = 'time_in_role'
             AND candidates.candidate_years_numeric >= 0 THEN 1
            ELSE 0
        END)::BIGINT AS populated_snapshot_count,
        COUNT(DISTINCT CASE
            WHEN candidates.tenure_years IS NOT NULL THEN candidates.employee_id
        END)::BIGINT AS distinct_employee_count,
        CAST(NULL AS BIGINT) AS minimum_monthly_headcount,
        CAST(NULL AS DECIMAL(18,6)) AS average_monthly_headcount,
        CAST(NULL AS BIGINT) AS voluntary_event_count,
        CAST(NULL AS VARCHAR(80)) AS event_reason
    FROM candidate_tenure_banded AS candidates
    INNER JOIN target_active_snapshots AS target
      ON target.employee_id = candidates.employee_id
     AND target.snapshot_date = candidates.snapshot_date
    GROUP BY 1, 2, 3
),
path_coverage AS (
    SELECT
        'path_coverage' AS row_type,
        candidate.fiscal_year,
        candidate.candidate,
        candidate.entry_path,
        CAST(NULL AS VARCHAR(80)) AS tenure_band,
        CAST(NULL AS BIGINT) AS snapshot_count,
        CAST(NULL AS BIGINT) AS fiscal_month_count,
        COUNT(*)::BIGINT AS eligible_snapshot_count,
        SUM(CASE WHEN candidate.tenure_years IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS populated_snapshot_count,
        COUNT(DISTINCT CASE WHEN candidate.tenure_years IS NOT NULL THEN candidate.employee_id END)::BIGINT AS distinct_employee_count,
        CAST(NULL AS BIGINT) AS minimum_monthly_headcount,
        CAST(NULL AS DECIMAL(18,6)) AS average_monthly_headcount,
        CAST(NULL AS BIGINT) AS voluntary_event_count,
        CAST(NULL AS VARCHAR(80)) AS event_reason
    FROM candidate_tenure_banded AS candidate
    GROUP BY 1, 2, 3, 4
),
band_summary AS (
    SELECT
        'candidate_band' AS row_type,
        candidate.fiscal_year,
        candidate.candidate,
        candidate.entry_path,
        candidate.tenure_band,
        COUNT(DISTINCT candidate.snapshot_date)::BIGINT AS snapshot_count,
        COUNT(DISTINCT candidate.fiscal_month)::BIGINT AS fiscal_month_count,
        COUNT(*)::BIGINT AS eligible_snapshot_count,
        COUNT(*)::BIGINT AS populated_snapshot_count,
        COUNT(DISTINCT candidate.employee_id)::BIGINT AS distinct_employee_count,
        MIN(monthly.monthly_headcount)::BIGINT AS minimum_monthly_headcount,
        AVG(monthly.monthly_headcount)::DECIMAL(18,6) AS average_monthly_headcount,
        CAST(NULL AS BIGINT) AS voluntary_event_count,
        CAST(NULL AS VARCHAR(80)) AS event_reason
    FROM candidate_bands AS candidate
    INNER JOIN (
        SELECT
            fiscal_year,
            candidate,
            entry_path,
            tenure_band,
            snapshot_date,
            COUNT(DISTINCT employee_id)::BIGINT AS monthly_headcount
        FROM candidate_bands
        WHERE tenure_band IS NOT NULL
        GROUP BY 1, 2, 3, 4, 5
    ) AS monthly
      ON monthly.fiscal_year = candidate.fiscal_year
     AND monthly.candidate = candidate.candidate
     AND monthly.entry_path = candidate.entry_path
     AND monthly.tenure_band = candidate.tenure_band
     AND monthly.snapshot_date = candidate.snapshot_date
    WHERE candidate.tenure_band IS NOT NULL
    GROUP BY 1, 2, 3, 4, 5
),
event_summary AS (
    SELECT
        'event_reason' AS row_type,
        reasons.fiscal_year,
        reasons.candidate,
        CAST(NULL AS VARCHAR(80)) AS entry_path,
        CAST(NULL AS VARCHAR(80)) AS tenure_band,
        CAST(NULL AS BIGINT) AS snapshot_count,
        CAST(NULL AS BIGINT) AS fiscal_month_count,
        CAST(NULL AS BIGINT) AS eligible_snapshot_count,
        CAST(NULL AS BIGINT) AS populated_snapshot_count,
        CAST(NULL AS BIGINT) AS distinct_employee_count,
        CAST(NULL AS BIGINT) AS minimum_monthly_headcount,
        CAST(NULL AS DECIMAL(18,6)) AS average_monthly_headcount,
        reasons.event_count AS voluntary_event_count,
        reasons.event_reason
    FROM event_reasons AS reasons
),
final_rows AS (
    SELECT row_type, fiscal_year, candidate, entry_path, tenure_band,
           snapshot_count, fiscal_month_count, eligible_snapshot_count,
           populated_snapshot_count, distinct_employee_count,
           minimum_monthly_headcount, average_monthly_headcount,
           voluntary_event_count, event_reason
    FROM calendar_summary
    UNION ALL
    SELECT row_type, fiscal_year, candidate, entry_path, tenure_band,
           snapshot_count, fiscal_month_count, eligible_snapshot_count,
           populated_snapshot_count, distinct_employee_count,
           minimum_monthly_headcount, average_monthly_headcount,
           voluntary_event_count, event_reason
    FROM source_coverage
    UNION ALL
    SELECT row_type, fiscal_year, candidate, entry_path, tenure_band,
           snapshot_count, fiscal_month_count, eligible_snapshot_count,
           populated_snapshot_count, distinct_employee_count,
           minimum_monthly_headcount, average_monthly_headcount,
           voluntary_event_count, event_reason
    FROM path_coverage
    UNION ALL
    SELECT row_type, fiscal_year, candidate, entry_path, tenure_band,
           snapshot_count, fiscal_month_count, eligible_snapshot_count,
           populated_snapshot_count, distinct_employee_count,
           minimum_monthly_headcount, average_monthly_headcount,
           voluntary_event_count, event_reason
    FROM band_summary
    UNION ALL
    SELECT row_type, fiscal_year, candidate, entry_path, tenure_band,
           snapshot_count, fiscal_month_count, eligible_snapshot_count,
           populated_snapshot_count, distinct_employee_count,
           minimum_monthly_headcount, average_monthly_headcount,
           voluntary_event_count, event_reason
    FROM event_summary
)
SELECT
    row_type,
    fiscal_year,
    candidate,
    entry_path,
    tenure_band,
    snapshot_count,
    fiscal_month_count,
    eligible_snapshot_count,
    populated_snapshot_count,
    distinct_employee_count,
    minimum_monthly_headcount,
    average_monthly_headcount,
    voluntary_event_count,
    event_reason
FROM final_rows
ORDER BY
    CASE row_type
        WHEN 'calendar' THEN 1
        WHEN 'source_coverage' THEN 2
        WHEN 'path_coverage' THEN 3
        WHEN 'candidate_band' THEN 4
        ELSE 5
    END,
    fiscal_year,
    candidate,
    entry_path,
    tenure_band,
    event_reason;
