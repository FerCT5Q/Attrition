-- Metadata-only inventory of employee-snapshot fields that could carry an
-- office/site/location identifier. This validates the available join keys
-- before assuming office_site is the only possible code.

SELECT
  column_name,
  data_type,
  ordinal_position,
  CASE
    WHEN LOWER(column_name) LIKE '%code%'
      OR LOWER(column_name) LIKE '%_id'
      OR LOWER(column_name) LIKE '%id_%'
    THEN 'potential_location_identifier'
    ELSE 'location_descriptor'
  END AS field_role
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND (
    LOWER(column_name) LIKE '%office%'
    OR LOWER(column_name) LIKE '%site%'
    OR LOWER(column_name) LIKE '%location%'
    OR LOWER(column_name) LIKE '%workplace%'
  )
ORDER BY ordinal_position;
