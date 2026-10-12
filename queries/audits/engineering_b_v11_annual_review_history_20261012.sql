-- Annual Review: grain, fechas técnicas y enlace agregado. Sin valores salariales.
WITH review_rows AS (
 SELECT TRIM(cycle_name) AS cycle_name,
        NULLIF(TRIM(CAST(employee_id AS VARCHAR(80))),'') AS employee_key,
        UPPER(NULLIF(TRIM(promotion_yes_no),'')) AS promotion_flag,
        NULLIF(TRIM(grade),'') AS grade,
        last_modified_date,airflow_execution_date
 FROM hrda.annual_review_report
), people AS (
 SELECT DISTINCT CAST(employee_id AS VARCHAR(80)) AS employee_key
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
 AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
 AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering'
), grouped AS (
 SELECT cycle_name,employee_key,COUNT(*) AS source_rows,
 COUNT(DISTINCT COALESCE(promotion_flag,'<NULL>')) AS flag_variants,
 COUNT(DISTINCT COALESCE(grade,'<NULL>')) AS grade_variants,
 MAX(CASE WHEN promotion_flag IS NULL OR promotion_flag NOT IN ('YES','NO') THEN 1 ELSE 0 END) AS invalid_flag,
 MIN(last_modified_date) AS first_modified,MAX(last_modified_date) AS last_modified,
 MIN(airflow_execution_date) AS first_loaded,MAX(airflow_execution_date) AS last_loaded,
 SUM(CASE WHEN last_modified_date<=DATE '2026-09-07' AND airflow_execution_date<=DATE '2026-09-07' THEN 1 ELSE 0 END) AS technical_before_boundary
 FROM review_rows GROUP BY 1,2
)
SELECT g.cycle_name,COUNT(*) AS person_cycles,SUM(g.source_rows) AS source_rows,
 SUM(CASE WHEN p.employee_key IS NOT NULL THEN 1 ELSE 0 END) AS ever_eligible_engineering,
 SUM(CASE WHEN g.employee_key IS NULL THEN 1 ELSE 0 END) AS missing_key_groups,
 SUM(CASE WHEN g.source_rows>1 THEN 1 ELSE 0 END) AS duplicate_groups,
 SUM(CASE WHEN g.flag_variants>1 OR g.grade_variants>1 THEN 1 ELSE 0 END) AS conflicting_groups,
 SUM(g.invalid_flag) AS invalid_flags,
 MIN(g.first_modified) AS first_modified,MAX(g.last_modified) AS last_modified,
 MIN(g.first_loaded) AS first_loaded,MAX(g.last_loaded) AS last_loaded,
 SUM(g.technical_before_boundary) AS technical_before_boundary
FROM grouped g LEFT JOIN people p ON p.employee_key=g.employee_key
GROUP BY g.cycle_name HAVING COUNT(DISTINCT g.employee_key)>=30
ORDER BY g.cycle_name
