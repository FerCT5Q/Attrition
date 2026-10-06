-- Metadata-only search for a table that could bridge employee records to an
-- office/site/location code. It reports column names and table capabilities,
-- never employee or location values.

WITH candidate_location_columns AS (
  SELECT
    table_name,
    column_name,
    data_type
  FROM information_schema.columns
  WHERE table_schema = 'hrda'
    AND (
      LOWER(column_name) LIKE '%office%code%'
      OR LOWER(column_name) LIKE '%office%id%'
      OR LOWER(column_name) LIKE '%site%code%'
      OR LOWER(column_name) LIKE '%site%id%'
      OR LOWER(column_name) LIKE '%location%code%'
      OR LOWER(column_name) LIKE '%location%id%'
      OR LOWER(column_name) LIKE '%work_site%'
      OR LOWER(column_name) LIKE '%work_location%'
    )
),
table_capabilities AS (
  SELECT
    table_name,
    MAX(CASE
      WHEN LOWER(column_name) IN (
        'employee_id', 'worker_id', 'worker_system_id', 'employee_number',
        'person_id', 'worker_unique_id'
      ) THEN 1 ELSE 0
    END) AS has_employee_identifier,
    MAX(CASE
      WHEN LOWER(column_name) LIKE '%effective%'
        OR LOWER(column_name) LIKE '%snapshot%'
        OR LOWER(column_name) LIKE '%as_of%'
        OR LOWER(column_name) LIKE '%date%'
      THEN 1 ELSE 0
    END) AS has_date_or_effective_field
  FROM information_schema.columns
  WHERE table_schema = 'hrda'
  GROUP BY table_name
)
SELECT
  c.table_name,
  c.column_name AS location_identifier_column,
  c.data_type,
  t.has_employee_identifier,
  t.has_date_or_effective_field
FROM candidate_location_columns c
JOIN table_capabilities t
  ON c.table_name = t.table_name
ORDER BY c.table_name, c.column_name;
