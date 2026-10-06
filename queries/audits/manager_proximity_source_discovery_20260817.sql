-- Metadata-only discovery for manager-proximity features.
-- Purpose: find governed office-site, time-zone, geographic-coordinate,
-- travel/commute and postal-code fields without reading employee values.
-- Privacy rule: a postal code can be used only after confirming that it
-- represents an office/site rather than a home address.

SELECT
  table_schema,
  table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    LOWER(column_name) LIKE '%office%'
    OR LOWER(column_name) LIKE '%site%'
    OR LOWER(column_name) LIKE '%location%'
    OR LOWER(column_name) LIKE '%postal%'
    OR LOWER(column_name) LIKE '%zip%'
    OR LOWER(column_name) LIKE '%latitude%'
    OR LOWER(column_name) LIKE '%longitude%'
    OR LOWER(column_name) LIKE '%geocode%'
    OR LOWER(column_name) LIKE '%time_zone%'
    OR LOWER(column_name) LIKE '%timezone%'
    OR LOWER(column_name) LIKE '%travel%'
    OR LOWER(column_name) LIKE '%commute%'
    OR LOWER(column_name) LIKE '%distance%'
  )
ORDER BY table_name, column_name;
