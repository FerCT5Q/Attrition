-- Propósito: revisar si el catálogo interno fully_loaded_cost tiene un
-- midpoint por grade para México. Es costo total cargado, no salario base;
-- se mantiene separado de la banda salarial.
-- Modo de entrega: presentation.

WITH eligible AS (
    SELECT
        compensation_grade,
        country,
        currency,
        labor_market,
        job_code,
        data_as_of,
        midpoint_usd
    FROM hrda.fully_loaded_cost
    WHERE LOWER(COALESCE(country, '')) = 'mexico'
      AND compensation_grade IN ('P30', 'P40')
      AND midpoint_usd IS NOT NULL
), counts AS (
    SELECT
        compensation_grade,
        country,
        currency,
        labor_market,
        COUNT(*) AS catalog_rows,
        COUNT(DISTINCT job_code) AS job_code_count,
        MIN(data_as_of) AS earliest_data_as_of,
        MAX(data_as_of) AS latest_data_as_of
    FROM eligible
    GROUP BY 1, 2, 3, 4
), percentiles AS (
    SELECT
        compensation_grade,
        country,
        currency,
        labor_market,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY midpoint_usd) AS p25_midpoint_usd,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY midpoint_usd) AS p50_midpoint_usd,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY midpoint_usd) AS p75_midpoint_usd
    FROM eligible
    GROUP BY 1, 2, 3, 4
)
SELECT
    c.compensation_grade,
    c.country,
    c.currency,
    c.labor_market,
    c.catalog_rows,
    c.job_code_count,
    c.earliest_data_as_of,
    c.latest_data_as_of,
    p.p25_midpoint_usd,
    p.p50_midpoint_usd,
    p.p75_midpoint_usd
FROM counts c
INNER JOIN percentiles p
    ON c.compensation_grade = p.compensation_grade
   AND c.country = p.country
   AND c.currency = p.currency
   AND c.labor_market = p.labor_market
ORDER BY c.compensation_grade, c.labor_market;
