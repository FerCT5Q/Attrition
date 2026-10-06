-- Propósito: evaluar si los insumos disponibles permiten una distribución
-- reproducible de “Position / time in level” en el snapshot 2026-08-23.
-- Claim: existe un constructo único de nivel y fecha de inicio que puede
-- calcularse sin ambigüedad para empleados regulares activos.
-- Regla de aceptación: una fila consistente por empleado-snapshot, cobertura
-- suficiente de la fecha elegida, ninguna fecha futura y una regla de reinicio
-- aprobada para promoción, democión, movimientos laterales y recontratación.
-- Esta auditoría prueba disponibilidad y calidad técnica; no atribuye semántica
-- de nivel a levelentrydate ni aprueba reglas de reinicio.
-- Población/grain: empleado regular activo, employee_id, fis_mo_end_dt=2026-08-23.

WITH base AS (
    SELECT
        employee_id,
        levelentrydate,
        time_in_role,
        time_in_job_profile_start_date,
        original_hire_date,
        max_hire_rehire_date,
        job_level_primary_position,
        level_grouped,
        management_level,
        is_promo,
        promotion_date,
        is_demoted,
        demotion_date,
        is_transferred,
        transfer_date,
        job_family_change,
        job_family_change_date,
        cost_center_change,
        cost_center_change_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = DATE '2026-08-23'
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
), per_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS snapshot_rows,
        COUNT(DISTINCT COALESCE(CAST(levelentrydate AS VARCHAR), '<NULL>')) AS levelentrydate_variants,
        COUNT(DISTINCT COALESCE(CAST(time_in_role AS VARCHAR), '<NULL>')) AS time_in_role_variants,
        COUNT(DISTINCT COALESCE(CAST(time_in_job_profile_start_date AS VARCHAR), '<NULL>')) AS job_profile_start_variants,
        COUNT(DISTINCT COALESCE(job_level_primary_position, '<NULL>')) AS job_level_variants,
        COUNT(DISTINCT COALESCE(level_grouped, '<NULL>')) AS level_grouped_variants,
        COUNT(DISTINCT COALESCE(management_level, '<NULL>')) AS management_level_variants,
        MAX(levelentrydate) AS levelentrydate,
        MAX(time_in_role) AS time_in_role,
        MAX(time_in_job_profile_start_date) AS time_in_job_profile_start_date,
        MAX(original_hire_date) AS original_hire_date,
        MAX(max_hire_rehire_date) AS max_hire_rehire_date,
        MAX(job_level_primary_position) AS job_level_primary_position,
        MAX(level_grouped) AS level_grouped,
        MAX(management_level) AS management_level,
        MAX(is_promo) AS is_promo,
        MAX(promotion_date) AS promotion_date,
        MAX(is_demoted) AS is_demoted,
        MAX(demotion_date) AS demotion_date,
        MAX(is_transferred) AS is_transferred,
        MAX(transfer_date) AS transfer_date,
        MAX(job_family_change) AS job_family_change,
        MAX(job_family_change_date) AS job_family_change_date,
        MAX(cost_center_change) AS cost_center_change,
        MAX(cost_center_change_date) AS cost_center_change_date
    FROM base
    GROUP BY employee_id
)
SELECT
    COUNT(*) AS active_regular_employee_count,
    SUM(snapshot_rows) AS active_regular_snapshot_row_count,
    SUM(CASE WHEN snapshot_rows > 1 THEN 1 ELSE 0 END) AS employees_with_duplicate_snapshot_rows,
    SUM(CASE WHEN levelentrydate_variants > 1
               OR time_in_role_variants > 1
               OR job_profile_start_variants > 1
               OR job_level_variants > 1
               OR level_grouped_variants > 1
               OR management_level_variants > 1
             THEN 1 ELSE 0 END) AS employees_with_conflicting_candidate_values,
    SUM(CASE WHEN levelentrydate IS NOT NULL THEN 1 ELSE 0 END) AS levelentrydate_populated_count,
    SUM(CASE WHEN time_in_role IS NOT NULL THEN 1 ELSE 0 END) AS time_in_role_populated_count,
    SUM(CASE WHEN time_in_job_profile_start_date IS NOT NULL THEN 1 ELSE 0 END) AS job_profile_start_populated_count,
    SUM(CASE WHEN levelentrydate > DATE '2026-08-23' THEN 1 ELSE 0 END) AS levelentrydate_future_count,
    SUM(CASE WHEN time_in_job_profile_start_date > DATE '2026-08-23' THEN 1 ELSE 0 END) AS job_profile_start_future_count,
    SUM(CASE WHEN time_in_role < 0 THEN 1 ELSE 0 END) AS negative_time_in_role_count,
    SUM(CASE WHEN levelentrydate IS NOT NULL
               AND max_hire_rehire_date IS NOT NULL
               AND levelentrydate < max_hire_rehire_date
             THEN 1 ELSE 0 END) AS levelentrydate_before_latest_hire_or_rehire_count,
    SUM(CASE WHEN job_level_primary_position IS NOT NULL THEN 1 ELSE 0 END) AS job_level_populated_count,
    SUM(CASE WHEN level_grouped IS NOT NULL THEN 1 ELSE 0 END) AS level_grouped_populated_count,
    SUM(CASE WHEN management_level IS NOT NULL THEN 1 ELSE 0 END) AS management_level_populated_count,
    SUM(CASE WHEN levelentrydate IS NOT NULL
               AND time_in_job_profile_start_date IS NOT NULL
               AND levelentrydate = time_in_job_profile_start_date
             THEN 1 ELSE 0 END) AS levelentrydate_equals_job_profile_start_count,
    SUM(CASE WHEN levelentrydate IS NOT NULL
               AND time_in_job_profile_start_date IS NOT NULL
               AND levelentrydate <> time_in_job_profile_start_date
             THEN 1 ELSE 0 END) AS levelentrydate_differs_from_job_profile_start_count,
    SUM(CASE WHEN is_promo = 1 AND promotion_date IS NULL THEN 1 ELSE 0 END) AS promotion_flag_without_date_count,
    SUM(CASE WHEN is_promo <> 1 AND promotion_date IS NOT NULL THEN 1 ELSE 0 END) AS promotion_date_without_flag_count,
    SUM(CASE WHEN is_demoted = 1 AND demotion_date IS NULL THEN 1 ELSE 0 END) AS demotion_flag_without_date_count,
    SUM(CASE WHEN is_demoted <> 1 AND demotion_date IS NOT NULL THEN 1 ELSE 0 END) AS demotion_date_without_flag_count,
    SUM(CASE WHEN is_transferred = 1 AND transfer_date IS NULL THEN 1 ELSE 0 END) AS transfer_flag_without_date_count,
    SUM(CASE WHEN is_transferred <> 1 AND transfer_date IS NOT NULL THEN 1 ELSE 0 END) AS transfer_date_without_flag_count,
    SUM(CASE WHEN job_family_change = 1 AND job_family_change_date IS NULL THEN 1 ELSE 0 END) AS job_family_flag_without_date_count,
    SUM(CASE WHEN job_family_change <> 1 AND job_family_change_date IS NOT NULL THEN 1 ELSE 0 END) AS job_family_date_without_flag_count,
    SUM(CASE WHEN cost_center_change = 1 AND cost_center_change_date IS NULL THEN 1 ELSE 0 END) AS cost_center_flag_without_date_count,
    SUM(CASE WHEN cost_center_change <> 1 AND cost_center_change_date IS NOT NULL THEN 1 ELSE 0 END) AS cost_center_date_without_flag_count
FROM per_employee;
