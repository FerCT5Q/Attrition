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
    max_hire_rehire_date,
    service_date,
    original_hire_date,
    COALESCE(
      CASE WHEN max_hire_rehire_date <= fis_mo_end_dt THEN max_hire_rehire_date END,
      CASE WHEN service_date <= fis_mo_end_dt THEN service_date END,
      CASE WHEN original_hire_date <= fis_mo_end_dt THEN original_hire_date END
    ) AS selected_tenure_start_date
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
    COUNT(DISTINCT NULLIF(TRIM(job_family), '')) AS job_family_values,
    COUNT(DISTINCT NULLIF(TRIM(job_level_primary_position), '')) AS job_level_values,
    COUNT(DISTINCT selected_tenure_start_date) AS tenure_date_values,
    SUM(CASE WHEN selected_tenure_start_date > snapshot_date THEN 1 ELSE 0 END) AS selected_tenure_future_rows
  FROM target_rows
  GROUP BY employee_id, snapshot_date
), snapshot_quality AS (
  SELECT
    COUNT(*) AS employee_snapshot_count,
    COALESCE(SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END), 0) AS duplicate_employee_snapshot_rows,
    COALESCE(SUM(CASE
      WHEN manager_values > 1
        OR region_values > 1
        OR job_family_values > 1
        OR job_level_values > 1
        OR tenure_date_values > 1
      THEN 1 ELSE 0 END), 0) AS conflicting_employee_snapshot_count,
    COALESCE(SUM(selected_tenure_future_rows), 0) AS selected_tenure_future_rows
  FROM snapshot_rollup
), raw_date_quality AS (
  SELECT
    COALESCE(SUM(CASE WHEN max_hire_rehire_date > snapshot_date THEN 1 ELSE 0 END), 0) AS raw_max_hire_future_rows,
    COALESCE(SUM(CASE WHEN service_date > snapshot_date THEN 1 ELSE 0 END), 0) AS raw_service_future_rows,
    COALESCE(SUM(CASE WHEN original_hire_date > snapshot_date THEN 1 ELSE 0 END), 0) AS raw_original_hire_future_rows,
    COALESCE(SUM(CASE WHEN selected_tenure_start_date IS NULL THEN 1 ELSE 0 END), 0) AS selected_tenure_missing_rows,
    COALESCE(SUM(CASE WHEN NULLIF(TRIM(job_family), '') IS NULL THEN 1 ELSE 0 END), 0) AS selected_job_family_missing_rows,
    COALESCE(SUM(CASE WHEN NULLIF(TRIM(job_level_primary_position), '') IS NULL THEN 1 ELSE 0 END), 0) AS selected_level_missing_rows
  FROM target_rows
), alternative_level_mapping AS (
  SELECT
    snapshot_date,
    NULLIF(TRIM(job_level_primary_position), '') AS detail_value,
    COUNT(DISTINCT NULLIF(TRIM(level_grouped), '')) AS group_values
  FROM target_rows
  WHERE NULLIF(TRIM(job_level_primary_position), '') IS NOT NULL
  GROUP BY snapshot_date, NULLIF(TRIM(job_level_primary_position), '')
), alternative_mapping_quality AS (
  SELECT COUNT(*) AS alternative_level_mapping_contradiction_count
  FROM alternative_level_mapping
  WHERE group_values > 1
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
      THEN 1 ELSE 0 END), 0) AS unclassified_term_type_rows
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
  s.selected_tenure_future_rows,
  r.raw_max_hire_future_rows,
  r.raw_service_future_rows,
  r.raw_original_hire_future_rows,
  r.selected_tenure_missing_rows,
  r.selected_job_family_missing_rows,
  r.selected_level_missing_rows,
  e.duplicate_event_rows,
  e.conflicting_event_type_count,
  d.null_term_date_rows,
  d.blank_term_type_rows,
  d.unclassified_term_type_rows,
  d.voluntary_event_rows,
  d.voluntary_exception_event_rows,
  d.involuntary_event_rows,
  m.alternative_level_mapping_contradiction_count,
  (
    s.duplicate_employee_snapshot_rows
    + s.conflicting_employee_snapshot_count
    + s.selected_tenure_future_rows
    + e.duplicate_event_rows
    + e.conflicting_event_type_count
    + d.null_term_date_rows
    + d.unclassified_term_type_rows
  ) AS anomaly_count,
  (
    s.selected_tenure_future_rows
    + d.null_term_date_rows
    + d.unclassified_term_type_rows
  ) AS invalid_count,
  (
    s.duplicate_employee_snapshot_rows
    + s.conflicting_employee_snapshot_count
    + e.duplicate_event_rows
    + e.conflicting_event_type_count
  ) AS unexplained_change_count
FROM snapshot_quality s
CROSS JOIN raw_date_quality r
CROSS JOIN alternative_mapping_quality m
CROSS JOIN event_quality e
CROSS JOIN event_domain d
CROSS JOIN history h;
