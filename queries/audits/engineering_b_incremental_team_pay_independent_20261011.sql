/* Recálculo independiente, sin reutilizar workforce/peer_stats ni rankings.
   Regla: reconciliar número de grupos comparables y población elegible. */
WITH source_direct AS (
 SELECT CAST(fis_mo_end_dt AS DATE) AS d,employee_id,manager_employee_id,
        UPPER(TRIM(country)) AS country,UPPER(TRIM(compensation_grade)) AS grade,
        UPPER(TRIM(fte_annual_base_pay_currency_code)) AS currency,
        fte_annual_base_pay AS pay
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2026-01-01' AND DATE '2026-09-07'
   AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
   AND is_rf360_yes_no=0 AND employee_id IS NOT NULL
   AND manager_employee_id IS NOT NULL AND manager_employee_id<>employee_id
   AND NULLIF(TRIM(country),'') IS NOT NULL AND NULLIF(TRIM(compensation_grade),'') IS NOT NULL
   AND NULLIF(TRIM(fte_annual_base_pay_currency_code),'') IS NOT NULL AND fte_annual_base_pay>0
),
cg AS (
 SELECT d,manager_employee_id,country,grade,currency,
        COUNT(DISTINCT employee_id) AS members,MIN(pay) AS pmin,MAX(pay) AS pmax
 FROM source_direct GROUP BY d,manager_employee_id,country,grade,currency
)
SELECT COUNT(*) AS peer_groups,
       SUM(CASE WHEN members>=2 THEN 1 ELSE 0 END) AS peer_groups_ge2,
       SUM(CASE WHEN members>=5 THEN 1 ELSE 0 END) AS peer_groups_ge5,
       MAX(members) AS maximum_members,SUM(members) AS member_rows,
       SUM(CASE WHEN members>=2 AND pmax/pmin>=1.10 THEN 1 ELSE 0 END) AS flagged_groups
FROM cg;
