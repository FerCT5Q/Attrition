-- Aggregate-only semantic summary of work_arrangement. It deliberately does
-- not return individual exception/reason labels because some can be sensitive.
--
-- Rule for the requested three-way feature: every stored category must map
-- through an approved rule to exactly one of Remote, Hybrid, or In office.
-- The mechanical buckets below diagnose whether that rule can be inferred from
-- the field alone; they are not an approved business mapping.

WITH base AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    UPPER(NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '')) AS raw_category
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
    AND NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '') IS NOT NULL
),
canonical AS (
  SELECT
    snapshot_date,
    raw_category,
    REGEXP_REPLACE(raw_category, '^[A-Z0-9]+\\.\\s*', '') AS canonical_category
  FROM base
),
classified AS (
  SELECT
    snapshot_date,
    raw_category,
    canonical_category,
    CASE
      WHEN canonical_category = 'ONSITE' THEN 'In office explícito'
      WHEN canonical_category LIKE '%HYBRID%' THEN 'Hybrid explícito'
      WHEN canonical_category LIKE '%REMOTE%' THEN 'Remote explícito'
      WHEN canonical_category LIKE 'OFFSITE%' THEN 'Offsite sin remote explícito'
      WHEN canonical_category LIKE 'INTERIM MODIFIED%' THEN 'Arreglo temporal / excepción'
      ELSE 'Otro / requiere mapping'
    END AS semantic_bucket,
    CASE
      WHEN canonical_category LIKE '%MEDICAL%'
        OR canonical_category LIKE '%CAREGIV%'
      THEN 1 ELSE 0
    END AS possible_sensitive_reason
  FROM canonical
),
latest_snapshot AS (
  SELECT MAX(snapshot_date) AS snapshot_date FROM classified
),
buckets AS (
  SELECT 'In office explícito' AS semantic_bucket
  UNION ALL SELECT 'Hybrid explícito'
  UNION ALL SELECT 'Remote explícito'
  UNION ALL SELECT 'Offsite sin remote explícito'
  UNION ALL SELECT 'Arreglo temporal / excepción'
  UNION ALL SELECT 'Otro / requiere mapping'
),
summary AS (
  SELECT
    c.semantic_bucket,
    COUNT(DISTINCT c.raw_category) AS raw_category_variants,
    COUNT(DISTINCT c.canonical_category) AS canonical_category_variants,
    COUNT(DISTINCT c.snapshot_date) AS observed_months,
    MIN(c.snapshot_date) AS first_seen_snapshot_date,
    MAX(c.snapshot_date) AS last_seen_snapshot_date,
    SUM(CASE WHEN c.snapshot_date = l.snapshot_date THEN 1 ELSE 0 END)
      AS latest_snapshot_rows,
    COUNT(DISTINCT CASE WHEN c.possible_sensitive_reason = 1
      THEN c.canonical_category END) AS possible_sensitive_reason_categories
  FROM classified c
  CROSS JOIN latest_snapshot l
  GROUP BY c.semantic_bucket
)
SELECT
  b.semantic_bucket,
  COALESCE(s.raw_category_variants, 0) AS raw_category_variants,
  COALESCE(s.canonical_category_variants, 0) AS canonical_category_variants,
  COALESCE(s.observed_months, 0) AS observed_months,
  s.first_seen_snapshot_date,
  s.last_seen_snapshot_date,
  COALESCE(s.latest_snapshot_rows, 0) AS latest_snapshot_rows,
  COALESCE(s.possible_sensitive_reason_categories, 0)
    AS possible_sensitive_reason_categories
FROM buckets b
LEFT JOIN summary s ON b.semantic_bucket = s.semantic_bucket
ORDER BY CASE b.semantic_bucket
  WHEN 'In office explícito' THEN 1
  WHEN 'Hybrid explícito' THEN 2
  WHEN 'Remote explícito' THEN 3
  WHEN 'Offsite sin remote explícito' THEN 4
  WHEN 'Arreglo temporal / excepción' THEN 5
  ELSE 6
END;
