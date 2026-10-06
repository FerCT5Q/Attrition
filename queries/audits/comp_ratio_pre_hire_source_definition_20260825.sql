SELECT
  ns.nspname AS table_schema,
  cls.relname AS object_name,
  CASE cls.relkind
    WHEN 'r' THEN 'BASE TABLE'
    WHEN 'v' THEN 'VIEW'
    WHEN 'm' THEN 'MATERIALIZED VIEW'
    ELSE cls.relkind::varchar
  END AS object_type,
  pg_catalog.pg_get_viewdef(cls.oid, true) AS object_definition
FROM pg_catalog.pg_class AS cls
JOIN pg_catalog.pg_namespace AS ns
  ON ns.oid = cls.relnamespace
WHERE ns.nspname = 'hrda'
  AND cls.relname IN (
    'pre_hire_flat_and_wide_summary_mvw',
    'worker_snapshot_vw'
  )
  AND cls.relkind IN ('v', 'm');
