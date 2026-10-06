/*
  Validación agregada de All eligible para el visual de attrition por distancia
  estimada. La población es Employee, Regular, active_status=1, sin filtro de
  work arrangement. La feature usa sólo ubicación disponible al snapshot y el
  target es una salida VOLUNTARY dentro de los seis meses siguientes.

  Regla de aceptación: 24 snapshots exactos; el perfil hash reconcilia la
  exposición y las salidas con los employee-snapshots de ubicación completa y
  no conflictiva; cobertura de distancia calculable >=70%; cada banda publicada
  tiene >=30 employee-snapshots y >=30 salidas Voluntary.
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
    GROUP BY 1, 2, 3, 4, 5, 6, 7
)
SELECT
    (SELECT COUNT(*) FROM snapshot_dates) AS snapshot_count,
    (SELECT MIN(snapshot_date) FROM snapshot_dates) AS first_snapshot_date,
    (SELECT MAX(snapshot_date) FROM snapshot_dates) AS last_snapshot_date,
    COUNT(*) AS eligible_employee_snapshots,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS multirow_employee_snapshots,
    SUM(CASE WHEN country_value_count > 1 OR city_value_count > 1 OR office_value_count > 1 OR postal_value_count > 1
             THEN 1 ELSE 0 END) AS conflicting_location_employee_snapshots,
    SUM(CASE WHEN country_value_count = 1 AND city_value_count = 1 AND office_value_count = 1 AND postal_value_count = 1
             THEN 1 ELSE 0 END) AS eligible_complete_location_employee_snapshots,
    SUM(CASE WHEN country_value_count = 1 AND city_value_count = 1 AND office_value_count = 1 AND postal_value_count = 1
             THEN voluntary_attrition_target ELSE 0 END) AS eligible_complete_location_voluntary_exits
FROM target_flags;
