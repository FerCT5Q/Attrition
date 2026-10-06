-- Metadata-only schema inspection of the two discovered coordinate tables.
-- Names alone do not establish whether coordinates represent office sites,
-- employee residences, survey locations, or another concept.

SELECT
  table_name,
  ordinal_position,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('esd_backup', 'exit_survey_data')
ORDER BY table_name, ordinal_position;
