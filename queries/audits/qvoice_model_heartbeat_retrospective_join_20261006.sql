/* Conciliación retrospectiva de Heartbeat 2026 con el playbook.
   Reproduce su lectura de eventos sin límite de snapshot de registro.
   Sólo explica diferencias; no alimenta el modelo ni sustituye el corte
   de conocimiento del experimento. Población y fecha de salida conservadas.
   SQL expandido y llaves se mantienen únicamente en memoria. */
/*
  Enlace descriptivo QVoice por concepto. Sólo agregados, presentation.
  El adaptador sustituye JSON de llaves/grupos EN MEMORIA. Nunca guarda el SQL
  expandido. La tabla source no es una tabla persistida de HRDA.
  Grupo = patrón de respuestas de un único concepto, sin texto libre.
  Regla: cada persona-wave participa una vez; workforce se deduplica, pero
  sus duplicados se contabilizan. La pertenencia al baseline NO acredita
  disponibilidad predictiva. La ventana anual comienza en el ancla histórica.
*/
WITH source AS (
  SELECT elem.k::BIGINT AS employee_id, elem.g::INTEGER AS group_code
  FROM (SELECT JSON_PARSE('__SOURCE_JSON__') AS payload) src,
       src.payload AS elem
), bounds AS (
  SELECT
    MAX(CASE WHEN CAST(fis_mo_end_dt AS DATE) < DATE '__BASELINE_BEFORE__'
             THEN CAST(fis_mo_end_dt AS DATE) END) AS baseline_snapshot,
    MAX(CASE WHEN CAST(fis_mo_end_dt AS DATE) <= DATE '__KNOWLEDGE_BOUNDARY__'
             THEN CAST(fis_mo_end_dt AS DATE) END) AS last_known_snapshot
  FROM hrda.post_hire_monthly_worker_dtls
), baseline AS (
  SELECT p.employee_id, COUNT(*) AS raw_rows,
    MAX(CASE WHEN p.is_rf360_yes_no = 0 AND TRIM(p.eng_or_noneng) = 'Engineering'
             THEN 1 ELSE 0 END) AS engineering
  FROM hrda.post_hire_monthly_worker_dtls p
  CROSS JOIN bounds d
  WHERE CAST(p.fis_mo_end_dt AS DATE) = d.baseline_snapshot
    AND p.worker_type = 'Employee' AND p.employee_type = 'Regular'
    AND p.active_status = 1 AND p.employee_id IS NOT NULL
  GROUP BY p.employee_id
), events AS (
  SELECT p.employee_id
  FROM hrda.post_hire_monthly_worker_dtls p
  CROSS JOIN bounds d
  WHERE p.worker_type = 'Employee' AND p.employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(p.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND CAST(p.term_date AS DATE) > DATE '__OUTCOME_START__'
    AND CAST(p.term_date AS DATE) <= LEAST(DATE '__OUTCOME_END__', d.last_known_snapshot)
  GROUP BY p.employee_id
), scopes AS (
  SELECT 'Engineering'::VARCHAR AS scope
  UNION ALL SELECT 'workforce'
), denominators AS (
  SELECT scope, COUNT(b.employee_id) AS eligible_count
  FROM scopes sc
  LEFT JOIN baseline b ON sc.scope = 'workforce' OR b.engineering = 1
  GROUP BY scope
)
SELECT sc.scope, s.group_code,
  MAX(d.baseline_snapshot) AS baseline_snapshot,
  MAX(LEAST(DATE '__OUTCOME_END__', d.last_known_snapshot)) AS outcome_end,
  MAX(n.eligible_count) AS eligible_count,
  COUNT(*) AS source_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL AND e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS event_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL AND b.raw_rows > 1 THEN 1 ELSE 0 END) AS multi_match_count
FROM source s
CROSS JOIN scopes sc
CROSS JOIN bounds d
INNER JOIN denominators n ON n.scope = sc.scope
LEFT JOIN baseline b ON b.employee_id = s.employee_id AND (sc.scope = 'workforce' OR b.engineering = 1)
LEFT JOIN events e ON e.employee_id = b.employee_id
GROUP BY sc.scope, s.group_code
ORDER BY sc.scope, s.group_code;
