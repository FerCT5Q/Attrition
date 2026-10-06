-- v4 source availability audit for the 43 historical attrition candidate variables.
-- Acceptance rule: every non-external required table/column pair must exist in information_schema.
WITH required AS (
  SELECT 'Applied to a job' AS variable_name, 'hrda' AS table_schema, 'applications' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'Applied to a job' AS variable_name, 'hrda' AS table_schema, 'applications' AS table_name, 'candidate_id' AS required_column
  UNION ALL
  SELECT 'Applied to a job' AS variable_name, 'hrda' AS table_schema, 'applications' AS table_name, 'cand_applied' AS required_column
  UNION ALL
  SELECT 'Applied to a job' AS variable_name, 'hrda' AS table_schema, 'applications' AS table_name, 'application_date' AS required_column
  UNION ALL
  SELECT 'Applied to a job' AS variable_name, 'hrda' AS table_schema, 'applications' AS table_name, 'req_id' AS required_column
  UNION ALL
  SELECT 'More than 3 job applications' AS variable_name, 'hrda' AS table_schema, 'applications' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'More than 3 job applications' AS variable_name, 'hrda' AS table_schema, 'applications' AS table_name, 'candidate_id' AS required_column
  UNION ALL
  SELECT 'More than 3 job applications' AS variable_name, 'hrda' AS table_schema, 'applications' AS table_name, 'cand_applied' AS required_column
  UNION ALL
  SELECT 'More than 3 job applications' AS variable_name, 'hrda' AS table_schema, 'applications' AS table_name, 'application_date' AS required_column
  UNION ALL
  SELECT 'More than 3 job applications' AS variable_name, 'hrda' AS table_schema, 'applications' AS table_name, 'req_id' AS required_column
  UNION ALL
  SELECT 'Transfer within past year' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'is_transferred' AS required_column
  UNION ALL
  SELECT 'Transfer within past year' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'transfer_date' AS required_column
  UNION ALL
  SELECT 'Location' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'country' AS required_column
  UNION ALL
  SELECT 'Location' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'office_site' AS required_column
  UNION ALL
  SELECT 'Within team compensation range' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'compa_ratio' AS required_column
  UNION ALL
  SELECT 'Within team compensation range' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'compensation_grade' AS required_column
  UNION ALL
  SELECT 'Within team compensation range' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_employee_id' AS required_column
  UNION ALL
  SELECT 'Team turnover' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_employee_id' AS required_column
  UNION ALL
  SELECT 'Team turnover' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'Team turnover' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'is_termed' AS required_column
  UNION ALL
  SELECT 'Team turnover' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'term_date' AS required_column
  UNION ALL
  SELECT 'Team turnover' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'term_type' AS required_column
  UNION ALL
  SELECT 'More than 1 employee leaves in a year' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_employee_id' AS required_column
  UNION ALL
  SELECT 'More than 1 employee leaves in a year' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'More than 1 employee leaves in a year' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'is_termed' AS required_column
  UNION ALL
  SELECT 'More than 1 employee leaves in a year' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'term_date' AS required_column
  UNION ALL
  SELECT 'More than 1 employee leaves in a year' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'term_type' AS required_column
  UNION ALL
  SELECT 'Job family' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'job_family' AS required_column
  UNION ALL
  SELECT 'Job family' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'job_family_group' AS required_column
  UNION ALL
  SELECT 'Region' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'region' AS required_column
  UNION ALL
  SELECT 'Gender' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'gender' AS required_column
  UNION ALL
  SELECT 'Remote / hybrid / in office status' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'work_arrangement' AS required_column
  UNION ALL
  SELECT 'Remote / hybrid / in office status' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'work_arrangement_start_date' AS required_column
  UNION ALL
  SELECT 'Remote / hybrid / in office status' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'work_arrangement_end_date' AS required_column
  UNION ALL
  SELECT 'Engineering vs. non-engineering' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'eng_or_noneng' AS required_column
  UNION ALL
  SELECT 'Rehire' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'is_rehire' AS required_column
  UNION ALL
  SELECT 'Rehire' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'rehire_date' AS required_column
  UNION ALL
  SELECT 'Years of experience prior to Qualcomm' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'prior_qc_work_years' AS required_column
  UNION ALL
  SELECT 'Non-respondents' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'emp_id' AS required_column
  UNION ALL
  SELECT 'Non-respondents' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'survey_launch_date' AS required_column
  UNION ALL
  SELECT 'Non-respondents' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'Non-respondents' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'fis_mo_end_dt' AS required_column
  UNION ALL
  SELECT 'Non-respondents' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'emp_id' AS required_column
  UNION ALL
  SELECT 'Non-respondents' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'survey_launch_date' AS required_column
  UNION ALL
  SELECT 'Non-respondents' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'Non-respondents' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'fis_mo_end_dt' AS required_column
  UNION ALL
  SELECT 'Intent to Stay items' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm' AS required_column
  UNION ALL
  SELECT 'Intent to Stay items' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job' AS required_column
  UNION ALL
  SELECT 'Intent to Stay items' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'emp_id' AS required_column
  UNION ALL
  SELECT 'Intent to Stay items' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'survey_launch_date' AS required_column
  UNION ALL
  SELECT 'Intent to Stay items' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm' AS required_column
  UNION ALL
  SELECT 'Intent to Stay items' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job' AS required_column
  UNION ALL
  SELECT 'Intent to Stay items' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'emp_id' AS required_column
  UNION ALL
  SELECT 'Intent to Stay items' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'survey_launch_date' AS required_column
  UNION ALL
  SELECT 'Career goals item' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'growth_and_development_item_1_career_goals_can_be_met' AS required_column
  UNION ALL
  SELECT 'Career goals item' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'emp_id' AS required_column
  UNION ALL
  SELECT 'Career goals item' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'survey_launch_date' AS required_column
  UNION ALL
  SELECT 'Career goals item' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'growth_and_development_item_1_career_goals_can_be_met' AS required_column
  UNION ALL
  SELECT 'Career goals item' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'emp_id' AS required_column
  UNION ALL
  SELECT 'Career goals item' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'survey_launch_date' AS required_column
  UNION ALL
  SELECT 'Average of all Qvoice items' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'emp_id' AS required_column
  UNION ALL
  SELECT 'Average of all Qvoice items' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'survey_launch_date' AS required_column
  UNION ALL
  SELECT 'Average of all Qvoice items' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'emp_id' AS required_column
  UNION ALL
  SELECT 'Average of all Qvoice items' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'survey_launch_date' AS required_column
  UNION ALL
  SELECT 'Standardized / normalized within region' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'emp_id' AS required_column
  UNION ALL
  SELECT 'Standardized / normalized within region' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'survey_launch_date' AS required_column
  UNION ALL
  SELECT 'Standardized / normalized within region' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'Standardized / normalized within region' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'region' AS required_column
  UNION ALL
  SELECT 'Standardized / normalized within region' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'fis_mo_end_dt' AS required_column
  UNION ALL
  SELECT 'Standardized / normalized within region' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'emp_id' AS required_column
  UNION ALL
  SELECT 'Standardized / normalized within region' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'survey_launch_date' AS required_column
  UNION ALL
  SELECT 'Standardized / normalized within region' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'Standardized / normalized within region' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'region' AS required_column
  UNION ALL
  SELECT 'Standardized / normalized within region' AS variable_name, 'hrda' AS table_schema, 'qvoice_survey_data' AS table_name, 'fis_mo_end_dt' AS required_column
  UNION ALL
  SELECT 'Position / time in level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'levelentrydate' AS required_column
  UNION ALL
  SELECT 'Position / time in level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'time_in_role' AS required_column
  UNION ALL
  SELECT 'Position / time in level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'time_in_job_profile_start_date' AS required_column
  UNION ALL
  SELECT 'Company tenure' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'original_hire_date' AS required_column
  UNION ALL
  SELECT 'Company tenure' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'max_hire_rehire_date' AS required_column
  UNION ALL
  SELECT 'Time since last promotion' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'is_promo' AS required_column
  UNION ALL
  SELECT 'Time since last promotion' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'promotion_date' AS required_column
  UNION ALL
  SELECT 'Promoted vs. hired into level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'levelentrydate' AS required_column
  UNION ALL
  SELECT 'Promoted vs. hired into level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'is_promo' AS required_column
  UNION ALL
  SELECT 'Promoted vs. hired into level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'promotion_date' AS required_column
  UNION ALL
  SELECT 'Promoted vs. hired into level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'original_hire_date' AS required_column
  UNION ALL
  SELECT 'Promoted vs. hired into level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'max_hire_rehire_date' AS required_column
  UNION ALL
  SELECT 'Level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'level_grouped' AS required_column
  UNION ALL
  SELECT 'Level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'job_level_primary_position' AS required_column
  UNION ALL
  SELECT 'Level' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'management_level' AS required_column
  UNION ALL
  SELECT 'Layers from CEO' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'worker_supervisory_organization_level_from_top' AS required_column
  UNION ALL
  SELECT 'Compensation grade' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'compensation_grade' AS required_column
  UNION ALL
  SELECT 'Comp ratio' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'compa_ratio' AS required_column
  UNION ALL
  SELECT 'Co-location with manager' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'Co-location with manager' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_employee_id' AS required_column
  UNION ALL
  SELECT 'Co-location with manager' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'office_site' AS required_column
  UNION ALL
  SELECT 'Co-location with manager' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'country' AS required_column
  UNION ALL
  SELECT 'High risk manager' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_employee_id' AS required_column
  UNION ALL
  SELECT 'High risk manager' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'High risk manager' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'is_termed' AS required_column
  UNION ALL
  SELECT 'High risk manager' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'term_date' AS required_column
  UNION ALL
  SELECT 'High risk manager' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'term_type' AS required_column
  UNION ALL
  SELECT 'High turnover under this person' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_employee_id' AS required_column
  UNION ALL
  SELECT 'High turnover under this person' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'High turnover under this person' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'is_termed' AS required_column
  UNION ALL
  SELECT 'High turnover under this person' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'term_date' AS required_column
  UNION ALL
  SELECT 'High turnover under this person' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'term_type' AS required_column
  UNION ALL
  SELECT 'Manager leaving' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_employee_id' AS required_column
  UNION ALL
  SELECT 'Manager leaving' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS required_column
  UNION ALL
  SELECT 'Manager leaving' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'is_termed' AS required_column
  UNION ALL
  SELECT 'Manager leaving' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'term_date' AS required_column
  UNION ALL
  SELECT 'Manager leaving' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'term_type' AS required_column
  UNION ALL
  SELECT 'Manager change' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_change' AS required_column
  UNION ALL
  SELECT 'Manager change' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_change_date' AS required_column
  UNION ALL
  SELECT 'Number of manager changes' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_change' AS required_column
  UNION ALL
  SELECT 'Number of manager changes' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_change_date' AS required_column
  UNION ALL
  SELECT 'Talent index' AS variable_name, 'hrda' AS table_schema, 'master_talent_index' AS table_name, 'empl_id' AS required_column
  UNION ALL
  SELECT 'Talent index' AS variable_name, 'hrda' AS table_schema, 'master_talent_index' AS table_name, 'talent_index' AS required_column
  UNION ALL
  SELECT 'Talent index' AS variable_name, 'hrda' AS table_schema, 'master_talent_index' AS table_name, 'perf' AS required_column
  UNION ALL
  SELECT 'Talent index' AS variable_name, 'hrda' AS table_schema, 'master_talent_index' AS table_name, 'stock' AS required_column
  UNION ALL
  SELECT 'Talent index' AS variable_name, 'hrda' AS table_schema, 'master_talent_index' AS table_name, 'bonus' AS required_column
  UNION ALL
  SELECT 'Talent index' AS variable_name, 'hrda' AS table_schema, 'master_talent_index' AS table_name, 'promo_index' AS required_column
  UNION ALL
  SELECT 'Talent index' AS variable_name, 'hrda' AS table_schema, 'master_talent_index' AS table_name, 'term_reason' AS required_column
  UNION ALL
  SELECT 'Talent index' AS variable_name, 'hrda' AS table_schema, 'master_talent_index' AS table_name, 'cycle_number' AS required_column
  UNION ALL
  SELECT 'Talent index' AS variable_name, 'hrda' AS table_schema, 'master_talent_index' AS table_name, 'last_modified_date' AS required_column
  UNION ALL
  SELECT 'Major inflection points' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_change' AS required_column
  UNION ALL
  SELECT 'Major inflection points' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'manager_change_date' AS required_column
  UNION ALL
  SELECT 'Major inflection points' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'cost_center_change' AS required_column
  UNION ALL
  SELECT 'Major inflection points' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'cost_center_change_date' AS required_column
  UNION ALL
  SELECT 'Major inflection points' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'job_family_change' AS required_column
  UNION ALL
  SELECT 'Major inflection points' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'job_family_change_date' AS required_column
  UNION ALL
  SELECT 'Major inflection points' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'location_change' AS required_column
  UNION ALL
  SELECT 'Major inflection points' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'location_change_date' AS required_column
  UNION ALL
  SELECT 'Major inflection points' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'is_transferred' AS required_column
  UNION ALL
  SELECT 'Major inflection points' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'transfer_date' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_1_leader' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_2_leader' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_3_leader' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_4_leader' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_5_leader' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_6_leader' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_7_leader' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_8_leader' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_9_leader' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_10_leader' AS required_column
  UNION ALL
  SELECT 'ET fields' AS variable_name, 'hrda' AS table_schema, 'post_hire_monthly_worker_dtls' AS table_name, 'et_11_leader' AS required_column
), checked AS (
  SELECT
    r.variable_name,
    r.table_schema,
    r.table_name,
    r.required_column,
    CASE WHEN t.table_name IS NOT NULL THEN 1 ELSE 0 END AS table_exists,
    CASE
      WHEN r.required_column IS NULL THEN CASE WHEN t.table_name IS NOT NULL THEN 1 ELSE 0 END
      WHEN c.column_name IS NOT NULL THEN 1
      ELSE 0
    END AS column_exists
  FROM required r
  LEFT JOIN information_schema.tables t
    ON t.table_schema = r.table_schema
   AND t.table_name = r.table_name
  LEFT JOIN information_schema.columns c
    ON c.table_schema = r.table_schema
   AND c.table_name = r.table_name
   AND c.column_name = r.required_column
)
SELECT
  variable_name,
  table_schema || '.' || table_name AS source_table,
  COUNT(*) AS required_items,
  SUM(table_exists) AS table_items_found,
  SUM(column_exists) AS column_items_found,
  SUM(CASE WHEN table_exists = 0 OR column_exists = 0 THEN 1 ELSE 0 END) AS missing_items
FROM checked
GROUP BY 1, 2
ORDER BY 1, 2;
