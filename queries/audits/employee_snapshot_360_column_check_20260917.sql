-- Purpose: metadata-only discovery of any employee-snapshot column whose
-- name includes `360`. No employee rows or values are read.
-- Acceptance rule: a candidate field exists only when returned by
-- information_schema for hrda.post_hire_monthly_worker_dtls.

SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND LOWER(column_name) LIKE '%360%'
ORDER BY ordinal_position;
