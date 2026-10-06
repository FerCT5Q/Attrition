-- Perfil agregado interno para calcular distancia sin devolver códigos postales.
-- postal_hash es un identificador técnico no reversible usado sólo en memoria
-- para cruzar con un catálogo público de centroides ZIP. No se publica ni se
-- guarda el código postal residencial.
--
-- Definición: empleados regulares activos en Mexico City en el snapshot
-- 2026-09-27; un bucket por empleado y postal_code normalizado.
-- La consulta devuelve sólo hash y COUNT(DISTINCT employee_id); el consumidor
-- debe conservar el resultado en memoria y publicar únicamente bandas con n>=30.
WITH base AS (
    SELECT
        employee_id,
        MD5(NULLIF(TRIM(CAST(postal_code AS VARCHAR(32))), '')) AS postal_hash
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-09-27'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND UPPER(TRIM(city)) = 'MEXICO CITY'
      AND UPPER(TRIM(country)) = 'MEXICO'
),
eligible AS (
    SELECT employee_id, postal_hash
    FROM base
    WHERE postal_hash IS NOT NULL
)
SELECT
    postal_hash,
    COUNT(DISTINCT employee_id) AS employee_count
FROM eligible
GROUP BY 1
ORDER BY 1;
