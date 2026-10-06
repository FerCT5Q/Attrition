-- Aggregate-only assessment of the VNDLY work-site candidate.
-- It does not disclose work-site codes, names, cities, or ZIPs.
--
-- Acceptance rule for a reusable site catalogue candidate:
-- each populated work_site_code maps to exactly one populated ZIP within this
-- source. A pass would establish only internal mapping stability; it would not
-- prove a time-safe join to regular employees or equivalence to office_site.

WITH base AS (
  SELECT
    NULLIF(TRIM(CAST(tdw_wo_work_site_code AS VARCHAR(256))), '') AS work_site_code,
    NULLIF(TRIM(CAST(tdw_wo_work_site_name AS VARCHAR(256))), '') AS work_site_name,
    NULLIF(TRIM(CAST(tdw_wo_work_site_zip AS VARCHAR(256))), '') AS work_site_zip
  FROM hrda.vndly_assignment
),
by_code AS (
  SELECT
    work_site_code,
    COUNT(DISTINCT work_site_zip) AS distinct_zip_codes,
    COUNT(DISTINCT work_site_name) AS distinct_site_names
  FROM base
  WHERE work_site_code IS NOT NULL
  GROUP BY work_site_code
)
SELECT
  (SELECT COUNT(*) FROM base) AS assignment_rows,
  (SELECT COUNT(*) FROM base WHERE work_site_code IS NOT NULL) AS rows_with_work_site_code,
  (SELECT COUNT(*) FROM base WHERE work_site_zip IS NOT NULL) AS rows_with_work_site_zip,
  COUNT(*) AS distinct_work_site_codes,
  SUM(CASE WHEN distinct_zip_codes = 0 THEN 1 ELSE 0 END) AS codes_without_zip,
  SUM(CASE WHEN distinct_zip_codes = 1 THEN 1 ELSE 0 END) AS codes_with_one_zip,
  SUM(CASE WHEN distinct_zip_codes > 1 THEN 1 ELSE 0 END) AS codes_with_multiple_zips,
  MAX(distinct_zip_codes) AS max_zips_for_one_work_site_code,
  SUM(CASE WHEN distinct_site_names > 1 THEN 1 ELSE 0 END) AS codes_with_multiple_site_names
FROM by_code;
