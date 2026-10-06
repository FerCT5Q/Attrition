-- Aggregate-only test of whether employee office_site labels can be crosswalked
-- to VNDLY work-site names. No office names, codes, ZIPs, or worker identities
-- are returned.
--
-- Acceptance rule for a candidate reference crosswalk:
-- every populated employee office_site must match exactly one VNDLY work-site
-- code by an approved, effective-dated mapping. This string-match audit is only
-- a discovery step; it cannot establish semantic or temporal lineage by itself.

WITH employee_sites AS (
  SELECT
    UPPER(NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), '')) AS office_site,
    COUNT(DISTINCT employee_id) AS employees_observed
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND office_site IS NOT NULL
  GROUP BY 1
),
vndly_sites AS (
  SELECT
    UPPER(NULLIF(TRIM(CAST(tdw_wo_work_site_name AS VARCHAR(256))), ''))
      AS work_site_name,
    COUNT(DISTINCT NULLIF(TRIM(CAST(tdw_wo_work_site_code AS VARCHAR(256))), ''))
      AS distinct_work_site_codes,
    COUNT(DISTINCT NULLIF(TRIM(CAST(tdw_wo_work_site_zip AS VARCHAR(256))), ''))
      AS distinct_work_site_zips
  FROM hrda.vndly_assignment
  WHERE tdw_wo_work_site_name IS NOT NULL
  GROUP BY 1
),
crosswalk AS (
  SELECT
    e.office_site,
    e.employees_observed,
    v.distinct_work_site_codes,
    v.distinct_work_site_zips
  FROM employee_sites e
  LEFT JOIN vndly_sites v
    ON e.office_site = v.work_site_name
)
SELECT
  COUNT(*) AS employee_office_site_values,
  SUM(CASE WHEN distinct_work_site_codes = 1 THEN 1 ELSE 0 END)
    AS office_site_values_with_one_vndly_code,
  SUM(CASE WHEN distinct_work_site_codes > 1 THEN 1 ELSE 0 END)
    AS office_site_values_with_multiple_vndly_codes,
  SUM(CASE WHEN distinct_work_site_codes IS NULL OR distinct_work_site_codes = 0 THEN 1 ELSE 0 END)
    AS office_site_values_without_vndly_name_match,
  SUM(CASE WHEN distinct_work_site_codes = 1 THEN employees_observed ELSE 0 END)
    AS distinct_employees_under_one_code_name_match,
  SUM(CASE WHEN distinct_work_site_codes IS NULL OR distinct_work_site_codes = 0 THEN employees_observed ELSE 0 END)
    AS distinct_employees_without_name_match,
  MAX(COALESCE(distinct_work_site_codes, 0)) AS max_vndly_codes_for_one_office_site_name,
  MAX(COALESCE(distinct_work_site_zips, 0)) AS max_vndly_zips_for_one_office_site_name
FROM crosswalk;
