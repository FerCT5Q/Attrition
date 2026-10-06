WITH routines AS (
  SELECT
    proc.proname AS routine_name,
    proc.pronargs AS argument_count,
    LOWER(COALESCE(proc.prosrc, '')) AS routine_source
  FROM pg_catalog.pg_proc AS proc
  JOIN pg_catalog.pg_namespace AS ns
    ON ns.oid = proc.pronamespace
  WHERE ns.nspname = 'hrda'
    AND (
      LOWER(COALESCE(proc.prosrc, '')) LIKE '%compa_ratio%'
      OR LOWER(COALESCE(proc.prosrc, '')) LIKE '%mid_payrange%'
    )
), positions AS (
  SELECT
    routine_name,
    argument_count,
    routine_source,
    POSITION('compa_ratio' IN routine_source) AS ratio_position,
    POSITION('base_pay_amount' IN routine_source) AS amount_position,
    POSITION('mid_payrange' IN routine_source) AS midpoint_position
  FROM routines
)
SELECT
  routine_name,
  argument_count,
  CASE
    WHEN ratio_position > 0 THEN SUBSTRING(routine_source, GREATEST(ratio_position - 700, 1), 2200)
    ELSE NULL
  END AS ratio_context,
  CASE
    WHEN amount_position > 0 THEN SUBSTRING(routine_source, GREATEST(amount_position - 700, 1), 2200)
    ELSE NULL
  END AS amount_context,
  CASE
    WHEN midpoint_position > 0 THEN SUBSTRING(routine_source, GREATEST(midpoint_position - 700, 1), 2200)
    ELSE NULL
  END AS midpoint_context
FROM positions
ORDER BY routine_name, argument_count;
