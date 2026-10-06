-- Dominio agregado visible de Compensation grade.
-- Se excluyen nulos/blancos y categorias con menos de 30 empleados distintos
-- para respetar la regla minima de privacidad.
-- Corte de conocimiento: no usar snapshots posteriores a 2026-08-25.
SELECT
    NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') AS compensation_grade,
    COUNT(*) AS worker_month_rows,
    COUNT(DISTINCT employee_id) AS distinct_employees,
    MIN(fis_mo_end_dt) AS first_snapshot,
    MAX(fis_mo_end_dt) AS last_snapshot
FROM hrda.post_hire_monthly_worker_dtls
WHERE worker_type = 'Employee'
  AND employee_type = 'Regular'
  AND active_status = 1
  AND fis_mo_end_dt <= '2026-08-25'
  AND NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') IS NOT NULL
GROUP BY 1
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY compensation_grade
LIMIT 100;
