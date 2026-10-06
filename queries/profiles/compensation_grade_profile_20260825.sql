-- Perfil agregado de Compensation grade.
-- Poblacion: empleados regulares activos en cada snapshot mensual.
-- Grain: fila empleado-snapshot; no devuelve identificadores.
-- Corte de conocimiento: no usar snapshots posteriores a 2026-08-25.
SELECT
    'compensation_grade_profile' AS profile_type,
    COUNT(*) AS worker_month_rows,
    COUNT(DISTINCT employee_id) AS distinct_employees,
    COUNT(NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '')) AS populated_rows,
    COUNT(*) - COUNT(NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '')) AS missing_or_blank_rows,
    COUNT(DISTINCT NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '')) AS distinct_grade_values,
    MIN(fis_mo_end_dt) AS first_snapshot,
    MAX(fis_mo_end_dt) AS last_snapshot
FROM hrda.post_hire_monthly_worker_dtls
WHERE worker_type = 'Employee'
  AND employee_type = 'Regular'
  AND active_status = 1
  AND fis_mo_end_dt <= '2026-08-25';
