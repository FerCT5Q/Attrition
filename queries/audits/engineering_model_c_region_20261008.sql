/* Contrato de entrada C: region. Sólo agregados; no demuestra un score semántico. */
WITH p AS (
 SELECT employee_id, CAST(fis_mo_end_dt AS DATE) AS d, NULLIF(TRIM(region), '') AS v
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE worker_type='Employee' AND employee_type='Regular' AND active_status=1
 AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
 AND CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
), cells AS (
 SELECT employee_id, d, COUNT(*) AS n, COUNT(DISTINCT v) AS versions,
        MAX(CASE WHEN v IS NOT NULL THEN 1 ELSE 0 END) AS populated
 FROM p GROUP BY 1,2
)
SELECT EXTRACT(year FROM d)::INTEGER AS year, COUNT(*) AS employee_snapshots,
 COUNT(DISTINCT employee_id) AS employee_count,
 SUM(CASE WHEN n>1 THEN 1 ELSE 0 END) AS duplicate_cells,
 SUM(CASE WHEN versions>1 THEN 1 ELSE 0 END) AS contradictory_cells,
 SUM(populated) AS populated_cells
FROM cells GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1
