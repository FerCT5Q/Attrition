-- Propósito: describir fechas de promoción conocidas por bandas temporales.
-- No define el tratamiento final de empleados sin promoción ni la feature derivada completa.
-- Población: empleados regulares activos en el último snapshot mensual cerrado.
WITH latest_snapshot AS (
    SELECT MAX(fis_mo_end_dt) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
), base AS (
    SELECT fis_mo_end_dt, is_promo, promotion_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM latest_snapshot)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
), bands AS (
    SELECT CASE
        WHEN promotion_date IS NULL THEN 'Sin fecha de promoción conocida'
        WHEN promotion_date > fis_mo_end_dt THEN 'Inválido: fecha futura'
        WHEN DATEDIFF(day, promotion_date, fis_mo_end_dt) < 365 THEN '< 1 año'
        WHEN DATEDIFF(day, promotion_date, fis_mo_end_dt) < 730 THEN '1 a < 2 años'
        WHEN DATEDIFF(day, promotion_date, fis_mo_end_dt) < 1826 THEN '2 a < 5 años'
        WHEN DATEDIFF(day, promotion_date, fis_mo_end_dt) < 3653 THEN '5 a < 10 años'
        ELSE '10 años o más'
    END AS band,
    CASE
        WHEN promotion_date IS NULL THEN 1
        WHEN promotion_date > fis_mo_end_dt THEN 2
        WHEN DATEDIFF(day, promotion_date, fis_mo_end_dt) < 365 THEN 3
        WHEN DATEDIFF(day, promotion_date, fis_mo_end_dt) < 730 THEN 4
        WHEN DATEDIFF(day, promotion_date, fis_mo_end_dt) < 1826 THEN 5
        WHEN DATEDIFF(day, promotion_date, fis_mo_end_dt) < 3653 THEN 6
        ELSE 7
    END AS band_order
    FROM base
)
SELECT band, band_order, COUNT(*) AS employee_count
FROM bands
GROUP BY 1, 2
HAVING COUNT(*) >= 30
ORDER BY band_order;
