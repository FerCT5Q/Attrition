-- Co-location with manager: latest-snapshot reconciliation.
-- Deliverable mode: presentation. Aggregate-only; no employee, manager, or site values are returned.
--
-- Claim tested: The historical chart's "same site" rate is reproducible as a
-- same-stored-office_site proxy at the employee-snapshot grain, with an
-- explicit comparable-pair denominator. It is not a measure of physical
-- proximity, commute distance, or actual attendance.
--
-- Acceptance rule (stated before execution):
--   1) every employee is assigned to exactly one mutually exclusive bucket;
--   2) a comparable pair has one manager ID, no conflicting normalized
--      employee site, a matched active regular manager, and one nonblank
--      normalized manager site;
--   3) duplicate/conflicting source rows, unmatched managers, and blank sites
--      are reported separately; and
--   4) the legacy raw rate and the normalized, ambiguity-excluded rate are
--      both reported with their own denominators.

WITH latest_snapshot AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
),
active_employee_rows AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    CAST(w.manager_employee_id AS BIGINT) AS manager_employee_id,
    w.employee_type,
    w.office_site AS office_site_raw,
    NULLIF(UPPER(TRIM(w.office_site)), '') AS office_site_normalized
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN latest_snapshot d
  WHERE CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
    AND w.worker_type = 'Employee'
    AND w.active_status = 1
),
legacy_managers AS (
  -- This intentionally mirrors the historical profile: MAX(raw office_site)
  -- for active regular employees, followed by exact raw-string comparison.
  SELECT
    employee_id,
    MAX(office_site_raw) AS office_site_raw
  FROM active_employee_rows
  WHERE employee_type = 'Regular'
  GROUP BY employee_id
),
legacy_results AS (
  SELECT
    COUNT(DISTINCT e.employee_id) AS legacy_eligible_employees,
    COUNT(DISTINCT CASE
      WHEN NULLIF(TRIM(e.office_site_raw), '') IS NOT NULL
       AND NULLIF(TRIM(m.office_site_raw), '') IS NOT NULL
      THEN e.employee_id
    END) AS legacy_observable_employees,
    COUNT(DISTINCT CASE
      WHEN NULLIF(TRIM(e.office_site_raw), '') IS NOT NULL
       AND NULLIF(TRIM(m.office_site_raw), '') IS NOT NULL
       AND e.office_site_raw = m.office_site_raw
      THEN e.employee_id
    END) AS legacy_same_raw_site_employees
  FROM active_employee_rows e
  LEFT JOIN legacy_managers m
    ON e.manager_employee_id = m.employee_id
  WHERE e.employee_type = 'Regular'
),
employee_snapshot AS (
  -- One row per employee after recording any duplicate or conflicting inputs.
  SELECT
    employee_id,
    COUNT(*) AS employee_source_rows,
    COUNT(DISTINCT manager_employee_id) AS manager_id_count,
    MAX(manager_employee_id) AS manager_employee_id,
    COUNT(DISTINCT office_site_normalized) AS employee_site_value_count,
    MAX(office_site_normalized) AS employee_site_normalized
  FROM active_employee_rows
  WHERE employee_type = 'Regular'
  GROUP BY employee_id
),
regular_manager_snapshot AS (
  SELECT
    employee_id,
    COUNT(*) AS manager_source_rows,
    COUNT(DISTINCT office_site_normalized) AS manager_site_value_count,
    MAX(office_site_normalized) AS manager_site_normalized
  FROM active_employee_rows
  WHERE employee_type = 'Regular'
  GROUP BY employee_id
),
manager_quality AS (
  SELECT
    COUNT(*) AS active_regular_manager_keys,
    SUM(CASE WHEN manager_source_rows > 1 THEN 1 ELSE 0 END) AS managers_with_duplicate_active_rows,
    SUM(CASE WHEN manager_site_value_count > 1 THEN 1 ELSE 0 END) AS managers_with_conflicting_normalized_sites
  FROM regular_manager_snapshot
),
all_active_employee_snapshot AS (
  -- Sensitivity check: does the regular-manager restriction drive non-matches?
  SELECT employee_id
  FROM active_employee_rows
  GROUP BY employee_id
),
classified AS (
  SELECT
    e.employee_id,
    e.employee_source_rows,
    e.manager_id_count,
    e.manager_employee_id,
    e.employee_site_value_count,
    e.employee_site_normalized,
    m.employee_id AS matched_regular_manager_id,
    m.manager_source_rows,
    m.manager_site_value_count,
    m.manager_site_normalized,
    a.employee_id AS matched_active_employee_any_type_id,
    CASE
      WHEN e.manager_id_count = 0 THEN 'no_manager_id'
      WHEN e.manager_id_count > 1 THEN 'conflicting_manager_id'
      WHEN m.employee_id IS NULL THEN 'active_regular_manager_not_found'
      WHEN e.employee_site_value_count > 1 THEN 'conflicting_employee_site'
      WHEN m.manager_site_value_count > 1 THEN 'conflicting_manager_site'
      WHEN e.employee_site_normalized IS NULL THEN 'employee_site_blank'
      WHEN m.manager_site_normalized IS NULL THEN 'manager_site_blank'
      WHEN e.employee_site_normalized = m.manager_site_normalized THEN 'same_normalized_site'
      ELSE 'different_normalized_site'
    END AS comparison_bucket
  FROM employee_snapshot e
  LEFT JOIN regular_manager_snapshot m
    ON e.manager_employee_id = m.employee_id
  LEFT JOIN all_active_employee_snapshot a
    ON e.manager_employee_id = a.employee_id
),
reconciliation AS (
  SELECT
    COUNT(*) AS reconciled_eligible_employees,
    SUM(CASE WHEN employee_source_rows > 1 THEN 1 ELSE 0 END) AS employees_with_duplicate_active_rows,
    SUM(CASE WHEN manager_id_count > 1 THEN 1 ELSE 0 END) AS employees_with_conflicting_manager_ids,
    SUM(CASE WHEN employee_site_value_count > 1 THEN 1 ELSE 0 END) AS employees_with_conflicting_normalized_sites,
    SUM(CASE WHEN manager_id_count = 1 AND matched_regular_manager_id IS NOT NULL THEN 1 ELSE 0 END) AS employees_matched_to_active_regular_manager,
    SUM(CASE
      WHEN manager_id_count = 1
       AND matched_regular_manager_id IS NOT NULL
       AND manager_source_rows > 1
      THEN 1 ELSE 0
    END) AS employees_matched_to_manager_with_duplicate_active_rows,
    SUM(CASE WHEN manager_id_count = 1 AND matched_regular_manager_id IS NULL THEN 1 ELSE 0 END) AS employees_without_active_regular_manager_match,
    SUM(CASE
      WHEN manager_id_count = 1
       AND matched_regular_manager_id IS NULL
       AND matched_active_employee_any_type_id IS NOT NULL
      THEN 1 ELSE 0
    END) AS matches_only_if_manager_employee_type_is_widened,
    SUM(CASE WHEN comparison_bucket = 'no_manager_id' THEN 1 ELSE 0 END) AS bucket_no_manager_id,
    SUM(CASE WHEN comparison_bucket = 'conflicting_manager_id' THEN 1 ELSE 0 END) AS bucket_conflicting_manager_id,
    SUM(CASE WHEN comparison_bucket = 'active_regular_manager_not_found' THEN 1 ELSE 0 END) AS bucket_active_regular_manager_not_found,
    SUM(CASE WHEN comparison_bucket = 'conflicting_employee_site' THEN 1 ELSE 0 END) AS bucket_conflicting_employee_site,
    SUM(CASE WHEN comparison_bucket = 'conflicting_manager_site' THEN 1 ELSE 0 END) AS bucket_conflicting_manager_site,
    SUM(CASE WHEN comparison_bucket = 'employee_site_blank' THEN 1 ELSE 0 END) AS bucket_employee_site_blank,
    SUM(CASE WHEN comparison_bucket = 'manager_site_blank' THEN 1 ELSE 0 END) AS bucket_manager_site_blank,
    SUM(CASE WHEN comparison_bucket = 'same_normalized_site' THEN 1 ELSE 0 END) AS normalized_same_site_employees,
    SUM(CASE WHEN comparison_bucket = 'different_normalized_site' THEN 1 ELSE 0 END) AS normalized_different_site_employees
  FROM classified
)
SELECT
  d.snapshot_date,
  l.legacy_eligible_employees,
  l.legacy_observable_employees,
  l.legacy_same_raw_site_employees,
  ROUND(100.0 * l.legacy_same_raw_site_employees
    / NULLIF(l.legacy_observable_employees, 0), 4) AS legacy_same_raw_site_percent_of_observable,
  r.reconciled_eligible_employees,
  r.employees_with_duplicate_active_rows,
  r.employees_with_conflicting_manager_ids,
  r.employees_with_conflicting_normalized_sites,
  r.employees_matched_to_active_regular_manager,
  r.employees_matched_to_manager_with_duplicate_active_rows,
  r.employees_without_active_regular_manager_match,
  r.matches_only_if_manager_employee_type_is_widened,
  r.bucket_no_manager_id,
  r.bucket_conflicting_manager_id,
  r.bucket_active_regular_manager_not_found,
  r.bucket_conflicting_employee_site,
  r.bucket_conflicting_manager_site,
  r.bucket_employee_site_blank,
  r.bucket_manager_site_blank,
  r.normalized_same_site_employees,
  r.normalized_different_site_employees,
  r.normalized_same_site_employees + r.normalized_different_site_employees AS normalized_comparable_pairs,
  ROUND(100.0 * r.normalized_same_site_employees
    / NULLIF(r.normalized_same_site_employees + r.normalized_different_site_employees, 0), 4)
    AS normalized_same_site_percent_of_comparable_pairs,
  ROUND(100.0 * r.normalized_same_site_employees
    / NULLIF(r.reconciled_eligible_employees, 0), 4)
    AS normalized_same_site_percent_of_all_eligible,
  q.active_regular_manager_keys,
  q.managers_with_duplicate_active_rows,
  q.managers_with_conflicting_normalized_sites,
  r.bucket_no_manager_id
    + r.bucket_conflicting_manager_id
    + r.bucket_active_regular_manager_not_found
    + r.bucket_conflicting_employee_site
    + r.bucket_conflicting_manager_site
    + r.bucket_employee_site_blank
    + r.bucket_manager_site_blank
    + r.normalized_same_site_employees
    + r.normalized_different_site_employees AS exclusive_bucket_sum
FROM latest_snapshot d
CROSS JOIN legacy_results l
CROSS JOIN reconciliation r
CROSS JOIN manager_quality q;
