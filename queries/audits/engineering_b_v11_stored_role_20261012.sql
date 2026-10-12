-- Reconciliación de bandas V11 del campo almacenado, sin afirmar fórmula/unidad de origen.
WITH cells AS (
 SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date,employee_id,
        MAX(time_in_role) AS stored_role,COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(CAST(time_in_role AS VARCHAR(64)),'<NULL>')) AS value_variants
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
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
), comparison AS (
 SELECT snapshot_date,employee_id,source_rows,value_variants,stored_role,time_in_role_stored_v11,
        CASE WHEN time_in_role_stored_v11='(unknown)' THEN -1
             WHEN time_in_role_stored_v11='<1' THEN 0
             WHEN time_in_role_stored_v11='1-<2' THEN 1
             WHEN time_in_role_stored_v11='2-<3' THEN 2
             WHEN time_in_role_stored_v11='3-<5' THEN 3
             WHEN time_in_role_stored_v11='5-<10' THEN 4 ELSE 5 END AS encoded_index,
        CASE WHEN stored_role IS NULL OR stored_role<0 OR value_variants<>1 THEN -1 ELSE
          CASE WHEN stored_role>=1 THEN 1 ELSE 0 END+CASE WHEN stored_role>=2 THEN 1 ELSE 0 END+
          CASE WHEN stored_role>=3 THEN 1 ELSE 0 END+CASE WHEN stored_role>=5 THEN 1 ELSE 0 END+
          CASE WHEN stored_role>=10 THEN 1 ELSE 0 END END AS independent_index
 FROM encoded
)
SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,COUNT(*) AS person_snapshots,
 COUNT(DISTINCT employee_id) AS distinct_people,
 SUM(CASE WHEN source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_keys,
 SUM(CASE WHEN value_variants<>1 THEN 1 ELSE 0 END) AS conflicting_values,
 SUM(CASE WHEN stored_role<0 THEN 1 ELSE 0 END) AS negative_values,
 SUM(CASE WHEN encoded_index>=0 THEN 1 ELSE 0 END) AS observable_rows,
 COUNT(DISTINCT CASE WHEN encoded_index>=0 THEN snapshot_date END) AS observable_snapshots,
 MIN(CASE WHEN encoded_index>=0 THEN snapshot_date END) AS first_observed_date,
 SUM(CASE WHEN encoded_index<>independent_index THEN 1 ELSE 0 END) AS band_mismatches,
 SUM(CASE WHEN (stored_role IS NULL OR stored_role<0) AND encoded_index>=0 THEN 1 ELSE 0 END) AS invalid_observed
FROM comparison GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1
