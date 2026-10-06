-- Talent index: diagnostico agregado dentro de talent_quartile.
--
-- Proposito:
--   Evaluar si la variacion continua de talent_index dentro de cada quartile
--   sigue a promo_index u otro score simple.
--
-- Limitacion:
--   talent_quartile es un campo relacionado con el target y por tanto este
--   diagnostico es contextual. No se usa como prueba de formula independiente.

WITH base AS (
  SELECT
    cycle_number,
    perf,
    stock,
    bonus,
    promo_index,
    talent_quartile,
    talent_index
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
    AND talent_index IS NOT NULL
    AND talent_quartile IS NOT NULL
),
pair_stats AS (
  SELECT
    cycle_number,
    talent_quartile,
    COUNT(CASE WHEN promo_index IS NOT NULL THEN 1 END)::double precision AS n_promo,
    SUM(CASE WHEN promo_index IS NOT NULL THEN talent_index::double precision ELSE 0 END) AS sum_y_promo,
    SUM(CASE WHEN promo_index IS NOT NULL THEN promo_index::double precision ELSE 0 END) AS sum_x_promo,
    SUM(CASE WHEN promo_index IS NOT NULL THEN (talent_index::double precision * talent_index::double precision) ELSE 0 END) AS sum_y2_promo,
    SUM(CASE WHEN promo_index IS NOT NULL THEN (promo_index::double precision * promo_index::double precision) ELSE 0 END) AS sum_x2_promo,
    SUM(CASE WHEN promo_index IS NOT NULL THEN (talent_index::double precision * promo_index::double precision) ELSE 0 END) AS sum_xy_promo,
    COUNT(*) AS quartile_rows,
    COUNT(DISTINCT talent_index) AS distinct_target_values,
    AVG(talent_index) AS target_mean,
    STDDEV_POP(talent_index) AS target_stddev,
    MIN(talent_index) AS target_min,
    MAX(talent_index) AS target_max,
    AVG(promo_index) AS promo_mean,
    AVG(perf) AS perf_mean,
    AVG(stock) AS stock_mean,
    AVG(bonus) AS bonus_mean
  FROM base
  GROUP BY 1, 2
  HAVING COUNT(*) >= 30
)
SELECT
  cycle_number,
  talent_quartile,
  quartile_rows,
  distinct_target_values,
  ROUND(target_mean, 4) AS target_mean,
  ROUND(target_stddev, 4) AS target_stddev,
  ROUND(target_min, 4) AS target_min,
  ROUND(target_max, 4) AS target_max,
  ROUND(promo_mean, 4) AS promo_mean,
  ROUND(perf_mean, 4) AS perf_mean,
  ROUND(stock_mean, 4) AS stock_mean,
  ROUND(bonus_mean, 4) AS bonus_mean,
  ROUND(
    (n_promo * sum_xy_promo - sum_x_promo * sum_y_promo)
    / NULLIF(SQRT((n_promo * sum_x2_promo - sum_x_promo * sum_x_promo) * (n_promo * sum_y2_promo - sum_y_promo * sum_y_promo)), 0),
    4
  ) AS target_promo_correlation,
  ROUND(
    (n_promo * sum_xy_promo - sum_x_promo * sum_y_promo)
    / NULLIF((n_promo * sum_x2_promo - sum_x_promo * sum_x_promo), 0),
    4
  ) AS target_promo_slope,
  ROUND(
    (n_promo * sum_xy_promo - sum_x_promo * sum_y_promo)
    / NULLIF((n_promo * sum_x2_promo - sum_x_promo * sum_x_promo), 0) * 25.0,
    4
  ) AS target_slope_per_promo_quartile_unit
FROM pair_stats
ORDER BY cycle_number, talent_quartile;
