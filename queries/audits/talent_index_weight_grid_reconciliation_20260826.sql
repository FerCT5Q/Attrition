-- Talent index: cuadrícula predefinida de pesos para una hipótesis lineal.
--
-- Claim:
--   Medir si una combinación ponderada de core_ratings_norm20 y promo_index
--   aproxima el valor almacenado, sin elegir pesos arbitrariamente por fila.
--
-- Regla de interpretación:
--   Se prueban pesos de 0.00 a 1.00 en incrementos de 0.05. Se informan
--   resultados globales, ciclos 1-6 y ciclos 7-9. Un peso ganador solo genera
--   una hipótesis; debe ser estable fuera de la muestra y contar con lineage.

WITH weights(weight_core) AS (
  SELECT 0.00 UNION ALL SELECT 0.05 UNION ALL SELECT 0.10 UNION ALL
  SELECT 0.15 UNION ALL SELECT 0.20 UNION ALL SELECT 0.25 UNION ALL
  SELECT 0.30 UNION ALL SELECT 0.35 UNION ALL SELECT 0.40 UNION ALL
  SELECT 0.45 UNION ALL SELECT 0.50 UNION ALL SELECT 0.55 UNION ALL
  SELECT 0.60 UNION ALL SELECT 0.65 UNION ALL SELECT 0.70 UNION ALL
  SELECT 0.75 UNION ALL SELECT 0.80 UNION ALL SELECT 0.85 UNION ALL
  SELECT 0.90 UNION ALL SELECT 0.95 UNION ALL SELECT 1.00
),
base AS (
  SELECT
    cycle_number,
    empl_id,
    perf,
    stock,
    bonus,
    promo_index,
    talent_index
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
    AND empl_id IS NOT NULL
),
employee_cycle AS (
  SELECT
    cycle_number,
    empl_id,
    COUNT(DISTINCT perf) AS perf_values,
    COUNT(DISTINCT stock) AS stock_values,
    COUNT(DISTINCT bonus) AS bonus_values,
    COUNT(DISTINCT promo_index) AS promo_index_values,
    COUNT(DISTINCT talent_index) AS talent_index_values,
    MIN(perf) AS perf_value,
    MIN(stock) AS stock_value,
    MIN(bonus) AS bonus_value,
    MIN(promo_index) AS promo_index_value,
    MIN(talent_index) AS talent_index_value
  FROM base
  GROUP BY 1, 2
),
complete AS (
  SELECT
    cycle_number,
    empl_id,
    talent_index_value AS stored_value,
    (((perf_value + stock_value + bonus_value) * 20.0) / 3.0)::double precision AS core_value,
    promo_index_value::double precision AS promo_value
  FROM employee_cycle
  WHERE perf_values <= 1
    AND stock_values <= 1
    AND bonus_values <= 1
    AND promo_index_values <= 1
    AND talent_index_values <= 1
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL
    AND talent_index_value IS NOT NULL
),
weighted AS (
  SELECT
    c.cycle_number,
    c.empl_id,
    w.weight_core,
    c.stored_value,
    (w.weight_core * c.core_value) + ((1.0 - w.weight_core) * c.promo_value) AS raw_value,
    CASE
      WHEN c.cycle_number <= 6 THEN 'cycles_1_6'
      WHEN c.cycle_number >= 7 THEN 'cycles_7_9'
      ELSE 'other_cycles'
    END AS cycle_window
  FROM complete AS c
  CROSS JOIN weights AS w
),
ranked AS (
  SELECT
    cycle_number,
    weight_core,
    stored_value,
    cycle_window,
    'percent_rank' AS method,
    100.0 * PERCENT_RANK() OVER (
      PARTITION BY cycle_number, weight_core
      ORDER BY raw_value
    ) AS candidate_value
  FROM weighted

  UNION ALL

  SELECT
    cycle_number,
    weight_core,
    stored_value,
    cycle_window,
    'cume_dist' AS method,
    100.0 * CUME_DIST() OVER (
      PARTITION BY cycle_number, weight_core
      ORDER BY raw_value
    ) AS candidate_value
  FROM weighted
),
raw_comparison AS (
  SELECT
    weight_core,
    'raw_weighted' AS method,
    cycle_window,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(stored_value - raw_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(stored_value - raw_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(stored_value - raw_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(stored_value - raw_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(stored_value - raw_value)), 4) AS max_absolute_error
  FROM weighted
  GROUP BY 1, 2, 3
),
rank_comparison AS (
  SELECT
    weight_core,
    method,
    cycle_window,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(stored_value - candidate_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(stored_value - candidate_value)), 4) AS max_absolute_error
  FROM ranked
  GROUP BY 1, 2, 3
)
SELECT
  weight_core,
  method,
  cycle_window,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error
FROM raw_comparison

UNION ALL

SELECT
  weight_core,
  method,
  cycle_window,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error
FROM rank_comparison
ORDER BY method, cycle_window, weight_core;
