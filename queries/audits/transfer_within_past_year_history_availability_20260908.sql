/* Aggregate source-history check. It is separate from the published 12-month display window. */
SELECT
  'monthly_active_regular_snapshots' AS source_scope,
  MIN(fis_mo_end_dt::date) AS first_available_date,
  MAX(fis_mo_end_dt::date) AS last_available_date,
  COUNT(DISTINCT fis_mo_end_dt::date) AS available_snapshot_or_event_dates,
  NULL::date AS first_transfer_event_date,
  NULL::date AS last_transfer_event_date,
  NULL::bigint AS distinct_transfer_employee_date_keys
FROM hrda.post_hire_monthly_worker_dtls
WHERE worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1
  AND fis_mo_end_dt IS NOT NULL
UNION ALL
SELECT
  'daily_active_regular_transaction_dates',
  MIN(transaction_date::date),
  MAX(transaction_date::date),
  COUNT(DISTINCT transaction_date::date),
  NULL::date,
  NULL::date,
  NULL::bigint
FROM hrda.post_hire_daily_worker_dtls
WHERE worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1
  AND transaction_date IS NOT NULL
UNION ALL
SELECT
  'documented_transfer_event_history',
  NULL::date,
  NULL::date,
  NULL::bigint,
  MIN(transfer_date::date),
  MAX(transfer_date::date),
  COUNT(DISTINCT employee_id || '-' || transfer_date::date::varchar)
FROM hrda.post_hire_monthly_worker_dtls
WHERE worker_type = 'Employee' AND employee_type = 'Regular'
  AND is_transferred > 0 AND employee_id IS NOT NULL AND transfer_date IS NOT NULL;
