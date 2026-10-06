-- Claim: establish the latest observable application event date in each HRDA
-- metadata candidate that contains the required application-event fields.
-- Semantic type: availability audit for the derived feature "Applied to a job".
-- Reporting mode: presentation (aggregate-only; no employee-level output).
-- Acceptance rule: a source is current for the 2026-08-23 workforce snapshot
-- only if its latest non-null application_date is on or after 2026-08-23.
-- A passing date would still require source ownership, event semantics,
-- completeness, and employee-snapshot join validation before use.
SELECT 'hrda.applications' AS source_table, COUNT(*) AS source_rows, MIN(application_date) AS first_application_date, MAX(application_date) AS last_application_date FROM hrda.applications
UNION ALL SELECT 'hrda.applications_vw', COUNT(*), MIN(application_date), MAX(application_date) FROM hrda.applications_vw
UNION ALL SELECT 'hrda.job_applications', COUNT(*), MIN(application_date), MAX(application_date) FROM hrda.job_applications
UNION ALL SELECT 'hrda.job_applications_vw', COUNT(*), MIN(application_date), MAX(application_date) FROM hrda.job_applications_vw
ORDER BY source_table;
