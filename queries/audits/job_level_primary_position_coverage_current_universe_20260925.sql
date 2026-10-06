/*
  Cobertura agregada de job_level_primary_position.

  Entregable: presentation-safe; sólo devuelve métricas agregadas.
  Grano de la métrica: empleado-snapshot, no filas físicas de la tabla.

  Universos comparados:
    1) base exacta: worker_type='Employee', employee_type='Regular',
       active_status=1 e is_rf360_yes_no=0;
    2) sensibilidad: la misma base, tratando NULL de is_rf360_yes_no como
       no-RF360; no es la definición aprobada, sólo muestra el impacto del
       tratamiento del NULL;
    3) scope V7: base exacta más match único en hrda.critical_tech y
       seg <> 'Other Eng'.

  Snapshots:
    - último snapshot disponible en la fuente;
    - 2026-08-23, snapshot usado por las auditorías de la slide de tenure,
      cuando está disponible.

  Regla de cobertura:
    job_level_primary_position está poblado si TRIM(value) no es vacío y no
    es NULL. El denominador es el número de empleados elegibles distintos en
    cada snapshot y universo.
*/
WITH latest_snapshot AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
target_dates AS (
    SELECT snapshot_date, 'latest_available' AS snapshot_label
    FROM latest_snapshot
    UNION ALL
    SELECT DATE '2026-08-23', 'slide_baseline_2026_08_23'
    WHERE (SELECT snapshot_date FROM latest_snapshot) <> DATE '2026-08-23'
),
catalogue_mapping AS (
    SELECT
        LOWER(TRIM(extended_job_family)) AS normalized_job_family,
        MAX(NULLIF(TRIM(seg), '')) AS seg
    FROM hrda.critical_tech
    WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
    GROUP BY 1
    HAVING COUNT(DISTINCT NULLIF(TRIM(seg), '')) = 1
),
source_rows AS (
    SELECT
        CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
        w.employee_id,
        w.worker_type,
        w.employee_type,
        w.active_status,
        w.is_rf360_yes_no,
        LOWER(TRIM(w.job_family)) AS normalized_job_family,
        NULLIF(TRIM(CAST(w.job_level_primary_position AS VARCHAR(256))), '') AS job_level_value
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN target_dates AS d
        ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
    WHERE w.employee_id IS NOT NULL
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
),
employee_snapshots AS (
    SELECT
        s.snapshot_date,
        s.employee_id,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(s.job_level_value, '__NULL__')) AS level_value_variants,
        MAX(CASE WHEN s.job_level_value IS NOT NULL THEN 1 ELSE 0 END) AS level_populated,
        MAX(CASE WHEN s.is_rf360_yes_no = 0 THEN 1 ELSE 0 END) AS rf360_zero,
        MAX(CASE WHEN s.is_rf360_yes_no IS NULL THEN 1 ELSE 0 END) AS rf360_null,
        MAX(CASE WHEN c.normalized_job_family IS NOT NULL
                       AND c.seg <> 'Other Eng'
                 THEN 1 ELSE 0 END) AS critical_tech_non_other_eng
    FROM source_rows AS s
    LEFT JOIN catalogue_mapping AS c
        ON c.normalized_job_family = s.normalized_job_family
    GROUP BY 1, 2
),
scoped AS (
    SELECT
        d.snapshot_date,
        d.snapshot_label,
        'base_exact_rf360_0' AS population,
        e.source_row_count,
        e.level_value_variants,
        e.level_populated
    FROM employee_snapshots AS e
    INNER JOIN target_dates AS d
        ON d.snapshot_date = e.snapshot_date
    WHERE e.rf360_zero = 1

    UNION ALL

    SELECT
        d.snapshot_date,
        d.snapshot_label,
        'base_rf360_0_or_null_sensitivity' AS population,
        e.source_row_count,
        e.level_value_variants,
        e.level_populated
    FROM employee_snapshots AS e
    INNER JOIN target_dates AS d
        ON d.snapshot_date = e.snapshot_date
    WHERE e.rf360_zero = 1 OR e.rf360_null = 1

    UNION ALL

    SELECT
        d.snapshot_date,
        d.snapshot_label,
        'v7_critical_tech_non_other_eng_rf360_0' AS population,
        e.source_row_count,
        e.level_value_variants,
        e.level_populated
    FROM employee_snapshots AS e
    INNER JOIN target_dates AS d
        ON d.snapshot_date = e.snapshot_date
    WHERE e.rf360_zero = 1
      AND e.critical_tech_non_other_eng = 1
),
summary AS (
    SELECT
        snapshot_date,
        snapshot_label,
        population,
        COUNT(*) AS eligible_employee_snapshots,
        SUM(level_populated) AS populated_employee_snapshots,
        SUM(CASE WHEN level_populated = 0 THEN 1 ELSE 0 END) AS missing_or_blank_employee_snapshots,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshots,
        SUM(CASE WHEN level_value_variants > 1 THEN 1 ELSE 0 END) AS conflicting_level_value_snapshots
    FROM scoped
    GROUP BY 1, 2, 3
)
SELECT
    snapshot_date,
    snapshot_label,
    population,
    eligible_employee_snapshots,
    populated_employee_snapshots,
    missing_or_blank_employee_snapshots,
    ROUND(
        100.0 * populated_employee_snapshots
        / NULLIF(eligible_employee_snapshots, 0),
        4
    ) AS coverage_percent,
    duplicate_employee_snapshots,
    conflicting_level_value_snapshots
FROM summary
ORDER BY snapshot_date, population;
