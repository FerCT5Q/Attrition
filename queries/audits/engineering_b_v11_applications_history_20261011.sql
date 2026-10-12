-- Fechas y observabilidad de solicitudes del V11. No sale ninguna requisición.
WITH sources AS (
 SELECT 'applications'::VARCHAR(32) AS source,employee_id,req_id,application_date,added_date,
        last_modified_date,airflow_execution_date AS loaded_date
 FROM hrda.applications WHERE cand_applied=1
 UNION ALL
 SELECT 'job_applications_vw'::VARCHAR(32),employee_id,req_id,application_date,added_date,
        last_modified_date,NULL::DATE
 FROM hrda.job_applications_vw WHERE cand_applied=1
), eligible AS (
 SELECT DISTINCT employee_id FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
   AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
   AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering'
)
SELECT s.source,COUNT(*) AS source_rows,COUNT(DISTINCT s.employee_id) AS linked_people,
       SUM(CASE WHEN s.employee_id IS NULL THEN 1 ELSE 0 END) AS missing_employee_rows,
       SUM(CASE WHEN s.req_id IS NULL OR s.application_date IS NULL THEN 1 ELSE 0 END) AS incomplete_event_rows,
       SUM(CASE WHEN e.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS rows_linked_to_ever_eligible_engineering,
       MIN(s.application_date) AS first_application_date,MAX(s.application_date) AS last_application_date,
       MIN(s.added_date) AS first_added_date,MAX(s.added_date) AS last_added_date,
       MIN(s.last_modified_date) AS first_modified_date,MAX(s.last_modified_date) AS last_modified_date,
       MIN(s.loaded_date) AS first_loaded_date,MAX(s.loaded_date) AS last_loaded_date,
       SUM(CASE WHEN s.employee_id IS NOT NULL AND s.req_id IS NOT NULL
                 AND s.application_date BETWEEN DATE '2020-07-26' AND DATE '2026-09-07' THEN 1 ELSE 0 END) AS events_before_boundary,
       SUM(CASE WHEN s.employee_id IS NOT NULL AND s.req_id IS NOT NULL
                 AND s.application_date BETWEEN DATE '2026-03-07' AND DATE '2026-09-07' THEN 1 ELSE 0 END) AS events_in_current_six_month_window,
       SUM(CASE WHEN s.employee_id IS NOT NULL AND s.req_id IS NOT NULL
                 AND s.application_date<=DATE '2026-09-07' AND s.added_date<=DATE '2026-09-07'
                 AND s.last_modified_date<=DATE '2026-09-07'
                 AND (s.loaded_date IS NULL OR s.loaded_date<=DATE '2026-09-07') THEN 1 ELSE 0 END) AS technical_times_before_boundary,
       CASE WHEN SUM(CASE WHEN s.application_date BETWEEN DATE '2026-03-07' AND DATE '2026-09-07' THEN 1 ELSE 0 END)=0
            THEN 1 ELSE 0 END AS missing_current_window
FROM sources s LEFT JOIN eligible e ON e.employee_id=s.employee_id
GROUP BY s.source ORDER BY s.source
