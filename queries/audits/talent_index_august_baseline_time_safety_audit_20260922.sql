-- Propósito: comprobar si un ciclo almacenado de Talent Index puede asignarse
-- de forma segura a un baseline fiscal de agosto para medir attrition prospectivo.
--
-- Entrega: presentation; la consulta es exclusivamente agregada. No devuelve
-- identificadores, valores individuales ni texto libre.
--
-- Claim: un valor de Talent Index sólo puede segmentar la cohorte de agosto si
-- la fuente confirma una fecha de vigencia/publicación de negocio en o antes
-- del snapshot y el join empleado-ciclo es único y sin valores conflictivos.
--
-- Regla de aceptación definida antes de ejecutar:
--   1. Debe existir una fecha de negocio oficial (efectiva, de evaluación o de
--      publicación) que vincule el ciclo candidato con cada baseline. Esta
--      condición se revisa junto con
--      talent_index_snapshot_history_schema_audit_20260921.sql.
--   2. Para cada empleado del baseline, el ciclo elegido debe producir como
--      máximo un valor no conflictivo; se reportan matches, duplicados y
--      conflictos para verificar el grain.
--   3. last_modified_date y airflow_execution_date son timestamps técnicos:
--      se muestran sólo como diagnóstico y nunca satisfacen la condición 1.
--
-- Si la condición 1 no se demuestra, no se calcula ni publica attrition por
-- banda: atribuir un ciclo retrospectivamente sería leakage potencial.

WITH august_snapshots AS (
  SELECT
    EXTRACT(YEAR FROM fis_mo_end_dt)::INTEGER AS baseline_year,
    MAX(fis_mo_end_dt) AS baseline_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE EXTRACT(MONTH FROM fis_mo_end_dt) = 8
    AND EXTRACT(YEAR FROM fis_mo_end_dt) BETWEEN 2023 AND 2025
  GROUP BY 1
),
baseline_cohorts AS (
  SELECT DISTINCT
    s.baseline_year,
    s.baseline_snapshot_date,
    w.employee_id
  FROM august_snapshots s
  INNER JOIN hrda.post_hire_monthly_worker_dtls w
    ON w.fis_mo_end_dt = s.baseline_snapshot_date
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND COALESCE(w.is_rf360_yes_no, 0) = 0
),
cycle_list AS (
  SELECT DISTINCT cycle_number
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
),
cycle_employee_quality AS (
  SELECT
    CAST(empl_id AS BIGINT) AS employee_id,
    cycle_number,
    COUNT(*) AS source_rows_for_employee_cycle,
    COUNT(DISTINCT talent_index) AS distinct_talent_index_values,
    MAX(CASE WHEN talent_index IS NOT NULL THEN 1 ELSE 0 END) AS has_talent_index_value
  FROM hrda.master_talent_index
  WHERE empl_id IS NOT NULL
    AND cycle_number IS NOT NULL
  GROUP BY 1, 2
),
cycle_technical_timing AS (
  SELECT
    cycle_number,
    MIN(last_modified_date) AS min_technical_last_modified_date,
    MAX(last_modified_date) AS max_technical_last_modified_date,
    MIN(airflow_execution_date) AS min_technical_airflow_execution_date,
    MAX(airflow_execution_date) AS max_technical_airflow_execution_date
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
  GROUP BY 1
)
SELECT
  c.baseline_year,
  c.baseline_snapshot_date,
  cycles.cycle_number,
  COUNT(DISTINCT c.employee_id) AS baseline_employees,
  COUNT(DISTINCT CASE WHEN q.employee_id IS NOT NULL THEN c.employee_id END)
    AS matched_employees,
  COUNT(DISTINCT CASE
    WHEN q.has_talent_index_value = 1
     AND q.source_rows_for_employee_cycle = 1
     AND q.distinct_talent_index_values = 1
    THEN c.employee_id
  END) AS usable_nonconflicting_value_employees,
  COUNT(DISTINCT CASE
    WHEN q.source_rows_for_employee_cycle > 1 THEN c.employee_id
  END) AS duplicate_employee_cycle_employees,
  COUNT(DISTINCT CASE
    WHEN q.distinct_talent_index_values > 1 THEN c.employee_id
  END) AS conflicting_value_employees,
  t.min_technical_last_modified_date,
  t.max_technical_last_modified_date,
  t.min_technical_airflow_execution_date,
  t.max_technical_airflow_execution_date
FROM baseline_cohorts c
CROSS JOIN cycle_list cycles
LEFT JOIN cycle_employee_quality q
  ON q.employee_id = c.employee_id
 AND q.cycle_number = cycles.cycle_number
INNER JOIN cycle_technical_timing t
  ON t.cycle_number = cycles.cycle_number
GROUP BY
  c.baseline_year,
  c.baseline_snapshot_date,
  cycles.cycle_number,
  t.min_technical_last_modified_date,
  t.max_technical_last_modified_date,
  t.min_technical_airflow_execution_date,
  t.max_technical_airflow_execution_date
ORDER BY c.baseline_year, cycles.cycle_number;
