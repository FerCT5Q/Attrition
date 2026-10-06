/*
  Purpose: render annual voluntary-attrition labels under the Rehire (1)
  prevalence bars on V7 slide 16.

  Deliverable: internal_analysis, aggregate-only.
  Population: active Regular Employees at each monthly snapshot
    (worker_type = Employee, employee_type = Regular, active_status = 1)
    with is_rehire = 1 at that snapshot.
  Grain: one employee-month exposure, deduplicated before the outcome join.
  Outcome: at least one strict VOLUNTARY termination in
    (snapshot_date, snapshot_date + 12 months].
  Follow-up: only snapshots at least 12 months before the latest source
    snapshot are estimable. FY2026 remains in the requested output and must
    render as Not estimable when it has no mature exposures.

  Acceptance rule: publish a rate only when both the distinct-employee cohort
  and employee-snapshot denominator are at least 30. No employee-level fields
  are returned.
*/
WITH requested_years AS (
  SELECT '2020' AS fiscal_year
  UNION ALL SELECT '2021'
  UNION ALL SELECT '2023'
  UNION ALL SELECT '2024'
  UNION ALL SELECT '2025'
  UNION ALL SELECT '2026'
),
source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
),
all_rehire_snapshots AS (
  SELECT
    CAST(w.fiscal_year AS VARCHAR(32)) AS fiscal_year,
    CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
    w.employee_id,
    MAX(COALESCE(w.is_rehire, 0)) AS is_rehire
  FROM hrda.post_hire_monthly_worker_dtls w
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.fis_mo_end_dt IS NOT NULL
  GROUP BY 1, 2, 3
),
mature_rehire_snapshots AS (
  SELECT
    CAST(w.fiscal_year AS VARCHAR(32)) AS fiscal_year,
    CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
    w.employee_id,
    MAX(COALESCE(w.is_rehire, 0)) AS is_rehire
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN source_bounds b
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.fis_mo_end_dt IS NOT NULL
    AND CAST(w.fis_mo_end_dt AS DATE) <= DATEADD(month, -12, b.latest_snapshot_date)
  GROUP BY 1, 2, 3
),
voluntary_events AS (
  SELECT
    employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
  GROUP BY 1, 2
),
annual_rehire_outcomes AS (
  SELECT
    s.fiscal_year,
    s.snapshot_date,
    s.employee_id,
    MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
  FROM mature_rehire_snapshots s
  LEFT JOIN voluntary_events v
    ON v.employee_id = s.employee_id
   AND v.term_date > s.snapshot_date
   AND v.term_date <= DATEADD(month, 12, s.snapshot_date)
  WHERE s.is_rehire = 1
  GROUP BY 1, 2, 3
),
annual_aggregate AS (
  SELECT
    fiscal_year,
    MIN(snapshot_date) AS first_mature_snapshot_date,
    MAX(snapshot_date) AS last_mature_snapshot_date,
    COUNT(*) AS employee_snapshot_count,
    COUNT(DISTINCT employee_id) AS distinct_employee_count,
    SUM(voluntary_attrition_target) AS voluntary_exits,
    100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0) AS attrition_rate_percent
  FROM annual_rehire_outcomes
  GROUP BY 1
),
all_annual_exposure AS (
  SELECT
    fiscal_year,
    COUNT(*) AS all_employee_snapshot_count
  FROM all_rehire_snapshots
  WHERE is_rehire = 1
  GROUP BY 1
)
SELECT
  y.fiscal_year,
  COALESCE(ae.all_employee_snapshot_count, 0) AS all_employee_snapshot_count,
  a.first_mature_snapshot_date,
  a.last_mature_snapshot_date,
  COALESCE(a.employee_snapshot_count, 0) AS employee_snapshot_count,
  COALESCE(a.distinct_employee_count, 0) AS distinct_employee_count,
  COALESCE(a.voluntary_exits, 0) AS voluntary_exits,
  CASE
    WHEN y.fiscal_year IN ('2020', '2021', '2026') THEN NULL
    WHEN a.employee_snapshot_count >= 30 AND a.distinct_employee_count >= 30
    THEN a.attrition_rate_percent
    ELSE NULL
  END AS attrition_rate_percent,
  CASE
    WHEN y.fiscal_year IN ('2020', '2021') THEN 'not_comparable_source_era'
    WHEN y.fiscal_year = '2026' THEN 'not_estimable_incomplete_followup'
    WHEN a.employee_snapshot_count >= 30 AND a.distinct_employee_count >= 30
      AND a.employee_snapshot_count < ae.all_employee_snapshot_count
    THEN 'publishable_mature_partial_year'
    WHEN a.employee_snapshot_count >= 30 AND a.distinct_employee_count >= 30 THEN 'publishable'
    WHEN COALESCE(a.employee_snapshot_count, 0) = 0 THEN 'not_estimable_incomplete_followup'
    ELSE 'not_publishable_below_n30'
  END AS publication_status
FROM requested_years y
LEFT JOIN annual_aggregate a
  ON a.fiscal_year = y.fiscal_year
LEFT JOIN all_annual_exposure ae
  ON ae.fiscal_year = y.fiscal_year
ORDER BY CAST(y.fiscal_year AS INTEGER);
