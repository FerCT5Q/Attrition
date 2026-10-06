-- Metadata-only inspection of the one candidate that contains an explicit
-- work-site code, name, city/state, and ZIP. This does not read assignments
-- or location values; it establishes whether the table has the keys and dates
-- needed before any aggregate reconciliation with regular employees.

SELECT
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'vndly_assignment'
ORDER BY ordinal_position;
