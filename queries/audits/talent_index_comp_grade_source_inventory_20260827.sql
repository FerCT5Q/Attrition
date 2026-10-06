-- Talent index: metadata inventory for the compensation-grade hypothesis.
-- This query returns schema metadata only; no employee rows or values.

SELECT
  column_name,
  data_type,
  numeric_precision,
  numeric_scale,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'master_talent_index'
ORDER BY ordinal_position;
