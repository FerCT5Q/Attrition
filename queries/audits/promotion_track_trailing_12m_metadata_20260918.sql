-- Metadata-only preflight for the slide 30 trailing-12-month refresh.
-- No employee-level values or aggregates are returned.
SELECT
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('post_hire_monthly_worker_dtls', 'annual_review_report')
  AND (
      table_name = 'annual_review_report'
      OR
      column_name IN (
          'employee_id', 'fis_mo_end_dt', 'worker_type', 'employee_type',
          'active_status', 'is_rf360_yes_no', 'compensation_grade',
          'is_promo', 'promotion_date', 'term_date', 'term_type',
          'promotion_yes_no', 'in_annual_review', 'snapshot_date',
          'fiscal_year', 'calendar_year', 'year', 'grade'
      )
      OR column_name ILIKE '%promo%'
      OR column_name ILIKE '%review%'
      OR column_name ILIKE '%snapshot%'
      OR column_name ILIKE '%grade%'
      OR column_name ILIKE '%year%'
  )
ORDER BY table_name, ordinal_position;
