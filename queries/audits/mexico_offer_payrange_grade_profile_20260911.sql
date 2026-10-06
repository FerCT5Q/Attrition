-- Propósito: verificar si las ofertas internas contienen una banda
-- min/mid/max para P30/P40 en México. Sólo resultados agregados.
-- Modo de entrega: presentation.

WITH eligible AS (
    SELECT
        compensation_grade_pa,
        country,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        candidate_id,
        req_id,
        min_payrange,
        mid_payrange,
        max_payrange,
        last_modified_date
    FROM hrda.offers_new
    WHERE LOWER(COALESCE(country, '')) = 'mexico'
      AND compensation_grade_pa IN ('P30', 'P40')
), counts AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        COUNT(*) AS offer_rows,
        COUNT(DISTINCT candidate_id) AS candidate_count,
        COUNT(DISTINCT req_id) AS requisition_count,
        SUM(CASE WHEN min_payrange IS NOT NULL AND mid_payrange IS NOT NULL AND max_payrange IS NOT NULL THEN 1 ELSE 0 END) AS complete_payrange_rows,
        MIN(last_modified_date) AS earliest_offer_date,
        MAX(last_modified_date) AS latest_offer_date
    FROM eligible
    GROUP BY 1, 2, 3, 4
), min_percentiles AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY min_payrange) AS p25_min_payrange,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY min_payrange) AS p50_min_payrange,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY min_payrange) AS p75_min_payrange
    FROM eligible
    GROUP BY 1, 2, 3, 4
), mid_percentiles AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY mid_payrange) AS p25_mid_payrange,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY mid_payrange) AS p50_mid_payrange,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY mid_payrange) AS p75_mid_payrange
    FROM eligible
    GROUP BY 1, 2, 3, 4
), max_percentiles AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY max_payrange) AS p25_max_payrange,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY max_payrange) AS p50_max_payrange,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY max_payrange) AS p75_max_payrange
    FROM eligible
    GROUP BY 1, 2, 3, 4
)
SELECT
    c.compensation_grade_pa,
    c.city,
    c.base_pay_amount_currency_code,
    c.base_pay_anualized_amt_currency_code,
    c.offer_rows,
    c.candidate_count,
    c.requisition_count,
    c.complete_payrange_rows,
    c.earliest_offer_date,
    c.latest_offer_date,
    p.p25_min_payrange,
    p.p50_min_payrange,
    p.p75_min_payrange,
    mp.p25_mid_payrange,
    mp.p50_mid_payrange,
    mp.p75_mid_payrange,
    xp.p25_max_payrange,
    xp.p50_max_payrange,
    xp.p75_max_payrange
FROM counts c
LEFT JOIN min_percentiles p
    ON c.compensation_grade_pa = p.compensation_grade_pa
   AND COALESCE(c.city, '') = COALESCE(p.city, '')
   AND COALESCE(c.base_pay_amount_currency_code, '') = COALESCE(p.base_pay_amount_currency_code, '')
   AND COALESCE(c.base_pay_anualized_amt_currency_code, '') = COALESCE(p.base_pay_anualized_amt_currency_code, '')
LEFT JOIN mid_percentiles mp
    ON c.compensation_grade_pa = mp.compensation_grade_pa
   AND COALESCE(c.city, '') = COALESCE(mp.city, '')
   AND COALESCE(c.base_pay_amount_currency_code, '') = COALESCE(mp.base_pay_amount_currency_code, '')
   AND COALESCE(c.base_pay_anualized_amt_currency_code, '') = COALESCE(mp.base_pay_anualized_amt_currency_code, '')
LEFT JOIN max_percentiles xp
    ON c.compensation_grade_pa = xp.compensation_grade_pa
   AND COALESCE(c.city, '') = COALESCE(xp.city, '')
   AND COALESCE(c.base_pay_amount_currency_code, '') = COALESCE(xp.base_pay_amount_currency_code, '')
   AND COALESCE(c.base_pay_anualized_amt_currency_code, '') = COALESCE(xp.base_pay_anualized_amt_currency_code, '')
ORDER BY c.compensation_grade_pa, c.city;
