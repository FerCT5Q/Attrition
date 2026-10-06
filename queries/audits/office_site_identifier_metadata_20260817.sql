-- Metadata-only discovery of candidate office/site/location identifiers and
-- reference tables in HRDA. It returns no workforce or location values.

SELECT
  table_schema,
  table_name,
  column_name,
  data_type,
  ordinal_position,
  CASE
    WHEN LOWER(column_name) LIKE '%zip%'
      OR LOWER(column_name) LIKE '%postal%'
    THEN 'candidate_postal_attribute'
    WHEN LOWER(column_name) LIKE '%latitude%'
      OR LOWER(column_name) LIKE '%longitude%'
      OR LOWER(column_name) LIKE '%timezone%'
    THEN 'candidate_geography_attribute'
    ELSE 'candidate_identifier_or_work_site'
  END AS candidate_role
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    LOWER(column_name) LIKE '%office%id%'
    OR LOWER(column_name) LIKE '%office%code%'
    OR LOWER(column_name) LIKE '%site%id%'
    OR LOWER(column_name) LIKE '%site%code%'
    OR LOWER(column_name) LIKE '%location%id%'
    OR LOWER(column_name) LIKE '%location%code%'
    OR LOWER(column_name) LIKE '%work_site%'
    OR LOWER(column_name) LIKE '%work_location%'
    OR (
      (LOWER(column_name) LIKE '%zip%' OR LOWER(column_name) LIKE '%postal%'
        OR LOWER(column_name) LIKE '%latitude%' OR LOWER(column_name) LIKE '%longitude%'
        OR LOWER(column_name) LIKE '%timezone%')
      AND (LOWER(table_name) LIKE '%office%' OR LOWER(table_name) LIKE '%site%'
        OR LOWER(table_name) LIKE '%location%' OR LOWER(table_name) LIKE '%facility%'
        OR LOWER(table_name) LIKE '%vndly%')
    )
  )
ORDER BY
  table_name,
  table_name,
  ordinal_position;
