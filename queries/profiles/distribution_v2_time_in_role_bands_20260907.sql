-- Propósito: describir time_in_role como campo candidato para Position / time in level.
-- No equivale a tiempo en nivel mientras no se apruebe la fecha autoritativa y los resets.
-- Población: empleados regulares activos en el último snapshot mensual cerrado.
WITH latest_snapshot AS (
    SELECT MAX(fis_mo_end_dt) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
), base AS (
    SELECT time_in_role
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM latest_snapshot)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
), bands AS (
    SELECT CASE
        WHEN time_in_role IS NULL THEN 'Sin valor'
        WHEN time_in_role < 0 THEN 'Inválido: < 0 años'
        WHEN time_in_role < 1 THEN '< 1 año'
        WHEN time_in_role < 2 THEN '1 a < 2 años'
        WHEN time_in_role < 3 THEN '2 a < 3 años'
        WHEN time_in_role < 5 THEN '3 a < 5 años'
        WHEN time_in_role < 10 THEN '5 a < 10 años'
        ELSE '10 años o más'
    END AS band,
    CASE
        WHEN time_in_role IS NULL THEN 1
        WHEN time_in_role < 0 THEN 2
        WHEN time_in_role < 1 THEN 3
        WHEN time_in_role < 2 THEN 4
        WHEN time_in_role < 3 THEN 5
        WHEN time_in_role < 5 THEN 6
        WHEN time_in_role < 10 THEN 7
        ELSE 8
    END AS band_order
    FROM base
)
SELECT band, band_order, COUNT(*) AS employee_count
FROM bands
GROUP BY 1, 2
HAVING COUNT(*) >= 30
ORDER BY band_order;
