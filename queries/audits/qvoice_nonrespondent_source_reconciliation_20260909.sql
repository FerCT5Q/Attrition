/*
Claim: qvoice_survey_data can distinguish a respondent from a non-respondent
within its stored 2026 wave by using an emp_id row with all 53 survey items
NULL.
Mode: internal_analysis; aggregate-only; emp_id is used only inside counts.
Grain: one stored qvoice_survey_data row per emp_id and survey wave.
Acceptance rule: for each survey_launch_date, report row/emp_id uniqueness,
employees with at least one populated item, and employees with all 53 items
NULL. This is sufficient to describe stored no-item rows, but not to prove that
the table is an invitation roster unless the eligible/invited population is
also present or joined through an approved source.
*/
SELECT
    survey_launch_date,
    hierarchy_date,
    COUNT(*) AS stored_rows,
    COUNT(DISTINCT emp_id) AS distinct_emp_ids,
    COUNT(*) - COUNT(DISTINCT emp_id) AS duplicate_emp_id_rows,
    COUNT(DISTINCT CASE
        WHEN
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
        THEN emp_id
    END) AS employees_with_any_item,
    COUNT(DISTINCT CASE
        WHEN
            engagement_kpi_item_1_recommend_qualcomm_great_place_to_work IS NULL
            AND engagement_kpi_item_2_work_gives_sense_of_personal_accomplishment IS NULL
            AND engagement_kpi_item_3_qualcomm_motivates_above_and_beyond IS NULL
            AND intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm IS NULL
            AND intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job IS NULL
            AND workplace_connection_kpi_item_1_sense_of_belonging_at_qualcomm IS NULL
            AND workplace_connection_kpi_item_2_professional_growth_accessible_to_everyone IS NULL
            AND workplace_connection_kpi_item_3_comfortable_being_myself_at_work IS NULL
            AND wellbeing_kpi_item_1_feel_energized_when_working IS NULL
            AND wellbeing_kpi_item_2_empowered_to_improve_wellbeing IS NULL
            AND wellbeing_kpi_item_3_enough_energy_after_work IS NULL
            AND wellbeing_kpi_item_4_stress_in_job_is_manageable IS NULL
            AND confidence_kpi_item_1_confidence_in_future_of_qualcomm IS NULL
            AND confidence_kpi_item_2_qualcomm_making_changes_to_compete IS NULL
            AND collaboration_item_1_effective_collaboration_between_teams IS NULL
            AND collaboration_item_2_open_and_honest_communication IS NULL
            AND managing_change_item_1_communicates_reasons_behind_changes IS NULL
            AND resources_item_1_adequate_resources_for_health_and_wellbeing IS NULL
            AND culture_work_env_item_1_programs_to_connect_employees IS NULL
            AND culture_work_env_item_2_understand_company_values IS NULL
            AND culture_work_env_item_3_time_in_meetings_is_reasonable IS NULL
            AND culture_work_env_item_4_team_culture_enjoyable_work_environment IS NULL
            AND biz_function_leadership_item_1_communicates_strategy_and_objectives IS NULL
            AND biz_function_leadership_item_2_responds_to_employee_feedback IS NULL
            AND biz_function_leadership_item_3_link_between_work_and_objectives IS NULL
            AND qualcomm_senior_leadership_item_1_communicates_direction_for_company IS NULL
            AND qualcomm_senior_leadership_item_2_confidence_in_senior_leadership IS NULL
            AND total_rewards_item_1_understand_how_rewards_are_determined IS NULL
            AND work_processes_item_1_processes_allow_employees_to_be_productive IS NULL
            AND manager_effectiveness_item_1_timely_feedback_to_improve_performance IS NULL
            AND manager_effectiveness_item_2_meaningful_career_development_discussions IS NULL
            AND manager_effectiveness_item_3_manager_keeps_me_informed IS NULL
            AND manager_effectiveness_item_4_supports_work_life_balance IS NULL
            AND manager_effectiveness_item_5_considers_ideas_from_others IS NULL
            AND manager_effectiveness_item_6_manager_keeps_commitments IS NULL
            AND manager_effectiveness_item_7_helps_remove_barriers IS NULL
            AND manager_effectiveness_item_8_recognizes_people_for_good_work IS NULL
            AND team_dynamics_item_1_looks_for_ways_to_improve_productivity IS NULL
            AND team_dynamics_item_2_people_cooperate_to_get_job_done IS NULL
            AND team_dynamics_item_3_decisions_made_in_timely_manner IS NULL
            AND respect_item_1_treated_with_respect_at_work IS NULL
            AND ethics_item_1_freely_raise_ethical_concerns IS NULL
            AND survey_action_planning_item_1_positive_changes_from_previous_surveys IS NULL
            AND survey_action_planning_item_2_team_action_on_jan_qvoice_survey IS NULL
            AND growth_and_development_item_1_career_goals_can_be_met IS NULL
            AND growth_and_development_item_2_understand_what_it_takes_to_advance IS NULL
            AND growth_and_development_item_3_opportunities_to_learn_and_develop IS NULL
            AND growth_and_development_item_4_job_makes_good_use_of_skills IS NULL
            AND work_life_balance_item_1_able_to_balance_work_and_personal_life IS NULL
            AND innovation_item_1_encouraged_to_find_new_and_better_ways IS NULL
            AND innovation_item_2_can_challenge_traditional_ways IS NULL
            AND innovation_item_3_comfortable_voicing_ideas_and_opinions IS NULL
            AND recognition_item_1_receive_meaningful_recognition IS NULL
        THEN emp_id
    END) AS employees_with_all_items_null
FROM hrda.qvoice_survey_data
GROUP BY 1, 2
ORDER BY 1, 2;
