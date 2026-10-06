-- Talent index: verify the descriptive 90--100 band in the distribution deck.
--
-- Claim: the deck's 90--100 bar is the aggregate count and percentage of
-- selected latest recoverable stored values for regular employees active on
-- 2026-08-23. This is not a claim that talent_index is a percentile or decile.
--
-- Acceptance rule: the all-cycle row must reproduce 4,846 employees in the
-- 90--100 band out of 39,647 recoverable values (12.222866%). If the value
-- were an equal-probability decile in this exact selected population, the
-- expected count would be 3,964.7; the query reports the descriptive gap but
-- does not infer why it exists.

WITH workforce_snapshot AS (
  SELECT CAST(employee_id AS BIGINT) AS employee_id
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
    MIN(talent_index) AS talent_index
  FROM hrda.master_talent_index
  WHERE empl_id IS NOT NULL
    AND cycle_number IS NOT NULL
  GROUP BY 1, 2
),
selected_cycle AS (
  SELECT employee_id, cycle_number, source_rows, populated_index_rows,
         distinct_index_values, talent_index
  FROM (
    SELECT
      employee_id,
      cycle_number,
      source_rows,
      populated_index_rows,
      distinct_index_values,
      talent_index,
      ROW_NUMBER() OVER (
        PARTITION BY employee_id ORDER BY cycle_number DESC
      ) AS cycle_rank
    FROM employee_cycle
  ) ranked
  WHERE cycle_rank = 1
),
recoverable AS (
  SELECT s.cycle_number, s.talent_index
  FROM workforce_snapshot w
  INNER JOIN selected_cycle s ON s.employee_id = w.employee_id
  WHERE s.source_rows = s.populated_index_rows
    AND s.distinct_index_values = 1
    AND s.talent_index BETWEEN 0 AND 100
),
counts AS (
  SELECT
    COALESCE(CAST(cycle_number AS VARCHAR), 'ALL_SELECTED_CYCLES') AS selected_cycle,
    COUNT(*) AS recoverable_employees,
    COUNT(CASE WHEN talent_index >= 90 AND talent_index <= 100 THEN 1 END)
      AS top_band_employees
  FROM recoverable
  GROUP BY GROUPING SETS ((cycle_number), ())
)
SELECT
  selected_cycle,
  recoverable_employees,
  top_band_employees,
  ROUND(100.0 * top_band_employees / NULLIF(recoverable_employees, 0), 6)
    AS top_band_percent,
  ROUND(recoverable_employees * 0.10, 1) AS equal_decile_expected_count,
  ROUND(
    top_band_employees - (recoverable_employees * 0.10),
    1
  ) AS difference_from_equal_decile_count,
  ROUND(
    100.0 * top_band_employees / NULLIF(recoverable_employees, 0) - 10.0,
    6
  ) AS difference_from_equal_decile_percentage_points
FROM counts
WHERE recoverable_employees >= 30
ORDER BY CASE WHEN selected_cycle = 'ALL_SELECTED_CYCLES' THEN 0 ELSE 1 END,
         selected_cycle;
