-- Reconciliación agregada de is_new_hire con los flags y fechas de contratación.
--
-- Objetivo: comprobar si is_new_hire se comporta como un evento de alta
-- (is_hire/new_hire_date) y no como un estado que sólo cambia al llegar una
-- promoción. Los resultados sólo muestran celdas con al menos 30 empleados.
-- Población: worker_type='Employee', employee_type='Regular', active_status=1.
-- Fecha de conocimiento: 2026-09-11; snapshots hasta esa fecha.
-- Modo: presentation; no devuelve employee_id ni filas individuales.

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
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END AS new_hire_flag_label,
        CASE
            WHEN is_hire IS NULL THEN 'NULL'
            WHEN is_hire = 0 THEN '0'
            WHEN is_hire = 1 THEN '1'
            ELSE 'Other value'
        END AS hire_flag_label,
        CASE
            WHEN is_rehire IS NULL THEN 'NULL'
            WHEN is_rehire = 0 THEN '0'
            WHEN is_rehire = 1 THEN '1'
            ELSE 'Other value'
        END AS rehire_flag_label,
        is_new_hire,
        is_hire,
        is_rehire,
        new_hire_date,
        max_hire_rehire_date,
        original_hire_date,
        hire_date_o_ea,
        new_hire_type,
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
        new_hire_flag_label,
        hire_flag_label,
        rehire_flag_label,
        is_new_hire,
        is_hire,
        is_rehire,
        new_hire_date,
        max_hire_rehire_date,
        original_hire_date,
        hire_date_o_ea,
        new_hire_type,
        source_row_rank
    FROM base_raw
    WHERE source_row_rank = 1
),
latest_ranked AS (
    SELECT
        b.employee_id,
        b.fis_mo_end_dt,
        b.country_group,
        ROW_NUMBER() OVER (
            PARTITION BY b.employee_id ORDER BY b.fis_mo_end_dt DESC
        ) AS latest_rank
    FROM base b
),
latest AS (
    SELECT employee_id, country_group
    FROM latest_ranked
    WHERE latest_rank = 1
),
base_latest_country AS (
    SELECT
        b.employee_id,
        b.fis_mo_end_dt,
        l.country_group,
        b.new_hire_flag_label,
        b.hire_flag_label,
        b.rehire_flag_label,
        b.is_new_hire,
        b.is_hire,
        b.is_rehire,
        b.new_hire_date,
        b.max_hire_rehire_date,
        b.original_hire_date,
        b.hire_date_o_ea,
        b.new_hire_type,
        b.source_row_rank
    FROM base b
    JOIN latest l
      ON l.employee_id = b.employee_id
),
flag_hire_cross AS (
    SELECT
        country_group,
        new_hire_flag_label || ' / is_hire=' || hire_flag_label AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS observation_count
    FROM base_latest_country
    GROUP BY country_group, new_hire_flag_label || ' / is_hire=' || hire_flag_label
),
flag_rehire_cross AS (
    SELECT
        country_group,
        rehire_flag_label AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS observation_count
    FROM base_latest_country
    WHERE is_new_hire = 1
    GROUP BY country_group, rehire_flag_label
),
flag_date_cross AS (
    SELECT
        country_group,
        CASE
            WHEN new_hire_date IS NULL THEN 'new_hire_date missing'
            WHEN max_hire_rehire_date IS NULL THEN 'max_hire_rehire_date missing'
            WHEN new_hire_date = max_hire_rehire_date THEN 'same as max_hire_rehire_date'
            WHEN new_hire_date < max_hire_rehire_date THEN 'before max_hire_rehire_date'
            WHEN new_hire_date > max_hire_rehire_date THEN 'after max_hire_rehire_date'
            ELSE 'other date relation'
        END AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS observation_count
    FROM base_latest_country
    WHERE is_new_hire = 1
    GROUP BY country_group,
        CASE
            WHEN new_hire_date IS NULL THEN 'new_hire_date missing'
            WHEN max_hire_rehire_date IS NULL THEN 'max_hire_rehire_date missing'
            WHEN new_hire_date = max_hire_rehire_date THEN 'same as max_hire_rehire_date'
            WHEN new_hire_date < max_hire_rehire_date THEN 'before max_hire_rehire_date'
            WHEN new_hire_date > max_hire_rehire_date THEN 'after max_hire_rehire_date'
            ELSE 'other date relation'
        END
),
flag_original_hire_cross AS (
    SELECT
        country_group,
        CASE
            WHEN original_hire_date IS NULL THEN 'original_hire_date missing'
            WHEN new_hire_date IS NULL THEN 'new_hire_date missing'
            WHEN new_hire_date = original_hire_date THEN 'same as original_hire_date'
            WHEN new_hire_date > original_hire_date THEN 'after original_hire_date'
            WHEN new_hire_date < original_hire_date THEN 'before original_hire_date'
            ELSE 'other date relation'
        END AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS observation_count
    FROM base_latest_country
    WHERE is_new_hire = 1
    GROUP BY country_group,
        CASE
            WHEN original_hire_date IS NULL THEN 'original_hire_date missing'
            WHEN new_hire_date IS NULL THEN 'new_hire_date missing'
            WHEN new_hire_date = original_hire_date THEN 'same as original_hire_date'
            WHEN new_hire_date > original_hire_date THEN 'after original_hire_date'
            WHEN new_hire_date < original_hire_date THEN 'before original_hire_date'
            ELSE 'other date relation'
        END
),
flag_type_cross AS (
    SELECT
        country_group,
        COALESCE(NULLIF(TRIM(new_hire_type), ''), '<NULL>') AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count,
        COUNT(*) AS observation_count
    FROM base_latest_country
    WHERE is_new_hire = 1
    GROUP BY country_group, COALESCE(NULLIF(TRIM(new_hire_type), ''), '<NULL>')
)
SELECT
    'is_new_hire_vs_is_hire' AS report_section,
    country_group,
    'flag cross-tab' AS metric,
    value_label,
    employee_count,
    observation_count,
    NULL::DECIMAL(18,4) AS percent_of_group,
    NULL::DATE AS min_snapshot_date,
    NULL::DATE AS max_snapshot_date
FROM flag_hire_cross
WHERE employee_count >= 30

UNION ALL

SELECT
    'is_new_hire_vs_is_rehire',
    country_group,
    'is_new_hire=1 / is_rehire',
    value_label,
    employee_count,
    observation_count,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM flag_rehire_cross
WHERE employee_count >= 30

UNION ALL

SELECT
    'is_new_hire_date_vs_episode',
    country_group,
    'date relationship',
    value_label,
    employee_count,
    observation_count,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM flag_date_cross
WHERE employee_count >= 30

UNION ALL

SELECT
    'is_new_hire_date_vs_original_hire',
    country_group,
    'date relationship',
    value_label,
    employee_count,
    observation_count,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM flag_original_hire_cross
WHERE employee_count >= 30

UNION ALL

SELECT
    'is_new_hire_vs_new_hire_type',
    country_group,
    'new_hire_type',
    value_label,
    employee_count,
    observation_count,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM flag_type_cross
WHERE employee_count >= 30

ORDER BY report_section, country_group, metric, value_label;
