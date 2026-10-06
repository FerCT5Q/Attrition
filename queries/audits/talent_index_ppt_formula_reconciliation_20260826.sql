-- Talent index: reconciliacion de la formula encontrada en PPT.
--
-- Formula reportada:
--   1,000,000 * stock rating + 500 * performance rating
--
-- Claim:
--   Evaluar si la formula coincide con el valor numerico almacenado o si solo
--   explica el orden relativo de los empleados.
--
-- Regla de interpretacion:
--   Se prueban cuatro lecturas: valor numerico bruto, normalizacion min-max
--   teorica 0-100, percentil y CUME_DIST por cycle_number. La formula usa los
--   ratings mas recientes disponibles en la fila y orden ascendente equivale a
--   stock como criterio primario y perf como desempate.

WITH population AS (
  SELECT
    cycle_number,
    stock,
    perf,
    talent_index,
    CAST((1000000 * stock) + (500 * perf) AS DECIMAL(18, 4)) AS ppt_formula_value
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
    AND stock IS NOT NULL
    AND perf IS NOT NULL
),
ranked_population AS (
  SELECT
    cycle_number,
    talent_index,
    ppt_formula_value,
    COUNT(*) OVER (PARTITION BY cycle_number) AS ranking_population_count,
    CAST(100.0 * PERCENT_RANK() OVER (
      PARTITION BY cycle_number
      ORDER BY stock, perf
    ) AS DECIMAL(18, 8)) AS percent_rank_value,
    CAST(100.0 * CUME_DIST() OVER (
      PARTITION BY cycle_number
      ORDER BY stock, perf
    ) AS DECIMAL(18, 8)) AS cume_dist_value,
    CAST(
      100.0 * (ppt_formula_value - 1000500.0) / NULLIF(4002000.0, 0)
      AS DECIMAL(18, 8)
    ) AS minmax_norm_value
  FROM population
),
formula_metrics AS (
  SELECT
    'ppt_numeric_formula' AS candidate_name,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(talent_index - ppt_formula_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(talent_index - ppt_formula_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - ppt_formula_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(talent_index - ppt_formula_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(talent_index - ppt_formula_value)), 4) AS max_absolute_error,
    MIN(ppt_formula_value) AS candidate_min,
    MAX(ppt_formula_value) AS candidate_max,
    MIN(talent_index) AS stored_min,
    MAX(talent_index) AS stored_max
  FROM ranked_population
  WHERE talent_index IS NOT NULL

  UNION ALL

  SELECT
    'ppt_minmax_norm_0_100' AS candidate_name,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(talent_index - minmax_norm_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(talent_index - minmax_norm_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - minmax_norm_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(talent_index - minmax_norm_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(talent_index - minmax_norm_value)), 4) AS max_absolute_error,
    MIN(minmax_norm_value) AS candidate_min,
    MAX(minmax_norm_value) AS candidate_max,
    MIN(talent_index) AS stored_min,
    MAX(talent_index) AS stored_max
  FROM ranked_population
  WHERE talent_index IS NOT NULL

  UNION ALL

  SELECT
    'ppt_stock_perf_percent_rank' AS candidate_name,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(talent_index - percent_rank_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(talent_index - percent_rank_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - percent_rank_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(talent_index - percent_rank_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(talent_index - percent_rank_value)), 4) AS max_absolute_error,
    MIN(percent_rank_value) AS candidate_min,
    MAX(percent_rank_value) AS candidate_max,
    MIN(talent_index) AS stored_min,
    MAX(talent_index) AS stored_max
  FROM ranked_population
  WHERE talent_index IS NOT NULL

  UNION ALL

  SELECT
    'ppt_stock_perf_cume_dist' AS candidate_name,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(talent_index - cume_dist_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(talent_index - cume_dist_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - cume_dist_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(talent_index - cume_dist_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(talent_index - cume_dist_value)), 4) AS max_absolute_error,
    MIN(cume_dist_value) AS candidate_min,
    MAX(cume_dist_value) AS candidate_max,
    MIN(talent_index) AS stored_min,
    MAX(talent_index) AS stored_max
  FROM ranked_population
  WHERE talent_index IS NOT NULL
),
cycle_metrics AS (
  SELECT
    'ppt_stock_perf_cume_dist' AS candidate_name,
    cycle_number,
    MAX(ranking_population_count) AS ranking_population_count,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(talent_index - cume_dist_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(talent_index - cume_dist_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - cume_dist_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(talent_index - cume_dist_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(talent_index - cume_dist_value)), 4) AS max_absolute_error
  FROM ranked_population
  WHERE talent_index IS NOT NULL
  GROUP BY 1, 2
)
SELECT
  'overall' AS section,
  candidate_name,
  CAST(NULL AS INTEGER) AS cycle_number,
  CAST(NULL AS BIGINT) AS ranking_population_count,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error,
  candidate_min,
  candidate_max,
  stored_min,
  stored_max
FROM formula_metrics

UNION ALL

SELECT
  'cycle' AS section,
  candidate_name,
  cycle_number,
  ranking_population_count,
  comparable_count,
  matched_within_tolerance_count,
  mismatch_count,
  match_rate_percent,
  mean_absolute_error,
  max_absolute_error,
  CAST(NULL AS DECIMAL(18, 4)) AS candidate_min,
  CAST(NULL AS DECIMAL(18, 4)) AS candidate_max,
  CAST(NULL AS DECIMAL(18, 4)) AS stored_min,
  CAST(NULL AS DECIMAL(18, 4)) AS stored_max
FROM cycle_metrics
WHERE comparable_count >= 30
ORDER BY section, candidate_name, cycle_number;
