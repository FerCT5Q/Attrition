/*
  QVoice heartbeat: aggregate reconciliation of the HRDA workforce snapshot
  and the warehouse QVoice wave context.

  The scale values are sourced from the governed Jan-2026 raw workbook; this
  query only checks the corresponding HRDA population and stored wave scope.
  No employee rows, identifiers, labels or response values are returned.
*/
WITH workforce AS (
    SELECT
        COUNT(*) AS snapshot_rows,
        COUNT(DISTINCT employee_id) AS workforce_employees
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2025-12-28'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
), qvoice_wave AS (
    SELECT
        COUNT(*) AS qvoice_rows,
        COUNT(DISTINCT emp_id) AS qvoice_employees,
        COUNT(DISTINCT survey_launch_date) AS survey_wave_count,
        MIN(survey_launch_date) AS first_survey_launch_date,
        MAX(survey_launch_date) AS last_survey_launch_date
    FROM hrda.qvoice_survey_data
    WHERE survey_launch_date = DATE '2026-01-07'
)
SELECT
    workforce.snapshot_rows,
    workforce.workforce_employees,
    qvoice_wave.qvoice_rows,
    qvoice_wave.qvoice_employees,
    qvoice_wave.survey_wave_count,
    qvoice_wave.first_survey_launch_date,
    qvoice_wave.last_survey_launch_date
FROM workforce
CROSS JOIN qvoice_wave;
