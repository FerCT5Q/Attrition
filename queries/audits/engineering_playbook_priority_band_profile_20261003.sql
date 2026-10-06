/*
  Perfil de valores para definir bandas de variables del playbook en
  Engineering (2026-10-03). Foto 2026-01-25, Employee/Regular activos, sin
  RF360. Sólo agregados; categorías con < 30 personas se agrupan en "otros".

  Pregunta: ¿qué cortes de prior_qc_work_years, capas desde el CEO y
  work_arrangement dejan grupos >= 30 personas por foto?
  Regla: cada banda definida debe tener >= 30 personas.
*/
WITH pop AS (
  SELECT employee_id,
         MAX(prior_qc_work_years) AS prior_years,
         MAX(worker_supervisory_organization_level_from_top) AS layers,
         MAX(NULLIF(TRIM(work_arrangement), '')) AS wa
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE '2026-01-25'
    AND worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1
    AND is_rf360_yes_no = 0 AND TRIM(eng_or_noneng) = 'Engineering' AND employee_id IS NOT NULL
  GROUP BY 1
),
profile AS (
  SELECT 'prior_years' AS variable,
         CASE WHEN prior_years IS NULL OR prior_years < 0 THEN '(unknown)'
              WHEN prior_years < 1 THEN '00 <1' WHEN prior_years >= 16 THEN '16+'
              ELSE LPAD(CAST(FLOOR(prior_years) AS VARCHAR), 2, '0') END AS value,
         COUNT(*) AS people
  FROM pop GROUP BY 1, 2
  UNION ALL
  SELECT 'layers', COALESCE(CAST(layers AS VARCHAR), '(unknown)'), COUNT(*) FROM pop GROUP BY 1, 2
  UNION ALL
  SELECT 'work_arrangement',
         CASE WHEN wa IS NULL THEN '(unknown)'
              WHEN UPPER(wa) LIKE '%MEDICAL%' OR UPPER(wa) LIKE '%CAREGIV%' OR UPPER(wa) LIKE '%LOA%' THEN '(restringida)'
              ELSE wa END,
         COUNT(*) FROM pop GROUP BY 1, 2
)
SELECT variable, CASE WHEN people < 30 THEN 'otros' ELSE value END AS value, SUM(people) AS people
FROM profile GROUP BY 1, 2 ORDER BY 1, 2
