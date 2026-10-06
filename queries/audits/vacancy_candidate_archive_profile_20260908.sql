/* Perfil agregado del archivo de requisiciones rescindidas. */
SELECT
    COUNT(*) AS row_count,
    COUNT(req_id) AS req_id_populated_rows,
    COUNT(DISTINCT req_id) AS distinct_req_ids,
    COUNT(*) - COUNT(DISTINCT req_id) AS duplicate_rows_vs_req_id,
    MIN(archive_date) AS min_archive_date,
    MAX(archive_date) AS max_archive_date,
    MIN(last_modified_date) AS min_last_modified_date,
    MAX(last_modified_date) AS max_last_modified_date,
    SUM(CASE WHEN openings_available > 0 THEN 1 ELSE 0 END) AS positive_openings_rows,
    SUM(CASE WHEN job_requisition_status = 'Open' OR job_req_status = 'Open' THEN 1 ELSE 0 END) AS open_status_rows
FROM hrda.requisitions_rescinds_archive;
