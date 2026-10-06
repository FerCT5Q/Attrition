SELECT
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('master_talent_index', 'qvoice_survey_data')
ORDER BY table_name, ordinal_position
