-- Preflight conjunto de metadata para las preparaciones del playbook V11.
-- No consulta filas ni agregados de empleados; modo presentation.
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    (table_name = 'post_hire_monthly_worker_dtls' AND column_name IN (
      'fis_mo_end_dt','employee_id','manager_employee_id','worker_type',
      'employee_type','active_status','is_rf360_yes_no','eng_or_noneng',
      'country','city','office_site','office_location','labor_market','postal_code',
      'work_arrangement','acquisition','compensation_grade','compensation_grade_old',
      'is_promo','promotion_date','is_demoted','demotion_date','time_in_role',
      'time_in_job_profile_start_date','date_entered_current_level',
      'max_hire_rehire_date','service_date','original_hire_date',
      'worker_supervisory_organization_level_from_top','job_title',
      'job_family','job_level_primary_position','region','term_date','term_type',
      'manager_change_date','manager_effective_date','manager_change'))
    OR (table_name = 'workers_ios_transfers' AND (
      column_name IN ('employee_id','effective_date','business_process_reason')
      OR column_name LIKE '%date%' OR column_name LIKE '%time%' OR column_name LIKE '%snapshot%'))
    OR (table_name IN ('annual_review_report','job_applications_vw') AND (
      column_name LIKE '%date%' OR column_name LIKE '%time%' OR column_name LIKE '%cycle%'
      OR column_name LIKE '%employee%' OR column_name LIKE '%applicant%'
      OR column_name LIKE '%candidate%' OR column_name LIKE '%talent%'
      OR column_name LIKE '%promotion%' OR column_name LIKE '%grade%'
      OR column_name LIKE '%fiscal%'))
  )
ORDER BY table_name, column_name
LIMIT 500;
