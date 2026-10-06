-- Exploratory, aggregate-only association between co-location with the manager
-- and voluntary attrition in the following monthly snapshot interval.
--
-- Feature at t: employee and active Regular-Employee manager have one resolved,
-- nonblank office_site at the same snapshot; comparison is same vs different
-- normalized office_site. Home address/postal_code is not used.
-- Outcome after t: term_type = 'Voluntary' and term_date is in (t, t+1].
-- This query is descriptive, not causal, and does not establish a feature
-- definition or model usefulness without adjustment for role, geography,
-- work arrangement, tenure and other confounders.
--
-- Acceptance rules:
-- 1. A cell must include at least 30 employee-snapshots.
-- 2. Event counts and rates are suppressed below 30 voluntary events.
-- 3. Only a unique manager and one normalized site per employee-snapshot are
--    eligible; ambiguous keys are excluded rather than arbitrarily resolved.

WITH calendar AS (
  SELECT
    snapshot_date,
    LEAD(snapshot_date) OVER (ORDER BY snapshot_date) AS next_snapshot_date
  FROM (
    SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
  ) dates
),
employee_rows AS (
  SELECT
    c.snapshot_date,
    c.next_snapshot_date,
    CAST(w.fiscal_year AS VARCHAR(32)) AS fiscal_year,
    w.employee_id,
    NULLIF(TRIM(CAST(w.manager_employee_id AS VARCHAR(256))), '')
      AS manager_employee_id,
    UPPER(NULLIF(TRIM(CAST(w.office_site AS VARCHAR(256))), ''))
      AS employee_office_site,
    CASE
      WHEN NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '') = 'Voluntary'
       AND CAST(w.term_date AS DATE) > c.snapshot_date
       AND CAST(w.term_date AS DATE) <= c.next_snapshot_date
      THEN 1 ELSE 0
    END AS voluntary_next_month
  FROM hrda.post_hire_monthly_worker_dtls w
  JOIN calendar c
    ON CAST(w.fis_mo_end_dt AS DATE) = c.snapshot_date
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
),
employee_snapshot AS (
  SELECT
    snapshot_date,
    next_snapshot_date,
    fiscal_year,
    employee_id,
    CASE
      WHEN COUNT(DISTINCT manager_employee_id) = 1
      THEN MIN(manager_employee_id)
    END AS manager_employee_id,
    CASE
      WHEN COUNT(DISTINCT employee_office_site) = 1
      THEN MIN(employee_office_site)
    END AS employee_office_site,
    MAX(voluntary_next_month) AS voluntary_next_month
  FROM employee_rows
  GROUP BY 1, 2, 3, 4
),
manager_rows AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    UPPER(NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), ''))
      AS manager_office_site
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
manager_snapshot AS (
  SELECT
    snapshot_date,
    employee_id,
    CASE
      WHEN COUNT(DISTINCT manager_office_site) = 1
      THEN MIN(manager_office_site)
    END AS manager_office_site
  FROM manager_rows
  GROUP BY 1, 2
),
features AS (
  SELECT
    e.fiscal_year,
    CASE
      WHEN e.employee_office_site = m.manager_office_site
      THEN 'Mismo office_site'
      ELSE 'Office_site distinto'
    END AS co_location_status,
    e.voluntary_next_month
  FROM employee_snapshot e
  JOIN manager_snapshot m
    ON m.snapshot_date = e.snapshot_date
   AND m.employee_id = e.manager_employee_id
  WHERE e.next_snapshot_date IS NOT NULL
    AND e.manager_employee_id IS NOT NULL
    AND e.manager_employee_id <> CAST(e.employee_id AS VARCHAR(256))
    AND e.employee_office_site IS NOT NULL
    AND m.manager_office_site IS NOT NULL
),
fiscal_stats AS (
  SELECT
    fiscal_year,
    co_location_status,
    COUNT(*) AS eligible_employee_snapshots,
    SUM(voluntary_next_month) AS voluntary_attrition_events
  FROM features
  GROUP BY 1, 2
),
all_stats AS (
  SELECT
    'Todos los meses comparables' AS fiscal_year,
    co_location_status,
    COUNT(*) AS eligible_employee_snapshots,
    SUM(voluntary_next_month) AS voluntary_attrition_events
  FROM features
  GROUP BY 1, 2
),
combined AS (
  SELECT
    fiscal_year,
    co_location_status,
    eligible_employee_snapshots,
    voluntary_attrition_events
  FROM all_stats
  UNION ALL
  SELECT
    fiscal_year,
    co_location_status,
    eligible_employee_snapshots,
    voluntary_attrition_events
  FROM fiscal_stats
)
SELECT
  fiscal_year,
  co_location_status,
  eligible_employee_snapshots,
  CASE
    WHEN voluntary_attrition_events >= 30 THEN voluntary_attrition_events
  END AS voluntary_attrition_events,
  CASE
    WHEN voluntary_attrition_events >= 30
    THEN ROUND(
      100.0 * voluntary_attrition_events
        / NULLIF(eligible_employee_snapshots, 0),
      4
    )
  END AS voluntary_attrition_rate_percent,
  CASE WHEN voluntary_attrition_events >= 30 THEN 1 ELSE 0 END
    AS event_count_reportable
FROM combined
WHERE eligible_employee_snapshots >= 30
ORDER BY
  CASE WHEN fiscal_year = 'Todos los meses comparables' THEN 0 ELSE 1 END,
  fiscal_year,
  co_location_status;
