/*
  Perfil agregado para attrition voluntaria a seis meses por distancia estimada
  para All eligible. No devuelve employee_id, postal_code ni office_site en
  claro; los hashes sólo se usan dentro del proceso local de geocodificación.

  Población: Employee + Regular + active_status=1, sin restringir el work
  arrangement, en cada snapshot. Outcome: term_type exactamente VOLUNTARY
  dentro de los seis meses posteriores al snapshot.
*/
WITH parameters AS (
    SELECT DATE '2024-03-24' AS first_snapshot_date,
           DATE '2026-02-22' AS last_snapshot_date
),
snapshot_dates AS (
    SELECT CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN parameters AS p
    WHERE CAST(w.fis_mo_end_dt AS DATE) BETWEEN p.first_snapshot_date AND p.last_snapshot_date
    GROUP BY 1
),
employee_snapshots AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        w.employee_id,
        MAX(NULLIF(TRIM(CAST(w.country AS VARCHAR(256))), '')) AS country_label,
        MAX(NULLIF(TRIM(CAST(w.city AS VARCHAR(256))), '')) AS city_label,
        MAX(NULLIF(TRIM(CAST(w.office_site AS VARCHAR(256))), '')) AS office_value,
        MAX(NULLIF(TRIM(CAST(w.postal_code AS VARCHAR(64))), '')) AS postal_value,
        COUNT(DISTINCT NULLIF(TRIM(CAST(w.country AS VARCHAR(256))), '')) AS country_value_count,
        COUNT(DISTINCT NULLIF(TRIM(CAST(w.city AS VARCHAR(256))), '')) AS city_value_count,
        COUNT(DISTINCT NULLIF(TRIM(CAST(w.office_site AS VARCHAR(256))), '')) AS office_value_count,
        COUNT(DISTINCT NULLIF(TRIM(CAST(w.postal_code AS VARCHAR(64))), '')) AS postal_value_count
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN snapshot_dates AS d
      ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND /* COMMUTE_DISTANCE_PARTITION_FILTER */ 1 = 1
    GROUP BY 1, 2
),
voluntary_events AS (
    SELECT
        w.employee_id,
        CAST(w.term_date AS DATE) AS term_date
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN parameters AS p
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
      AND CAST(w.term_date AS DATE) > p.first_snapshot_date
      AND CAST(w.term_date AS DATE) <= DATEADD(month, 6, p.last_snapshot_date)
    GROUP BY 1, 2
),
target_flags AS (
    SELECT
        s.snapshot_date,
        s.employee_id,
        s.country_label,
        s.city_label,
        s.office_value,
        s.postal_value,
        MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
    FROM employee_snapshots AS s
    LEFT JOIN voluntary_events AS v
      ON v.employee_id = s.employee_id
     AND v.term_date > s.snapshot_date
     AND v.term_date <= DATEADD(month, 6, s.snapshot_date)
    WHERE s.country_value_count = 1
      AND s.city_value_count = 1
      AND s.office_value_count = 1
      AND s.postal_value_count = 1
    GROUP BY 1, 2, 3, 4, 5, 6
)
SELECT
    country_label,
    city_label,
    MD5(UPPER(TRIM(office_value))) AS office_hash,
    MD5(UPPER(TRIM(postal_value))) AS postal_hash,
    MD5(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', '')) AS postal_hash_compact,
    MD5(LEFT(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 2)) AS postal_hash_prefix_2,
    MD5(LEFT(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 3)) AS postal_hash_prefix_3,
    MD5(LEFT(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 4)) AS postal_hash_prefix_4,
    MD5(LPAD(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 5, '0')) AS postal_hash_zero_pad_5,
    MD5(LPAD(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 6, '0')) AS postal_hash_zero_pad_6,
    MD5(LPAD(REGEXP_REPLACE(UPPER(postal_value), '[^A-Z0-9]', ''), 7, '0')) AS postal_hash_zero_pad_7,
    COUNT(*) AS employee_snapshot_count,
    SUM(voluntary_attrition_target) AS voluntary_exits
FROM target_flags
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
ORDER BY 1, 2, 3;
