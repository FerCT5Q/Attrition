-- Claim: identify current HRDA metadata candidates that may contain internal-job
-- application information or fields needed to link an application event to a worker.
-- Semantic type: metadata preflight for the derived feature "Applied to a job".
-- Reporting mode: presentation (metadata only; no employee-level data).
-- Acceptance rule: list all matching HRDA tables/columns. A match is only a
-- discovery lead; it does not establish that a table is a valid replacement for
-- hrda.applications or that its events are current, complete, or time-safe.
SELECT
  table_schema,
  table_name,
  COUNT(*) AS matching_metadata_columns,
  MAX(CASE WHEN column_name = 'employee_id' THEN 1 ELSE 0 END) AS has_employee_id,
  MAX(CASE WHEN column_name = 'cand_applied' THEN 1 ELSE 0 END) AS has_cand_applied,
  MAX(CASE WHEN column_name = 'application_date' THEN 1 ELSE 0 END) AS has_application_date,
  MAX(CASE WHEN column_name = 'req_id' THEN 1 ELSE 0 END) AS has_req_id
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    LOWER(table_name) LIKE '%applic%'
    OR LOWER(table_name) LIKE '%recruit%'
    OR LOWER(column_name) LIKE '%applic%'
    OR LOWER(column_name) LIKE '%recruit%'
    OR LOWER(column_name) IN ('candidate_id', 'req_id', 'cand_applied', 'application_date')
  )
GROUP BY table_schema, table_name
ORDER BY table_name;
