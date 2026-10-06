-- Metadata-only check: identify HRDA tables that contain both an office/site
-- field and a postal/ZIP field. No employee or location values are read.

WITH relevant_columns AS (
  SELECT
    table_name,
    column_name,
    data_type,
    CASE
      WHEN LOWER(column_name) LIKE '%office%'
        OR LOWER(column_name) LIKE '%site%'
      THEN 1 ELSE 0
    END AS is_site_column,
    CASE
      WHEN LOWER(column_name) LIKE '%postal%'
        OR LOWER(column_name) LIKE '%zip%'
      THEN 1 ELSE 0
    END AS is_postal_column
  FROM information_schema.columns
  WHERE table_schema = 'hrda'
),
candidate_tables AS (
  SELECT
    table_name,
    MAX(is_site_column) AS has_site_column,
    MAX(is_postal_column) AS has_postal_column
  FROM relevant_columns
  GROUP BY table_name
)
SELECT
  r.table_name,
  r.column_name,
  r.data_type,
  r.is_site_column,
  r.is_postal_column
FROM relevant_columns r
JOIN candidate_tables c
  ON c.table_name = r.table_name
WHERE c.has_site_column = 1
  AND c.has_postal_column = 1
  AND (r.is_site_column = 1 OR r.is_postal_column = 1)
ORDER BY r.table_name, r.is_site_column DESC, r.is_postal_column DESC, r.column_name;
