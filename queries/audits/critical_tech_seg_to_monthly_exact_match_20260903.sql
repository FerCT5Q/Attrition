-- Pregunta: ¿Con cual columna categorial de la tabla mensual hacen match exacto
-- los valores de critical_tech.seg en el ultimo snapshot de empleados regulares activos?
-- Regla de aceptacion para un match fuerte: todos los valores distintos de seg deben
-- estar presentes en una sola columna candidata y no debe haber duplicados en el mapping.
WITH latest_snapshot AS (
  SELECT MAX(fis_mo_end_dt) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
critical_mapping AS (
  SELECT
    UPPER(TRIM(seg)) AS normalized_value,
    COUNT(*) AS mapping_rows
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(seg), '') IS NOT NULL
  GROUP BY 1
),
monthly_candidate_rows AS (
  SELECT l.snapshot_date, 'job_family' AS candidate_column, UPPER(TRIM(m.job_family)) AS normalized_value
  FROM hrda.post_hire_monthly_worker_dtls AS m CROSS JOIN latest_snapshot AS l
  WHERE m.fis_mo_end_dt = l.snapshot_date AND m.worker_type = 'Employee' AND m.employee_type = 'Regular' AND m.active_status = 1
    AND NULLIF(TRIM(m.job_family), '') IS NOT NULL
  UNION ALL
  SELECT l.snapshot_date, 'job_family_group', UPPER(TRIM(m.job_family_group))
  FROM hrda.post_hire_monthly_worker_dtls AS m CROSS JOIN latest_snapshot AS l
  WHERE m.fis_mo_end_dt = l.snapshot_date AND m.worker_type = 'Employee' AND m.employee_type = 'Regular' AND m.active_status = 1
    AND NULLIF(TRIM(m.job_family_group), '') IS NOT NULL
  UNION ALL
  SELECT l.snapshot_date, 'job_family_group_short', UPPER(TRIM(m.job_family_group_short))
  FROM hrda.post_hire_monthly_worker_dtls AS m CROSS JOIN latest_snapshot AS l
  WHERE m.fis_mo_end_dt = l.snapshot_date AND m.worker_type = 'Employee' AND m.employee_type = 'Regular' AND m.active_status = 1
    AND NULLIF(TRIM(m.job_family_group_short), '') IS NOT NULL
  UNION ALL
  SELECT l.snapshot_date, 'job_family_short', UPPER(TRIM(m.job_family_short))
  FROM hrda.post_hire_monthly_worker_dtls AS m CROSS JOIN latest_snapshot AS l
  WHERE m.fis_mo_end_dt = l.snapshot_date AND m.worker_type = 'Employee' AND m.employee_type = 'Regular' AND m.active_status = 1
    AND NULLIF(TRIM(m.job_family_short), '') IS NOT NULL
  UNION ALL
  SELECT l.snapshot_date, 'technical_employee1', UPPER(TRIM(m.technical_employee1))
  FROM hrda.post_hire_monthly_worker_dtls AS m CROSS JOIN latest_snapshot AS l
  WHERE m.fis_mo_end_dt = l.snapshot_date AND m.worker_type = 'Employee' AND m.employee_type = 'Regular' AND m.active_status = 1
    AND NULLIF(TRIM(m.technical_employee1), '') IS NOT NULL
),
candidate_names AS (
  SELECT 'job_family' AS candidate_column
  UNION ALL SELECT 'job_family_group'
  UNION ALL SELECT 'job_family_group_short'
  UNION ALL SELECT 'job_family_short'
  UNION ALL SELECT 'technical_employee1'
),
candidate_values AS (
  SELECT candidate_column, normalized_value
  FROM monthly_candidate_rows
  GROUP BY 1, 2
),
mapping_metrics AS (
  SELECT
    cn.candidate_column,
    COUNT(*) AS mapping_values,
    SUM(CASE WHEN cv.normalized_value IS NOT NULL THEN 1 ELSE 0 END) AS mapping_values_present,
    SUM(CASE WHEN cv.normalized_value IS NULL THEN 1 ELSE 0 END) AS mapping_values_not_present,
    SUM(CASE WHEN cm.mapping_rows > 1 THEN 1 ELSE 0 END) AS mapping_duplicate_values
  FROM candidate_names AS cn
  CROSS JOIN critical_mapping AS cm
  LEFT JOIN candidate_values AS cv
    ON cv.candidate_column = cn.candidate_column
   AND cv.normalized_value = cm.normalized_value
  GROUP BY 1
),
row_metrics AS (
  SELECT
    r.snapshot_date,
    r.candidate_column,
    COUNT(*) AS eligible_rows,
    SUM(CASE WHEN cm.normalized_value IS NOT NULL THEN 1 ELSE 0 END) AS matched_rows,
    SUM(CASE WHEN cm.normalized_value IS NULL THEN 1 ELSE 0 END) AS unmatched_rows,
    COUNT(DISTINCT r.normalized_value) AS candidate_distinct_values,
    COUNT(DISTINCT CASE WHEN cm.normalized_value IS NOT NULL THEN r.normalized_value END) AS matched_distinct_values
  FROM monthly_candidate_rows AS r
  LEFT JOIN critical_mapping AS cm
    ON cm.normalized_value = r.normalized_value
  GROUP BY 1, 2
)
SELECT
  r.snapshot_date,
  r.candidate_column,
  m.mapping_values,
  m.mapping_values_present,
  m.mapping_values_not_present,
  m.mapping_duplicate_values,
  r.candidate_distinct_values,
  r.matched_distinct_values,
  r.eligible_rows,
  r.matched_rows,
  r.unmatched_rows,
  ROUND(100.0 * r.matched_rows / NULLIF(r.eligible_rows, 0), 2) AS matched_row_percent
FROM row_metrics AS r
INNER JOIN mapping_metrics AS m
  ON m.candidate_column = r.candidate_column
ORDER BY r.candidate_column;
