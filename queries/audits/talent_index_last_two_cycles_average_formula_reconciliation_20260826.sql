-- Talent index: reconciliacion de la formula actualizada de la presentacion.
--
-- Formula reportada en Talent Index Refresh_6.19.26.pptx:
--   Stock promedio = (Stock t-1 + Stock t) / 2
--   Performance promedio = (Performance t-1 + Performance t) / 2
--   Talent Index = 1,000,000 * Stock promedio
--                  + 500 * Performance promedio
--
-- Claim:
--   Evaluar si los dos ultimos ciclos disponibles por empleado explican el
--   talent_index almacenado en el ciclo actual, ya sea como valor bruto, como
--   reescala 0-100 o como posicion relativa dentro del ciclo.
--
-- Regla de aceptacion:
--   La formula solo se consideraria reproducida si, en la poblacion comparable
--   y en cada ciclo con al menos 30 casos, al menos 95% de los valores coincide
--   con una tolerancia de 0.01 puntos. La formula bruta se reporta por separado
--   porque su escala teorica es aproximadamente 1,000,500-5,002,500, mientras
--   que el target observado historicamente esta en escala 0-100.
--
-- Privacidad:
--   Los IDs solo se usan internamente para unir ciclos. El resultado es
--   agregado y no devuelve filas de empleados.

WITH ordered_cycles AS (
  SELECT
    cycle_number,
    ROW_NUMBER() OVER (ORDER BY cycle_number) AS cycle_position
  FROM (
    SELECT DISTINCT cycle_number
    FROM hrda.master_talent_index
    WHERE cycle_number IS NOT NULL
  ) AS distinct_cycles
),
employee_cycle AS (
  SELECT
    m.empl_id,
    m.cycle_number,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT m.stock) AS stock_values,
    COUNT(DISTINCT m.perf) AS perf_values,
    COUNT(DISTINCT m.talent_index) AS talent_index_values,
    MIN(m.stock) AS stock,
    MIN(m.perf) AS perf,
    MIN(m.talent_index) AS talent_index
  FROM hrda.master_talent_index AS m
  INNER JOIN ordered_cycles AS oc
    ON oc.cycle_number = m.cycle_number
  GROUP BY 1, 2
),
cycle_pair_population AS (
  SELECT
    current_cycle.cycle_number AS current_cycle,
    previous_cycle.cycle_number AS previous_cycle,
    current_cycle.empl_id,
    current_cycle.source_rows AS current_source_rows,
    previous_cycle.source_rows AS previous_source_rows,
    current_cycle.stock AS current_stock,
    previous_cycle.stock AS previous_stock,
    current_cycle.perf AS current_perf,
    previous_cycle.perf AS previous_perf,
    current_cycle.talent_index,
    CASE
      WHEN current_cycle.source_rows = 1
       AND previous_cycle.source_rows = 1
       AND current_cycle.stock_values <= 1
       AND previous_cycle.stock_values <= 1
       AND current_cycle.perf_values <= 1
       AND previous_cycle.perf_values <= 1
       AND current_cycle.talent_index_values <= 1
      THEN 1 ELSE 0
    END AS grain_quality_pass
  FROM employee_cycle AS current_cycle
  INNER JOIN ordered_cycles AS current_order
    ON current_order.cycle_number = current_cycle.cycle_number
  INNER JOIN ordered_cycles AS previous_order
    ON previous_order.cycle_position = current_order.cycle_position - 1
  INNER JOIN employee_cycle AS previous_cycle
    ON previous_cycle.cycle_number = previous_order.cycle_number
   AND previous_cycle.empl_id = current_cycle.empl_id
),
comparable AS (
  SELECT
    current_cycle,
    previous_cycle,
    current_stock,
    previous_stock,
    current_perf,
    previous_perf,
    talent_index,
    CAST((current_stock + previous_stock) / 2.0 AS DECIMAL(18, 6)) AS stock_average,
    CAST((current_perf + previous_perf) / 2.0 AS DECIMAL(18, 6)) AS perf_average
  FROM cycle_pair_population
  WHERE grain_quality_pass = 1
    AND current_stock IS NOT NULL
    AND previous_stock IS NOT NULL
    AND current_perf IS NOT NULL
    AND previous_perf IS NOT NULL
    AND talent_index IS NOT NULL
),
candidate_values AS (
  SELECT
    current_cycle,
    previous_cycle,
    talent_index,
    stock_average,
    perf_average,
    CAST(
      1000000.0 * stock_average + 500.0 * perf_average
      AS DECIMAL(18, 6)
    ) AS average_formula_value,
    CAST(
      100.0 * (
        (1000000.0 * stock_average + 500.0 * perf_average) - 1000500.0
      ) / 4002000.0
      AS DECIMAL(18, 8)
    ) AS average_formula_minmax_0_100,
    CAST(
      1000000.0 * current_stock + 500.0 * current_perf
      AS DECIMAL(18, 6)
    ) AS current_formula_value,
    CAST(
      100.0 * (
        (1000000.0 * current_stock + 500.0 * current_perf) - 1000500.0
      ) / 4002000.0
      AS DECIMAL(18, 8)
    ) AS current_formula_minmax_0_100,
    current_stock,
    current_perf
  FROM comparable
),
ranked_candidates AS (
  SELECT
    current_cycle,
    previous_cycle,
    talent_index,
    average_formula_value,
    average_formula_minmax_0_100,
    current_formula_value,
    current_formula_minmax_0_100,
    CAST(
      100.0 * CUME_DIST() OVER (
        PARTITION BY current_cycle
        ORDER BY stock_average, perf_average
      )
      AS DECIMAL(18, 8)
    ) AS average_formula_cume_dist,
    CAST(
      100.0 * PERCENT_RANK() OVER (
        PARTITION BY current_cycle
        ORDER BY stock_average, perf_average
      )
      AS DECIMAL(18, 8)
    ) AS average_formula_percent_rank,
    CAST(
      100.0 * CUME_DIST() OVER (
        PARTITION BY current_cycle
        ORDER BY current_stock, current_perf
      )
      AS DECIMAL(18, 8)
    ) AS current_formula_cume_dist,
    CAST(
      100.0 * PERCENT_RANK() OVER (
        PARTITION BY current_cycle
        ORDER BY current_stock, current_perf
      )
      AS DECIMAL(18, 8)
    ) AS current_formula_percent_rank
  FROM candidate_values
),
cycle_sizes AS (
  SELECT
    current_cycle,
    previous_cycle,
    COUNT(*) AS comparable_count
  FROM ranked_candidates
  GROUP BY 1, 2
),
report_population AS (
  SELECT
    r.current_cycle,
    r.previous_cycle,
    r.talent_index,
    r.average_formula_value,
    r.average_formula_minmax_0_100,
    r.current_formula_value,
    r.current_formula_minmax_0_100,
    r.average_formula_cume_dist,
    r.average_formula_percent_rank,
    r.current_formula_cume_dist,
    r.current_formula_percent_rank
  FROM ranked_candidates AS r
  INNER JOIN cycle_sizes AS s
    ON s.current_cycle = r.current_cycle
   AND s.previous_cycle = r.previous_cycle
  WHERE s.comparable_count >= 30
),
candidate_long AS (
  SELECT
    current_cycle,
    previous_cycle,
    talent_index,
    'last_two_average_raw' AS candidate_name,
    CAST(average_formula_value AS DECIMAL(18, 8)) AS candidate_value
  FROM report_population

  UNION ALL

  SELECT
    current_cycle,
    previous_cycle,
    talent_index,
    'last_two_average_minmax_0_100',
    CAST(average_formula_minmax_0_100 AS DECIMAL(18, 8))
  FROM report_population

  UNION ALL

  SELECT
    current_cycle,
    previous_cycle,
    talent_index,
    'last_two_average_cume_dist',
    CAST(average_formula_cume_dist AS DECIMAL(18, 8))
  FROM report_population

  UNION ALL

  SELECT
    current_cycle,
    previous_cycle,
    talent_index,
    'last_two_average_percent_rank',
    CAST(average_formula_percent_rank AS DECIMAL(18, 8))
  FROM report_population

  UNION ALL

  SELECT
    current_cycle,
    previous_cycle,
    talent_index,
    'current_cycle_cume_dist',
    CAST(current_formula_cume_dist AS DECIMAL(18, 8))
  FROM report_population

  UNION ALL

  SELECT
    current_cycle,
    previous_cycle,
    talent_index,
    'current_cycle_minmax_0_100',
    CAST(current_formula_minmax_0_100 AS DECIMAL(18, 8))
  FROM report_population
),
formula_metrics AS (
  SELECT
    'last_two_average_raw' AS candidate_name,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(talent_index - average_formula_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(talent_index - average_formula_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - average_formula_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(talent_index - average_formula_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(talent_index - average_formula_value)), 4) AS max_absolute_error,
    MIN(average_formula_value) AS candidate_min,
    MAX(average_formula_value) AS candidate_max,
    MIN(talent_index) AS stored_min,
    MAX(talent_index) AS stored_max
  FROM report_population

  UNION ALL

  SELECT
    'last_two_average_minmax_0_100',
    COUNT(*),
    COUNT(CASE WHEN ABS(talent_index - average_formula_minmax_0_100) <= 0.01 THEN 1 END),
    COUNT(CASE WHEN ABS(talent_index - average_formula_minmax_0_100) > 0.01 THEN 1 END),
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - average_formula_minmax_0_100) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4),
    ROUND(AVG(ABS(talent_index - average_formula_minmax_0_100)), 4),
    ROUND(MAX(ABS(talent_index - average_formula_minmax_0_100)), 4),
    MIN(average_formula_minmax_0_100),
    MAX(average_formula_minmax_0_100),
    MIN(talent_index),
    MAX(talent_index)
  FROM report_population

  UNION ALL

  SELECT
    'last_two_average_cume_dist',
    COUNT(*),
    COUNT(CASE WHEN ABS(talent_index - average_formula_cume_dist) <= 0.01 THEN 1 END),
    COUNT(CASE WHEN ABS(talent_index - average_formula_cume_dist) > 0.01 THEN 1 END),
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - average_formula_cume_dist) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4),
    ROUND(AVG(ABS(talent_index - average_formula_cume_dist)), 4),
    ROUND(MAX(ABS(talent_index - average_formula_cume_dist)), 4),
    MIN(average_formula_cume_dist),
    MAX(average_formula_cume_dist),
    MIN(talent_index),
    MAX(talent_index)
  FROM report_population

  UNION ALL

  SELECT
    'last_two_average_percent_rank',
    COUNT(*),
    COUNT(CASE WHEN ABS(talent_index - average_formula_percent_rank) <= 0.01 THEN 1 END),
    COUNT(CASE WHEN ABS(talent_index - average_formula_percent_rank) > 0.01 THEN 1 END),
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - average_formula_percent_rank) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4),
    ROUND(AVG(ABS(talent_index - average_formula_percent_rank)), 4),
    ROUND(MAX(ABS(talent_index - average_formula_percent_rank)), 4),
    MIN(average_formula_percent_rank),
    MAX(average_formula_percent_rank),
    MIN(talent_index),
    MAX(talent_index)
  FROM report_population

  UNION ALL

  SELECT
    'current_cycle_cume_dist',
    COUNT(*),
    COUNT(CASE WHEN ABS(talent_index - current_formula_cume_dist) <= 0.01 THEN 1 END),
    COUNT(CASE WHEN ABS(talent_index - current_formula_cume_dist) > 0.01 THEN 1 END),
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - current_formula_cume_dist) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4),
    ROUND(AVG(ABS(talent_index - current_formula_cume_dist)), 4),
    ROUND(MAX(ABS(talent_index - current_formula_cume_dist)), 4),
    MIN(current_formula_cume_dist),
    MAX(current_formula_cume_dist),
    MIN(talent_index),
    MAX(talent_index)
  FROM report_population

  UNION ALL

  SELECT
    'current_cycle_minmax_0_100',
    COUNT(*),
    COUNT(CASE WHEN ABS(talent_index - current_formula_minmax_0_100) <= 0.01 THEN 1 END),
    COUNT(CASE WHEN ABS(talent_index - current_formula_minmax_0_100) > 0.01 THEN 1 END),
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - current_formula_minmax_0_100) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4),
    ROUND(AVG(ABS(talent_index - current_formula_minmax_0_100)), 4),
    ROUND(MAX(ABS(talent_index - current_formula_minmax_0_100)), 4),
    MIN(current_formula_minmax_0_100),
    MAX(current_formula_minmax_0_100),
    MIN(talent_index),
    MAX(talent_index)
  FROM report_population
),
cycle_metrics AS (
  SELECT
    current_cycle,
    previous_cycle,
    candidate_name,
    COUNT(*) AS comparable_count,
    COUNT(CASE WHEN ABS(talent_index - candidate_value) <= 0.01 THEN 1 END) AS matched_within_tolerance_count,
    COUNT(CASE WHEN ABS(talent_index - candidate_value) > 0.01 THEN 1 END) AS mismatch_count,
    ROUND(100.0 * COUNT(CASE WHEN ABS(talent_index - candidate_value) <= 0.01 THEN 1 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(AVG(ABS(talent_index - candidate_value)), 4) AS mean_absolute_error,
    ROUND(MAX(ABS(talent_index - candidate_value)), 4) AS max_absolute_error,
    MIN(candidate_value) AS candidate_min,
    MAX(candidate_value) AS candidate_max,
    MIN(talent_index) AS stored_min,
    MAX(talent_index) AS stored_max
  FROM candidate_long
  GROUP BY 1, 2, 3
)
SELECT
  'overall' AS section,
  candidate_name,
  CAST(NULL AS INTEGER) AS current_cycle,
  CAST(NULL AS INTEGER) AS previous_cycle,
  CAST(comparable_count AS BIGINT),
  CAST(matched_within_tolerance_count AS BIGINT),
  CAST(mismatch_count AS BIGINT),
  CAST(match_rate_percent AS DECIMAL(18, 4)),
  CAST(mean_absolute_error AS DECIMAL(18, 4)),
  CAST(max_absolute_error AS DECIMAL(18, 4)),
  CAST(candidate_min AS DECIMAL(18, 4)),
  CAST(candidate_max AS DECIMAL(18, 4)),
  CAST(stored_min AS DECIMAL(18, 4)),
  CAST(stored_max AS DECIMAL(18, 4))
FROM formula_metrics

UNION ALL

SELECT
  'pair_coverage' AS section,
  'employee_present_in_both_cycles' AS candidate_name,
  CAST(NULL AS INTEGER),
  CAST(NULL AS INTEGER),
  COUNT(*),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  CAST(NULL AS DECIMAL(18, 4)),
  CAST(NULL AS DECIMAL(18, 4)),
  CAST(NULL AS DECIMAL(18, 4)),
  CAST(NULL AS DECIMAL(18, 4)),
  CAST(NULL AS DECIMAL(18, 4)),
  CAST(NULL AS DECIMAL(18, 4)),
  CAST(NULL AS DECIMAL(18, 4))
FROM cycle_pair_population
WHERE grain_quality_pass = 1

UNION ALL

SELECT
  'cycle' AS section,
  candidate_name,
  current_cycle,
  previous_cycle,
  CAST(comparable_count AS BIGINT),
  CAST(matched_within_tolerance_count AS BIGINT),
  CAST(mismatch_count AS BIGINT),
  CAST(match_rate_percent AS DECIMAL(18, 4)),
  CAST(mean_absolute_error AS DECIMAL(18, 4)),
  CAST(max_absolute_error AS DECIMAL(18, 4)),
  CAST(candidate_min AS DECIMAL(18, 4)),
  CAST(candidate_max AS DECIMAL(18, 4)),
  CAST(stored_min AS DECIMAL(18, 4)),
  CAST(stored_max AS DECIMAL(18, 4))
FROM cycle_metrics
ORDER BY section, candidate_name, current_cycle, previous_cycle;
