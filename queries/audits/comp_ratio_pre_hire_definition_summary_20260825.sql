WITH objects AS (
  SELECT
    ns.nspname AS table_schema,
    cls.relname AS object_name,
    CASE cls.relkind
      WHEN 'r' THEN 'BASE TABLE'
      WHEN 'v' THEN 'VIEW'
      WHEN 'm' THEN 'MATERIALIZED VIEW'
      ELSE cls.relkind::varchar
    END AS object_type,
    LOWER(COALESCE(pg_catalog.pg_get_viewdef(cls.oid, true), '')) AS object_definition
  FROM pg_catalog.pg_class AS cls
  JOIN pg_catalog.pg_namespace AS ns
    ON ns.oid = cls.relnamespace
  WHERE ns.nspname = 'hrda'
    AND cls.relname = 'pre_hire_flat_and_wide_summary_mvw'
)
SELECT
  table_schema,
  object_name,
  object_type,
  CASE WHEN object_definition LIKE '%compa_ratio_base_pay%' THEN 1 ELSE 0 END AS references_compa_ratio_base_pay,
  CASE WHEN object_definition LIKE '%mid_payrange%' THEN 1 ELSE 0 END AS references_mid_payrange,
  CASE WHEN object_definition LIKE '%base_pay_amount%' THEN 1 ELSE 0 END AS references_base_pay_amount,
  CASE WHEN object_definition LIKE '% / %' OR object_definition LIKE '%/%' THEN 1 ELSE 0 END AS contains_division_operator,
  CASE WHEN object_definition LIKE '%round(%' THEN 1 ELSE 0 END AS contains_rounding,
  LENGTH(object_definition) AS definition_length
FROM objects;
