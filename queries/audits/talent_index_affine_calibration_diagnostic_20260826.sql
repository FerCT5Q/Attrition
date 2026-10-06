-- Talent index: calibracion lineal exploratoria sobre componentes visibles.
--
-- Proposito:
--   Separar dos preguntas: (1) si existe relacion lineal suficiente para
--   aproximar el target y (2) si esa relacion es estable en ciclos posteriores.
--
-- Importante:
--   Los interceptos y pendientes se estiman con los mismos datos; esto es un
--   diagnostico estadistico y no una formula de negocio. La evaluacion
--   cycles_7_9 usa parametros ajustados solo en cycles_1_6 para limitar el
--   sobreajuste temporal.

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
candidate_values AS (
  SELECT
    cycle_number,
    'core_ratings_mean_norm20' AS candidate_name,
    talent_index::double precision AS stored_value,
    (((perf + stock + bonus) * 20.0) / 3.0)::double precision AS x_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    'promo_index' AS candidate_name,
    talent_index::double precision AS stored_value,
    promo_index::double precision AS x_value
  FROM base

  UNION ALL

  SELECT
    cycle_number,
    'core_promo_25_75_norm20' AS candidate_name,
    talent_index::double precision AS stored_value,
    (((((perf + stock + bonus) * 20.0) / 3.0) * 0.25) + (promo_index * 0.75))::double precision AS x_value
  FROM base
),
fit_rows AS (
  SELECT
    candidate_name,
    'all_cycles' AS fit_scope,
    stored_value,
    x_value
  FROM candidate_values

  UNION ALL

  SELECT
    candidate_name,
    'cycles_1_6' AS fit_scope,
    stored_value,
    x_value
  FROM candidate_values
  WHERE cycle_number <= 6
),
fit_stats AS (
  SELECT
    candidate_name,
    fit_scope,
    COUNT(*)::double precision AS n,
    SUM(stored_value) AS sum_y,
    SUM(x_value) AS sum_x,
    SUM(stored_value * stored_value) AS sum_y2,
    SUM(x_value * x_value) AS sum_x2,
    SUM(stored_value * x_value) AS sum_xy
  FROM fit_rows
  GROUP BY 1, 2
),
fit_params AS (
  SELECT
    candidate_name,
    fit_scope,
    n,
    (n * sum_xy - sum_x * sum_y)
      / NULLIF((n * sum_x2 - sum_x * sum_x), 0) AS slope,
    (
      sum_y
      - (
        (n * sum_xy - sum_x * sum_y)
        / NULLIF((n * sum_x2 - sum_x * sum_x), 0)
      ) * sum_x
    ) / NULLIF(n, 0) AS intercept
  FROM fit_stats
),
evaluation_rows AS (
  SELECT
    candidate_name,
    'all_cycles' AS eval_scope,
    stored_value,
    cycle_number,
    x_value
  FROM candidate_values

  UNION ALL

  SELECT
    candidate_name,
    'cycles_1_6' AS eval_scope,
    stored_value,
    cycle_number,
    x_value
  FROM candidate_values
  WHERE cycle_number <= 6

  UNION ALL

  SELECT
    candidate_name,
    'cycles_7_9' AS eval_scope,
    stored_value,
    cycle_number,
    x_value
  FROM candidate_values
  WHERE cycle_number >= 7
),
predictions AS (
  SELECT
    p.candidate_name,
    p.fit_scope,
    e.eval_scope,
    p.n AS fit_count,
    e.stored_value,
    (p.intercept + (p.slope * e.x_value)) AS predicted_value,
    p.slope,
    p.intercept
  FROM fit_params AS p
  JOIN evaluation_rows AS e
    ON e.candidate_name = p.candidate_name
),
comparison AS (
  SELECT
    candidate_name,
    fit_scope,
    eval_scope,
    MAX(fit_count) AS fit_count,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(stored_value - predicted_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(stored_value - predicted_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(stored_value - predicted_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(stored_value - predicted_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(stored_value - predicted_value)), 4) AS max_absolute_error,
    ROUND(MAX(slope), 4) AS fitted_slope,
    ROUND(MAX(intercept), 4) AS fitted_intercept
  FROM predictions
  GROUP BY 1, 2, 3
)
SELECT
  candidate_name,
  fit_scope,
  eval_scope,
  fit_count,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error,
  fitted_slope,
  fitted_intercept
FROM comparison
WHERE comparable_count >= 30
ORDER BY candidate_name, fit_scope, eval_scope;
