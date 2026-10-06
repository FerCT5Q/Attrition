/*
  QVoice 2026 population diagnostic.

  Purpose:
    Test whether the difference between the Excel raw population and the
    Redshift wave can be explained by workforce eligibility fields or by the
    temporal snapshot selected for the join.

  Privacy:
    Employee IDs are used only inside joins and COUNT(DISTINCT ...). The
    result contains aggregate counts and controlled category labels only.

  Snapshot rule:
    launch_aligned uses the latest workforce snapshot on or before
    survey_launch_date. hierarchy_aligned uses the latest snapshot on or
    before hierarchy_date, as a date-sensitivity check only.
*/
WITH survey_meta AS (
  SELECT
    CAST(survey_launch_date AS DATE) AS survey_launch_date,
    MAX(hierarchy_date) AS hierarchy_date,
    COUNT(DISTINCT hierarchy_date) AS hierarchy_dates_checked,
    COUNT(*) AS qvoice_rows,
    COUNT(DISTINCT emp_id) AS qvoice_distinct_emp_ids,
    COUNT(CASE WHEN emp_id IS NULL THEN 1 END) AS qvoice_null_emp_id_rows
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date = DATE '2026-01-07'
  GROUP BY 1
),
response_key_counts AS (
  SELECT
    CAST(survey_launch_date AS DATE) AS survey_launch_date,
    emp_id,
    COUNT(*) AS response_rows
  FROM hrda.qvoice_survey_data
  WHERE survey_launch_date = DATE '2026-01-07'
    AND emp_id IS NOT NULL
  GROUP BY 1, 2
),
snapshot_dates AS (
  SELECT
    'launch_aligned' AS alignment,
    survey_meta.survey_launch_date,
    survey_meta.hierarchy_date,
    MAX(workers.fis_mo_end_dt) AS snapshot_date
  FROM survey_meta
  JOIN hrda.post_hire_monthly_worker_dtls workers
    ON workers.fis_mo_end_dt <= survey_meta.survey_launch_date
  GROUP BY 1, 2, 3
  UNION ALL
  SELECT
    'hierarchy_aligned' AS alignment,
    survey_meta.survey_launch_date,
    survey_meta.hierarchy_date,
    MAX(workers.fis_mo_end_dt) AS snapshot_date
  FROM survey_meta
  JOIN hrda.post_hire_monthly_worker_dtls workers
    ON workers.fis_mo_end_dt <= survey_meta.hierarchy_date
  GROUP BY 1, 2, 3
),
workforce_key_counts AS (
  SELECT
    snapshot_dates.alignment,
    workers.employee_id,
    workers.worker_type,
    workers.employee_type,
    workers.active_status,
    COUNT(*) AS workforce_rows
  FROM snapshot_dates
  JOIN hrda.post_hire_monthly_worker_dtls workers
    ON workers.fis_mo_end_dt = snapshot_dates.snapshot_date
  GROUP BY 1, 2, 3, 4, 5
),
classified AS (
  SELECT
    snapshot_dates.alignment,
    response_key_counts.emp_id,
    response_key_counts.response_rows,
    workforce_key_counts.employee_id,
    workforce_key_counts.worker_type,
    workforce_key_counts.employee_type,
    workforce_key_counts.active_status,
    workforce_key_counts.workforce_rows,
    CASE
      WHEN workforce_key_counts.employee_id IS NULL
        THEN 'no_match_in_workforce_snapshot'
      WHEN workforce_key_counts.worker_type IS NULL
        OR workforce_key_counts.employee_type IS NULL
        OR workforce_key_counts.active_status IS NULL
        THEN 'matched_with_null_eligibility_field'
      WHEN workforce_key_counts.worker_type = 'Employee'
        AND workforce_key_counts.employee_type = 'Regular'
        AND workforce_key_counts.active_status = 1
        THEN 'employee_regular_active'
      WHEN workforce_key_counts.worker_type = 'Employee'
        AND workforce_key_counts.employee_type = 'Regular'
        AND workforce_key_counts.active_status <> 1
        THEN 'employee_regular_not_active'
      WHEN workforce_key_counts.worker_type = 'Employee'
        AND workforce_key_counts.employee_type <> 'Regular'
        AND workforce_key_counts.active_status = 1
        THEN 'employee_nonregular_active'
      WHEN workforce_key_counts.worker_type = 'Employee'
        AND workforce_key_counts.employee_type <> 'Regular'
        AND workforce_key_counts.active_status <> 1
        THEN 'employee_nonregular_not_active'
      WHEN workforce_key_counts.worker_type <> 'Employee'
        AND workforce_key_counts.active_status = 1
        THEN 'nonemployee_active'
      WHEN workforce_key_counts.worker_type <> 'Employee'
        AND workforce_key_counts.active_status <> 1
        THEN 'nonemployee_not_active'
      ELSE 'other_workforce_classification'
    END AS classification
  FROM snapshot_dates
  CROSS JOIN response_key_counts
  LEFT JOIN workforce_key_counts
    ON workforce_key_counts.alignment = snapshot_dates.alignment
   AND workforce_key_counts.employee_id = response_key_counts.emp_id
  WHERE response_key_counts.survey_launch_date = snapshot_dates.survey_launch_date
),
classification_counts AS (
  SELECT
    alignment,
    classification,
    COUNT(*) AS employee_key_count,
    SUM(response_rows) AS response_row_count
  FROM classified
  GROUP BY 1, 2
),
classification_totals AS (
  SELECT
    alignment,
    COUNT(*) AS qvoice_response_employee_keys,
    SUM(response_rows) AS qvoice_response_rows,
    SUM(CASE WHEN employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_workforce_employee_keys,
    SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END) AS unmatched_workforce_employee_keys,
    SUM(CASE WHEN worker_type = 'Employee' THEN 1 ELSE 0 END) AS worker_type_employee_keys,
    SUM(CASE WHEN employee_type = 'Regular' THEN 1 ELSE 0 END) AS employee_type_regular_keys,
    SUM(CASE WHEN active_status = 1 THEN 1 ELSE 0 END) AS active_status_1_keys,
    SUM(CASE WHEN worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1 THEN 1 ELSE 0 END) AS default_eligible_employee_keys,
    SUM(CASE WHEN workforce_rows > 1 THEN 1 ELSE 0 END) AS duplicate_workforce_employee_keys
  FROM classified
  GROUP BY 1
),
response_quality AS (
  SELECT
    COUNT(*) AS response_employee_keys,
    SUM(response_rows) AS response_rows,
    SUM(CASE WHEN response_rows > 1 THEN 1 ELSE 0 END) AS duplicate_response_employee_keys
  FROM response_key_counts
)
SELECT
  'wave_metadata' AS section,
  'launch_aligned' AS alignment,
  'qvoice_wave' AS category,
  survey_meta.qvoice_rows::BIGINT AS employee_key_count,
  survey_meta.qvoice_rows::BIGINT AS response_row_count,
  survey_meta.qvoice_distinct_emp_ids::BIGINT AS denominator_count,
  survey_meta.qvoice_null_emp_id_rows::BIGINT AS auxiliary_count,
  survey_meta.survey_launch_date AS survey_launch_date,
  survey_meta.hierarchy_date AS hierarchy_date,
  NULL::DATE AS snapshot_date,
  'qvoice_rows, qvoice_distinct_emp_ids, qvoice_null_emp_id_rows' AS notes
FROM survey_meta
UNION ALL
SELECT
  'snapshot_metadata',
  snapshot_dates.alignment,
  'selected_workforce_snapshot',
  NULL::BIGINT,
  NULL::BIGINT,
  NULL::BIGINT,
  NULL::BIGINT,
  snapshot_dates.survey_launch_date,
  snapshot_dates.hierarchy_date,
  snapshot_dates.snapshot_date,
  'Latest fis_mo_end_dt on or before the alignment date.'
FROM snapshot_dates
UNION ALL
SELECT
  'response_quality',
  'launch_aligned',
  'response_keys',
  response_quality.response_employee_keys::BIGINT,
  response_quality.response_rows::BIGINT,
  response_quality.duplicate_response_employee_keys::BIGINT,
  NULL::BIGINT,
  DATE '2026-01-07',
  NULL::DATE,
  NULL::DATE,
  'employee_key_count=response keys, response_row_count=response rows, denominator_count=duplicate response keys.'
FROM response_quality
UNION ALL
SELECT
  'population_summary',
  classification_totals.alignment,
  'all_qvoice_response_keys',
  classification_totals.qvoice_response_employee_keys::BIGINT,
  classification_totals.qvoice_response_rows::BIGINT,
  NULL::BIGINT,
  NULL::BIGINT,
  DATE '2026-01-07',
  NULL::DATE,
  snapshot_dates.snapshot_date,
  'Counts are distinct QVoice employee keys except response_row_count.'
FROM classification_totals
JOIN snapshot_dates
  ON snapshot_dates.alignment = classification_totals.alignment
UNION ALL
SELECT
  'population_summary',
  classification_totals.alignment,
  'matched_workforce',
  classification_totals.matched_workforce_employee_keys::BIGINT,
  NULL::BIGINT,
  classification_totals.unmatched_workforce_employee_keys::BIGINT,
  classification_totals.duplicate_workforce_employee_keys::BIGINT,
  DATE '2026-01-07',
  NULL::DATE,
  snapshot_dates.snapshot_date,
  'employee_key_count=matched, denominator_count=unmatched, auxiliary_count=duplicate workforce keys.'
FROM classification_totals
JOIN snapshot_dates
  ON snapshot_dates.alignment = classification_totals.alignment
UNION ALL
SELECT
  'flag_summary',
  classification_totals.alignment,
  'worker_type_employee',
  classification_totals.worker_type_employee_keys::BIGINT,
  classification_totals.qvoice_response_employee_keys::BIGINT,
  NULL::BIGINT,
  NULL::BIGINT,
  DATE '2026-01-07',
  NULL::DATE,
  snapshot_dates.snapshot_date,
  'employee_key_count=QVoice keys with worker_type=Employee.'
FROM classification_totals
JOIN snapshot_dates
  ON snapshot_dates.alignment = classification_totals.alignment
UNION ALL
SELECT
  'flag_summary',
  classification_totals.alignment,
  'employee_type_regular',
  classification_totals.employee_type_regular_keys::BIGINT,
  classification_totals.qvoice_response_employee_keys::BIGINT,
  NULL::BIGINT,
  NULL::BIGINT,
  DATE '2026-01-07',
  NULL::DATE,
  snapshot_dates.snapshot_date,
  'employee_key_count=QVoice keys with employee_type=Regular.'
FROM classification_totals
JOIN snapshot_dates
  ON snapshot_dates.alignment = classification_totals.alignment
UNION ALL
SELECT
  'flag_summary',
  classification_totals.alignment,
  'active_status_1',
  classification_totals.active_status_1_keys::BIGINT,
  classification_totals.qvoice_response_employee_keys::BIGINT,
  NULL::BIGINT,
  NULL::BIGINT,
  DATE '2026-01-07',
  NULL::DATE,
  snapshot_dates.snapshot_date,
  'employee_key_count=QVoice keys with active_status=1.'
FROM classification_totals
JOIN snapshot_dates
  ON snapshot_dates.alignment = classification_totals.alignment
UNION ALL
SELECT
  'flag_summary',
  classification_totals.alignment,
  'default_employee_regular_active',
  classification_totals.default_eligible_employee_keys::BIGINT,
  classification_totals.qvoice_response_employee_keys::BIGINT,
  NULL::BIGINT,
  NULL::BIGINT,
  DATE '2026-01-07',
  NULL::DATE,
  snapshot_dates.snapshot_date,
  'employee_key_count=worker_type Employee AND employee_type Regular AND active_status=1.'
FROM classification_totals
JOIN snapshot_dates
  ON snapshot_dates.alignment = classification_totals.alignment
UNION ALL
SELECT
  'classification',
  classification_counts.alignment,
  classification_counts.classification,
  classification_counts.employee_key_count::BIGINT,
  classification_counts.response_row_count::BIGINT,
  NULL::BIGINT,
  NULL::BIGINT,
  DATE '2026-01-07',
  NULL::DATE,
  snapshot_dates.snapshot_date,
  'Mutually exclusive classification of QVoice response employee keys.'
FROM classification_counts
JOIN snapshot_dates
  ON snapshot_dates.alignment = classification_counts.alignment
ORDER BY section, alignment, category;
