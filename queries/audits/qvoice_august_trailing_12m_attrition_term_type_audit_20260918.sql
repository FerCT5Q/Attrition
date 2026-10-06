/*
  Validación de la definición de salida voluntaria para el slide 18 de QVoice.

  Pregunta: ¿qué valores de term_type aparecen entre los cortes de agosto de
  2022 y 2026 para empleados regulares no-RF360?
  Motivo: confirmar que la etiqueta VOLUNTARY se usa de forma literal antes de
  calcular attrition anual retrospectivo.
  Grano: tipo de terminación agregado; no devuelve empleados.
  Regla de aceptación: VOLUNTARY debe existir con al menos 30 salidas y los
  eventos se deduplican por empleado-fecha-tipo antes de agrupar.
*/
WITH termination_events AS (
  SELECT DISTINCT
    employee_id,
    CAST(term_date AS DATE) AS term_date,
    UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) AS normalized_term_type
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND COALESCE(is_rf360_yes_no, 0) = 0
    AND term_date > DATE '2022-08-20'
    AND term_date <= DATE '2026-08-23'
    AND employee_id IS NOT NULL
)
SELECT
  COALESCE(normalized_term_type, 'NULL_OR_BLANK') AS normalized_term_type,
  COUNT(DISTINCT employee_id) AS distinct_employee_count,
  COUNT(*) AS distinct_employee_date_type_events
FROM termination_events
GROUP BY 1
ORDER BY distinct_employee_count DESC, normalized_term_type;
