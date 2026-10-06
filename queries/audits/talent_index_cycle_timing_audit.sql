-- Talent Index: auditoria agregada de fechas de ciclo y carga.
--
-- Claim:
--   Determinar si last_modified_date funciona como fecha historica de disponibilidad
--   del Talent Index o si representa principalmente una fecha comun de carga/refresh.
--
-- Population:
--   Todos los registros de hrda.master_talent_index con empl_id y cycle_number.
--
-- Grain:
--   Un agregado por cycle_number; no se publican IDs ni valores individuales.
--
-- Acceptance / interpretation rule stated before execution:
--   * Una fecha de conocimiento util requiere una relacion gobernada entre ciclo,
--     publicacion y disponibilidad antes del snapshot de prediccion.
--   * Si un ciclo completo comparte una sola fecha de modificacion/ejecucion, o varios
--     ciclos historicos comparten la misma fecha tardia, se tratara como indicio de
--     carga batch. En ese caso last_modified_date no prueba por si sola cuando el score
--     estuvo disponible originalmente y no puede habilitar historia time-safe.

SELECT
  cycle_number,
  COUNT(*) AS source_rows,
  COUNT(DISTINCT empl_id) AS distinct_employees,
  MIN(last_modified_date) AS min_last_modified_date,
  MAX(last_modified_date) AS max_last_modified_date,
  COUNT(DISTINCT last_modified_date) AS distinct_last_modified_dates,
  MIN(airflow_execution_date) AS min_airflow_execution_date,
  MAX(airflow_execution_date) AS max_airflow_execution_date,
  COUNT(DISTINCT airflow_execution_date) AS distinct_airflow_execution_dates,
  COUNT(CASE WHEN talent_index IS NOT NULL THEN 1 END) AS populated_talent_index_rows,
  COUNT(CASE
    WHEN NULLIF(TRIM(CAST(term_reason AS VARCHAR)), '') IS NOT NULL THEN 1
  END) AS populated_term_reason_rows
FROM hrda.master_talent_index
WHERE empl_id IS NOT NULL
  AND cycle_number IS NOT NULL
GROUP BY 1
HAVING COUNT(DISTINCT empl_id) >= 30
ORDER BY cycle_number;
