-- Aggregate discovery of the voluntary-attrition label needed for a
-- time-safe manager-proximity association test. No employee rows are output.
--
-- Population: terminated Employee / Regular records with a non-null term date.
-- Acceptance rule: identify a term_type label with at least 30 terminated
-- employees before using it as the voluntary outcome definition.

SELECT
  NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '') AS term_type,
  COUNT(DISTINCT employee_id) AS terminated_employees,
  MIN(CAST(term_date AS DATE)) AS first_term_date,
  MAX(CAST(term_date AS DATE)) AS latest_term_date
FROM hrda.post_hire_monthly_worker_dtls
WHERE worker_type = 'Employee'
  AND employee_type = 'Regular'
  AND term_date IS NOT NULL
GROUP BY 1
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY terminated_employees DESC;
