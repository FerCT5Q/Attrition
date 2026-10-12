/* Preflight de portfolio: sólo metadata; sin agregados de empleados. */
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    (table_name IN ('post_hire_monthly_worker_dtls', 'workers_ios_transfers')
      AND (column_name IN (
        'employee_id','fis_mo_end_dt','worker_type','employee_type','active_status',
        'is_rf360_yes_no','eng_or_noneng','manager_employee_id','original_hire_date',
        'service_date','level_grouped','levelentrydate','prior_qc_work_years',
        'reg_non_intern_dir_reports','worker_supervisory_organization_level_from_top',
        'work_arrangement','region','compa_ratio','compensation_grade','acquisition',
        'is_transferred','transfer_date','is_promo','promotion_date','manager_change',
        'manager_change_date','term_date','term_type','effective_date',
        'business_process_reason','job_family','job_family_short','job_family_group',
        'country','city','office_site','office_location','location_change',
        'location_change_date','job_family_change','job_family_change_date',
        'annual_base_pay','fte_annual_base_pay','fte_annual_base_pay_currency_code',
        'time_in_role','time_in_job_profile_start_date','job_code')
        OR LOWER(column_name) LIKE '%talent%'
        OR LOWER(column_name) LIKE '%time%zone%'))
    OR (LOWER(table_name) LIKE '%application%' AND column_name IN
        ('employee_id','candidate_id','application_date','applied_date',
         'application_created_date','created_date','effective_date','snapshot_date',
         'fis_mo_end_dt','is_internal','internal_candidate'))
    OR LOWER(table_name) LIKE '%draup%'
    OR LOWER(table_name) LIKE '%unemployment%'
    OR (LOWER(table_name) LIKE '%talent%' AND LOWER(column_name) LIKE '%index%')
  )
ORDER BY table_name, column_name;
