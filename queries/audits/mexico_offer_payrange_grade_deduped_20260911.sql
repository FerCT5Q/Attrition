-- Propósito: estimar rangos configurados por requisición, evitando que una
-- misma banda se pese varias veces por candidato o etapa de oferta.
-- Modo de entrega: presentation; no devuelve identificadores.

WITH source_rows AS (
    SELECT
        compensation_grade_pa,
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
      AND NULLIF(TRIM(CAST(req_id AS VARCHAR)), '') IS NOT NULL
), candidate_counts AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        COUNT(DISTINCT candidate_id) AS candidate_count,
        COUNT(DISTINCT req_id) AS requisition_count,
        MIN(last_modified_date) AS earliest_offer_date,
        MAX(last_modified_date) AS latest_offer_date
    FROM source_rows
    GROUP BY 1, 2, 3, 4
), ranked_req_rows AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        req_id,
        min_payrange,
        mid_payrange,
        max_payrange,
        last_modified_date,
        ROW_NUMBER() OVER (
            PARTITION BY req_id
            ORDER BY last_modified_date DESC
        ) AS req_row_rank
    FROM source_rows
), latest_req_rows AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        req_id,
        min_payrange,
        mid_payrange,
        max_payrange,
        last_modified_date
    FROM ranked_req_rows
    WHERE req_row_rank = 1
), complete_req_ranges AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        req_id,
        min_payrange,
        mid_payrange,
        max_payrange,
        last_modified_date
    FROM latest_req_rows
    WHERE min_payrange IS NOT NULL
      AND mid_payrange IS NOT NULL
      AND max_payrange IS NOT NULL
), req_percentiles_min AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        COUNT(*) AS complete_requisition_ranges,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY min_payrange) AS p25_min_payrange,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY min_payrange) AS p50_min_payrange,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY min_payrange) AS p75_min_payrange
    FROM complete_req_ranges
    GROUP BY 1, 2, 3, 4
), req_percentiles_mid AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY mid_payrange) AS p25_mid_payrange,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY mid_payrange) AS p50_mid_payrange,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY mid_payrange) AS p75_mid_payrange
    FROM complete_req_ranges
    GROUP BY 1, 2, 3, 4
), req_percentiles_max AS (
    SELECT
        compensation_grade_pa,
        city,
        base_pay_amount_currency_code,
        base_pay_anualized_amt_currency_code,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY max_payrange) AS p25_max_payrange,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY max_payrange) AS p50_max_payrange,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY max_payrange) AS p75_max_payrange
    FROM complete_req_ranges
    GROUP BY 1, 2, 3, 4
)
SELECT
    c.compensation_grade_pa,
    c.city,
    c.base_pay_amount_currency_code,
    c.base_pay_anualized_amt_currency_code,
    c.candidate_count,
    c.requisition_count,
    c.earliest_offer_date,
    c.latest_offer_date,
    p.complete_requisition_ranges,
    p.p25_min_payrange,
    p.p50_min_payrange,
    p.p75_min_payrange,
    m.p25_mid_payrange,
    m.p50_mid_payrange,
    m.p75_mid_payrange,
    x.p25_max_payrange,
    x.p50_max_payrange,
    x.p75_max_payrange
FROM candidate_counts c
INNER JOIN req_percentiles_min p
    ON c.compensation_grade_pa = p.compensation_grade_pa
   AND COALESCE(c.city, '') = COALESCE(p.city, '')
   AND COALESCE(c.base_pay_amount_currency_code, '') = COALESCE(p.base_pay_amount_currency_code, '')
   AND COALESCE(c.base_pay_anualized_amt_currency_code, '') = COALESCE(p.base_pay_anualized_amt_currency_code, '')
INNER JOIN req_percentiles_mid m
    ON c.compensation_grade_pa = m.compensation_grade_pa
   AND COALESCE(c.city, '') = COALESCE(m.city, '')
   AND COALESCE(c.base_pay_amount_currency_code, '') = COALESCE(m.base_pay_amount_currency_code, '')
   AND COALESCE(c.base_pay_anualized_amt_currency_code, '') = COALESCE(m.base_pay_anualized_amt_currency_code, '')
INNER JOIN req_percentiles_max x
    ON c.compensation_grade_pa = x.compensation_grade_pa
   AND COALESCE(c.city, '') = COALESCE(x.city, '')
   AND COALESCE(c.base_pay_amount_currency_code, '') = COALESCE(x.base_pay_amount_currency_code, '')
   AND COALESCE(c.base_pay_anualized_amt_currency_code, '') = COALESCE(x.base_pay_anualized_amt_currency_code, '')
ORDER BY c.compensation_grade_pa, c.city;
