-- Validación agregada de la relación entre is_new_hire y cambios de puesto.
--
-- Afirmación evaluada:
--   cuando una persona pasa de new hire a no-new-hire, la transición coincide
--   con un cambio de posición/promoción; y, en sentido inverso, una promoción o
--   cambio observable de puesto ocurre después de que desaparece el flag.
--
-- Población: worker_type='Employee', employee_type='Regular', active_status=1.
-- Fecha de conocimiento: 2026-09-11; sólo snapshots hasta esa fecha.
-- Grain: pares de snapshots consecutivos del mismo empleado, con separación de
-- 20 a 45 días. employee_id se usa sólo dentro de joins y agregaciones.
-- `position_change_proxy` significa cambio de job_code, job_title o job_family;
-- no se presenta como definición oficial de promoción.
-- Modo: presentation. No devuelve employee_id ni filas individuales.

WITH base_raw AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        CASE
            WHEN UPPER(TRIM(country)) IN ('MEXICO', 'MÉXICO')
                THEN 'Mexico'
            WHEN UPPER(TRIM(country)) IN (
                'US', 'USA', 'UNITED STATES', 'UNITED STATES OF AMERICA'
            )
                THEN 'United States'
            WHEN country IS NULL OR TRIM(country) = ''
                THEN 'Other / unknown'
            ELSE 'Other countries'
        END AS country_group,
        CASE
            WHEN is_new_hire IN (0, 1) THEN is_new_hire
            ELSE NULL
        END AS is_new_hire,
        job_code,
        job_title,
        job_family,
        job_level_primary_position,
        compensation_grade,
        is_promo,
        promotion_date,
        is_transferred,
        job_family_change,
        time_in_job_profile_start_date,
        airflow_db_processing_ts,
        last_modified_date,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id, fis_mo_end_dt
            ORDER BY airflow_db_processing_ts DESC NULLS LAST,
                     last_modified_date DESC NULLS LAST
        ) AS source_row_rank
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt <= DATE '2026-09-11'
),
base AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        country_group,
        is_new_hire,
        job_code,
        job_title,
        job_family,
        job_level_primary_position,
        compensation_grade,
        is_promo,
        promotion_date,
        is_transferred,
        job_family_change,
        time_in_job_profile_start_date,
        airflow_db_processing_ts,
        last_modified_date,
        source_row_rank
    FROM base_raw
    WHERE source_row_rank = 1
),
latest_ranked AS (
    SELECT
        b.employee_id,
        b.fis_mo_end_dt,
        b.country_group,
        b.is_new_hire,
        b.job_code,
        b.job_title,
        b.job_family,
        b.job_level_primary_position,
        b.compensation_grade,
        b.is_promo,
        b.promotion_date,
        b.is_transferred,
        b.job_family_change,
        b.time_in_job_profile_start_date,
        b.airflow_db_processing_ts,
        b.last_modified_date,
        b.source_row_rank,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt DESC
        ) AS latest_rank
    FROM base b
),
latest AS (
    SELECT employee_id, country_group
    FROM latest_ranked
    WHERE latest_rank = 1
),
ordered AS (
    SELECT
        b.employee_id,
        b.fis_mo_end_dt,
        b.country_group,
        b.is_new_hire,
        b.job_code,
        b.job_title,
        b.job_family,
        b.job_level_primary_position,
        b.compensation_grade,
        b.is_promo,
        b.promotion_date,
        b.is_transferred,
        b.job_family_change,
        b.time_in_job_profile_start_date,
        b.airflow_db_processing_ts,
        b.last_modified_date,
        b.source_row_rank,
        LAG(is_new_hire) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_is_new_hire,
        LAG(job_code) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_job_code,
        LAG(job_title) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_job_title,
        LAG(job_family) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_job_family,
        LAG(job_level_primary_position) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_job_level,
        LAG(compensation_grade) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_compensation_grade,
        LAG(time_in_job_profile_start_date) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_profile_start_date,
        LAG(fis_mo_end_dt) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_snapshot_date,
        LAG(is_promo) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_is_promo,
        LAG(is_transferred) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_is_transferred,
        LAG(job_family_change) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_job_family_change
    FROM base b
),
pairs AS (
    SELECT
        o.employee_id,
        o.fis_mo_end_dt,
        o.is_new_hire,
        o.previous_is_new_hire,
        o.previous_snapshot_date,
        o.previous_job_code,
        o.previous_job_title,
        o.previous_job_family,
        o.job_code,
        o.job_title,
        o.job_family,
        o.job_level_primary_position,
        o.previous_job_level,
        o.compensation_grade,
        o.previous_compensation_grade,
        o.time_in_job_profile_start_date,
        o.previous_profile_start_date,
        o.is_promo,
        o.previous_is_promo,
        o.is_transferred,
        o.previous_is_transferred,
        o.job_family_change,
        o.previous_job_family_change,
        l.country_group AS latest_country_group,
        CASE
            WHEN COALESCE(o.job_code, '<NULL>')
                 <> COALESCE(o.previous_job_code, '<NULL>')
              OR COALESCE(o.job_title, '<NULL>')
                 <> COALESCE(o.previous_job_title, '<NULL>')
              OR COALESCE(o.job_family, '<NULL>')
                 <> COALESCE(o.previous_job_family, '<NULL>')
                THEN 1 ELSE 0
        END AS position_change_proxy,
        CASE
            WHEN COALESCE(o.job_level_primary_position, '<NULL>')
                 <> COALESCE(o.previous_job_level, '<NULL>')
                THEN 1 ELSE 0
        END AS detailed_level_change,
        CASE
            WHEN COALESCE(o.compensation_grade, '<NULL>')
                 <> COALESCE(o.previous_compensation_grade, '<NULL>')
                THEN 1 ELSE 0
        END AS compensation_grade_change,
        CASE
            WHEN COALESCE(o.time_in_job_profile_start_date, DATE '1900-01-01')
                 <> COALESCE(o.previous_profile_start_date, DATE '1900-01-01')
                THEN 1 ELSE 0
        END AS profile_start_reset,
        CASE
            WHEN COALESCE(o.is_promo, 0) = 1
              OR COALESCE(o.previous_is_promo, 0) = 1
                THEN 1 ELSE 0
        END AS promotion_event_in_pair,
        CASE
            WHEN COALESCE(o.is_transferred, 0) = 1
              OR COALESCE(o.previous_is_transferred, 0) = 1
                THEN 1 ELSE 0
        END AS transfer_event_in_pair,
        CASE
            WHEN COALESCE(o.job_family_change, 0) = 1
              OR COALESCE(o.previous_job_family_change, 0) = 1
                THEN 1 ELSE 0
        END AS job_family_event_in_pair
    FROM ordered o
    JOIN latest l
      ON l.employee_id = o.employee_id
    WHERE o.previous_snapshot_date IS NOT NULL
      AND DATEDIFF(day, o.previous_snapshot_date, o.fis_mo_end_dt)
          BETWEEN 20 AND 45
),
pair_flag_labels AS (
    SELECT
        p.employee_id,
        p.fis_mo_end_dt,
        p.is_new_hire,
        p.previous_is_new_hire,
        p.latest_country_group,
        p.position_change_proxy,
        p.profile_start_reset,
        p.compensation_grade_change,
        p.promotion_event_in_pair,
        p.transfer_event_in_pair,
        p.job_family_event_in_pair,
        CASE
            WHEN previous_is_new_hire IS NULL THEN 'NULL'
            WHEN previous_is_new_hire = 0 THEN '0'
            WHEN previous_is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END AS previous_flag_label,
        CASE
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END AS current_flag_label
    FROM pairs p
),
first_flag_ranked AS (
    SELECT
        b.employee_id,
        b.fis_mo_end_dt AS first_flag_date,
        ROW_NUMBER() OVER (
            PARTITION BY b.employee_id ORDER BY b.fis_mo_end_dt
        ) AS first_flag_rank
    FROM base b
    WHERE b.is_new_hire = 1
),
first_flag AS (
    SELECT employee_id, first_flag_date
    FROM first_flag_ranked
    WHERE first_flag_rank = 1
),
movement_after_flag_ranked AS (
    SELECT
        p.employee_id,
        p.latest_country_group AS country_group,
        p.fis_mo_end_dt,
        p.is_new_hire,
        CASE
            WHEN p.promotion_event_in_pair = 1 THEN 'Promotion flag in pair'
            WHEN p.position_change_proxy = 1 THEN 'Position proxy changed'
            WHEN p.profile_start_reset = 1 THEN 'Current profile start date changed'
            WHEN p.compensation_grade_change = 1 THEN 'Compensation grade changed'
            ELSE 'Other movement'
        END AS movement_type,
        ROW_NUMBER() OVER (
            PARTITION BY p.employee_id ORDER BY p.fis_mo_end_dt
        ) AS movement_rank
    FROM pair_flag_labels p
    JOIN first_flag f
      ON f.employee_id = p.employee_id
    WHERE p.fis_mo_end_dt > f.first_flag_date
      AND (
            p.promotion_event_in_pair = 1
         OR p.position_change_proxy = 1
         OR p.profile_start_reset = 1
         OR p.compensation_grade_change = 1
      )
),
first_movement_after_flag AS (
    SELECT
        employee_id,
        country_group,
        movement_type,
        is_new_hire,
        fis_mo_end_dt
    FROM movement_after_flag_ranked
    WHERE movement_rank = 1
),
pair_transition_counts AS (
    SELECT
        latest_country_group AS country_group,
        previous_flag_label,
        current_flag_label,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS pair_count
    FROM pair_flag_labels
    GROUP BY latest_country_group, previous_flag_label, current_flag_label
),
one_to_zero_context AS (
    SELECT
        latest_country_group AS country_group,
        CASE
            WHEN position_change_proxy = 1
             AND promotion_event_in_pair = 1
                THEN 'Position proxy + promotion flag'
            WHEN profile_start_reset = 1
             AND promotion_event_in_pair = 1
                THEN 'Profile date change + promotion flag'
            WHEN position_change_proxy = 1
                THEN 'Position proxy changed'
            WHEN profile_start_reset = 1
                THEN 'Profile start date changed'
            WHEN promotion_event_in_pair = 1
                THEN 'Promotion flag'
            WHEN compensation_grade_change = 1
                THEN 'Compensation grade changed'
            WHEN transfer_event_in_pair = 1
                THEN 'Transfer flag'
            WHEN job_family_event_in_pair = 1
                THEN 'Job family flag'
            ELSE 'No movement proxy in pair'
        END AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS pair_count
    FROM pair_flag_labels
    WHERE previous_is_new_hire = 1
      AND is_new_hire = 0
    GROUP BY latest_country_group,
        CASE
            WHEN position_change_proxy = 1
             AND promotion_event_in_pair = 1
                THEN 'Position proxy + promotion flag'
            WHEN profile_start_reset = 1
             AND promotion_event_in_pair = 1
                THEN 'Profile date change + promotion flag'
            WHEN position_change_proxy = 1
                THEN 'Position proxy changed'
            WHEN profile_start_reset = 1
                THEN 'Profile start date changed'
            WHEN promotion_event_in_pair = 1
                THEN 'Promotion flag'
            WHEN compensation_grade_change = 1
                THEN 'Compensation grade changed'
            WHEN transfer_event_in_pair = 1
                THEN 'Transfer flag'
            WHEN job_family_event_in_pair = 1
                THEN 'Job family flag'
            ELSE 'No movement proxy in pair'
        END
),
movement_flag_state_counts AS (
    SELECT
        country_group,
        movement_type,
        CASE
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM first_movement_after_flag
    GROUP BY country_group, movement_type,
        CASE
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END
),
promotion_flag_state_counts AS (
    SELECT
        latest_country_group AS country_group,
        CASE
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS promotion_snapshot_count
    FROM pairs
    WHERE is_promo = 1
    GROUP BY latest_country_group,
        CASE
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END
),
position_change_flag_state_counts AS (
    SELECT
        latest_country_group AS country_group,
        CASE
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS position_change_pair_count
    FROM pairs
    WHERE position_change_proxy = 1
    GROUP BY latest_country_group,
        CASE
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END
)
SELECT
    'flag_transition_matrix' AS report_section,
    country_group,
    previous_flag_label || ' -> ' || current_flag_label AS metric,
    'consecutive_monthly_pair' AS value_label,
    employee_count,
    pair_count AS observation_count,
    NULL::DECIMAL(18,4) AS percent_of_group,
    NULL::DATE AS min_snapshot_date,
    NULL::DATE AS max_snapshot_date
FROM pair_transition_counts
WHERE employee_count >= 30

UNION ALL

SELECT
    'one_to_zero_context',
    country_group,
    '1 -> 0 transition context',
    value_label,
    employee_count,
    pair_count,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM one_to_zero_context
WHERE employee_count >= 30

UNION ALL

SELECT
    'first_movement_after_new_hire',
    country_group,
    movement_type,
    value_label,
    employee_count,
    NULL::BIGINT,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM movement_flag_state_counts
WHERE employee_count >= 30

UNION ALL

SELECT
    'promotion_snapshot_flag_state',
    country_group,
    'is_promo=1 snapshot',
    value_label,
    employee_count,
    promotion_snapshot_count,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM promotion_flag_state_counts
WHERE employee_count >= 30

UNION ALL

SELECT
    'position_proxy_change_flag_state',
    country_group,
    'position_change_proxy=1 pair',
    value_label,
    employee_count,
    position_change_pair_count,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM position_change_flag_state_counts
WHERE employee_count >= 30

ORDER BY report_section, country_group, metric, value_label;
