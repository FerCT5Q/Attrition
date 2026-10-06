-- Perfil agregado interno global para Commute distance con bandera Onsite.
-- postal_hash y office_hash se mantienen solo en memoria para cruzar con los
-- catalogos externos; la evidencia final no conserva ninguno de los dos.
WITH base AS (
    SELECT
        employee_id,
        NULLIF(TRIM(CAST(country AS VARCHAR(128))), '') AS country_label,
        NULLIF(TRIM(CAST(city AS VARCHAR(128))), '') AS city_label,
        NULLIF(TRIM(CAST(postal_code AS VARCHAR(32))), '') AS postal_value,
        MD5(UPPER(NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), ''))) AS office_hash,
        MD5(UPPER(NULLIF(TRIM(CAST(postal_code AS VARCHAR(32))), ''))) AS postal_hash,
        CASE WHEN UPPER(NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '')) = 'ONSITE' THEN 1 ELSE 0 END AS onsite_flag,
        CASE WHEN NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '') IS NOT NULL THEN 1 ELSE 0 END AS work_arrangement_observable
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-09-27'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
eligible AS (
    SELECT
        employee_id,
        country_label,
        city_label,
        office_hash,
        postal_hash,
        onsite_flag,
        work_arrangement_observable,
        MD5(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', '')) AS postal_hash_compact,
        MD5(LEFT(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 2)) AS postal_hash_prefix_2,
        MD5(LEFT(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 3)) AS postal_hash_prefix_3,
        MD5(LEFT(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 4)) AS postal_hash_prefix_4,
        MD5(LPAD(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 5, '0')) AS postal_hash_zero_pad_5,
        MD5(LPAD(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 6, '0')) AS postal_hash_zero_pad_6,
        MD5(LPAD(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 7, '0')) AS postal_hash_zero_pad_7
    FROM base
    WHERE country_label IS NOT NULL
      AND city_label IS NOT NULL
      AND office_hash IS NOT NULL
      AND postal_hash IS NOT NULL
)
SELECT
    country_label,
    city_label,
    MD5(UPPER(TRIM(country_label))) AS country_hash,
    MD5(UPPER(TRIM(city_label))) AS city_hash,
    office_hash,
    postal_hash,
    postal_hash_compact,
    postal_hash_prefix_2,
    postal_hash_prefix_3,
    postal_hash_prefix_4,
    postal_hash_zero_pad_5,
    postal_hash_zero_pad_6,
    postal_hash_zero_pad_7,
    onsite_flag,
    work_arrangement_observable,
    COUNT(DISTINCT employee_id) AS employee_count
FROM eligible
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
ORDER BY 1, 2, 3, 4, 5, 14;
