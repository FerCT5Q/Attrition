/*
  Tipo de objeto y columnas clave de las fuentes candidatas.
  Entregable: internal_analysis exploratorio.
  Sólo metadata.
*/
SELECT
    t.table_schema,
    t.table_name,
    t.table_type,
    COUNT(c.column_name) AS column_count,
    SUM(CASE WHEN c.column_name IN (
        'req_id', 'requisition_id', 'job_requisition_id',
        'job_requisition_status', 'job_req_status',
        'openings_available', 'number_of_openings_available',
        'openings_total', 'number_of_openings_total',
        'number_of_openings_filled', 'job_code',
        'job_requisition_filled_date', 'close_date', 'last_modified_date'
    ) THEN 1 ELSE 0 END) AS key_vacancy_column_count
FROM information_schema.tables t
LEFT JOIN information_schema.columns c
  ON c.table_schema = t.table_schema
 AND c.table_name = t.table_name
WHERE t.table_schema = 'hrda'
  AND t.table_name IN (
      'requisitions', 'requisitions_vw', 'requisitions_rescinds_archive',
      'vndly_requisition', 'pipeline', 'applications', 'job_applications',
      'pre_hire_flat_and_wide_summary_mvw', 'offers'
  )
GROUP BY 1, 2, 3
ORDER BY key_vacancy_column_count DESC, table_name;
