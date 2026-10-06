/*
  Catálogo agregado de particiones para el perfil hash de distancia y attrition.
  No devuelve empleados, postal_code, office_site ni etiquetas de país; sólo
  hashes de país y exposición agregada.  El script de evidencia usa cada hash
  para ejecutar el perfil en lotes de <=1,000 filas, respetando el límite del
  helper read-only.
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
        MAX(CASE WHEN UPPER(NULLIF(TRIM(CAST(w.work_arrangement AS VARCHAR(256))), '')) = 'ONSITE' THEN 1 ELSE 0 END) AS onsite_flag,
        MAX(NULLIF(TRIM(CAST(w.country AS VARCHAR(256))), '')) AS country_label,
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
        MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
    FROM employee_snapshots AS s
    LEFT JOIN voluntary_events AS v
      ON v.employee_id = s.employee_id
     AND v.term_date > s.snapshot_date
     AND v.term_date <= DATEADD(month, 6, s.snapshot_date)
    WHERE s.onsite_flag = 1
      AND s.country_value_count = 1
      AND s.city_value_count = 1
      AND s.office_value_count = 1
      AND s.postal_value_count = 1
    GROUP BY 1, 2, 3
)
SELECT
    MD5(UPPER(TRIM(country_label))) AS country_hash,
    COUNT(*) AS employee_snapshot_count,
    SUM(voluntary_attrition_target) AS voluntary_exits
FROM target_flags
GROUP BY 1
ORDER BY 2 DESC, 1;
