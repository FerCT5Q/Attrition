/*
  Pregunta: ¿La fuente contiene eventos utilizables y qué volumen de
  deduplicación o req_id nulo afecta al conteo de seis meses?

  Regla de aceptación para Source: las cinco columnas existen (preflight) y
  existe al menos un evento con employee_id, req_id y application_date para
  cand_applied=1. Esta consulta no aprueba la semántica de cand_applied ni la
  completitud del feed; esas condiciones se revisan por separado.
*/
WITH raw_events AS (
  SELECT
    employee_id,
    req_id,
    CAST(application_date AS DATE) AS application_date
  FROM hrda.applications
  WHERE cand_applied = 1
),
deduplicated_events AS (
  SELECT employee_id, req_id, application_date
  FROM raw_events
  WHERE employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
  GROUP BY 1, 2, 3
)
SELECT
  COUNT(*) AS raw_cand_applied_rows,
  SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END) AS null_employee_id_rows,
  SUM(CASE WHEN req_id IS NULL THEN 1 ELSE 0 END) AS null_req_id_rows,
  SUM(CASE WHEN application_date IS NULL THEN 1 ELSE 0 END) AS null_application_date_rows,
  (SELECT COUNT(*) FROM deduplicated_events) AS deduplicated_event_rows,
  COUNT(*) - (SELECT COUNT(*) FROM deduplicated_events) AS duplicate_or_incomplete_rows,
  MIN(application_date) AS first_application_date,
  MAX(application_date) AS last_application_date,
  COUNT(DISTINCT employee_id) AS distinct_employees_with_cand_applied
FROM raw_events;
