WITH target AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS VARCHAR(32)) AS fiscal_year,
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
    MAX(fiscal_year) AS fiscal_year,
    DENSE_RANK() OVER (ORDER BY snapshot_date) AS snapshot_seq
  FROM target
  GROUP BY snapshot_date
), base AS (
  SELECT
    t.snapshot_date,
    c.fiscal_year,
    c.snapshot_seq,
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
), feature_ready AS (
  SELECT manager_id, snapshot_date
  FROM manager_persistence
  WHERE score_ready = 1
    AND recent_score_snapshots = 6
    AND recent_ready_scores = 6
)
SELECT
  b.snapshot_date,
  MAX(b.fiscal_year) AS fiscal_year,
  COUNT(DISTINCT b.employee_id) AS eligible_employees,
  COUNT(DISTINCT CASE WHEN f.manager_id IS NOT NULL THEN b.employee_id END) AS observable_employees,
  CAST(NULL AS BIGINT) AS event_employees,
  'Observable exige 12 snapshots de ventana, 5 reportes, 60 empleado-meses y seis scores consecutivos calculables. Historia insuficiente es Unknown.' AS notes
FROM base b
LEFT JOIN feature_ready f
  ON f.manager_id = b.manager_employee_id
 AND f.snapshot_date = b.snapshot_date
GROUP BY b.snapshot_date
ORDER BY b.snapshot_date;
