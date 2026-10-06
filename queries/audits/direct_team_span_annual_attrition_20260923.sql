/*
  Analisis interno exploratorio V7: tamano del equipo directo (span) y
  attrition voluntaria anual.

  Definicion primaria: el span se reconstruye contando las relaciones
  manager_employee_id en el mismo snapshot del 2025-08-24. No se usan los
  campos almacenados de numero de reportes como valor del visual.

  Poblacion base: trabajadores Employee, Regular y activos al snapshot.
  Cobertura: se excluye una persona cuando su relacion de manager es nula,
  conflictiva o no se puede resolver contra un nodo Employee, Regular y activo
  del mismo snapshot. Esta regla mantiene la unidad de equipo dentro de la
  poblacion regular visible.
  Esta exclusion se informa como cobertura; no se convierte en una banda.

  Outcome: term_type estrictamente VOLUNTARY con term_date en
  (2025-08-24, 2026-08-23]. Los identificadores se usan solo dentro de CTEs y
  joins; el resultado final devuelve exclusivamente agregados.

  Regla de aceptacion para el artefacto V7:
  - 45,003 empleados base y 44,737 elegibles con manager resoluble;
  - 266 exclusiones de cobertura;
  - las seis bandas reconcilian a 44,737 empleados y 2,480 salidas voluntarias;
  - el tamano exacto 5 reconcilia a 7,160 empleados y 1,432 equipos;
  - el tamano exacto 20 reconcilia a 80 empleados y 4 equipos;
  - cada tasa es salidas voluntarias / empleados del cohorte base.
*/
WITH
params AS (
  SELECT DATE '2025-08-24' AS baseline_date,
         DATE '2026-08-23' AS outcome_cutoff
),
snapshot_source AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    CAST(NULLIF(TRIM(CAST(w.manager_employee_id AS VARCHAR(64))), '') AS BIGINT)
      AS manager_employee_id,
    w.worker_type,
    w.employee_type
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_date
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
),
active_nodes AS (
  SELECT
    employee_id,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT COALESCE(CAST(manager_employee_id AS VARCHAR(64)), '<NULL>'))
      AS manager_assignment_count,
    MIN(manager_employee_id) AS canonical_manager_employee_id,
    MAX(CASE
      WHEN worker_type = 'Employee' AND employee_type = 'Regular' THEN 1
      ELSE 0
    END) AS active_regular_flag
  FROM snapshot_source
  GROUP BY 1
),
baseline_employees AS (
  SELECT
    employee_id,
    CASE
      WHEN manager_assignment_count = 1 THEN canonical_manager_employee_id
      ELSE NULL
    END AS manager_employee_id,
    manager_assignment_count
  FROM active_nodes
  WHERE active_regular_flag = 1
),
eligible_relationships AS (
  SELECT
    b.employee_id,
    b.manager_employee_id
  FROM baseline_employees b
  INNER JOIN active_nodes manager_node
    ON manager_node.employee_id = b.manager_employee_id
   AND manager_node.active_regular_flag = 1
  WHERE b.manager_assignment_count = 1
    AND b.manager_employee_id IS NOT NULL
),
team_sizes AS (
  SELECT
    manager_employee_id,
    COUNT(DISTINCT employee_id) AS direct_report_count
  FROM eligible_relationships
  GROUP BY 1
),
voluntary_events AS (
  SELECT DISTINCT CAST(w.employee_id AS BIGINT) AS employee_id
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > p.baseline_date
    AND CAST(w.term_date AS DATE) <= p.outcome_cutoff
    AND w.employee_id IS NOT NULL
),
eligible_with_span AS (
  SELECT
    e.employee_id,
    e.manager_employee_id,
    t.direct_report_count,
    CASE WHEN v.employee_id IS NULL THEN 0 ELSE 1 END AS voluntary_exit
  FROM eligible_relationships e
  INNER JOIN team_sizes t
    ON t.manager_employee_id = e.manager_employee_id
  LEFT JOIN voluntary_events v
    ON v.employee_id = e.employee_id
),
banded AS (
  SELECT
    CASE
      WHEN direct_report_count BETWEEN 1 AND 4 THEN '1-4'
      WHEN direct_report_count BETWEEN 5 AND 9 THEN '5-9'
      WHEN direct_report_count BETWEEN 10 AND 14 THEN '10-14'
      WHEN direct_report_count BETWEEN 15 AND 19 THEN '15-19'
      WHEN direct_report_count BETWEEN 20 AND 29 THEN '20-29'
      WHEN direct_report_count >= 30 THEN '30+'
      ELSE 'invalid'
    END AS span_band,
    CASE
      WHEN direct_report_count BETWEEN 1 AND 4 THEN 1
      WHEN direct_report_count BETWEEN 5 AND 9 THEN 5
      WHEN direct_report_count BETWEEN 10 AND 14 THEN 10
      WHEN direct_report_count BETWEEN 15 AND 19 THEN 15
      WHEN direct_report_count BETWEEN 20 AND 29 THEN 20
      WHEN direct_report_count >= 30 THEN 30
      ELSE -1
    END AS band_order,
    employee_id,
    manager_employee_id,
    direct_report_count,
    voluntary_exit
  FROM eligible_with_span
),
metric_rows AS (
  SELECT
    'metric' AS row_type,
    'baseline_employee_count' AS metric,
    NULL::VARCHAR(16) AS span_band,
    NULL::INTEGER AS band_order,
    NULL::BIGINT AS direct_report_count,
    COUNT(DISTINCT employee_id)::BIGINT AS employee_count,
    NULL::BIGINT AS team_count,
    NULL::BIGINT AS voluntary_exits,
    NULL::DECIMAL(18,8) AS annual_attrition_rate_percent
  FROM baseline_employees

  UNION ALL

  SELECT
    'metric',
    'eligible_employee_count',
    NULL::VARCHAR(16),
    NULL::INTEGER,
    NULL::BIGINT,
    COUNT(DISTINCT employee_id)::BIGINT,
    NULL::BIGINT,
    NULL::BIGINT,
    NULL::DECIMAL(18,8)
  FROM eligible_with_span

  UNION ALL

  SELECT
    'metric',
    'unresolvable_manager_exclusion_count',
    NULL::VARCHAR(16),
    NULL::INTEGER,
    NULL::BIGINT,
    (
      SELECT COUNT(DISTINCT employee_id) FROM baseline_employees
    ) - COUNT(DISTINCT employee_id),
    NULL::BIGINT,
    NULL::BIGINT,
    NULL::DECIMAL(18,8)
  FROM eligible_with_span

  UNION ALL

  SELECT
    'metric',
    'eligible_team_count',
    NULL::VARCHAR(16),
    NULL::INTEGER,
    NULL::BIGINT,
    NULL::BIGINT,
    COUNT(DISTINCT manager_employee_id)::BIGINT,
    NULL::BIGINT,
    NULL::DECIMAL(18,8)
  FROM eligible_with_span

  UNION ALL

  SELECT
    'metric',
    'baseline_voluntary_exits',
    NULL::VARCHAR(16),
    NULL::INTEGER,
    NULL::BIGINT,
    NULL::BIGINT,
    NULL::BIGINT,
    SUM(voluntary_exit)::BIGINT,
    NULL::DECIMAL(18,8)
  FROM eligible_with_span

  UNION ALL

  SELECT
    'metric',
    'manager_assignment_conflict_count',
    NULL::VARCHAR(16),
    NULL::INTEGER,
    NULL::BIGINT,
    COUNT(DISTINCT employee_id)::BIGINT,
    NULL::BIGINT,
    NULL::BIGINT,
    NULL::DECIMAL(18,8)
  FROM baseline_employees
  WHERE manager_assignment_count <> 1

  UNION ALL

  SELECT
    'metric',
    'missing_manager_value_count',
    NULL::VARCHAR(16),
    NULL::INTEGER,
    NULL::BIGINT,
    COUNT(DISTINCT employee_id)::BIGINT,
    NULL::BIGINT,
    NULL::BIGINT,
    NULL::DECIMAL(18,8)
  FROM baseline_employees
  WHERE manager_assignment_count = 1
    AND manager_employee_id IS NULL

  UNION ALL

  SELECT
    'metric',
    'manager_not_active_regular_snapshot_count',
    NULL::VARCHAR(16),
    NULL::INTEGER,
    NULL::BIGINT,
    COUNT(DISTINCT b.employee_id)::BIGINT,
    NULL::BIGINT,
    NULL::BIGINT,
    NULL::DECIMAL(18,8)
  FROM baseline_employees b
  LEFT JOIN active_nodes manager_node
    ON manager_node.employee_id = b.manager_employee_id
  WHERE b.manager_assignment_count = 1
    AND b.manager_employee_id IS NOT NULL
    AND COALESCE(manager_node.active_regular_flag, 0) <> 1
),
band_rows AS (
  SELECT
    'span_band' AS row_type,
    'direct_team_span' AS metric,
    span_band,
    band_order,
    NULL::BIGINT AS direct_report_count,
    COUNT(DISTINCT employee_id)::BIGINT AS employee_count,
    COUNT(DISTINCT manager_employee_id)::BIGINT AS team_count,
    SUM(voluntary_exit)::BIGINT AS voluntary_exits,
    100.0 * SUM(voluntary_exit) / NULLIF(COUNT(DISTINCT employee_id), 0)
      AS annual_attrition_rate_percent
  FROM banded
  GROUP BY 1, 2, 3, 4
),
exact_rows AS (
  SELECT
    'exact_span' AS row_type,
    'direct_team_span' AS metric,
    NULL::VARCHAR(16) AS span_band,
    NULL::INTEGER AS band_order,
    direct_report_count,
    COUNT(DISTINCT employee_id)::BIGINT AS employee_count,
    COUNT(DISTINCT manager_employee_id)::BIGINT AS team_count,
    SUM(voluntary_exit)::BIGINT AS voluntary_exits,
    100.0 * SUM(voluntary_exit) / NULLIF(COUNT(DISTINCT employee_id), 0)
      AS annual_attrition_rate_percent
  FROM banded
  WHERE direct_report_count IN (5, 20)
  GROUP BY 1, 2, 3, 4, 5
),
all_rows AS (
  SELECT
    row_type,
    metric,
    span_band,
    band_order,
    direct_report_count,
    employee_count,
    team_count,
    voluntary_exits,
    annual_attrition_rate_percent
  FROM metric_rows
  UNION ALL
  SELECT
    row_type,
    metric,
    span_band,
    band_order,
    direct_report_count,
    employee_count,
    team_count,
    voluntary_exits,
    annual_attrition_rate_percent
  FROM band_rows
  UNION ALL
  SELECT
    row_type,
    metric,
    span_band,
    band_order,
    direct_report_count,
    employee_count,
    team_count,
    voluntary_exits,
    annual_attrition_rate_percent
  FROM exact_rows
)
SELECT
  row_type,
  metric,
  span_band,
  band_order,
  direct_report_count,
  employee_count,
  team_count,
  voluntary_exits,
  annual_attrition_rate_percent
FROM all_rows
ORDER BY
  CASE row_type WHEN 'metric' THEN 1 WHEN 'span_band' THEN 2 ELSE 3 END,
  COALESCE(band_order, 0),
  COALESCE(direct_report_count, 0),
  metric;
