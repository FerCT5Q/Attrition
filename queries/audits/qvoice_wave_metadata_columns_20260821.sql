SELECT
  'qvoice_date_metadata_column' AS section,
  column_name AS scope,
  data_type AS data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'qvoice_survey_data'
  AND (
    LOWER(column_name) LIKE '%survey%'
    OR LOWER(column_name) LIKE '%wave%'
    OR LOWER(column_name) LIKE '%year%'
    OR LOWER(column_name) LIKE '%date%'
  )
ORDER BY ordinal_position
