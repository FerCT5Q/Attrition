/* Componentes temporales del proxy de distancia. Hashes sólo en RAM;
   nunca se devuelven domicilios, postales legibles ni importes. */
WITH source AS (
 SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date,employee_id,
        NULLIF(UPPER(TRIM(country)),'') AS country_label,
        NULLIF(UPPER(TRIM(city)),'') AS city_label,
        NULLIF(UPPER(TRIM(office_site)),'') AS office_value,
        NULLIF(UPPER(TRIM(CAST(postal_code AS VARCHAR(32)))),'') AS postal_value,
        NULLIF(UPPER(TRIM(work_arrangement)),'') AS arrangement
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
   AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
   AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
), population AS (
 SELECT snapshot_date,employee_id,MAX(country_label) AS country_label,
        MAX(city_label) AS city_label,MAX(office_value) AS office_value,
        MAX(postal_value) AS postal_value,MAX(arrangement) AS arrangement,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(country_label,'<NULL>')) AS country_variants,
        COUNT(DISTINCT COALESCE(city_label,'<NULL>')) AS city_variants,
        COUNT(DISTINCT COALESCE(office_value,'<NULL>')) AS office_variants,
        COUNT(DISTINCT COALESCE(postal_value,'<NULL>')) AS postal_variants,
        COUNT(DISTINCT COALESCE(arrangement,'<NULL>')) AS arrangement_variants
 FROM source GROUP BY 1,2
), encoded AS (
 SELECT snapshot_date,employee_id,country_label,city_label,
        MD5(office_value) AS office_hash,MD5(postal_value) AS postal_hash,
        MD5(REGEXP_REPLACE(postal_value,'[^A-Z0-9]','')) AS postal_hash_compact,
        MD5(LEFT(REGEXP_REPLACE(postal_value,'[^A-Z0-9]',''),2)) AS postal_hash_prefix_2,
        MD5(LEFT(REGEXP_REPLACE(postal_value,'[^A-Z0-9]',''),3)) AS postal_hash_prefix_3,
        MD5(LEFT(REGEXP_REPLACE(postal_value,'[^A-Z0-9]',''),4)) AS postal_hash_prefix_4,
        MD5(LEFT(REGEXP_REPLACE(postal_value,'[^A-Z0-9]',''),5)) AS postal_hash_prefix_5,
        MD5(LPAD(REGEXP_REPLACE(postal_value,'[^A-Z0-9]',''),5,'0')) AS postal_hash_zero_pad_5,
        MD5(LPAD(REGEXP_REPLACE(postal_value,'[^A-Z0-9]',''),6,'0')) AS postal_hash_zero_pad_6,
        MD5(LPAD(REGEXP_REPLACE(postal_value,'[^A-Z0-9]',''),7,'0')) AS postal_hash_zero_pad_7,
        CASE WHEN arrangement IS NULL THEN -1 WHEN arrangement='ONSITE' THEN 1 ELSE 0 END AS onsite_flag,
        CASE WHEN source_rows=1 AND country_variants=1 AND city_variants=1
                       AND office_variants=1 AND postal_variants=1 AND arrangement_variants=1
             THEN 1 ELSE 0 END AS valid_components,
        source_rows,country_variants,city_variants,office_variants,postal_variants,arrangement_variants
 FROM population
)

SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
       COUNT(*) AS person_snapshots,COUNT(DISTINCT employee_id) AS employee_count,
       SUM(CASE WHEN source_rows>1 THEN 1 ELSE 0 END) AS duplicate_source_keys,
       SUM(CASE WHEN valid_components<>1 THEN 1 ELSE 0 END) AS conflicting_input_rows,
       SUM(CASE WHEN onsite_flag=1 THEN 1 ELSE 0 END) AS onsite_rows,
       SUM(CASE WHEN onsite_flag=-1 THEN 1 ELSE 0 END) AS arrangement_unknown_rows,
       SUM(CASE WHEN country_label IS NOT NULL AND city_label IS NOT NULL
                      AND office_hash IS NOT NULL AND postal_hash IS NOT NULL AND valid_components=1
                THEN 1 ELSE 0 END) AS complete_location_rows,
       SUM(CASE WHEN onsite_flag=1 AND country_label IS NOT NULL AND city_label IS NOT NULL
                      AND office_hash IS NOT NULL AND postal_hash IS NOT NULL AND valid_components=1
                THEN 1 ELSE 0 END) AS complete_onsite_rows
FROM encoded GROUP BY 1 ORDER BY 1
