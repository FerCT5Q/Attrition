-- Propósito: identificar claves y campos comparables para una reconciliación
-- agregada entre aplicaciones, requisiciones y snapshots de empleados.
-- Modo de entrega: presentation; sólo metadatos.
SELECT
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN (
      'job_applications_vw', 'job_applications',
      'applications', 'applications_vw',
      'requisitions', 'requisitions_vw',
      'post_hire_monthly_worker_dtls', 'worker_details_latest',
      'worker_snapshot_vw'
  )
  AND (
      LOWER(column_name) IN (
          'req_id', 'requisition_id', 'job_requisition_id', 'job_code',
          'candidate_id', 'employee_id', 'compensation_grade',
          'compensation_grade_pa', 'compensation_grade_old',
          'requisition_compensation_grade_profile',
          'job_level_compensation', 'rf360_comp_grade',
          'compensation_grade_profile'
      )
      OR LOWER(column_name) LIKE '%requisition%'
      OR LOWER(column_name) LIKE '%job%code%'
  )
ORDER BY table_name, ordinal_position;
