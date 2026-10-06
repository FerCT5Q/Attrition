-- Talent index: reconciliacion de la hipotesis comunicada por Mandy.
--
-- Hipotesis:
--   1) usar el rating AR mas reciente de stock y performance;
--   2) convertir cada rating a percentile rank dentro de un comp grade;
--   3) usar stock_percentile * 1,000,000 + perf_percentile * 500;
--   4) algunos grupos pequenos pueden agruparse.
--
-- La tabla no contiene una columna llamada compensation_grade. Por eso se
-- prueban rewards_group y level como candidatos tecnicos, sin afirmar que
-- ninguno sea el comp grade oficial.
--
-- Regla de aceptacion:
--   una variante solo se consideraria reconciliada si obtiene al menos 95%
--   de coincidencias con talent_index, tolerancia 0.01, en cada poblacion
--   reportada con al menos 30 observaciones comparables. El resultado es
--   agregado y no devuelve IDs ni etiquetas de grupo.

WITH source AS (
  SELECT
    m.cycle_number,
    m.empl_id,
    NULLIF(TRIM(m.rewards_group), '') AS rewards_group,
    NULLIF(TRIM(m.level), '') AS level,
    m.stock,
    m.perf,
    m.talent_index
  FROM hrda.master_talent_index AS m
  WHERE m.cycle_number IS NOT NULL
    AND m.empl_id IS NOT NULL
),
employee_cycle AS (
  SELECT
    cycle_number,
    empl_id,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT rewards_group) AS rewards_group_values,
    COUNT(DISTINCT level) AS level_values,
    COUNT(DISTINCT stock) AS stock_values,
    COUNT(DISTINCT perf) AS perf_values,
    COUNT(DISTINCT talent_index) AS talent_index_values,
    MIN(rewards_group) AS rewards_group_value,
    MIN(level) AS level_value,
    MIN(stock) AS stock_value,
    MIN(perf) AS perf_value,
    MIN(talent_index) AS talent_index_value
  FROM source
  GROUP BY 1, 2
),
candidate_rows AS (
  SELECT
    cycle_number,
    empl_id,
    'rewards_group' AS grouping_candidate,
    rewards_group_value AS grouping_value,
    stock_value AS stock,
    perf_value AS perf,
    talent_index_value AS talent_index
  FROM employee_cycle
  WHERE rewards_group_values = 1
    AND stock_values <= 1
    AND perf_values <= 1
    AND talent_index_values <= 1
    AND rewards_group_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND talent_index_value IS NOT NULL

  UNION ALL

  SELECT
    cycle_number,
    empl_id,
    'level' AS grouping_candidate,
    level_value AS grouping_value,
    stock_value AS stock,
    perf_value AS perf,
    talent_index_value AS talent_index
  FROM employee_cycle
  WHERE level_values = 1
    AND stock_values <= 1
    AND perf_values <= 1
    AND talent_index_values <= 1
    AND level_value IS NOT NULL
    AND stock_value IS NOT NULL
    AND perf_value IS NOT NULL
    AND talent_index_value IS NOT NULL
),
group_sizes AS (
  SELECT
    grouping_candidate,
    cycle_number,
    grouping_value,
    COUNT(*) AS group_employees
  FROM candidate_rows
  GROUP BY 1, 2, 3
),
rank_inputs AS (
  SELECT
    r.grouping_candidate,
    r.cycle_number,
    r.empl_id,
    r.grouping_value,
    g.group_employees,
    r.stock,
    r.perf,
    r.talent_index,
    PERCENT_RANK() OVER (
      PARTITION BY r.grouping_candidate, r.cycle_number, r.grouping_value
      ORDER BY r.stock
    ) AS stock_percent_rank,
    PERCENT_RANK() OVER (
      PARTITION BY r.grouping_candidate, r.cycle_number, r.grouping_value
      ORDER BY r.perf
    ) AS perf_percent_rank,
    CUME_DIST() OVER (
      PARTITION BY r.grouping_candidate, r.cycle_number, r.grouping_value
      ORDER BY r.stock
    ) AS stock_cume_dist,
    CUME_DIST() OVER (
      PARTITION BY r.grouping_candidate, r.cycle_number, r.grouping_value
      ORDER BY r.perf
    ) AS perf_cume_dist
  FROM candidate_rows AS r
  INNER JOIN group_sizes AS g
    ON g.grouping_candidate = r.grouping_candidate
   AND g.cycle_number = r.cycle_number
   AND g.grouping_value = r.grouping_value
),
weighted AS (
  SELECT
    grouping_candidate,
    cycle_number,
    empl_id,
    grouping_value,
    group_employees,
    talent_index,
    CAST(
      stock_percent_rank * 1000000.0 + perf_percent_rank * 500.0
      AS DECIMAL(20, 8)
    ) AS weighted_percent_rank_formula,
    CAST(
      stock_cume_dist * 1000000.0 + perf_cume_dist * 500.0
      AS DECIMAL(20, 8)
    ) AS weighted_cume_dist_formula
  FROM rank_inputs
),
final_ranks AS (
  SELECT
    w.grouping_candidate,
    w.cycle_number,
    w.empl_id,
    w.grouping_value,
    w.group_employees,
    w.talent_index,
    w.weighted_percent_rank_formula,
    w.weighted_cume_dist_formula,
    CAST(
      100.0 * PERCENT_RANK() OVER (
        PARTITION BY w.grouping_candidate, w.cycle_number
        ORDER BY w.weighted_percent_rank_formula
      ) AS DECIMAL(20, 8)
    ) AS final_percent_rank_cycle,
    CAST(
      100.0 * CUME_DIST() OVER (
        PARTITION BY w.grouping_candidate, w.cycle_number
        ORDER BY w.weighted_percent_rank_formula
      ) AS DECIMAL(20, 8)
    ) AS final_cume_dist_cycle
  FROM weighted AS w
),
-- Recompute the final ranking by the actual group key. The first rank block
-- above is retained for the raw weighted candidates; this block supplies the
-- within-group final percentile required by the hypothesis.
final_ranks_by_group AS (
  SELECT
    r.grouping_candidate,
    r.cycle_number,
    r.empl_id,
    r.grouping_value,
    r.group_employees,
    r.talent_index,
    r.weighted_percent_rank_formula,
    r.weighted_cume_dist_formula,
    r.final_percent_rank_cycle,
    r.final_cume_dist_cycle,
    CAST(
      100.0 * PERCENT_RANK() OVER (
        PARTITION BY r.grouping_candidate, r.cycle_number, r.grouping_value
        ORDER BY r.weighted_percent_rank_formula
      ) AS DECIMAL(20, 8)
    ) AS final_percent_rank_within_group,
    CAST(
      100.0 * CUME_DIST() OVER (
        PARTITION BY r.grouping_candidate, r.cycle_number, r.grouping_value
        ORDER BY r.weighted_percent_rank_formula
      ) AS DECIMAL(20, 8)
    ) AS final_cume_dist_within_group
  FROM final_ranks AS r
),
candidate_values AS (
  SELECT grouping_candidate, cycle_number, group_employees, talent_index,
         'weighted_percent_rank_formula' AS variant,
         weighted_percent_rank_formula AS candidate_value
  FROM final_ranks_by_group

  UNION ALL

  SELECT grouping_candidate, cycle_number, group_employees, talent_index,
         'weighted_cume_dist_formula', weighted_cume_dist_formula
  FROM final_ranks_by_group

  UNION ALL

  SELECT grouping_candidate, cycle_number, group_employees, talent_index,
         'final_percent_rank_cycle', final_percent_rank_cycle
  FROM final_ranks_by_group

  UNION ALL

  SELECT grouping_candidate, cycle_number, group_employees, talent_index,
         'final_cume_dist_cycle', final_cume_dist_cycle
  FROM final_ranks_by_group

  UNION ALL

  SELECT grouping_candidate, cycle_number, group_employees, talent_index,
         'final_percent_rank_within_group', final_percent_rank_within_group
  FROM final_ranks_by_group

  UNION ALL

  SELECT grouping_candidate, cycle_number, group_employees, talent_index,
         'final_cume_dist_within_group', final_cume_dist_within_group
  FROM final_ranks_by_group
),
scoped AS (
  SELECT
    grouping_candidate,
    cycle_number,
    'all_groups' AS population_scope,
    variant,
    talent_index,
    candidate_value
  FROM candidate_values
  WHERE candidate_value IS NOT NULL

  UNION ALL

  SELECT
    grouping_candidate,
    cycle_number,
    'groups_at_least_30' AS population_scope,
    variant,
    talent_index,
    candidate_value
  FROM candidate_values
  WHERE candidate_value IS NOT NULL
    AND group_employees >= 30
),
cycle_metrics AS (
  SELECT
    population_scope,
    grouping_candidate,
    cycle_number,
    variant,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(talent_index - candidate_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(talent_index - candidate_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - candidate_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(talent_index - candidate_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(talent_index - candidate_value)), 4) AS max_absolute_error
  FROM scoped
  GROUP BY 1, 2, 3, 4
),
overall_metrics AS (
  SELECT
    population_scope,
    grouping_candidate,
    CAST(NULL AS INTEGER) AS cycle_number,
    variant,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(talent_index - candidate_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(talent_index - candidate_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - candidate_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(talent_index - candidate_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(talent_index - candidate_value)), 4) AS max_absolute_error
  FROM scoped
  GROUP BY 1, 2, 4
)
SELECT
  'overall' AS result_scope,
  population_scope,
  grouping_candidate,
  cycle_number,
  variant,
  CAST(comparable_count AS BIGINT) AS comparable_count,
  CAST(matched_within_tolerance_count AS BIGINT) AS matched_within_tolerance_count,
  CAST(mismatch_count AS BIGINT) AS mismatch_count,
  CAST(match_rate_percent AS DECIMAL(18, 4)) AS match_rate_percent,
  CAST(mean_absolute_error AS DECIMAL(18, 4)) AS mean_absolute_error,
  CAST(max_absolute_error AS DECIMAL(18, 4)) AS max_absolute_error
FROM overall_metrics

UNION ALL

SELECT
  'cycle' AS result_scope,
  population_scope,
  grouping_candidate,
  cycle_number,
  variant,
  CAST(comparable_count AS BIGINT),
  CAST(matched_within_tolerance_count AS BIGINT),
  CAST(mismatch_count AS BIGINT),
  CAST(match_rate_percent AS DECIMAL(18, 4)),
  CAST(mean_absolute_error AS DECIMAL(18, 4)),
  CAST(max_absolute_error AS DECIMAL(18, 4))
FROM cycle_metrics
WHERE comparable_count >= 30
ORDER BY result_scope, population_scope, grouping_candidate, cycle_number, variant;
