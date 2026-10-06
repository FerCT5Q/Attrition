/*
  Pregunta añadida tras la auditoría inicial: cand_applied=1 contiene muchas
  filas sin employee_id. ¿Qué parte del feed puede enlazarse de manera segura
  a la población de empleados y a requisiciones deduplicables?

  Regla de interpretación: employee_id nulo no puede entrar a la feature. La
  consulta no asume que esas filas sean solicitudes internas ni que su ausencia
  demuestre un cero para la población de fuerza laboral.
*/
WITH applied_rows AS (
  SELECT
    employee_id,
    req_id,
    CAST(application_date AS DATE) AS application_date
  FROM hrda.applications
  WHERE cand_applied = 1
),
employee_linked_events AS (
  SELECT employee_id, req_id, application_date
  FROM applied_rows
  WHERE employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
  GROUP BY 1, 2, 3
)
SELECT
  COUNT(*) AS cand_applied_rows,
  SUM(CASE WHEN employee_id IS NOT NULL THEN 1 ELSE 0 END) AS employee_id_present_rows,
  SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END) AS employee_id_missing_rows,
  SUM(CASE WHEN employee_id IS NOT NULL AND req_id IS NOT NULL AND application_date IS NOT NULL THEN 1 ELSE 0 END) AS complete_employee_event_rows,
  (SELECT COUNT(*) FROM employee_linked_events) AS deduplicated_employee_event_rows,
  COUNT(DISTINCT CASE WHEN employee_id IS NOT NULL THEN employee_id END) AS distinct_linked_employees,
  MIN(CASE WHEN employee_id IS NOT NULL THEN application_date END) AS first_linked_event_date,
  MAX(CASE WHEN employee_id IS NOT NULL THEN application_date END) AS last_linked_event_date
FROM applied_rows;
