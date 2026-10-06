/*
  Cohorte descriptiva: participación QVoice proxy y attrition voluntaria.

  Claim
  -----
  Para cada wave QVoice, la población se fija en el último snapshot mensual
  anterior a la wave con worker_type='Employee', employee_type='Regular' y
  active_status=1. En ejecución, el workbook raw se procesa en memoria y
  aporta una clasificación mutuamente exclusiva: Responded, QVoice row / no
  answer o No QVoice row. Las llaves de empleado nunca se guardan ni se
  devuelven: se inyectan temporalmente en consultas agregadas por lotes.

  Outcome
  -------
  Mar-2023, Jan-2024 y Jan-2025: term_type estrictamente VOLUNTARY entre el
  inicio de la wave y los 12 meses posteriores. Jan-2026: salida voluntaria
  del 07 Jan 2026 al 23 Aug 2026; es YTD parcial y no se anualiza.

  Regla de aceptación
  -------------------
  Las tres categorías deben reconciliar al baseline, no traslaparse, conservar
  n >= 30 por categoría publicada y reconciliar exits / cohort. “No QVoice
  row” sigue siendo un proxy de cobertura, no una no-respuesta confirmada.
*/
WITH baseline AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = :baseline_snapshot
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
  GROUP BY 1
),
voluntary_events AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(term_date AS DATE) > :outcome_start
    AND CAST(term_date AS DATE) <= :outcome_end
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1
),
/* Runtime supplies Responded and QVoice-row-without-answer memberships in
   memory. The actual query omits that membership from persisted SQL. */
classified AS (
  SELECT
    b.employee_id,
    CASE
      WHEN b.employee_id IN (/* runtime Responded IDs */) THEN 'Responded'
      WHEN b.employee_id IN (/* runtime QVoice row / no answer IDs */) THEN 'QVoice row / no answer'
      ELSE 'No QVoice row'
    END AS participation_proxy,
    CASE WHEN e.employee_id IS NOT NULL THEN 1 ELSE 0 END AS voluntary_exit
  FROM baseline AS b
  LEFT JOIN voluntary_events AS e
    ON e.employee_id = b.employee_id
)
SELECT
  participation_proxy,
  COUNT(*) AS cohort_n,
  SUM(voluntary_exit) AS voluntary_exit_count,
  ROUND(100.0 * SUM(voluntary_exit) / NULLIF(COUNT(*), 0), 4) AS voluntary_attrition_rate_percent
FROM classified
GROUP BY 1
ORDER BY 1;
