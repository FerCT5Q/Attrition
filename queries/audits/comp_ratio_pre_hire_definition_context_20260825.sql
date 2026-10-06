WITH objects AS (
  SELECT
    LOWER(COALESCE(pg_catalog.pg_get_viewdef(cls.oid, true), '')) AS object_definition
  FROM pg_catalog.pg_class AS cls
  JOIN pg_catalog.pg_namespace AS ns
    ON ns.oid = cls.relnamespace
  WHERE ns.nspname = 'hrda'
    AND cls.relname = 'pre_hire_flat_and_wide_summary_mvw'
    AND cls.relkind = 'v'
), positions AS (
  SELECT
    object_definition,
    POSITION('compa_ratio_base_pay' IN object_definition) AS ratio_position,
    POSITION('mid_payrange' IN object_definition) AS midpoint_position,
    POSITION('base_pay_anualized_amt' IN object_definition) AS pay_position
  FROM objects
)
SELECT
  CASE
    WHEN ratio_position > 0 THEN SUBSTRING(object_definition, GREATEST(ratio_position - 700, 1), 1800)
    ELSE NULL
  END AS ratio_definition_context,
  CASE
    WHEN midpoint_position > 0 THEN SUBSTRING(object_definition, GREATEST(midpoint_position - 700, 1), 1800)
    ELSE NULL
  END AS midpoint_definition_context,
  CASE
    WHEN pay_position > 0 THEN SUBSTRING(object_definition, GREATEST(pay_position - 700, 1), 1800)
    ELSE NULL
  END AS pay_definition_context
FROM positions;
