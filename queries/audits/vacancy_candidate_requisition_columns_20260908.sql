/*
  Inspección dirigida de columnas relevantes en fuentes de recruiting.
  Entregable: internal_analysis exploratorio.
  Sólo metadata; no lee filas de empleados.
*/
SELECT
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN (
      'requisitions',
      'requisitions_vw',
      'requisitions_rescinds_archive',
      'pipeline',
      'applications',
      'job_applications',
      'vndly_requisition',
      'offers',
      'pre_hire_flat_and_wide_summary_mvw'
  )
  AND (
      column_name ILIKE '%req%'
      OR column_name ILIKE '%vacan%'
      OR column_name ILIKE '%open%'
      OR column_name ILIKE '%posit%'
      OR column_name ILIKE '%post%'
      OR column_name ILIKE '%job%'
      OR column_name ILIKE '%status%'
      OR column_name ILIKE '%state%'
      OR column_name ILIKE '%date%'
      OR column_name ILIKE '%title%'
      OR column_name ILIKE '%location%'
      OR column_name ILIKE '%headcount%'
      OR column_name ILIKE '%worker%'
  )
ORDER BY table_name, ordinal_position;
