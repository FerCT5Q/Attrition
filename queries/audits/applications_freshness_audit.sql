SELECT
  COUNT(*) AS source_rows,
  COUNT(DISTINCT employee_id) AS linked_employees,
  COUNT(DISTINCT CASE
    WHEN cand_applied = 1 AND application_date IS NOT NULL THEN employee_id
  END) AS employees_with_applied_events,
  COUNT(DISTINCT CASE
    WHEN cand_applied = 1 AND application_date IS NOT NULL THEN req_id
  END) AS applied_requisitions,
  MIN(CASE
    WHEN cand_applied = 1 THEN application_date
  END) AS first_applied_event_date,
  MAX(CASE
    WHEN cand_applied = 1 THEN application_date
  END) AS last_applied_event_date
FROM hrda.applications
