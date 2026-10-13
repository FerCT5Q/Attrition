/*
  Distribucion actual y attrition voluntaria anual por BU L3 para la poblacion
  Engineering del playbook interno.

  Clasificacion: internal_analysis.
  Poblacion: Employee, Regular, active_status = 1, RF360 = 0,
    TRIM(eng_or_noneng) = 'Engineering'.
  Distribucion: foto fiscal 2026-08-23.
  Attrition: cohorte fija 2025-08-24 y al menos una salida con
    UPPER(TRIM(term_type)) = 'VOLUNTARY' en (2025-08-24, 2026-08-23].

  BU L3 es un grouped_mapping temporal:
    post_hire_monthly_worker_dtls.cost_centerid = d_department.nk_dept_id
    y la version vigente cumple [edw_effective_dt, edw_end_dt).

  Regla de aceptacion:
  - una sola persona por snapshot despues de deduplicar la fuente;
  - cost_center_value_count <= 1 por persona-snapshot;
  - valid_mapping_rows <= 1 y valid_bu_value_count <= 1;
  - faltantes se conservan como (unknown);
  - categorias actuales con menos de 30 personas se agregan sin revelar su etiqueta;
  - por instruccion del usuario para este analisis interno, una tasa se muestra
    con baseline >= 30 aunque tenga menos de 30 salidas voluntarias;
  - las tasas con menos de 30 salidas se marcan como direccionales.
  - el grupo agregado Other BU L3 puede quedar debajo de 30 por la autorizacion
    interna config/bu_l3_internal_analysis_authorization_20261013.json; no se
    devuelven las etiquetas originales que lo componen.

  La salida es exclusivamente agregada. employee_id se usa dentro de CTEs y
  agregaciones, pero nunca se devuelve.
*/
WITH params AS (
  SELECT
    DATE '2025-08-24' AS baseline_snapshot_date,
    DATE '2026-08-23' AS current_snapshot_date,
    30::INTEGER AS publication_minimum
),
snapshot_source AS (
  SELECT
    CAST(p.fis_mo_end_dt AS DATE) AS snapshot_date,
    p.employee_id,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT NULLIF(TRIM(CAST(p.cost_centerid AS VARCHAR(256))), '')) AS cost_center_value_count,
    MAX(NULLIF(TRIM(CAST(p.cost_centerid AS VARCHAR(256))), '')) AS cost_centerid
  FROM hrda.post_hire_monthly_worker_dtls p
  WHERE CAST(p.fis_mo_end_dt AS DATE) IN (
      (SELECT baseline_snapshot_date FROM params),
      (SELECT current_snapshot_date FROM params)
    )
    AND p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
    AND p.is_rf360_yes_no = 0
    AND TRIM(p.eng_or_noneng) = 'Engineering'
    AND p.employee_id IS NOT NULL
  GROUP BY 1, 2
),
mapping_matches AS (
  SELECT
    s.snapshot_date,
    s.employee_id,
    s.source_row_count,
    s.cost_center_value_count,
    s.cost_centerid,
    NULLIF(TRIM(CAST(d.ude_bu_reporting_l3 AS VARCHAR(512))), '') AS bu_l3,
    d.edw_effective_dt,
    d.edw_end_dt
  FROM snapshot_source s
  LEFT JOIN hrda.d_department d
    ON CAST(d.nk_dept_id AS VARCHAR(256)) = s.cost_centerid
   AND CAST(d.edw_effective_dt AS DATE) <= s.snapshot_date
   AND (
        d.edw_end_dt IS NULL
        OR s.snapshot_date < CAST(d.edw_end_dt AS DATE)
   )
),
employee_snapshot AS (
  SELECT
    snapshot_date,
    employee_id,
    MAX(source_row_count) AS source_row_count,
    MAX(cost_center_value_count) AS cost_center_value_count,
    MAX(CASE WHEN cost_centerid IS NOT NULL THEN 1 ELSE 0 END) AS has_cost_center,
    COUNT(edw_effective_dt) AS valid_mapping_rows,
    COUNT(DISTINCT bu_l3) AS valid_bu_value_count,
    COALESCE(MAX(bu_l3), '(unknown)') AS bu_l3
  FROM mapping_matches
  GROUP BY 1, 2
),
snapshot_quality AS (
  SELECT
    snapshot_date,
    SUM(source_row_count) AS source_rows,
    COUNT(*) AS distinct_employees,
    SUM(source_row_count - 1) AS duplicate_source_rows,
    SUM(CASE WHEN cost_center_value_count > 1 THEN 1 ELSE 0 END) AS contradictory_cost_center_employee_snapshots,
    SUM(CASE WHEN has_cost_center = 0 THEN 1 ELSE 0 END) AS missing_cost_center_employee_snapshots,
    SUM(CASE WHEN valid_mapping_rows = 0 THEN 1 ELSE 0 END) AS unmatched_mapping_employee_snapshots,
    SUM(CASE WHEN valid_mapping_rows > 1 THEN 1 ELSE 0 END) AS duplicate_valid_mapping_employee_snapshots,
    SUM(CASE WHEN valid_bu_value_count > 1 THEN 1 ELSE 0 END) AS multi_bu_employee_snapshots,
    SUM(CASE WHEN bu_l3 = '(unknown)' THEN 1 ELSE 0 END) AS unknown_bu_employee_snapshots
  FROM employee_snapshot
  GROUP BY 1
),
current_counts AS (
  SELECT
    bu_l3,
    COUNT(*) AS current_employee_count
  FROM employee_snapshot
  WHERE snapshot_date = (SELECT current_snapshot_date FROM params)
  GROUP BY 1
),
publishable_current_labels AS (
  SELECT bu_l3
  FROM current_counts
  WHERE current_employee_count >= (SELECT publication_minimum FROM params)
),
current_display AS (
  SELECT
    CASE
      WHEN p.bu_l3 IS NOT NULL THEN c.bu_l3
      ELSE 'Other BU L3 (<30)'
    END AS category_label,
    SUM(c.current_employee_count) AS current_employee_count
  FROM current_counts c
  LEFT JOIN publishable_current_labels p
    ON p.bu_l3 = c.bu_l3
  GROUP BY 1
),
voluntary_events AS (
  SELECT
    p.employee_id,
    MIN(CAST(p.term_date AS DATE)) AS first_voluntary_term_date
  FROM hrda.post_hire_monthly_worker_dtls p
  WHERE p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(p.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND CAST(p.term_date AS DATE) > (SELECT baseline_snapshot_date FROM params)
    AND CAST(p.term_date AS DATE) <= (SELECT current_snapshot_date FROM params)
    AND p.employee_id IS NOT NULL
  GROUP BY 1
),
baseline_targets AS (
  SELECT
    b.employee_id,
    CASE
      WHEN p.bu_l3 IS NOT NULL THEN b.bu_l3
      ELSE 'Other BU L3 (<30)'
    END AS category_label,
    CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END AS voluntary_exit_flag
  FROM employee_snapshot b
  LEFT JOIN publishable_current_labels p
    ON p.bu_l3 = b.bu_l3
  LEFT JOIN voluntary_events v
    ON v.employee_id = b.employee_id
  WHERE b.snapshot_date = (SELECT baseline_snapshot_date FROM params)
),
baseline_metrics AS (
  SELECT
    category_label,
    COUNT(*) AS baseline_employee_count,
    SUM(voluntary_exit_flag) AS voluntary_exit_count,
    100.0 * SUM(voluntary_exit_flag) / NULLIF(COUNT(*), 0) AS annual_attrition_rate_percent
  FROM baseline_targets
  GROUP BY 1
),
display_rows AS (
  SELECT
    c.category_label,
    c.current_employee_count,
    100.0 * c.current_employee_count
      / NULLIF(SUM(c.current_employee_count) OVER (), 0) AS current_share_percent,
    COALESCE(b.baseline_employee_count, 0) AS baseline_employee_count,
    COALESCE(b.voluntary_exit_count, 0) AS voluntary_exit_count,
    CASE
      WHEN COALESCE(b.baseline_employee_count, 0) >= (SELECT publication_minimum FROM params)
      THEN b.annual_attrition_rate_percent
      ELSE NULL
    END AS annual_attrition_rate_percent,
    CASE
      WHEN c.current_employee_count < (SELECT publication_minimum FROM params)
       AND c.category_label <> 'Other BU L3 (<30)'
        THEN 'suppressed_current_cohort_lt_30'
      WHEN COALESCE(b.baseline_employee_count, 0) < (SELECT publication_minimum FROM params)
        THEN 'suppressed_baseline_cohort_lt_30'
      WHEN COALESCE(b.voluntary_exit_count, 0) < (SELECT publication_minimum FROM params)
        THEN 'directional_voluntary_events_lt_30'
      ELSE 'publishable'
    END AS publication_status
  FROM current_display c
  LEFT JOIN baseline_metrics b
    ON b.category_label = c.category_label
),
overall_attrition AS (
  SELECT
    COUNT(*) AS baseline_employee_count,
    SUM(voluntary_exit_flag) AS voluntary_exit_count,
    100.0 * SUM(voluntary_exit_flag) / NULLIF(COUNT(*), 0) AS annual_attrition_rate_percent
  FROM baseline_targets
),
summary AS (
  SELECT
    'summary' AS row_type,
    CAST(NULL AS INTEGER) AS display_order,
    CAST(NULL AS VARCHAR(512)) AS category_label,
    p.current_snapshot_date,
    p.baseline_snapshot_date,
    cq.source_rows AS current_source_rows,
    cq.distinct_employees AS current_distinct_employees,
    cq.duplicate_source_rows AS current_duplicate_source_rows,
    cq.contradictory_cost_center_employee_snapshots AS current_contradictory_cost_centers,
    cq.missing_cost_center_employee_snapshots AS current_missing_cost_centers,
    cq.unmatched_mapping_employee_snapshots AS current_unmatched_mappings,
    cq.duplicate_valid_mapping_employee_snapshots AS current_duplicate_valid_mappings,
    cq.multi_bu_employee_snapshots AS current_multi_bu_mappings,
    cq.unknown_bu_employee_snapshots AS current_unknown_bu,
    bq.source_rows AS baseline_source_rows,
    bq.distinct_employees AS baseline_distinct_employees,
    bq.duplicate_source_rows AS baseline_duplicate_source_rows,
    bq.contradictory_cost_center_employee_snapshots AS baseline_contradictory_cost_centers,
    bq.missing_cost_center_employee_snapshots AS baseline_missing_cost_centers,
    bq.unmatched_mapping_employee_snapshots AS baseline_unmatched_mappings,
    bq.duplicate_valid_mapping_employee_snapshots AS baseline_duplicate_valid_mappings,
    bq.multi_bu_employee_snapshots AS baseline_multi_bu_mappings,
    bq.unknown_bu_employee_snapshots AS baseline_unknown_bu,
    (SELECT COUNT(*) FROM current_counts) AS current_raw_bu_category_count,
    (SELECT COUNT(*) FROM display_rows) AS displayed_bu_category_count,
    CAST(NULL AS BIGINT) AS current_employee_count,
    CAST(NULL AS DECIMAL(18, 4)) AS current_share_percent,
    oa.baseline_employee_count,
    oa.voluntary_exit_count,
    ROUND(oa.annual_attrition_rate_percent, 4) AS annual_attrition_rate_percent,
    'aggregate_quality' AS publication_status
  FROM params p
  INNER JOIN snapshot_quality cq
    ON cq.snapshot_date = p.current_snapshot_date
  INNER JOIN snapshot_quality bq
    ON bq.snapshot_date = p.baseline_snapshot_date
  CROSS JOIN overall_attrition oa
),
categories AS (
  SELECT
    'category' AS row_type,
    ROW_NUMBER() OVER (
      ORDER BY d.current_employee_count DESC, d.category_label
    ) AS display_order,
    d.category_label,
    p.current_snapshot_date,
    p.baseline_snapshot_date,
    CAST(NULL AS BIGINT) AS current_source_rows,
    CAST(NULL AS BIGINT) AS current_distinct_employees,
    CAST(NULL AS BIGINT) AS current_duplicate_source_rows,
    CAST(NULL AS BIGINT) AS current_contradictory_cost_centers,
    CAST(NULL AS BIGINT) AS current_missing_cost_centers,
    CAST(NULL AS BIGINT) AS current_unmatched_mappings,
    CAST(NULL AS BIGINT) AS current_duplicate_valid_mappings,
    CAST(NULL AS BIGINT) AS current_multi_bu_mappings,
    CAST(NULL AS BIGINT) AS current_unknown_bu,
    CAST(NULL AS BIGINT) AS baseline_source_rows,
    CAST(NULL AS BIGINT) AS baseline_distinct_employees,
    CAST(NULL AS BIGINT) AS baseline_duplicate_source_rows,
    CAST(NULL AS BIGINT) AS baseline_contradictory_cost_centers,
    CAST(NULL AS BIGINT) AS baseline_missing_cost_centers,
    CAST(NULL AS BIGINT) AS baseline_unmatched_mappings,
    CAST(NULL AS BIGINT) AS baseline_duplicate_valid_mappings,
    CAST(NULL AS BIGINT) AS baseline_multi_bu_mappings,
    CAST(NULL AS BIGINT) AS baseline_unknown_bu,
    CAST(NULL AS BIGINT) AS current_raw_bu_category_count,
    CAST(NULL AS BIGINT) AS displayed_bu_category_count,
    d.current_employee_count,
    ROUND(d.current_share_percent, 4) AS current_share_percent,
    d.baseline_employee_count,
    d.voluntary_exit_count,
    ROUND(d.annual_attrition_rate_percent, 4) AS annual_attrition_rate_percent,
    d.publication_status
  FROM display_rows d
  CROSS JOIN params p
)
SELECT
  row_type, display_order, category_label, current_snapshot_date,
  baseline_snapshot_date, current_source_rows, current_distinct_employees,
  current_duplicate_source_rows, current_contradictory_cost_centers,
  current_missing_cost_centers, current_unmatched_mappings,
  current_duplicate_valid_mappings, current_multi_bu_mappings,
  current_unknown_bu, baseline_source_rows, baseline_distinct_employees,
  baseline_duplicate_source_rows, baseline_contradictory_cost_centers,
  baseline_missing_cost_centers, baseline_unmatched_mappings,
  baseline_duplicate_valid_mappings, baseline_multi_bu_mappings,
  baseline_unknown_bu, current_raw_bu_category_count,
  displayed_bu_category_count, current_employee_count,
  current_share_percent, baseline_employee_count, voluntary_exit_count,
  annual_attrition_rate_percent, publication_status
FROM summary
UNION ALL
SELECT
  row_type, display_order, category_label, current_snapshot_date,
  baseline_snapshot_date, current_source_rows, current_distinct_employees,
  current_duplicate_source_rows, current_contradictory_cost_centers,
  current_missing_cost_centers, current_unmatched_mappings,
  current_duplicate_valid_mappings, current_multi_bu_mappings,
  current_unknown_bu, baseline_source_rows, baseline_distinct_employees,
  baseline_duplicate_source_rows, baseline_contradictory_cost_centers,
  baseline_missing_cost_centers, baseline_unmatched_mappings,
  baseline_duplicate_valid_mappings, baseline_multi_bu_mappings,
  baseline_unknown_bu, current_raw_bu_category_count,
  displayed_bu_category_count, current_employee_count,
  current_share_percent, baseline_employee_count, voluntary_exit_count,
  annual_attrition_rate_percent, publication_status
FROM categories
ORDER BY row_type DESC, display_order;
