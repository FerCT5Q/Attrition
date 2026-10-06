-- presentation | aggregate-only | validación de cifras del slide Company tenure
--
-- Claim: el slide V2 describe correctamente, en el snapshot fijo 2026-08-23,
-- las distribuciones separadas de original_hire_date y max_hire_rehire_date
-- para Employee / Regular / Active. No selecciona una definición HRIS de
-- Company tenure ni usa un campo como sustituto del otro.
--
-- Grain: empleado distinto en un único snapshot mensual.
--
-- Regla de aceptación previa:
--   1) el snapshot debe tener exactamente una fila por empleado elegible;
--   2) no debe haber fechas nulas, futuras ni original_hire_date posterior a
--      max_hire_rehire_date;
--   3) cada perfil debe reconciliar su denominador con la población única y
--      cada banda compartible debe tener n >= 30.

WITH
parameters AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
population_source AS (
    SELECT
        employee_id,
        original_hire_date,
        max_hire_rehire_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM parameters)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
by_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(CAST(original_hire_date AS VARCHAR(32)), '__NULL__')) AS original_hire_values,
        COUNT(DISTINCT COALESCE(CAST(max_hire_rehire_date AS VARCHAR(32)), '__NULL__')) AS latest_hire_rehire_values,
        MAX(original_hire_date) AS original_hire_date,
        MAX(max_hire_rehire_date) AS max_hire_rehire_date
    FROM population_source
    WHERE employee_id IS NOT NULL
    GROUP BY employee_id
),
unique_population AS (
    SELECT employee_id, original_hire_date, max_hire_rehire_date
    FROM by_employee
    WHERE source_rows = 1
),
clock_dates AS (
    SELECT 'original_hire_date' AS proxy_field, original_hire_date AS start_date
    FROM unique_population
    UNION ALL
    SELECT 'max_hire_rehire_date' AS proxy_field, max_hire_rehire_date AS start_date
    FROM unique_population
),
classified AS (
    SELECT
        proxy_field,
        CASE
            WHEN start_date IS NULL OR start_date > (SELECT snapshot_date FROM parameters) THEN 'not_calculable'
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 1, start_date) THEN 'lt_1'
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 2, start_date) THEN 'y1_to_lt2'
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 3, start_date) THEN 'y2_to_lt3'
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 5, start_date) THEN 'y3_to_lt5'
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 10, start_date) THEN 'y5_to_lt10'
            ELSE 'y10_plus'
        END AS band
    FROM clock_dates
),
band_counts AS (
    SELECT proxy_field, band, COUNT(*)::BIGINT AS employee_count
    FROM classified
    GROUP BY proxy_field, band
),
metrics AS (
    SELECT 'source' AS check_group, 'latest_available_snapshot' AS check_name,
           NULL::BIGINT AS employee_count,
           CAST(MAX(fis_mo_end_dt) AS VARCHAR(32)) AS text_value
    FROM hrda.post_hire_monthly_worker_dtls

    UNION ALL

    SELECT 'population', 'source_rows', COUNT(*)::BIGINT, NULL::VARCHAR(32)
    FROM population_source

    UNION ALL

    SELECT 'population', 'missing_employee_id_rows', COUNT(*)::BIGINT, NULL::VARCHAR(32)
    FROM population_source
    WHERE employee_id IS NULL

    UNION ALL

    SELECT 'population', 'unique_employee_count', COUNT(*)::BIGINT, NULL::VARCHAR(32)
    FROM by_employee

    UNION ALL

    SELECT 'population', 'duplicate_employee_count',
           COALESCE(SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM by_employee

    UNION ALL

    SELECT 'population', 'duplicate_row_excess_count',
           COALESCE(SUM(CASE WHEN source_rows > 1 THEN source_rows - 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM by_employee

    UNION ALL

    SELECT 'population', 'conflicting_duplicate_employee_count',
           COALESCE(SUM(CASE WHEN source_rows > 1
                              AND (original_hire_values > 1 OR latest_hire_rehire_values > 1)
                         THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM by_employee

    UNION ALL

    SELECT 'date_integrity', 'original_hire_null_count',
           COALESCE(SUM(CASE WHEN original_hire_date IS NULL THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM unique_population

    UNION ALL

    SELECT 'date_integrity', 'latest_hire_rehire_null_count',
           COALESCE(SUM(CASE WHEN max_hire_rehire_date IS NULL THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM unique_population

    UNION ALL

    SELECT 'date_integrity', 'original_hire_future_date_count',
           COALESCE(SUM(CASE WHEN original_hire_date > (SELECT snapshot_date FROM parameters) THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM unique_population

    UNION ALL

    SELECT 'date_integrity', 'latest_hire_rehire_future_date_count',
           COALESCE(SUM(CASE WHEN max_hire_rehire_date > (SELECT snapshot_date FROM parameters) THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM unique_population

    UNION ALL

    SELECT 'date_integrity', 'impossible_date_order_count',
           COALESCE(SUM(CASE WHEN original_hire_date IS NOT NULL
                                  AND max_hire_rehire_date IS NOT NULL
                                  AND original_hire_date > max_hire_rehire_date
                             THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM unique_population

    UNION ALL

    SELECT 'distribution', proxy_field || ':' || band, employee_count, NULL::VARCHAR(32)
    FROM band_counts

    UNION ALL

    SELECT 'distribution', 'bands_below_minimum_cohort',
           COALESCE(SUM(CASE WHEN employee_count < 30 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM band_counts
)
SELECT
    (SELECT snapshot_date FROM parameters) AS snapshot_date,
    check_group,
    check_name,
    employee_count,
    text_value
FROM metrics
ORDER BY check_group, check_name;
