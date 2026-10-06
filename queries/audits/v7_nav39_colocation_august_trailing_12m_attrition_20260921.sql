/*
  V7 navigation slide 36 / technical stage 41: co-location proxy and
  trailing-12-month voluntary attrition.

  Claim: the slide can show a complete FY2026 rate when the cohort is fixed at
  the prior fiscal-year-end snapshot and voluntary exits are observed through
  the FY2026 fiscal-year-end snapshot.  The same method is applied to every
  displayed fiscal year.

  Semantic type: derived feature (employee-manager same assigned office-site
  proxy at the baseline snapshot) plus an observed trailing-12-month outcome.
  Population: active regular employees at each baseline snapshot, excluding
  no population beyond the stored employee/manager relationship; the visual is
  presentation-safe and returns aggregate results only.

  Acceptance rule:
  - FY2021-FY2026 each resolve to a prior fiscal-year-end baseline and a
    fiscal-year-end outcome cutoff 364-371 days later (FY2024 is a 53-week
    fiscal year); FY2020 has no prior fiscal-year-end baseline in the source;
  - baseline employee-snapshot duplication and conflicting mapping counts are
    zero;
  - each displayed co-location cohort has at least 30 employees;
  - FY2026's cutoff is present in the source, so the full trailing outcome is
    observed rather than inferred from a partial forward window.

  The co-location flag is fixed at baseline.  It remains an assigned-location
  proxy, not proof of physical co-location.
*/
WITH all_snapshot_dates AS (
    SELECT
        CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
        MAX(CAST(fiscal_year AS INTEGER)) AS fiscal_year
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
    GROUP BY 1
),
fiscal_year_end_dates AS (
    SELECT fiscal_year, MAX(snapshot_date) AS fiscal_year_end_snapshot_date
    FROM all_snapshot_dates
    WHERE fiscal_year BETWEEN 2019 AND 2026
    GROUP BY 1
),
trailing_windows AS (
    SELECT
        outcome.fiscal_year AS report_fiscal_year,
        baseline.fiscal_year_end_snapshot_date AS baseline_snapshot_date,
        outcome.fiscal_year_end_snapshot_date AS outcome_cutoff_date,
        DATEDIFF(day, baseline.fiscal_year_end_snapshot_date, outcome.fiscal_year_end_snapshot_date) AS window_days
    FROM fiscal_year_end_dates AS outcome
    INNER JOIN fiscal_year_end_dates AS baseline
      ON baseline.fiscal_year = outcome.fiscal_year - 1
    WHERE outcome.fiscal_year BETWEEN 2020 AND 2026
),
source_bounds AS (
    SELECT MAX(snapshot_date) AS latest_snapshot_date
    FROM all_snapshot_dates
),
baseline_rows AS (
    SELECT
        window.report_fiscal_year,
        window.baseline_snapshot_date,
        window.outcome_cutoff_date,
        window.window_days,
        CAST(worker.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(worker.manager_employee_id AS BIGINT)) AS manager_employee_id,
        MAX(NULLIF(UPPER(TRIM(CAST(worker.office_site AS VARCHAR(256)))), '')) AS office_site_normalized,
        MAX(NULLIF(UPPER(TRIM(CAST(worker.city AS VARCHAR(256)))), '')) AS city_normalized,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(worker.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants,
        COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(worker.office_site AS VARCHAR(256)))), ''), '<NULL>')) AS office_site_variants,
        COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(worker.city AS VARCHAR(256)))), ''), '<NULL>')) AS city_variants
    FROM hrda.post_hire_monthly_worker_dtls AS worker
    INNER JOIN trailing_windows AS window
      ON CAST(worker.fis_mo_end_dt AS DATE) = window.baseline_snapshot_date
    WHERE worker.worker_type = 'Employee'
      AND worker.employee_type = 'Regular'
      AND worker.active_status = 1
      AND worker.employee_id IS NOT NULL
    GROUP BY 1, 2, 3, 4, 5
),
baseline_quality AS (
    SELECT
        report_fiscal_year,
        baseline_snapshot_date,
        outcome_cutoff_date,
        window_days,
        COUNT(*) AS active_baseline_employee_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN manager_id_variants > 1 OR office_site_variants > 1 OR city_variants > 1 THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count
    FROM baseline_rows
    GROUP BY 1, 2, 3, 4
),
pairs AS (
    SELECT
        employee.report_fiscal_year,
        employee.baseline_snapshot_date,
        employee.outcome_cutoff_date,
        employee.window_days,
        employee.employee_id,
        CASE
          WHEN employee.manager_id_variants = 1
           AND employee.office_site_variants <= 1
           AND employee.office_site_normalized IS NOT NULL
           AND manager.employee_id IS NOT NULL
           AND manager.office_site_variants = 1
           AND manager.office_site_normalized IS NOT NULL
           AND employee.office_site_normalized = manager.office_site_normalized
          THEN 1 ELSE 0
        END AS same_office_site,
        CASE
          WHEN employee.manager_id_variants = 1
           AND employee.office_site_variants <= 1
           AND employee.office_site_normalized IS NOT NULL
           AND manager.employee_id IS NOT NULL
           AND manager.office_site_variants = 1
           AND manager.office_site_normalized IS NOT NULL
           AND employee.city_variants <= 1
           AND employee.city_normalized IS NOT NULL
           AND manager.city_variants = 1
           AND manager.city_normalized IS NOT NULL
           AND employee.office_site_normalized = manager.office_site_normalized
           AND employee.city_normalized = manager.city_normalized
          THEN 1 ELSE 0
        END AS same_office_site_and_city,
        CASE WHEN employee.manager_employee_id IS NOT NULL AND manager.employee_id IS NULL THEN 1 ELSE 0 END AS unmatched_manager_flag
    FROM baseline_rows AS employee
    LEFT JOIN baseline_rows AS manager
      ON manager.report_fiscal_year = employee.report_fiscal_year
     AND manager.employee_id = employee.manager_employee_id
),
pair_quality AS (
    SELECT report_fiscal_year, SUM(unmatched_manager_flag) AS unmatched_manager_count
    FROM pairs
    GROUP BY 1
),
voluntary_events AS (
    SELECT CAST(employee_id AS BIGINT) AS employee_id, CAST(term_date AS DATE) AS term_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND term_date IS NOT NULL
    GROUP BY 1, 2
),
target_flags AS (
    SELECT
        pair.report_fiscal_year,
        pair.baseline_snapshot_date,
        pair.outcome_cutoff_date,
        pair.window_days,
        pair.employee_id,
        pair.same_office_site,
        pair.same_office_site_and_city,
        MAX(CASE WHEN event.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS trailing_12m_voluntary_attrition_target
    FROM pairs AS pair
    LEFT JOIN voluntary_events AS event
      ON event.employee_id = pair.employee_id
     AND event.term_date > pair.baseline_snapshot_date
     AND event.term_date <= pair.outcome_cutoff_date
    GROUP BY 1, 2, 3, 4, 5, 6, 7
),
category_rows AS (
    SELECT CAST('same_office_site' AS VARCHAR(64)) AS metric, report_fiscal_year, baseline_snapshot_date, outcome_cutoff_date, window_days, employee_id, trailing_12m_voluntary_attrition_target
    FROM target_flags
    WHERE same_office_site = 1
    UNION ALL
    SELECT CAST('same_office_site_and_city' AS VARCHAR(64)), report_fiscal_year, baseline_snapshot_date, outcome_cutoff_date, window_days, employee_id, trailing_12m_voluntary_attrition_target
    FROM target_flags
    WHERE same_office_site_and_city = 1
),
category_metrics AS (
    SELECT
        metric,
        report_fiscal_year,
        baseline_snapshot_date,
        outcome_cutoff_date,
        window_days,
        COUNT(DISTINCT employee_id) AS employee_count,
        SUM(trailing_12m_voluntary_attrition_target) AS voluntary_exits,
        ROUND(100.0 * SUM(trailing_12m_voluntary_attrition_target) / NULLIF(COUNT(DISTINCT employee_id), 0), 4) AS attrition_rate_percent
    FROM category_rows
    GROUP BY 1, 2, 3, 4, 5
)
SELECT
    'category' AS row_type,
    metric,
    CAST(report_fiscal_year AS VARCHAR(32)) AS fiscal_year,
    baseline_snapshot_date,
    outcome_cutoff_date,
    window_days::BIGINT AS window_days,
    employee_count::BIGINT AS employee_count,
    voluntary_exits::BIGINT AS voluntary_exits,
    attrition_rate_percent,
    CAST(NULL AS BIGINT) AS duplicate_employee_snapshot_count,
    CAST(NULL AS BIGINT) AS conflicting_employee_snapshot_count,
    CAST(NULL AS BIGINT) AS unmatched_manager_count,
    CASE WHEN employee_count >= 30 THEN 'publishable' ELSE 'not_estimable_small_cohort' END AS publication_status
FROM category_metrics
UNION ALL
SELECT
    'diagnostic',
    'baseline_quality',
    CAST(quality.report_fiscal_year AS VARCHAR(32)),
    quality.baseline_snapshot_date,
    quality.outcome_cutoff_date,
    quality.window_days::BIGINT,
    quality.active_baseline_employee_count::BIGINT,
    CAST(NULL AS BIGINT),
    CAST(NULL AS DECIMAL(18,4)),
    quality.duplicate_employee_snapshot_count::BIGINT,
    quality.conflicting_employee_snapshot_count::BIGINT,
    pair_quality.unmatched_manager_count::BIGINT,
    CASE
      WHEN quality.window_days BETWEEN 364 AND 371
       AND quality.outcome_cutoff_date <= bounds.latest_snapshot_date
      THEN 'complete_trailing_window'
      ELSE 'incomplete_or_invalid_window'
    END
FROM baseline_quality AS quality
INNER JOIN pair_quality
  ON pair_quality.report_fiscal_year = quality.report_fiscal_year
CROSS JOIN source_bounds AS bounds
ORDER BY row_type, metric, fiscal_year;
