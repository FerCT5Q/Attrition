-- Propósito: localizar columnas para vincular requisiciones con empleados,
-- ciudad, grado y compensación; sólo metadatos.
-- Modo de entrega: presentation.
SELECT
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN (
      'requisitions', 'requisitions_vw',
      'post_hire_monthly_worker_dtls', 'worker_details_latest',
      'worker_snapshot_vw'
  )
  AND (
      LOWER(column_name) LIKE '%title%'
      OR LOWER(column_name) LIKE '%city%'
      OR LOWER(column_name) LIKE '%country%'
      OR LOWER(column_name) LIKE '%location%'
      OR LOWER(column_name) LIKE '%compensation%'
      OR LOWER(column_name) LIKE '%base%pay%'
      OR LOWER(column_name) LIKE '%currency%'
      OR LOWER(column_name) LIKE '%job%code%'
      OR LOWER(column_name) IN (
          'req_id', 'job_code', 'job_family', 'job_family_group',
          'employee_id', 'employee_type', 'worker_type', 'active_status',
          'last_modified_date', 'fis_mo_end_dt'
      )
  )
ORDER BY table_name, ordinal_position;
