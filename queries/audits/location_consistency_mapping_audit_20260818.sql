WITH base AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    NULLIF(TRIM(CAST(country AS VARCHAR)), '') AS country_norm,
    NULLIF(TRIM(CAST(office_site AS VARCHAR)), '') AS office_site_norm
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
latest AS (
  SELECT MAX(snapshot_date) AS snapshot_date
  FROM base
),
latest_base AS (
  SELECT
    b.snapshot_date,
    b.employee_id,
    b.country_norm,
    b.office_site_norm
  FROM base b
  JOIN latest l
    ON b.snapshot_date = l.snapshot_date
),
latest_employee_metrics AS (
  SELECT
    COUNT(DISTINCT employee_id) AS latest_eligible_employees,
    COUNT(DISTINCT CASE WHEN country_norm IS NOT NULL THEN employee_id END) AS latest_country_populated_employees,
    COUNT(DISTINCT CASE WHEN office_site_norm IS NOT NULL THEN employee_id END) AS latest_site_populated_employees,
    COUNT(DISTINCT CASE WHEN country_norm IS NOT NULL AND office_site_norm IS NOT NULL THEN employee_id END) AS latest_both_populated_employees,
    COUNT(DISTINCT CASE WHEN country_norm IS NULL AND office_site_norm IS NOT NULL THEN employee_id END) AS latest_country_missing_site_present_employees,
    COUNT(DISTINCT CASE WHEN country_norm IS NOT NULL AND office_site_norm IS NULL THEN employee_id END) AS latest_site_missing_country_present_employees,
    COUNT(DISTINCT CASE WHEN country_norm IS NULL AND office_site_norm IS NULL THEN employee_id END) AS latest_both_missing_employees
  FROM latest_base
),
history_employee_metrics AS (
  SELECT
    COUNT(DISTINCT snapshot_date) AS snapshot_count,
    COUNT(*) AS eligible_rows,
    COUNT(DISTINCT CASE WHEN country_norm IS NULL AND office_site_norm IS NOT NULL THEN CAST(snapshot_date AS VARCHAR) || '|' || CAST(employee_id AS VARCHAR) END) AS history_country_missing_site_present_employee_snapshots,
    COUNT(DISTINCT CASE WHEN country_norm IS NOT NULL AND office_site_norm IS NULL THEN CAST(snapshot_date AS VARCHAR) || '|' || CAST(employee_id AS VARCHAR) END) AS history_site_missing_country_present_employee_snapshots
  FROM base
),
site_month_country_counts AS (
  SELECT
    snapshot_date,
    office_site_norm,
    COUNT(DISTINCT country_norm) AS country_count
  FROM base
  WHERE office_site_norm IS NOT NULL
    AND country_norm IS NOT NULL
  GROUP BY 1, 2
),
site_history_country_counts AS (
  SELECT
    office_site_norm,
    COUNT(DISTINCT country_norm) AS country_count
  FROM base
  WHERE office_site_norm IS NOT NULL
    AND country_norm IS NOT NULL
  GROUP BY 1
),
country_month_site_counts AS (
  SELECT
    snapshot_date,
    country_norm,
    COUNT(DISTINCT office_site_norm) AS site_count
  FROM base
  WHERE office_site_norm IS NOT NULL
    AND country_norm IS NOT NULL
  GROUP BY 1, 2
),
latest_conflict_sites AS (
  SELECT smcc.office_site_norm
  FROM site_month_country_counts smcc
  WHERE smcc.snapshot_date = (SELECT snapshot_date FROM latest)
    AND smcc.country_count > 1
),
history_conflict_site_months AS (
  SELECT
    smcc.snapshot_date,
    smcc.office_site_norm
  FROM site_month_country_counts smcc
  WHERE smcc.country_count > 1
),
latest_conflict_impact AS (
  SELECT
    COUNT(DISTINCT lb.employee_id) AS latest_employees_on_conflicting_site_codes
  FROM latest_base lb
  JOIN latest_conflict_sites lcs
    ON lb.office_site_norm = lcs.office_site_norm
  WHERE lb.employee_id IS NOT NULL
),
latest_conflict_site_country_counts AS (
  SELECT
    lb.office_site_norm,
    lb.country_norm,
    COUNT(DISTINCT lb.employee_id) AS employee_count
  FROM latest_base lb
  JOIN latest_conflict_sites lcs
    ON lb.office_site_norm = lcs.office_site_norm
  WHERE lb.employee_id IS NOT NULL
    AND lb.country_norm IS NOT NULL
  GROUP BY 1, 2
),
latest_conflict_site_severity AS (
  SELECT
    office_site_norm,
    SUM(employee_count) AS site_employee_count,
    MAX(employee_count) AS dominant_country_employee_count,
    SUM(employee_count) - MAX(employee_count) AS non_dominant_country_employee_count,
    COUNT(*) AS country_count
  FROM latest_conflict_site_country_counts
  GROUP BY 1
),
latest_conflict_severity_metrics AS (
  SELECT
    SUM(site_employee_count) AS latest_conflict_site_country_populated_employees,
    SUM(non_dominant_country_employee_count) AS latest_conflict_non_dominant_country_employees,
    MAX(non_dominant_country_employee_count) AS latest_max_non_dominant_employees_for_one_site,
    ROUND(100.0 * SUM(non_dominant_country_employee_count) / NULLIF(SUM(site_employee_count), 0), 4) AS latest_conflict_non_dominant_employee_percent
  FROM latest_conflict_site_severity
),
history_conflict_impact AS (
  SELECT
    COUNT(DISTINCT CAST(b.snapshot_date AS VARCHAR) || '|' || CAST(b.employee_id AS VARCHAR)) AS history_employee_snapshots_on_conflicting_site_codes
  FROM base b
  JOIN history_conflict_site_months hcsm
    ON b.snapshot_date = hcsm.snapshot_date
   AND b.office_site_norm = hcsm.office_site_norm
  WHERE b.employee_id IS NOT NULL
),
site_month_metrics AS (
  SELECT
    SUM(CASE WHEN country_count > 1 THEN 1 ELSE 0 END) AS site_months_with_multiple_countries,
    MAX(country_count) AS max_countries_per_site_month,
    COUNT(DISTINCT CASE WHEN country_count > 1 THEN office_site_norm END) AS sites_with_same_month_country_conflicts
  FROM site_month_country_counts
),
site_history_metrics AS (
  SELECT
    COUNT(DISTINCT CASE WHEN country_count > 1 THEN office_site_norm END) AS sites_with_historical_country_changes,
    MAX(country_count) AS max_historical_countries_per_site
  FROM site_history_country_counts
),
country_month_metrics AS (
  SELECT
    SUM(CASE WHEN site_count > 1 THEN 1 ELSE 0 END) AS country_months_with_multiple_sites,
    MAX(site_count) AS max_sites_per_country_month
  FROM country_month_site_counts
),
latest_mapping_metrics AS (
  SELECT
    COUNT(DISTINCT CASE WHEN country_count > 1 THEN office_site_norm END) AS latest_sites_with_multiple_countries,
    MAX(country_count) AS latest_max_countries_per_site
  FROM site_month_country_counts
  WHERE snapshot_date = (SELECT snapshot_date FROM latest)
),
summary AS (
  SELECT
    hem.snapshot_count,
    hem.eligible_rows,
    lem.latest_eligible_employees,
    lem.latest_country_populated_employees,
    lem.latest_site_populated_employees,
    lem.latest_both_populated_employees,
    lem.latest_country_missing_site_present_employees,
    lem.latest_site_missing_country_present_employees,
    lem.latest_both_missing_employees,
    ROUND(100.0 * lem.latest_both_populated_employees / NULLIF(lem.latest_eligible_employees, 0), 4) AS latest_both_populated_percent,
    lci.latest_employees_on_conflicting_site_codes,
    lcsm.latest_conflict_site_country_populated_employees,
    lcsm.latest_conflict_non_dominant_country_employees,
    lcsm.latest_max_non_dominant_employees_for_one_site,
    lcsm.latest_conflict_non_dominant_employee_percent,
    hci.history_employee_snapshots_on_conflicting_site_codes,
    hem.history_country_missing_site_present_employee_snapshots,
    hem.history_site_missing_country_present_employee_snapshots,
    lmm.latest_sites_with_multiple_countries,
    lmm.latest_max_countries_per_site,
    smm.site_months_with_multiple_countries,
    smm.max_countries_per_site_month,
    smm.sites_with_same_month_country_conflicts,
    shm.sites_with_historical_country_changes,
    shm.max_historical_countries_per_site,
    cmm.country_months_with_multiple_sites,
    cmm.max_sites_per_country_month
  FROM history_employee_metrics hem
  CROSS JOIN latest_employee_metrics lem
  CROSS JOIN latest_conflict_impact lci
  CROSS JOIN latest_conflict_severity_metrics lcsm
  CROSS JOIN history_conflict_impact hci
  CROSS JOIN latest_mapping_metrics lmm
  CROSS JOIN site_month_metrics smm
  CROSS JOIN site_history_metrics shm
  CROSS JOIN country_month_metrics cmm
)
SELECT
  'overall_consistency_rule' AS check_id,
  'pass only when office_site maps to one country per snapshot, no historical site-country changes remain unexplained, and no site-present rows lack country' AS acceptance_rule,
  CASE
    WHEN latest_country_missing_site_present_employees = 0
     AND latest_sites_with_multiple_countries = 0
     AND site_months_with_multiple_countries = 0
     AND sites_with_historical_country_changes = 0
    THEN 'pass'
    ELSE 'fail'
  END AS outcome,
  snapshot_count,
  eligible_rows,
  latest_eligible_employees,
  latest_both_populated_percent,
  latest_country_missing_site_present_employees,
  latest_site_missing_country_present_employees,
  latest_employees_on_conflicting_site_codes,
  latest_conflict_site_country_populated_employees,
  latest_conflict_non_dominant_country_employees,
  latest_max_non_dominant_employees_for_one_site,
  latest_conflict_non_dominant_employee_percent,
  history_employee_snapshots_on_conflicting_site_codes,
  latest_sites_with_multiple_countries,
  latest_max_countries_per_site,
  site_months_with_multiple_countries,
  max_countries_per_site_month,
  sites_with_same_month_country_conflicts,
  sites_with_historical_country_changes,
  max_historical_countries_per_site,
  country_months_with_multiple_sites,
  max_sites_per_country_month,
  history_country_missing_site_present_employee_snapshots,
  history_site_missing_country_present_employee_snapshots
FROM summary;
