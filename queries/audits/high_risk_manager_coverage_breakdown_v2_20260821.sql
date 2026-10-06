WITH target AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
), snapshot_calendar AS (
  SELECT
    snapshot_date,
    DENSE_RANK() OVER (ORDER BY snapshot_date) AS snapshot_seq,
    DENSE_RANK() OVER (ORDER BY snapshot_date DESC) AS reverse_snapshot_seq
  FROM target
  GROUP BY snapshot_date
), base AS (
  SELECT
    t.snapshot_date,
    c.snapshot_seq,
    c.reverse_snapshot_seq,
    t.employee_id,
    t.manager_employee_id
  FROM target t
  INNER JOIN snapshot_calendar c
    ON c.snapshot_date = t.snapshot_date
), manager_snapshots AS (
  SELECT DISTINCT
    manager_employee_id AS manager_id,
    snapshot_date,
    snapshot_seq
  FROM base
  WHERE manager_employee_id IS NOT NULL
), manager_rolling AS (
  SELECT
    m.manager_id,
    m.snapshot_date,
    m.snapshot_seq,
    COUNT(h.employee_id) AS employee_months,
    COUNT(DISTINCT h.employee_id) AS distinct_reports,
    CASE
      WHEN m.snapshot_seq >= 12
       AND COUNT(h.employee_id) >= 60
       AND COUNT(DISTINCT h.employee_id) >= 5
      THEN 1 ELSE 0
    END AS score_ready
  FROM manager_snapshots m
  INNER JOIN base h
    ON h.manager_employee_id = m.manager_id
   AND h.snapshot_seq BETWEEN m.snapshot_seq - 11 AND m.snapshot_seq
  GROUP BY m.manager_id, m.snapshot_date, m.snapshot_seq
), manager_persistence AS (
  SELECT
    current_score.manager_id,
    current_score.snapshot_date,
    current_score.snapshot_seq,
    current_score.employee_months,
    current_score.distinct_reports,
    current_score.score_ready,
    COUNT(prior_score.snapshot_seq) AS recent_score_snapshots,
    COALESCE(SUM(prior_score.score_ready), 0) AS recent_ready_scores
  FROM manager_rolling current_score
  LEFT JOIN manager_rolling prior_score
    ON prior_score.manager_id = current_score.manager_id
   AND prior_score.snapshot_seq BETWEEN current_score.snapshot_seq - 5 AND current_score.snapshot_seq
  GROUP BY
    current_score.manager_id,
    current_score.snapshot_date,
    current_score.snapshot_seq,
    current_score.employee_months,
    current_score.distinct_reports,
    current_score.score_ready
), classified AS (
  SELECT
    b.snapshot_date,
    b.employee_id,
    CASE
      WHEN b.manager_employee_id IS NULL THEN 'missing_manager'
      WHEN p.manager_id IS NULL THEN 'missing_manager_history'
      WHEN p.snapshot_seq < 12 THEN 'global_history_under_12'
      WHEN p.distinct_reports < 5 THEN 'below_five_reports'
      WHEN p.employee_months < 60 THEN 'below_sixty_employee_months'
      WHEN p.recent_score_snapshots < 6 THEN 'under_six_manager_snapshots'
      WHEN p.recent_ready_scores < 6 THEN 'under_six_ready_scores'
      WHEN p.score_ready = 1 THEN 'observable'
      ELSE 'unclassified'
    END AS coverage_class
  FROM base b
  LEFT JOIN manager_persistence p
    ON p.manager_id = b.manager_employee_id
   AND p.snapshot_date = b.snapshot_date
  WHERE b.reverse_snapshot_seq <= 3
)
SELECT
  snapshot_date,
  COUNT(DISTINCT employee_id) AS eligible_count,
  COUNT(DISTINCT CASE WHEN coverage_class = 'observable' THEN employee_id END) AS observable_count,
  COUNT(DISTINCT CASE WHEN coverage_class = 'missing_manager' THEN employee_id END) AS missing_manager_count,
  COUNT(DISTINCT CASE WHEN coverage_class = 'missing_manager_history' THEN employee_id END) AS missing_manager_history_count,
  COUNT(DISTINCT CASE WHEN coverage_class = 'global_history_under_12' THEN employee_id END) AS global_history_under_12_count,
  COUNT(DISTINCT CASE WHEN coverage_class = 'below_five_reports' THEN employee_id END) AS below_five_reports_count,
  COUNT(DISTINCT CASE WHEN coverage_class = 'below_sixty_employee_months' THEN employee_id END) AS below_sixty_employee_months_count,
  COUNT(DISTINCT CASE WHEN coverage_class = 'under_six_manager_snapshots' THEN employee_id END) AS under_six_manager_snapshots_count,
  COUNT(DISTINCT CASE WHEN coverage_class = 'under_six_ready_scores' THEN employee_id END) AS under_six_ready_scores_count,
  COUNT(DISTINCT CASE WHEN coverage_class = 'unclassified' THEN employee_id END) AS unclassified_count,
  (
    COUNT(DISTINCT CASE WHEN coverage_class = 'observable' THEN employee_id END)
    + COUNT(DISTINCT CASE WHEN coverage_class = 'missing_manager' THEN employee_id END)
    + COUNT(DISTINCT CASE WHEN coverage_class = 'missing_manager_history' THEN employee_id END)
    + COUNT(DISTINCT CASE WHEN coverage_class = 'global_history_under_12' THEN employee_id END)
    + COUNT(DISTINCT CASE WHEN coverage_class = 'below_five_reports' THEN employee_id END)
    + COUNT(DISTINCT CASE WHEN coverage_class = 'below_sixty_employee_months' THEN employee_id END)
    + COUNT(DISTINCT CASE WHEN coverage_class = 'under_six_manager_snapshots' THEN employee_id END)
    + COUNT(DISTINCT CASE WHEN coverage_class = 'under_six_ready_scores' THEN employee_id END)
    + COUNT(DISTINCT CASE WHEN coverage_class = 'unclassified' THEN employee_id END)
  ) AS classified_count
FROM classified
GROUP BY snapshot_date
ORDER BY snapshot_date;
