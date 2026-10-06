WITH target_rows AS (
  SELECT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    manager_employee_id,
    region,
    job_family,
    job_family_group,
    job_level_primary_position,
    level_grouped,
    COALESCE(max_hire_rehire_date, service_date, original_hire_date) AS tenure_start_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
), target_people AS (
  SELECT DISTINCT employee_id
  FROM target_rows
), snapshot_rollup AS (
  SELECT
    employee_id,
    snapshot_date,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT manager_employee_id) AS manager_values,
    COUNT(DISTINCT NULLIF(TRIM(region), '')) AS region_values,
    COUNT(DISTINCT NULLIF(TRIM(job_family), '')) AS job_family_detail_values,
    COUNT(DISTINCT NULLIF(TRIM(job_family_group), '')) AS job_family_values,
    COUNT(DISTINCT NULLIF(TRIM(job_level_primary_position), '')) AS job_level_detail_values,
    COUNT(DISTINCT NULLIF(TRIM(level_grouped), '')) AS level_values,
    COUNT(DISTINCT tenure_start_date) AS tenure_date_values,
    SUM(CASE WHEN tenure_start_date > snapshot_date THEN 1 ELSE 0 END) AS future_tenure_rows
  FROM target_rows
  GROUP BY employee_id, snapshot_date
), snapshot_quality AS (
  SELECT
    COUNT(*) AS employee_snapshot_count,
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS duplicate_employee_snapshot_rows,
    COALESCE(SUM(CASE
      WHEN manager_values > 1
        OR region_values > 1
        OR job_family_detail_values > 1
        OR job_family_values > 1
        OR job_level_detail_values > 1
        OR level_values > 1
        OR tenure_date_values > 1
      THEN 1 ELSE 0 END), 0) AS conflicting_employee_snapshot_count,
    COALESCE(SUM(future_tenure_rows), 0) AS future_tenure_rows
  FROM snapshot_rollup
), job_family_snapshot_mapping AS (
  SELECT
    snapshot_date,
    NULLIF(TRIM(job_family), '') AS detail_value,
    COUNT(DISTINCT NULLIF(TRIM(job_family_group), '')) AS group_values
  FROM target_rows
  WHERE NULLIF(TRIM(job_family), '') IS NOT NULL
  GROUP BY snapshot_date, NULLIF(TRIM(job_family), '')
), job_family_history_mapping AS (
  SELECT
    NULLIF(TRIM(job_family), '') AS detail_value,
    COUNT(DISTINCT NULLIF(TRIM(job_family_group), '')) AS group_values
  FROM target_rows
  WHERE NULLIF(TRIM(job_family), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(job_family), '')
), level_snapshot_mapping AS (
  SELECT
    snapshot_date,
    NULLIF(TRIM(job_level_primary_position), '') AS detail_value,
    COUNT(DISTINCT NULLIF(TRIM(level_grouped), '')) AS group_values
  FROM target_rows
  WHERE NULLIF(TRIM(job_level_primary_position), '') IS NOT NULL
  GROUP BY snapshot_date, NULLIF(TRIM(job_level_primary_position), '')
), level_history_mapping AS (
  SELECT
    NULLIF(TRIM(job_level_primary_position), '') AS detail_value,
    COUNT(DISTINCT NULLIF(TRIM(level_grouped), '')) AS group_values
  FROM target_rows
  WHERE NULLIF(TRIM(job_level_primary_position), '') IS NOT NULL
  GROUP BY NULLIF(TRIM(job_level_primary_position), '')
), mapping_quality AS (
  SELECT
    (SELECT COUNT(*) FROM job_family_snapshot_mapping WHERE group_values > 1) AS job_family_mapping_contradiction_count,
    (SELECT COUNT(*) FROM level_snapshot_mapping WHERE group_values > 1) AS level_mapping_contradiction_count,
    (SELECT COUNT(*) FROM job_family_history_mapping WHERE group_values > 1) AS job_family_values_with_mapping_changes,
    (SELECT COUNT(*) FROM level_history_mapping WHERE group_values > 1) AS level_values_with_mapping_changes,
    (SELECT COUNT(*) FROM target_rows
      WHERE (NULLIF(TRIM(job_family), '') IS NOT NULL AND NULLIF(TRIM(job_family_group), '') IS NULL)
         OR (NULLIF(TRIM(job_level_primary_position), '') IS NOT NULL AND NULLIF(TRIM(level_grouped), '') IS NULL)
    ) AS unmapped_group_rows
), event_source AS (
  SELECT
    a.employeeid,
    a.term_date,
    LOWER(TRIM(a.term_type)) AS normalized_term_type
  FROM hrda.all_terminations a
  INNER JOIN target_people p
    ON p.employee_id = a.employeeid
), event_rollup AS (
  SELECT
    employeeid,
    term_date,
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT normalized_term_type) AS term_type_values
  FROM event_source
  GROUP BY employeeid, term_date
), event_quality AS (
  SELECT
    COUNT(*) AS event_key_count,
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS duplicate_event_rows,
    COALESCE(SUM(CASE WHEN term_type_values > 1 THEN 1 ELSE 0 END), 0) AS conflicting_event_type_count
  FROM event_rollup
), event_domain AS (
  SELECT
    COUNT(*) AS event_rows,
    COALESCE(SUM(CASE WHEN term_date IS NULL THEN 1 ELSE 0 END), 0) AS null_term_date_rows,
    COALESCE(SUM(CASE WHEN normalized_term_type IS NULL OR normalized_term_type = '' THEN 1 ELSE 0 END), 0) AS blank_term_type_rows,
    COALESCE(SUM(CASE WHEN normalized_term_type = 'voluntary' THEN 1 ELSE 0 END), 0) AS voluntary_event_rows,
    COALESCE(SUM(CASE WHEN normalized_term_type = 'voluntary exception' THEN 1 ELSE 0 END), 0) AS voluntary_exception_event_rows,
    COALESCE(SUM(CASE WHEN normalized_term_type = 'involuntary' THEN 1 ELSE 0 END), 0) AS involuntary_event_rows,
    COALESCE(SUM(CASE
      WHEN normalized_term_type IS NOT NULL
       AND normalized_term_type <> ''
       AND normalized_term_type NOT IN ('voluntary', 'voluntary exception', 'involuntary')
      THEN 1 ELSE 0 END), 0) AS unclassified_term_type_rows,
    COUNT(DISTINCT normalized_term_type) AS normalized_term_type_count
  FROM event_source
), history AS (
  SELECT COUNT(DISTINCT snapshot_date) AS months_checked
  FROM target_rows
)
SELECT
  'High risk manager' AS variable_name,
  (s.employee_snapshot_count + d.event_rows) AS observations_checked,
  h.months_checked,
  s.employee_snapshot_count,
  d.event_rows,
  e.event_key_count,
  s.duplicate_employee_snapshot_rows,
  s.conflicting_employee_snapshot_count,
  s.future_tenure_rows,
  e.duplicate_event_rows,
  e.conflicting_event_type_count,
  d.null_term_date_rows,
  d.blank_term_type_rows,
  d.unclassified_term_type_rows,
  d.normalized_term_type_count,
  d.voluntary_event_rows,
  d.voluntary_exception_event_rows,
  d.involuntary_event_rows,
  m.job_family_mapping_contradiction_count,
  m.level_mapping_contradiction_count,
  m.job_family_values_with_mapping_changes,
  m.level_values_with_mapping_changes,
  m.unmapped_group_rows,
  (
    s.duplicate_employee_snapshot_rows
    + s.conflicting_employee_snapshot_count
    + s.future_tenure_rows
    + e.duplicate_event_rows
    + e.conflicting_event_type_count
    + d.null_term_date_rows
    + d.blank_term_type_rows
    + d.unclassified_term_type_rows
    + m.job_family_mapping_contradiction_count
    + m.level_mapping_contradiction_count
    + m.unmapped_group_rows
  ) AS anomaly_count,
  (
    s.future_tenure_rows
    + d.null_term_date_rows
    + d.blank_term_type_rows
    + d.unclassified_term_type_rows
    + m.unmapped_group_rows
  ) AS invalid_count,
  (
    s.duplicate_employee_snapshot_rows
    + s.conflicting_employee_snapshot_count
    + e.duplicate_event_rows
    + e.conflicting_event_type_count
    + m.job_family_mapping_contradiction_count
    + m.level_mapping_contradiction_count
  ) AS unexplained_change_count
FROM snapshot_quality s
CROSS JOIN event_quality e
CROSS JOIN event_domain d
CROSS JOIN history h
CROSS JOIN mapping_quality m;
