-- Propósito: localizar de forma agregada la etiqueta de city que representa
-- Mexico City antes de comparar postal_code con office_site.
-- No devuelve empleados ni códigos postales; sólo etiquetas de ciudad con
-- cohortes publicables.
WITH latest_snapshot AS (
    SELECT MAX(fis_mo_end_dt) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
), base AS (
    SELECT
        employee_id,
        UPPER(TRIM(city)) AS city_label
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM latest_snapshot)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND NULLIF(TRIM(city), '') IS NOT NULL
)
SELECT
    city_label,
    COUNT(DISTINCT employee_id) AS employee_count
FROM base
GROUP BY 1
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY employee_count DESC, city_label;
