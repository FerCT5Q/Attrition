/*
  Auditoria agregada de posibles tablas historicas para
  time_in_job_profile_start_date.

  Modo de entrega: presentation. No devuelve IDs ni filas individuales.
  Esta consulta no autoriza sustituir la fuente gobernada: compara cobertura,
  grain temporal y poblacion agregada de tablas antiguas con la tabla mensual
  principal. Las tablas phdwd_* y phmwd_* son candidatos tecnicos sin lineage
  de negocio confirmado.
*/
WITH source_rows AS (
    SELECT
        'post_hire_monthly_worker_dtls' AS source_table,
        CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
        CAST(fiscal_year AS INTEGER) AS fiscal_year,
        employee_id,
        time_in_job_profile_start_date,
        worker_type,
        employee_type,
        active_status
    FROM hrda.post_hire_monthly_worker_dtls

    UNION ALL
    SELECT 'phmwd_1348', CAST(fis_mo_end_dt AS DATE), CAST(fiscal_year AS INTEGER), employee_id,
           time_in_job_profile_start_date, worker_type, employee_type, active_status
    FROM hrda.phmwd_1348

    UNION ALL
    SELECT 'phmwd_1351', CAST(fis_mo_end_dt AS DATE), CAST(fiscal_year AS INTEGER), employee_id,
           time_in_job_profile_start_date, worker_type, employee_type, active_status
    FROM hrda.phmwd_1351

    UNION ALL
    SELECT 'phmwd_backup_20251029', CAST(fis_mo_end_dt AS DATE), CAST(fiscal_year AS INTEGER), employee_id,
           time_in_job_profile_start_date, worker_type, employee_type, active_status
    FROM hrda.phmwd_backup_20251029

    UNION ALL
    SELECT 'phmwd_e_del_backup', CAST(fis_mo_end_dt AS DATE), CAST(fiscal_year AS INTEGER), employee_id,
           time_in_job_profile_start_date, worker_type, employee_type, active_status
    FROM hrda.phmwd_e_del_backup

    UNION ALL
    SELECT 'phdwd_1348', CAST(fis_mo_end_dt AS DATE), CAST(fiscal_year AS INTEGER), employee_id,
           time_in_job_profile_start_date, worker_type, employee_type, active_status
    FROM hrda.phdwd_1348

    UNION ALL
    SELECT 'phdwd_1351', CAST(fis_mo_end_dt AS DATE), CAST(fiscal_year AS INTEGER), employee_id,
           time_in_job_profile_start_date, worker_type, employee_type, active_status
    FROM hrda.phdwd_1351

    UNION ALL
    SELECT 'phdwd_backup_20251029', CAST(fis_mo_end_dt AS DATE), CAST(fiscal_year AS INTEGER), employee_id,
           time_in_job_profile_start_date, worker_type, employee_type, active_status
    FROM hrda.phdwd_backup_20251029

    UNION ALL
    SELECT 'phdwd_e_del_backup', CAST(fis_mo_end_dt AS DATE), CAST(fiscal_year AS INTEGER), employee_id,
           time_in_job_profile_start_date, worker_type, employee_type, active_status
    FROM hrda.phdwd_e_del_backup
),
source_summary AS (
    SELECT
        'source_summary' AS row_type,
        source_table,
        CAST(NULL AS INTEGER) AS fiscal_year,
        MIN(snapshot_date) AS min_snapshot_date,
        MAX(snapshot_date) AS max_snapshot_date,
        COUNT(*)::BIGINT AS row_count,
        COUNT(DISTINCT snapshot_date)::BIGINT AS snapshot_count,
        COUNT(DISTINCT fiscal_year)::BIGINT AS fiscal_year_count,
        SUM(CASE WHEN fiscal_year BETWEEN 2021 AND 2025 THEN 1 ELSE 0 END)::BIGINT AS fy21_fy25_rows,
        COUNT(DISTINCT CASE WHEN fiscal_year BETWEEN 2021 AND 2025 THEN snapshot_date END)::BIGINT AS fy21_fy25_snapshot_count,
        SUM(CASE WHEN fiscal_year BETWEEN 2021 AND 2025
                  AND worker_type = 'Employee'
                  AND employee_type = 'Regular'
                  AND active_status = 1
                 THEN 1 ELSE 0 END)::BIGINT AS fy21_fy25_active_regular_rows,
        SUM(CASE WHEN fiscal_year BETWEEN 2021 AND 2025
                  AND worker_type = 'Employee'
                  AND employee_type = 'Regular'
                  AND active_status = 1
                  AND time_in_job_profile_start_date IS NOT NULL
                 THEN 1 ELSE 0 END)::BIGINT AS fy21_fy25_active_regular_profile_start_rows,
        COUNT(DISTINCT CASE WHEN fiscal_year BETWEEN 2021 AND 2025
                              AND worker_type = 'Employee'
                              AND employee_type = 'Regular'
                              AND active_status = 1
                              AND time_in_job_profile_start_date IS NOT NULL
                            THEN employee_id END)::BIGINT AS fy21_fy25_active_regular_profile_start_employees
    FROM source_rows
    GROUP BY 1, 2
),
calendar_summary AS (
    SELECT
        'calendar_by_source_year' AS row_type,
        source_table,
        fiscal_year,
        MIN(snapshot_date) AS min_snapshot_date,
        MAX(snapshot_date) AS max_snapshot_date,
        COUNT(*)::BIGINT AS row_count,
        COUNT(DISTINCT snapshot_date)::BIGINT AS snapshot_count,
        CAST(NULL AS BIGINT) AS fiscal_year_count,
        CAST(NULL AS BIGINT) AS fy21_fy25_rows,
        CAST(NULL AS BIGINT) AS fy21_fy25_snapshot_count,
        SUM(CASE WHEN worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1 THEN 1 ELSE 0 END)::BIGINT AS fy21_fy25_active_regular_rows,
        SUM(CASE WHEN worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1 AND time_in_job_profile_start_date IS NOT NULL THEN 1 ELSE 0 END)::BIGINT AS fy21_fy25_active_regular_profile_start_rows,
        COUNT(DISTINCT CASE WHEN worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1 AND time_in_job_profile_start_date IS NOT NULL THEN employee_id END)::BIGINT AS fy21_fy25_active_regular_profile_start_employees
    FROM source_rows
    WHERE fiscal_year BETWEEN 2021 AND 2025
    GROUP BY 1, 2, 3
)
SELECT
    combined.row_type,
    combined.source_table,
    combined.fiscal_year,
    combined.min_snapshot_date,
    combined.max_snapshot_date,
    combined.row_count,
    combined.snapshot_count,
    combined.fiscal_year_count,
    combined.fy21_fy25_rows,
    combined.fy21_fy25_snapshot_count,
    combined.fy21_fy25_active_regular_rows,
    combined.fy21_fy25_active_regular_profile_start_rows,
    combined.fy21_fy25_active_regular_profile_start_employees
FROM (
    SELECT row_type, source_table, fiscal_year, min_snapshot_date, max_snapshot_date,
           row_count, snapshot_count, fiscal_year_count, fy21_fy25_rows,
           fy21_fy25_snapshot_count, fy21_fy25_active_regular_rows,
           fy21_fy25_active_regular_profile_start_rows,
           fy21_fy25_active_regular_profile_start_employees
    FROM source_summary
    UNION ALL
    SELECT row_type, source_table, fiscal_year, min_snapshot_date, max_snapshot_date,
           row_count, snapshot_count, fiscal_year_count, fy21_fy25_rows,
           fy21_fy25_snapshot_count, fy21_fy25_active_regular_rows,
           fy21_fy25_active_regular_profile_start_rows,
           fy21_fy25_active_regular_profile_start_employees
    FROM calendar_summary
) AS combined
ORDER BY
    CASE combined.row_type WHEN 'source_summary' THEN 1 ELSE 2 END,
    combined.source_table,
    combined.fiscal_year;
