-- Aggregate-only audit of whether post_hire_monthly_worker_dtls.postal_code
-- behaves as a stable office-site mapping. It never returns a site or ZIP code.
--
-- Acceptance rule for a candidate site mapping:
-- each populated office_site must have one postal code at a snapshot and a
-- governed, effective-dated mapping across history. Even a passing cardinality
-- result does not override the documented sensitivity/lineage classification
-- of postal_code.

WITH base AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    UPPER(NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), '')) AS office_site,
    NULLIF(TRIM(CAST(postal_code AS VARCHAR(256))), '') AS postal_code
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
site_snapshot AS (
  SELECT
    snapshot_date,
    office_site,
    COUNT(DISTINCT postal_code) AS distinct_postal_codes
  FROM base
  WHERE office_site IS NOT NULL
  GROUP BY 1, 2
),
site_history AS (
  SELECT
    office_site,
    COUNT(DISTINCT postal_code) AS distinct_postal_codes_over_history
  FROM base
  WHERE office_site IS NOT NULL
  GROUP BY 1
),
base_summary AS (
  SELECT
    COUNT(*) AS eligible_employee_snapshots,
    SUM(CASE
      WHEN office_site IS NOT NULL AND postal_code IS NOT NULL THEN 1 ELSE 0
    END) AS employee_snapshots_with_both_fields,
    COUNT(DISTINCT office_site) AS observed_office_sites
  FROM base
),
snapshot_summary AS (
  SELECT
    SUM(CASE WHEN distinct_postal_codes = 0 THEN 1 ELSE 0 END)
      AS office_site_snapshots_without_postal,
    SUM(CASE WHEN distinct_postal_codes = 1 THEN 1 ELSE 0 END)
      AS office_site_snapshots_with_one_postal,
    SUM(CASE WHEN distinct_postal_codes > 1 THEN 1 ELSE 0 END)
      AS office_site_snapshots_with_multiple_postals,
    MAX(distinct_postal_codes) AS max_postal_codes_for_one_office_site_snapshot
  FROM site_snapshot
),
history_summary AS (
  SELECT
    SUM(CASE WHEN distinct_postal_codes_over_history = 1 THEN 1 ELSE 0 END)
      AS office_sites_with_one_postal_over_history,
    SUM(CASE WHEN distinct_postal_codes_over_history > 1 THEN 1 ELSE 0 END)
      AS office_sites_with_multiple_postals_over_history,
    MAX(distinct_postal_codes_over_history)
      AS max_postal_codes_for_one_office_site_over_history
  FROM site_history
)
SELECT
  b.eligible_employee_snapshots,
  b.employee_snapshots_with_both_fields,
  ROUND(
    100.0 * b.employee_snapshots_with_both_fields
      / NULLIF(b.eligible_employee_snapshots, 0),
    4
  ) AS both_fields_coverage_percent,
  b.observed_office_sites,
  s.office_site_snapshots_without_postal,
  s.office_site_snapshots_with_one_postal,
  s.office_site_snapshots_with_multiple_postals,
  s.max_postal_codes_for_one_office_site_snapshot,
  h.office_sites_with_one_postal_over_history,
  h.office_sites_with_multiple_postals_over_history,
  h.max_postal_codes_for_one_office_site_over_history
FROM base_summary b
CROSS JOIN snapshot_summary s
CROSS JOIN history_summary h;
