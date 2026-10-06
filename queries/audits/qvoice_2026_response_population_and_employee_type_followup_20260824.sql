/*
  Focused follow-up after qvoice_2026_population_filter_diagnostic_20260824.sql.

  Purpose:
    1) Check whether the Redshift wave contains rows with no populated binary
       item at all.
    2) Show the aggregate employee_type composition of the QVoice keys at the
       launch-aligned workforce snapshot.

  Privacy:
    Employee IDs are used only inside COUNT(DISTINCT ...). Small workforce
    groups are suppressed from the employee_type breakdown.
*/
WITH snapshot_date AS (
  SELECT MAX(fis_mo_end_dt) AS fis_mo_end_dt
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt <= DATE '2026-01-07'
),
qvoice_keys AS (
  SELECT emp_id
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date = DATE '2026-01-07'
    AND emp_id IS NOT NULL
  GROUP BY 1
),
qvoice_workforce AS (
  SELECT
    qvoice_keys.emp_id,
    workers.worker_type,
    workers.employee_type,
    workers.active_status
  FROM qvoice_keys
  JOIN snapshot_date
    ON TRUE
  JOIN hrda.post_hire_monthly_worker_dtls workers
    ON workers.employee_id = qvoice_keys.emp_id
   AND workers.fis_mo_end_dt = snapshot_date.fis_mo_end_dt
)
SELECT
  'qvoice_response_population' AS section,
  '2026-01-07' AS scope,
  NULL::VARCHAR AS worker_type,
  NULL::VARCHAR AS employee_type,
  NULL::INTEGER AS active_status,
  COUNT(*)::BIGINT AS qvoice_rows,
  COUNT(DISTINCT emp_id)::BIGINT AS qvoice_distinct_emp_ids,
  COUNT(CASE WHEN emp_id IS NULL THEN 1 END)::BIGINT AS null_emp_id_rows,
  COUNT(CASE WHEN
    engagement_kpi_item_1_recommend_qualcomm_great_place_to_work IS NOT NULL
    OR engagement_kpi_item_2_work_gives_sense_of_personal_accomplishment IS NOT NULL
    OR engagement_kpi_item_3_qualcomm_motivates_above_and_beyond IS NOT NULL
    OR intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm IS NOT NULL
    OR intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job IS NOT NULL
    OR workplace_connection_kpi_item_1_sense_of_belonging_at_qualcomm IS NOT NULL
    OR workplace_connection_kpi_item_2_professional_growth_accessible_to_everyone IS NOT NULL
    OR workplace_connection_kpi_item_3_comfortable_being_myself_at_work IS NOT NULL
    OR wellbeing_kpi_item_1_feel_energized_when_working IS NOT NULL
    OR wellbeing_kpi_item_2_empowered_to_improve_wellbeing IS NOT NULL
    OR wellbeing_kpi_item_3_enough_energy_after_work IS NOT NULL
    OR wellbeing_kpi_item_4_stress_in_job_is_manageable IS NOT NULL
    OR confidence_kpi_item_1_confidence_in_future_of_qualcomm IS NOT NULL
    OR confidence_kpi_item_2_qualcomm_making_changes_to_compete IS NOT NULL
    OR collaboration_item_1_effective_collaboration_between_teams IS NOT NULL
    OR collaboration_item_2_open_and_honest_communication IS NOT NULL
    OR managing_change_item_1_communicates_reasons_behind_changes IS NOT NULL
    OR resources_item_1_adequate_resources_for_health_and_wellbeing IS NOT NULL
    OR culture_work_env_item_1_programs_to_connect_employees IS NOT NULL
    OR culture_work_env_item_2_understand_company_values IS NOT NULL
    OR culture_work_env_item_3_time_in_meetings_is_reasonable IS NOT NULL
    OR culture_work_env_item_4_team_culture_enjoyable_work_environment IS NOT NULL
    OR biz_function_leadership_item_1_communicates_strategy_and_objectives IS NOT NULL
    OR biz_function_leadership_item_2_responds_to_employee_feedback IS NOT NULL
    OR biz_function_leadership_item_3_link_between_work_and_objectives IS NOT NULL
    OR qualcomm_senior_leadership_item_1_communicates_direction_for_company IS NOT NULL
    OR qualcomm_senior_leadership_item_2_confidence_in_senior_leadership IS NOT NULL
    OR total_rewards_item_1_understand_how_rewards_are_determined IS NOT NULL
    OR work_processes_item_1_processes_allow_employees_to_be_productive IS NOT NULL
    OR manager_effectiveness_item_1_timely_feedback_to_improve_performance IS NOT NULL
    OR manager_effectiveness_item_2_meaningful_career_development_discussions IS NOT NULL
    OR manager_effectiveness_item_3_manager_keeps_me_informed IS NOT NULL
    OR manager_effectiveness_item_4_supports_work_life_balance IS NOT NULL
    OR manager_effectiveness_item_5_considers_ideas_from_others IS NOT NULL
    OR manager_effectiveness_item_6_manager_keeps_commitments IS NOT NULL
    OR manager_effectiveness_item_7_helps_remove_barriers IS NOT NULL
    OR manager_effectiveness_item_8_recognizes_people_for_good_work IS NOT NULL
    OR team_dynamics_item_1_looks_for_ways_to_improve_productivity IS NOT NULL
    OR team_dynamics_item_2_people_cooperate_to_get_job_done IS NOT NULL
    OR team_dynamics_item_3_decisions_made_in_timely_manner IS NOT NULL
    OR respect_item_1_treated_with_respect_at_work IS NOT NULL
    OR ethics_item_1_freely_raise_ethical_concerns IS NOT NULL
    OR survey_action_planning_item_1_positive_changes_from_previous_surveys IS NOT NULL
    OR survey_action_planning_item_2_team_action_on_jan_qvoice_survey IS NOT NULL
    OR growth_and_development_item_1_career_goals_can_be_met IS NOT NULL
    OR growth_and_development_item_2_understand_what_it_takes_to_advance IS NOT NULL
    OR growth_and_development_item_3_opportunities_to_learn_and_develop IS NOT NULL
    OR growth_and_development_item_4_job_makes_good_use_of_skills IS NOT NULL
    OR work_life_balance_item_1_able_to_balance_work_and_personal_life IS NOT NULL
    OR innovation_item_1_encouraged_to_find_new_and_better_ways IS NOT NULL
    OR innovation_item_2_can_challenge_traditional_ways IS NOT NULL
    OR innovation_item_3_comfortable_voicing_ideas_and_opinions IS NOT NULL
    OR recognition_item_1_receive_meaningful_recognition IS NOT NULL
  THEN 1 END)::BIGINT AS rows_with_any_binary_item,
  COUNT(CASE WHEN NOT (
    engagement_kpi_item_1_recommend_qualcomm_great_place_to_work IS NOT NULL
    OR engagement_kpi_item_2_work_gives_sense_of_personal_accomplishment IS NOT NULL
    OR engagement_kpi_item_3_qualcomm_motivates_above_and_beyond IS NOT NULL
    OR intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm IS NOT NULL
    OR intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job IS NOT NULL
    OR workplace_connection_kpi_item_1_sense_of_belonging_at_qualcomm IS NOT NULL
    OR workplace_connection_kpi_item_2_professional_growth_accessible_to_everyone IS NOT NULL
    OR workplace_connection_kpi_item_3_comfortable_being_myself_at_work IS NOT NULL
    OR wellbeing_kpi_item_1_feel_energized_when_working IS NOT NULL
    OR wellbeing_kpi_item_2_empowered_to_improve_wellbeing IS NOT NULL
    OR wellbeing_kpi_item_3_enough_energy_after_work IS NOT NULL
    OR wellbeing_kpi_item_4_stress_in_job_is_manageable IS NOT NULL
    OR confidence_kpi_item_1_confidence_in_future_of_qualcomm IS NOT NULL
    OR confidence_kpi_item_2_qualcomm_making_changes_to_compete IS NOT NULL
    OR collaboration_item_1_effective_collaboration_between_teams IS NOT NULL
    OR collaboration_item_2_open_and_honest_communication IS NOT NULL
    OR managing_change_item_1_communicates_reasons_behind_changes IS NOT NULL
    OR resources_item_1_adequate_resources_for_health_and_wellbeing IS NOT NULL
    OR culture_work_env_item_1_programs_to_connect_employees IS NOT NULL
    OR culture_work_env_item_2_understand_company_values IS NOT NULL
    OR culture_work_env_item_3_time_in_meetings_is_reasonable IS NOT NULL
    OR culture_work_env_item_4_team_culture_enjoyable_work_environment IS NOT NULL
    OR biz_function_leadership_item_1_communicates_strategy_and_objectives IS NOT NULL
    OR biz_function_leadership_item_2_responds_to_employee_feedback IS NOT NULL
    OR biz_function_leadership_item_3_link_between_work_and_objectives IS NOT NULL
    OR qualcomm_senior_leadership_item_1_communicates_direction_for_company IS NOT NULL
    OR qualcomm_senior_leadership_item_2_confidence_in_senior_leadership IS NOT NULL
    OR total_rewards_item_1_understand_how_rewards_are_determined IS NOT NULL
    OR work_processes_item_1_processes_allow_employees_to_be_productive IS NOT NULL
    OR manager_effectiveness_item_1_timely_feedback_to_improve_performance IS NOT NULL
    OR manager_effectiveness_item_2_meaningful_career_development_discussions IS NOT NULL
    OR manager_effectiveness_item_3_manager_keeps_me_informed IS NOT NULL
    OR manager_effectiveness_item_4_supports_work_life_balance IS NOT NULL
    OR manager_effectiveness_item_5_considers_ideas_from_others IS NOT NULL
    OR manager_effectiveness_item_6_manager_keeps_commitments IS NOT NULL
    OR manager_effectiveness_item_7_helps_remove_barriers IS NOT NULL
    OR manager_effectiveness_item_8_recognizes_people_for_good_work IS NOT NULL
    OR team_dynamics_item_1_looks_for_ways_to_improve_productivity IS NOT NULL
    OR team_dynamics_item_2_people_cooperate_to_get_job_done IS NOT NULL
    OR team_dynamics_item_3_decisions_made_in_timely_manner IS NOT NULL
    OR respect_item_1_treated_with_respect_at_work IS NOT NULL
    OR ethics_item_1_freely_raise_ethical_concerns IS NOT NULL
    OR survey_action_planning_item_1_positive_changes_from_previous_surveys IS NOT NULL
    OR survey_action_planning_item_2_team_action_on_jan_qvoice_survey IS NOT NULL
    OR growth_and_development_item_1_career_goals_can_be_met IS NOT NULL
    OR growth_and_development_item_2_understand_what_it_takes_to_advance IS NOT NULL
    OR growth_and_development_item_3_opportunities_to_learn_and_develop IS NOT NULL
    OR growth_and_development_item_4_job_makes_good_use_of_skills IS NOT NULL
    OR work_life_balance_item_1_able_to_balance_work_and_personal_life IS NOT NULL
    OR innovation_item_1_encouraged_to_find_new_and_better_ways IS NOT NULL
    OR innovation_item_2_can_challenge_traditional_ways IS NOT NULL
    OR innovation_item_3_comfortable_voicing_ideas_and_opinions IS NOT NULL
    OR recognition_item_1_receive_meaningful_recognition IS NOT NULL
  ) THEN 1 END)::BIGINT AS rows_without_any_binary_item,
  'The table has no explicit valid or eligible survey flag, this checks observable item population instead.' AS notes
FROM hrda.qvoice_survey_data
WHERE survey_launch_date = DATE '2026-01-07'

UNION ALL

SELECT
  'employee_type_breakdown' AS section,
  'launch_aligned_2025-12-28' AS scope,
  COALESCE(worker_type, '<NULL>') AS worker_type,
  COALESCE(employee_type, '<NULL>') AS employee_type,
  active_status,
  NULL::BIGINT AS qvoice_rows,
  COUNT(DISTINCT emp_id)::BIGINT AS qvoice_distinct_emp_ids,
  NULL::BIGINT AS null_emp_id_rows,
  NULL::BIGINT AS rows_with_any_binary_item,
  NULL::BIGINT AS rows_without_any_binary_item,
  'Groups below 30 employee keys are omitted for privacy.' AS notes
FROM qvoice_workforce
GROUP BY 1, 2, 3, 4, 5
HAVING COUNT(DISTINCT emp_id) >= 30
ORDER BY employee_type, worker_type, active_status;
