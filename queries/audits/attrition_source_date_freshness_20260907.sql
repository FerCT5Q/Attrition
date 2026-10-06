/*
  Attrition model preflight: source date freshness and future-date check.

  Claim:
    The monthly snapshot dates used for modeling represent observations
    available no later than the execution date, or any later fiscal date is
    explicitly explainable by source timing.

  Population:
    All rows in the monthly workforce source; reported counts are restricted
    to the regular Employee population for model relevance.

  Acceptance rule:
    No snapshot_date may be later than DATE '2026-09-07' for production
    scoring. If later dates exist, their row counts and ingestion timestamps
    must be reviewed and excluded until the source owner explains the timing.

  Privacy:
    Aggregate counts only; no employee-level fields are returned.
*/
SELECT
  CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
  COUNT(*) AS regular_employee_rows,
  COUNT(DISTINCT employee_id) AS regular_employee_count,
  MIN(CAST(airflow_db_processing_ts AS TIMESTAMP))
    AS earliest_processing_timestamp,
  MAX(CAST(airflow_db_processing_ts AS TIMESTAMP))
    AS latest_processing_timestamp,
  CASE
    WHEN CAST(fis_mo_end_dt AS DATE) > DATE '2026-09-07'
    THEN 'future_snapshot_review_required'
    ELSE 'within_execution_date'
  END AS freshness_outcome
FROM hrda.post_hire_monthly_worker_dtls
WHERE worker_type = 'Employee'
  AND employee_type = 'Regular'
  AND fis_mo_end_dt IS NOT NULL
  AND CAST(fis_mo_end_dt AS DATE) >= DATE '2026-08-01'
GROUP BY 1
ORDER BY 1;
