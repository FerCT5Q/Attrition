/* Auditoría en RAM de enlace anual de QVoice; sin outcomes ni texto libre. */
WITH population AS (
 SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date,employee_id,
        MAX(CAST(service_date AS DATE)) AS service_date,COUNT(*) AS source_rows
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '__PERIOD_START__' AND DATE '__PERIOD_END__'
   AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
   AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
 GROUP BY 1,2
)
SELECT p.snapshot_date,MD5(CAST(p.employee_id AS VARCHAR)||'__RUN_SALT__') AS person_key,
       p.source_rows,
       CASE WHEN p.source_rows=1 AND p.service_date IS NOT NULL AND p.service_date<=DATE '2024-01-01'
                 AND NOT EXISTS (SELECT 1 FROM hrda.post_hire_monthly_worker_dtls e
                   WHERE e.employee_id=p.employee_id AND CAST(e.term_date AS DATE)>=DATE '2024-01-01'
                     AND CAST(e.term_date AS DATE)<=p.snapshot_date AND CAST(e.fis_mo_end_dt AS DATE)<=p.snapshot_date)
            THEN 1 ELSE 0 END AS same_episode_2024,
       CASE WHEN p.source_rows=1 AND p.service_date IS NOT NULL AND p.service_date<=DATE '2025-01-01'
                 AND NOT EXISTS (SELECT 1 FROM hrda.post_hire_monthly_worker_dtls e
                   WHERE e.employee_id=p.employee_id AND CAST(e.term_date AS DATE)>=DATE '2025-01-01'
                     AND CAST(e.term_date AS DATE)<=p.snapshot_date AND CAST(e.fis_mo_end_dt AS DATE)<=p.snapshot_date)
            THEN 1 ELSE 0 END AS same_episode_2025
FROM population p
