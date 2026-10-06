-- Propósito: comprobar la cobertura histórica y actual de P30/P40 en México.
-- Se reportan conteos agregados, no filas individuales.
-- Modo de entrega: presentation.

SELECT
    compensation_grade,
    COUNT(*) AS worker_month_rows,
    COUNT(DISTINCT employee_id) AS employee_count,
    COUNT(DISTINCT CASE WHEN fte_annual_base_pay IS NOT NULL AND fte_annual_base_pay > 0 THEN employee_id END) AS employees_with_positive_pay,
    MIN(fis_mo_end_dt) AS first_snapshot,
    MAX(fis_mo_end_dt) AS last_snapshot
FROM hrda.post_hire_monthly_worker_dtls
WHERE LOWER(COALESCE(country, '')) = 'mexico'
  AND compensation_grade IN ('P30', 'P40')
  AND worker_type = 'Employee'
  AND employee_type = 'Regular'
GROUP BY 1
ORDER BY compensation_grade;
