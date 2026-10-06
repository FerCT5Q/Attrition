-- Talent index: perfil agregado de escalas y disponibilidad de componentes.
--
-- Claim:
--   Identificar, por ciclo, los dominios aproximados, nulls y filas comparables
--   antes de evaluar formulas candidatas contra talent_index.
--
-- Regla de interpretacion:
--   Solo se interpretan ciclos con al menos 30 empleados internos. Este perfil
--   no confirma la formula; prepara la poblacion para una reconciliacion.

WITH base AS (
  SELECT
    cycle_number,
    NULLIF(TRIM(cycle_name), '') AS cycle_name,
    empl_id,
    perf,
    prev_perf,
    stock,
    bonus,
    promo_quartile,
    talent_quartile,
    promo_index,
    talent_index
  FROM hrda.master_talent_index
),
cycle_counts AS (
  SELECT
    cycle_number,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT empl_id) AS distinct_employees,
    COUNT(DISTINCT cycle_name) AS distinct_cycle_names,
    COUNT(DISTINCT talent_index) AS distinct_talent_index_values,
    COUNT(CASE WHEN talent_index IS NOT NULL THEN 1 END) AS populated_talent_index_rows,
    COUNT(CASE WHEN perf IS NOT NULL THEN 1 END) AS populated_perf_rows,
    COUNT(CASE WHEN prev_perf IS NOT NULL THEN 1 END) AS populated_prev_perf_rows,
    COUNT(CASE WHEN stock IS NOT NULL THEN 1 END) AS populated_stock_rows,
    COUNT(CASE WHEN bonus IS NOT NULL THEN 1 END) AS populated_bonus_rows,
    COUNT(CASE WHEN promo_quartile IS NOT NULL THEN 1 END) AS populated_promo_quartile_rows,
    COUNT(CASE WHEN talent_quartile IS NOT NULL THEN 1 END) AS populated_talent_quartile_rows,
    COUNT(CASE WHEN promo_index IS NOT NULL THEN 1 END) AS populated_promo_index_rows,
    MIN(perf) AS min_perf,
    MAX(perf) AS max_perf,
    MIN(prev_perf) AS min_prev_perf,
    MAX(prev_perf) AS max_prev_perf,
    MIN(stock) AS min_stock,
    MAX(stock) AS max_stock,
    MIN(bonus) AS min_bonus,
    MAX(bonus) AS max_bonus,
    MIN(promo_quartile) AS min_promo_quartile,
    MAX(promo_quartile) AS max_promo_quartile,
    MIN(talent_quartile) AS min_talent_quartile,
    MAX(talent_quartile) AS max_talent_quartile,
    MIN(promo_index) AS min_promo_index,
    MAX(promo_index) AS max_promo_index,
    MIN(talent_index) AS min_talent_index,
    MAX(talent_index) AS max_talent_index
  FROM base
  WHERE cycle_number IS NOT NULL
  GROUP BY 1
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
    COUNT(DISTINCT promo_quartile) AS promo_quartile_values,
    COUNT(DISTINCT talent_quartile) AS talent_quartile_values,
    COUNT(DISTINCT promo_index) AS promo_index_values,
    COUNT(DISTINCT talent_index) AS talent_index_values,
    MIN(perf) AS perf_value,
    MIN(prev_perf) AS prev_perf_value,
    MIN(stock) AS stock_value,
    MIN(bonus) AS bonus_value,
    MIN(promo_quartile) AS promo_quartile_value,
    MIN(talent_quartile) AS talent_quartile_value,
    MIN(promo_index) AS promo_index_value,
    MIN(talent_index) AS talent_index_value
  FROM base
  WHERE cycle_number IS NOT NULL
    AND empl_id IS NOT NULL
  GROUP BY 1, 2
),
group_metrics AS (
  SELECT
    cycle_number,
    COUNT(*) AS employee_cycle_groups,
    COUNT(CASE WHEN rows_in_group > 1 THEN 1 END) AS employee_cycle_groups_with_duplicates,
    COUNT(CASE
      WHEN perf_values <= 1
       AND prev_perf_values <= 1
       AND stock_values <= 1
       AND bonus_values <= 1
       AND promo_quartile_values <= 1
       AND talent_quartile_values <= 1
       AND promo_index_values <= 1
       AND talent_index_values <= 1
      THEN 1
    END) AS internally_consistent_employee_cycle_groups,
    COUNT(CASE
      WHEN talent_index_values = 1
       AND perf_value IS NOT NULL
       AND stock_value IS NOT NULL
       AND bonus_value IS NOT NULL
       AND promo_index_value IS NOT NULL
      THEN 1
    END) AS comparable_all_four_groups,
    COUNT(CASE
      WHEN talent_index_values = 1
       AND perf_value IS NOT NULL
       AND stock_value IS NOT NULL
       AND bonus_value IS NOT NULL
      THEN 1
    END) AS comparable_three_core_groups
  FROM employee_cycle
  GROUP BY 1
)
SELECT
  c.cycle_number,
  c.source_rows,
  c.distinct_employees,
  c.distinct_cycle_names,
  c.distinct_talent_index_values,
  c.populated_talent_index_rows,
  c.populated_perf_rows,
  c.populated_prev_perf_rows,
  c.populated_stock_rows,
  c.populated_bonus_rows,
  c.populated_promo_quartile_rows,
  c.populated_talent_quartile_rows,
  c.populated_promo_index_rows,
  c.min_perf,
  c.max_perf,
  c.min_prev_perf,
  c.max_prev_perf,
  c.min_stock,
  c.max_stock,
  c.min_bonus,
  c.max_bonus,
  c.min_promo_quartile,
  c.max_promo_quartile,
  c.min_talent_quartile,
  c.max_talent_quartile,
  c.min_promo_index,
  c.max_promo_index,
  c.min_talent_index,
  c.max_talent_index,
  g.employee_cycle_groups,
  g.employee_cycle_groups_with_duplicates,
  g.internally_consistent_employee_cycle_groups,
  g.comparable_all_four_groups,
  g.comparable_three_core_groups
FROM cycle_counts AS c
JOIN group_metrics AS g USING (cycle_number)
WHERE c.distinct_employees >= 30
ORDER BY c.cycle_number;
