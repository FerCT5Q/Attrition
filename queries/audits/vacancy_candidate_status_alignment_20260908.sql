/* Reconciliación explícita de los dos estados de requisición. */
SELECT
    COUNT(*) AS eligible_rows,
    COUNT(DISTINCT req_id) AS eligible_req_ids,
    SUM(CASE WHEN job_req_status = 'Open' THEN 1 ELSE 0 END) AS req_status_open_rows,
    SUM(CASE WHEN job_requisition_status = 'Open' THEN 1 ELSE 0 END) AS requisition_status_open_rows,
    SUM(CASE WHEN job_req_status = 'Open' AND job_requisition_status = 'Open' THEN 1 ELSE 0 END) AS both_open_rows,
    SUM(CASE WHEN job_req_status = 'Open' AND job_requisition_status <> 'Open' THEN 1 ELSE 0 END) AS req_open_requisition_not_open_rows,
    SUM(CASE WHEN job_req_status <> 'Open' AND job_requisition_status = 'Open' THEN 1 ELSE 0 END) AS req_not_open_requisition_open_rows,
    SUM(CASE WHEN job_req_status = 'Filled (Future Start)' AND job_requisition_status = 'Open' THEN 1 ELSE 0 END) AS future_start_vs_open_rows,
    SUM(CASE WHEN job_req_status <> job_requisition_status THEN 1 ELSE 0 END) AS any_status_mismatch_rows
FROM hrda.requisitions_vw;
