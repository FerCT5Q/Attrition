-- presentation | aggregate-only | reconciliación contextual entre tenure y experiencia previa
--
-- Hipótesis contextual: una persona puede tener menos de un año de experiencia
-- almacenada antes de Qualcomm y, al mismo tiempo, cinco o más años desde su
-- contratación en Qualcomm. Esta consulta prueba compatibilidad aritmética en
-- un snapshot común; no prueba que prior_qc_work_years tenga esa semántica.
--
-- Población: Employee / Regular / Active al 2026-08-23.
-- Grain: empleado distinto en un único snapshot mensual.
--
-- Regla de aceptación previa:
--   Las cuatro celdas por proxy deben reconciliar con la población con ambos
--   campos calculables y cada celda visible debe tener n >= 30. Los resultados
--   sólo son contexto para interpretar las dos distribuciones, no lineage.

WITH
parameters AS (
    SELECT DATE '2026-08-23' AS snapshot_date
),
source_rows AS (
    SELECT
        employee_id,
        original_hire_date,
        max_hire_rehire_date,
        prior_qc_work_years
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = (SELECT snapshot_date FROM parameters)
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
),
by_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS source_row_count,
        MAX(original_hire_date) AS original_hire_date,
        MAX(max_hire_rehire_date) AS max_hire_rehire_date,
        MAX(prior_qc_work_years) AS prior_qc_work_years
    FROM source_rows
    WHERE employee_id IS NOT NULL
    GROUP BY employee_id
),
unique_population AS (
    SELECT employee_id, original_hire_date, max_hire_rehire_date, prior_qc_work_years
    FROM by_employee
    WHERE source_row_count = 1
),
classified AS (
    SELECT
        'original_hire_date' AS tenure_proxy,
        CASE
            WHEN prior_qc_work_years IS NULL OR prior_qc_work_years < 0 THEN NULL
            WHEN prior_qc_work_years < 1 THEN 'prior_lt_1'
            ELSE 'prior_1_plus'
        END AS prior_experience_group,
        CASE
            WHEN original_hire_date IS NULL OR original_hire_date > (SELECT snapshot_date FROM parameters) THEN NULL
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 5, original_hire_date) THEN 'tenure_lt_5'
            ELSE 'tenure_5_plus'
        END AS tenure_group
    FROM unique_population

    UNION ALL

    SELECT
        'max_hire_rehire_date' AS tenure_proxy,
        CASE
            WHEN prior_qc_work_years IS NULL OR prior_qc_work_years < 0 THEN NULL
            WHEN prior_qc_work_years < 1 THEN 'prior_lt_1'
            ELSE 'prior_1_plus'
        END AS prior_experience_group,
        CASE
            WHEN max_hire_rehire_date IS NULL OR max_hire_rehire_date > (SELECT snapshot_date FROM parameters) THEN NULL
            WHEN (SELECT snapshot_date FROM parameters) < DATEADD(year, 5, max_hire_rehire_date) THEN 'tenure_lt_5'
            ELSE 'tenure_5_plus'
        END AS tenure_group
    FROM unique_population
),
cross_tab AS (
    SELECT tenure_proxy, prior_experience_group, tenure_group, COUNT(*)::BIGINT AS employee_count
    FROM classified
    WHERE prior_experience_group IS NOT NULL
      AND tenure_group IS NOT NULL
    GROUP BY tenure_proxy, prior_experience_group, tenure_group
),
metrics AS (
    SELECT 'population'::VARCHAR(32) AS check_group, 'source_rows'::VARCHAR(128) AS check_name, COUNT(*)::BIGINT AS employee_count
    FROM source_rows

    UNION ALL

    SELECT 'population', 'unique_employee_count', COUNT(*)::BIGINT
    FROM by_employee

    UNION ALL

    SELECT 'population', 'duplicate_employee_count',
           COALESCE(SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM by_employee

    UNION ALL

    SELECT 'cross_tab'::VARCHAR(32),
           CAST(tenure_proxy || ':' || prior_experience_group || ':' || tenure_group AS VARCHAR(128)),
           employee_count
    FROM cross_tab

    UNION ALL

    SELECT 'cross_tab'::VARCHAR(32), 'visible_cells_below_minimum_cohort'::VARCHAR(128),
           COALESCE(SUM(CASE WHEN employee_count < 30 THEN 1 ELSE 0 END), 0)::BIGINT
    FROM cross_tab

    UNION ALL

    SELECT 'cross_tab'::VARCHAR(32),
           CAST(tenure_proxy || ':reconciled_cross_tab_total' AS VARCHAR(128)),
           SUM(employee_count)::BIGINT
    FROM cross_tab
    GROUP BY tenure_proxy
)
SELECT
    (SELECT snapshot_date FROM parameters) AS snapshot_date,
    check_group,
    check_name,
    employee_count
FROM metrics
ORDER BY check_group, check_name;
