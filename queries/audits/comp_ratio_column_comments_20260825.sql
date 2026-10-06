SELECT
  ns.nspname AS table_schema,
  cls.relname AS table_name,
  att.attname AS column_name,
  pg_catalog.format_type(att.atttypid, att.atttypmod) AS data_type,
  descs.description AS column_comment
FROM pg_catalog.pg_class AS cls
JOIN pg_catalog.pg_namespace AS ns
  ON ns.oid = cls.relnamespace
JOIN pg_catalog.pg_attribute AS att
  ON att.attrelid = cls.oid
LEFT JOIN pg_catalog.pg_description AS descs
  ON descs.objoid = cls.oid
 AND descs.objsubid = att.attnum
WHERE ns.nspname = 'hrda'
  AND cls.relkind IN ('r', 'v', 'm')
  AND att.attnum > 0
  AND NOT att.attisdropped
  AND (
    LOWER(att.attname) IN (
      'compa_ratio',
      'compensation_ratio',
      'current_compa_ratio',
      'new_compa_ratio',
      'base_pay_amount',
      'base_pay',
      'base_pay_current',
      'base_pay_proposed',
      'mid_payrange',
      'midpoint',
      'mid_point'
    )
    OR LOWER(att.attname) LIKE '%midpoint%'
    OR LOWER(att.attname) LIKE '%payrange%'
    OR LOWER(att.attname) LIKE '%compa%'
  )
ORDER BY cls.relname, att.attnum;
