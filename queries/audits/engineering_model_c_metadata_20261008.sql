SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
 AND table_name IN ('post_hire_monthly_worker_dtls', 'workers_ios_transfers')
 AND column_name IN ('employee_id','fis_mo_end_dt','region','compa_ratio','compensation_grade',
 'acquisition','is_transferred','transfer_date','level_grouped','original_hire_date','service_date',
 'levelentrydate','prior_qc_work_years','worker_supervisory_organization_level_from_top',
 'work_arrangement','reg_non_intern_dir_reports','is_promo','promotion_date','manager_change',
 'manager_change_date','manager_employee_id','term_date','term_type','effective_date',
 'business_process_reason','worker_type','employee_type','active_status','is_rf360_yes_no','eng_or_noneng')
ORDER BY table_name, column_name
