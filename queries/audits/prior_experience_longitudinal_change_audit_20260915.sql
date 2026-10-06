-- presentation | aggregate-only | seguimiento de cambios de prior_qc_work_years
--
-- Claim contextual: si prior_qc_work_years representa años completados antes
-- de ingresar a Qualcomm, su valor debería permanecer estable para empleados
-- con los 13 snapshots mensuales consecutivos, salvo correcciones de origen
-- documentadas. Este chequeo detecta cambios, pero no sustituye lineage.
--
-- Población: cohorte Employee / Regular / Active en 2026-09-27 que también
-- cuenta con los 13 snapshots más recientes y un valor no negativo en todos.
-- Grain: empleado, retenido solamente dentro de CTEs; salida agregada.
--
-- Regla de aceptación previa:
--   cero cambios sin una explicación de corrección aprobada. Un resultado
--   distinto de cero bloquea la confirmación semántica de la etiqueta hasta
--   obtener lineage y explicar los cambios agregados.

WITH
parameters AS (
    SELECT DATE '2026-09-27' AS claimed_snapshot_date
),
recent_snapshot_dates AS (
    SELECT DISTINCT fis_mo_end_dt AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt <= (SELECT claimed_snapshot_date FROM parameters)
    ORDER BY snapshot_date DESC
    LIMIT 13
),
date_bounds AS (
    SELECT
        MIN(snapshot_date) AS first_snapshot_date,
        MAX(snapshot_date) AS last_snapshot_date,
        COUNT(*) AS snapshot_count
    FROM recent_snapshot_dates
),
current_cohort AS (
    SELECT employee_id
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT claimed_snapshot_date FROM parameters)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND employee_id IS NOT NULL
    GROUP BY employee_id
    HAVING COUNT(*) = 1
),
history_by_employee AS (
    SELECT
        h.employee_id,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT h.fis_mo_end_dt) AS observed_snapshot_count,
        COUNT(DISTINCT CASE WHEN h.prior_qc_work_years IS NOT NULL AND h.prior_qc_work_years >= 0
                            THEN h.fis_mo_end_dt END) AS valid_value_snapshot_count,
        MAX(CASE WHEN h.fis_mo_end_dt = (SELECT first_snapshot_date FROM date_bounds)
                 THEN h.prior_qc_work_years END) AS first_value,
        MAX(CASE WHEN h.fis_mo_end_dt = (SELECT last_snapshot_date FROM date_bounds)
                 THEN h.prior_qc_work_years END) AS last_value
    FROM hrda.post_hire_monthly_worker_dtls h
    INNER JOIN current_cohort c
        ON c.employee_id = h.employee_id
    INNER JOIN recent_snapshot_dates d
        ON d.snapshot_date = h.fis_mo_end_dt
    WHERE h.worker_type = 'Employee'
      AND h.employee_type = 'Regular'
      AND h.active_status = 1
    GROUP BY h.employee_id
),
full_window AS (
    SELECT
        employee_id,
        last_value - first_value AS value_change
    FROM history_by_employee
    WHERE source_row_count = (SELECT snapshot_count FROM date_bounds)
      AND observed_snapshot_count = (SELECT snapshot_count FROM date_bounds)
      AND valid_value_snapshot_count = (SELECT snapshot_count FROM date_bounds)
      AND first_value IS NOT NULL
      AND last_value IS NOT NULL
),
metrics AS (
    SELECT 'source_window'::VARCHAR(32) AS check_group,
           'first_snapshot_date'::VARCHAR(128) AS check_name,
           NULL::BIGINT AS employee_count,
           CAST((SELECT first_snapshot_date FROM date_bounds) AS VARCHAR(32)) AS text_value

    UNION ALL

    SELECT 'source_window'::VARCHAR(32), 'last_snapshot_date'::VARCHAR(128), NULL::BIGINT,
           CAST((SELECT last_snapshot_date FROM date_bounds) AS VARCHAR(32))

    UNION ALL

    SELECT 'source_window'::VARCHAR(32), 'snapshot_count'::VARCHAR(128),
           (SELECT snapshot_count FROM date_bounds)::BIGINT, NULL::VARCHAR(32)

    UNION ALL

    SELECT 'longitudinal_change'::VARCHAR(32), 'full_13_snapshot_valid_cohort'::VARCHAR(128),
           COUNT(*)::BIGINT, NULL::VARCHAR(32)
    FROM full_window

    UNION ALL

    SELECT 'longitudinal_change'::VARCHAR(32), 'unchanged_value_count'::VARCHAR(128),
           COALESCE(SUM(CASE WHEN ABS(value_change) <= 0.000001 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM full_window

    UNION ALL

    SELECT 'longitudinal_change'::VARCHAR(32), 'changed_value_count'::VARCHAR(128),
           COALESCE(SUM(CASE WHEN ABS(value_change) > 0.000001 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM full_window

    UNION ALL

    SELECT 'longitudinal_change'::VARCHAR(32), 'increase_approximately_one_year_count'::VARCHAR(128),
           COALESCE(SUM(CASE WHEN value_change >= 0.90 AND value_change <= 1.10 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM full_window

    UNION ALL

    SELECT 'longitudinal_change'::VARCHAR(32), 'increase_other_than_one_year_count'::VARCHAR(128),
           COALESCE(SUM(CASE WHEN value_change > 0.000001
                                  AND NOT (value_change >= 0.90 AND value_change <= 1.10)
                             THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM full_window

    UNION ALL

    SELECT 'longitudinal_change'::VARCHAR(32), 'decrease_value_count'::VARCHAR(128),
           COALESCE(SUM(CASE WHEN value_change < -0.000001 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM full_window
)
SELECT
    (SELECT claimed_snapshot_date FROM parameters) AS claimed_snapshot_date,
    check_group,
    check_name,
    employee_count,
    text_value
FROM metrics
ORDER BY check_group, check_name;
