-- Talent index: resumen agregado de fechas tecnicas, ciclos y empates temporales.
--
-- Claim:
--   Determinar si cada ciclo tiene una fecha util de conocimiento y si esa fecha
--   permite seleccionar un solo ciclo por empleado sin una regla adicional.
--
-- Acceptance rule stated before execution for fully governed timing:
--   Todos los ciclos utilizables deben tener fecha oficial de publicacion, no debe
--   haber ciclos sin fecha y no deben existir varios ciclos del mismo empleado con
--   la misma fecha de disponibilidad salvo que exista una regla oficial de version.
--
-- Note:
--   last_modified_date y airflow_execution_date son fechas tecnicas. Su existencia
--   no demuestra la fecha oficial de publicacion del ciclo.

WITH base AS (
  SELECT
    CAST(empl_id AS BIGINT) AS employee_id,
    cycle_number,
    cycle_name,
    last_modified_date,
    airflow_execution_date,
    COALESCE(last_modified_date, airflow_execution_date) AS availability_date
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
),
cycle_stats AS (
  SELECT
    cycle_number,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT employee_id) AS distinct_employees,
    COUNT(DISTINCT cycle_name) AS distinct_cycle_names,
    MIN(last_modified_date) AS min_last_modified_date,
    MAX(last_modified_date) AS max_last_modified_date,
    COUNT(DISTINCT last_modified_date) AS distinct_last_modified_dates,
    MIN(airflow_execution_date) AS min_airflow_execution_date,
    MAX(airflow_execution_date) AS max_airflow_execution_date,
    COUNT(DISTINCT airflow_execution_date) AS distinct_airflow_execution_dates,
    MIN(availability_date) AS min_availability_date,
    MAX(availability_date) AS max_availability_date
  FROM base
  GROUP BY 1
  HAVING COUNT(DISTINCT employee_id) >= 30
),
date_reuse AS (
  SELECT
    min_availability_date,
    COUNT(*) AS cycles_on_date
  FROM cycle_stats
  WHERE min_availability_date IS NOT NULL
    AND min_availability_date = max_availability_date
  GROUP BY 1
  HAVING COUNT(*) > 1
),
availability_ties AS (
  SELECT
    employee_id,
    availability_date,
    COUNT(DISTINCT cycle_number) AS cycles_on_date
  FROM base
  WHERE employee_id IS NOT NULL
    AND availability_date IS NOT NULL
  GROUP BY 1, 2
  HAVING COUNT(DISTINCT cycle_number) > 1
)
SELECT
  'Talent index' AS variable_name,
  COUNT(*) AS cycles_checked,
  COUNT(CASE WHEN distinct_cycle_names = 0 THEN 1 END)
    AS cycles_without_cycle_name,
  COUNT(CASE WHEN min_last_modified_date IS NULL THEN 1 END)
    AS cycles_without_last_modified_date,
  COUNT(CASE WHEN min_airflow_execution_date IS NULL THEN 1 END)
    AS cycles_without_airflow_execution_date,
  COUNT(CASE WHEN min_availability_date IS NULL THEN 1 END)
    AS cycles_without_any_technical_date,
  COUNT(CASE WHEN distinct_last_modified_dates > 1 THEN 1 END)
    AS cycles_with_multiple_last_modified_dates,
  COUNT(CASE WHEN distinct_airflow_execution_dates > 1 THEN 1 END)
    AS cycles_with_multiple_airflow_dates,
  COUNT(CASE
    WHEN min_last_modified_date IS NOT NULL
     AND min_airflow_execution_date IS NOT NULL
     AND (
       min_last_modified_date <> min_airflow_execution_date
       OR max_last_modified_date <> max_airflow_execution_date
     )
    THEN 1
  END) AS cycles_with_technical_date_disagreement,
  COALESCE((SELECT SUM(cycles_on_date) FROM date_reuse), 0)
    AS cycles_sharing_a_technical_date,
  COALESCE((SELECT COUNT(*) FROM availability_ties), 0)
    AS employee_availability_tie_groups,
  COALESCE((SELECT COUNT(DISTINCT employee_id) FROM availability_ties), 0)
    AS employees_with_availability_ties
FROM cycle_stats;
