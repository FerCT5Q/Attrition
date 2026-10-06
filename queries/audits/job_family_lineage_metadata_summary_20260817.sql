WITH metadata AS (
  SELECT
    cols.table_name,
    cols.column_name,
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
    AND cols.column_name IN (
      'job_family',
      'job_family_short',
      'job_family_group',
      'job_family_group_short'
    )
)
SELECT
  COUNT(*) AS column_instances_found,
  COUNT(DISTINCT table_name) AS tables_with_job_family_columns,
  SUM(CASE WHEN NULLIF(TRIM(column_comment), '') IS NOT NULL THEN 1 ELSE 0 END)
    AS column_instances_with_comments,
  COUNT(DISTINCT CASE
    WHEN NULLIF(TRIM(column_comment), '') IS NOT NULL THEN table_name
  END) AS tables_with_any_job_family_comment
FROM metadata;
