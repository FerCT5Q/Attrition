/*
  V7 navigation slide 39: annual voluntary attrition for employees who match
  their manager on the stored office-site proxy (and, separately, site + city)
  at the historical snapshot.  The visual's annual prevalence bars remain
  unchanged; each bar receives the matching employee cohort's 12-month exit
  rate only where follow-up is observable.

  This remains an assigned-location proxy, not evidence of physical presence.
*/
WITH source_bounds AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
all_snapshot_dates AS (
    SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, MAX(fiscal_year) AS fiscal_year
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
    GROUP BY 1
),
complete_snapshot_dates AS (
    SELECT d.snapshot_date, d.fiscal_year
    FROM all_snapshot_dates AS d
    CROSS JOIN source_bounds AS bounds
    WHERE d.snapshot_date <= DATEADD(month, -12, bounds.latest_snapshot_date)
),
fiscal_snapshot_coverage AS (
    SELECT
        all_dates.fiscal_year,
        COUNT(*) AS total_source_snapshots,
        SUM(CASE WHEN complete.snapshot_date IS NOT NULL THEN 1 ELSE 0 END) AS complete_followup_snapshots
    FROM all_snapshot_dates AS all_dates
    LEFT JOIN complete_snapshot_dates AS complete
      ON complete.snapshot_date = all_dates.snapshot_date
    GROUP BY 1
),
source_rows AS (
    SELECT
        complete.snapshot_date,
        complete.fiscal_year,
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.manager_employee_id AS BIGINT)) AS manager_employee_id,
        MAX(NULLIF(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '')) AS office_site_normalized,
        MAX(NULLIF(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '')) AS city_normalized,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants,
        COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), ''), '<NULL>')) AS office_site_variants,
        COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), ''), '<NULL>')) AS city_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN complete_snapshot_dates AS complete
      ON CAST(w.fis_mo_end_dt AS DATE) = complete.snapshot_date
    WHERE w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1, 2, 3
),
source_quality AS (
    SELECT
        COUNT(*) AS active_employee_snapshot_count,
        COUNT(DISTINCT snapshot_date) AS snapshot_count,
        SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count,
        SUM(CASE WHEN manager_id_variants > 1 OR office_site_variants > 1 OR city_variants > 1 THEN 1 ELSE 0 END) AS conflicting_employee_snapshot_count
    FROM source_rows
),
pairs AS (
    SELECT
        employee.snapshot_date,
        employee.fiscal_year,
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
        END AS same_office_site_and_city
    FROM source_rows AS employee
    LEFT JOIN source_rows AS manager
      ON manager.snapshot_date = employee.snapshot_date
     AND manager.employee_id = employee.manager_employee_id
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
        pair.snapshot_date,
        pair.fiscal_year,
        pair.employee_id,
        pair.same_office_site,
        pair.same_office_site_and_city,
        MAX(CASE WHEN event.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS annual_voluntary_attrition_target
    FROM pairs AS pair
    LEFT JOIN voluntary_events AS event
      ON event.employee_id = pair.employee_id
     AND event.term_date > pair.snapshot_date
     AND event.term_date <= DATEADD(month, 12, pair.snapshot_date)
    GROUP BY 1, 2, 3, 4, 5
),
category_rows AS (
    SELECT 'same_office_site' AS metric, fiscal_year, snapshot_date, employee_id, annual_voluntary_attrition_target
    FROM target_flags
    WHERE same_office_site = 1
    UNION ALL
    SELECT 'same_office_site_and_city', fiscal_year, snapshot_date, employee_id, annual_voluntary_attrition_target
    FROM target_flags
    WHERE same_office_site_and_city = 1
),
category_metrics AS (
    SELECT
        metric,
        fiscal_year,
        COUNT(DISTINCT employee_id) AS distinct_employee_count,
        COUNT(*) AS employee_snapshot_count,
        SUM(annual_voluntary_attrition_target) AS voluntary_exits,
        ROUND(100.0 * SUM(annual_voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS annual_attrition_rate_percent
    FROM category_rows
    GROUP BY 1, 2
)
SELECT
    'category' AS row_type,
    metric,
    CAST(metrics.fiscal_year AS VARCHAR(32)) AS category,
    CAST(NULL AS DATE) AS first_snapshot_date,
    CAST(NULL AS DATE) AS last_snapshot_date,
    distinct_employee_count,
    employee_snapshot_count,
    voluntary_exits,
    annual_attrition_rate_percent,
    CAST(NULL AS BIGINT) AS diagnostic_value,
    coverage.total_source_snapshots,
    coverage.complete_followup_snapshots
FROM category_metrics AS metrics
INNER JOIN fiscal_snapshot_coverage AS coverage
  ON coverage.fiscal_year = metrics.fiscal_year
UNION ALL
SELECT
    'coverage',
    'fiscal_year',
    CAST(fiscal_year AS VARCHAR(32)),
    CAST(NULL AS DATE), CAST(NULL AS DATE), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), CAST(NULL AS BIGINT),
    total_source_snapshots, complete_followup_snapshots
FROM fiscal_snapshot_coverage
WHERE fiscal_year BETWEEN 2020 AND 2026
UNION ALL
SELECT
    'diagnostic', metric, CAST(NULL AS VARCHAR(32)),
    CAST(NULL AS DATE), CAST(NULL AS DATE), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
    CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), diagnostic_value,
    CAST(NULL AS BIGINT), CAST(NULL AS BIGINT)
FROM (
    SELECT 'snapshot_count' AS metric, snapshot_count::BIGINT AS diagnostic_value FROM source_quality
    UNION ALL SELECT 'active_employee_snapshot_count', active_employee_snapshot_count::BIGINT FROM source_quality
    UNION ALL SELECT 'duplicate_employee_snapshot_count', duplicate_employee_snapshot_count::BIGINT FROM source_quality
    UNION ALL SELECT 'conflicting_employee_snapshot_count', conflicting_employee_snapshot_count::BIGINT FROM source_quality
) diagnostics
ORDER BY row_type, metric, category;
