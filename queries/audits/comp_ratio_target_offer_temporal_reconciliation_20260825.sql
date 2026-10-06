WITH offer_raw AS (
  SELECT
    employee_id,
    candidate_id,
    hire_date,
    compa_ratio_base_pay,
    base_pay_amount,
    mid_payrange
  FROM hrda.offers
  WHERE last_updated_date <= DATE '2026-08-25'
    AND employee_id IS NOT NULL
    AND candidate_id IS NOT NULL
    AND hire_date IS NOT NULL
    AND hire_date <= DATE '2026-08-25'
), offer_key_counts AS (
  SELECT
    employee_id,
    candidate_id,
    hire_date,
    COUNT(*) AS rows_at_offer_key
  FROM offer_raw
  GROUP BY employee_id, candidate_id, hire_date
), offers_unique AS (
  SELECT
    offer_raw.employee_id,
    offer_raw.candidate_id,
    offer_raw.hire_date,
    offer_raw.compa_ratio_base_pay,
    offer_raw.base_pay_amount,
    offer_raw.mid_payrange
  FROM offer_raw
  JOIN offer_key_counts
    ON offer_key_counts.employee_id = offer_raw.employee_id
   AND offer_key_counts.candidate_id = offer_raw.candidate_id
   AND offer_key_counts.hire_date = offer_raw.hire_date
   AND offer_key_counts.rows_at_offer_key = 1
), target_rows AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    compa_ratio
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
    AND fis_mo_end_dt <= DATE '2026-08-25'
), candidate_pairs AS (
  SELECT
    offers_unique.employee_id,
    offers_unique.candidate_id,
    offers_unique.hire_date,
    offers_unique.compa_ratio_base_pay,
    offers_unique.base_pay_amount,
    offers_unique.mid_payrange,
    target_rows.fis_mo_end_dt,
    target_rows.compa_ratio,
    COUNT(target_rows.fis_mo_end_dt) OVER (PARTITION BY offers_unique.candidate_id) AS possible_target_snapshots,
    ROW_NUMBER() OVER (
      PARTITION BY offers_unique.candidate_id
      ORDER BY target_rows.fis_mo_end_dt
    ) AS target_snapshot_rank
  FROM offers_unique
  LEFT JOIN target_rows
    ON target_rows.employee_id = offers_unique.employee_id
   AND target_rows.fis_mo_end_dt >= offers_unique.hire_date
   AND target_rows.fis_mo_end_dt <= DATEADD(day, 45, offers_unique.hire_date)
), first_pairs AS (
  SELECT
    employee_id,
    candidate_id,
    hire_date,
    compa_ratio_base_pay,
    base_pay_amount,
    mid_payrange,
    fis_mo_end_dt,
    compa_ratio,
    possible_target_snapshots
  FROM candidate_pairs
  WHERE target_snapshot_rank = 1
), offer_duplicate_metrics AS (
  SELECT
    COUNT(*) AS offer_rows_before_deduplication,
    COUNT(DISTINCT employee_id) AS offer_employees_before_deduplication,
    SUM(CASE WHEN rows_at_offer_key > 1 THEN 1 ELSE 0 END) AS duplicate_offer_key_groups,
    SUM(CASE WHEN rows_at_offer_key > 1 THEN rows_at_offer_key ELSE 0 END) AS rows_in_duplicate_offer_keys
  FROM offer_key_counts
), reconciliation AS (
  SELECT
    COUNT(*) AS unique_offer_rows,
    COUNT(DISTINCT employee_id) AS unique_offer_employees,
    SUM(CASE WHEN fis_mo_end_dt IS NOT NULL THEN 1 ELSE 0 END) AS matched_first_target_snapshot_rows,
    SUM(CASE WHEN fis_mo_end_dt IS NULL THEN 1 ELSE 0 END) AS unmatched_first_target_snapshot_rows,
    SUM(CASE WHEN possible_target_snapshots > 1 THEN 1 ELSE 0 END) AS offers_with_multiple_target_snapshots_in_window,
    SUM(CASE WHEN fis_mo_end_dt IS NOT NULL AND compa_ratio IS NOT NULL THEN 1 ELSE 0 END) AS target_ratio_comparable_rows,
    SUM(CASE
      WHEN fis_mo_end_dt IS NOT NULL
       AND compa_ratio IS NOT NULL
       AND compa_ratio_base_pay IS NOT NULL
       AND ABS(compa_ratio - compa_ratio_base_pay) <= 0.01
      THEN 1 ELSE 0 END) AS target_matches_offer_ratio_within_001_rows,
    SUM(CASE
      WHEN fis_mo_end_dt IS NOT NULL
       AND compa_ratio IS NOT NULL
       AND base_pay_amount IS NOT NULL
       AND mid_payrange > 0
       AND ABS(compa_ratio - (base_pay_amount / NULLIF(mid_payrange, 0))) <= 0.01
      THEN 1 ELSE 0 END) AS target_matches_offer_formula_within_001_rows
  FROM first_pairs
)
SELECT
  offer_duplicate_metrics.offer_rows_before_deduplication,
  offer_duplicate_metrics.offer_employees_before_deduplication,
  offer_duplicate_metrics.duplicate_offer_key_groups,
  offer_duplicate_metrics.rows_in_duplicate_offer_keys,
  reconciliation.unique_offer_rows,
  reconciliation.unique_offer_employees,
  reconciliation.matched_first_target_snapshot_rows,
  reconciliation.unmatched_first_target_snapshot_rows,
  reconciliation.offers_with_multiple_target_snapshots_in_window,
  reconciliation.target_ratio_comparable_rows,
  reconciliation.target_matches_offer_ratio_within_001_rows,
  reconciliation.target_matches_offer_formula_within_001_rows,
  ROUND(100.0 * reconciliation.target_matches_offer_ratio_within_001_rows / NULLIF(reconciliation.target_ratio_comparable_rows, 0), 2) AS target_match_offer_ratio_rate_percent,
  ROUND(100.0 * reconciliation.target_matches_offer_formula_within_001_rows / NULLIF(reconciliation.target_ratio_comparable_rows, 0), 2) AS target_match_offer_formula_rate_percent
FROM offer_duplicate_metrics
CROSS JOIN reconciliation
WHERE reconciliation.unique_offer_employees >= 30;
