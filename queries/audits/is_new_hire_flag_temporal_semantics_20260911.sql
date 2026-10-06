-- Validación agregada de la hipótesis semántica de is_new_hire.
--
-- Afirmación evaluada:
--   is_new_hire identifica una incorporación reciente/primera incorporación,
--   aparece en los snapshots iniciales y después deja de estar activo.
--
-- Población: worker_type='Employee', employee_type='Regular', active_status=1.
-- Fecha de conocimiento: 2026-09-11; se excluyen snapshots posteriores a esa
-- fecha aunque existan en la tabla.
-- Grain analítico: empleado-snapshot mensual. La deduplicación interna conserva
-- el registro más reciente por empleado y fis_mo_end_dt; la sección de integridad
-- informa cuántas filas fuente fueron deduplicadas.
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
        CASE
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END AS flag_label,
        new_hire_date,
        max_hire_rehire_date,
        new_hire_type,
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
        flag_label,
        new_hire_date,
        max_hire_rehire_date,
        new_hire_type,
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
        b.flag_label,
        b.new_hire_date,
        b.max_hire_rehire_date,
        b.new_hire_type,
        b.airflow_db_processing_ts,
        b.last_modified_date,
        b.source_row_rank,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id
            ORDER BY fis_mo_end_dt DESC
        ) AS latest_rank
    FROM base b
),
latest AS (
    SELECT employee_id, country_group, is_new_hire, fis_mo_end_dt
    FROM latest_ranked
    WHERE latest_rank = 1
),
base_latest_country AS (
    SELECT
        b.employee_id,
        b.fis_mo_end_dt,
        l.country_group AS country_group,
        b.is_new_hire,
        b.flag_label,
        b.new_hire_date,
        b.max_hire_rehire_date,
        b.new_hire_type,
        b.airflow_db_processing_ts,
        b.last_modified_date,
        b.source_row_rank
    FROM base b
    JOIN latest l
      ON l.employee_id = b.employee_id
),
ordered AS (
    SELECT
        b.employee_id,
        b.fis_mo_end_dt,
        b.country_group,
        b.is_new_hire,
        b.flag_label,
        b.new_hire_date,
        b.max_hire_rehire_date,
        b.new_hire_type,
        b.airflow_db_processing_ts,
        b.last_modified_date,
        b.source_row_rank,
        LAG(is_new_hire) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_is_new_hire,
        LAG(fis_mo_end_dt) OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS previous_snapshot_date
    FROM base b
),
first_nonnull_ranked AS (
    SELECT
        employee_id,
        is_new_hire,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS first_nonnull_rank
    FROM base
    WHERE is_new_hire IS NOT NULL
),
first_nonnull AS (
    SELECT employee_id, is_new_hire AS first_nonnull_flag
    FROM first_nonnull_ranked
    WHERE first_nonnull_rank = 1
),
last_nonnull_ranked AS (
    SELECT
        employee_id,
        is_new_hire,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt DESC
        ) AS last_nonnull_rank
    FROM base
    WHERE is_new_hire IS NOT NULL
),
last_nonnull AS (
    SELECT employee_id, is_new_hire AS last_nonnull_flag
    FROM last_nonnull_ranked
    WHERE last_nonnull_rank = 1
),
first_flag_ranked AS (
    SELECT
        employee_id,
        fis_mo_end_dt AS first_flag_date,
        new_hire_date AS first_flag_new_hire_date,
        new_hire_type AS first_flag_new_hire_type,
        ROW_NUMBER() OVER (
            PARTITION BY employee_id ORDER BY fis_mo_end_dt
        ) AS first_flag_rank
    FROM base
    WHERE is_new_hire = 1
),
first_flag AS (
    SELECT
        employee_id,
        first_flag_date,
        first_flag_new_hire_date,
        first_flag_new_hire_type
    FROM first_flag_ranked
    WHERE first_flag_rank = 1
),
employee_summary AS (
    SELECT
        l.country_group,
        l.employee_id,
        COUNT(*) AS snapshot_count,
        SUM(CASE WHEN o.is_new_hire = 1 THEN 1 ELSE 0 END) AS flag_1_observations,
        SUM(CASE WHEN o.is_new_hire IS NULL THEN 1 ELSE 0 END) AS null_observations,
        SUM(
            CASE
                WHEN o.previous_is_new_hire = 1
                 AND o.is_new_hire = 0
                 AND DATEDIFF(day, o.previous_snapshot_date, o.fis_mo_end_dt)
                     BETWEEN 20 AND 45
                THEN 1 ELSE 0
            END
        ) AS transition_1_to_0_count,
        SUM(
            CASE
                WHEN o.previous_is_new_hire = 0
                 AND o.is_new_hire = 1
                 AND DATEDIFF(day, o.previous_snapshot_date, o.fis_mo_end_dt)
                     BETWEEN 20 AND 45
                THEN 1 ELSE 0
            END
        ) AS transition_0_to_1_count
    FROM ordered o
    JOIN latest l
      ON l.employee_id = o.employee_id
    GROUP BY l.country_group, l.employee_id
),
employee_trajectory AS (
    SELECT
        s.country_group,
        s.employee_id,
        s.snapshot_count,
        s.flag_1_observations,
        s.null_observations,
        s.transition_1_to_0_count,
        s.transition_0_to_1_count,
        f.first_flag_date,
        f.first_flag_new_hire_date,
        f.first_flag_new_hire_type,
        n.first_nonnull_flag,
        z.last_nonnull_flag,
        CASE
            WHEN n.first_nonnull_flag IS NULL THEN 'No observed 0/1 flag'
            WHEN s.flag_1_observations = 0 THEN 'Observed 0 only'
            WHEN n.first_nonnull_flag = 0 AND s.flag_1_observations > 0
                THEN 'Starts 0 then becomes 1'
            WHEN n.first_nonnull_flag = 1
             AND s.transition_1_to_0_count > 0
             AND s.transition_0_to_1_count > 0
                THEN '1 then 0 then 1 again'
            WHEN n.first_nonnull_flag = 1
             AND s.transition_1_to_0_count > 0
             AND z.last_nonnull_flag = 0
                THEN '1 then 0, no re-entry'
            WHEN n.first_nonnull_flag = 1
             AND z.last_nonnull_flag = 1
                THEN 'Starts 1, no observed 1-to-0'
            ELSE 'Other observed trajectory'
        END AS trajectory_pattern,
        CASE
            WHEN s.flag_1_observations = 0 THEN 'No snapshot with flag 1'
            WHEN s.flag_1_observations = 1 THEN '1 snapshot'
            WHEN s.flag_1_observations BETWEEN 2 AND 3 THEN '2-3 snapshots'
            WHEN s.flag_1_observations BETWEEN 4 AND 6 THEN '4-6 snapshots'
            ELSE '7+ snapshots'
        END AS flag_duration_band
    FROM employee_summary s
    LEFT JOIN first_flag f
      ON f.employee_id = s.employee_id
    LEFT JOIN first_nonnull n
      ON n.employee_id = s.employee_id
    LEFT JOIN last_nonnull z
      ON z.employee_id = s.employee_id
),
domain_counts AS (
    SELECT
        country_group,
        flag_label AS value_label,
        COUNT(*) AS observation_count,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM base_latest_country
    GROUP BY country_group, flag_label
),
domain_totals AS (
    SELECT country_group, SUM(observation_count) AS country_observation_count
    FROM domain_counts
    GROUP BY country_group
),
type_counts AS (
    SELECT
        country_group,
        COALESCE(NULLIF(TRIM(new_hire_type), ''), '<NULL>') AS value_label,
        COUNT(*) AS observation_count,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM base_latest_country
    WHERE is_new_hire = 1
    GROUP BY country_group, COALESCE(NULLIF(TRIM(new_hire_type), ''), '<NULL>')
),
first_flag_alignment AS (
    SELECT
        country_group,
        CASE
            WHEN first_flag_new_hire_date IS NULL THEN 'new_hire_date missing'
            WHEN first_flag_date < first_flag_new_hire_date THEN 'flag before new_hire_date'
            WHEN DATEDIFF(day, first_flag_new_hire_date, first_flag_date)
                 BETWEEN 0 AND 45 THEN '0-45 days after new_hire_date'
            WHEN DATEDIFF(day, first_flag_new_hire_date, first_flag_date)
                 BETWEEN 46 AND 90 THEN '46-90 days after new_hire_date'
            WHEN DATEDIFF(day, first_flag_new_hire_date, first_flag_date) > 90
                THEN '91+ days after new_hire_date'
            ELSE 'unclassified date relation'
        END AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM employee_trajectory
    WHERE flag_1_observations > 0
    GROUP BY country_group,
        CASE
            WHEN first_flag_new_hire_date IS NULL THEN 'new_hire_date missing'
            WHEN first_flag_date < first_flag_new_hire_date THEN 'flag before new_hire_date'
            WHEN DATEDIFF(day, first_flag_new_hire_date, first_flag_date)
                 BETWEEN 0 AND 45 THEN '0-45 days after new_hire_date'
            WHEN DATEDIFF(day, first_flag_new_hire_date, first_flag_date)
                 BETWEEN 46 AND 90 THEN '46-90 days after new_hire_date'
            WHEN DATEDIFF(day, first_flag_new_hire_date, first_flag_date) > 90
                THEN '91+ days after new_hire_date'
            ELSE 'unclassified date relation'
        END
),
trajectory_counts AS (
    SELECT
        country_group,
        trajectory_pattern AS value_label,
        COUNT(*) AS employee_count
    FROM employee_trajectory
    GROUP BY country_group, trajectory_pattern
),
duration_counts AS (
    SELECT
        country_group,
        flag_duration_band AS value_label,
        COUNT(*) AS employee_count
    FROM employee_trajectory
    WHERE flag_1_observations > 0
    GROUP BY country_group, flag_duration_band
),
current_flag_counts AS (
    SELECT
        country_group,
        CASE
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END AS value_label,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM latest
    GROUP BY country_group,
        CASE
            WHEN is_new_hire IS NULL THEN 'NULL'
            WHEN is_new_hire = 0 THEN '0'
            WHEN is_new_hire = 1 THEN '1'
            ELSE 'Other value'
        END
)
SELECT
    'snapshot_integrity' AS report_section,
    'All countries' AS country_group,
    'source_rows_before_deduplication' AS metric,
    'all' AS value_label,
    COUNT(DISTINCT employee_id) AS employee_count,
    COUNT(*) AS observation_count,
    NULL::DECIMAL(18,4) AS percent_of_group,
    MIN(fis_mo_end_dt) AS min_snapshot_date,
    MAX(fis_mo_end_dt) AS max_snapshot_date
FROM base_raw

UNION ALL

SELECT
    'snapshot_integrity',
    'All countries',
    'deduplicated_employee_snapshots',
    'all',
    COUNT(DISTINCT employee_id),
    COUNT(*),
    NULL::DECIMAL(18,4),
    MIN(fis_mo_end_dt),
    MAX(fis_mo_end_dt)
FROM base

UNION ALL

SELECT
    'coverage_by_country',
    country_group,
    'employee_snapshots',
    'all',
    COUNT(DISTINCT employee_id),
    COUNT(*),
    NULL::DECIMAL(18,4),
    MIN(fis_mo_end_dt),
    MAX(fis_mo_end_dt)
FROM base_latest_country
GROUP BY country_group
HAVING COUNT(DISTINCT employee_id) >= 30

UNION ALL

SELECT
    'flag_domain',
    d.country_group,
    'is_new_hire_observations',
    d.value_label,
    d.employee_count,
    d.observation_count,
    100.0 * d.observation_count / NULLIF(t.country_observation_count, 0),
    NULL::DATE,
    NULL::DATE
FROM domain_counts d
JOIN domain_totals t
  ON t.country_group = d.country_group
WHERE d.employee_count >= 30

UNION ALL

SELECT
    'new_hire_type_when_flag_1',
    country_group,
    'new_hire_type',
    value_label,
    employee_count,
    observation_count,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM type_counts
WHERE employee_count >= 30

UNION ALL

SELECT
    'first_flag_date_alignment',
    country_group,
    'first_flag_vs_new_hire_date',
    value_label,
    employee_count,
    NULL::BIGINT,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM first_flag_alignment
WHERE employee_count >= 30

UNION ALL

SELECT
    'employee_trajectory',
    country_group,
    'flag_trajectory',
    value_label,
    employee_count,
    NULL::BIGINT,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM trajectory_counts
WHERE employee_count >= 30

UNION ALL

SELECT
    'flag_duration',
    country_group,
    'number_of_flag_1_snapshots',
    value_label,
    employee_count,
    NULL::BIGINT,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM duration_counts
WHERE employee_count >= 30

UNION ALL

SELECT
    'latest_snapshot_flag',
    country_group,
    'latest_is_new_hire',
    value_label,
    employee_count,
    NULL::BIGINT,
    NULL::DECIMAL(18,4),
    NULL::DATE,
    NULL::DATE
FROM current_flag_counts
WHERE employee_count >= 30

ORDER BY report_section, country_group, metric, value_label;
