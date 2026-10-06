WITH objects AS (
  SELECT
    cls.relname AS object_name,
    LOWER(COALESCE(pg_catalog.pg_get_viewdef(cls.oid, true), '')) AS object_definition
  FROM pg_catalog.pg_class AS cls
  JOIN pg_catalog.pg_namespace AS ns
    ON ns.oid = cls.relnamespace
  WHERE ns.nspname = 'hrda'
    AND cls.relkind = 'v'
    AND cls.relname IN (
      'offers_vw',
      'offers_snapshot',
      'pre_hire_flat_and_wide_summary_mvw',
      'worker_details_latest',
      'worker_snapshot_vw'
    )
), positions AS (
  SELECT
    object_name,
    object_definition,
    POSITION('compa_ratio' IN object_definition) AS ratio_position
  FROM objects
)
SELECT
  object_name,
  CASE
    WHEN ratio_position > 0 THEN SUBSTRING(object_definition, GREATEST(ratio_position - 500, 1), 1400)
    ELSE NULL
  END AS ratio_context
FROM positions
ORDER BY object_name;
