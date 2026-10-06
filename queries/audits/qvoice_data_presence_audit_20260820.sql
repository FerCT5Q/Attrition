WITH qvoice_summary AS (
  SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT emp_id) AS distinct_emp_ids,
    COUNT(DISTINCT CAST(survey_launch_date AS DATE)) AS survey_waves,
    MIN(CAST(survey_launch_date AS DATE)) AS min_survey_launch_date,
    MAX(CAST(survey_launch_date AS DATE)) AS max_survey_launch_date,
    COUNT(CASE WHEN emp_id IS NOT NULL THEN 1 END) AS rows_with_emp_id,
    COUNT(CASE WHEN survey_launch_date IS NOT NULL THEN 1 END) AS rows_with_survey_launch_date,
    COUNT(CASE WHEN intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm IS NOT NULL THEN 1 END) AS rows_with_intent_item_1,
    COUNT(CASE WHEN intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job IS NOT NULL THEN 1 END) AS rows_with_intent_item_2,
    COUNT(CASE WHEN growth_and_development_item_1_career_goals_can_be_met IS NOT NULL THEN 1 END) AS rows_with_career_goals_item
  FROM hrda.qvoice_survey_data
),
qvoice_waves AS (
  SELECT
    CAST(survey_launch_date AS DATE) AS survey_launch_date,
    COUNT(*) AS response_rows,
    COUNT(DISTINCT emp_id) AS distinct_emp_ids,
    COUNT(CASE WHEN intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm IS NOT NULL THEN 1 END) AS rows_with_intent_item_1,
    COUNT(CASE WHEN intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job IS NOT NULL THEN 1 END) AS rows_with_intent_item_2,
    COUNT(CASE WHEN growth_and_development_item_1_career_goals_can_be_met IS NOT NULL THEN 1 END) AS rows_with_career_goals_item
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date IS NOT NULL
  GROUP BY 1
)
SELECT
  'qvoice_summary' AS section,
  'hrda.qvoice_survey_data' AS scope,
  row_count AS metric_1,
  distinct_emp_ids AS metric_2,
  survey_waves AS metric_3,
  rows_with_emp_id AS metric_4,
  rows_with_survey_launch_date AS metric_5,
  min_survey_launch_date AS date_1,
  max_survey_launch_date AS date_2,
  'metric_1=row_count, metric_2=distinct_emp_ids, metric_3=survey_waves, metric_4=rows_with_emp_id, metric_5=rows_with_survey_launch_date' AS notes
FROM qvoice_summary
UNION ALL
SELECT
  'qvoice_structured_item_summary' AS section,
  'hrda.qvoice_survey_data' AS scope,
  rows_with_intent_item_1 AS metric_1,
  rows_with_intent_item_2 AS metric_2,
  rows_with_career_goals_item AS metric_3,
  NULL::BIGINT AS metric_4,
  NULL::BIGINT AS metric_5,
  NULL::DATE AS date_1,
  NULL::DATE AS date_2,
  'metric_1=rows_with_intent_item_1, metric_2=rows_with_intent_item_2, metric_3=rows_with_career_goals_item' AS notes
FROM qvoice_summary
UNION ALL
SELECT
  'qvoice_wave_summary' AS section,
  CAST(survey_launch_date AS VARCHAR(32)) AS scope,
  response_rows AS metric_1,
  distinct_emp_ids AS metric_2,
  rows_with_intent_item_1 AS metric_3,
  rows_with_intent_item_2 AS metric_4,
  rows_with_career_goals_item AS metric_5,
  survey_launch_date AS date_1,
  NULL::DATE AS date_2,
  'metric_1=response_rows, metric_2=distinct_emp_ids, metric_3=rows_with_intent_item_1, metric_4=rows_with_intent_item_2, metric_5=rows_with_career_goals_item' AS notes
FROM qvoice_waves
WHERE response_rows >= 30
ORDER BY section, scope
