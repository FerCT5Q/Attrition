/*
  Seguimiento de la diferencia encontrada al conciliar Intent to Stay.
  Población y filtro originales del playbook, sin extraer identificadores.
  Los conteos new_extraction_count son los agregados observados en el primer
  audit actual, congelados antes de esta comprobación independiente.
  Regla: mismo total que la nueva extracción, unicidad de empleado-baseline.
  Las diferencias frente al JSON histórico se reportan; no elevan scores.
*/
WITH windows AS (
  SELECT 2024 AS survey_year, DATE '2023-12-24' AS baseline_snapshot,
         40145 AS published_count, 40144 AS new_extraction_count
  UNION ALL SELECT 2025, DATE '2024-12-29', 42342, 42341
  UNION ALL SELECT 2026, DATE '2025-12-28', 47134, 47134
), baseline AS (
  SELECT w.survey_year, p.employee_id, COUNT(*) AS raw_rows
  FROM windows w
  INNER JOIN hrda.post_hire_monthly_worker_dtls p
    ON CAST(p.fis_mo_end_dt AS DATE) = w.baseline_snapshot
  WHERE p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
    AND p.employee_id IS NOT NULL
  GROUP BY w.survey_year, p.employee_id
)
SELECT w.survey_year, w.baseline_snapshot,
       COUNT(b.employee_id) AS current_eligible_count,
       MAX(w.published_count) AS published_eligible_count,
       COUNT(b.employee_id) - MAX(w.published_count) AS difference_from_published,
       CASE WHEN COUNT(b.employee_id) = MAX(w.new_extraction_count) THEN 0 ELSE 1 END AS new_extraction_mismatch_count,
       SUM(CASE WHEN b.raw_rows > 1 THEN 1 ELSE 0 END) AS duplicate_baseline_employee_count
FROM windows w
LEFT JOIN baseline b ON b.survey_year = w.survey_year
GROUP BY w.survey_year, w.baseline_snapshot
ORDER BY w.survey_year;
