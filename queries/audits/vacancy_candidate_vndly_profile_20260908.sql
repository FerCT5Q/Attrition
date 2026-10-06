/*
  Perfil agregado de requisiciones VNDLY.
  Entregable: internal_analysis exploratorio.
  No devuelve IDs, nombres ni tarifas individuales.
*/
WITH base AS (
    SELECT
        tdw_j_sourcing_doc_id,
        COALESCE(NULLIF(TRIM(tdw_j_status), ''), '<NULL_OR_BLANK>') AS requisition_status,
        COALESCE(tdw_j_number_of_positions_requested, 0) AS positions_requested,
        tdw_j_country,
        tdw_j_state,
        tdw_j_job_type,
        tdw_j_hire_type,
        tdw_j_create_date,
        tdw_j_approved_date,
        tdw_j_start_date,
        tdw_j_end_date,
        last_modified_date
    FROM hrda.vndly_requisition
), status_summary AS (
    SELECT
        requisition_status,
        COUNT(*) AS requisition_count,
        COUNT(DISTINCT tdw_j_sourcing_doc_id) AS distinct_requisition_ids,
        SUM(CASE WHEN positions_requested > 0 THEN 1 ELSE 0 END) AS positive_position_rows,
        SUM(positions_requested) AS positions_requested_total,
        MIN(tdw_j_create_date) AS min_create_date,
        MAX(tdw_j_create_date) AS max_create_date,
        MIN(last_modified_date) AS min_last_modified_date,
        MAX(last_modified_date) AS max_last_modified_date,
        MIN(tdw_j_start_date) AS min_start_date,
        MAX(tdw_j_start_date) AS max_start_date
    FROM base
    GROUP BY 1
), country_summary AS (
    SELECT
        COALESCE(NULLIF(TRIM(tdw_j_country), ''), '<NULL_OR_BLANK>') AS country,
        COUNT(*) AS requisition_count,
        COUNT(DISTINCT tdw_j_sourcing_doc_id) AS distinct_requisition_ids,
        SUM(CASE WHEN positions_requested > 0 THEN 1 ELSE 0 END) AS positive_position_rows,
        SUM(positions_requested) AS positions_requested_total
    FROM base
    GROUP BY 1
    HAVING COUNT(*) >= 30
)
SELECT
    'status_summary' AS result_type,
    requisition_status AS category,
    requisition_count,
    distinct_requisition_ids,
    positive_position_rows,
    positions_requested_total,
    min_create_date,
    max_create_date,
    min_last_modified_date,
    max_last_modified_date,
    min_start_date,
    max_start_date
FROM status_summary
UNION ALL
SELECT
    'country_summary' AS result_type,
    country AS category,
    requisition_count,
    distinct_requisition_ids,
    positive_position_rows,
    positions_requested_total,
    NULL AS min_create_date,
    NULL AS max_create_date,
    NULL AS min_last_modified_date,
    NULL AS max_last_modified_date,
    NULL AS min_start_date,
    NULL AS max_start_date
FROM country_summary
ORDER BY result_type, requisition_count DESC, category;
