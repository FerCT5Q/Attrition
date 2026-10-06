-- Propósito: estimar bandas agregadas de compensación para grades internos
-- de México usando el snapshot más reciente disponible por trabajador.
-- Población: Employee + Regular + active_status=1 + moneda MXN + pago FTE
-- anualizado positivo. No devuelve identificadores ni valores individuales.
-- Regla de aceptación: publicar sólo grades con >=30 empleados distintos.
-- Modo de entrega: presentation.

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
), grade_counts AS (
    SELECT
        compensation_grade,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS eligible_rows
    FROM eligible
    GROUP BY 1
), grade_percentiles AS (
    SELECT
        compensation_grade,
        MAX(last_modified_date) AS latest_source_date,
        PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY fte_annual_base_pay) AS p10_annual_mxn,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY fte_annual_base_pay) AS p25_annual_mxn,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY fte_annual_base_pay) AS p50_annual_mxn,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY fte_annual_base_pay) AS p75_annual_mxn,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY fte_annual_base_pay) AS p90_annual_mxn
    FROM eligible
    GROUP BY 1
), grade_stats AS (
    SELECT
        c.compensation_grade,
        c.employee_count,
        c.eligible_rows,
        p.latest_source_date,
        p.p10_annual_mxn,
        p.p25_annual_mxn,
        p.p50_annual_mxn,
        p.p75_annual_mxn,
        p.p90_annual_mxn
    FROM grade_counts c
    INNER JOIN grade_percentiles p
        ON c.compensation_grade = p.compensation_grade
    WHERE c.employee_count >= 30
)
SELECT
    compensation_grade,
    employee_count,
    eligible_rows,
    latest_source_date,
    ROUND(p10_annual_mxn / 12.0, -3) AS p10_monthly_mxn,
    ROUND(p25_annual_mxn / 12.0, -3) AS p25_monthly_mxn,
    ROUND(p50_annual_mxn / 12.0, -3) AS p50_monthly_mxn,
    ROUND(p75_annual_mxn / 12.0, -3) AS p75_monthly_mxn,
    ROUND(p90_annual_mxn / 12.0, -3) AS p90_monthly_mxn
FROM grade_stats
ORDER BY compensation_grade;
