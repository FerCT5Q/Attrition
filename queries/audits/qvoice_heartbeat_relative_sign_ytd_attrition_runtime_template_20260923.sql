/*
  Plantilla de join agregado para los segmentos +1, 0 y -1 de QVoice
  heartbeat. El builder inserta en memoria employee_id y group_code; esos
  identificadores nunca se devuelven ni se persisten en el artefacto.
*/
WITH source AS (
  SELECT
    elem.employee_id::BIGINT AS employee_id,
    elem.group_code::INTEGER AS group_code
  FROM (SELECT JSON_PARSE('{{SOURCE_JSON}}') AS payload) AS src,
       src.payload AS elem
),
baseline AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE '{{BASELINE_SNAPSHOT}}'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
  GROUP BY 1
),
voluntary_events AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND CAST(term_date AS DATE) > DATE '{{SURVEY_LAUNCH_DATE}}'
    AND CAST(term_date AS DATE) <= DATE '{{AUGUST_CUTOFF_DATE}}'
  GROUP BY 1
)
SELECT
  s.group_code,
  COUNT(*) AS source_employee_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_employee_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL AND e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count
FROM source AS s
LEFT JOIN baseline AS b
  ON b.employee_id = s.employee_id
LEFT JOIN voluntary_events AS e
  ON e.employee_id = b.employee_id
GROUP BY 1
ORDER BY 1;
