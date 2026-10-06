/*
  Claim: the rolling-August application-attrition calculation has the four
  application-event fields and two termination fields it requires.

  Semantic type: derived feature.
  Deliverable mode: internal_analysis; metadata only.
  Acceptance rule: each required column exists exactly once in its source.
*/
SELECT
  table_name,
  COUNT(*) AS required_columns_found,
  SUM(CASE WHEN column_name = 'employee_id' THEN 1 ELSE 0 END) AS employee_id_columns,
  SUM(CASE WHEN column_name = 'req_id' THEN 1 ELSE 0 END) AS req_id_columns,
  SUM(CASE WHEN column_name = 'application_date' THEN 1 ELSE 0 END) AS application_date_columns,
  SUM(CASE WHEN column_name = 'cand_applied' THEN 1 ELSE 0 END) AS cand_applied_columns,
  SUM(CASE WHEN column_name = 'term_date' THEN 1 ELSE 0 END) AS term_date_columns,
  SUM(CASE WHEN column_name = 'term_type' THEN 1 ELSE 0 END) AS term_type_columns
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    (table_name = 'job_applications_vw'
     AND column_name IN ('employee_id', 'req_id', 'application_date', 'cand_applied'))
    OR
    (table_name = 'post_hire_monthly_worker_dtls'
     AND column_name IN ('employee_id', 'term_date', 'term_type'))
  )
GROUP BY table_name
ORDER BY table_name;
