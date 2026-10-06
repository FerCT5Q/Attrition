-- Propósito: validar la unidad de min/mid/max payrange comparándola con
-- base_pay_amount y base_pay_anualized_amt; resultados agregados.
-- Modo de entrega: presentation.

WITH eligible AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount,
        base_pay_anualized_amt,
        min_payrange,
        mid_payrange,
        max_payrange
    FROM hrda.offers_new
    WHERE LOWER(COALESCE(country, '')) = 'mexico'
      AND compensation_grade_pa IN ('P30', 'P40')
      AND base_pay_amount IS NOT NULL
      AND base_pay_anualized_amt IS NOT NULL
), base_amount_pct AS (
    SELECT
        compensation_grade_pa,
        city,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY base_pay_amount) AS p50_base_pay_amount
    FROM eligible
    GROUP BY 1, 2
), annualized_pct AS (
    SELECT
        compensation_grade_pa,
        city,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY base_pay_anualized_amt) AS p50_base_pay_anualized_amt
    FROM eligible
    GROUP BY 1, 2
), range_pct AS (
    SELECT
        compensation_grade_pa,
        city,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY mid_payrange) AS p50_mid_payrange
    FROM eligible
    GROUP BY 1, 2
)
SELECT
    b.compensation_grade_pa,
    b.city,
    b.p50_base_pay_amount,
    a.p50_base_pay_anualized_amt,
    r.p50_mid_payrange,
    a.p50_base_pay_anualized_amt / NULLIF(b.p50_base_pay_amount, 0) AS annualized_to_base_ratio
FROM base_amount_pct b
INNER JOIN annualized_pct a
    ON b.compensation_grade_pa = a.compensation_grade_pa
   AND COALESCE(b.city, '') = COALESCE(a.city, '')
INNER JOIN range_pct r
    ON b.compensation_grade_pa = r.compensation_grade_pa
   AND COALESCE(b.city, '') = COALESCE(r.city, '')
ORDER BY b.compensation_grade_pa, b.city;
