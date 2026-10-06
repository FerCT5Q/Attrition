WITH date_observations AS (
  SELECT
    'survey_launch_date' AS date_field,
    CAST(survey_launch_date AS DATE) AS observation_date,
    COUNT(*) AS response_rows,
    COUNT(DISTINCT emp_id) AS distinct_emp_ids
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date IS NOT NULL
  GROUP BY 1, 2
  UNION ALL
  SELECT
    'hierarchy_date' AS date_field,
    CAST(hierarchy_date AS DATE) AS observation_date,
    COUNT(*) AS response_rows,
    COUNT(DISTINCT emp_id) AS distinct_emp_ids
  FROM hrda.qvoice_survey_data
  WHERE hierarchy_date IS NOT NULL
  GROUP BY 1, 2
  UNION ALL
  SELECT
    'last_modified_date' AS date_field,
    CAST(last_modified_date AS DATE) AS observation_date,
    COUNT(*) AS response_rows,
    COUNT(DISTINCT emp_id) AS distinct_emp_ids
  FROM hrda.qvoice_survey_data
  WHERE last_modified_date IS NOT NULL
  GROUP BY 1, 2
  UNION ALL
  SELECT
    'airflow_execution_date' AS date_field,
    CAST(airflow_execution_date AS DATE) AS observation_date,
    COUNT(*) AS response_rows,
    COUNT(DISTINCT emp_id) AS distinct_emp_ids
  FROM hrda.qvoice_survey_data
  WHERE airflow_execution_date IS NOT NULL
  GROUP BY 1, 2
),
by_year AS (
  SELECT
    date_field,
    EXTRACT(year FROM observation_date)::INTEGER AS calendar_year,
    COUNT(DISTINCT observation_date) AS distinct_dates,
    SUM(response_rows) AS response_rows,
    SUM(distinct_emp_ids) AS distinct_emp_id_date_sum,
    MIN(observation_date) AS min_observation_date,
    MAX(observation_date) AS max_observation_date
  FROM date_observations
  GROUP BY 1, 2
)
SELECT
  date_field,
  calendar_year,
  distinct_dates,
  response_rows,
  distinct_emp_id_date_sum,
  min_observation_date,
  max_observation_date
FROM by_year
ORDER BY date_field, calendar_year
