-- Auditoría semántica y longitudinal de Ingreso por adquisición.
-- Modo de entrega: presentation. Sólo devuelve métricas agregadas; las claves
-- de empleado se usan exclusivamente dentro de CTEs y nunca se seleccionan.
-- Regla previa: detectar duplicados, contradicciones, blankness, variantes de
-- normalización y cambios antes de interpretar el campo como origen de ingreso.
WITH history_rows AS (
    SELECT
        fis_mo_end_dt AS snapshot_date,
        employee_id,
        NULLIF(TRIM(acquisition), '') AS acquisition_trimmed,
        UPPER(NULLIF(TRIM(acquisition), '')) AS acquisition_normalized
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt <= DATE '2026-08-23'
),
history_employee_snapshot AS (
    SELECT
        snapshot_date,
        employee_id,
        COUNT(*) AS raw_row_count,
        COUNT(DISTINCT acquisition_normalized) AS normalized_value_count,
        MAX(acquisition_normalized) AS acquisition_normalized
    FROM history_rows
    GROUP BY snapshot_date, employee_id
),
snapshot_quality AS (
    SELECT
        h.snapshot_date,
        COUNT(*) AS employee_snapshot_count,
        SUM(h.raw_row_count) AS raw_row_count,
        SUM(h.raw_row_count - 1) AS duplicate_excess_row_count,
        SUM(CASE WHEN h.raw_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN h.normalized_value_count > 1 THEN 1 ELSE 0 END) AS contradictory_employee_snapshot_count,
        SUM(CASE WHEN h.acquisition_normalized IS NOT NULL THEN 1 ELSE 0 END) AS populated_employee_count,
        SUM(CASE WHEN h.acquisition_normalized IS NULL THEN 1 ELSE 0 END) AS blank_employee_count
    FROM history_employee_snapshot h
    WHERE h.snapshot_date IN (DATE '2025-08-24', DATE '2026-08-23')
    GROUP BY h.snapshot_date
),
snapshot_domain AS (
    SELECT
        snapshot_date,
        COUNT(DISTINCT acquisition_trimmed) AS trimmed_distinct_value_count,
        COUNT(DISTINCT acquisition_normalized) AS normalized_distinct_value_count,
        COUNT(DISTINCT acquisition_trimmed) - COUNT(DISTINCT acquisition_normalized) AS trim_or_case_variant_excess_count
    FROM history_rows
    WHERE snapshot_date IN (DATE '2025-08-24', DATE '2026-08-23')
    GROUP BY snapshot_date
),
monthly_coverage AS (
    SELECT
        snapshot_date,
        COUNT(*) AS employee_snapshot_count,
        SUM(CASE WHEN acquisition_normalized IS NOT NULL THEN 1 ELSE 0 END) AS populated_employee_count,
        100.0 * SUM(CASE WHEN acquisition_normalized IS NOT NULL THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0) AS coverage_percent
    FROM history_employee_snapshot
    GROUP BY snapshot_date
),
history_employee_summary AS (
    SELECT
        employee_id,
        COUNT(*) AS observed_snapshot_count,
        COUNT(DISTINCT acquisition_normalized) AS distinct_nonblank_acquisition_count
    FROM history_employee_snapshot
    GROUP BY employee_id
),
history_transitions AS (
    SELECT
        snapshot_date,
        employee_id,
        acquisition_normalized,
        LAG(snapshot_date) OVER (PARTITION BY employee_id ORDER BY snapshot_date) AS prior_snapshot_date,
        LAG(acquisition_normalized) OVER (PARTITION BY employee_id ORDER BY snapshot_date) AS prior_acquisition_normalized
    FROM history_employee_snapshot
),
transition_summary AS (
    SELECT
        COUNT(*) AS transition_rows_checked,
        SUM(CASE
            WHEN prior_snapshot_date IS NOT NULL
             AND DATEDIFF(day, prior_snapshot_date, snapshot_date) BETWEEN 20 AND 45
            THEN 1 ELSE 0
        END) AS consecutive_snapshot_transition_count,
        SUM(CASE
            WHEN prior_snapshot_date IS NOT NULL
             AND DATEDIFF(day, prior_snapshot_date, snapshot_date) BETWEEN 20 AND 45
             AND acquisition_normalized IS NOT NULL
             AND prior_acquisition_normalized IS NOT NULL
             AND acquisition_normalized <> prior_acquisition_normalized
            THEN 1 ELSE 0
        END) AS changed_nonblank_value_transition_count,
        SUM(CASE
            WHEN prior_snapshot_date IS NOT NULL
             AND DATEDIFF(day, prior_snapshot_date, snapshot_date) BETWEEN 20 AND 45
             AND acquisition_normalized IS NOT NULL
             AND prior_acquisition_normalized IS NULL
            THEN 1 ELSE 0
        END) AS blank_to_populated_transition_count,
        SUM(CASE
            WHEN prior_snapshot_date IS NOT NULL
             AND DATEDIFF(day, prior_snapshot_date, snapshot_date) BETWEEN 20 AND 45
             AND acquisition_normalized IS NULL
             AND prior_acquisition_normalized IS NOT NULL
            THEN 1 ELSE 0
        END) AS populated_to_blank_transition_count
    FROM history_transitions
),
legacy_snapshot_history AS (
    SELECT
        MIN(snapshot_date) AS minimum_snapshot_date,
        MAX(snapshot_date) AS maximum_snapshot_date,
        COUNT(DISTINCT snapshot_date) AS distinct_snapshot_count,
        COUNT(DISTINCT emplid) AS distinct_employee_count
    FROM hrda.worker_details_ms_snapshot
),
new_hire_by_employee AS (
    SELECT
        employee_id,
        COUNT(*) AS raw_row_count,
        COUNT(DISTINCT UPPER(NULLIF(TRIM(acquisition_org), ''))) AS normalized_value_count,
        MAX(UPPER(NULLIF(TRIM(acquisition_org), ''))) AS acquisition_normalized
    FROM hrda.new_hires
    WHERE employee_id IS NOT NULL
    GROUP BY employee_id
),
current_employee AS (
    SELECT
        employee_id,
        acquisition_normalized
    FROM history_employee_snapshot
    WHERE snapshot_date = DATE '2026-08-23'
),
new_hire_context AS (
    SELECT
        COUNT(*) AS current_employee_count,
        SUM(CASE WHEN c.acquisition_normalized IS NOT NULL THEN 1 ELSE 0 END) AS current_populated_count,
        SUM(CASE WHEN n.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS new_hire_matched_employee_count,
        SUM(CASE WHEN n.normalized_value_count > 1 THEN 1 ELSE 0 END) AS new_hire_multivalue_employee_count,
        SUM(CASE
            WHEN c.acquisition_normalized IS NOT NULL
             AND n.acquisition_normalized IS NOT NULL
             AND n.normalized_value_count = 1
            THEN 1 ELSE 0
        END) AS comparable_populated_employee_count,
        SUM(CASE
            WHEN c.acquisition_normalized IS NOT NULL
             AND n.acquisition_normalized IS NOT NULL
             AND n.normalized_value_count = 1
             AND c.acquisition_normalized = n.acquisition_normalized
            THEN 1 ELSE 0
        END) AS exact_normalized_agreement_count,
        SUM(CASE
            WHEN c.acquisition_normalized IS NOT NULL
             AND n.acquisition_normalized IS NOT NULL
             AND n.normalized_value_count = 1
             AND c.acquisition_normalized <> n.acquisition_normalized
            THEN 1 ELSE 0
        END) AS normalized_disagreement_count
    FROM current_employee c
    LEFT JOIN new_hire_by_employee n
      ON n.employee_id = c.employee_id
),
history_summary AS (
    SELECT
        COUNT(*) AS employee_count,
        SUM(CASE WHEN observed_snapshot_count >= 2 THEN 1 ELSE 0 END) AS employees_with_two_or_more_snapshots,
        SUM(CASE WHEN distinct_nonblank_acquisition_count > 1 THEN 1 ELSE 0 END) AS employees_with_multiple_nonblank_values
    FROM history_employee_summary
),
coverage_summary AS (
    SELECT
        COUNT(*) AS observation_count,
        MIN(coverage_percent) AS minimum_coverage_percent,
        MAX(coverage_percent) AS maximum_coverage_percent,
        MIN(snapshot_date) AS first_snapshot_date,
        MAX(snapshot_date) AS last_snapshot_date
    FROM monthly_coverage
)
SELECT 'snapshot_quality' AS metric_group, snapshot_date, 'employee_snapshot_count' AS metric_name, employee_snapshot_count::DECIMAL(24,6) AS metric_value FROM snapshot_quality
UNION ALL SELECT 'snapshot_quality', snapshot_date, 'raw_row_count', raw_row_count::DECIMAL(24,6) FROM snapshot_quality
UNION ALL SELECT 'snapshot_quality', snapshot_date, 'duplicate_excess_row_count', duplicate_excess_row_count::DECIMAL(24,6) FROM snapshot_quality
UNION ALL SELECT 'snapshot_quality', snapshot_date, 'duplicate_employee_snapshot_count', duplicate_employee_snapshot_count::DECIMAL(24,6) FROM snapshot_quality
UNION ALL SELECT 'snapshot_quality', snapshot_date, 'contradictory_employee_snapshot_count', contradictory_employee_snapshot_count::DECIMAL(24,6) FROM snapshot_quality
UNION ALL SELECT 'snapshot_quality', snapshot_date, 'populated_employee_count', populated_employee_count::DECIMAL(24,6) FROM snapshot_quality
UNION ALL SELECT 'snapshot_quality', snapshot_date, 'blank_employee_count', blank_employee_count::DECIMAL(24,6) FROM snapshot_quality
UNION ALL SELECT 'snapshot_domain', snapshot_date, 'trimmed_distinct_value_count', trimmed_distinct_value_count::DECIMAL(24,6) FROM snapshot_domain
UNION ALL SELECT 'snapshot_domain', snapshot_date, 'normalized_distinct_value_count', normalized_distinct_value_count::DECIMAL(24,6) FROM snapshot_domain
UNION ALL SELECT 'snapshot_domain', snapshot_date, 'trim_or_case_variant_excess_count', trim_or_case_variant_excess_count::DECIMAL(24,6) FROM snapshot_domain
UNION ALL SELECT 'history', NULL::DATE, 'employee_count', employee_count::DECIMAL(24,6) FROM history_summary
UNION ALL SELECT 'history', NULL::DATE, 'employees_with_two_or_more_snapshots', employees_with_two_or_more_snapshots::DECIMAL(24,6) FROM history_summary
UNION ALL SELECT 'history', NULL::DATE, 'employees_with_multiple_nonblank_values', employees_with_multiple_nonblank_values::DECIMAL(24,6) FROM history_summary
UNION ALL SELECT 'transitions', NULL::DATE, 'transition_rows_checked', transition_rows_checked::DECIMAL(24,6) FROM transition_summary
UNION ALL SELECT 'transitions', NULL::DATE, 'consecutive_snapshot_transition_count', consecutive_snapshot_transition_count::DECIMAL(24,6) FROM transition_summary
UNION ALL SELECT 'transitions', NULL::DATE, 'changed_nonblank_value_transition_count', changed_nonblank_value_transition_count::DECIMAL(24,6) FROM transition_summary
UNION ALL SELECT 'transitions', NULL::DATE, 'blank_to_populated_transition_count', blank_to_populated_transition_count::DECIMAL(24,6) FROM transition_summary
UNION ALL SELECT 'transitions', NULL::DATE, 'populated_to_blank_transition_count', populated_to_blank_transition_count::DECIMAL(24,6) FROM transition_summary
UNION ALL SELECT 'main_history', first_snapshot_date, 'observation_count', observation_count::DECIMAL(24,6) FROM coverage_summary
UNION ALL SELECT 'main_history', first_snapshot_date, 'minimum_coverage_percent', minimum_coverage_percent::DECIMAL(24,6) FROM coverage_summary
UNION ALL SELECT 'main_history', last_snapshot_date, 'maximum_coverage_percent', maximum_coverage_percent::DECIMAL(24,6) FROM coverage_summary
UNION ALL SELECT 'legacy_history', minimum_snapshot_date, 'distinct_snapshot_count', distinct_snapshot_count::DECIMAL(24,6) FROM legacy_snapshot_history
UNION ALL SELECT 'legacy_history', maximum_snapshot_date, 'distinct_employee_count', distinct_employee_count::DECIMAL(24,6) FROM legacy_snapshot_history
UNION ALL SELECT 'new_hire_context', NULL::DATE, 'current_employee_count', current_employee_count::DECIMAL(24,6) FROM new_hire_context
UNION ALL SELECT 'new_hire_context', NULL::DATE, 'current_populated_count', current_populated_count::DECIMAL(24,6) FROM new_hire_context
UNION ALL SELECT 'new_hire_context', NULL::DATE, 'new_hire_matched_employee_count', new_hire_matched_employee_count::DECIMAL(24,6) FROM new_hire_context
UNION ALL SELECT 'new_hire_context', NULL::DATE, 'new_hire_multivalue_employee_count', new_hire_multivalue_employee_count::DECIMAL(24,6) FROM new_hire_context
UNION ALL SELECT 'new_hire_context', NULL::DATE, 'comparable_populated_employee_count', comparable_populated_employee_count::DECIMAL(24,6) FROM new_hire_context
UNION ALL SELECT 'new_hire_context', NULL::DATE, 'exact_normalized_agreement_count', exact_normalized_agreement_count::DECIMAL(24,6) FROM new_hire_context
UNION ALL SELECT 'new_hire_context', NULL::DATE, 'normalized_disagreement_count', normalized_disagreement_count::DECIMAL(24,6) FROM new_hire_context
ORDER BY metric_group, snapshot_date, metric_name;
