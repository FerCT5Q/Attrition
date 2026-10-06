SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN ('et_1_leader', 'et_2_leader', 'et_3_leader', 'et_4_leader', 'et_5_leader', 'et_6_leader', 'et_7_leader', 'et_8_leader', 'et_9_leader', 'et_10_leader', 'et_11_leader')
ORDER BY ordinal_position
