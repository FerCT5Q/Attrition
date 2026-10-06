/*
  Reconciliación agregada de estado y aperturas en requisitions_vw.
  Afirmación: los campos de estado y apertura describen de forma consistente
  una requisición actual y openings_available = openings_total - openings_filled
  cuando los tres componentes están disponibles.
*/
WITH base AS (
    SELECT
        req_id,
        NULLIF(TRIM(job_req_status), '') AS req_status,
        NULLIF(TRIM(job_requisition_status), '') AS requisition_status,
        openings_available,
        number_of_openings_available,
        openings_total,
        number_of_openings_total,
        number_of_openings_filled,
        last_modified_date
    FROM hrda.requisitions_vw
), normalized AS (
    SELECT
        req_id,
        req_status,
        requisition_status,
        COALESCE(openings_available, number_of_openings_available) AS available_n,
        COALESCE(openings_total, number_of_openings_total) AS total_n,
        number_of_openings_filled AS filled_n,
        last_modified_date
    FROM base
), checks AS (
    SELECT
        COUNT(*) AS eligible_rows,
        COUNT(DISTINCT req_id) AS eligible_req_ids,
        SUM(CASE WHEN req_status IS NOT NULL AND requisition_status IS NOT NULL AND req_status = requisition_status THEN 1 ELSE 0 END) AS status_exact_match_rows,
        SUM(CASE WHEN req_status IS NOT NULL AND requisition_status IS NOT NULL AND req_status <> requisition_status THEN 1 ELSE 0 END) AS status_mismatch_rows,
        SUM(CASE WHEN (req_status IS NULL) <> (requisition_status IS NULL) THEN 1 ELSE 0 END) AS status_one_sided_null_rows,
        SUM(CASE WHEN req_status IS NULL AND requisition_status IS NULL THEN 1 ELSE 0 END) AS status_both_null_rows,
        SUM(CASE WHEN available_n IS NOT NULL THEN 1 ELSE 0 END) AS available_populated_rows,
        SUM(CASE WHEN total_n IS NOT NULL THEN 1 ELSE 0 END) AS total_populated_rows,
        SUM(CASE WHEN filled_n IS NOT NULL THEN 1 ELSE 0 END) AS filled_populated_rows,
        SUM(CASE WHEN available_n IS NOT NULL AND total_n IS NOT NULL AND filled_n IS NOT NULL
                      AND total_n - filled_n = available_n THEN 1 ELSE 0 END) AS formula_match_rows,
        SUM(CASE WHEN available_n IS NOT NULL AND total_n IS NOT NULL AND filled_n IS NOT NULL
                      AND total_n - filled_n <> available_n THEN 1 ELSE 0 END) AS formula_mismatch_rows,
        SUM(CASE WHEN available_n IS NOT NULL AND total_n IS NOT NULL AND available_n > total_n THEN 1 ELSE 0 END) AS available_gt_total_rows,
        SUM(CASE WHEN filled_n IS NOT NULL AND total_n IS NOT NULL AND filled_n > total_n THEN 1 ELSE 0 END) AS filled_gt_total_rows,
        MIN(last_modified_date) AS min_last_modified_date,
        MAX(last_modified_date) AS max_last_modified_date
    FROM normalized
)
SELECT
    'reconciliation' AS result_type,
    eligible_rows,
    eligible_req_ids,
    status_exact_match_rows,
    status_mismatch_rows,
    status_one_sided_null_rows,
    status_both_null_rows,
    available_populated_rows,
    total_populated_rows,
    filled_populated_rows,
    formula_match_rows,
    formula_mismatch_rows,
    available_gt_total_rows,
    filled_gt_total_rows,
    min_last_modified_date,
    max_last_modified_date
FROM checks;
