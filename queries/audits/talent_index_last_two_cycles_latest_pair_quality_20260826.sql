-- Talent index: calidad de la poblacion del ultimo par de ciclos.
--
-- Esta consulta acompana la reconciliacion de formula. No prueba el significado
-- del indice; confirma que la comparacion 8 -> 9 (o el ultimo par disponible)
-- no este dominada por duplicados, contradicciones o ausencia de componentes.
-- Los IDs solo se usan internamente para el join y no se devuelven.

WITH ordered_cycles AS (
  SELECT
    cycle_number,
    ROW_NUMBER() OVER (ORDER BY cycle_number DESC) AS cycle_rank
  FROM (
    SELECT DISTINCT cycle_number
    FROM hrda.master_talent_index
    WHERE cycle_number IS NOT NULL
  ) AS distinct_cycles
),
cycle_limits AS (
  SELECT
    MAX(CASE WHEN cycle_rank = 1 THEN cycle_number END) AS current_cycle,
    MAX(CASE WHEN cycle_rank = 2 THEN cycle_number END) AS previous_cycle
  FROM ordered_cycles
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
  INNER JOIN cycle_limits AS l
    ON m.cycle_number IN (l.current_cycle, l.previous_cycle)
  GROUP BY 1, 2
),
cycle_group_metrics AS (
  SELECT
    cycle_number,
    COUNT(*) AS employee_cycle_groups,
    COUNT(CASE WHEN source_rows > 1 THEN 1 END) AS duplicate_group_count,
    COUNT(CASE
      WHEN stock_values > 1 OR perf_values > 1 OR talent_index_values > 1
      THEN 1
    END) AS contradictory_group_count,
    COUNT(CASE WHEN stock IS NULL THEN 1 END) AS stock_missing_group_count,
    COUNT(CASE WHEN perf IS NULL THEN 1 END) AS perf_missing_group_count,
    COUNT(CASE WHEN talent_index IS NULL THEN 1 END) AS talent_index_missing_group_count
  FROM employee_cycle
  GROUP BY 1
),
latest_pair AS (
  SELECT
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
  INNER JOIN cycle_limits AS l
    ON current_cycle.cycle_number = l.current_cycle
  INNER JOIN employee_cycle AS previous_cycle
    ON previous_cycle.cycle_number = l.previous_cycle
   AND previous_cycle.empl_id = current_cycle.empl_id
),
pair_summary AS (
  SELECT
    COUNT(*) AS employee_present_in_both_cycles,
    COUNT(CASE WHEN grain_quality_pass = 1 THEN 1 END) AS grain_quality_pass_count,
    COUNT(CASE WHEN grain_quality_pass = 0 THEN 1 END) AS grain_quality_fail_count,
    COUNT(CASE
      WHEN grain_quality_pass = 1
       AND current_stock IS NOT NULL
       AND previous_stock IS NOT NULL
       AND current_perf IS NOT NULL
       AND previous_perf IS NOT NULL
       AND talent_index IS NOT NULL
      THEN 1
    END) AS comparable_count,
    COUNT(CASE
      WHEN grain_quality_pass = 1
       AND current_stock IS NOT NULL
       AND previous_stock IS NOT NULL
       AND MOD(current_stock + previous_stock, 2) <> 0
      THEN 1
    END) AS half_step_stock_average_count,
    COUNT(CASE
      WHEN grain_quality_pass = 1
       AND current_perf IS NOT NULL
       AND previous_perf IS NOT NULL
       AND MOD(current_perf + previous_perf, 2) <> 0
      THEN 1
    END) AS half_step_perf_average_count
  FROM latest_pair
)
SELECT
  l.current_cycle,
  l.previous_cycle,
  current_metrics.employee_cycle_groups AS current_employee_cycle_groups,
  previous_metrics.employee_cycle_groups AS previous_employee_cycle_groups,
  current_metrics.duplicate_group_count AS current_duplicate_group_count,
  previous_metrics.duplicate_group_count AS previous_duplicate_group_count,
  current_metrics.contradictory_group_count AS current_contradictory_group_count,
  previous_metrics.contradictory_group_count AS previous_contradictory_group_count,
  current_metrics.stock_missing_group_count AS current_stock_missing_group_count,
  previous_metrics.stock_missing_group_count AS previous_stock_missing_group_count,
  current_metrics.perf_missing_group_count AS current_perf_missing_group_count,
  previous_metrics.perf_missing_group_count AS previous_perf_missing_group_count,
  current_metrics.talent_index_missing_group_count AS current_talent_index_missing_group_count,
  previous_metrics.talent_index_missing_group_count AS previous_talent_index_missing_group_count,
  p.employee_present_in_both_cycles,
  p.grain_quality_pass_count,
  p.grain_quality_fail_count,
  p.comparable_count,
  p.half_step_stock_average_count,
  p.half_step_perf_average_count
FROM cycle_limits AS l
LEFT JOIN cycle_group_metrics AS current_metrics
  ON current_metrics.cycle_number = l.current_cycle
LEFT JOIN cycle_group_metrics AS previous_metrics
  ON previous_metrics.cycle_number = l.previous_cycle
CROSS JOIN pair_summary AS p;
