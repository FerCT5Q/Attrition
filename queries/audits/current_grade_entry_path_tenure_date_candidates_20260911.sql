/*
  Perfil agregado de fechas candidatas para un giro de tenure.

  Modo: presentation. No devuelve employee_id ni filas de empleados.
  La pregunta es disponibilidad historica de relojes alternativos; una fecha
  de empresa no se interpreta como fecha de entrada al compensation grade.

  Regla: para una sustitucion tecnica de FY2021-FY2025, una fecha debe estar
  poblada y no futura en al menos 95% de los snapshots activos regulares de
  cada FY. La semantica y el lineage se evaluan por separado.
*/
WITH selected_periods AS (
    SELECT
        CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(fiscal_year AS INTEGER) AS fiscal_year
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
      AND fiscal_year BETWEEN 2021 AND 2025
    GROUP BY 1, 2
),
target AS (
    SELECT
        worker.employee_id,
        CAST(worker.fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(worker.fiscal_year AS INTEGER) AS fiscal_year,
        CAST(worker.max_hire_rehire_date AS DATE) AS max_hire_rehire_date,
        CAST(worker.original_hire_date AS DATE) AS original_hire_date,
        CAST(worker.service_date AS DATE) AS service_date,
        CAST(worker.seniority_date AS DATE) AS seniority_date,
        CAST(worker.hire_date_o_ea AS DATE) AS hire_date_o_ea,
        CAST(worker.new_hire_date AS DATE) AS new_hire_date,
        CAST(worker.rehire_date AS DATE) AS rehire_date,
        CAST(worker.levelentrydate AS DATE) AS levelentrydate,
        CAST(worker.time_in_job_profile_start_date AS DATE) AS time_in_job_profile_start_date,
        CAST(worker.time_in_role AS DECIMAL(18,6)) AS time_in_role
    FROM hrda.post_hire_monthly_worker_dtls AS worker
    INNER JOIN selected_periods AS periods
      ON periods.snapshot_date = CAST(worker.fis_mo_end_dt AS DATE)
     AND periods.fiscal_year = CAST(worker.fiscal_year AS INTEGER)
    WHERE worker.worker_type = 'Employee'
      AND worker.employee_type = 'Regular'
      AND worker.active_status = 1
),
candidate_rows AS (
    SELECT fiscal_year, snapshot_date, employee_id, 'max_hire_rehire_date' AS candidate, max_hire_rehire_date AS candidate_date, CAST(NULL AS DECIMAL(18,6)) AS candidate_numeric FROM target
    UNION ALL SELECT fiscal_year, snapshot_date, employee_id, 'original_hire_date', original_hire_date, CAST(NULL AS DECIMAL(18,6)) FROM target
    UNION ALL SELECT fiscal_year, snapshot_date, employee_id, 'service_date', service_date, CAST(NULL AS DECIMAL(18,6)) FROM target
    UNION ALL SELECT fiscal_year, snapshot_date, employee_id, 'seniority_date', seniority_date, CAST(NULL AS DECIMAL(18,6)) FROM target
    UNION ALL SELECT fiscal_year, snapshot_date, employee_id, 'hire_date_o_ea', hire_date_o_ea, CAST(NULL AS DECIMAL(18,6)) FROM target
    UNION ALL SELECT fiscal_year, snapshot_date, employee_id, 'new_hire_date', new_hire_date, CAST(NULL AS DECIMAL(18,6)) FROM target
    UNION ALL SELECT fiscal_year, snapshot_date, employee_id, 'rehire_date', rehire_date, CAST(NULL AS DECIMAL(18,6)) FROM target
    UNION ALL SELECT fiscal_year, snapshot_date, employee_id, 'levelentrydate', levelentrydate, CAST(NULL AS DECIMAL(18,6)) FROM target
    UNION ALL SELECT fiscal_year, snapshot_date, employee_id, 'time_in_job_profile_start_date', time_in_job_profile_start_date, CAST(NULL AS DECIMAL(18,6)) FROM target
    UNION ALL SELECT fiscal_year, snapshot_date, employee_id, 'time_in_role', NULL, time_in_role FROM target
),
summary AS (
    SELECT
        'date_candidate_coverage' AS row_type,
        candidate,
        fiscal_year,
        COUNT(*)::BIGINT AS eligible_snapshot_count,
        SUM(CASE WHEN candidate_date IS NOT NULL OR candidate_numeric IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS populated_snapshot_count,
        SUM(CASE
            WHEN candidate_date IS NOT NULL AND candidate_date <= snapshot_date THEN 1
            WHEN candidate_numeric IS NOT NULL AND candidate_numeric >= 0 THEN 1
            ELSE 0
        END)::BIGINT AS valid_snapshot_count,
        COUNT(DISTINCT CASE
            WHEN (candidate_date IS NOT NULL AND candidate_date <= snapshot_date)
              OR (candidate_numeric IS NOT NULL AND candidate_numeric >= 0)
            THEN employee_id
        END)::BIGINT AS distinct_employee_count,
        SUM(CASE WHEN candidate_date > snapshot_date THEN 1 ELSE 0 END)::BIGINT AS future_date_count,
        MIN(candidate_date) AS earliest_candidate_date,
        MAX(candidate_date) AS latest_candidate_date,
        CAST(NULL AS BIGINT) AS snapshot_count,
        CAST(NULL AS BIGINT) AS fiscal_month_count
    FROM candidate_rows
    GROUP BY 1, 2, 3
),
calendar AS (
    SELECT
        'calendar' AS row_type,
        CAST(NULL AS VARCHAR(80)) AS candidate,
        fiscal_year,
        CAST(NULL AS BIGINT) AS eligible_snapshot_count,
        CAST(NULL AS BIGINT) AS populated_snapshot_count,
        CAST(NULL AS BIGINT) AS valid_snapshot_count,
        CAST(NULL AS BIGINT) AS distinct_employee_count,
        CAST(NULL AS BIGINT) AS future_date_count,
        CAST(NULL AS DATE) AS earliest_candidate_date,
        CAST(NULL AS DATE) AS latest_candidate_date,
        COUNT(DISTINCT snapshot_date)::BIGINT AS snapshot_count,
        COUNT(DISTINCT MOD(EXTRACT(MONTH FROM snapshot_date)::INTEGER, 12))::BIGINT AS fiscal_month_count
    FROM selected_periods
    GROUP BY 1, 3
),
final_rows AS (
    SELECT
        row_type,
        candidate,
        fiscal_year,
        eligible_snapshot_count,
        populated_snapshot_count,
        valid_snapshot_count,
        distinct_employee_count,
        future_date_count,
        earliest_candidate_date,
        latest_candidate_date,
        snapshot_count,
        fiscal_month_count
    FROM calendar
    UNION ALL
    SELECT
        row_type,
        candidate,
        fiscal_year,
        eligible_snapshot_count,
        populated_snapshot_count,
        valid_snapshot_count,
        distinct_employee_count,
        future_date_count,
        earliest_candidate_date,
        latest_candidate_date,
        snapshot_count,
        fiscal_month_count
    FROM summary
)
SELECT
    row_type,
    candidate,
    fiscal_year,
    eligible_snapshot_count,
    populated_snapshot_count,
    valid_snapshot_count,
    distinct_employee_count,
    future_date_count,
    earliest_candidate_date,
    latest_candidate_date,
    snapshot_count,
    fiscal_month_count
FROM final_rows
ORDER BY
    CASE row_type WHEN 'calendar' THEN 1 ELSE 2 END,
    fiscal_year,
    candidate;
