WITH survey_dates AS (
  SELECT CAST(survey_launch_date AS DATE) AS survey_date
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date IS NOT NULL
  GROUP BY survey_launch_date
),
snapshot_match AS (
  SELECT survey_dates.survey_date, MAX(workers.fis_mo_end_dt) AS snapshot_date
  FROM survey_dates
  JOIN hrda.post_hire_monthly_worker_dtls workers
    ON workers.fis_mo_end_dt <= survey_dates.survey_date
  GROUP BY survey_dates.survey_date
),
eligible AS (
  SELECT
    snapshot_match.survey_date,
    CAST(MAX(workers.fiscal_year) AS VARCHAR(32)) AS fiscal_year,
    workers.employee_id
  FROM snapshot_match
  JOIN hrda.post_hire_monthly_worker_dtls workers
    ON workers.fis_mo_end_dt = snapshot_match.snapshot_date
   AND workers.worker_type = 'Employee'
   AND workers.employee_type = 'Regular'
   AND workers.active_status = 1
  GROUP BY snapshot_match.survey_date, workers.employee_id
),
responses AS (
  SELECT
    CAST(survey_launch_date AS DATE) AS survey_date,
    emp_id
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date IS NOT NULL
    AND emp_id IS NOT NULL
    AND growth_and_development_item_1_career_goals_can_be_met IS NOT NULL
  GROUP BY survey_launch_date, emp_id
)
SELECT
  eligible.survey_date AS snapshot_date,
  MAX(eligible.fiscal_year) AS fiscal_year,
  COUNT(DISTINCT eligible.employee_id) AS eligible_employees,
  COUNT(DISTINCT responses.emp_id) AS observable_employees,
  CAST(NULL AS BIGINT) AS event_employees,
  'Observable means the Career Goals item is populated for an eligible employee.' AS notes
FROM eligible
LEFT JOIN responses
  ON eligible.survey_date = responses.survey_date
 AND eligible.employee_id = responses.emp_id
GROUP BY eligible.survey_date
ORDER BY eligible.survey_date
