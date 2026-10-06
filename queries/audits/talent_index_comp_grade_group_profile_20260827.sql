-- Talent index: aggregate profile of candidate peer-group fields.
-- The source has no column named compensation_grade. This query checks whether
-- rewards_group or level has the group-size pattern described by the owner.
-- Group labels are intentionally not returned.

WITH base AS (
  SELECT
    cycle_number,
    empl_id,
    NULLIF(TRIM(rewards_group), '') AS rewards_group,
    NULLIF(TRIM(level), '') AS level
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
    AND empl_id IS NOT NULL
), candidate_groups AS (
  SELECT
    'rewards_group' AS grouping_candidate,
    cycle_number,
    rewards_group AS grouping_value,
    COUNT(DISTINCT empl_id) AS group_employees
  FROM base
  WHERE rewards_group IS NOT NULL
  GROUP BY 1, 2, 3

  UNION ALL

  SELECT
    'level' AS grouping_candidate,
    cycle_number,
    level AS grouping_value,
    COUNT(DISTINCT empl_id) AS group_employees
  FROM base
  WHERE level IS NOT NULL
  GROUP BY 1, 2, 3
),
source_counts AS (
  SELECT
    'rewards_group' AS grouping_candidate,
    cycle_number,
    COUNT(DISTINCT empl_id) AS source_employees,
    COUNT(CASE WHEN rewards_group IS NOT NULL THEN 1 END) AS populated_rows,
    COUNT(DISTINCT CASE WHEN rewards_group IS NOT NULL THEN empl_id END) AS populated_employees
  FROM base
  GROUP BY 1, 2

  UNION ALL

  SELECT
    'level' AS grouping_candidate,
    cycle_number,
    COUNT(DISTINCT empl_id) AS source_employees,
    COUNT(CASE WHEN level IS NOT NULL THEN 1 END) AS populated_rows,
    COUNT(DISTINCT CASE WHEN level IS NOT NULL THEN empl_id END) AS populated_employees
  FROM base
  GROUP BY 1, 2
),
group_summary AS (
  SELECT
    grouping_candidate,
    cycle_number,
    COUNT(*) AS group_count,
    MIN(group_employees) AS min_group_employees,
    MAX(group_employees) AS max_group_employees,
    SUM(CASE WHEN group_employees < 30 THEN 1 ELSE 0 END) AS groups_below_30,
    SUM(CASE WHEN group_employees >= 30 THEN 1 ELSE 0 END) AS groups_at_least_30,
    SUM(CASE WHEN group_employees < 30 THEN group_employees ELSE 0 END) AS employees_in_groups_below_30,
    SUM(CASE WHEN group_employees >= 30 THEN group_employees ELSE 0 END) AS employees_in_groups_at_least_30
  FROM candidate_groups
  GROUP BY 1, 2
)
SELECT
  g.grouping_candidate,
  g.cycle_number,
  s.source_employees,
  s.populated_rows,
  s.populated_employees,
  g.group_count,
  g.min_group_employees,
  g.max_group_employees,
  g.groups_below_30,
  g.groups_at_least_30,
  g.employees_in_groups_below_30,
  g.employees_in_groups_at_least_30
FROM group_summary AS g
JOIN source_counts AS s
  ON s.grouping_candidate = g.grouping_candidate
 AND s.cycle_number = g.cycle_number
WHERE s.source_employees >= 30
ORDER BY g.grouping_candidate, g.cycle_number;
