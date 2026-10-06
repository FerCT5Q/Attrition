/*
Claim: the stored QVoice 2026 table covers the complete default workforce
denominator at the survey launch-aligned snapshot.
Mode: internal_analysis; aggregate-only; employee_id is used only in joins and
distinct counts.
Acceptance rule: report the launch-aligned snapshot, the distinct default
eligible workforce, QVoice keys, matched eligible QVoice keys, eligible
workforce keys without a QVoice row, and QVoice keys outside the eligible
workforce. Equality would show source coverage of the workforce denominator;
it would still not prove that all were invited.
*/
WITH survey_meta AS (
    SELECT
        CAST(MAX(survey_launch_date) AS DATE) AS survey_launch_date
    FROM hrda.qvoice_survey_data
),
snapshot_dates AS (
    SELECT MAX(w.fis_mo_end_dt) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN survey_meta AS s
    WHERE w.fis_mo_end_dt <= s.survey_launch_date
),
eligible_workforce AS (
    SELECT DISTINCT w.employee_id
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN snapshot_dates AS s
    WHERE w.fis_mo_end_dt = s.snapshot_date
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
),
qvoice_keys AS (
    SELECT DISTINCT emp_id AS employee_id
    FROM hrda.qvoice_survey_data
    WHERE emp_id IS NOT NULL
),
matched AS (
    SELECT q.employee_id
    FROM qvoice_keys AS q
    JOIN eligible_workforce AS e
      ON e.employee_id = q.employee_id
),
eligible_without_qvoice AS (
    SELECT e.employee_id
    FROM eligible_workforce AS e
    LEFT JOIN qvoice_keys AS q
      ON q.employee_id = e.employee_id
    WHERE q.employee_id IS NULL
),
qvoice_outside_eligible AS (
    SELECT q.employee_id
    FROM qvoice_keys AS q
    LEFT JOIN eligible_workforce AS e
      ON e.employee_id = q.employee_id
    WHERE e.employee_id IS NULL
)
SELECT
    s.survey_launch_date,
    x.snapshot_date,
    (SELECT COUNT(*) FROM eligible_workforce) AS eligible_workforce_employees,
    (SELECT COUNT(*) FROM qvoice_keys) AS qvoice_distinct_emp_ids,
    (SELECT COUNT(*) FROM matched) AS qvoice_keys_matched_to_eligible,
    (SELECT COUNT(*) FROM eligible_without_qvoice) AS eligible_without_qvoice_row,
    (SELECT COUNT(*) FROM qvoice_outside_eligible) AS qvoice_keys_outside_eligible,
    CASE
        WHEN (SELECT COUNT(*) FROM eligible_without_qvoice) = 0 THEN 'coverage_complete_for_default_workforce'
        ELSE 'coverage_incomplete_for_default_workforce'
    END AS workforce_coverage_result
FROM survey_meta AS s
    CROSS JOIN snapshot_dates AS x;
