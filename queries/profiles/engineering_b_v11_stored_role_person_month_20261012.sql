-- Valor time_in_role de la misma foto. Procesamiento sólo en RAM autorizado.
WITH cells AS (
 SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date,employee_id,
        MAX(time_in_role) AS stored_role,COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(CAST(time_in_role AS VARCHAR(64)),'<NULL>')) AS value_variants
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '__PERIOD_START__' AND DATE '__PERIOD_END__'
   AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
   AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering'
 GROUP BY 1,2
), encoded AS (
 SELECT snapshot_date,employee_id,stored_role,source_rows,value_variants,
 CASE WHEN stored_role IS NULL OR stored_role<0 OR value_variants<>1 THEN '(unknown)'
      WHEN stored_role<1 THEN '<1'
      WHEN stored_role<2 THEN '1-<2'
      WHEN stored_role<3 THEN '2-<3'
      WHEN stored_role<5 THEN '3-<5'
      WHEN stored_role<10 THEN '5-<10'
      ELSE '10+' END AS time_in_role_stored_v11
 FROM cells
)
-- MODEL_OUTPUT
SELECT snapshot_date,MD5(CAST(employee_id AS VARCHAR)||'__RUN_SALT__') AS person_key,
       time_in_role_stored_v11
FROM encoded
