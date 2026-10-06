-- Perfil agregado presentation para Time since last promotion al 2026-08-23.
-- La duración usa aniversarios calendario de la promoción válida más reciente:
-- evento is_promo=1 con fecha no futura, no posterior al snapshot del evento y
-- no anterior a max_hire_rehire_date. Los pares idénticos empleado + fecha se
-- deduplican; transferencias no se usan en la fórmula.
-- El denominador de todos los porcentajes es toda la población activa regular.
WITH params AS (
    SELECT DATE '2026-08-23' AS cutoff_date
),
target_rows AS (
    SELECT employee_id, max_hire_rehire_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT cutoff_date FROM params)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
target_canonical AS (
    -- El audit rechaza más de una fila o conflictos; MAX hace el profile
    -- determinista mientras el builder aplica esa puerta de integridad.
    SELECT employee_id, MAX(max_hire_rehire_date) AS episode_start_date
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
latest_event AS (
    SELECT employee_id, MAX(promotion_date) AS latest_promotion_date
    FROM valid_event_pairs
    GROUP BY employee_id
),
classified AS (
    SELECT
        target.employee_id,
        CASE
            WHEN target.episode_start_date IS NULL THEN 'episode_start_unknown'
            WHEN latest.latest_promotion_date IS NULL
                 AND target.episode_start_date < history.observed_history_start_date
                THEN 'history_predates_observed_promotion_events'
            WHEN latest.latest_promotion_date IS NULL THEN 'no_promotion_recorded_current_episode'
            WHEN (SELECT cutoff_date FROM params) < DATEADD(year, 1, latest.latest_promotion_date) THEN 'y0_to_lt1'
            WHEN (SELECT cutoff_date FROM params) < DATEADD(year, 2, latest.latest_promotion_date) THEN 'y1_to_lt2'
            WHEN (SELECT cutoff_date FROM params) < DATEADD(year, 3, latest.latest_promotion_date) THEN 'y2_to_lt3'
            WHEN (SELECT cutoff_date FROM params) < DATEADD(year, 5, latest.latest_promotion_date) THEN 'y3_to_lt5'
            ELSE 'y5_plus'
        END AS bucket_key
    FROM target_canonical AS target
    CROSS JOIN observed_history AS history
    LEFT JOIN latest_event AS latest ON latest.employee_id = target.employee_id
),
bucket_counts AS (
    SELECT bucket_key, COUNT(*)::BIGINT AS employee_count
    FROM classified
    GROUP BY bucket_key
),
denominator AS (
    SELECT COUNT(*)::BIGINT AS employee_count
    FROM target_canonical
),
latest_recorded AS (
    SELECT COALESCE(SUM(employee_count), 0)::BIGINT AS employee_count
    FROM bucket_counts
    WHERE bucket_key IN ('y0_to_lt1', 'y1_to_lt2', 'y2_to_lt3', 'y3_to_lt5', 'y5_plus')
),
two_plus AS (
    SELECT COALESCE(SUM(employee_count), 0)::BIGINT AS employee_count
    FROM bucket_counts
    WHERE bucket_key IN ('y2_to_lt3', 'y3_to_lt5', 'y5_plus')
),
non_temporal AS (
    SELECT COALESCE(SUM(employee_count), 0)::BIGINT AS employee_count
    FROM bucket_counts
    WHERE bucket_key IN (
        'no_promotion_recorded_current_episode',
        'history_predates_observed_promotion_events',
        'episode_start_unknown'
    )
)
SELECT
    (SELECT cutoff_date FROM params) AS snapshot_date,
    'metric' AS row_type,
    'denominator_active_regular' AS bucket_key,
    employee_count,
    CAST(NULL AS DATE) AS observed_history_start_date
FROM denominator
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'latest_recorded_promotion_event', employee_count, CAST(NULL AS DATE)
FROM latest_recorded
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'two_plus_years', employee_count, CAST(NULL AS DATE)
FROM two_plus
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'non_temporal_state_total', employee_count, CAST(NULL AS DATE)
FROM non_temporal
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'observability', 'observed_promotion_history_start', 0::BIGINT, observed_history_start_date
FROM observed_history
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'band', bucket_key, employee_count, CAST(NULL AS DATE)
FROM bucket_counts
WHERE bucket_key IN ('y0_to_lt1', 'y1_to_lt2', 'y2_to_lt3', 'y3_to_lt5', 'y5_plus')
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'state', bucket_key, employee_count, CAST(NULL AS DATE)
FROM bucket_counts
WHERE bucket_key IN (
    'no_promotion_recorded_current_episode',
    'history_predates_observed_promotion_events',
    'episode_start_unknown'
)
ORDER BY row_type, bucket_key;
