-- Talent index: prueba agregada de rankings lexicograficos por cycle.
--
-- Claim:
--   Evaluar si el indice almacenado se aproxima a un ranking ordenado por
--   ratings ordinales y un campo continuo de promocion, sin imponer pesos.
--
-- Regla de interpretacion:
--   Se prueban ordenamientos predefinidos, PERCENT_RANK y CUME_DIST, con
--   tolerancia de 0.01. Un resultado positivo probaria reproducibilidad del
--   ordenamiento, no su significado oficial.

WITH base AS (
  SELECT
    cycle_number,
    perf,
    stock,
    bonus,
    prev_perf,
    promo_index,
    talent_index
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
    AND perf IS NOT NULL
    AND stock IS NOT NULL
    AND bonus IS NOT NULL
    AND promo_index IS NOT NULL
    AND talent_index IS NOT NULL
),
ranked AS (
  SELECT
    cycle_number,
    talent_index AS stored_value,
    'perf_stock_bonus_promo' AS candidate_name,
    'percent_rank' AS rank_method,
    100.0 * PERCENT_RANK() OVER (PARTITION BY cycle_number ORDER BY perf, stock, bonus, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    'perf_stock_bonus_promo' AS candidate_name,
    'cume_dist' AS rank_method,
    100.0 * CUME_DIST() OVER (PARTITION BY cycle_number ORDER BY perf, stock, bonus, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    'stock_perf_bonus_promo' AS candidate_name,
    'percent_rank' AS rank_method,
    100.0 * PERCENT_RANK() OVER (PARTITION BY cycle_number ORDER BY stock, perf, bonus, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    'stock_perf_bonus_promo' AS candidate_name,
    'cume_dist' AS rank_method,
    100.0 * CUME_DIST() OVER (PARTITION BY cycle_number ORDER BY stock, perf, bonus, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    'perf_bonus_stock_promo' AS candidate_name,
    'percent_rank' AS rank_method,
    100.0 * PERCENT_RANK() OVER (PARTITION BY cycle_number ORDER BY perf, bonus, stock, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    'perf_bonus_stock_promo' AS candidate_name,
    'cume_dist' AS rank_method,
    100.0 * CUME_DIST() OVER (PARTITION BY cycle_number ORDER BY perf, bonus, stock, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    'bonus_stock_perf_promo' AS candidate_name,
    'percent_rank' AS rank_method,
    100.0 * PERCENT_RANK() OVER (PARTITION BY cycle_number ORDER BY bonus, stock, perf, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    'bonus_stock_perf_promo' AS candidate_name,
    'cume_dist' AS rank_method,
    100.0 * CUME_DIST() OVER (PARTITION BY cycle_number ORDER BY bonus, stock, perf, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    'perf_stock_bonus_prev_promo' AS candidate_name,
    'percent_rank' AS rank_method,
    100.0 * PERCENT_RANK() OVER (PARTITION BY cycle_number ORDER BY perf, stock, bonus, prev_perf, promo_index) AS candidate_value
  FROM base
  WHERE prev_perf IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    'perf_stock_bonus_prev_promo' AS candidate_name,
    'cume_dist' AS rank_method,
    100.0 * CUME_DIST() OVER (PARTITION BY cycle_number ORDER BY perf, stock, bonus, prev_perf, promo_index) AS candidate_value
  FROM base
  WHERE prev_perf IS NOT NULL
),
comparison_by_cycle AS (
  SELECT
    candidate_name,
    rank_method,
    cycle_number,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(stored_value - candidate_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(stored_value - candidate_value)), 4) AS max_absolute_error
  FROM ranked
  GROUP BY 1, 2, 3
),
comparison_all AS (
  SELECT
    candidate_name,
    rank_method,
    CAST(NULL AS INTEGER) AS cycle_number,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(stored_value - candidate_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(stored_value - candidate_value)), 4) AS max_absolute_error
  FROM ranked
  GROUP BY 1, 2
)
SELECT
  candidate_name,
  rank_method,
  cycle_number,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error
FROM comparison_by_cycle
WHERE comparable_count >= 30

UNION ALL

SELECT
  candidate_name,
  rank_method,
  cycle_number,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error
FROM comparison_all
WHERE comparable_count >= 30
ORDER BY candidate_name, rank_method, cycle_number;
