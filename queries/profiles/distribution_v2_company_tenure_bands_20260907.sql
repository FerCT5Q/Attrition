-- Propósito: comparar dos definiciones almacenadas de antigüedad por bandas.
-- No selecciona una definición de negocio ni recalcula puntajes.
-- Población: empleados regulares activos en el último snapshot mensual cerrado.
-- HISTORICAL ONLY: this profile selects the latest snapshot and must not feed
-- slide 27. The current slide source is the fixed 2026-08-23 profile:
-- queries/profiles/company_tenure_stored_date_distribution_20260823.sql.
WITH latest_snapshot AS (
    SELECT MAX(fis_mo_end_dt) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
), base AS (
    SELECT fis_mo_end_dt, original_hire_date, max_hire_rehire_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM latest_snapshot)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
), definitions AS (
    SELECT 'Desde contratación original' AS tenure_definition, fis_mo_end_dt, original_hire_date AS start_date
    FROM base
    UNION ALL
    SELECT 'Desde última contratación/rehire' AS tenure_definition, fis_mo_end_dt, max_hire_rehire_date AS start_date
    FROM base
), bands AS (
    SELECT tenure_definition,
    CASE
        WHEN start_date IS NULL THEN 'Sin fecha'
        WHEN start_date > fis_mo_end_dt THEN 'Inválido: fecha futura'
        WHEN DATEDIFF(day, start_date, fis_mo_end_dt) < 365 THEN '< 1 año'
        WHEN DATEDIFF(day, start_date, fis_mo_end_dt) < 730 THEN '1 a < 2 años'
        WHEN DATEDIFF(day, start_date, fis_mo_end_dt) < 1826 THEN '2 a < 5 años'
        WHEN DATEDIFF(day, start_date, fis_mo_end_dt) < 3653 THEN '5 a < 10 años'
        WHEN DATEDIFF(day, start_date, fis_mo_end_dt) < 5479 THEN '10 a < 15 años'
        ELSE '15 años o más'
    END AS band,
    CASE
        WHEN start_date IS NULL THEN 1
        WHEN start_date > fis_mo_end_dt THEN 2
        WHEN DATEDIFF(day, start_date, fis_mo_end_dt) < 365 THEN 3
        WHEN DATEDIFF(day, start_date, fis_mo_end_dt) < 730 THEN 4
        WHEN DATEDIFF(day, start_date, fis_mo_end_dt) < 1826 THEN 5
        WHEN DATEDIFF(day, start_date, fis_mo_end_dt) < 3653 THEN 6
        WHEN DATEDIFF(day, start_date, fis_mo_end_dt) < 5479 THEN 7
        ELSE 8
    END AS band_order
    FROM definitions
)
SELECT tenure_definition, band, band_order, COUNT(*) AS employee_count
FROM bands
GROUP BY 1, 2, 3
HAVING COUNT(*) >= 30
ORDER BY tenure_definition, band_order;
