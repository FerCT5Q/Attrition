WITH object_definitions AS (
  SELECT
    ns.nspname AS table_schema,
    cls.relname AS object_name,
    CASE cls.relkind
      WHEN 'v' THEN 'VIEW'
      WHEN 'm' THEN 'MATERIALIZED VIEW'
      ELSE cls.relkind::varchar
    END AS object_type,
    LOWER(COALESCE(pg_catalog.pg_get_viewdef(cls.oid, true), '')) AS object_definition
  FROM pg_catalog.pg_class AS cls
  JOIN pg_catalog.pg_namespace AS ns
    ON ns.oid = cls.relnamespace
  WHERE ns.nspname = 'hrda'
    AND cls.relkind IN ('v', 'm')
), candidates AS (
  SELECT
    table_schema,
    object_name,
    object_type,
    object_definition
  FROM object_definitions
  WHERE object_definition LIKE '%compa_ratio%'
     OR object_definition LIKE '%mid_payrange%'
     OR object_definition LIKE '%payrange%'
)
SELECT
  table_schema,
  object_name,
  object_type,
  CASE WHEN object_definition LIKE '%compa_ratio%' THEN 1 ELSE 0 END AS references_compa_ratio,
  CASE WHEN object_definition LIKE '%compa_ratio_base_pay%' THEN 1 ELSE 0 END AS references_offer_ratio,
  CASE WHEN object_definition LIKE '%mid_payrange%' THEN 1 ELSE 0 END AS references_mid_payrange,
  CASE WHEN object_definition LIKE '%base_pay_amount%' THEN 1 ELSE 0 END AS references_base_pay_amount,
  CASE WHEN object_definition LIKE '%base_pay_anualized_amt%' THEN 1 ELSE 0 END AS references_annualized_pay,
  CASE WHEN object_definition LIKE '%/%' THEN 1 ELSE 0 END AS contains_division_operator,
  LENGTH(object_definition) AS definition_length
FROM candidates
ORDER BY object_name;
