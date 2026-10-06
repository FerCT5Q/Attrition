-- Metadata-only discovery for possible alternative fields that explicitly
-- describe remote, hybrid, telework, workplace, or work arrangement.

SELECT
  table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    LOWER(column_name) LIKE '%remote%'
    OR LOWER(column_name) LIKE '%hybrid%'
    OR LOWER(column_name) LIKE '%telework%'
    OR LOWER(column_name) LIKE '%work_arrangement%'
    OR LOWER(column_name) LIKE '%workplace%'
  )
ORDER BY table_name, column_name;
