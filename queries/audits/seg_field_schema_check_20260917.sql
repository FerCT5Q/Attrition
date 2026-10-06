-- Purpose: metadata-only check for a field named `seg` in the employee
-- snapshot and the Critical Tech catalogue. No employee data is read.
-- Acceptance rule: a source is confirmed only when this query returns a row.

SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('post_hire_monthly_worker_dtls', 'critical_tech')
  AND LOWER(column_name) = 'seg'
ORDER BY table_name, ordinal_position;
