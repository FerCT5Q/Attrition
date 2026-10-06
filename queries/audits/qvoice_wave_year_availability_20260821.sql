WITH qvoice_summary AS (
  SELECT
    COUNT(*) AS response_rows,
    COUNT(DISTINCT emp_id) AS distinct_emp_ids,
    COUNT(DISTINCT CAST(survey_launch_date AS DATE)) AS distinct_survey_dates,
    MIN(CAST(survey_launch_date AS DATE)) AS min_survey_launch_date,
    MAX(CAST(survey_launch_date AS DATE)) AS max_survey_launch_date,
    COUNT(CASE WHEN survey_launch_date IS NULL THEN 1 END) AS rows_missing_survey_launch_date
  FROM hrda.qvoice_survey_data
),
qvoice_by_calendar_year AS (
  SELECT
    EXTRACT(year FROM CAST(survey_launch_date AS DATE))::INTEGER AS calendar_year,
    COUNT(*) AS response_rows,
    COUNT(DISTINCT emp_id) AS distinct_emp_ids,
    COUNT(DISTINCT CAST(survey_launch_date AS DATE)) AS distinct_survey_dates,
    MIN(CAST(survey_launch_date AS DATE)) AS min_survey_launch_date,
    MAX(CAST(survey_launch_date AS DATE)) AS max_survey_launch_date
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date IS NOT NULL
  GROUP BY 1
),
requested_years AS (
  SELECT 2024 AS calendar_year
  UNION ALL SELECT 2025
  UNION ALL SELECT 2026
)
SELECT
  'qvoice_summary' AS section,
  'hrda.qvoice_survey_data' AS scope,
  NULL::INTEGER AS calendar_year,
  response_rows AS metric_1,
  distinct_emp_ids AS metric_2,
  distinct_survey_dates AS metric_3,
  rows_missing_survey_launch_date AS metric_4,
  NULL::BIGINT AS metric_5,
  min_survey_launch_date AS date_1,
  max_survey_launch_date AS date_2,
  'metric_1=response_rows, metric_2=distinct_emp_ids, metric_3=distinct_survey_dates, metric_4=rows_missing_survey_launch_date' AS notes
FROM qvoice_summary
UNION ALL
SELECT
  'qvoice_calendar_year_presence' AS section,
  'survey_launch_date_year' AS scope,
  requested_years.calendar_year,
  COALESCE(qvoice_by_calendar_year.response_rows, 0) AS metric_1,
  COALESCE(qvoice_by_calendar_year.distinct_emp_ids, 0) AS metric_2,
  COALESCE(qvoice_by_calendar_year.distinct_survey_dates, 0) AS metric_3,
  NULL::BIGINT AS metric_4,
  NULL::BIGINT AS metric_5,
  qvoice_by_calendar_year.min_survey_launch_date AS date_1,
  qvoice_by_calendar_year.max_survey_launch_date AS date_2,
  'metric_1=response_rows, metric_2=distinct_emp_ids, metric_3=distinct_survey_dates for requested calendar year' AS notes
FROM requested_years
LEFT JOIN qvoice_by_calendar_year
  ON requested_years.calendar_year = qvoice_by_calendar_year.calendar_year
UNION ALL
SELECT
  'qvoice_available_calendar_year' AS section,
  'survey_launch_date_year' AS scope,
  calendar_year,
  response_rows AS metric_1,
  distinct_emp_ids AS metric_2,
  distinct_survey_dates AS metric_3,
  NULL::BIGINT AS metric_4,
  NULL::BIGINT AS metric_5,
  min_survey_launch_date AS date_1,
  max_survey_launch_date AS date_2,
  'metric_1=response_rows, metric_2=distinct_emp_ids, metric_3=distinct_survey_dates in available data' AS notes
FROM qvoice_by_calendar_year
ORDER BY section, calendar_year, scope
