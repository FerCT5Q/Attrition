/* Columnas de enlace y granularidad de tablas supporting recruiting. */
SELECT
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('pre_hire_flat_and_wide_summary_mvw', 'pipeline', 'applications', 'job_applications', 'offers')
  AND (
      column_name ILIKE '%candidate%'
      OR column_name ILIKE '%req%'
      OR column_name ILIKE '%requisition%'
      OR column_name ILIKE '%application%'
      OR column_name ILIKE '%job_post%'
      OR column_name ILIKE '%job_code%'
  )
ORDER BY table_name, ordinal_position;
