/*
  QVoice binary association with subsequent attrition.

  Claim:
    Test whether the binary QVoice favorable signal is directionally associated
    with a later term_date, using a time-safe six-month follow-up.

  Population:
    QVoice 2026 respondents matched to the workforce snapshot on or before
    survey_launch_date. Primary population is active Employee at baseline.
    Sensitivity population is active Employee with employee_type='Regular'.

  Outcome:
    term_date > survey_launch_date and term_date <= the latest workforce
    snapshot on or before DATEADD(month, 6, survey_launch_date).

  Privacy:
    Employee IDs are used only inside joins and COUNT(DISTINCT ...). The
    result contains aggregate rates by item and binary value.
*/
WITH survey AS (
  SELECT DATE '2026-01-07' AS survey_date
),
snapshots AS (
  SELECT
    survey.survey_date,
    MAX(CASE WHEN workers.fis_mo_end_dt <= survey.survey_date THEN workers.fis_mo_end_dt END) AS baseline_snapshot,
    MAX(CASE WHEN workers.fis_mo_end_dt <= DATEADD(month, 6, survey.survey_date) THEN workers.fis_mo_end_dt END) AS cutoff_snapshot
  FROM survey
  CROSS JOIN hrda.post_hire_monthly_worker_dtls workers
  GROUP BY 1
),
qvoice_wave AS (
  SELECT
    emp_id,
    engagement_kpi_item_1_recommend_qualcomm_great_place_to_work,
    engagement_kpi_item_2_work_gives_sense_of_personal_accomplishment,
    engagement_kpi_item_3_qualcomm_motivates_above_and_beyond,
    intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm,
    intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job,
    workplace_connection_kpi_item_1_sense_of_belonging_at_qualcomm,
    workplace_connection_kpi_item_2_professional_growth_accessible_to_everyone,
    workplace_connection_kpi_item_3_comfortable_being_myself_at_work,
    wellbeing_kpi_item_1_feel_energized_when_working,
    wellbeing_kpi_item_2_empowered_to_improve_wellbeing,
    wellbeing_kpi_item_3_enough_energy_after_work,
    wellbeing_kpi_item_4_stress_in_job_is_manageable,
    confidence_kpi_item_1_confidence_in_future_of_qualcomm,
    confidence_kpi_item_2_qualcomm_making_changes_to_compete,
    collaboration_item_1_effective_collaboration_between_teams,
    collaboration_item_2_open_and_honest_communication,
    managing_change_item_1_communicates_reasons_behind_changes,
    resources_item_1_adequate_resources_for_health_and_wellbeing,
    culture_work_env_item_1_programs_to_connect_employees,
    culture_work_env_item_2_understand_company_values,
    culture_work_env_item_3_time_in_meetings_is_reasonable,
    culture_work_env_item_4_team_culture_enjoyable_work_environment,
    biz_function_leadership_item_1_communicates_strategy_and_objectives,
    biz_function_leadership_item_2_responds_to_employee_feedback,
    biz_function_leadership_item_3_link_between_work_and_objectives,
    qualcomm_senior_leadership_item_1_communicates_direction_for_company,
    qualcomm_senior_leadership_item_2_confidence_in_senior_leadership,
    total_rewards_item_1_understand_how_rewards_are_determined,
    work_processes_item_1_processes_allow_employees_to_be_productive,
    manager_effectiveness_item_1_timely_feedback_to_improve_performance,
    manager_effectiveness_item_2_meaningful_career_development_discussions,
    manager_effectiveness_item_3_manager_keeps_me_informed,
    manager_effectiveness_item_4_supports_work_life_balance,
    manager_effectiveness_item_5_considers_ideas_from_others,
    manager_effectiveness_item_6_manager_keeps_commitments,
    manager_effectiveness_item_7_helps_remove_barriers,
    manager_effectiveness_item_8_recognizes_people_for_good_work,
    team_dynamics_item_1_looks_for_ways_to_improve_productivity,
    team_dynamics_item_2_people_cooperate_to_get_job_done,
    team_dynamics_item_3_decisions_made_in_timely_manner,
    respect_item_1_treated_with_respect_at_work,
    ethics_item_1_freely_raise_ethical_concerns,
    survey_action_planning_item_1_positive_changes_from_previous_surveys,
    survey_action_planning_item_2_team_action_on_jan_qvoice_survey,
    growth_and_development_item_1_career_goals_can_be_met,
    growth_and_development_item_2_understand_what_it_takes_to_advance,
    growth_and_development_item_3_opportunities_to_learn_and_develop,
    growth_and_development_item_4_job_makes_good_use_of_skills,
    work_life_balance_item_1_able_to_balance_work_and_personal_life,
    innovation_item_1_encouraged_to_find_new_and_better_ways,
    innovation_item_2_can_challenge_traditional_ways,
    innovation_item_3_comfortable_voicing_ideas_and_opinions,
    recognition_item_1_receive_meaningful_recognition
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date = DATE '2026-01-07'
),
baseline_workforce AS (
  SELECT
    workers.employee_id,
    workers.worker_type,
    workers.employee_type,
    workers.active_status
  FROM hrda.post_hire_monthly_worker_dtls workers
  JOIN snapshots
    ON workers.fis_mo_end_dt = snapshots.baseline_snapshot
),
future_terminations AS (
  SELECT
    workers.employee_id
  FROM hrda.post_hire_monthly_worker_dtls workers
  JOIN snapshots
    ON workers.fis_mo_end_dt > snapshots.baseline_snapshot
   AND workers.fis_mo_end_dt <= snapshots.cutoff_snapshot
  WHERE workers.term_date > snapshots.survey_date
    AND workers.term_date <= DATEADD(month, 6, snapshots.survey_date)
  GROUP BY 1
),
base_population AS (
  SELECT
    qvoice_wave.emp_id,
    baseline_workforce.worker_type,
    baseline_workforce.employee_type,
    baseline_workforce.active_status,
    CASE WHEN future_terminations.employee_id IS NOT NULL THEN 1 ELSE 0 END AS attrition_flag
  FROM qvoice_wave
  JOIN baseline_workforce
    ON baseline_workforce.employee_id = qvoice_wave.emp_id
  LEFT JOIN future_terminations
    ON future_terminations.employee_id = qvoice_wave.emp_id
),
eligible_keys AS (
  SELECT
    emp_id,
    'employee_active' AS population,
    attrition_flag
  FROM base_population
  WHERE worker_type = 'Employee'
    AND active_status = 1
  UNION ALL
  SELECT
    emp_id,
    'employee_regular_active' AS population,
    attrition_flag
  FROM base_population
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
item_values AS (
  SELECT 'engagement_kpi_item_1_recommend_qualcomm_great_place_to_work' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.engagement_kpi_item_1_recommend_qualcomm_great_place_to_work AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.engagement_kpi_item_1_recommend_qualcomm_great_place_to_work IS NOT NULL  UNION ALL
  SELECT 'engagement_kpi_item_2_work_gives_sense_of_personal_accomplishment' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.engagement_kpi_item_2_work_gives_sense_of_personal_accomplishment AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.engagement_kpi_item_2_work_gives_sense_of_personal_accomplishment IS NOT NULL  UNION ALL
  SELECT 'engagement_kpi_item_3_qualcomm_motivates_above_and_beyond' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.engagement_kpi_item_3_qualcomm_motivates_above_and_beyond AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.engagement_kpi_item_3_qualcomm_motivates_above_and_beyond IS NOT NULL  UNION ALL
  SELECT 'intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm IS NOT NULL  UNION ALL
  SELECT 'intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job IS NOT NULL  UNION ALL
  SELECT 'workplace_connection_kpi_item_1_sense_of_belonging_at_qualcomm' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.workplace_connection_kpi_item_1_sense_of_belonging_at_qualcomm AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.workplace_connection_kpi_item_1_sense_of_belonging_at_qualcomm IS NOT NULL  UNION ALL
  SELECT 'workplace_connection_kpi_item_2_professional_growth_accessible_to_everyone' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.workplace_connection_kpi_item_2_professional_growth_accessible_to_everyone AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.workplace_connection_kpi_item_2_professional_growth_accessible_to_everyone IS NOT NULL  UNION ALL
  SELECT 'workplace_connection_kpi_item_3_comfortable_being_myself_at_work' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.workplace_connection_kpi_item_3_comfortable_being_myself_at_work AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.workplace_connection_kpi_item_3_comfortable_being_myself_at_work IS NOT NULL  UNION ALL
  SELECT 'wellbeing_kpi_item_1_feel_energized_when_working' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.wellbeing_kpi_item_1_feel_energized_when_working AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.wellbeing_kpi_item_1_feel_energized_when_working IS NOT NULL  UNION ALL
  SELECT 'wellbeing_kpi_item_2_empowered_to_improve_wellbeing' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.wellbeing_kpi_item_2_empowered_to_improve_wellbeing AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.wellbeing_kpi_item_2_empowered_to_improve_wellbeing IS NOT NULL  UNION ALL
  SELECT 'wellbeing_kpi_item_3_enough_energy_after_work' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.wellbeing_kpi_item_3_enough_energy_after_work AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.wellbeing_kpi_item_3_enough_energy_after_work IS NOT NULL  UNION ALL
  SELECT 'wellbeing_kpi_item_4_stress_in_job_is_manageable' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.wellbeing_kpi_item_4_stress_in_job_is_manageable AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.wellbeing_kpi_item_4_stress_in_job_is_manageable IS NOT NULL  UNION ALL
  SELECT 'confidence_kpi_item_1_confidence_in_future_of_qualcomm' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.confidence_kpi_item_1_confidence_in_future_of_qualcomm AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.confidence_kpi_item_1_confidence_in_future_of_qualcomm IS NOT NULL  UNION ALL
  SELECT 'confidence_kpi_item_2_qualcomm_making_changes_to_compete' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.confidence_kpi_item_2_qualcomm_making_changes_to_compete AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.confidence_kpi_item_2_qualcomm_making_changes_to_compete IS NOT NULL  UNION ALL
  SELECT 'collaboration_item_1_effective_collaboration_between_teams' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.collaboration_item_1_effective_collaboration_between_teams AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.collaboration_item_1_effective_collaboration_between_teams IS NOT NULL  UNION ALL
  SELECT 'collaboration_item_2_open_and_honest_communication' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.collaboration_item_2_open_and_honest_communication AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.collaboration_item_2_open_and_honest_communication IS NOT NULL  UNION ALL
  SELECT 'managing_change_item_1_communicates_reasons_behind_changes' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.managing_change_item_1_communicates_reasons_behind_changes AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.managing_change_item_1_communicates_reasons_behind_changes IS NOT NULL  UNION ALL
  SELECT 'resources_item_1_adequate_resources_for_health_and_wellbeing' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.resources_item_1_adequate_resources_for_health_and_wellbeing AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.resources_item_1_adequate_resources_for_health_and_wellbeing IS NOT NULL  UNION ALL
  SELECT 'culture_work_env_item_1_programs_to_connect_employees' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.culture_work_env_item_1_programs_to_connect_employees AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.culture_work_env_item_1_programs_to_connect_employees IS NOT NULL  UNION ALL
  SELECT 'culture_work_env_item_2_understand_company_values' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.culture_work_env_item_2_understand_company_values AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.culture_work_env_item_2_understand_company_values IS NOT NULL  UNION ALL
  SELECT 'culture_work_env_item_3_time_in_meetings_is_reasonable' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.culture_work_env_item_3_time_in_meetings_is_reasonable AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.culture_work_env_item_3_time_in_meetings_is_reasonable IS NOT NULL  UNION ALL
  SELECT 'culture_work_env_item_4_team_culture_enjoyable_work_environment' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.culture_work_env_item_4_team_culture_enjoyable_work_environment AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.culture_work_env_item_4_team_culture_enjoyable_work_environment IS NOT NULL  UNION ALL
  SELECT 'biz_function_leadership_item_1_communicates_strategy_and_objectives' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.biz_function_leadership_item_1_communicates_strategy_and_objectives AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.biz_function_leadership_item_1_communicates_strategy_and_objectives IS NOT NULL  UNION ALL
  SELECT 'biz_function_leadership_item_2_responds_to_employee_feedback' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.biz_function_leadership_item_2_responds_to_employee_feedback AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.biz_function_leadership_item_2_responds_to_employee_feedback IS NOT NULL  UNION ALL
  SELECT 'biz_function_leadership_item_3_link_between_work_and_objectives' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.biz_function_leadership_item_3_link_between_work_and_objectives AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.biz_function_leadership_item_3_link_between_work_and_objectives IS NOT NULL  UNION ALL
  SELECT 'qualcomm_senior_leadership_item_1_communicates_direction_for_company' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.qualcomm_senior_leadership_item_1_communicates_direction_for_company AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.qualcomm_senior_leadership_item_1_communicates_direction_for_company IS NOT NULL  UNION ALL
  SELECT 'qualcomm_senior_leadership_item_2_confidence_in_senior_leadership' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.qualcomm_senior_leadership_item_2_confidence_in_senior_leadership AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.qualcomm_senior_leadership_item_2_confidence_in_senior_leadership IS NOT NULL  UNION ALL
  SELECT 'total_rewards_item_1_understand_how_rewards_are_determined' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.total_rewards_item_1_understand_how_rewards_are_determined AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.total_rewards_item_1_understand_how_rewards_are_determined IS NOT NULL  UNION ALL
  SELECT 'work_processes_item_1_processes_allow_employees_to_be_productive' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.work_processes_item_1_processes_allow_employees_to_be_productive AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.work_processes_item_1_processes_allow_employees_to_be_productive IS NOT NULL  UNION ALL
  SELECT 'manager_effectiveness_item_1_timely_feedback_to_improve_performance' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.manager_effectiveness_item_1_timely_feedback_to_improve_performance AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.manager_effectiveness_item_1_timely_feedback_to_improve_performance IS NOT NULL  UNION ALL
  SELECT 'manager_effectiveness_item_2_meaningful_career_development_discussions' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.manager_effectiveness_item_2_meaningful_career_development_discussions AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.manager_effectiveness_item_2_meaningful_career_development_discussions IS NOT NULL  UNION ALL
  SELECT 'manager_effectiveness_item_3_manager_keeps_me_informed' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.manager_effectiveness_item_3_manager_keeps_me_informed AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.manager_effectiveness_item_3_manager_keeps_me_informed IS NOT NULL  UNION ALL
  SELECT 'manager_effectiveness_item_4_supports_work_life_balance' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.manager_effectiveness_item_4_supports_work_life_balance AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.manager_effectiveness_item_4_supports_work_life_balance IS NOT NULL  UNION ALL
  SELECT 'manager_effectiveness_item_5_considers_ideas_from_others' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.manager_effectiveness_item_5_considers_ideas_from_others AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.manager_effectiveness_item_5_considers_ideas_from_others IS NOT NULL  UNION ALL
  SELECT 'manager_effectiveness_item_6_manager_keeps_commitments' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.manager_effectiveness_item_6_manager_keeps_commitments AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.manager_effectiveness_item_6_manager_keeps_commitments IS NOT NULL  UNION ALL
  SELECT 'manager_effectiveness_item_7_helps_remove_barriers' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.manager_effectiveness_item_7_helps_remove_barriers AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.manager_effectiveness_item_7_helps_remove_barriers IS NOT NULL  UNION ALL
  SELECT 'manager_effectiveness_item_8_recognizes_people_for_good_work' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.manager_effectiveness_item_8_recognizes_people_for_good_work AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.manager_effectiveness_item_8_recognizes_people_for_good_work IS NOT NULL  UNION ALL
  SELECT 'team_dynamics_item_1_looks_for_ways_to_improve_productivity' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.team_dynamics_item_1_looks_for_ways_to_improve_productivity AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.team_dynamics_item_1_looks_for_ways_to_improve_productivity IS NOT NULL  UNION ALL
  SELECT 'team_dynamics_item_2_people_cooperate_to_get_job_done' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.team_dynamics_item_2_people_cooperate_to_get_job_done AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.team_dynamics_item_2_people_cooperate_to_get_job_done IS NOT NULL  UNION ALL
  SELECT 'team_dynamics_item_3_decisions_made_in_timely_manner' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.team_dynamics_item_3_decisions_made_in_timely_manner AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.team_dynamics_item_3_decisions_made_in_timely_manner IS NOT NULL  UNION ALL
  SELECT 'respect_item_1_treated_with_respect_at_work' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.respect_item_1_treated_with_respect_at_work AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.respect_item_1_treated_with_respect_at_work IS NOT NULL  UNION ALL
  SELECT 'ethics_item_1_freely_raise_ethical_concerns' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.ethics_item_1_freely_raise_ethical_concerns AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.ethics_item_1_freely_raise_ethical_concerns IS NOT NULL  UNION ALL
  SELECT 'survey_action_planning_item_1_positive_changes_from_previous_surveys' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.survey_action_planning_item_1_positive_changes_from_previous_surveys AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.survey_action_planning_item_1_positive_changes_from_previous_surveys IS NOT NULL  UNION ALL
  SELECT 'survey_action_planning_item_2_team_action_on_jan_qvoice_survey' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.survey_action_planning_item_2_team_action_on_jan_qvoice_survey AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.survey_action_planning_item_2_team_action_on_jan_qvoice_survey IS NOT NULL  UNION ALL
  SELECT 'growth_and_development_item_1_career_goals_can_be_met' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.growth_and_development_item_1_career_goals_can_be_met AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.growth_and_development_item_1_career_goals_can_be_met IS NOT NULL  UNION ALL
  SELECT 'growth_and_development_item_2_understand_what_it_takes_to_advance' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.growth_and_development_item_2_understand_what_it_takes_to_advance AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.growth_and_development_item_2_understand_what_it_takes_to_advance IS NOT NULL  UNION ALL
  SELECT 'growth_and_development_item_3_opportunities_to_learn_and_develop' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.growth_and_development_item_3_opportunities_to_learn_and_develop AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.growth_and_development_item_3_opportunities_to_learn_and_develop IS NOT NULL  UNION ALL
  SELECT 'growth_and_development_item_4_job_makes_good_use_of_skills' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.growth_and_development_item_4_job_makes_good_use_of_skills AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.growth_and_development_item_4_job_makes_good_use_of_skills IS NOT NULL  UNION ALL
  SELECT 'work_life_balance_item_1_able_to_balance_work_and_personal_life' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.work_life_balance_item_1_able_to_balance_work_and_personal_life AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.work_life_balance_item_1_able_to_balance_work_and_personal_life IS NOT NULL  UNION ALL
  SELECT 'innovation_item_1_encouraged_to_find_new_and_better_ways' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.innovation_item_1_encouraged_to_find_new_and_better_ways AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.innovation_item_1_encouraged_to_find_new_and_better_ways IS NOT NULL  UNION ALL
  SELECT 'innovation_item_2_can_challenge_traditional_ways' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.innovation_item_2_can_challenge_traditional_ways AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.innovation_item_2_can_challenge_traditional_ways IS NOT NULL  UNION ALL
  SELECT 'innovation_item_3_comfortable_voicing_ideas_and_opinions' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.innovation_item_3_comfortable_voicing_ideas_and_opinions AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.innovation_item_3_comfortable_voicing_ideas_and_opinions IS NOT NULL  UNION ALL
  SELECT 'recognition_item_1_receive_meaningful_recognition' AS item_name, eligible_keys.population, eligible_keys.emp_id, eligible_keys.attrition_flag, qvoice_wave.recognition_item_1_receive_meaningful_recognition AS binary_value
  FROM eligible_keys
  JOIN qvoice_wave
    ON qvoice_wave.emp_id = eligible_keys.emp_id
  WHERE qvoice_wave.recognition_item_1_receive_meaningful_recognition IS NOT NULL
),
item_counts AS (
  SELECT
    item_name,
    population,
    binary_value,
    COUNT(DISTINCT emp_id) AS respondent_count,
    COUNT(DISTINCT CASE WHEN attrition_flag = 1 THEN emp_id END) AS term_count
  FROM item_values
  GROUP BY 1, 2, 3
),
item_rates AS (
  SELECT
    item_name,
    population,
    MAX(CASE WHEN binary_value = 0 THEN respondent_count END) AS respondents_0,
    MAX(CASE WHEN binary_value = 0 THEN term_count END) AS terms_0,
    MAX(CASE WHEN binary_value = 1 THEN respondent_count END) AS respondents_1,
    MAX(CASE WHEN binary_value = 1 THEN term_count END) AS terms_1
  FROM item_counts
  GROUP BY 1, 2
),
population_summary AS (
  SELECT
    population,
    COUNT(DISTINCT emp_id) AS baseline_employee_count,
    COUNT(DISTINCT CASE WHEN attrition_flag = 1 THEN emp_id END) AS baseline_term_count
  FROM eligible_keys
  GROUP BY 1
)
SELECT
  'population_summary' AS section,
  population_summary.population,
  NULL::VARCHAR AS item_name,
  NULL::BIGINT AS respondents_0,
  NULL::BIGINT AS terms_0,
  NULL::DECIMAL(18, 6) AS attrition_rate_0_pct,
  NULL::BIGINT AS respondents_1,
  NULL::BIGINT AS terms_1,
  NULL::DECIMAL(18, 6) AS attrition_rate_1_pct,
  NULL::DECIMAL(18, 6) AS difference_0_minus_1_pp,
  population_summary.baseline_employee_count,
  population_summary.baseline_term_count,
  ROUND(100.0 * population_summary.baseline_term_count / NULLIF(population_summary.baseline_employee_count, 0), 4) AS baseline_attrition_rate_pct,
  snapshots.baseline_snapshot,
  snapshots.cutoff_snapshot,
  'Outcome uses term_date inside the six-month post-survey window.' AS notes
FROM population_summary
CROSS JOIN snapshots
UNION ALL
SELECT
  'item_association' AS section,
  item_rates.population,
  item_rates.item_name,
  item_rates.respondents_0,
  item_rates.terms_0,
  ROUND(100.0 * item_rates.terms_0 / NULLIF(item_rates.respondents_0, 0), 4) AS attrition_rate_0_pct,
  item_rates.respondents_1,
  item_rates.terms_1,
  ROUND(100.0 * item_rates.terms_1 / NULLIF(item_rates.respondents_1, 0), 4) AS attrition_rate_1_pct,
  ROUND(
    100.0 * (
      item_rates.terms_0::DECIMAL(18, 8) / NULLIF(item_rates.respondents_0, 0)
      - item_rates.terms_1::DECIMAL(18, 8) / NULLIF(item_rates.respondents_1, 0)
    ),
    4
  ) AS difference_0_minus_1_pp,
  population_summary.baseline_employee_count,
  population_summary.baseline_term_count,
  ROUND(100.0 * population_summary.baseline_term_count / NULLIF(population_summary.baseline_employee_count, 0), 4) AS baseline_attrition_rate_pct,
  snapshots.baseline_snapshot,
  snapshots.cutoff_snapshot,
  '0 is unfavorable and 1 is favorable according to the Excel mapping. Positive difference means higher attrition for 0.' AS notes
FROM item_rates
JOIN population_summary
  ON population_summary.population = item_rates.population
CROSS JOIN snapshots
WHERE item_rates.respondents_0 >= 30
  AND item_rates.respondents_1 >= 30
ORDER BY section, population, item_name;
