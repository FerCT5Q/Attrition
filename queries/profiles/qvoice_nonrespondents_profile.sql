WITH survey_dates AS (
  SELECT CAST(survey_launch_date AS DATE) AS survey_date
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date IS NOT NULL
  GROUP BY survey_launch_date
),
snapshot_match AS (
  SELECT
    survey_dates.survey_date,
    MAX(workers.fis_mo_end_dt) AS snapshot_date
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
respondents AS (
  SELECT
    CAST(survey_launch_date AS DATE) AS survey_date,
    emp_id
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date IS NOT NULL
    AND emp_id IS NOT NULL
  GROUP BY survey_launch_date, emp_id
)
SELECT
  eligible.survey_date AS snapshot_date,
  MAX(eligible.fiscal_year) AS fiscal_year,
  COUNT(DISTINCT eligible.employee_id) AS eligible_employees,
  COUNT(DISTINCT eligible.employee_id) AS observable_employees,
  COUNT(DISTINCT CASE
    WHEN respondents.emp_id IS NULL THEN eligible.employee_id
  END) AS event_employees,
  'Eligibility uses the latest active Regular Employee snapshot on or before launch.' AS notes
FROM eligible
LEFT JOIN respondents
  ON eligible.survey_date = respondents.survey_date
 AND eligible.employee_id = respondents.emp_id
GROUP BY eligible.survey_date
ORDER BY eligible.survey_date
