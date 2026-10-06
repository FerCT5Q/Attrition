-- Perfil agregado internal_analysis para Promotion history by current compensation grade.
-- Las cuatro categorías son exhaustivas y mutuamente excluyentes: los episodios
-- iniciados antes de 2016-10-23 se clasifican como Partial promotion history
-- aun cuando tengan eventos registrados. Para los episodios observables se
-- cuentan solamente los eventos válidos distintos por empleado + fecha.
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
    -- La auditoría rechaza duplicados o conflictos; MAX sólo hace determinista
    -- este profile mientras el constructor aplica la puerta de integridad.
    SELECT
        employee_id,
        MAX(compensation_grade) AS compensation_grade,
        MAX(max_hire_rehire_date) AS episode_start_date
    FROM target_rows
    GROUP BY employee_id
),
observed_history AS (
    SELECT MIN(fis_mo_end_dt) AS observed_history_start_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt <= (SELECT cutoff_date FROM params)
),
candidate_event_rows AS (
    SELECT
        history.employee_id,
        history.promotion_date,
        target.episode_start_date
    FROM hrda.post_hire_monthly_worker_dtls AS history
    INNER JOIN target_canonical AS target
      ON target.employee_id = history.employee_id
    WHERE history.fis_mo_end_dt <= (SELECT cutoff_date FROM params)
      AND history.is_promo = 1
      AND history.promotion_date IS NOT NULL
      AND history.promotion_date <= (SELECT cutoff_date FROM params)
      AND history.promotion_date <= history.fis_mo_end_dt
      AND target.episode_start_date IS NOT NULL
      AND history.promotion_date >= target.episode_start_date
),
valid_event_pairs AS (
    SELECT DISTINCT employee_id, promotion_date
    FROM candidate_event_rows
),
event_counts AS (
    SELECT employee_id, COUNT(*)::BIGINT AS recorded_promotion_count
    FROM valid_event_pairs
    GROUP BY employee_id
),
classified AS (
    SELECT
        target.employee_id,
        target.compensation_grade,
        target.episode_start_date,
        CASE
            WHEN target.episode_start_date < history.observed_history_start_date THEN 'partial_promotion_history'
            WHEN COALESCE(events.recorded_promotion_count, 0) = 0 THEN 'zero_recorded_promotions'
            WHEN events.recorded_promotion_count = 1 THEN 'one_recorded_promotion'
            ELSE 'two_or_more_recorded_promotions'
        END AS category_key
    FROM target_canonical AS target
    CROSS JOIN observed_history AS history
    LEFT JOIN event_counts AS events ON events.employee_id = target.employee_id
),
category_counts AS (
    SELECT compensation_grade, category_key, COUNT(*)::BIGINT AS employee_count
    FROM classified
    GROUP BY compensation_grade, category_key
),
grade_domain AS (
    SELECT DISTINCT compensation_grade FROM target_canonical
),
category_domain AS (
    SELECT 'zero_recorded_promotions' AS category_key
    UNION ALL SELECT 'one_recorded_promotion'
    UNION ALL SELECT 'two_or_more_recorded_promotions'
    UNION ALL SELECT 'partial_promotion_history'
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
    UNION ALL
    SELECT 'observable_history_employee_count', COUNT(*)::BIGINT
    FROM classified
    CROSS JOIN observed_history
    WHERE episode_start_date >= observed_history_start_date
    UNION ALL
    SELECT 'partial_history_employee_count', COUNT(*)::BIGINT FROM classified WHERE category_key = 'partial_promotion_history'
    UNION ALL
    SELECT 'zero_recorded_promotions', COUNT(*)::BIGINT FROM classified WHERE category_key = 'zero_recorded_promotions'
    UNION ALL
    SELECT 'one_recorded_promotion', COUNT(*)::BIGINT FROM classified WHERE category_key = 'one_recorded_promotion'
    UNION ALL
    SELECT 'two_or_more_recorded_promotions', COUNT(*)::BIGINT FROM classified WHERE category_key = 'two_or_more_recorded_promotions'
    UNION ALL
    SELECT 'valid_event_pair_count', COUNT(*)::BIGINT FROM valid_event_pairs
    UNION ALL
    SELECT 'employees_with_valid_event_count', COUNT(*)::BIGINT FROM event_counts
)
SELECT
    (SELECT cutoff_date FROM params) AS snapshot_date,
    'metric' AS row_type,
    CAST(NULL AS VARCHAR(80)) AS compensation_grade,
    category_key,
    employee_count,
    CAST(NULL AS DATE) AS observed_history_start_date
FROM metrics
UNION ALL
SELECT
    (SELECT cutoff_date FROM params),
    'observability',
    CAST(NULL AS VARCHAR(80)),
    'observed_promotion_history_start',
    0::BIGINT,
    observed_history_start_date
FROM observed_history
UNION ALL
SELECT
    (SELECT cutoff_date FROM params),
    'grade_category',
    compensation_grade,
    category_key,
    employee_count,
    CAST(NULL AS DATE)
FROM full_grade_matrix
ORDER BY row_type, compensation_grade, category_key;
