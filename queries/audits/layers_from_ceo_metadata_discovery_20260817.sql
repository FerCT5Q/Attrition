SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND (
    column_name IN (
      'employee_id',
      'manager_employee_id',
      'supervisor_emplid',
      'fis_mo_end_dt',
      'worker_supervisory_organization_level_from_top',
      'job_title',
      'business_title',
      'management_level',
      'worker_type',
      'employee_type',
      'active_status'
    )
    OR LOWER(column_name) LIKE '%ceo%'
    OR LOWER(column_name) LIKE '%chief_executive%'
    OR LOWER(column_name) LIKE '%supervisory_organization%'
  )
ORDER BY ordinal_position;
