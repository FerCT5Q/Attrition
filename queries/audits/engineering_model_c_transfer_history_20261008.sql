/* Investigación enfocada: no hay eventos de transfer en 2020–2021.
   Pregunta: ¿el flag existe en esas fotos o se estaría imputando ausencia? */
WITH p AS (
 SELECT employee_id, CAST(fis_mo_end_dt AS DATE) AS d,
        is_transferred, CAST(transfer_date AS DATE) AS transfer_date
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE worker_type='Employee' AND employee_type='Regular' AND active_status=1
 AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
 AND CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
)
SELECT EXTRACT(year FROM d)::INTEGER AS year,
 COUNT(DISTINCT employee_id) AS employee_count, COUNT(*) AS employee_snapshots,
 SUM(CASE WHEN is_transferred IS NOT NULL THEN 1 ELSE 0 END) AS flag_present_rows,
 SUM(CASE WHEN is_transferred NOT IN (0,1) THEN 1 ELSE 0 END) AS contradictory_cells,
 MIN(CASE WHEN is_transferred IS NOT NULL THEN d END) AS first_flag_snapshot,
 MIN(CASE WHEN is_transferred=1 THEN d END) AS first_event_snapshot,
 SUM(CASE WHEN is_transferred=1 THEN 1 ELSE 0 END) AS event_flag_rows,
 SUM(CASE WHEN is_transferred=1 AND transfer_date IS NULL THEN 1 ELSE 0 END) AS event_missing_date_rows,
 SUM(CASE WHEN is_transferred=1 AND transfer_date>d THEN 1 ELSE 0 END) AS future_date_rows
FROM p GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1
