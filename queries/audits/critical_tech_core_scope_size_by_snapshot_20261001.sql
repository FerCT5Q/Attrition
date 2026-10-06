/*
  Pregunta: ¿cuántas personas entran por foto en el alcance del playbook
  (Critical Tech sin Other Eng, sin RF360) a lo largo de la historia del modelo?
  Población: Employee, Regular, active_status=1, is_rf360_yes_no=0, job_family
  con match en hrda.critical_tech y seg <> 'Other Eng' (job family de cada foto).
  Sólo conteos agregados por foto; también se reporta RF360 nulo.
*/
WITH catalogo AS (
  SELECT
    TRIM(LOWER(extended_job_family)) AS family_key,
    MAX(NULLIF(TRIM(seg), '')) AS seg
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
  GROUP BY 1
)
SELECT
  CAST(p.fis_mo_end_dt AS DATE) AS foto,
  COUNT(DISTINCT CASE WHEN c.seg <> 'Other Eng' AND p.is_rf360_yes_no = 0 THEN p.employee_id END) AS alcance_playbook,
  COUNT(DISTINCT CASE WHEN c.seg <> 'Other Eng' AND p.is_rf360_yes_no IS NULL THEN p.employee_id END) AS rf360_nulo,
  COUNT(DISTINCT CASE WHEN c.seg IS NOT NULL AND p.is_rf360_yes_no = 0 THEN p.employee_id END) AS critical_tech_sin_rf360
FROM hrda.post_hire_monthly_worker_dtls p
INNER JOIN catalogo c
  ON TRIM(LOWER(p.job_family)) = c.family_key
WHERE CAST(p.fis_mo_end_dt AS DATE) >= DATE '2020-07-26'
  AND p.worker_type = 'Employee'
  AND p.employee_type = 'Regular'
  AND p.active_status = 1
GROUP BY 1
ORDER BY 1;
