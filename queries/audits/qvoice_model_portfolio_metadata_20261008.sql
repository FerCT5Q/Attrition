/* Preflight conjunto 2026-10-08; solo metadata, sin perfiles de empleados. presentation. */
SELECT table_schema, table_name, column_name, data_type, ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    table_name = 'qvoice_survey_data'
    OR (table_name = 'post_hire_monthly_worker_dtls' AND column_name IN (
      'employee_id', 'fis_mo_end_dt', 'worker_type', 'employee_type', 'active_status',
      'is_rf360_yes_no', 'eng_or_noneng', 'term_date', 'term_type', 'service_date',
      'original_hire_date', 'max_hire_rehire_date', 'rehire_date', 'level_grouped',
      'is_promo', 'promotion_date', 'manager_employee_id', 'manager_change',
      'manager_change_date', 'reg_non_intern_dir_reports', 'last_modified_date'
    ))
  )
ORDER BY table_name, ordinal_position;
