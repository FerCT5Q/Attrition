-- Propósito: describir el campo almacenado prior_qc_work_years por bandas.
-- No prueba la fórmula, el lineage ni la definición de experiencia previa.
-- Población: empleados regulares activos en el último snapshot mensual cerrado.
WITH latest_snapshot AS (
    SELECT MAX(fis_mo_end_dt) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
), base AS (
    SELECT prior_qc_work_years
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM latest_snapshot)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
), bands AS (
    SELECT CASE
        WHEN prior_qc_work_years IS NULL THEN 'Sin valor'
        WHEN prior_qc_work_years < 0 THEN 'Inválido: < 0 años'
        WHEN prior_qc_work_years = 0 THEN '0 años'
        WHEN prior_qc_work_years < 1 THEN '> 0 a < 1 año'
        WHEN prior_qc_work_years < 3 THEN '1 a < 3 años'
        WHEN prior_qc_work_years < 5 THEN '3 a < 5 años'
        WHEN prior_qc_work_years < 10 THEN '5 a < 10 años'
        WHEN prior_qc_work_years < 15 THEN '10 a < 15 años'
        ELSE '15 años o más'
    END AS band,
    CASE
        WHEN prior_qc_work_years IS NULL THEN 1
        WHEN prior_qc_work_years < 0 THEN 2
        WHEN prior_qc_work_years = 0 THEN 3
        WHEN prior_qc_work_years < 1 THEN 4
        WHEN prior_qc_work_years < 3 THEN 5
        WHEN prior_qc_work_years < 5 THEN 6
        WHEN prior_qc_work_years < 10 THEN 7
        WHEN prior_qc_work_years < 15 THEN 8
        ELSE 9
    END AS band_order
    FROM base
)
SELECT band, band_order, COUNT(*) AS employee_count
FROM bands
GROUP BY 1, 2
HAVING COUNT(*) >= 30
ORDER BY band_order;
