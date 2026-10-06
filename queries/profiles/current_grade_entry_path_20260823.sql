-- Perfil agregado internal_analysis para responder: entre las personas que hoy
-- están en cada compensation_grade, ¿qué vía OBSERVABLE las llevó a ese grade?
-- No identifica contrataciones directas. El último cambio observado al grade
-- actual se deriva exclusivamente de snapshots mensuales en el episodio
-- vigente; el campo de grade previo auditado se excluye de la clasificación.
WITH params AS (
    SELECT DATE '2026-08-23' AS cutoff_date
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
target_canonical AS (
    -- La auditoría de integridad rechaza duplicados y conflictos. MAX hace la
    -- consulta determinista mientras el constructor exige esa puerta previa.
    SELECT
        employee_id,
        MAX(compensation_grade) AS current_compensation_grade,
        MAX(max_hire_rehire_date) AS current_episode_start
    FROM target_rows
    GROUP BY employee_id
),
history_snapshot_grouped AS (
    SELECT
        history.employee_id,
        history.fis_mo_end_dt AS snapshot_date,
        MAX(NULLIF(TRIM(CAST(history.compensation_grade AS VARCHAR(80))), '')) AS snapshot_compensation_grade,
        MAX(history.is_promo) AS snapshot_is_promo,
        MAX(history.promotion_date) AS snapshot_promotion_date,
        MAX(target.current_compensation_grade) AS current_compensation_grade,
        MAX(target.current_episode_start) AS current_episode_start
    FROM hrda.post_hire_monthly_worker_dtls AS history
    INNER JOIN target_canonical AS target
      ON target.employee_id = history.employee_id
    WHERE history.fis_mo_end_dt <= (SELECT cutoff_date FROM params)
      AND history.fis_mo_end_dt >= target.current_episode_start
    GROUP BY history.employee_id, history.fis_mo_end_dt
),
timeline AS (
    SELECT
        history.employee_id,
        history.snapshot_date,
        history.snapshot_compensation_grade,
        history.snapshot_is_promo,
        history.snapshot_promotion_date,
        history.current_compensation_grade,
        history.current_episode_start,
        LAG(snapshot_date) OVER (PARTITION BY employee_id ORDER BY snapshot_date) AS previous_snapshot_date,
        LAG(snapshot_compensation_grade) OVER (PARTITION BY employee_id ORDER BY snapshot_date) AS previous_snapshot_grade
    FROM history_snapshot_grouped AS history
),
ranked_current_grade_entries AS (
    SELECT
        employee_id,
        current_compensation_grade,
        current_episode_start,
        snapshot_date AS entry_snapshot_date,
        previous_snapshot_date,
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
        entry_recency_rank
    FROM ranked_current_grade_entries
    WHERE entry_recency_rank = 1
),
valid_entry_promotion_pairs AS (
    SELECT DISTINCT
        history.employee_id,
        history.snapshot_promotion_date AS promotion_date
    FROM history_snapshot_grouped AS history
    INNER JOIN selected_current_grade_entries AS entry
      ON entry.employee_id = history.employee_id
    WHERE history.snapshot_is_promo = 1
      AND history.snapshot_promotion_date IS NOT NULL
      AND history.snapshot_promotion_date <= (SELECT cutoff_date FROM params)
      AND history.snapshot_promotion_date <= history.snapshot_date
      AND history.snapshot_promotion_date >= entry.current_episode_start
      AND history.snapshot_promotion_date > entry.previous_snapshot_date
      AND history.snapshot_promotion_date <= entry.entry_snapshot_date
      AND history.snapshot_compensation_grade = entry.current_compensation_grade
),
employees_with_valid_entry_promotion AS (
    SELECT DISTINCT employee_id FROM valid_entry_promotion_pairs
),
classified AS (
    SELECT
        target.employee_id,
        target.current_compensation_grade AS compensation_grade,
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
category_counts AS (
    SELECT compensation_grade, category_key, COUNT(*)::BIGINT AS employee_count
    FROM classified
    GROUP BY compensation_grade, category_key
),
grade_domain AS (
    SELECT DISTINCT compensation_grade FROM classified
),
category_domain AS (
    SELECT 'promotion_confirmed_into_current_grade' AS category_key
    UNION ALL SELECT 'observed_entry_without_registered_promotion'
    UNION ALL SELECT 'current_grade_entry_not_observable'
),
full_grade_matrix AS (
    SELECT
        grades.compensation_grade,
        categories.category_key,
        COALESCE(counts.employee_count, 0)::BIGINT AS employee_count
    FROM grade_domain AS grades
    CROSS JOIN category_domain AS categories
    LEFT JOIN category_counts AS counts
      ON counts.compensation_grade = grades.compensation_grade
     AND counts.category_key = categories.category_key
),
metrics AS (
    SELECT 'denominator_active_regular' AS category_key, COUNT(*)::BIGINT AS employee_count FROM classified
    UNION ALL SELECT 'observed_current_grade_entry_count', COUNT(*)::BIGINT FROM classified WHERE category_key <> 'current_grade_entry_not_observable'
    UNION ALL SELECT 'promotion_confirmed_into_current_grade', COUNT(*)::BIGINT FROM classified WHERE category_key = 'promotion_confirmed_into_current_grade'
    UNION ALL SELECT 'observed_entry_without_registered_promotion', COUNT(*)::BIGINT FROM classified WHERE category_key = 'observed_entry_without_registered_promotion'
    UNION ALL SELECT 'current_grade_entry_not_observable', COUNT(*)::BIGINT FROM classified WHERE category_key = 'current_grade_entry_not_observable'
    UNION ALL SELECT 'valid_entry_promotion_pair_count', COUNT(*)::BIGINT FROM valid_entry_promotion_pairs
    UNION ALL SELECT 'employees_with_valid_entry_promotion_count', COUNT(*)::BIGINT FROM employees_with_valid_entry_promotion
    UNION ALL SELECT 'raw_current_grade_count', COUNT(*)::BIGINT FROM grade_domain
)
SELECT
    (SELECT cutoff_date FROM params) AS snapshot_date,
    'metric' AS row_type,
    CAST(NULL AS VARCHAR(80)) AS compensation_grade,
    category_key,
    employee_count
FROM metrics
UNION ALL
SELECT
    (SELECT cutoff_date FROM params),
    'grade_category',
    compensation_grade,
    category_key,
    employee_count
FROM full_grade_matrix
ORDER BY row_type, compensation_grade, category_key;
