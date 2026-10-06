/*
  Validación agregada para la visual de attrition por distancia estimada.

  Pregunta: ¿la población Onsite de cada snapshot mensual puede relacionarse,
  sin usar información futura para la feature, con una salida Voluntary dentro
  de los seis meses posteriores?

  Definición de la visual:
  - Población: Employee, Regular, active_status=1 y work_arrangement=ONSITE.
  - Grain: un empleado-snapshot mensual, deduplicado dentro de cada fecha.
  - Ventana: los 24 snapshots completos de 2024-03-24 a 2026-02-22.
  - Outcome: al menos un term_type exactamente VOLUNTARY con term_date en
    (snapshot_date, snapshot_date + 6 meses].
  - La distancia se calcula fuera de Redshift usando hashes de postal_code y
    catálogos públicos; este audit no devuelve códigos postales ni empleados.

  Regla de aceptación antes de publicar:
  1. Deben existir exactamente 24 snapshots en la ventana.
  2. Cada empleado-snapshot se reduce a un único registro.
  3. Los conflictos de ubicación se contabilizan y se excluyen de la medida.
  4. Los resultados de la visual deben reconciliar sus exposiciones con
     eligible_onsite_complete_location_employee_snapshots.
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
        COUNT(*) AS source_row_count,
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
        s.onsite_flag,
        s.source_row_count,
        s.country_value_count,
        s.city_value_count,
        s.office_value_count,
        s.postal_value_count,
        MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
    FROM employee_snapshots AS s
    LEFT JOIN voluntary_events AS v
      ON v.employee_id = s.employee_id
     AND v.term_date > s.snapshot_date
     AND v.term_date <= DATEADD(month, 6, s.snapshot_date)
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
)
SELECT
    (SELECT COUNT(*) FROM snapshot_dates) AS snapshot_count,
    (SELECT MIN(snapshot_date) FROM snapshot_dates) AS first_snapshot_date,
    (SELECT MAX(snapshot_date) FROM snapshot_dates) AS last_snapshot_date,
    COUNT(*) AS active_regular_employee_snapshots,
    SUM(CASE WHEN onsite_flag = 1 THEN 1 ELSE 0 END) AS eligible_onsite_employee_snapshots,
    SUM(CASE WHEN onsite_flag = 1 AND source_row_count > 1 THEN 1 ELSE 0 END) AS multirow_onsite_employee_snapshots,
    SUM(CASE WHEN onsite_flag = 1
              AND (country_value_count > 1 OR city_value_count > 1 OR office_value_count > 1 OR postal_value_count > 1)
             THEN 1 ELSE 0 END) AS conflicting_location_onsite_employee_snapshots,
    SUM(CASE WHEN onsite_flag = 1
              AND country_value_count = 1
              AND city_value_count = 1
              AND office_value_count = 1
              AND postal_value_count = 1
             THEN 1 ELSE 0 END) AS eligible_onsite_complete_location_employee_snapshots,
    SUM(CASE WHEN onsite_flag = 1
              AND country_value_count = 1
              AND city_value_count = 1
              AND office_value_count = 1
              AND postal_value_count = 1
             THEN voluntary_attrition_target ELSE 0 END) AS eligible_onsite_complete_location_voluntary_exits
FROM target_flags;
