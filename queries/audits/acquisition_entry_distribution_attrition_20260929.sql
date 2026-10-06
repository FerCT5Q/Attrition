-- Distribución y attrition anual para Ingreso por adquisición.
-- Modo de entrega: presentation. Sin filas ni identificadores en la salida.
-- Regla v2: current=2026-08-23; baseline=2025-08-24; sólo la etiqueta
-- UPPER(TRIM(term_type)) exactamente VOLUNTARY y term_date en (baseline,
-- current], una salida por persona.
WITH snapshot_rows AS (
    SELECT
        fis_mo_end_dt AS snapshot_date,
        CAST(employee_id AS VARCHAR(256)) AS employee_key,
        NULLIF(TRIM(acquisition), '') AS acquisition_trimmed,
        UPPER(NULLIF(TRIM(acquisition), '')) AS acquisition_normalized
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt IN (DATE '2025-08-24', DATE '2026-08-23')
),
snapshot_employee AS (
    SELECT
        snapshot_date,
        employee_key,
        COUNT(*) AS raw_row_count,
        COUNT(DISTINCT acquisition_normalized) AS acquisition_value_count,
        MAX(acquisition_normalized) AS acquisition_normalized,
        MIN(acquisition_trimmed) AS acquisition_display_label
    FROM snapshot_rows
    GROUP BY snapshot_date, employee_key
),
snapshot_quality AS (
    SELECT
        snapshot_date,
        SUM(raw_row_count) AS raw_row_count,
        COUNT(*) AS distinct_employee_count,
        SUM(raw_row_count - 1) AS duplicate_excess_row_count,
        SUM(CASE WHEN raw_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN acquisition_value_count > 1 THEN 1 ELSE 0 END) AS contradictory_employee_snapshot_count
    FROM snapshot_employee
    GROUP BY snapshot_date
),
current_population AS (
    SELECT
        snapshot_date,
        employee_key,
        raw_row_count,
        acquisition_value_count,
        acquisition_normalized,
        acquisition_display_label
    FROM snapshot_employee
    WHERE snapshot_date = DATE '2026-08-23'
),
baseline_population AS (
    SELECT
        snapshot_date,
        employee_key,
        raw_row_count,
        acquisition_value_count,
        acquisition_normalized,
        acquisition_display_label
    FROM snapshot_employee
    WHERE snapshot_date = DATE '2025-08-24'
),
main_voluntary_events AS (
    SELECT
        CAST(employee_id AS VARCHAR(256)) AS employee_key,
        MIN(term_date) AS term_date,
        COUNT(*) AS raw_event_row_count
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date > DATE '2025-08-24'
      AND term_date <= DATE '2026-08-23'
    GROUP BY CAST(employee_id AS VARCHAR(256))
),
all_termination_voluntary_events AS (
    SELECT
        CAST(employeeid AS VARCHAR(256)) AS employee_key,
        MIN(term_date) AS term_date,
        COUNT(*) AS raw_event_row_count
    FROM hrda.all_terminations
    WHERE UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date > DATE '2025-08-24'
      AND term_date <= DATE '2026-08-23'
    GROUP BY CAST(employeeid AS VARCHAR(256))
),
baseline_with_event AS (
    SELECT
        b.employee_key,
        b.acquisition_normalized,
        b.acquisition_display_label,
        CASE WHEN e.employee_key IS NOT NULL THEN 1 ELSE 0 END AS voluntary_exit_flag
    FROM baseline_population b
    LEFT JOIN main_voluntary_events e
      ON e.employee_key = b.employee_key
),
overall_current AS (
    SELECT
        CASE
            WHEN acquisition_normalized IS NOT NULL THEN 'Con adquisición registrada'
            ELSE 'Sin adquisición registrada'
        END AS segment_label,
        COUNT(*) AS current_employee_count
    FROM current_population
    GROUP BY 1
),
overall_baseline AS (
    SELECT
        CASE
            WHEN acquisition_normalized IS NOT NULL THEN 'Con adquisición registrada'
            ELSE 'Sin adquisición registrada'
        END AS segment_label,
        COUNT(*) AS baseline_employee_count,
        SUM(voluntary_exit_flag) AS voluntary_exit_count
    FROM baseline_with_event
    GROUP BY 1
),
overall_rows AS (
    SELECT
        c.segment_label,
        c.current_employee_count,
        b.baseline_employee_count,
        b.voluntary_exit_count
    FROM overall_current c
    LEFT JOIN overall_baseline b
      ON b.segment_label = c.segment_label
),
current_acquisition AS (
    SELECT
        acquisition_normalized,
        MIN(acquisition_display_label) AS acquisition_display_label,
        COUNT(*) AS current_employee_count
    FROM current_population
    WHERE acquisition_normalized IS NOT NULL
    GROUP BY acquisition_normalized
),
ranked_current_acquisition AS (
    SELECT
        acquisition_normalized,
        acquisition_display_label,
        current_employee_count,
        ROW_NUMBER() OVER (
            ORDER BY current_employee_count DESC, acquisition_normalized
        ) AS acquisition_rank
    FROM current_acquisition
),
top_current_acquisition AS (
    SELECT
        acquisition_normalized,
        acquisition_display_label,
        current_employee_count,
        acquisition_rank
    FROM ranked_current_acquisition
    WHERE acquisition_rank <= 10
),
acquisition_categories AS (
    SELECT
        acquisition_normalized AS category_key,
        acquisition_display_label AS segment_label,
        acquisition_rank AS segment_order
    FROM top_current_acquisition
    UNION ALL
    SELECT '__OTHER__' AS category_key, 'Otras adquisiciones' AS segment_label, 11 AS segment_order
),
top_current AS (
    SELECT
        COALESCE(t.acquisition_normalized, '__OTHER__') AS category_key,
        COUNT(*) AS current_employee_count
    FROM current_population c
    LEFT JOIN top_current_acquisition t
      ON t.acquisition_normalized = c.acquisition_normalized
    WHERE c.acquisition_normalized IS NOT NULL
    GROUP BY 1
),
top_baseline AS (
    SELECT
        COALESCE(t.acquisition_normalized, '__OTHER__') AS category_key,
        COUNT(*) AS baseline_employee_count,
        SUM(b.voluntary_exit_flag) AS voluntary_exit_count
    FROM baseline_with_event b
    LEFT JOIN top_current_acquisition t
      ON t.acquisition_normalized = b.acquisition_normalized
    WHERE b.acquisition_normalized IS NOT NULL
    GROUP BY 1
),
top_rows AS (
    SELECT
        c.segment_order,
        c.segment_label,
        c.category_key,
        COALESCE(curr.current_employee_count, 0) AS current_employee_count,
        COALESCE(base.baseline_employee_count, 0) AS baseline_employee_count,
        COALESCE(base.voluntary_exit_count, 0) AS voluntary_exit_count
    FROM acquisition_categories c
    LEFT JOIN top_current curr
      ON curr.category_key = c.category_key
    LEFT JOIN top_baseline base
      ON base.category_key = c.category_key
),
totals AS (
    SELECT
        (SELECT COUNT(*) FROM current_population) AS current_population_count,
        (SELECT COUNT(*) FROM baseline_population) AS baseline_population_count,
        (SELECT COUNT(*) FROM current_population WHERE acquisition_normalized IS NOT NULL) AS current_acquired_count,
        (SELECT COUNT(*) FROM baseline_population WHERE acquisition_normalized IS NOT NULL) AS baseline_acquired_count,
        (SELECT SUM(voluntary_exit_flag) FROM baseline_with_event) AS baseline_voluntary_exit_count,
        (SELECT COUNT(*) FROM main_voluntary_events) AS main_voluntary_source_event_count,
        (SELECT SUM(raw_event_row_count - 1) FROM main_voluntary_events) AS main_voluntary_duplicate_event_row_count
),
term_reconciliation AS (
    SELECT
        SUM(CASE WHEN m.employee_key IS NOT NULL THEN 1 ELSE 0 END) AS main_cohort_event_count,
        SUM(CASE WHEN a.employee_key IS NOT NULL THEN 1 ELSE 0 END) AS all_terminations_cohort_event_count,
        SUM(CASE WHEN m.employee_key IS NOT NULL AND a.employee_key IS NOT NULL THEN 1 ELSE 0 END) AS matching_employee_date_event_count,
        SUM(CASE WHEN m.employee_key IS NOT NULL AND a.employee_key IS NULL THEN 1 ELSE 0 END) AS main_only_employee_date_event_count,
        SUM(CASE WHEN m.employee_key IS NULL AND a.employee_key IS NOT NULL THEN 1 ELSE 0 END) AS all_terminations_only_employee_date_event_count
    FROM (
        SELECT b.employee_key, e.term_date
        FROM baseline_population b
        INNER JOIN main_voluntary_events e
          ON e.employee_key = b.employee_key
    ) m
    FULL OUTER JOIN (
        SELECT b.employee_key, e.term_date
        FROM baseline_population b
        INNER JOIN all_termination_voluntary_events e
          ON e.employee_key = b.employee_key
    ) a
      ON a.employee_key = m.employee_key
     AND a.term_date = m.term_date
)
SELECT
    'overall_segment' AS row_type,
    CASE o.segment_label
        WHEN 'Con adquisición registrada' THEN 1
        ELSE 2
    END AS row_order,
    o.segment_label,
    CAST(NULL AS VARCHAR(256)) AS category_key,
    o.current_employee_count,
    t.current_population_count AS current_denominator_count,
    100.0 * o.current_employee_count / NULLIF(t.current_population_count, 0) AS current_share_percent,
    o.baseline_employee_count,
    t.baseline_population_count AS baseline_denominator_count,
    o.voluntary_exit_count,
    CASE
        WHEN o.baseline_employee_count >= 30 AND o.voluntary_exit_count >= 30
        THEN 100.0 * o.voluntary_exit_count / NULLIF(o.baseline_employee_count, 0)
        ELSE NULL
    END AS annual_attrition_rate_percent,
    CASE
        WHEN o.current_employee_count < 30 THEN 'suppressed_current_cohort_lt_30'
        WHEN o.baseline_employee_count = 0 THEN 'no_annual_comparable_cohort'
        WHEN o.baseline_employee_count < 30 THEN 'suppressed_baseline_cohort_lt_30'
        WHEN o.voluntary_exit_count < 30 THEN 'suppressed_voluntary_events_lt_30'
        ELSE 'publishable'
    END AS publication_status
FROM overall_rows o
CROSS JOIN totals t
UNION ALL
SELECT
    'top_acquisition' AS row_type,
    r.segment_order AS row_order,
    r.segment_label,
    r.category_key,
    r.current_employee_count,
    t.current_acquired_count AS current_denominator_count,
    100.0 * r.current_employee_count / NULLIF(t.current_acquired_count, 0) AS current_share_percent,
    r.baseline_employee_count,
    t.baseline_acquired_count AS baseline_denominator_count,
    r.voluntary_exit_count,
    CASE
        WHEN r.baseline_employee_count >= 30 AND r.voluntary_exit_count >= 30
        THEN 100.0 * r.voluntary_exit_count / NULLIF(r.baseline_employee_count, 0)
        ELSE NULL
    END AS annual_attrition_rate_percent,
    CASE
        WHEN r.current_employee_count < 30 THEN 'suppressed_current_cohort_lt_30'
        WHEN r.baseline_employee_count = 0 THEN 'no_annual_comparable_cohort'
        WHEN r.baseline_employee_count < 30 THEN 'suppressed_baseline_cohort_lt_30'
        WHEN r.voluntary_exit_count < 30 THEN 'suppressed_voluntary_events_lt_30'
        ELSE 'publishable'
    END AS publication_status
FROM top_rows r
CROSS JOIN totals t
UNION ALL
SELECT
    'snapshot_reconciliation' AS row_type,
    1 AS row_order,
    'Snapshot 2025-08-24' AS segment_label,
    CAST(NULL AS VARCHAR(256)) AS category_key,
    q.raw_row_count AS current_employee_count,
    q.distinct_employee_count AS current_denominator_count,
    q.duplicate_excess_row_count AS current_share_percent,
    q.duplicate_employee_snapshot_count AS baseline_employee_count,
    q.contradictory_employee_snapshot_count AS baseline_denominator_count,
    CAST(NULL AS BIGINT) AS voluntary_exit_count,
    CAST(NULL AS DECIMAL(24,6)) AS annual_attrition_rate_percent,
    'aggregate_quality_metrics' AS publication_status
FROM snapshot_quality q
WHERE q.snapshot_date = DATE '2025-08-24'
UNION ALL
SELECT
    'snapshot_reconciliation' AS row_type,
    2 AS row_order,
    'Snapshot 2026-08-23' AS segment_label,
    CAST(NULL AS VARCHAR(256)) AS category_key,
    q.raw_row_count AS current_employee_count,
    q.distinct_employee_count AS current_denominator_count,
    q.duplicate_excess_row_count AS current_share_percent,
    q.duplicate_employee_snapshot_count AS baseline_employee_count,
    q.contradictory_employee_snapshot_count AS baseline_denominator_count,
    CAST(NULL AS BIGINT) AS voluntary_exit_count,
    CAST(NULL AS DECIMAL(24,6)) AS annual_attrition_rate_percent,
    'aggregate_quality_metrics' AS publication_status
FROM snapshot_quality q
WHERE q.snapshot_date = DATE '2026-08-23'
UNION ALL
SELECT
    'term_source_reconciliation' AS row_type,
    1 AS row_order,
    'Voluntary exits in baseline cohort' AS segment_label,
    CAST(NULL AS VARCHAR(256)) AS category_key,
    tr.main_cohort_event_count AS current_employee_count,
    tr.all_terminations_cohort_event_count AS current_denominator_count,
    tr.matching_employee_date_event_count AS current_share_percent,
    tr.main_only_employee_date_event_count AS baseline_employee_count,
    tr.all_terminations_only_employee_date_event_count AS baseline_denominator_count,
    t.main_voluntary_duplicate_event_row_count AS voluntary_exit_count,
    CAST(NULL AS DECIMAL(24,6)) AS annual_attrition_rate_percent,
    'contextual_source_comparison' AS publication_status
FROM term_reconciliation tr
CROSS JOIN totals t
ORDER BY row_type, row_order;
