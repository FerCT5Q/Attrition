/*
  BU L3 como mapping histórico para el frame de modelado.

  Claim: cada empleado-snapshot elegible puede recibir como máximo una versión
  válida de BU L3 mediante cost_centerid = nk_dept_id y la ventana SCD
  [edw_effective_dt, edw_end_dt).

  Regla de aceptación previa:
  - employee_snapshot_rows = model_rows después de deduplicar la población;
  - duplicate_valid_matches = 0 y multi_bu_valid_matches = 0;
  - unmatched_rows se reporta y se codifica como (unknown), no se elimina;
  - no se permiten matches cuyo edw_effective_dt sea posterior al snapshot;
  - la población y el periodo se mantienen alineados con el SQL de F+Q.

  El resultado es exclusivamente agregado. employee_id se usa sólo dentro de
  COUNT DISTINCT y GROUP BY internos; no sale en el resultado.
*/
WITH params AS (
  SELECT
    DATE '2020-07-26' AS start_date,
    DATE '2026-09-07' AS end_date
),
employee_snapshot AS (
  SELECT
    CAST(p.fis_mo_end_dt AS DATE) AS snapshot_date,
    p.employee_id,
    COUNT(DISTINCT NULLIF(TRIM(p.cost_centerid), '')) AS cost_center_values,
    MAX(NULLIF(TRIM(p.cost_centerid), '')) AS cost_centerid
  FROM hrda.post_hire_monthly_worker_dtls p
  WHERE CAST(p.fis_mo_end_dt AS DATE) BETWEEN (SELECT start_date FROM params)
    AND (SELECT end_date FROM params)
    AND p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
    AND p.is_rf360_yes_no = 0
    AND TRIM(p.eng_or_noneng) = 'Engineering'
    AND p.employee_id IS NOT NULL
  GROUP BY 1, 2
),
valid_matches AS (
  SELECT
    e.snapshot_date,
    e.employee_id,
    e.cost_centerid,
    e.cost_center_values,
    d.ude_bu_reporting_l3 AS bu_l3,
    d.edw_effective_dt,
    d.edw_end_dt
  FROM employee_snapshot e
  LEFT JOIN hrda.d_department d
    ON CAST(d.nk_dept_id AS VARCHAR) = e.cost_centerid
   AND CAST(d.edw_effective_dt AS DATE) <= e.snapshot_date
   AND (
        d.edw_end_dt IS NULL
        OR e.snapshot_date < CAST(d.edw_end_dt AS DATE)
   )
),
per_snapshot AS (
  SELECT
    snapshot_date,
    employee_id,
    MAX(cost_center_values) AS cost_center_values,
    COUNT(d.edw_effective_dt) AS valid_match_rows,
    COUNT(DISTINCT NULLIF(TRIM(bu_l3), '')) AS valid_bu_values,
    MAX(CASE WHEN NULLIF(TRIM(bu_l3), '') IS NOT NULL THEN 1 ELSE 0 END) AS has_bu,
    MAX(CASE WHEN cost_centerid IS NOT NULL THEN 1 ELSE 0 END) AS has_cost_center
  FROM valid_matches d
  GROUP BY 1, 2
),
future_mapping AS (
  SELECT DISTINCT
    e.snapshot_date,
    e.employee_id
  FROM employee_snapshot e
  INNER JOIN hrda.d_department d
    ON CAST(d.nk_dept_id AS VARCHAR) = e.cost_centerid
   AND CAST(d.edw_effective_dt AS DATE) > e.snapshot_date
  WHERE NOT EXISTS (
    SELECT 1
    FROM hrda.d_department prior_d
    WHERE CAST(prior_d.nk_dept_id AS VARCHAR) = e.cost_centerid
      AND CAST(prior_d.edw_effective_dt AS DATE) <= e.snapshot_date
      AND (
           prior_d.edw_end_dt IS NULL
           OR e.snapshot_date < CAST(prior_d.edw_end_dt AS DATE)
      )
  )
),
department_history AS (
  SELECT
    CAST(d.nk_dept_id AS VARCHAR) AS nk_dept_id,
    COUNT(DISTINCT NULLIF(TRIM(d.ude_bu_reporting_l3), '')) AS bu_values,
    COUNT(*) AS mapping_rows
  FROM hrda.d_department d
  GROUP BY 1
),
aggregate_metrics AS (
  SELECT 'employee_snapshot_rows' AS metric,
         COUNT(*)::DECIMAL(20,4) AS value,
         COUNT(DISTINCT employee_id)::DECIMAL(20,4) AS value_2
  FROM per_snapshot
  UNION ALL
  SELECT 'snapshot_dates', COUNT(DISTINCT snapshot_date)::DECIMAL(20,4), NULL
  FROM per_snapshot
  UNION ALL
  SELECT 'rows_with_cost_center', SUM(CASE WHEN has_cost_center = 1 THEN 1 ELSE 0 END)::DECIMAL(20,4), NULL
  FROM per_snapshot
  UNION ALL
  SELECT 'rows_with_multiple_cost_centers', SUM(CASE WHEN cost_center_values > 1 THEN 1 ELSE 0 END)::DECIMAL(20,4), NULL
  FROM per_snapshot
  UNION ALL
  SELECT 'matched_rows', SUM(CASE WHEN valid_match_rows > 0 THEN 1 ELSE 0 END)::DECIMAL(20,4), NULL
  FROM per_snapshot
  UNION ALL
  SELECT 'unmatched_rows', SUM(CASE WHEN valid_match_rows = 0 THEN 1 ELSE 0 END)::DECIMAL(20,4), NULL
  FROM per_snapshot
  UNION ALL
  SELECT 'duplicate_valid_matches', SUM(CASE WHEN valid_match_rows > 1 THEN 1 ELSE 0 END)::DECIMAL(20,4), NULL
  FROM per_snapshot
  UNION ALL
  SELECT 'multi_bu_valid_matches', SUM(CASE WHEN valid_bu_values > 1 THEN 1 ELSE 0 END)::DECIMAL(20,4), NULL
  FROM per_snapshot
  UNION ALL
  SELECT 'rows_with_bu_l3', SUM(CASE WHEN has_bu = 1 THEN 1 ELSE 0 END)::DECIMAL(20,4), NULL
  FROM per_snapshot
  UNION ALL
  SELECT 'future_only_mapping_rows', COUNT(*)::DECIMAL(20,4), NULL
  FROM future_mapping
  UNION ALL
  SELECT 'department_ids_with_multiple_bu_values', SUM(CASE WHEN bu_values > 1 THEN 1 ELSE 0 END)::DECIMAL(20,4),
         COUNT(*)::DECIMAL(20,4)
  FROM department_history
)
SELECT metric, value, value_2
FROM aggregate_metrics
ORDER BY metric;
