-- Talent Index: aggregate distribution of the latest recoverable stored value
-- for regular employees active in the 2026-08-23 monthly workforce snapshot.
--
-- Selection rule: group hrda.master_talent_index to employee + cycle_number,
-- then select the highest cycle_number per employee. A selected cycle is
-- recoverable only when every source row has a non-null talent_index and all
-- source rows agree on one distinct value. The query does not use technical
-- timestamps as an effective date and does not fall back to an older cycle.
--
-- Publication rule: bands start at 10-point intervals over the stored 0--100
-- scale. If a non-empty 10-point band is below n=30, the query deterministically
-- coarsens to the first eligible width among 20, 50, and 100 points. Every
-- output row is aggregate-only; employee identifiers remain inside the CTEs.

WITH workforce_snapshot AS (
  SELECT
    CAST(employee_id AS BIGINT) AS employee_id,
    COUNT(*) AS workforce_source_rows
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
    AND fis_mo_end_dt = DATE '2026-08-23'
  GROUP BY 1
),
employee_cycle AS (
  SELECT
    CAST(empl_id AS BIGINT) AS employee_id,
    cycle_number,
    COUNT(*) AS source_rows,
    COUNT(talent_index) AS populated_index_rows,
    COUNT(DISTINCT talent_index) AS distinct_index_values,
    MIN(talent_index) AS sole_talent_index
  FROM hrda.master_talent_index
  WHERE empl_id IS NOT NULL
    AND cycle_number IS NOT NULL
  GROUP BY 1, 2
),
ranked_cycles AS (
  SELECT
    employee_id,
    cycle_number,
    source_rows,
    populated_index_rows,
    distinct_index_values,
    sole_talent_index,
    ROW_NUMBER() OVER (
      PARTITION BY employee_id
      ORDER BY cycle_number DESC
    ) AS cycle_rank
  FROM employee_cycle
),
selected_cycle AS (
  SELECT
    employee_id,
    cycle_number,
    source_rows,
    populated_index_rows,
    distinct_index_values,
    sole_talent_index
  FROM ranked_cycles
  WHERE cycle_rank = 1
),
classified AS (
  SELECT
    w.employee_id,
    w.workforce_source_rows,
    s.cycle_number,
    s.source_rows,
    s.populated_index_rows,
    s.distinct_index_values,
    CASE
      WHEN s.employee_id IS NULL THEN 'no_stored_cycle'
      WHEN s.populated_index_rows <> s.source_rows THEN 'null_in_selected_cycle'
      WHEN s.distinct_index_values <> 1 THEN 'conflicting_selected_cycle'
      ELSE 'recoverable'
    END AS selection_status,
    CASE
      WHEN s.employee_id IS NOT NULL
       AND s.populated_index_rows = s.source_rows
       AND s.distinct_index_values = 1
      THEN s.sole_talent_index
      ELSE NULL
    END AS selected_talent_index
  FROM workforce_snapshot w
  LEFT JOIN selected_cycle s
    ON s.employee_id = w.employee_id
),
summary AS (
  SELECT
    COUNT(*) AS eligible_employees,
    COUNT(CASE WHEN cycle_number IS NOT NULL THEN 1 END) AS join_matched_employees,
    COUNT(CASE WHEN cycle_number IS NULL THEN 1 END) AS join_unmatched_employees,
    COUNT(CASE WHEN selection_status = 'recoverable' THEN 1 END) AS observable_employees,
    COUNT(CASE WHEN selection_status <> 'recoverable' THEN 1 END) AS not_observable_employees,
    COUNT(CASE WHEN selection_status = 'no_stored_cycle' THEN 1 END) AS no_stored_cycle_employees,
    COUNT(CASE WHEN selection_status = 'null_in_selected_cycle' THEN 1 END) AS selected_null_safeguard_employees,
    COUNT(CASE WHEN selection_status = 'conflicting_selected_cycle' THEN 1 END) AS selected_conflict_safeguard_employees,
    COALESCE(SUM(workforce_source_rows - 1), 0) AS workforce_duplicate_source_rows,
    COUNT(CASE WHEN workforce_source_rows > 1 THEN 1 END) AS workforce_duplicate_employee_keys,
    COALESCE(SUM(CASE WHEN source_rows > 1 THEN source_rows - 1 ELSE 0 END), 0) AS selected_cycle_duplicate_source_rows,
    COUNT(CASE WHEN source_rows > 1 THEN 1 END) AS selected_cycle_duplicate_employee_keys,
    COUNT(CASE WHEN selection_status = 'recoverable' AND (selected_talent_index < 0 OR selected_talent_index > 100) THEN 1 END) AS out_of_range_employees,
    COUNT(CASE WHEN selection_status = 'recoverable' AND selected_talent_index BETWEEN 0 AND 100 THEN 1 END) AS in_range_employees,
    MIN(CASE WHEN selection_status = 'recoverable' THEN selected_talent_index END) AS minimum_stored_value,
    MAX(CASE WHEN selection_status = 'recoverable' THEN selected_talent_index END) AS maximum_stored_value,
    PERCENTILE_CONT(0.25) WITHIN GROUP (
      ORDER BY CASE WHEN selection_status = 'recoverable' THEN selected_talent_index END
    ) AS first_quartile,
    PERCENTILE_CONT(0.50) WITHIN GROUP (
      ORDER BY CASE WHEN selection_status = 'recoverable' THEN selected_talent_index END
    ) AS median_stored_value,
    PERCENTILE_CONT(0.75) WITHIN GROUP (
      ORDER BY CASE WHEN selection_status = 'recoverable' THEN selected_talent_index END
    ) AS third_quartile
  FROM classified
),
candidate_widths AS (
  SELECT 10 AS band_width
  UNION ALL SELECT 20
  UNION ALL SELECT 50
  UNION ALL SELECT 100
),
candidate_band_counts AS (
  SELECT
    c.band_width,
    LEAST(
      FLOOR(classified.selected_talent_index / c.band_width)::INTEGER,
      (100 / c.band_width) - 1
    ) AS band_order,
    COUNT(*) AS employee_count
  FROM classified
  CROSS JOIN candidate_widths c
  WHERE classified.selection_status = 'recoverable'
    AND classified.selected_talent_index BETWEEN 0 AND 100
  GROUP BY 1, 2
),
eligible_widths AS (
  SELECT band_width
  FROM candidate_band_counts
  GROUP BY 1
  HAVING MIN(employee_count) >= 30
),
chosen_width AS (
  SELECT MIN(band_width) AS band_width
  FROM eligible_widths
),
published_bands AS (
  SELECT
    b.band_order,
    c.band_width,
    b.band_order * c.band_width AS band_lower,
    (b.band_order + 1) * c.band_width AS band_upper,
    b.employee_count,
    100.0 * b.employee_count / NULLIF(s.observable_employees, 0) AS percent_of_observable
  FROM candidate_band_counts b
  CROSS JOIN chosen_width c
  CROSS JOIN summary s
  WHERE b.band_width = c.band_width
),
band_summary AS (
  SELECT COALESCE(SUM(employee_count), 0) AS published_band_employees
  FROM published_bands
)
SELECT
  CAST('summary' AS VARCHAR(16)) AS row_type,
  CAST(metric AS VARCHAR(80)) AS metric,
  CAST(NULL AS INTEGER) AS band_order,
  CAST(NULL AS NUMERIC(10, 2)) AS band_lower,
  CAST(NULL AS NUMERIC(10, 2)) AS band_upper,
  CAST(NULL AS INTEGER) AS band_upper_inclusive,
  CAST(NULL AS BIGINT) AS employee_count,
  CAST(NULL AS NUMERIC(12, 6)) AS percent_of_observable,
  CAST(metric_value AS NUMERIC(18, 6)) AS metric_value
FROM (
  SELECT 'eligible_employees' AS metric, eligible_employees::NUMERIC(18, 6) AS metric_value FROM summary
  UNION ALL SELECT 'join_matched_employees', join_matched_employees::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'join_unmatched_employees', join_unmatched_employees::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'observable_employees', observable_employees::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'not_observable_employees', not_observable_employees::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'no_stored_cycle_employees', no_stored_cycle_employees::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'selected_null_safeguard_employees', selected_null_safeguard_employees::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'selected_conflict_safeguard_employees', selected_conflict_safeguard_employees::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'workforce_duplicate_source_rows', workforce_duplicate_source_rows::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'workforce_duplicate_employee_keys', workforce_duplicate_employee_keys::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'selected_cycle_duplicate_source_rows', selected_cycle_duplicate_source_rows::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'selected_cycle_duplicate_employee_keys', selected_cycle_duplicate_employee_keys::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'out_of_range_employees', out_of_range_employees::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'in_range_employees', in_range_employees::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'minimum_stored_value', minimum_stored_value::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'maximum_stored_value', maximum_stored_value::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'first_quartile', first_quartile::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'median_stored_value', median_stored_value::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'third_quartile', third_quartile::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'interquartile_range', (third_quartile - first_quartile)::NUMERIC(18, 6) FROM summary
  UNION ALL SELECT 'published_band_employees', published_band_employees::NUMERIC(18, 6) FROM band_summary
  UNION ALL SELECT 'selected_band_width', chosen_width.band_width::NUMERIC(18, 6) FROM chosen_width
  UNION ALL SELECT 'selected_output_duplicate_employee_keys', 0::NUMERIC(18, 6)
) metrics
UNION ALL
SELECT
  CAST('band' AS VARCHAR(16)) AS row_type,
  CAST('stored_talent_index' AS VARCHAR(80)) AS metric,
  band_order,
  band_lower::NUMERIC(10, 2),
  band_upper::NUMERIC(10, 2),
  CASE WHEN band_upper = 100 THEN 1 ELSE 0 END AS band_upper_inclusive,
  employee_count,
  percent_of_observable::NUMERIC(12, 6),
  CAST(NULL AS NUMERIC(18, 6)) AS metric_value
FROM published_bands
ORDER BY row_type, band_order, metric;
