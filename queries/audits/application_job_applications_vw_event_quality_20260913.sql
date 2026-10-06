-- Claim: the candidate event feed can be profiled at the approved event grain
-- without exposing rows, IDs, or requisition values.
-- Semantic type: input event quality for a derived feature.
-- Population: hrda.job_applications_vw rows with cand_applied=1.
-- Grain: raw source row and deduplicated employee_id + req_id + date key.
-- Acceptance rule: qualified events exist; the reported duplicate and null
-- counts are retained as limitations, not silently treated as zero events.
WITH raw_events AS (
  SELECT
    employee_id,
    TRIM(req_id) AS req_id,
    CAST(application_date AS DATE) AS application_date
  FROM hrda.job_applications_vw
  WHERE cand_applied = 1
    AND (application_date IS NULL OR CAST(application_date AS DATE) <= DATE '2026-09-10')
),
qualified_events AS (
  SELECT employee_id, req_id, application_date
  FROM raw_events
  WHERE employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
),
deduplicated_event_keys AS (
  SELECT employee_id, req_id, application_date
  FROM qualified_events
  GROUP BY 1, 2, 3
),
row_stats AS (
  SELECT
    COUNT(*) AS cand_applied_rows,
    SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END) AS null_employee_id_rows,
    SUM(CASE WHEN req_id IS NULL THEN 1 ELSE 0 END) AS null_req_id_rows,
    SUM(CASE WHEN application_date IS NULL THEN 1 ELSE 0 END) AS null_application_date_rows,
    MIN(application_date) AS first_application_date,
    MAX(application_date) AS last_application_date,
    COUNT(DISTINCT employee_id) AS distinct_employees_with_cand_applied
  FROM raw_events
),
qualified_stats AS (
  SELECT
    COUNT(*) AS qualified_rows,
    COUNT(DISTINCT employee_id) AS qualified_distinct_employees,
    COUNT(DISTINCT req_id) AS qualified_distinct_requisitions,
    COUNT(DISTINCT CAST(application_date AS DATE)) AS qualified_distinct_dates
  FROM qualified_events
),
dedup_stats AS (
  SELECT COUNT(*) AS qualified_unique_event_keys
  FROM deduplicated_event_keys
)
SELECT
  row_stats.cand_applied_rows,
  row_stats.null_employee_id_rows,
  row_stats.null_req_id_rows,
  row_stats.null_application_date_rows,
  qualified_stats.qualified_rows,
  dedup_stats.qualified_unique_event_keys,
  qualified_stats.qualified_rows - dedup_stats.qualified_unique_event_keys AS duplicate_event_rows,
  row_stats.first_application_date,
  row_stats.last_application_date,
  row_stats.distinct_employees_with_cand_applied,
  qualified_stats.qualified_distinct_employees,
  qualified_stats.qualified_distinct_requisitions,
  qualified_stats.qualified_distinct_dates
FROM row_stats
CROSS JOIN qualified_stats
CROSS JOIN dedup_stats;
