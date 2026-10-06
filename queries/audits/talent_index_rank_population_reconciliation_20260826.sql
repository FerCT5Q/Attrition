-- Talent index: ranking con poblacion de componentes versus poblacion observada.
--
-- Claim:
--   Comprobar si los percentiles almacenados fueron calculados usando todas las
--   filas elegibles con componentes, aunque algunas no tengan talent_index.
--
-- Regla de interpretacion:
--   El ranking se calcula en la poblacion de componentes y se compara solo donde
--   talent_index esta poblado. Se reporta el tamaño del denominador. Un match
--   alto seguiria sin demostrar lineage ni semantica oficial.

WITH base AS (
  SELECT
    cycle_number,
    perf,
    stock,
    bonus,
    promo_index,
    talent_index
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
    AND perf IS NOT NULL
    AND stock IS NOT NULL
    AND bonus IS NOT NULL
    AND promo_index IS NOT NULL
),
ranked AS (
  SELECT
    cycle_number,
    talent_index AS stored_value,
    COUNT(*) OVER (PARTITION BY cycle_number) AS ranking_population_count,
    'stock_perf_bonus_promo' AS candidate_name,
    'percent_rank' AS rank_method,
    100.0 * PERCENT_RANK() OVER (PARTITION BY cycle_number ORDER BY stock, perf, bonus, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    COUNT(*) OVER (PARTITION BY cycle_number) AS ranking_population_count,
    'stock_perf_bonus_promo' AS candidate_name,
    'cume_dist' AS rank_method,
    100.0 * CUME_DIST() OVER (PARTITION BY cycle_number ORDER BY stock, perf, bonus, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    COUNT(*) OVER (PARTITION BY cycle_number) AS ranking_population_count,
    'perf_stock_bonus_promo' AS candidate_name,
    'percent_rank' AS rank_method,
    100.0 * PERCENT_RANK() OVER (PARTITION BY cycle_number ORDER BY perf, stock, bonus, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    COUNT(*) OVER (PARTITION BY cycle_number) AS ranking_population_count,
    'perf_stock_bonus_promo' AS candidate_name,
    'cume_dist' AS rank_method,
    100.0 * CUME_DIST() OVER (PARTITION BY cycle_number ORDER BY perf, stock, bonus, promo_index) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    COUNT(*) OVER (PARTITION BY cycle_number) AS ranking_population_count,
    'core_promo_25_75_norm20' AS candidate_name,
    'percent_rank' AS rank_method,
    100.0 * PERCENT_RANK() OVER (
      PARTITION BY cycle_number
      ORDER BY (((perf + stock + bonus) * 20.0) / 3.0) * 0.25 + (promo_index * 0.75)
    ) AS candidate_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    talent_index AS stored_value,
    COUNT(*) OVER (PARTITION BY cycle_number) AS ranking_population_count,
    'core_promo_25_75_norm20' AS candidate_name,
    'cume_dist' AS rank_method,
    100.0 * CUME_DIST() OVER (
      PARTITION BY cycle_number
      ORDER BY (((perf + stock + bonus) * 20.0) / 3.0) * 0.25 + (promo_index * 0.75)
    ) AS candidate_value
  FROM base
),
comparison_by_cycle AS (
  SELECT
    candidate_name,
    rank_method,
    cycle_number,
    MAX(ranking_population_count) AS ranking_population_count,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(stored_value - candidate_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(stored_value - candidate_value)), 4) AS max_absolute_error
  FROM ranked
  WHERE stored_value IS NOT NULL
  GROUP BY 1, 2, 3
),
comparison_all AS (
  SELECT
    candidate_name,
    rank_method,
    CAST(NULL AS INTEGER) AS cycle_number,
    MAX(ranking_population_count) AS ranking_population_count,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(stored_value - candidate_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(stored_value - candidate_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(stored_value - candidate_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(stored_value - candidate_value)), 4) AS max_absolute_error
  FROM ranked
  WHERE stored_value IS NOT NULL
  GROUP BY 1, 2
)
SELECT
  candidate_name,
  rank_method,
  cycle_number,
  ranking_population_count,
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
  ranking_population_count,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error
FROM comparison_all
WHERE comparable_count >= 30
ORDER BY candidate_name, rank_method, cycle_number;
