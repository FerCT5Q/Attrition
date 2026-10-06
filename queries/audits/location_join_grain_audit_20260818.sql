WITH eligible AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
key_counts AS (
  SELECT
    snapshot_date,
    employee_id,
    COUNT(*) AS rows_per_employee_snapshot
  FROM eligible
  WHERE employee_id IS NOT NULL
  GROUP BY 1, 2
),
eligible_summary AS (
  SELECT
    COUNT(DISTINCT snapshot_date) AS eligible_snapshot_count,
    COUNT(*) AS eligible_rows,
    SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END) AS null_employee_key_rows
  FROM eligible
),
latest AS (
  SELECT MAX(snapshot_date) AS snapshot_date
  FROM key_counts
),
summary AS (
  SELECT
    es.eligible_snapshot_count AS snapshot_count,
    es.eligible_rows,
    es.null_employee_key_rows,
    COUNT(*) AS employee_snapshot_keys,
    SUM(CASE WHEN rows_per_employee_snapshot = 1 THEN 1 ELSE 0 END) AS matched_once_keys,
    SUM(CASE WHEN rows_per_employee_snapshot > 1 THEN 1 ELSE 0 END) AS duplicate_key_count,
    SUM(CASE WHEN rows_per_employee_snapshot > 1 THEN rows_per_employee_snapshot - 1 ELSE 0 END) AS duplicate_extra_rows,
    MAX(rows_per_employee_snapshot) AS max_rows_per_employee_snapshot,
    COUNT(DISTINCT CASE WHEN rows_per_employee_snapshot > 1 THEN snapshot_date END) AS months_with_duplicate_keys,
    SUM(CASE WHEN snapshot_date = (SELECT snapshot_date FROM latest) AND rows_per_employee_snapshot > 1 THEN 1 ELSE 0 END) AS latest_duplicate_key_count,
    SUM(CASE WHEN snapshot_date = (SELECT snapshot_date FROM latest) AND rows_per_employee_snapshot > 1 THEN rows_per_employee_snapshot - 1 ELSE 0 END) AS latest_duplicate_extra_rows
  FROM key_counts
  CROSS JOIN eligible_summary es
  GROUP BY 1, 2, 3
)
SELECT
  'employee_snapshot_grain' AS check_id,
  'pass only when every active regular employee row has a non-null employee key and exactly one row per employee_id plus fis_mo_end_dt' AS acceptance_rule,
  CASE
    WHEN null_employee_key_rows = 0
     AND duplicate_key_count = 0
     AND duplicate_extra_rows = 0
     AND max_rows_per_employee_snapshot = 1
    THEN 'pass'
    ELSE 'fail'
  END AS outcome,
  snapshot_count,
  eligible_rows,
  employee_snapshot_keys,
  matched_once_keys,
  null_employee_key_rows AS unmatched_key_count,
  null_employee_key_rows,
  duplicate_key_count,
  duplicate_extra_rows,
  max_rows_per_employee_snapshot,
  months_with_duplicate_keys,
  latest_duplicate_key_count,
  latest_duplicate_extra_rows,
  ROUND(100.0 * duplicate_extra_rows / NULLIF(eligible_rows, 0), 6) AS duplicate_extra_row_percent
FROM summary;
