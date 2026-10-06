SELECT
  ns.nspname AS routine_schema,
  proc.proname AS routine_name,
  proc.pronargs AS argument_count,
  CASE WHEN LOWER(COALESCE(proc.prosrc, '')) LIKE '%compa_ratio%' THEN 1 ELSE 0 END AS references_compa_ratio,
  CASE WHEN LOWER(COALESCE(proc.prosrc, '')) LIKE '%mid_payrange%' THEN 1 ELSE 0 END AS references_mid_payrange,
  CASE WHEN LOWER(COALESCE(proc.prosrc, '')) LIKE '%base_pay_amount%' THEN 1 ELSE 0 END AS references_base_pay_amount,
  CASE WHEN LOWER(COALESCE(proc.prosrc, '')) LIKE '%base_pay_anualized_amt%' THEN 1 ELSE 0 END AS references_annualized_pay,
  CASE WHEN LOWER(COALESCE(proc.prosrc, '')) LIKE '%/%' THEN 1 ELSE 0 END AS contains_division_operator
FROM pg_catalog.pg_proc AS proc
JOIN pg_catalog.pg_namespace AS ns
  ON ns.oid = proc.pronamespace
WHERE ns.nspname = 'hrda'
  AND (
    LOWER(COALESCE(proc.prosrc, '')) LIKE '%compa_ratio%'
    OR LOWER(COALESCE(proc.prosrc, '')) LIKE '%mid_payrange%'
    OR LOWER(COALESCE(proc.prosrc, '')) LIKE '%payrange%'
  )
ORDER BY routine_name, argument_count;
