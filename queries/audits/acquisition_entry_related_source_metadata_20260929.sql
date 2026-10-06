-- Inventario metadata de fuentes relacionadas; no devuelve datos de empleados.
SELECT
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN (
      'post_hire_monthly_worker_dtls',
      'new_hires',
      'all_terminations',
      'worker_details_ms_snapshot'
  )
  AND (
      column_name IN (
          'employee_id', 'fis_mo_end_dt', 'fiscal_year', 'acquisition',
          'acquisition_org', 'acquisition_name', 'acquisition_yn',
          'hire_date', 'new_hire_date', 'hire_date_o_ea', 'max_hire_rehire_date',
          'term_date', 'term_type', 'worker_type', 'employee_type', 'active_status'
      )
      OR LOWER(column_name) LIKE '%acquisition%'
      OR LOWER(column_name) LIKE '%employee%'
      OR LOWER(column_name) LIKE '%emplid%'
      OR LOWER(column_name) LIKE '%person%'
      OR LOWER(column_name) LIKE '%worker%'
      OR LOWER(column_name) LIKE '%term%'
      OR LOWER(column_name) LIKE '%date%'
      OR LOWER(column_name) LIKE '%month%'
      OR LOWER(column_name) LIKE '%year%'
  )
ORDER BY table_name, ordinal_position;
