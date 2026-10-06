-- Metadata-only inventory of tables whose names suggest an office, site,
-- location, facility, geography, address, or workplace reference. It returns
-- table metadata only, so a table with generic columns (id/name/address) is
-- not missed merely because its column names lack the word "office".

SELECT
  table_schema,
  table_name,
  table_type
FROM information_schema.tables
WHERE table_schema = 'hrda'
  AND (
    LOWER(table_name) LIKE '%office%'
    OR LOWER(table_name) LIKE '%site%'
    OR LOWER(table_name) LIKE '%location%'
    OR LOWER(table_name) LIKE '%facility%'
    OR LOWER(table_name) LIKE '%workplace%'
    OR LOWER(table_name) LIKE '%geograph%'
    OR LOWER(table_name) LIKE '%address%'
  )
ORDER BY table_name;
