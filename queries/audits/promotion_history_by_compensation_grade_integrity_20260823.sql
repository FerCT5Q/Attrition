-- Evidencia internal_analysis / agregada para Promotion history by current compensation grade.
-- Claim: para el snapshot activo-regular 2026-08-23, cada persona se clasifica
-- por su compensation_grade actual y por eventos de promoción registrados dentro
-- de su episodio vigente. Un evento válido cumple is_promo=1, fecha presente,
-- conocida al corte, no posterior a su snapshot y >= max_hire_rehire_date.
-- Regla de aceptación: un único empleado-snapshot sin grado ni episodio
-- faltante/conflictivo; flags y fechas íntegros; y ningún evento seleccionado
-- antes del episodio. Los eventos anteriores al rehire se cuentan como
-- excluidos, no como un error de fuente.
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
target_grouped AS (
    SELECT
        employee_id,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(compensation_grade, '<null>')) AS grade_variant_count,
        COUNT(DISTINCT COALESCE(CAST(max_hire_rehire_date AS VARCHAR(10)), '<null>')) AS episode_variant_count,
        MAX(compensation_grade) AS canonical_compensation_grade,
        MAX(max_hire_rehire_date) AS canonical_episode_start
    FROM target_rows
    GROUP BY employee_id
),
target_canonical AS (
    SELECT employee_id, canonical_compensation_grade, canonical_episode_start
    FROM target_grouped
),
history_rows AS (
    SELECT
        history.employee_id,
        history.fis_mo_end_dt,
        history.is_promo,
        history.promotion_date,
        target.canonical_episode_start
    FROM hrda.post_hire_monthly_worker_dtls AS history
    INNER JOIN target_canonical AS target
      ON target.employee_id = history.employee_id
    WHERE history.fis_mo_end_dt <= (SELECT cutoff_date FROM params)
),
history_snapshot_grouped AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(is_promo AS VARCHAR(12)), '<null>')) AS promo_flag_variant_count,
        COUNT(DISTINCT COALESCE(CAST(promotion_date AS VARCHAR(10)), '<null>')) AS promo_date_variant_count
    FROM history_rows
    GROUP BY employee_id, fis_mo_end_dt
),
candidate_event_rows AS (
    SELECT employee_id, promotion_date, canonical_episode_start
    FROM history_rows
    WHERE is_promo = 1
      AND promotion_date IS NOT NULL
      AND promotion_date <= (SELECT cutoff_date FROM params)
      AND promotion_date <= fis_mo_end_dt
),
raw_event_pairs AS (
    SELECT employee_id, promotion_date, COUNT(*) AS source_event_row_count
    FROM candidate_event_rows
    GROUP BY employee_id, promotion_date
),
valid_event_pairs AS (
    -- La deduplicación sólo aplica al mismo par empleado + promotion_date.
    SELECT DISTINCT employee_id, promotion_date, canonical_episode_start
    FROM candidate_event_rows
    WHERE canonical_episode_start IS NOT NULL
      AND promotion_date >= canonical_episode_start
),
selected_events AS (
    SELECT employee_id, COUNT(*) AS recorded_promotion_count, MAX(promotion_date) AS last_selected_promotion_date
    FROM valid_event_pairs
    GROUP BY employee_id
)
SELECT (SELECT cutoff_date FROM params) AS snapshot_date, 'metric' AS row_type, 'target_source_row_count' AS metric, COUNT(*)::BIGINT AS metric_value
FROM target_rows
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'target_missing_employee_id_row_count', COALESCE(SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END), 0)::BIGINT FROM target_rows
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'target_unique_employee_count', COUNT(*)::BIGINT FROM target_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'target_duplicate_employee_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'target_duplicate_row_excess_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN source_row_count - 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'target_conflicting_grade_count', COALESCE(SUM(CASE WHEN grade_variant_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'target_conflicting_episode_count', COALESCE(SUM(CASE WHEN episode_variant_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'target_missing_compensation_grade_count', COALESCE(SUM(CASE WHEN canonical_compensation_grade IS NULL THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'target_missing_episode_start_count', COALESCE(SUM(CASE WHEN canonical_episode_start IS NULL THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'target_episode_start_future_count', COALESCE(SUM(CASE WHEN canonical_episode_start > (SELECT cutoff_date FROM params) THEN 1 ELSE 0 END), 0)::BIGINT FROM target_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'history_source_row_count', COUNT(*)::BIGINT FROM history_rows
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'history_duplicate_employee_snapshot_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM history_snapshot_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'history_duplicate_snapshot_row_excess_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN source_row_count - 1 ELSE 0 END), 0)::BIGINT FROM history_snapshot_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'history_conflicting_event_snapshot_count', COALESCE(SUM(CASE WHEN promo_flag_variant_count > 1 OR promo_date_variant_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM history_snapshot_grouped
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'invalid_promo_flag_count', COALESCE(SUM(CASE WHEN is_promo IS NULL OR is_promo NOT IN (0, 1) THEN 1 ELSE 0 END), 0)::BIGINT FROM history_rows
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'promo_flag_without_date_count', COALESCE(SUM(CASE WHEN is_promo = 1 AND promotion_date IS NULL THEN 1 ELSE 0 END), 0)::BIGINT FROM history_rows
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'promotion_date_without_promo_flag_count', COALESCE(SUM(CASE WHEN promotion_date IS NOT NULL AND (is_promo IS NULL OR is_promo <> 1) THEN 1 ELSE 0 END), 0)::BIGINT FROM history_rows
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'future_promotion_date_count', COALESCE(SUM(CASE WHEN promotion_date > (SELECT cutoff_date FROM params) THEN 1 ELSE 0 END), 0)::BIGINT FROM history_rows
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'promotion_date_after_event_snapshot_count', COALESCE(SUM(CASE WHEN promotion_date IS NOT NULL AND promotion_date > fis_mo_end_dt THEN 1 ELSE 0 END), 0)::BIGINT FROM history_rows
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'identical_event_duplicate_pair_count', COALESCE(SUM(CASE WHEN source_event_row_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT FROM raw_event_pairs
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'identical_event_duplicate_row_excess_count', COALESCE(SUM(CASE WHEN source_event_row_count > 1 THEN source_event_row_count - 1 ELSE 0 END), 0)::BIGINT FROM raw_event_pairs
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'candidate_event_before_current_episode_count', COALESCE(SUM(CASE WHEN canonical_episode_start IS NOT NULL AND promotion_date < canonical_episode_start THEN 1 ELSE 0 END), 0)::BIGINT FROM candidate_event_rows
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'valid_event_pair_count', COUNT(*)::BIGINT FROM valid_event_pairs
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'employees_with_valid_event_count', COUNT(*)::BIGINT FROM selected_events
UNION ALL
SELECT (SELECT cutoff_date FROM params), 'metric', 'selected_event_before_current_episode_count', COALESCE(SUM(CASE WHEN selected.last_selected_promotion_date < target.canonical_episode_start THEN 1 ELSE 0 END), 0)::BIGINT
FROM selected_events AS selected
INNER JOIN target_canonical AS target ON target.employee_id = selected.employee_id
ORDER BY metric;
