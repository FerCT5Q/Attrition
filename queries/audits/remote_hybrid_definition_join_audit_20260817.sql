-- Aggregate-only semantic and key-grain audit for
-- "Remote / hybrid / in office status".
--
-- Claim tested: work_arrangement is a single work-arrangement category recorded
-- for each active Regular Employee at the monthly prediction snapshot; when
-- start/end dates are populated, they must not contradict that snapshot.
--
-- Definition support rule: no populated category may have start_date > snapshot,
-- end_date < snapshot, or start_date > end_date. This operational rule cannot
-- replace an owner-approved business definition of the category labels.
--
-- Join rule: at employee_id + fis_mo_end_dt grain, there must be no duplicate
-- source keys and no key carrying more than one normalized category. A blank
-- category is counted as coverage missingness, not as a failed join.

WITH base AS (
  SELECT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    UPPER(NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), ''))
      AS normalized_work_arrangement,
    CAST(work_arrangement_start_date AS DATE) AS work_arrangement_start_date,
    CAST(work_arrangement_end_date AS DATE) AS work_arrangement_end_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
key_rollup AS (
  SELECT
    employee_id,
    snapshot_date,
    COUNT(*) AS source_rows,
    COUNT(normalized_work_arrangement) AS populated_category_rows,
    COUNT(DISTINCT normalized_work_arrangement) AS distinct_normalized_categories
  FROM base
  GROUP BY employee_id, snapshot_date
),
row_metrics AS (
  SELECT
    COUNT(*) AS eligible_rows,
    COUNT(normalized_work_arrangement) AS populated_rows,
    COUNT(DISTINCT normalized_work_arrangement) AS distinct_normalized_categories,
    MIN(CASE WHEN normalized_work_arrangement IS NOT NULL THEN snapshot_date END)
      AS first_populated_snapshot_date,
    MAX(CASE WHEN normalized_work_arrangement IS NOT NULL THEN snapshot_date END)
      AS latest_populated_snapshot_date,
    SUM(CASE
      WHEN normalized_work_arrangement IS NOT NULL
       AND work_arrangement_start_date IS NOT NULL
      THEN 1 ELSE 0
    END) AS category_rows_with_start_date,
    SUM(CASE
      WHEN normalized_work_arrangement IS NOT NULL
       AND work_arrangement_end_date IS NOT NULL
      THEN 1 ELSE 0
    END) AS category_rows_with_end_date,
    SUM(CASE
      WHEN normalized_work_arrangement IS NOT NULL
       AND work_arrangement_start_date IS NOT NULL
       AND work_arrangement_end_date IS NOT NULL
      THEN 1 ELSE 0
    END) AS category_rows_with_both_dates,
    SUM(CASE
      WHEN normalized_work_arrangement IS NOT NULL
       AND work_arrangement_start_date > snapshot_date
      THEN 1 ELSE 0
    END) AS category_start_after_snapshot_rows,
    SUM(CASE
      WHEN normalized_work_arrangement IS NOT NULL
       AND work_arrangement_end_date < snapshot_date
      THEN 1 ELSE 0
    END) AS category_end_before_snapshot_rows,
    SUM(CASE
      WHEN normalized_work_arrangement IS NOT NULL
       AND work_arrangement_start_date IS NOT NULL
       AND work_arrangement_end_date IS NOT NULL
       AND work_arrangement_start_date > work_arrangement_end_date
      THEN 1 ELSE 0
    END) AS category_start_after_end_rows
  FROM base
)
SELECT
  COUNT(*) AS eligible_count,
  SUM(k.source_rows) AS eligible_rows,
  SUM(CASE
    WHEN k.source_rows = 1 AND k.populated_category_rows = 1
    THEN 1 ELSE 0
  END) AS matched_count,
  SUM(CASE WHEN k.populated_category_rows = 0 THEN 1 ELSE 0 END) AS unmatched_count,
  SUM(CASE WHEN k.source_rows > 1 THEN 1 ELSE 0 END) AS duplicate_count,
  SUM(CASE WHEN k.distinct_normalized_categories > 1 THEN 1 ELSE 0 END)
    AS multi_match_count,
  MAX(r.distinct_normalized_categories) AS distinct_normalized_categories,
  MAX(r.first_populated_snapshot_date) AS first_populated_snapshot_date,
  MAX(r.latest_populated_snapshot_date) AS latest_populated_snapshot_date,
  MAX(r.category_rows_with_start_date) AS category_rows_with_start_date,
  MAX(r.category_rows_with_end_date) AS category_rows_with_end_date,
  MAX(r.category_rows_with_both_dates) AS category_rows_with_both_dates,
  MAX(r.category_start_after_snapshot_rows) AS category_start_after_snapshot_rows,
  MAX(r.category_end_before_snapshot_rows) AS category_end_before_snapshot_rows,
  MAX(r.category_start_after_end_rows) AS category_start_after_end_rows
FROM key_rollup k
CROSS JOIN row_metrics r;
