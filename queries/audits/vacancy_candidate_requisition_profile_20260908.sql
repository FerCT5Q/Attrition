/*
  Perfil agregado de fuentes candidatas de vacantes/requisiciones.
  Entregable: internal_analysis exploratorio.
  No devuelve req_id ni otras claves; sólo métricas agregadas.
*/
WITH source_metrics AS (
    SELECT
        'requisitions' AS source_table,
        COUNT(*) AS row_count,
        COUNT(req_id) AS req_id_populated_rows,
        COUNT(DISTINCT req_id) AS distinct_req_ids,
        COUNT(*) - COUNT(DISTINCT req_id) AS duplicate_rows_vs_req_id,
        MIN(date_request_entered) AS min_request_date,
        MAX(last_modified_date) AS max_last_modified_date,
        MIN(recruiting_start_date) AS min_recruiting_start_date,
        MAX(recruiting_start_date) AS max_recruiting_start_date,
        MIN(close_date) AS min_close_date,
        MAX(close_date) AS max_close_date,
        SUM(CASE WHEN openings_available IS NOT NULL THEN 1 ELSE 0 END) AS openings_available_rows,
        SUM(CASE WHEN openings_total IS NOT NULL THEN 1 ELSE 0 END) AS openings_total_rows,
        SUM(CASE WHEN job_requisition_status IS NOT NULL THEN 1 ELSE 0 END) AS requisition_status_rows,
        SUM(CASE WHEN job_req_status IS NOT NULL THEN 1 ELSE 0 END) AS req_status_rows
    FROM hrda.requisitions

    UNION ALL

    SELECT
        'requisitions_vw' AS source_table,
        COUNT(*) AS row_count,
        COUNT(req_id) AS req_id_populated_rows,
        COUNT(DISTINCT req_id) AS distinct_req_ids,
        COUNT(*) - COUNT(DISTINCT req_id) AS duplicate_rows_vs_req_id,
        MIN(date_request_entered) AS min_request_date,
        MAX(last_modified_date) AS max_last_modified_date,
        MIN(recruiting_start_date) AS min_recruiting_start_date,
        MAX(recruiting_start_date) AS max_recruiting_start_date,
        MIN(close_date) AS min_close_date,
        MAX(close_date) AS max_close_date,
        SUM(CASE WHEN openings_available IS NOT NULL THEN 1 ELSE 0 END) AS openings_available_rows,
        SUM(CASE WHEN openings_total IS NOT NULL THEN 1 ELSE 0 END) AS openings_total_rows,
        SUM(CASE WHEN job_requisition_status IS NOT NULL THEN 1 ELSE 0 END) AS requisition_status_rows,
        SUM(CASE WHEN job_req_status IS NOT NULL THEN 1 ELSE 0 END) AS req_status_rows
    FROM hrda.requisitions_vw
), status_metrics AS (
    SELECT
        'requisitions' AS source_table,
        'job_requisition_status' AS status_field,
        COALESCE(NULLIF(TRIM(job_requisition_status), ''), '<NULL_OR_BLANK>') AS status_value,
        COUNT(*) AS row_count,
        COUNT(DISTINCT req_id) AS distinct_req_ids
    FROM hrda.requisitions
    GROUP BY 1, 2, 3

    UNION ALL

    SELECT
        'requisitions' AS source_table,
        'job_req_status' AS status_field,
        COALESCE(NULLIF(TRIM(job_req_status), ''), '<NULL_OR_BLANK>') AS status_value,
        COUNT(*) AS row_count,
        COUNT(DISTINCT req_id) AS distinct_req_ids
    FROM hrda.requisitions
    GROUP BY 1, 2, 3

    UNION ALL

    SELECT
        'requisitions_vw' AS source_table,
        'job_requisition_status' AS status_field,
        COALESCE(NULLIF(TRIM(job_requisition_status), ''), '<NULL_OR_BLANK>') AS status_value,
        COUNT(*) AS row_count,
        COUNT(DISTINCT req_id) AS distinct_req_ids
    FROM hrda.requisitions_vw
    GROUP BY 1, 2, 3

    UNION ALL

    SELECT
        'requisitions_vw' AS source_table,
        'job_req_status' AS status_field,
        COALESCE(NULLIF(TRIM(job_req_status), ''), '<NULL_OR_BLANK>') AS status_value,
        COUNT(*) AS row_count,
        COUNT(DISTINCT req_id) AS distinct_req_ids
    FROM hrda.requisitions_vw
    GROUP BY 1, 2, 3
)
SELECT
    'source_profile' AS result_type,
    source_table,
    CAST(NULL AS VARCHAR(80)) AS status_field,
    CAST(NULL AS VARCHAR(200)) AS status_value,
    row_count,
    req_id_populated_rows,
    distinct_req_ids,
    duplicate_rows_vs_req_id,
    min_request_date,
    max_last_modified_date,
    min_recruiting_start_date,
    max_recruiting_start_date,
    min_close_date,
    max_close_date,
    openings_available_rows,
    openings_total_rows,
    requisition_status_rows,
    req_status_rows
FROM source_metrics

UNION ALL

SELECT
    'status_distribution' AS result_type,
    source_table,
    status_field,
    status_value,
    row_count,
    NULL AS req_id_populated_rows,
    distinct_req_ids,
    NULL AS duplicate_rows_vs_req_id,
    NULL AS min_request_date,
    NULL AS max_last_modified_date,
    NULL AS min_recruiting_start_date,
    NULL AS max_recruiting_start_date,
    NULL AS min_close_date,
    NULL AS max_close_date,
    NULL AS openings_available_rows,
    NULL AS openings_total_rows,
    NULL AS requisition_status_rows,
    NULL AS req_status_rows
FROM status_metrics
ORDER BY result_type, source_table, status_field, row_count DESC;
