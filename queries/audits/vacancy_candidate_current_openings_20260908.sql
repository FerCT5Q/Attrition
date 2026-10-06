/*
  Validación agregada de vacantes actuales en requisitions_vw.
  Entregable: internal_analysis exploratorio.
  No devuelve req_id, nombres, descripciones ni filas individuales.
*/
WITH base AS (
    SELECT
        req_id,
        COALESCE(NULLIF(TRIM(job_req_status), ''), NULLIF(TRIM(job_requisition_status), ''), '<NULL_OR_BLANK>') AS requisition_status,
        COALESCE(openings_available, number_of_openings_available, 0) AS openings_available,
        COALESCE(openings_total, number_of_openings_total, 0) AS openings_total,
        COALESCE(number_of_openings_filled, 0) AS openings_filled,
        job_family_group,
        job_family_group_short,
        job_requisition_primary_location,
        job_posted_internally,
        job_posted_externally,
        recruiting_start_date,
        target_hire_date,
        close_date,
        last_modified_date,
        job_requisition_status,
        job_req_status
    FROM hrda.requisitions_vw
), current_open AS (
    SELECT
        req_id,
        requisition_status,
        openings_available,
        openings_total,
        openings_filled,
        job_family_group,
        job_family_group_short,
        job_requisition_primary_location,
        job_posted_internally,
        job_posted_externally,
        recruiting_start_date,
        target_hire_date,
        close_date,
        last_modified_date,
        job_requisition_status,
        job_req_status
    FROM base
    WHERE requisition_status = 'Open'
), status_summary AS (
    SELECT
        'status_summary' AS result_type,
        requisition_status AS category_1,
        CAST(NULL AS VARCHAR(200)) AS category_2,
        COUNT(*) AS requisition_count,
        SUM(CASE WHEN openings_available > 0 THEN 1 ELSE 0 END) AS reqs_with_positive_openings,
        SUM(openings_available) AS openings_available_total,
        SUM(openings_total) AS openings_total_sum,
        SUM(openings_filled) AS openings_filled_sum,
        MIN(last_modified_date) AS min_last_modified_date,
        MAX(last_modified_date) AS max_last_modified_date,
        MIN(recruiting_start_date) AS min_recruiting_start_date,
        MAX(recruiting_start_date) AS max_recruiting_start_date,
        MIN(target_hire_date) AS min_target_hire_date,
        MAX(target_hire_date) AS max_target_hire_date,
        MIN(close_date) AS min_close_date,
        MAX(close_date) AS max_close_date
    FROM base
    GROUP BY 1, 2
), openings_bands AS (
    SELECT
        'openings_band_current_open' AS result_type,
        CASE
            WHEN openings_available IS NULL THEN '<NULL>'
            WHEN openings_available <= 0 THEN '0'
            WHEN openings_available = 1 THEN '1'
            WHEN openings_available BETWEEN 2 AND 4 THEN '2-4'
            ELSE '5+'
        END AS category_1,
        CAST(NULL AS VARCHAR(200)) AS category_2,
        COUNT(*) AS requisition_count,
        SUM(CASE WHEN openings_available > 0 THEN 1 ELSE 0 END) AS reqs_with_positive_openings,
        SUM(openings_available) AS openings_available_total,
        SUM(openings_total) AS openings_total_sum,
        SUM(openings_filled) AS openings_filled_sum,
        MIN(last_modified_date) AS min_last_modified_date,
        MAX(last_modified_date) AS max_last_modified_date,
        MIN(recruiting_start_date) AS min_recruiting_start_date,
        MAX(recruiting_start_date) AS max_recruiting_start_date,
        MIN(target_hire_date) AS min_target_hire_date,
        MAX(target_hire_date) AS max_target_hire_date,
        MIN(close_date) AS min_close_date,
        MAX(close_date) AS max_close_date
    FROM current_open
    GROUP BY 1, 2
), family_summary AS (
    SELECT
        'current_open_by_job_family_group' AS result_type,
        COALESCE(NULLIF(TRIM(job_family_group), ''), '<NULL_OR_BLANK>') AS category_1,
        COALESCE(NULLIF(TRIM(job_family_group_short), ''), '<NULL_OR_BLANK>') AS category_2,
        COUNT(*) AS requisition_count,
        SUM(CASE WHEN openings_available > 0 THEN 1 ELSE 0 END) AS reqs_with_positive_openings,
        SUM(openings_available) AS openings_available_total,
        SUM(openings_total) AS openings_total_sum,
        SUM(openings_filled) AS openings_filled_sum,
        MIN(last_modified_date) AS min_last_modified_date,
        MAX(last_modified_date) AS max_last_modified_date,
        MIN(recruiting_start_date) AS min_recruiting_start_date,
        MAX(recruiting_start_date) AS max_recruiting_start_date,
        MIN(target_hire_date) AS min_target_hire_date,
        MAX(target_hire_date) AS max_target_hire_date,
        MIN(close_date) AS min_close_date,
        MAX(close_date) AS max_close_date
    FROM current_open
    GROUP BY 1, 2, 3
    HAVING COUNT(*) >= 30
), location_summary AS (
    SELECT
        'current_open_by_location' AS result_type,
        COALESCE(NULLIF(TRIM(job_requisition_primary_location), ''), '<NULL_OR_BLANK>') AS category_1,
        CAST(NULL AS VARCHAR(200)) AS category_2,
        COUNT(*) AS requisition_count,
        SUM(CASE WHEN openings_available > 0 THEN 1 ELSE 0 END) AS reqs_with_positive_openings,
        SUM(openings_available) AS openings_available_total,
        SUM(openings_total) AS openings_total_sum,
        SUM(openings_filled) AS openings_filled_sum,
        MIN(last_modified_date) AS min_last_modified_date,
        MAX(last_modified_date) AS max_last_modified_date,
        MIN(recruiting_start_date) AS min_recruiting_start_date,
        MAX(recruiting_start_date) AS max_recruiting_start_date,
        MIN(target_hire_date) AS min_target_hire_date,
        MAX(target_hire_date) AS max_target_hire_date,
        MIN(close_date) AS min_close_date,
        MAX(close_date) AS max_close_date
    FROM current_open
    GROUP BY 1, 2
    HAVING COUNT(*) >= 30
)
SELECT result_type, category_1, category_2, requisition_count,
       reqs_with_positive_openings, openings_available_total,
       openings_total_sum, openings_filled_sum, min_last_modified_date,
       max_last_modified_date, min_recruiting_start_date,
       max_recruiting_start_date, min_target_hire_date, max_target_hire_date,
       min_close_date, max_close_date
FROM status_summary
UNION ALL
SELECT result_type, category_1, category_2, requisition_count,
       reqs_with_positive_openings, openings_available_total,
       openings_total_sum, openings_filled_sum, min_last_modified_date,
       max_last_modified_date, min_recruiting_start_date,
       max_recruiting_start_date, min_target_hire_date, max_target_hire_date,
       min_close_date, max_close_date
FROM openings_bands
UNION ALL
SELECT result_type, category_1, category_2, requisition_count,
       reqs_with_positive_openings, openings_available_total,
       openings_total_sum, openings_filled_sum, min_last_modified_date,
       max_last_modified_date, min_recruiting_start_date,
       max_recruiting_start_date, min_target_hire_date, max_target_hire_date,
       min_close_date, max_close_date
FROM family_summary
UNION ALL
SELECT result_type, category_1, category_2, requisition_count,
       reqs_with_positive_openings, openings_available_total,
       openings_total_sum, openings_filled_sum, min_last_modified_date,
       max_last_modified_date, min_recruiting_start_date,
       max_recruiting_start_date, min_target_hire_date, max_target_hire_date,
       min_close_date, max_close_date
FROM location_summary
ORDER BY result_type, requisition_count DESC, category_1;
