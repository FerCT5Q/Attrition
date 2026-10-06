-- Talent index: prueba agregada de formulas basadas en ranking por ciclo.
--
-- Claim:
--   Evaluar si talent_index coincide con el percentil de un score compuesto
--   construido con los componentes disponibles dentro de cada cycle_number.
--
-- Regla de interpretacion:
--   Se compara con tolerance <= 0.01. Se prueban PERCENT_RANK y CUME_DIST
--   porque producen escalas 0..100 distintas en presencia de empates.
--   Un match alto seria evidencia de reproducibilidad computacional, no de
--   significado de negocio ni de lineage oficial.

WITH base AS (
  SELECT
    cycle_number,
    empl_id,
    perf,
    prev_perf,
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
    COUNT(*) AS rows_in_group,
    COUNT(DISTINCT perf) AS perf_values,
    COUNT(DISTINCT prev_perf) AS prev_perf_values,
    COUNT(DISTINCT stock) AS stock_values,
    COUNT(DISTINCT bonus) AS bonus_values,
    COUNT(DISTINCT promo_index) AS promo_index_values,
    COUNT(DISTINCT talent_index) AS talent_index_values,
    MIN(perf) AS perf_value,
    MIN(prev_perf) AS prev_perf_value,
    MIN(stock) AS stock_value,
    MIN(bonus) AS bonus_value,
    MIN(promo_index) AS promo_index_value,
    MIN(talent_index) AS talent_index_value
  FROM base
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
    promo_index_value,
    talent_index_value
  FROM employee_cycle
  WHERE perf_values <= 1
    AND prev_perf_values <= 1
    AND stock_values <= 1
    AND bonus_values <= 1
    AND promo_index_values <= 1
    AND talent_index_values <= 1
),
scores AS (
  SELECT
    cycle_number,
    empl_id,
    talent_index_value AS stored_value,
    'rank_core_ratings' AS candidate_name,
    CAST(perf_value + stock_value + bonus_value AS DECIMAL(18, 8)) AS score_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    empl_id,
    talent_index_value AS stored_value,
    'rank_promo_index' AS candidate_name,
    CAST(promo_index_value AS DECIMAL(18, 8)) AS score_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    empl_id,
    talent_index_value AS stored_value,
    'rank_equal4_norm20' AS candidate_name,
    CAST(((perf_value * 20.0) + (stock_value * 20.0) + (bonus_value * 20.0) + promo_index_value) / 4.0 AS DECIMAL(18, 8)) AS score_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    empl_id,
    talent_index_value AS stored_value,
    'rank_core_promo_25_75_norm20' AS candidate_name,
    CAST(((((perf_value + stock_value + bonus_value) * 20.0) / 3.0) * 0.25) + (promo_index_value * 0.75) AS DECIMAL(18, 8)) AS score_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    empl_id,
    talent_index_value AS stored_value,
    'rank_core_promo_50_50_norm20' AS candidate_name,
    CAST(((((perf_value + stock_value + bonus_value) * 20.0) / 3.0) * 0.50) + (promo_index_value * 0.50) AS DECIMAL(18, 8)) AS score_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    empl_id,
    talent_index_value AS stored_value,
    'rank_core_promo_75_25_norm20' AS candidate_name,
    CAST(((((perf_value + stock_value + bonus_value) * 20.0) / 3.0) * 0.75) + (promo_index_value * 0.25) AS DECIMAL(18, 8)) AS score_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    empl_id,
    talent_index_value AS stored_value,
    'rank_equal5_norm20_with_prev_perf' AS candidate_name,
    CAST(((perf_value * 20.0) + (prev_perf_value * 20.0) + (stock_value * 20.0) + (bonus_value * 20.0) + promo_index_value) / 5.0 AS DECIMAL(18, 8)) AS score_value
  FROM stable
  WHERE talent_index_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND prev_perf_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND bonus_value IS NOT NULL
    AND promo_index_value IS NOT NULL
),
ranked AS (
  SELECT
    cycle_number,
    candidate_name,
    stored_value,
    'percent_rank' AS rank_method,
    CAST(100.0 * PERCENT_RANK() OVER (
      PARTITION BY cycle_number, candidate_name
      ORDER BY score_value
    ) AS DECIMAL(18, 8)) AS candidate_value
  FROM scores

  UNION ALL

  SELECT
    cycle_number,
    candidate_name,
    stored_value,
    'cume_dist' AS rank_method,
    CAST(100.0 * CUME_DIST() OVER (
      PARTITION BY cycle_number, candidate_name
      ORDER BY score_value
    ) AS DECIMAL(18, 8)) AS candidate_value
  FROM scores
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
