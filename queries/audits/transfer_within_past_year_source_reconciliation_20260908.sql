/*
  Aggregate source reconciliation for Transfer within past year.

  Documented history is the monthly HRDA transfer_date event key.  The
  workers_ios_transfers feed is audited for context only and is not used by
  the distribution query.  No employee-level rows or identifiers are returned.
*/
WITH documented_events AS (
  SELECT DISTINCT
    employee_id,
    transfer_date::date AS transfer_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE employee_id IS NOT NULL
    AND is_transferred > 0
    AND transfer_date IS NOT NULL
),
ios_events AS (
  SELECT DISTINCT
    employee_id,
    effective_date::date AS transfer_date
  FROM hrda.workers_ios_transfers
  WHERE employee_id IS NOT NULL
    AND effective_date IS NOT NULL
),
ios_reconciliation AS (
  SELECT
    COUNT(*) AS ios_distinct_employee_date_keys,
    COUNT(CASE WHEN d.employee_id IS NOT NULL THEN 1 END) AS ios_keys_matched_to_documented_history
  FROM ios_events i
  LEFT JOIN documented_events d
    ON d.employee_id = i.employee_id
   AND d.transfer_date = i.transfer_date
),
documented_reconciliation AS (
  SELECT
    COUNT(*) AS documented_distinct_employee_date_keys,
    COUNT(CASE WHEN i.employee_id IS NOT NULL THEN 1 END) AS documented_keys_matched_to_ios
  FROM documented_events d
  LEFT JOIN ios_events i
    ON i.employee_id = d.employee_id
   AND i.transfer_date = d.transfer_date
),
source_rows AS (
  SELECT
    'workers_ios_transfers_vs_documented_history' AS comparison,
    i.ios_distinct_employee_date_keys AS left_distinct_employee_date_keys,
    i.ios_keys_matched_to_documented_history AS matched_employee_date_keys,
    ROUND(100.0 * i.ios_keys_matched_to_documented_history / NULLIF(i.ios_distinct_employee_date_keys, 0), 4) AS matched_percent,
    d.documented_distinct_employee_date_keys AS documented_distinct_employee_date_keys,
    d.documented_keys_matched_to_ios,
    ROUND(100.0 * d.documented_keys_matched_to_ios / NULLIF(d.documented_distinct_employee_date_keys, 0), 4) AS documented_history_covered_percent
  FROM ios_reconciliation i
  CROSS JOIN documented_reconciliation d
)
SELECT
  comparison,
  left_distinct_employee_date_keys,
  matched_employee_date_keys,
  matched_percent,
  documented_distinct_employee_date_keys,
  documented_keys_matched_to_ios,
  documented_history_covered_percent,
  'workers_ios_transfers is context only and the published series uses monthly transfer_date history' AS usage_decision
FROM source_rows;
