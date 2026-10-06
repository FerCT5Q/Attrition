/*
  Pregunta: ¿qué categorías y volúmenes tienen las candidatas categóricas
  (region, labor_market, work_arrangement, new_hire_type, grade family,
  capas de organización) en la foto 2026-07-26 de Engineering?
  Regla de aceptación: categorías con < 300 personas por foto se agrupan en
  "Other" en el loader para mantener grupos publicables (>= 30) en cada fold.
  Sólo conteos agregados.
*/
WITH base AS (
  SELECT
    employee_id,
    COALESCE(NULLIF(TRIM(region), ''), '(unknown)') AS region,
    COALESCE(NULLIF(TRIM(labor_market), ''), '(unknown)') AS labor_market,
    COALESCE(NULLIF(TRIM(work_arrangement), ''), '(unknown)') AS work_arrangement,
    COALESCE(NULLIF(TRIM(new_hire_type), ''), '(unknown)') AS new_hire_type,
    COALESCE(LEFT(NULLIF(TRIM(compensation_grade), ''), 1), '(unknown)') AS grade_family,
    COALESCE(CAST(worker_supervisory_organization_level_from_top AS VARCHAR), '(unknown)') AS layers,
    COALESCE(NULLIF(TRIM(level_grouped), ''), '(unknown)') AS level_grouped
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE '2026-07-26'
    AND worker_type = 'Employee' AND employee_type = 'Regular'
    AND active_status = 1 AND is_rf360_yes_no = 0
    AND TRIM(eng_or_noneng) = 'Engineering'
)
SELECT 'region' AS variable, region AS categoria, COUNT(DISTINCT employee_id) AS personas FROM base GROUP BY 2
UNION ALL SELECT 'labor_market', labor_market, COUNT(DISTINCT employee_id) FROM base GROUP BY 2
UNION ALL SELECT 'work_arrangement', work_arrangement, COUNT(DISTINCT employee_id) FROM base GROUP BY 2
UNION ALL SELECT 'new_hire_type', new_hire_type, COUNT(DISTINCT employee_id) FROM base GROUP BY 2
UNION ALL SELECT 'grade_family', grade_family, COUNT(DISTINCT employee_id) FROM base GROUP BY 2
UNION ALL SELECT 'layers', layers, COUNT(DISTINCT employee_id) FROM base GROUP BY 2
UNION ALL SELECT 'level_grouped', level_grouped, COUNT(DISTINCT employee_id) FROM base GROUP BY 2
ORDER BY 1, 3 DESC
