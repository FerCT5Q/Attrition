-- Talent index: reconciliación del join actual por empleado.
--
-- Claim:
--   Cuantificar el match entre la población activa del último snapshot laboral y la
--   fuente de Talent index. Se selecciona el mayor cycle_number por empleado sólo
--   como convención de recuperación actual. No es un join temporal validado.
--
-- Acceptance rule stated before execution for Join=2:
--   Cada empleado elegible debe empatar exactamente una vez, sin unmatched,
--   duplicados, multi-match ni conflictos, y la selección del ciclo debe estar
--   gobernada. Sin fecha efectiva/publicación oficial, Join queda como máximo en 1
--   aunque la reconciliación técnica actual sea determinista.

WITH latest_snapshot AS (
  SELECT MAX(fis_mo_end_dt) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
),
eligible AS (
  SELECT DISTINCT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    w.fis_mo_end_dt AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN latest_snapshot s
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
    AND w.fis_mo_end_dt = s.snapshot_date
),
raw_source AS (
  SELECT
    CAST(empl_id AS BIGINT) AS employee_id,
    cycle_number,
    talent_index
  FROM hrda.master_talent_index
),
source_people AS (
  SELECT DISTINCT employee_id
  FROM raw_source
  WHERE employee_id IS NOT NULL
),
employee_cycle AS (
  SELECT
    employee_id,
    cycle_number,
    COUNT(*) AS source_rows,
    COUNT(talent_index) AS populated_index_rows,
    COUNT(DISTINCT talent_index) AS distinct_index_values,
    MIN(talent_index) AS min_talent_index
  FROM raw_source
  WHERE employee_id IS NOT NULL
    AND cycle_number IS NOT NULL
  GROUP BY 1, 2
),
ranked_cycles AS (
  SELECT
    employee_id,
    cycle_number,
    source_rows,
    populated_index_rows,
    distinct_index_values,
    CASE
      WHEN distinct_index_values = 1
       AND populated_index_rows = source_rows
      THEN min_talent_index
      ELSE NULL
    END AS talent_index,
    ROW_NUMBER() OVER (
      PARTITION BY employee_id
      ORDER BY cycle_number DESC NULLS LAST
    ) AS cycle_rank
  FROM employee_cycle
),
selected_cycle AS (
  SELECT
    employee_id,
    cycle_number,
    source_rows,
    populated_index_rows,
    distinct_index_values,
    talent_index
  FROM ranked_cycles
  WHERE cycle_rank = 1
),
global_cycle AS (
  SELECT MAX(cycle_number) AS global_max_cycle_number
  FROM employee_cycle
),
global_cycle_employee AS (
  SELECT
    e.employee_id,
    e.source_rows,
    e.populated_index_rows,
    e.distinct_index_values,
    CASE
      WHEN e.distinct_index_values = 1
       AND e.populated_index_rows = e.source_rows
      THEN e.min_talent_index
      ELSE NULL
    END AS talent_index
  FROM employee_cycle e
  CROSS JOIN global_cycle g
  WHERE e.cycle_number = g.global_max_cycle_number
),
joined AS (
  SELECT
    e.employee_id,
    e.snapshot_date,
    CASE WHEN p.employee_id IS NOT NULL THEN 1 ELSE 0 END AS any_source_match,
    s.employee_id AS selected_employee_id,
    s.cycle_number,
    s.source_rows,
    s.populated_index_rows,
    s.distinct_index_values,
    s.talent_index
  FROM eligible e
  LEFT JOIN source_people p
    ON p.employee_id = e.employee_id
  LEFT JOIN selected_cycle s
    ON s.employee_id = e.employee_id
),
global_joined AS (
  SELECT
    e.employee_id,
    g.employee_id AS global_cycle_employee_id,
    g.talent_index
  FROM eligible e
  LEFT JOIN global_cycle_employee g
    ON g.employee_id = e.employee_id
),
join_metrics AS (
  SELECT
    MAX(snapshot_date) AS current_snapshot_date,
    COUNT(*) AS eligible_count,
    COUNT(CASE WHEN any_source_match = 1 THEN 1 END) AS identity_matched_count,
    COUNT(CASE WHEN any_source_match = 0 THEN 1 END) AS identity_unmatched_count,
    COUNT(CASE WHEN selected_employee_id IS NOT NULL THEN 1 END) AS matched_count,
    COUNT(CASE WHEN selected_employee_id IS NULL THEN 1 END) AS unmatched_count,
    COUNT(CASE WHEN talent_index IS NOT NULL THEN 1 END) AS observable_count,
    COALESCE(SUM(CASE WHEN source_rows > 1 THEN source_rows - 1 ELSE 0 END), 0)
      AS duplicate_count,
    COUNT(CASE WHEN source_rows > 1 THEN 1 END) AS multi_match_count,
    COUNT(CASE
      WHEN distinct_index_values > 1
        OR (populated_index_rows > 0 AND populated_index_rows < source_rows)
      THEN 1
    END) AS conflicting_selected_key_count
  FROM joined
),
global_metrics AS (
  SELECT
    COUNT(CASE WHEN global_cycle_employee_id IS NOT NULL THEN 1 END)
      AS global_cycle_matched_count,
    COUNT(CASE WHEN talent_index IS NOT NULL THEN 1 END)
      AS global_cycle_observable_count
  FROM global_joined
),
source_metrics AS (
  SELECT
    COUNT(CASE WHEN source_rows > 1 THEN 1 END) AS source_duplicate_key_groups,
    COUNT(CASE
      WHEN distinct_index_values > 1
        OR (populated_index_rows > 0 AND populated_index_rows < source_rows)
      THEN 1
    END) AS source_conflicting_key_groups
  FROM employee_cycle
)
SELECT
  'Talent index' AS variable_name,
  join_metrics.current_snapshot_date,
  global_cycle.global_max_cycle_number,
  join_metrics.eligible_count,
  join_metrics.identity_matched_count,
  join_metrics.identity_unmatched_count,
  join_metrics.matched_count,
  join_metrics.unmatched_count,
  join_metrics.observable_count,
  join_metrics.duplicate_count,
  join_metrics.multi_match_count,
  join_metrics.conflicting_selected_key_count,
  global_metrics.global_cycle_matched_count,
  global_metrics.global_cycle_observable_count,
  source_metrics.source_duplicate_key_groups,
  source_metrics.source_conflicting_key_groups,
  ROUND(
    100.0 * join_metrics.matched_count / NULLIF(join_metrics.eligible_count, 0),
    4
  ) AS matched_percent,
  ROUND(
    100.0 * join_metrics.observable_count / NULLIF(join_metrics.eligible_count, 0),
    4
  ) AS observable_percent,
  ROUND(
    100.0 * global_metrics.global_cycle_observable_count
      / NULLIF(join_metrics.eligible_count, 0),
    4
  ) AS global_cycle_observable_percent
FROM join_metrics
CROSS JOIN global_metrics
CROSS JOIN source_metrics
CROSS JOIN global_cycle;
