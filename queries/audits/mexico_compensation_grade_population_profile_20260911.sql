-- Propósito: perfilar la población interna disponible para estimar P30/P40
-- en México, con conteos agregados por ciudad y moneda.
-- Modo de entrega: presentation; no devuelve identificadores.

SELECT
    compensation_grade,
    country,
    city,
    fte_annual_base_pay_currency_code,
    base_pay_frequency,
    employee_type,
    worker_type,
    active_status,
    COUNT(*) AS worker_rows,
    COUNT(DISTINCT employee_id) AS employee_count,
    SUM(CASE WHEN fte_annual_base_pay IS NOT NULL AND fte_annual_base_pay > 0 THEN 1 ELSE 0 END) AS rows_with_positive_fte_pay
FROM hrda.worker_details_latest
WHERE LOWER(COALESCE(country, '')) = 'mexico'
  AND compensation_grade IN ('P30', 'P40')
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
ORDER BY compensation_grade, city, employee_count DESC;
