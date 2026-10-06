-- Evidencia internal_analysis/agregada para la vía de entrada al compensation
-- grade actual.  Claim: al 2026-08-23 se toma el último cambio OBSERVADO al
-- grade actual, dentro de la última contratación/recontratación. Una promoción
-- lo confirma sólo si el evento válido cae después del snapshot anterior y
-- hasta el snapshot de entrada, y su snapshot de evento conserva el grade
-- actual.  compensation_grade_old se audita contra el snapshot previo, pero
-- queda explícitamente fuera de la derivación porque no reconcilia.
-- Regla de aceptación: el snapshot objetivo y cada employee-snapshot histórico
-- son únicos y no conflictivos; no hay flags/fechas de promoción inválidos;
-- las tres categorías se reconcilian al denominador; y la evidencia de
-- compensation_grade_old muestra al menos una discrepancia con el snapshot
-- previo. Los gaps y grades históricos faltantes se miden y hacen que la
-- entrada no sea observable cuando no existe un cambio previo completo.
WITH params AS (
    SELECT DATE '2026-08-23' AS cutoff_date, 45::INTEGER AS maximum_monthly_gap_days
),
target_rows AS (
    SELECT
        employee_id,
        NULLIF(TRIM(CAST(compensation_grade AS VARCHAR(80))), '') AS compensation_grade,
        max_hire_rehire_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT cutoff_date FROM params)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
target_grouped AS (
    SELECT
        employee_id,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(compensation_grade, '<null>')) AS grade_variant_count,
        COUNT(DISTINCT COALESCE(CAST(max_hire_rehire_date AS VARCHAR(10)), '<null>')) AS episode_variant_count,
        MAX(compensation_grade) AS current_compensation_grade,
        MAX(max_hire_rehire_date) AS current_episode_start
    FROM target_rows
    GROUP BY employee_id
),
target_canonical AS (
    SELECT employee_id, current_compensation_grade, current_episode_start
    FROM target_grouped
),
all_history_rows AS (
    SELECT
        history.employee_id,
        history.fis_mo_end_dt AS snapshot_date,
        NULLIF(TRIM(CAST(history.compensation_grade AS VARCHAR(80))), '') AS compensation_grade,
        NULLIF(TRIM(CAST(history.compensation_grade_old AS VARCHAR(80))), '') AS compensation_grade_old,
        history.is_promo,
        history.promotion_date,
        target.current_compensation_grade,
        target.current_episode_start
    FROM hrda.post_hire_monthly_worker_dtls AS history
    INNER JOIN target_canonical AS target
      ON target.employee_id = history.employee_id
    WHERE history.fis_mo_end_dt <= (SELECT cutoff_date FROM params)
),
history_rows AS (
    SELECT
        employee_id,
        snapshot_date,
        compensation_grade,
        compensation_grade_old,
        is_promo,
        promotion_date,
        current_compensation_grade,
        current_episode_start
    FROM all_history_rows
    WHERE snapshot_date >= current_episode_start
),
history_snapshot_grouped AS (
    SELECT
        employee_id,
        snapshot_date,
        MAX(current_compensation_grade) AS current_compensation_grade,
        MAX(current_episode_start) AS current_episode_start,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(compensation_grade, '<null>')) AS grade_variant_count,
        COUNT(DISTINCT COALESCE(compensation_grade_old, '<null>')) AS old_grade_variant_count,
        COUNT(DISTINCT COALESCE(CAST(is_promo AS VARCHAR(12)), '<null>')) AS promo_flag_variant_count,
        COUNT(DISTINCT COALESCE(CAST(promotion_date AS VARCHAR(10)), '<null>')) AS promo_date_variant_count,
        MAX(compensation_grade) AS snapshot_compensation_grade,
        MAX(compensation_grade_old) AS snapshot_compensation_grade_old,
        MAX(is_promo) AS snapshot_is_promo,
        MAX(promotion_date) AS snapshot_promotion_date
    FROM history_rows
    GROUP BY employee_id, snapshot_date
),
timeline AS (
    SELECT
        history.employee_id,
        history.snapshot_date,
        history.current_compensation_grade,
        history.current_episode_start,
        history.source_row_count,
        history.grade_variant_count,
        history.old_grade_variant_count,
        history.promo_flag_variant_count,
        history.promo_date_variant_count,
        history.snapshot_compensation_grade,
        history.snapshot_compensation_grade_old,
        history.snapshot_is_promo,
        history.snapshot_promotion_date,
        LAG(snapshot_date) OVER (PARTITION BY employee_id ORDER BY snapshot_date) AS previous_snapshot_date,
        LAG(snapshot_compensation_grade) OVER (PARTITION BY employee_id ORDER BY snapshot_date) AS previous_snapshot_grade
    FROM history_snapshot_grouped AS history
),
observed_current_grade_entries AS (
    SELECT
        employee_id,
        current_compensation_grade,
        current_episode_start,
        snapshot_date AS entry_snapshot_date,
        previous_snapshot_date,
        previous_snapshot_grade,
        ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY snapshot_date DESC) AS entry_recency_rank
    FROM timeline
    WHERE snapshot_compensation_grade = current_compensation_grade
      AND previous_snapshot_grade IS NOT NULL
      AND previous_snapshot_grade <> current_compensation_grade
),
selected_current_grade_entries AS (
    SELECT
        employee_id,
        current_compensation_grade,
        current_episode_start,
        entry_snapshot_date,
        previous_snapshot_date,
        previous_snapshot_grade,
        entry_recency_rank
    FROM observed_current_grade_entries
    WHERE entry_recency_rank = 1
),
candidate_promotion_rows AS (
    SELECT
        history.employee_id,
        history.snapshot_date AS event_snapshot_date,
        history.snapshot_compensation_grade AS event_snapshot_grade,
        history.snapshot_promotion_date AS promotion_date,
        history.current_episode_start
    FROM history_snapshot_grouped AS history
    WHERE history.snapshot_is_promo = 1
      AND history.snapshot_promotion_date IS NOT NULL
      AND history.snapshot_promotion_date <= (SELECT cutoff_date FROM params)
      AND history.snapshot_promotion_date <= history.snapshot_date
      AND history.snapshot_promotion_date >= history.current_episode_start
),
entry_window_promotion_rows AS (
    SELECT
        event.employee_id,
        event.promotion_date,
        event.event_snapshot_date,
        event.event_snapshot_grade,
        entry.current_compensation_grade,
        entry.entry_snapshot_date,
        entry.previous_snapshot_date
    FROM candidate_promotion_rows AS event
    INNER JOIN selected_current_grade_entries AS entry
      ON entry.employee_id = event.employee_id
    WHERE event.promotion_date > entry.previous_snapshot_date
      AND event.promotion_date <= entry.entry_snapshot_date
),
valid_entry_promotion_pairs AS (
    SELECT DISTINCT employee_id, promotion_date
    FROM entry_window_promotion_rows
    WHERE event_snapshot_grade = current_compensation_grade
),
employees_with_valid_entry_promotion AS (
    SELECT DISTINCT employee_id FROM valid_entry_promotion_pairs
),
classified AS (
    SELECT
        target.employee_id,
        target.current_compensation_grade,
        CASE
            WHEN entry.employee_id IS NULL THEN 'current_grade_entry_not_observable'
            WHEN valid.employee_id IS NOT NULL THEN 'promotion_confirmed_into_current_grade'
            ELSE 'observed_entry_without_registered_promotion'
        END AS category_key
    FROM target_canonical AS target
    LEFT JOIN selected_current_grade_entries AS entry
      ON entry.employee_id = target.employee_id
    LEFT JOIN employees_with_valid_entry_promotion AS valid
      ON valid.employee_id = target.employee_id
),
classification_counts AS (
    SELECT category_key, COUNT(*)::BIGINT AS employee_count
    FROM classified
    GROUP BY category_key
),
entry_counts AS (
    SELECT
        COUNT(*)::BIGINT AS observed_entry_count,
        COUNT(DISTINCT employee_id)::BIGINT AS employees_with_observed_entry_count,
        COUNT(DISTINCT CASE WHEN entry_recency_rank > 1 THEN employee_id END)::BIGINT AS employees_with_multiple_observed_entries_count,
        COALESCE(SUM(CASE WHEN entry_recency_rank > 1 THEN 1 ELSE 0 END), 0)::BIGINT AS older_observed_entries_not_selected_count,
        COALESCE(SUM(CASE WHEN previous_snapshot_date IS NOT NULL AND DATEDIFF(day, previous_snapshot_date, entry_snapshot_date) > (SELECT maximum_monthly_gap_days FROM params) THEN 1 ELSE 0 END), 0)::BIGINT AS selected_entries_after_gap_over_45_days_count
    FROM observed_current_grade_entries
),
old_grade_reconciliation AS (
    SELECT
        COUNT(CASE WHEN previous_snapshot_grade IS NOT NULL AND snapshot_compensation_grade_old IS NOT NULL THEN 1 END)::BIGINT AS comparable_old_grade_snapshot_count,
        COUNT(CASE WHEN previous_snapshot_grade IS NOT NULL AND snapshot_compensation_grade_old = previous_snapshot_grade THEN 1 END)::BIGINT AS old_grade_matches_previous_snapshot_count,
        COUNT(CASE WHEN previous_snapshot_grade IS NOT NULL AND snapshot_compensation_grade_old IS NOT NULL AND snapshot_compensation_grade_old <> previous_snapshot_grade THEN 1 END)::BIGINT AS old_grade_mismatch_previous_snapshot_count,
        COUNT(CASE WHEN previous_snapshot_grade IS NOT NULL AND snapshot_compensation_grade_old IS NULL THEN 1 END)::BIGINT AS old_grade_blank_with_previous_snapshot_count
    FROM timeline
)
SELECT (SELECT cutoff_date FROM params) AS snapshot_date, 'metric' AS row_type, 'target_source_row_count' AS metric, COUNT(*)::BIGINT AS metric_value FROM target_rows
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'target_missing_employee_id_row_count', COALESCE(SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END), 0)::BIGINT FROM target_rows
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'target_unique_employee_count', COUNT(*)::BIGINT FROM target_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'target_duplicate_employee_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'target_duplicate_row_excess_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN source_row_count - 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'target_conflicting_grade_count', COALESCE(SUM(CASE WHEN grade_variant_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'target_conflicting_episode_count', COALESCE(SUM(CASE WHEN episode_variant_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'target_missing_compensation_grade_count', COALESCE(SUM(CASE WHEN current_compensation_grade IS NULL THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'target_missing_episode_start_count', COALESCE(SUM(CASE WHEN current_episode_start IS NULL THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'target_episode_start_future_count', COALESCE(SUM(CASE WHEN current_episode_start > (SELECT cutoff_date FROM params) THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'history_source_row_count', COUNT(*)::BIGINT FROM history_rows
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'history_duplicate_employee_snapshot_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM history_snapshot_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'history_duplicate_snapshot_row_excess_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN source_row_count - 1 ELSE 0 END), 0)::BIGINT FROM history_snapshot_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'history_conflicting_grade_snapshot_count', COALESCE(SUM(CASE WHEN grade_variant_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM history_snapshot_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'history_missing_grade_snapshot_count', COALESCE(SUM(CASE WHEN snapshot_compensation_grade IS NULL THEN 1 ELSE 0 END), 0)::BIGINT FROM history_snapshot_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'history_conflicting_event_snapshot_count', COALESCE(SUM(CASE WHEN promo_flag_variant_count > 1 OR promo_date_variant_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM history_snapshot_grouped
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'history_snapshot_gap_over_45_days_count', COALESCE(SUM(CASE WHEN previous_snapshot_date IS NOT NULL AND DATEDIFF(day, previous_snapshot_date, snapshot_date) > (SELECT maximum_monthly_gap_days FROM params) THEN 1 ELSE 0 END), 0)::BIGINT FROM timeline
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'invalid_promo_flag_count', COALESCE(SUM(CASE WHEN is_promo IS NULL OR is_promo NOT IN (0, 1) THEN 1 ELSE 0 END), 0)::BIGINT FROM history_rows
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'promo_flag_without_date_count', COALESCE(SUM(CASE WHEN is_promo = 1 AND promotion_date IS NULL THEN 1 ELSE 0 END), 0)::BIGINT FROM history_rows
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'promotion_date_without_promo_flag_count', COALESCE(SUM(CASE WHEN promotion_date IS NOT NULL AND (is_promo IS NULL OR is_promo <> 1) THEN 1 ELSE 0 END), 0)::BIGINT FROM history_rows
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'future_promotion_date_count', COALESCE(SUM(CASE WHEN promotion_date > (SELECT cutoff_date FROM params) THEN 1 ELSE 0 END), 0)::BIGINT FROM history_rows
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'promotion_date_after_event_snapshot_count', COALESCE(SUM(CASE WHEN promotion_date IS NOT NULL AND promotion_date > snapshot_date THEN 1 ELSE 0 END), 0)::BIGINT FROM history_rows
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'candidate_event_before_current_episode_count', COALESCE(SUM(CASE WHEN is_promo = 1 AND promotion_date IS NOT NULL AND promotion_date < current_episode_start THEN 1 ELSE 0 END), 0)::BIGINT FROM all_history_rows
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'observed_current_grade_entry_count', (SELECT employees_with_observed_entry_count FROM entry_counts)
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'employees_with_multiple_observed_entries_count', (SELECT employees_with_multiple_observed_entries_count FROM entry_counts)
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'older_observed_entries_not_selected_count', (SELECT older_observed_entries_not_selected_count FROM entry_counts)
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'selected_entries_after_gap_over_45_days_count', (SELECT selected_entries_after_gap_over_45_days_count FROM entry_counts)
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'entry_window_event_grade_mismatch_count', COALESCE(SUM(CASE WHEN event_snapshot_grade <> current_compensation_grade OR event_snapshot_grade IS NULL THEN 1 ELSE 0 END), 0)::BIGINT FROM entry_window_promotion_rows
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'valid_entry_promotion_pair_count', COUNT(*)::BIGINT FROM valid_entry_promotion_pairs
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'employees_with_valid_entry_promotion_count', COUNT(*)::BIGINT FROM employees_with_valid_entry_promotion
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'promotion_confirmed_into_current_grade_count', COALESCE(MAX(CASE WHEN category_key = 'promotion_confirmed_into_current_grade' THEN employee_count END), 0)::BIGINT FROM classification_counts
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'observed_entry_without_registered_promotion_count', COALESCE(MAX(CASE WHEN category_key = 'observed_entry_without_registered_promotion' THEN employee_count END), 0)::BIGINT FROM classification_counts
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'current_grade_entry_not_observable_count', COALESCE(MAX(CASE WHEN category_key = 'current_grade_entry_not_observable' THEN employee_count END), 0)::BIGINT FROM classification_counts
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'old_grade_comparable_snapshot_count', (SELECT comparable_old_grade_snapshot_count FROM old_grade_reconciliation)
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'old_grade_matches_previous_snapshot_count', (SELECT old_grade_matches_previous_snapshot_count FROM old_grade_reconciliation)
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'old_grade_mismatch_previous_snapshot_count', (SELECT old_grade_mismatch_previous_snapshot_count FROM old_grade_reconciliation)
UNION ALL SELECT (SELECT cutoff_date FROM params), 'metric', 'old_grade_blank_with_previous_snapshot_count', (SELECT old_grade_blank_with_previous_snapshot_count FROM old_grade_reconciliation)
ORDER BY metric;
