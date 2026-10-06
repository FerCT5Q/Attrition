SELECT
  cols.table_schema,
  cols.table_name,
  cols.column_name,
  cols.data_type,
  cols.character_maximum_length,
  COALESCE(descr.description, '') AS column_comment
FROM information_schema.columns AS cols
LEFT JOIN pg_catalog.pg_namespace AS ns
  ON ns.nspname = cols.table_schema
LEFT JOIN pg_catalog.pg_class AS cls
  ON cls.relnamespace = ns.oid
 AND cls.relname = cols.table_name
LEFT JOIN pg_catalog.pg_attribute AS attr
  ON attr.attrelid = cls.oid
 AND attr.attname = cols.column_name
LEFT JOIN pg_catalog.pg_description AS descr
  ON descr.objoid = cls.oid
 AND descr.objsubid = attr.attnum
WHERE cols.table_schema = 'hrda'
  AND cols.table_name = 'post_hire_monthly_worker_dtls'
  AND cols.column_name IN (
    'job_family',
    'job_family_short',
    'job_family_group',
    'job_family_group_short'
  )
ORDER BY cols.ordinal_position;
