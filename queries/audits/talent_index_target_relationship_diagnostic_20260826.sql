-- Talent index: diagnostico agregado de relaciones con componentes y quartiles.
--
-- Proposito:
--   Medir relaciones lineales simples sin depender de funciones estadisticas
--   opcionales del cluster. Las correlaciones se reconstruyen con sumas,
--   productos y la formula de Pearson sobre agregados.
--
-- Regla de interpretacion:
--   Las correlaciones y perfiles por quartile generan hipotesis. No prueban la
--   formula ni su semantica de negocio.

WITH base AS (
  SELECT
    cycle_number,
    perf,
    prev_perf,
    stock,
    bonus,
    promo_quartile,
    talent_quartile,
    promo_index,
    talent_index
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
    AND talent_index IS NOT NULL
),
pair_observations AS (
  SELECT
    'promo_index' AS predictor_name,
    cycle_number,
    talent_index::double precision AS target_value,
    promo_index::double precision AS predictor_value
  FROM base
  WHERE promo_index IS NOT NULL

  UNION ALL

  SELECT
    'core_ratings_mean_norm20' AS predictor_name,
    cycle_number,
    talent_index::double precision AS target_value,
    (((perf + stock + bonus) * 20.0) / 3.0)::double precision AS predictor_value
  FROM base
  WHERE perf IS NOT NULL
    AND stock IS NOT NULL
    AND bonus IS NOT NULL

  UNION ALL

  SELECT
    'core_promo_25_75_norm20' AS predictor_name,
    cycle_number,
    talent_index::double precision AS target_value,
    (((((perf + stock + bonus) * 20.0) / 3.0) * 0.25) + (promo_index * 0.75))::double precision AS predictor_value
  FROM base
  WHERE perf IS NOT NULL
    AND stock IS NOT NULL
    AND bonus IS NOT NULL
    AND promo_index IS NOT NULL

  UNION ALL

  SELECT
    'perf' AS predictor_name,
    cycle_number,
    talent_index::double precision AS target_value,
    perf::double precision AS predictor_value
  FROM base
  WHERE perf IS NOT NULL

  UNION ALL

  SELECT
    'prev_perf' AS predictor_name,
    cycle_number,
    talent_index::double precision AS target_value,
    prev_perf::double precision AS predictor_value
  FROM base
  WHERE prev_perf IS NOT NULL

  UNION ALL

  SELECT
    'stock' AS predictor_name,
    cycle_number,
    talent_index::double precision AS target_value,
    stock::double precision AS predictor_value
  FROM base
  WHERE stock IS NOT NULL

  UNION ALL

  SELECT
    'bonus' AS predictor_name,
    cycle_number,
    talent_index::double precision AS target_value,
    bonus::double precision AS predictor_value
  FROM base
  WHERE bonus IS NOT NULL
),
pair_stats_by_cycle AS (
  SELECT
    predictor_name,
    cycle_number,
    COUNT(*)::double precision AS n,
    SUM(target_value) AS sum_y,
    SUM(predictor_value) AS sum_x,
    SUM(target_value * target_value) AS sum_y2,
    SUM(predictor_value * predictor_value) AS sum_x2,
    SUM(target_value * predictor_value) AS sum_xy
  FROM pair_observations
  GROUP BY 1, 2
),
pair_stats_all AS (
  SELECT
    predictor_name,
    CAST(NULL AS INTEGER) AS cycle_number,
    COUNT(*)::double precision AS n,
    SUM(target_value) AS sum_y,
    SUM(predictor_value) AS sum_x,
    SUM(target_value * target_value) AS sum_y2,
    SUM(predictor_value * predictor_value) AS sum_x2,
    SUM(target_value * predictor_value) AS sum_xy
  FROM pair_observations
  GROUP BY 1
),
pair_stats AS (
  SELECT
    predictor_name,
    cycle_number,
    n,
    sum_y,
    sum_x,
    sum_y2,
    sum_x2,
    sum_xy
  FROM pair_stats_by_cycle

  UNION ALL

  SELECT
    predictor_name,
    cycle_number,
    n,
    sum_y,
    sum_x,
    sum_y2,
    sum_x2,
    sum_xy
  FROM pair_stats_all
),
quartile_profile AS (
  SELECT
    cycle_number,
    talent_quartile AS quartile_value,
    COUNT(*) AS quartile_rows,
    COUNT(DISTINCT talent_index) AS distinct_target_values,
    ROUND(AVG(talent_index), 4) AS target_mean,
    ROUND(MIN(talent_index), 4) AS target_min,
    ROUND(MAX(talent_index), 4) AS target_max,
    ROUND(AVG(promo_index), 4) AS promo_index_mean,
    ROUND(AVG(perf), 4) AS perf_mean,
    ROUND(AVG(stock), 4) AS stock_mean,
    ROUND(AVG(bonus), 4) AS bonus_mean
  FROM base
  WHERE talent_quartile IS NOT NULL
  GROUP BY 1, 2
  HAVING COUNT(*) >= 30
)
SELECT
  'predictor_relationship' AS section,
  predictor_name,
  cycle_number,
  CAST(NULL AS INTEGER) AS quartile_value,
  CAST(n AS BIGINT) AS comparable_count,
  ROUND(sum_y / NULLIF(n, 0), 4) AS target_mean,
  ROUND(sum_x / NULLIF(n, 0), 4) AS predictor_mean,
  ROUND(
    (n * sum_xy - sum_x * sum_y)
    / NULLIF(SQRT((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)), 0),
    4
  ) AS pearson_correlation,
  ROUND(
    (n * sum_xy - sum_x * sum_y)
    / NULLIF((n * sum_x2 - sum_x * sum_x), 0),
    4
  ) AS univariate_slope,
  ROUND(
    POWER(
      (n * sum_xy - sum_x * sum_y)
      / NULLIF(SQRT((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)), 0),
      2
    ),
    4
  ) AS univariate_r2,
  CAST(NULL AS BIGINT) AS quartile_rows,
  CAST(NULL AS BIGINT) AS distinct_target_values,
  CAST(NULL AS DECIMAL(18, 4)) AS target_min,
  CAST(NULL AS DECIMAL(18, 4)) AS target_max,
  CAST(NULL AS DECIMAL(18, 4)) AS promo_index_mean,
  CAST(NULL AS DECIMAL(18, 4)) AS perf_mean,
  CAST(NULL AS DECIMAL(18, 4)) AS stock_mean,
  CAST(NULL AS DECIMAL(18, 4)) AS bonus_mean
FROM pair_stats
WHERE n >= 30

UNION ALL

SELECT
  'talent_quartile_profile' AS section,
  'talent_index_by_talent_quartile' AS predictor_name,
  cycle_number,
  quartile_value,
  CAST(NULL AS BIGINT) AS comparable_count,
  target_mean,
  CAST(NULL AS DECIMAL(18, 4)) AS predictor_mean,
  CAST(NULL AS DECIMAL(18, 4)) AS pearson_correlation,
  CAST(NULL AS DECIMAL(18, 4)) AS univariate_slope,
  CAST(NULL AS DECIMAL(18, 4)) AS univariate_r2,
  quartile_rows,
  distinct_target_values,
  target_min,
  target_max,
  promo_index_mean,
  perf_mean,
  stock_mean,
  bonus_mean
FROM quartile_profile
ORDER BY section, predictor_name, cycle_number, quartile_value;
