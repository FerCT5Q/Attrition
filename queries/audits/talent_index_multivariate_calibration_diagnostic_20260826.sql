-- Talent index: calibracion lineal multivariable agregada.
--
-- Proposito:
--   Estimar el mejor ajuste lineal de core_ratings_mean_norm20 y promo_index
--   usando solo estadisticas suficientes agregadas, y verificar estabilidad en
--   ciclos posteriores.
--
-- Importante:
--   Es un limite diagnostico de reproducibilidad, no una formula de negocio.
--   Los coeficientes ajustados no deben documentarse como lineage oficial.

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
    AND talent_index IS NOT NULL
),
complete AS (
  SELECT
    cycle_number,
    talent_index::double precision AS y_value,
    (((perf + stock + bonus) * 20.0) / 3.0)::double precision AS x_core,
    promo_index::double precision AS x_promo
  FROM base
),
fit_rows AS (
  SELECT
    'all_cycles' AS fit_scope,
    y_value,
    x_core,
    x_promo
  FROM complete

  UNION ALL

  SELECT
    'cycles_1_6' AS fit_scope,
    y_value,
    x_core,
    x_promo
  FROM complete
  WHERE cycle_number <= 6
),
fit_stats AS (
  SELECT
    fit_scope,
    COUNT(*)::double precision AS n,
    SUM(y_value) AS sum_y,
    SUM(x_core) AS sum_core,
    SUM(x_promo) AS sum_promo,
    SUM(y_value * y_value) AS sum_y2,
    SUM(x_core * x_core) AS sum_core2,
    SUM(x_promo * x_promo) AS sum_promo2,
    SUM(x_core * x_promo) AS sum_core_promo,
    SUM(y_value * x_core) AS sum_y_core,
    SUM(y_value * x_promo) AS sum_y_promo
  FROM fit_rows
  GROUP BY 1
),
centered AS (
  SELECT
    fit_scope,
    n,
    sum_y,
    sum_core,
    sum_promo,
    (sum_core2 - (sum_core * sum_core / NULLIF(n, 0))) AS s_core_core,
    (sum_promo2 - (sum_promo * sum_promo / NULLIF(n, 0))) AS s_promo_promo,
    (sum_core_promo - (sum_core * sum_promo / NULLIF(n, 0))) AS s_core_promo,
    (sum_y_core - (sum_core * sum_y / NULLIF(n, 0))) AS s_y_core,
    (sum_y_promo - (sum_promo * sum_y / NULLIF(n, 0))) AS s_y_promo
  FROM fit_stats
),
params AS (
  SELECT
    fit_scope,
    n,
    (
      (s_y_core * s_promo_promo) - (s_y_promo * s_core_promo)
    ) / NULLIF((s_core_core * s_promo_promo) - (s_core_promo * s_core_promo), 0) AS core_coefficient,
    (
      (s_y_promo * s_core_core) - (s_y_core * s_core_promo)
    ) / NULLIF((s_core_core * s_promo_promo) - (s_core_promo * s_core_promo), 0) AS promo_coefficient,
    (
      (sum_y / NULLIF(n, 0))
      - (
        (
          (s_y_core * s_promo_promo) - (s_y_promo * s_core_promo)
        ) / NULLIF((s_core_core * s_promo_promo) - (s_core_promo * s_core_promo), 0)
      ) * (sum_core / NULLIF(n, 0))
      - (
        (
          (s_y_promo * s_core_core) - (s_y_core * s_core_promo)
        ) / NULLIF((s_core_core * s_promo_promo) - (s_core_promo * s_core_promo), 0)
      ) * (sum_promo / NULLIF(n, 0))
    ) AS intercept
  FROM centered
),
evaluation_rows AS (
  SELECT
    'all_cycles' AS eval_scope,
    y_value,
    x_core,
    x_promo
  FROM complete

  UNION ALL

  SELECT
    'cycles_1_6' AS eval_scope,
    y_value,
    x_core,
    x_promo
  FROM complete
  WHERE cycle_number <= 6

  UNION ALL

  SELECT
    'cycles_7_9' AS eval_scope,
    y_value,
    x_core,
    x_promo
  FROM complete
  WHERE cycle_number >= 7
),
predictions AS (
  SELECT
    p.fit_scope,
    e.eval_scope,
    p.n AS fit_count,
    e.y_value,
    p.intercept + (p.core_coefficient * e.x_core) + (p.promo_coefficient * e.x_promo) AS predicted_value,
    p.intercept,
    p.core_coefficient,
    p.promo_coefficient
  FROM params AS p
  CROSS JOIN evaluation_rows AS e
),
comparison AS (
  SELECT
    fit_scope,
    eval_scope,
    MAX(fit_count) AS fit_count,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(y_value - predicted_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(y_value - predicted_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(y_value - predicted_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(y_value - predicted_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(y_value - predicted_value)), 4) AS max_absolute_error,
    ROUND(MAX(intercept), 4) AS fitted_intercept,
    ROUND(MAX(core_coefficient), 4) AS fitted_core_coefficient,
    ROUND(MAX(promo_coefficient), 4) AS fitted_promo_coefficient
  FROM predictions
  GROUP BY 1, 2
)
SELECT
  fit_scope,
  eval_scope,
  fit_count,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error,
  fitted_intercept,
  fitted_core_coefficient,
  fitted_promo_coefficient
FROM comparison
WHERE comparable_count >= 30
ORDER BY fit_scope, eval_scope;
