/*
  Presentation-safe aggregate check for the proposed Manager layers follow-up.

  Claim: the 0–2 reconstructed-manager-layer cohort at 2025-08-24 can be
  described by compensation-grade family without changing the validated
  hierarchy or attrition definition used on the Manager layers to the CEO
  slide.

  Population: active Regular Employees at 2025-08-24, excluding RF360 through
  the same worker_type / employee_type contract as the existing layers audit.
  Hierarchy: same-snapshot manager_employee_id chain to the unique active
  no-manager root whose job title is classified as CEO. The root identifier is
  used only in joins and is never returned.
  Outcome: strict VOLUNTARY termination in (2025-08-24, 2026-08-23].
  Grade grouping: V-grade family versus every other compensation-grade family.
  The V family is determined by the first character of the stored
  compensation_grade; blank, conflicting, and non-V grades remain in the
  complementary group.

  Acceptance rule:
  - The reconstructed 0–2 layer cohort must reconcile to 185 baseline
    employees and 19 strict-voluntary exits from the frozen layers evidence.
  - There must be one root, every chain must resolve to that approved root, and
    there must be no manager or compensation-grade conflicts in the displayed
    cohort.
  - Both displayed groups must have at least 30 baseline employees and must
    reconcile to the 185-person cohort and its 19 strict-voluntary exits.

  Output is aggregate-only. It never returns employee IDs, managers, names,
  exact pay, or raw grade values.
*/
WITH RECURSIVE
params AS (
  SELECT DATE '2025-08-24' AS baseline_date,
         DATE '2026-08-23' AS outcome_cutoff
),
source_rows AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    CAST(NULLIF(TRIM(CAST(w.manager_employee_id AS VARCHAR(64))), '') AS BIGINT)
      AS manager_employee_id,
    UPPER(TRIM(CAST(w.job_title AS VARCHAR(512)))) AS normalized_job_title,
    w.worker_type,
    w.employee_type
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_date
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
),
node_rollup AS (
  SELECT
    employee_id,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT COALESCE(CAST(manager_employee_id AS VARCHAR(64)), '<NULL>'))
      AS manager_assignment_count,
    MIN(manager_employee_id) AS canonical_manager_employee_id,
    MAX(CASE
      WHEN normalized_job_title LIKE '%CEO%'
        OR normalized_job_title LIKE '%CHIEF EXECUTIVE OFFICER%'
      THEN 1 ELSE 0
    END) AS ceo_title_flag,
    MAX(CASE
      WHEN worker_type = 'Employee' AND employee_type = 'Regular' THEN 1
      ELSE 0
    END) AS display_employee_flag
  FROM source_rows
  GROUP BY 1
),
nodes AS (
  SELECT
    employee_id,
    source_rows,
    manager_assignment_count,
    CASE
      WHEN manager_assignment_count = 1 THEN canonical_manager_employee_id
      ELSE NULL
    END AS manager_employee_id,
    ceo_title_flag,
    display_employee_flag
  FROM node_rollup
),
hierarchy_walk (
  origin_employee_id,
  origin_display_employee_flag,
  current_employee_id,
  current_manager_employee_id,
  reconstructed_depth,
  visited_path,
  failure_reason
) AS (
  SELECT
    n.employee_id AS origin_employee_id,
    n.display_employee_flag AS origin_display_employee_flag,
    n.employee_id AS current_employee_id,
    n.manager_employee_id AS current_manager_employee_id,
    0 AS reconstructed_depth,
    CAST('|' || CAST(n.employee_id AS VARCHAR(32)) || '|' AS VARCHAR(4096))
      AS visited_path,
    CASE
      WHEN n.manager_assignment_count <> 1 THEN 'manager_conflict'
      WHEN n.manager_employee_id = n.employee_id THEN 'self_manager'
      ELSE NULL
    END AS failure_reason
  FROM nodes n

  UNION ALL

  SELECT
    h.origin_employee_id,
    h.origin_display_employee_flag,
    COALESCE(m.employee_id, h.current_manager_employee_id) AS current_employee_id,
    m.manager_employee_id AS current_manager_employee_id,
    CASE
      WHEN h.reconstructed_depth >= 25 THEN h.reconstructed_depth
      ELSE h.reconstructed_depth + 1
    END AS reconstructed_depth,
    CAST(
      h.visited_path || COALESCE(CAST(m.employee_id AS VARCHAR(32)), '<MISSING>') || '|'
      AS VARCHAR(4096)
    ) AS visited_path,
    CASE
      WHEN h.reconstructed_depth >= 25 THEN 'depth_exceeded'
      WHEN m.employee_id IS NULL THEN 'missing_manager'
      WHEN m.manager_assignment_count <> 1 THEN 'manager_conflict'
      WHEN m.manager_employee_id = m.employee_id THEN 'self_manager'
      WHEN POSITION('|' || CAST(m.employee_id AS VARCHAR(32)) || '|' IN h.visited_path) > 0
        THEN 'cycle'
      ELSE NULL
    END AS failure_reason
  FROM hierarchy_walk h
  LEFT JOIN nodes m
    ON m.employee_id = h.current_manager_employee_id
  WHERE h.failure_reason IS NULL
    AND h.current_manager_employee_id IS NOT NULL
),
terminal_ranked AS (
  SELECT
    h.origin_employee_id,
    h.origin_display_employee_flag,
    h.current_employee_id,
    h.current_manager_employee_id,
    h.reconstructed_depth,
    h.visited_path,
    h.failure_reason,
    ROW_NUMBER() OVER (
      PARTITION BY h.origin_employee_id
      ORDER BY h.reconstructed_depth DESC
    ) AS terminal_rank
  FROM hierarchy_walk h
),
terminal AS (
  SELECT
    origin_employee_id,
    origin_display_employee_flag,
    current_employee_id AS terminal_root_employee_id,
    current_manager_employee_id,
    reconstructed_depth,
    failure_reason,
    CASE
      WHEN failure_reason IS NULL AND current_manager_employee_id IS NULL THEN 1
      ELSE 0
    END AS reconstructed_flag
  FROM terminal_ranked
  WHERE terminal_rank = 1
),
root_distribution AS (
  SELECT terminal_root_employee_id, COUNT(*) AS reconstructed_nodes
  FROM terminal
  WHERE reconstructed_flag = 1
  GROUP BY 1
),
root_summary AS (
  SELECT
    COUNT(*) AS root_count,
    COALESCE(MAX(reconstructed_nodes), 0) AS largest_root_node_count
  FROM root_distribution
),
root_reference AS (
  SELECT
    MIN(employee_id) AS approved_root_employee_id,
    COUNT(*) AS approved_root_title_count
  FROM nodes
  WHERE manager_assignment_count = 1
    AND manager_employee_id IS NULL
    AND ceo_title_flag = 1
),
voluntary_events AS (
  SELECT DISTINCT CAST(w.employee_id AS BIGINT) AS employee_id
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > p.baseline_date
    AND CAST(w.term_date AS DATE) <= p.outcome_cutoff
    AND w.employee_id IS NOT NULL
),
display_targets AS (
  SELECT
    t.origin_employee_id AS employee_id,
    t.reconstructed_depth AS depth,
    CASE WHEN v.employee_id IS NULL THEN 0 ELSE 1 END AS voluntary_attrition_target
  FROM terminal t
  LEFT JOIN voluntary_events v
    ON v.employee_id = t.origin_employee_id
  WHERE t.reconstructed_flag = 1
    AND t.terminal_root_employee_id = (SELECT approved_root_employee_id FROM root_reference)
    AND t.origin_display_employee_flag = 1
)
SELECT
  'grade_group_distribution' AS row_type,
  CAST('V_grade_family_vs_all_other_grade_families' AS VARCHAR(128)) AS metric,
  CASE
    WHEN LEFT(g.compensation_grade, 1) = 'V' THEN 'V grade family'
    ELSE 'All other grade families'
  END AS grade_family,
  COUNT(*) AS employee_count,
  SUM(d.voluntary_attrition_target) AS voluntary_exits,
  100.0 * COUNT(*) / 185 AS cohort_share_percent,
  100.0 * SUM(d.voluntary_attrition_target) / NULLIF(COUNT(*), 0)
    AS annual_attrition_rate_percent
FROM display_targets d
INNER JOIN (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    CASE
      WHEN COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(w.compensation_grade AS VARCHAR(256)))), ''), '<NULL>')) = 1
      THEN MIN(NULLIF(UPPER(TRIM(CAST(w.compensation_grade AS VARCHAR(256)))), ''))
      ELSE NULL
    END AS compensation_grade
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN params p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_date
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
  GROUP BY 1
) g
  ON g.employee_id = d.employee_id
WHERE d.depth BETWEEN 0 AND 2
GROUP BY
  CASE
    WHEN LEFT(g.compensation_grade, 1) = 'V' THEN 'V grade family'
    ELSE 'All other grade families'
  END
HAVING COUNT(*) >= 30
ORDER BY grade_family;
