SELECT
  table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    (
      table_name = 'post_hire_monthly_worker_dtls'
      AND column_name IN (
        'employee_id', 'fis_mo_end_dt', 'fiscal_year',
        'worker_type', 'employee_type', 'active_status',
        'is_transferred', 'transfer_date', 'country', 'office_site',
        'compa_ratio', 'compensation_grade', 'manager_employee_id',
        'is_termed', 'term_date', 'term_type',
        'job_family', 'job_family_group', 'region', 'gender',
        'work_arrangement', 'work_arrangement_start_date',
        'work_arrangement_end_date', 'eng_or_noneng',
        'is_rehire', 'rehire_date', 'prior_qc_work_years',
        'levelentrydate', 'time_in_role',
        'time_in_job_profile_start_date', 'original_hire_date',
        'max_hire_rehire_date', 'is_promo', 'promotion_date',
        'level_grouped', 'job_level_primary_position', 'management_level',
        'worker_supervisory_organization_level_from_top',
        'manager_change', 'manager_change_date',
        'cost_center_change', 'cost_center_change_date',
        'job_family_change', 'job_family_change_date',
        'location_change', 'location_change_date',
        'homeaddresswithcountry', 'postal_code',
        'et_1_leader', 'et_2_leader', 'et_3_leader',
        'et_4_leader', 'et_5_leader', 'et_6_leader',
        'et_7_leader', 'et_8_leader', 'et_9_leader',
        'et_10_leader', 'et_11_leader'
      )
    )
    OR (
      table_name = 'applications'
      AND column_name IN (
        'employee_id', 'candidate_id', 'cand_applied',
        'application_date', 'req_id'
      )
    )
    OR (
      table_name = 'qvoice_survey_data'
      AND (
        column_name IN ('emp_id', 'survey_launch_date')
        OR column_name LIKE 'intent_to_stay_kpi_item_%'
        OR column_name = 'growth_and_development_item_1_career_goals_can_be_met'
      )
    )
    OR (
      table_name = 'master_talent_index'
      AND column_name IN (
        'employee_id', 'talent_index', 'perf', 'stock', 'bonus',
        'promo_index', 'term_reason', 'cycle_number', 'last_modified_date'
      )
    )
  )
ORDER BY table_name, column_name
