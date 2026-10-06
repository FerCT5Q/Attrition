-- Tablas candidatas para un catalogo o mapping de grades y niveles.
-- Se limita la salida a metadatos; no devuelve filas de empleados.
SELECT
    t.table_schema,
    t.table_name,
    t.table_type,
    c.column_name,
    c.data_type,
    c.ordinal_position
FROM information_schema.tables AS t
JOIN information_schema.columns AS c
  ON c.table_schema = t.table_schema
 AND c.table_name = t.table_name
WHERE t.table_schema = 'hrda'
  AND (
      LOWER(t.table_name) LIKE '%grade%'
      OR LOWER(t.table_name) LIKE '%compensation%'
      OR LOWER(t.table_name) LIKE '%level%'
      OR LOWER(t.table_name) IN ('annual_review_report', 'worker_details', 'worker_details_latest', 'worker_details_snapshot')
  )
  AND LOWER(c.column_name) IN (
      'compensation_grade',
      'compensation_grade_old',
      'compensation_grade_profile',
      'rf360_comp_grade',
      'grade',
      'grade_profile',
      'new_compensation_grade',
      'new_compensation_grade_profile',
      'job_level',
      'job_level_primary_position',
      'job_level_compensation',
      'management_level',
      'new_management_level',
      'level_grouped',
      'levelentrydate',
      'level_entry_date'
  )
ORDER BY 1, 2, c.ordinal_position;
