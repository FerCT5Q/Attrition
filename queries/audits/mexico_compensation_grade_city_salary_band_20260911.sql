-- Propósito: estimar bandas por ciudad sólo cuando la ciudad-grade tiene
-- al menos 30 empleados distintos.
-- Modo de entrega: presentation; no devuelve identificadores ni valores
-- individuales. Si no hay filas, no se publica una variante ciudad-grade.

WITH eligible AS (
    SELECT
        compensation_grade,
        employee_id,
        city,
        fte_annual_base_pay,
        last_modified_date
    FROM hrda.worker_details_latest
    WHERE LOWER(COALESCE(country, '')) = 'mexico'
      AND compensation_grade IN ('P30', 'P40')
      AND employee_type = 'Regular'
      AND worker_type = 'Employee'
      AND active_status = 1
      AND fte_annual_base_pay_currency_code = 'MXN'
      AND fte_annual_base_pay > 0
), city_counts AS (
    SELECT
        compensation_grade,
        city,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS eligible_rows
    FROM eligible
    GROUP BY 1, 2
), city_percentiles AS (
    SELECT
        compensation_grade,
        city,
        MAX(last_modified_date) AS latest_source_date,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY fte_annual_base_pay) AS p25_annual_mxn,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY fte_annual_base_pay) AS p50_annual_mxn,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY fte_annual_base_pay) AS p75_annual_mxn
    FROM eligible
    GROUP BY 1, 2
)
SELECT
    c.compensation_grade,
    c.city,
    c.employee_count,
    c.eligible_rows,
    p.latest_source_date,
    ROUND(p.p25_annual_mxn / 12.0, -3) AS p25_monthly_mxn,
    ROUND(p.p50_annual_mxn / 12.0, -3) AS p50_monthly_mxn,
    ROUND(p.p75_annual_mxn / 12.0, -3) AS p75_monthly_mxn
FROM city_counts c
INNER JOIN city_percentiles p
    ON c.compensation_grade = p.compensation_grade
   AND c.city = p.city
WHERE c.employee_count >= 30
ORDER BY c.compensation_grade, c.city;
