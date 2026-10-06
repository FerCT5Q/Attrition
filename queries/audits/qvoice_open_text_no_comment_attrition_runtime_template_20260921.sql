/*
  Aggregate-only runtime join template for QVoice comment / no-comment attrition.

  The builder replaces <RUNTIME_SOURCE_JSON> in memory with participant/group
  membership from the workbook and never persists that payload. The resulting
  query returns only group-level counts; it does not return employee rows or
  identifiers.

  group_code is assigned by the caller:
    0 = request / concern commenter
    1 = all other open-text commenter
    2 = no comment submitted
*/
WITH source AS (
  SELECT
    elem.employee_id::BIGINT AS employee_id,
    elem.group_code::INTEGER AS group_code
  FROM (SELECT JSON_PARSE('<RUNTIME_SOURCE_JSON>') AS payload) AS src,
       src.payload AS elem
), baseline AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE '<BASELINE_SNAPSHOT>'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
  GROUP BY 1
), voluntary_events AS (
  SELECT employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND CAST(term_date AS DATE) > DATE '<OUTCOME_START>'
    AND CAST(term_date AS DATE) <= DATE '<OUTCOME_END>'
  GROUP BY 1
)
SELECT
  s.group_code,
  COUNT(*) AS source_participant_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_employee_count,
  SUM(CASE WHEN b.employee_id IS NULL THEN 1 ELSE 0 END) AS unmatched_employee_count,
  SUM(CASE WHEN b.employee_id IS NOT NULL AND e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_exit_count
FROM source AS s
LEFT JOIN baseline AS b ON b.employee_id = s.employee_id
LEFT JOIN voluntary_events AS e ON e.employee_id = b.employee_id
GROUP BY 1
ORDER BY 1;
