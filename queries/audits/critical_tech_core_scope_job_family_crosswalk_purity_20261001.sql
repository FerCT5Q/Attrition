/*
  Pregunta: ¿el job family de agosto-2026 (antes de la reasignación) predice si
  la persona queda en el alcance de septiembre (Critical Tech sin Other Eng, sin
  RF360)? Si cada job family viejo cae casi entero dentro o fuera, se puede
  definir el universo histórico por job family viejo (incluye a quienes se
  fueron) en lugar de congelar IDs (que sólo incluye a quienes se quedaron).
  Población: Employee, Regular, activos, sin RF360, presentes en 2026-08-23 y
  2026-09-27. Sólo conteos agregados por banda de pureza.
*/
WITH catalogo AS (
  SELECT TRIM(LOWER(extended_job_family)) AS family_key, MAX(NULLIF(TRIM(seg), '')) AS seg
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
  GROUP BY 1
),
foto AS (
  SELECT CAST(p.fis_mo_end_dt AS DATE) AS foto, p.employee_id,
         TRIM(LOWER(p.job_family)) AS family_key, c.seg
  FROM hrda.post_hire_monthly_worker_dtls p
  LEFT JOIN catalogo c ON TRIM(LOWER(p.job_family)) = c.family_key
  WHERE CAST(p.fis_mo_end_dt AS DATE) IN (DATE '2026-08-23', DATE '2026-09-27')
    AND p.worker_type = 'Employee' AND p.employee_type = 'Regular'
    AND p.active_status = 1 AND p.is_rf360_yes_no = 0
),
par AS (
  SELECT a.family_key AS jf_ago,
         CASE WHEN b.seg IS NOT NULL AND b.seg <> 'Other Eng' THEN 1 ELSE 0 END AS en_alcance_sep
  FROM foto a JOIN foto b ON a.employee_id = b.employee_id
   AND a.foto = DATE '2026-08-23' AND b.foto = DATE '2026-09-27'
),
jf AS (
  SELECT jf_ago, COUNT(*) AS personas, SUM(en_alcance_sep) AS en_alcance
  FROM par GROUP BY 1
)
SELECT
  CASE WHEN 1.0*en_alcance/personas >= 0.9 THEN '1. >=90% en alcance'
       WHEN 1.0*en_alcance/personas >= 0.5 THEN '2. 50-90%'
       WHEN 1.0*en_alcance/personas > 0.1 THEN '3. 10-50%'
       ELSE '4. <=10% en alcance' END AS banda_pureza,
  COUNT(*) AS job_families_ago,
  SUM(personas) AS personas,
  SUM(en_alcance) AS personas_en_alcance_sep
FROM jf
GROUP BY 1 ORDER BY 1;
