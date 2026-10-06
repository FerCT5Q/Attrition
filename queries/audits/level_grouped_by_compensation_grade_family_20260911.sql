-- Auditoría agregada para la vista exploratoria "Level grouped by grade family".
--
-- Afirmación: level_grouped es la dimensión ordinal visible; el primer
-- carácter alfabético de compensation_grade se usa únicamente como proxy
-- descriptivo de familia/track. No se interpreta el sufijo numérico como una
-- escala transversal.
--
-- Población y fecha: worker_type='Employee', employee_type='Regular',
-- active_status=1, snapshot exacto 2026-08-23.
-- Grano: empleado-snapshot distinto. employee_id sólo se usa dentro de
-- agregados y no se devuelve.
-- Regla de aceptación:
--   * no hay duplicados ni conflictos empleado-snapshot;
--   * las nueve bandas de level_grouped están presentes y cada banda visible
--     tiene n >= 30;
--   * la suma de la matriz visible reconcilia exactamente con la población;
--   * no se observan snapshots posteriores al corte;
--   * las familias se derivan mecánicamente del prefijo y no quedan grades
--     no mapeados fuera de la categoría de cola.

WITH source_rows AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') AS compensation_grade_value,
        CASE
            WHEN NULLIF(TRIM(CAST(level_grouped AS VARCHAR)), '') IS NULL THEN NULL
            ELSE REGEXP_REPLACE(
                TRIM(CAST(level_grouped AS VARCHAR)),
                '^[0-9]+[[:space:]]*-[[:space:]]*',
                ''
            )
        END AS level_label
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt = DATE '2026-08-23'
), normalized AS (
    SELECT
        employee_id,
        fis_mo_end_dt,
        compensation_grade_value,
        level_label,
        CASE
            WHEN compensation_grade_value IS NULL THEN 'Missing / blank'
            WHEN SUBSTRING(UPPER(compensation_grade_value), 1, 1) IN ('M', 'P', 'R', 'S', 'T', 'V')
                THEN SUBSTRING(UPPER(compensation_grade_value), 1, 1)
            ELSE 'Other / unmapped'
        END AS grade_family,
        CASE
            WHEN compensation_grade_value IS NULL THEN 'Missing / blank'
            WHEN SUBSTRING(UPPER(compensation_grade_value), 1, 1) IN ('M', 'P', 'R', 'S', 'T')
                THEN SUBSTRING(UPPER(compensation_grade_value), 1, 1)
            ELSE 'V / other grade families'
        END AS grade_family_display
    FROM source_rows
), employee_mapping AS (
    SELECT
        employee_id,
        COUNT(*) AS source_rows_for_employee_snapshot,
        COUNT(DISTINCT level_label) AS level_values_for_employee_snapshot,
        COUNT(DISTINCT grade_family) AS family_values_for_employee_snapshot,
        COUNT(DISTINCT compensation_grade_value) AS grade_values_for_employee_snapshot
    FROM normalized
    GROUP BY employee_id
), source_metrics AS (
    SELECT
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT employee_id) AS eligible_employee_count,
        COUNT(*) - COUNT(DISTINCT employee_id) AS duplicate_employee_snapshot_row_count,
        COUNT(DISTINCT CASE WHEN level_label IS NULL THEN employee_id END) AS missing_level_employee_count,
        COUNT(DISTINCT CASE WHEN compensation_grade_value IS NULL THEN employee_id END) AS missing_grade_employee_count,
        COUNT(DISTINCT level_label) AS level_band_count,
        COUNT(DISTINCT grade_family) AS raw_grade_family_count,
        MIN(fis_mo_end_dt) AS min_snapshot,
        MAX(fis_mo_end_dt) AS max_snapshot
    FROM normalized
), mapping_metrics AS (
    SELECT
        SUM(CASE WHEN source_rows_for_employee_snapshot > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN level_values_for_employee_snapshot > 1 THEN 1 ELSE 0 END) AS employee_level_conflict_count,
        SUM(CASE WHEN family_values_for_employee_snapshot > 1 THEN 1 ELSE 0 END) AS employee_family_conflict_count,
        SUM(CASE WHEN grade_values_for_employee_snapshot > 1 THEN 1 ELSE 0 END) AS employee_grade_conflict_count
    FROM employee_mapping
), matrix AS (
    SELECT
        level_label,
        grade_family_display,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM normalized
    WHERE level_label IS NOT NULL
    GROUP BY 1, 2
), level_totals AS (
    SELECT
        level_label,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM normalized
    WHERE level_label IS NOT NULL
    GROUP BY 1
), family_totals AS (
    SELECT
        grade_family_display,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM normalized
    WHERE grade_family_display IS NOT NULL
    GROUP BY 1
), matrix_metrics AS (
    SELECT
        COUNT(*) AS raw_matrix_cell_count,
        SUM(CASE WHEN employee_count < 30 THEN 1 ELSE 0 END) AS raw_matrix_cells_below_minimum_count,
        SUM(employee_count) AS raw_matrix_employee_count
    FROM matrix
), result_rows AS (
    SELECT
        'distribution' AS result_type,
        level_label,
        grade_family_display,
        CAST(NULL AS VARCHAR) AS metric_name,
        employee_count,
        employee_count::DECIMAL(18, 8) / NULLIF((SELECT eligible_employee_count FROM source_metrics), 0) * 100 AS percentage,
        CAST(NULL AS BIGINT) AS metric_value,
        CAST(NULL AS DATE) AS observed_date
    FROM matrix
    UNION ALL
    SELECT
        'level_total',
        level_label,
        CAST(NULL AS VARCHAR),
        CAST(NULL AS VARCHAR),
        employee_count,
        employee_count::DECIMAL(18, 8) / NULLIF((SELECT eligible_employee_count FROM source_metrics), 0) * 100,
        CAST(NULL AS BIGINT),
        CAST(NULL AS DATE)
    FROM level_totals
    UNION ALL
    SELECT
        'family_total',
        CAST(NULL AS VARCHAR),
        grade_family_display,
        CAST(NULL AS VARCHAR),
        employee_count,
        employee_count::DECIMAL(18, 8) / NULLIF((SELECT eligible_employee_count FROM source_metrics), 0) * 100,
        CAST(NULL AS BIGINT),
        CAST(NULL AS DATE)
    FROM family_totals
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'source_row_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), source_row_count, CAST(NULL AS DATE) FROM source_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'eligible_employee_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), eligible_employee_count, CAST(NULL AS DATE) FROM source_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'duplicate_employee_snapshot_row_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), duplicate_employee_snapshot_row_count, CAST(NULL AS DATE) FROM source_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'missing_level_employee_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), missing_level_employee_count, CAST(NULL AS DATE) FROM source_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'missing_grade_employee_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), missing_grade_employee_count, CAST(NULL AS DATE) FROM source_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'level_band_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), level_band_count, CAST(NULL AS DATE) FROM source_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'raw_grade_family_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), raw_grade_family_count, CAST(NULL AS DATE) FROM source_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'raw_matrix_cell_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), raw_matrix_cell_count, CAST(NULL AS DATE) FROM matrix_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'raw_matrix_cells_below_minimum_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), raw_matrix_cells_below_minimum_count, CAST(NULL AS DATE) FROM matrix_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'raw_matrix_employee_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), raw_matrix_employee_count, CAST(NULL AS DATE) FROM matrix_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'duplicate_employee_snapshot_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), duplicate_employee_snapshot_count, CAST(NULL AS DATE) FROM mapping_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'employee_level_conflict_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), employee_level_conflict_count, CAST(NULL AS DATE) FROM mapping_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'employee_family_conflict_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), employee_family_conflict_count, CAST(NULL AS DATE) FROM mapping_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'employee_grade_conflict_count', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), employee_grade_conflict_count, CAST(NULL AS DATE) FROM mapping_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'min_snapshot', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST(NULL AS BIGINT), min_snapshot FROM source_metrics
    UNION ALL
    SELECT 'metric', CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR), 'max_snapshot', CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST(NULL AS BIGINT), max_snapshot FROM source_metrics
)
SELECT
    result_type,
    level_label,
    grade_family_display,
    metric_name,
    employee_count,
    percentage,
    metric_value,
    observed_date
FROM result_rows
ORDER BY
    CASE result_type WHEN 'distribution' THEN 1 WHEN 'level_total' THEN 2 WHEN 'family_total' THEN 3 ELSE 4 END,
    level_label,
    grade_family_display,
    metric_name;
