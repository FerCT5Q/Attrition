-- Presentation | metadata-only preflight | Time since last promotion
--
-- Claim: the monthly worker table exposes the keys, dates, event fields and
-- RF360 flag needed to classify the two 2025-08-24 cohorts without using any
-- information from the subsequent attrition window.
--
-- Acceptance rule: every required column exists with a compatible type before
-- the aggregate cohort audit is run. No employee values are returned.
SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN (
      'employee_id',
      'fis_mo_end_dt',
      'worker_type',
      'employee_type',
      'active_status',
      'is_rf360_yes_no',
      'is_promo',
      'promotion_date',
      'max_hire_rehire_date',
      'time_in_role',
      'term_date',
      'term_type'
  )
ORDER BY column_name;
