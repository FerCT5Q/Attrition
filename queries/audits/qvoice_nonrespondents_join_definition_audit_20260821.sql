WITH survey_dates AS (
  SELECT CAST(survey_launch_date AS DATE) AS survey_date
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date IS NOT NULL
  GROUP BY 1
),
snapshot_match AS (
  SELECT
    survey_dates.survey_date,
    MAX(workers.fis_mo_end_dt) AS snapshot_date
  FROM survey_dates
  JOIN hrda.post_hire_monthly_worker_dtls workers
    ON workers.fis_mo_end_dt <= survey_dates.survey_date
  GROUP BY 1
),
eligible_raw AS (
  SELECT
    snapshot_match.survey_date,
    workers.employee_id
  FROM snapshot_match
  JOIN hrda.post_hire_monthly_worker_dtls workers
    ON workers.fis_mo_end_dt = snapshot_match.snapshot_date
   AND workers.worker_type = 'Employee'
   AND workers.employee_type = 'Regular'
   AND workers.active_status = 1
),
eligible_key_counts AS (
  SELECT
    survey_date,
    employee_id,
    COUNT(*) AS row_count
  FROM eligible_raw
  GROUP BY 1, 2
),
eligible_keys AS (
  SELECT survey_date, employee_id
  FROM eligible_key_counts
),
response_key_counts AS (
  SELECT
    CAST(survey_launch_date AS DATE) AS survey_date,
    emp_id,
    COUNT(*) AS row_count
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date IS NOT NULL
    AND emp_id IS NOT NULL
  GROUP BY 1, 2
),
response_keys AS (
  SELECT survey_date, emp_id
  FROM response_key_counts
),
joined AS (
  SELECT
    eligible_keys.survey_date,
    eligible_keys.employee_id,
    response_keys.emp_id
  FROM eligible_keys
  LEFT JOIN response_keys
    ON eligible_keys.survey_date = response_keys.survey_date
   AND eligible_keys.employee_id = response_keys.emp_id
),
respondent_match AS (
  SELECT
    response_keys.survey_date,
    response_keys.emp_id,
    eligible_keys.employee_id
  FROM response_keys
  LEFT JOIN eligible_keys
    ON response_keys.survey_date = eligible_keys.survey_date
   AND response_keys.emp_id = eligible_keys.employee_id
),
eligible_summary AS (
  SELECT
    survey_date,
    COUNT(*) AS eligible_employees,
    SUM(CASE WHEN row_count > 1 THEN 1 ELSE 0 END) AS duplicate_eligible_employee_date_keys
  FROM eligible_key_counts
  GROUP BY 1
),
response_summary AS (
  SELECT
    survey_date,
    COUNT(*) AS response_employee_keys,
    SUM(CASE WHEN row_count > 1 THEN 1 ELSE 0 END) AS duplicate_response_employee_date_keys
  FROM response_key_counts
  GROUP BY 1
),
join_summary AS (
  SELECT
    survey_date,
    COUNT(DISTINCT emp_id) AS eligible_respondents,
    COUNT(DISTINCT CASE WHEN emp_id IS NULL THEN employee_id END) AS eligible_nonrespondents
  FROM joined
  GROUP BY 1
),
respondent_outside_summary AS (
  SELECT
    survey_date,
    COUNT(DISTINCT CASE WHEN employee_id IS NULL THEN emp_id END) AS respondent_keys_not_in_eligible_snapshot
  FROM respondent_match
  GROUP BY 1
)
SELECT
  'qvoice_nonrespondents_join_definition' AS section,
  CAST(survey_dates.survey_date AS VARCHAR(32)) AS scope,
  MAX(eligible_summary.eligible_employees) AS eligible_employees,
  MAX(response_summary.response_employee_keys) AS response_employee_keys,
  MAX(join_summary.eligible_respondents) AS eligible_respondents,
  MAX(join_summary.eligible_nonrespondents) AS eligible_nonrespondents,
  MAX(respondent_outside_summary.respondent_keys_not_in_eligible_snapshot) AS respondent_keys_not_in_eligible_snapshot,
  MAX(eligible_summary.duplicate_eligible_employee_date_keys) AS duplicate_eligible_employee_date_keys,
  MAX(response_summary.duplicate_response_employee_date_keys) AS duplicate_response_employee_date_keys,
  MIN(snapshot_match.snapshot_date) AS worker_snapshot_used,
  survey_dates.survey_date AS survey_launch_date,
  'Acceptance for Definition/Join 2 would require approved eligibility roster or accepted proxy plus zero unexplained duplicate keys and explained respondent keys outside eligible snapshot.' AS notes
FROM survey_dates
JOIN snapshot_match
  ON survey_dates.survey_date = snapshot_match.survey_date
LEFT JOIN eligible_summary
  ON survey_dates.survey_date = eligible_summary.survey_date
LEFT JOIN response_summary
  ON survey_dates.survey_date = response_summary.survey_date
LEFT JOIN join_summary
  ON survey_dates.survey_date = join_summary.survey_date
LEFT JOIN respondent_outside_summary
  ON survey_dates.survey_date = respondent_outside_summary.survey_date
GROUP BY survey_dates.survey_date
ORDER BY survey_dates.survey_date
