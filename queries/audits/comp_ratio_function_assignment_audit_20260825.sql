SELECT
  proc.proname AS routine_name,
  proc.pronargs AS argument_count,
  CASE
    WHEN LOWER(COALESCE(proc.prosrc, '')) LIKE '%compa_ratio =%'
      OR LOWER(COALESCE(proc.prosrc, '')) LIKE '%compa_ratio:=%'
      OR LOWER(COALESCE(proc.prosrc, '')) LIKE '%compa_ratio :=%'
    THEN 1 ELSE 0
  END AS contains_compa_ratio_assignment,
  CASE WHEN LOWER(COALESCE(proc.prosrc, '')) LIKE '%mid_payrange%' THEN 1 ELSE 0 END AS references_mid_payrange,
  CASE WHEN LOWER(COALESCE(proc.prosrc, '')) LIKE '%base_pay_amount%' THEN 1 ELSE 0 END AS references_base_pay_amount
FROM pg_catalog.pg_proc AS proc
JOIN pg_catalog.pg_namespace AS ns
  ON ns.oid = proc.pronamespace
WHERE ns.nspname = 'hrda'
  AND (
    LOWER(COALESCE(proc.prosrc, '')) LIKE '%compa_ratio%'
    OR LOWER(COALESCE(proc.prosrc, '')) LIKE '%mid_payrange%'
  )
ORDER BY routine_name, argument_count;
