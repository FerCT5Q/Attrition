/*
  Pregunta: ¿cuántas personas de Critical Tech quedan en 'Other Eng' antes y
  después de la reasignación de job family del 2026-09-01?
  Población: empleados Regular activos en las fotos mensuales 2026-08-23 y
  2026-09-27. El segmento sale de job_family vía hrda.critical_tech.
  Sólo conteos agregados.
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
  COUNT(DISTINCT CASE WHEN c.seg IS NOT NULL THEN p.employee_id END) AS critical_tech,
  COUNT(DISTINCT CASE WHEN c.seg = 'Other Eng' THEN p.employee_id END) AS other_eng,
  COUNT(DISTINCT CASE WHEN c.seg <> 'Other Eng' THEN p.employee_id END) AS sin_other_eng
FROM hrda.post_hire_monthly_worker_dtls p
LEFT JOIN catalogo c
  ON TRIM(LOWER(p.job_family)) = c.family_key
WHERE CAST(p.fis_mo_end_dt AS DATE) IN (DATE '2026-08-23', DATE '2026-09-27')
  AND p.worker_type = 'Employee'
  AND p.employee_type = 'Regular'
  AND p.active_status = 1
GROUP BY 1
ORDER BY 1;
