-- Evidencia presentation / agregada para Time since last promotion.
-- Claim: la última promoción publicada procede exclusivamente de eventos
-- is_promo=1 con promotion_date válida, conocida al 2026-08-23 y dentro del
-- episodio actual (promotion_date >= max_hire_rehire_date).
-- Regla de aceptación: un único snapshot activo-regular por empleado; ningún
-- conflicto de flag/fecha, flag inválido, fecha futura o fecha posterior a su
-- snapshot; y ninguna promoción seleccionada anterior al episodio actual.
-- Los eventos anteriores al rehire se contabilizan como excluidos, no como
-- errores de la fuente. Las transferencias se auditan, pero no intervienen en
-- la selección ni en el cálculo de la última promoción.
WITH params AS (
    SELECT DATE '2026-08-23' AS cutoff_date
),
target_rows AS (
    SELECT
        employee_id,
        max_hire_rehire_date,
        is_promo,
        promotion_date
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
        COUNT(DISTINCT COALESCE(CAST(max_hire_rehire_date AS VARCHAR(10)), '<null>')) AS episode_start_variant_count,
        COUNT(DISTINCT COALESCE(CAST(is_promo AS VARCHAR(12)), '<null>')) AS promo_flag_variant_count,
        COUNT(DISTINCT COALESCE(CAST(promotion_date AS VARCHAR(10)), '<null>')) AS promo_date_variant_count,
        MAX(max_hire_rehire_date) AS canonical_episode_start
    FROM target_rows
    GROUP BY employee_id
),
target_canonical AS (
    SELECT employee_id, canonical_episode_start
    FROM target_grouped
),
history_rows AS (
    SELECT
        history.employee_id,
        history.fis_mo_end_dt,
        history.is_promo,
        history.promotion_date,
        history.is_transferred,
        history.transfer_date,
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
raw_event_pairs AS (
    SELECT
        employee_id,
        promotion_date,
        COUNT(*) AS source_event_row_count
    FROM history_rows
    WHERE is_promo = 1
      AND promotion_date IS NOT NULL
      AND promotion_date <= (SELECT cutoff_date FROM params)
      AND promotion_date <= fis_mo_end_dt
    GROUP BY employee_id, promotion_date
),
candidate_event_rows AS (
    SELECT
        employee_id,
        promotion_date,
        canonical_episode_start,
        is_transferred,
        transfer_date
    FROM history_rows
    WHERE is_promo = 1
      AND promotion_date IS NOT NULL
      AND promotion_date <= (SELECT cutoff_date FROM params)
      AND promotion_date <= fis_mo_end_dt
),
valid_event_pairs AS (
    -- La deduplicación se limita al par idéntico empleado + fecha de promoción.
    SELECT DISTINCT employee_id, promotion_date, canonical_episode_start
    FROM candidate_event_rows
    WHERE canonical_episode_start IS NOT NULL
      AND promotion_date >= canonical_episode_start
),
latest_selected_events AS (
    SELECT employee_id, MAX(promotion_date) AS promotion_date
    FROM valid_event_pairs
    GROUP BY employee_id
)
SELECT 'metric' AS row_type, 'target_source_row_count' AS metric, COUNT(*)::BIGINT AS metric_value
FROM target_rows
UNION ALL
SELECT 'metric', 'target_unique_employee_count', COUNT(*)::BIGINT
FROM target_grouped
UNION ALL
SELECT 'metric', 'target_duplicate_employee_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT
FROM target_grouped
UNION ALL
SELECT 'metric', 'target_duplicate_row_excess_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN source_row_count - 1 ELSE 0 END), 0)::BIGINT
FROM target_grouped
UNION ALL
SELECT 'metric', 'target_conflicting_event_snapshot_count', COALESCE(SUM(CASE WHEN promo_flag_variant_count > 1 OR promo_date_variant_count > 1 OR episode_start_variant_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT
FROM target_grouped
UNION ALL
SELECT 'metric', 'target_episode_start_future_count', COALESCE(SUM(CASE WHEN canonical_episode_start > (SELECT cutoff_date FROM params) THEN 1 ELSE 0 END), 0)::BIGINT
FROM target_grouped
UNION ALL
SELECT 'metric', 'target_episode_start_unknown_count', COALESCE(SUM(CASE WHEN canonical_episode_start IS NULL THEN 1 ELSE 0 END), 0)::BIGINT
FROM target_grouped
UNION ALL
SELECT 'metric', 'history_source_row_count', COUNT(*)::BIGINT
FROM history_rows
UNION ALL
SELECT 'metric', 'history_duplicate_employee_snapshot_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT
FROM history_snapshot_grouped
UNION ALL
SELECT 'metric', 'history_duplicate_snapshot_row_excess_count', COALESCE(SUM(CASE WHEN source_row_count > 1 THEN source_row_count - 1 ELSE 0 END), 0)::BIGINT
FROM history_snapshot_grouped
UNION ALL
SELECT 'metric', 'history_conflicting_event_snapshot_count', COALESCE(SUM(CASE WHEN promo_flag_variant_count > 1 OR promo_date_variant_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT
FROM history_snapshot_grouped
UNION ALL
SELECT 'metric', 'invalid_promo_flag_count', COALESCE(SUM(CASE WHEN is_promo IS NULL OR is_promo NOT IN (0, 1) THEN 1 ELSE 0 END), 0)::BIGINT
FROM history_rows
UNION ALL
SELECT 'metric', 'promo_flag_without_date_count', COALESCE(SUM(CASE WHEN is_promo = 1 AND promotion_date IS NULL THEN 1 ELSE 0 END), 0)::BIGINT
FROM history_rows
UNION ALL
SELECT 'metric', 'promotion_date_without_promo_flag_count', COALESCE(SUM(CASE WHEN promotion_date IS NOT NULL AND (is_promo IS NULL OR is_promo <> 1) THEN 1 ELSE 0 END), 0)::BIGINT
FROM history_rows
UNION ALL
SELECT 'metric', 'future_promotion_date_count', COALESCE(SUM(CASE WHEN promotion_date > (SELECT cutoff_date FROM params) THEN 1 ELSE 0 END), 0)::BIGINT
FROM history_rows
UNION ALL
SELECT 'metric', 'promotion_date_after_event_snapshot_count', COALESCE(SUM(CASE WHEN promotion_date IS NOT NULL AND promotion_date > fis_mo_end_dt THEN 1 ELSE 0 END), 0)::BIGINT
FROM history_rows
UNION ALL
SELECT 'metric', 'identical_event_duplicate_pair_count', COALESCE(SUM(CASE WHEN source_event_row_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT
FROM raw_event_pairs
UNION ALL
SELECT 'metric', 'identical_event_duplicate_row_excess_count', COALESCE(SUM(CASE WHEN source_event_row_count > 1 THEN source_event_row_count - 1 ELSE 0 END), 0)::BIGINT
FROM raw_event_pairs
UNION ALL
SELECT 'metric', 'candidate_event_before_current_episode_count', COALESCE(SUM(CASE WHEN canonical_episode_start IS NOT NULL AND promotion_date < canonical_episode_start THEN 1 ELSE 0 END), 0)::BIGINT
FROM candidate_event_rows
UNION ALL
SELECT 'metric', 'selected_latest_event_before_current_episode_count', COALESCE(SUM(CASE WHEN selected.promotion_date < target.canonical_episode_start THEN 1 ELSE 0 END), 0)::BIGINT
FROM latest_selected_events AS selected
INNER JOIN target_canonical AS target ON target.employee_id = selected.employee_id
UNION ALL
SELECT 'metric', 'valid_event_pair_count', COUNT(*)::BIGINT
FROM valid_event_pairs
UNION ALL
SELECT 'metric', 'employees_with_valid_event_count', COUNT(*)::BIGINT
FROM latest_selected_events
UNION ALL
SELECT 'metric', 'transfer_flag_on_valid_promotion_event_count', COUNT(DISTINCT employee_id)::BIGINT
FROM candidate_event_rows
WHERE canonical_episode_start IS NOT NULL
  AND promotion_date >= canonical_episode_start
  AND is_transferred = 1
UNION ALL
SELECT 'metric', 'transfer_date_coincident_with_valid_promotion_event_count', COUNT(DISTINCT employee_id)::BIGINT
FROM candidate_event_rows
WHERE canonical_episode_start IS NOT NULL
  AND promotion_date >= canonical_episode_start
  AND is_transferred = 1
  AND transfer_date = promotion_date
ORDER BY metric;
