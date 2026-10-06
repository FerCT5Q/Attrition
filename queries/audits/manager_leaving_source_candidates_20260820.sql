SELECT
  table_schema,
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN (
    'post_hire_monthly_worker_dtls',
    'post_hire_monthly_worker_dtls_term',
    'all_terminations',
    'wd_term'
  )
  AND (
    column_name ILIKE '%employee%id%'
    OR column_name ILIKE '%manager%id%'
    OR column_name ILIKE '%term%'
    OR column_name ILIKE '%effective%date%'
    OR column_name IN (
      'active_status',
      'employee_type',
      'worker_type',
      'fis_mo_beg_dt',
      'fis_mo_end_dt',
      'max_hire_rehire_date',
      'is_rehire'
    )
  )
ORDER BY table_name, ordinal_position;
