-- Talent index: reconciliacion agregada de formulas candidatas.
--
-- Claim:
--   Medir cuanto se aproxima cada formula plausible al valor almacenado en
--   hrda.master_talent_index, usando el mismo grain empleado-ciclo.
--
-- Poblacion y controles:
--   Se colapsan filas repetidas solo cuando todos los campos usados son
--   internamente consistentes. Los grupos con conflictos se excluyen de la
--   comparacion, no se resuelven con una fecha tecnica.
--
-- Formula de escala para ratings:
--   *_norm20 usa 1..5 -> 20..100; *_norm0 usa 1..5 -> 0..100.
--   Estas transformaciones son hipotesis, no una definicion oficial.
--
-- Regla de aceptacion exploratoria:
--   Una coincidencia es ABS(talent_index - formula) <= 0.01 puntos despues de
--   redondear la formula a 4 decimales. Se reportan comparable, matched,
--   mismatch, match rate y error absoluto; ningun resultado por si solo prueba
--   el significado de negocio ni habilita Definition=2.

WITH base AS (
  SELECT
    cycle_number,
    empl_id,
    perf,
    prev_perf,
    stock,
    bonus,
    promo_quartile,
    talent_quartile,
    promo_index,
    talent_index
  FROM hrda.master_talent_index
),
employee_cycle AS (
  SELECT
    cycle_number,
    empl_id,
    COUNT(*) AS rows_in_group,
    COUNT(DISTINCT perf) AS perf_values,
    COUNT(DISTINCT prev_perf) AS prev_perf_values,
    COUNT(DISTINCT stock) AS stock_values,
    COUNT(DISTINCT bonus) AS bonus_values,
    COUNT(DISTINCT promo_quartile) AS promo_quartile_values,
    COUNT(DISTINCT talent_quartile) AS talent_quartile_values,
    COUNT(DISTINCT promo_index) AS promo_index_values,
    COUNT(DISTINCT talent_index) AS talent_index_values,
    MIN(perf) AS perf_value,
    MIN(prev_perf) AS prev_perf_value,
    MIN(stock) AS stock_value,
    MIN(bonus) AS bonus_value,
    MIN(promo_quartile) AS promo_quartile_value,
    MIN(talent_quartile) AS talent_quartile_value,
    MIN(promo_index) AS promo_index_value,
    MIN(talent_index) AS talent_index_value
  FROM base
  WHERE cycle_number IS NOT NULL
    AND empl_id IS NOT NULL
  GROUP BY 1, 2
),
stable AS (
  SELECT
    cycle_number,
    empl_id,
    perf_value,
    prev_perf_value,
    stock_value,
    bonus_value,
    promo_quartile_value,
    talent_quartile_value,
    promo_index_value,
    talent_index_value
  FROM employee_cycle
  WHERE perf_values <= 1
    AND prev_perf_values <= 1
    AND stock_values <= 1
    AND bonus_values <= 1
    AND promo_quartile_values <= 1
    AND talent_quartile_values <= 1
    AND promo_index_values <= 1
    AND talent_index_values <= 1
),
candidate_values AS (
  SELECT
    cycle_number,
    'promo_index_only' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(promo_index_value AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'core_ratings_mean_norm20' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((perf_value + stock_value + bonus_value) * 20.0) / 3.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'core_ratings_mean_norm0' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((perf_value + stock_value + bonus_value - 3) * 100.0) / 12.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'equal_4_components_norm20' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((perf_value * 20.0) + (stock_value * 20.0) + (bonus_value * 20.0) + promo_index_value) / 4.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'equal_4_components_norm0' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND((((perf_value - 1) * 25.0) + ((stock_value - 1) * 25.0) + ((bonus_value - 1) * 25.0) + promo_index_value) / 4.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'equal_4_components_with_promo_quartile_norm20' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((perf_value * 20.0) + (stock_value * 20.0) + (bonus_value * 20.0) + (promo_quartile_value * 20.0)) / 4.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_quartile_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'equal_4_components_with_promo_quartile_norm0' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND((((perf_value - 1) * 25.0) + ((stock_value - 1) * 25.0) + ((bonus_value - 1) * 25.0) + (((promo_quartile_value - 1) * 100.0) / 3.0)) / 4.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_quartile_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'core_promo_quartile_50_50_norm20' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((((perf_value + stock_value + bonus_value) * 20.0) / 3.0) + (promo_quartile_value * 20.0)) / 2.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_quartile_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'core_promo_quartile_25_75_norm20' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((((perf_value + stock_value + bonus_value) * 20.0) / 3.0) * 0.25) + ((promo_quartile_value * 20.0) * 0.75), 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_quartile_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'core_promo_50_50_norm20' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((((perf_value + stock_value + bonus_value) * 20.0) / 3.0) + promo_index_value) / 2.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'core_promo_75_25_norm20' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((((perf_value + stock_value + bonus_value) * 20.0) / 3.0) * 0.75) + (promo_index_value * 0.25), 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'core_promo_25_75_norm20' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((((perf_value + stock_value + bonus_value) * 20.0) / 3.0) * 0.25) + (promo_index_value * 0.75), 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'raw_mean_4_components' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND((perf_value + stock_value + bonus_value + promo_index_value) / 4.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'equal_5_components_norm20_with_prev_perf' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((perf_value * 20.0) + (prev_perf_value * 20.0) + (stock_value * 20.0) + (bonus_value * 20.0) + promo_index_value) / 5.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND prev_perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    'ratings_mean_norm20_with_prev_perf_no_promo' AS candidate_name,
    talent_index_value AS stored_value,
    CAST(ROUND(((perf_value + prev_perf_value + stock_value + bonus_value) * 20.0) / 4.0, 4) AS DECIMAL(18, 8)) AS candidate_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND prev_perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
),
comparison AS (
  SELECT
    candidate_name,
    cycle_number,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END)
      AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) > 0.01 THEN 1 END)
      AS mismatch_count,
    ROUND(
      100.0 * COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END)
      / NULLIF(COUNT(*), 0),
      4
    ) AS match_rate_percent,
    ROUND(AVG(ABS(stored_value - candidate_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(stored_value - candidate_value)), 4) AS max_absolute_error,
    ROUND(AVG(stored_value), 4) AS stored_mean,
    ROUND(AVG(candidate_value), 4) AS candidate_mean
  FROM candidate_values
  GROUP BY 1, 2
),
all_cycles AS (
  SELECT
    candidate_name,
    CAST(NULL AS INTEGER) AS cycle_number,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END)
      AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) > 0.01 THEN 1 END)
      AS mismatch_count,
    ROUND(
      100.0 * COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END)
      / NULLIF(COUNT(*), 0),
      4
    ) AS match_rate_percent,
    ROUND(AVG(ABS(stored_value - candidate_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(stored_value - candidate_value)), 4) AS max_absolute_error,
    ROUND(AVG(stored_value), 4) AS stored_mean,
    ROUND(AVG(candidate_value), 4) AS candidate_mean
  FROM candidate_values
  GROUP BY 1
)
SELECT
  candidate_name,
  cycle_number,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error,
  stored_mean,
  candidate_mean
FROM comparison
WHERE comparable_count >= 30

UNION ALL

SELECT
  candidate_name,
  cycle_number,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error,
  stored_mean,
  candidate_mean
FROM all_cycles
WHERE comparable_count >= 30
ORDER BY candidate_name, cycle_number;
