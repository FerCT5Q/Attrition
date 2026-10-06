-- Claim: hrda.job_applications_vw exposes the fields required for the
-- descriptive annual and employee-snapshot application views.
-- Semantic type: source availability / direct field metadata.
-- Reporting mode: presentation; metadata only.
-- Acceptance rule: employee_id, req_id, application_date and cand_applied
-- must each be present exactly once in the requested view.
SELECT
  table_schema,
  table_name,
  COUNT(*) AS required_columns_found,
  SUM(CASE WHEN column_name = 'employee_id' THEN 1 ELSE 0 END) AS employee_id_columns,
  SUM(CASE WHEN column_name = 'req_id' THEN 1 ELSE 0 END) AS req_id_columns,
  SUM(CASE WHEN column_name = 'application_date' THEN 1 ELSE 0 END) AS application_date_columns,
  SUM(CASE WHEN column_name = 'cand_applied' THEN 1 ELSE 0 END) AS cand_applied_columns
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'job_applications_vw'
  AND column_name IN ('employee_id', 'req_id', 'application_date', 'cand_applied')
GROUP BY 1, 2;
