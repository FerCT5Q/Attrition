WITH snapshots AS (
  SELECT
    fis_mo_end_dt::date AS snapshot_date,
    fiscal_year,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
latest_snapshot AS (
  SELECT MAX(snapshot_date) AS snapshot_date
  FROM snapshots
),
recent_snapshots AS (
  SELECT snapshot_date
  FROM (
    SELECT DISTINCT snapshot_date
    FROM snapshots
    ORDER BY snapshot_date DESC
    LIMIT 3
  ) s
),
application_rows AS (
  SELECT
    employee_id,
    candidate_id,
    req_id,
    application_date::date AS application_date,
    cand_applied
  FROM hrda.applications
),
source_summary AS (
  SELECT
    COUNT(*) AS application_rows,
    COUNT(CASE WHEN employee_id IS NOT NULL THEN 1 END) AS rows_with_employee_id,
    COUNT(CASE WHEN application_date IS NOT NULL THEN 1 END) AS rows_with_application_date,
    COUNT(CASE WHEN cand_applied = 1 THEN 1 END) AS cand_applied_rows,
    COUNT(DISTINCT employee_id) AS linked_employees,
    COUNT(DISTINCT CASE WHEN cand_applied = 1 THEN employee_id END) AS applied_employees,
    COUNT(DISTINCT CASE WHEN cand_applied = 1 THEN req_id END) AS applied_requisitions,
    MIN(CASE WHEN cand_applied = 1 THEN application_date END) AS min_applied_date,
    MAX(CASE WHEN cand_applied = 1 THEN application_date END) AS max_applied_date
  FROM application_rows
),
applied_events_raw AS (
  SELECT
    employee_id,
    application_date,
    req_id,
    COUNT(*) AS raw_rows
  FROM application_rows
  WHERE employee_id IS NOT NULL
    AND application_date IS NOT NULL
    AND cand_applied = 1
  GROUP BY 1, 2, 3
),
applied_events AS (
  SELECT
    employee_id,
    application_date,
    req_id
  FROM applied_events_raw
),
dedup_summary AS (
  SELECT
    COUNT(*) AS deduped_employee_date_req_events,
    SUM(raw_rows) AS raw_applied_rows,
    SUM(CASE WHEN raw_rows > 1 THEN 1 ELSE 0 END) AS duplicated_event_keys,
    SUM(CASE WHEN raw_rows > 1 THEN raw_rows - 1 ELSE 0 END) AS duplicate_extra_rows
  FROM applied_events_raw
),
linked_employees AS (
  SELECT employee_id
  FROM application_rows
  WHERE employee_id IS NOT NULL
  GROUP BY 1
),
employee_month AS (
  SELECT
    s.snapshot_date,
    s.fiscal_year,
    s.employee_id,
    MAX(CASE WHEN le.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS observable_flag,
    COUNT(DISTINCT CASE
      WHEN ae.application_date > DATEADD(month, -12, s.snapshot_date)
       AND ae.application_date <= s.snapshot_date
      THEN ae.req_id
    END) AS trailing_applications
  FROM snapshots s
  LEFT JOIN linked_employees le
    ON s.employee_id = le.employee_id
  LEFT JOIN applied_events ae
    ON s.employee_id = ae.employee_id
   AND ae.application_date > DATEADD(month, -12, s.snapshot_date)
   AND ae.application_date <= s.snapshot_date
  GROUP BY 1, 2, 3
),
scoped_employee_month AS (
  SELECT 'full_history' AS scope, em.*
  FROM employee_month em
  UNION ALL
  SELECT 'recent_3_snapshots' AS scope, em.*
  FROM employee_month em
  JOIN recent_snapshots r
    ON em.snapshot_date = r.snapshot_date
  UNION ALL
  SELECT 'latest_snapshot' AS scope, em.*
  FROM employee_month em
  JOIN latest_snapshot l
    ON em.snapshot_date = l.snapshot_date
),
coverage_summary AS (
  SELECT
    scope,
    COUNT(*) AS eligible_rows,
    SUM(observable_flag) AS observable_rows,
    COUNT(*) - SUM(observable_flag) AS missing_rows,
    SUM(CASE WHEN trailing_applications > 3 THEN 1 ELSE 0 END) AS more_than_3_rows,
    ROUND(100.0 * SUM(observable_flag) / NULLIF(COUNT(*), 0), 4) AS coverage_percent,
    ROUND(100.0 * (COUNT(*) - SUM(observable_flag)) / NULLIF(COUNT(*), 0), 4) AS missingness_percent,
    ROUND(100.0 * SUM(CASE WHEN trailing_applications > 3 THEN 1 ELSE 0 END) / NULLIF(SUM(observable_flag), 0), 4) AS event_percent_of_observable
  FROM scoped_employee_month
  GROUP BY 1
),
fiscal_year_summary AS (
  SELECT
    fiscal_year::varchar AS fiscal_year,
    COUNT(*) AS eligible_rows,
    SUM(observable_flag) AS observable_rows,
    COUNT(*) - SUM(observable_flag) AS missing_rows,
    SUM(CASE WHEN trailing_applications > 3 THEN 1 ELSE 0 END) AS more_than_3_rows,
    ROUND(100.0 * SUM(observable_flag) / NULLIF(COUNT(*), 0), 4) AS coverage_percent,
    ROUND(100.0 * SUM(CASE WHEN trailing_applications > 3 THEN 1 ELSE 0 END) / NULLIF(SUM(observable_flag), 0), 4) AS event_percent_of_observable
  FROM employee_month
  GROUP BY 1
),
date_window AS (
  SELECT
    l.snapshot_date AS latest_snapshot_date,
    DATEADD(month, -12, l.snapshot_date)::date AS latest_window_start_date,
    s.max_applied_date,
    DATEDIFF(day, s.max_applied_date, l.snapshot_date) AS days_between_latest_application_and_snapshot,
    CASE
      WHEN s.max_applied_date >= DATEADD(month, -12, l.snapshot_date)::date THEN 1
      ELSE 0
    END AS feed_covers_latest_12m_window
  FROM latest_snapshot l
  CROSS JOIN source_summary s
)
SELECT
  'source_summary' AS section,
  'all' AS scope,
  ss.application_rows AS metric_1,
  ss.rows_with_employee_id AS metric_2,
  ss.rows_with_application_date AS metric_3,
  ss.cand_applied_rows AS metric_4,
  ss.linked_employees AS metric_5,
  ss.applied_employees AS metric_6,
  ss.applied_requisitions AS metric_7,
  ss.min_applied_date AS date_1,
  ss.max_applied_date AS date_2,
  NULL::DECIMAL(18,4) AS percent_1,
  NULL::DECIMAL(18,4) AS percent_2,
  'metric_1=application_rows, metric_2=rows_with_employee_id, metric_3=rows_with_application_date, metric_4=cand_applied_rows, metric_5=linked_employees, metric_6=applied_employees, metric_7=applied_requisitions, date_1=min_applied_date, date_2=max_applied_date' AS notes
FROM source_summary ss
UNION ALL
SELECT
  'dedup_summary' AS section,
  'all' AS scope,
  ds.raw_applied_rows AS metric_1,
  ds.deduped_employee_date_req_events AS metric_2,
  ds.duplicated_event_keys AS metric_3,
  ds.duplicate_extra_rows AS metric_4,
  NULL::BIGINT AS metric_5,
  NULL::BIGINT AS metric_6,
  NULL::BIGINT AS metric_7,
  NULL::DATE AS date_1,
  NULL::DATE AS date_2,
  ROUND(100.0 * ds.duplicate_extra_rows / NULLIF(ds.raw_applied_rows, 0), 4) AS percent_1,
  NULL::DECIMAL(18,4) AS percent_2,
  'metric_1=raw_applied_rows, metric_2=deduped_employee_date_req_events, metric_3=duplicated_event_keys, metric_4=duplicate_extra_rows, percent_1=duplicate_extra_row_percent' AS notes
FROM dedup_summary ds
UNION ALL
SELECT
  'date_window' AS section,
  'latest_snapshot' AS scope,
  dw.days_between_latest_application_and_snapshot AS metric_1,
  dw.feed_covers_latest_12m_window AS metric_2,
  NULL::BIGINT AS metric_3,
  NULL::BIGINT AS metric_4,
  NULL::BIGINT AS metric_5,
  NULL::BIGINT AS metric_6,
  NULL::BIGINT AS metric_7,
  dw.latest_window_start_date AS date_1,
  dw.max_applied_date AS date_2,
  NULL::DECIMAL(18,4) AS percent_1,
  NULL::DECIMAL(18,4) AS percent_2,
  'metric_1=days_between_latest_application_and_snapshot, metric_2=feed_covers_latest_12m_window, date_1=latest_window_start_date, date_2=max_applied_date' AS notes
FROM date_window dw
UNION ALL
SELECT
  'coverage_summary' AS section,
  scope,
  eligible_rows AS metric_1,
  observable_rows AS metric_2,
  missing_rows AS metric_3,
  more_than_3_rows AS metric_4,
  NULL::BIGINT AS metric_5,
  NULL::BIGINT AS metric_6,
  NULL::BIGINT AS metric_7,
  NULL::DATE AS date_1,
  NULL::DATE AS date_2,
  coverage_percent AS percent_1,
  event_percent_of_observable AS percent_2,
  'metric_1=eligible_rows, metric_2=observable_rows, metric_3=missing_rows, metric_4=more_than_3_rows, percent_1=coverage_percent, percent_2=event_percent_of_observable' AS notes
FROM coverage_summary
UNION ALL
SELECT
  'fiscal_year_summary' AS section,
  'fy_' || fiscal_year AS scope,
  eligible_rows AS metric_1,
  observable_rows AS metric_2,
  missing_rows AS metric_3,
  more_than_3_rows AS metric_4,
  NULL::BIGINT AS metric_5,
  NULL::BIGINT AS metric_6,
  NULL::BIGINT AS metric_7,
  NULL::DATE AS date_1,
  NULL::DATE AS date_2,
  coverage_percent AS percent_1,
  event_percent_of_observable AS percent_2,
  'metric_1=eligible_rows, metric_2=observable_rows, metric_3=missing_rows, metric_4=more_than_3_rows, percent_1=coverage_percent, percent_2=event_percent_of_observable' AS notes
FROM fiscal_year_summary
ORDER BY section, scope
