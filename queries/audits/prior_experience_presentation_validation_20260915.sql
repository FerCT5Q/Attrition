-- presentation | aggregate-only | validación del slide Years of experience prior to Qualcomm
--
-- Claim numérico: el slide V2 reproduce la distribución de
-- prior_qc_work_years en el snapshot 2026-09-27 para Employee / Regular /
-- Active, con una sola fila por empleado y categorías publicables.
--
-- Claim semántico separado: la etiqueta "experience prior to Qualcomm" sólo
-- sería confirmable con lineage autoritativo del campo. La prueba longitudinal
-- de estabilidad de abajo es contextual: detecta cambios que requerirían una
-- explicación, pero no sustituye fórmula, owner ni documentación HRIS.
--
-- Grain: empleado distinto en el snapshot objetivo; la estabilidad se mide
-- sólo de forma agregada para la cohorte presente en dicho snapshot.
--
-- Reglas de aceptación previas:
--   1) la cifra es reproducible si el snapshot existe, la población es única,
--      no hay nulos/negativos y las categorías mostradas suman el denominador
--      con n >= 30;
--   2) una presentación fechada al 2026-09-15 no puede describirse como
--      "actual" con un snapshot posterior sin autorizar explícitamente un
--      extracto future-dated;
--   3) una etiqueta de experiencia previa no se considera confirmada sin
--      lineage y sin explicación de cualquier cambio longitudinal observado.

WITH
parameters AS (
    SELECT
        DATE '2026-09-27' AS claimed_snapshot_date,
        DATE '2026-09-15' AS review_date
),
base AS (
    SELECT
        employee_id,
        prior_qc_work_years
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT claimed_snapshot_date FROM parameters)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
by_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT COALESCE(CAST(prior_qc_work_years AS VARCHAR(64)), '__NULL__')) AS distinct_stored_values,
        MAX(prior_qc_work_years) AS prior_qc_work_years
    FROM base
    WHERE employee_id IS NOT NULL
    GROUP BY employee_id
),
unique_population AS (
    SELECT employee_id, prior_qc_work_years
    FROM by_employee
    WHERE source_rows = 1
),
classified AS (
    SELECT
        employee_id,
        CASE
            WHEN prior_qc_work_years IS NULL OR prior_qc_work_years < 0 THEN NULL
            WHEN prior_qc_work_years < 1 THEN '<1'
            WHEN prior_qc_work_years < 32 THEN FLOOR(prior_qc_work_years)::INT::VARCHAR(10)
            ELSE '32+'
        END AS category,
        CASE
            WHEN prior_qc_work_years IS NULL OR prior_qc_work_years < 0 THEN NULL
            WHEN prior_qc_work_years < 1 THEN 0
            WHEN prior_qc_work_years < 32 THEN FLOOR(prior_qc_work_years)::INT + 1
            ELSE 34
        END AS category_order
    FROM unique_population
),
category_counts AS (
    SELECT category, category_order, COUNT(*)::BIGINT AS employee_count
    FROM classified
    WHERE category IS NOT NULL
    GROUP BY category, category_order
),
current_cohort AS (
    SELECT employee_id
    FROM unique_population
),
recent_snapshot_dates AS (
    SELECT DISTINCT fis_mo_end_dt AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt <= (SELECT claimed_snapshot_date FROM parameters)
    ORDER BY snapshot_date DESC
    LIMIT 13
),
history_by_employee AS (
    SELECT
        h.employee_id,
        COUNT(DISTINCT h.fis_mo_end_dt) AS observed_snapshots,
        COUNT(DISTINCT CASE WHEN h.prior_qc_work_years IS NOT NULL AND h.prior_qc_work_years >= 0
                            THEN h.fis_mo_end_dt END) AS valid_value_snapshots,
        MIN(CASE WHEN h.prior_qc_work_years IS NOT NULL AND h.prior_qc_work_years >= 0
                 THEN h.prior_qc_work_years END) AS min_valid_value,
        MAX(CASE WHEN h.prior_qc_work_years IS NOT NULL AND h.prior_qc_work_years >= 0
                 THEN h.prior_qc_work_years END) AS max_valid_value
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
metrics AS (
    SELECT 'source' AS check_group, 'latest_available_snapshot' AS check_name,
           NULL::BIGINT AS employee_count,
           CAST(MAX(fis_mo_end_dt) AS VARCHAR(32)) AS text_value
    FROM hrda.post_hire_monthly_worker_dtls

    UNION ALL

    SELECT 'source', 'claimed_snapshot_date', NULL::BIGINT,
           CAST((SELECT claimed_snapshot_date FROM parameters) AS VARCHAR(32))

    UNION ALL

    SELECT 'review_boundary', 'claimed_snapshot_after_review_date',
           CASE WHEN (SELECT claimed_snapshot_date FROM parameters) > (SELECT review_date FROM parameters)
                THEN 1 ELSE 0 END::BIGINT,
           CAST((SELECT review_date FROM parameters) AS VARCHAR(32))

    UNION ALL

    SELECT 'population', 'source_rows', COUNT(*)::BIGINT, NULL::VARCHAR(32)
    FROM base

    UNION ALL

    SELECT 'population', 'missing_employee_id_rows', COUNT(*)::BIGINT, NULL::VARCHAR(32)
    FROM base
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

    SELECT 'population', 'conflicting_duplicate_employee_count',
           COALESCE(SUM(CASE WHEN source_rows > 1 AND distinct_stored_values > 1 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM by_employee

    UNION ALL

    SELECT 'domain', 'null_value_count',
           COALESCE(SUM(CASE WHEN prior_qc_work_years IS NULL THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM unique_population

    UNION ALL

    SELECT 'domain', 'negative_value_count',
           COALESCE(SUM(CASE WHEN prior_qc_work_years < 0 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM unique_population

    UNION ALL

    SELECT 'domain', 'valid_non_negative_value_count',
           COALESCE(SUM(CASE WHEN prior_qc_work_years >= 0 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM unique_population

    UNION ALL

    SELECT 'distribution', 'published_category_count', COUNT(*)::BIGINT, NULL::VARCHAR(32)
    FROM category_counts

    UNION ALL

    SELECT 'distribution', 'published_count_sum', COALESCE(SUM(employee_count), 0)::BIGINT, NULL::VARCHAR(32)
    FROM category_counts

    UNION ALL

    SELECT 'distribution', 'minimum_published_category_count', COALESCE(MIN(employee_count), 0)::BIGINT, NULL::VARCHAR(32)
    FROM category_counts

    UNION ALL

    SELECT 'distribution', 'categories_below_minimum_cohort',
           COALESCE(SUM(CASE WHEN employee_count < 30 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM category_counts

    UNION ALL

    SELECT 'distribution', 'exact_year_32_count',
           COALESCE(SUM(CASE WHEN prior_qc_work_years >= 32 AND prior_qc_work_years < 33 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM unique_population

    UNION ALL

    SELECT 'distribution', category, employee_count, NULL::VARCHAR(32)
    FROM category_counts

    UNION ALL

    SELECT 'longitudinal_context', 'current_cohort_with_two_or_more_valid_snapshots',
           COALESCE(SUM(CASE WHEN valid_value_snapshots >= 2 THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM history_by_employee

    UNION ALL

    SELECT 'longitudinal_context', 'current_cohort_value_changed',
           COALESCE(SUM(CASE WHEN valid_value_snapshots >= 2
                                  AND max_valid_value - min_valid_value > 0.000001
                             THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM history_by_employee

    UNION ALL

    SELECT 'longitudinal_context', 'current_cohort_value_increased_by_at_least_one',
           COALESCE(SUM(CASE WHEN valid_value_snapshots >= 2
                                  AND max_valid_value - min_valid_value >= 0.999999
                             THEN 1 ELSE 0 END), 0)::BIGINT,
           NULL::VARCHAR(32)
    FROM history_by_employee
)
SELECT
    (SELECT claimed_snapshot_date FROM parameters) AS claimed_snapshot_date,
    check_group,
    check_name,
    employee_count,
    text_value
FROM metrics
ORDER BY
    check_group,
    CASE WHEN check_group = 'distribution' THEN
        CASE check_name
            WHEN '<1' THEN 0
            WHEN '1' THEN 1
            WHEN '2' THEN 2
            WHEN '3' THEN 3
            WHEN '4' THEN 4
            WHEN '5' THEN 5
            WHEN '6' THEN 6
            WHEN '7' THEN 7
            WHEN '8' THEN 8
            WHEN '9' THEN 9
            WHEN '10' THEN 10
            WHEN '11' THEN 11
            WHEN '12' THEN 12
            WHEN '13' THEN 13
            WHEN '14' THEN 14
            WHEN '15' THEN 15
            WHEN '16' THEN 16
            WHEN '17' THEN 17
            WHEN '18' THEN 18
            WHEN '19' THEN 19
            WHEN '20' THEN 20
            WHEN '21' THEN 21
            WHEN '22' THEN 22
            WHEN '23' THEN 23
            WHEN '24' THEN 24
            WHEN '25' THEN 25
            WHEN '26' THEN 26
            WHEN '27' THEN 27
            WHEN '28' THEN 28
            WHEN '29' THEN 29
            WHEN '30' THEN 30
            WHEN '31' THEN 31
            WHEN '32+' THEN 32
            ELSE 100
        END
    ELSE 100 END,
    check_name;
