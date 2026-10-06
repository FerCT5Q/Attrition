/*
  Plantilla de una cohorte índice del estudio de salidas secuenciales.
  El generador sustituye exclusivamente los nueve DATE de parameters usando el
  calendario auditado y ejecuta una cohorte a la vez. La salida es agregada.
*/
WITH parameters AS (
  SELECT DATE '2026-03-29' AS t, DATE '2026-02-22' AS p1, DATE '2025-09-28' AS p6,
    DATE '2026-04-26' AS f1, DATE '2026-05-24' AS f2, DATE '2026-06-28' AS f3,
    DATE '2026-07-26' AS f4, DATE '2026-08-23' AS f5, DATE '2026-09-27' AS f6
),
monthly_event_keys AS (
  SELECT w.employee_id, CAST(w.term_date AS DATE) AS term_date,
    UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) AS term_type
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN parameters AS p
  WHERE w.worker_type = 'Employee' AND w.employee_type = 'Regular'
    AND w.term_date > p.p6 AND w.term_date <= p.f6
  GROUP BY 1, 2, 3
),
termination_event_keys AS (
  SELECT a.employeeid AS employee_id, a.term_date,
    UPPER(NULLIF(TRIM(CAST(a.term_type AS VARCHAR(256))), '')) AS term_type
  FROM hrda.all_terminations AS a
  CROSS JOIN parameters AS p
  WHERE a.term_date > p.p6 AND a.term_date <= p.f6
  GROUP BY 1, 2, 3
),
reconciled_event_keys AS (
  SELECT m.employee_id, m.term_date, m.term_type
  FROM monthly_event_keys AS m
  INNER JOIN termination_event_keys AS a
    ON a.employee_id = m.employee_id AND a.term_date = m.term_date
   AND COALESCE(a.term_type, '__NULL__') = COALESCE(m.term_type, '__NULL__')
),
event_manager_candidates AS (
  SELECT e.employee_id, e.term_date, e.term_type, h.manager_employee_id,
    ROW_NUMBER() OVER (
      PARTITION BY e.employee_id, e.term_date, e.term_type
      ORDER BY CAST(h.fis_mo_end_dt AS DATE) DESC
    ) AS manager_rank
  FROM reconciled_event_keys AS e
  CROSS JOIN parameters AS p
  LEFT JOIN hrda.post_hire_monthly_worker_dtls AS h
    ON h.employee_id = e.employee_id
   AND h.worker_type = 'Employee' AND h.employee_type = 'Regular'
   AND h.manager_employee_id IS NOT NULL
   AND CAST(h.fis_mo_end_dt AS DATE) <= e.term_date
   AND CAST(h.fis_mo_end_dt AS DATE) >= DATEADD(month, -2, p.p6)
),
events AS (
  SELECT employee_id, term_date, manager_employee_id,
    CASE WHEN term_type = 'VOLUNTARY' THEN 'voluntary'
         WHEN term_type IS NOT NULL THEN 'nonvoluntary' ELSE 'unknown' END AS event_class
  FROM event_manager_candidates
  WHERE manager_rank = 1 AND manager_employee_id IS NOT NULL
),
active_index AS (
  SELECT w.employee_id, w.manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN parameters AS p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.t
    AND w.worker_type = 'Employee' AND w.employee_type = 'Regular' AND w.active_status = 1
    AND w.manager_employee_id IS NOT NULL
  GROUP BY 1, 2
),
team_sizes AS (
  SELECT manager_employee_id, COUNT(*) AS team_size,
    CASE WHEN COUNT(*) BETWEEN 1 AND 5 THEN '1–5'
         WHEN COUNT(*) BETWEEN 6 AND 10 THEN '6–10'
         WHEN COUNT(*) BETWEEN 11 AND 20 THEN '11–20' ELSE '21+' END AS size_band
  FROM active_index
  GROUP BY 1
),
recent_events AS (
  SELECT e.manager_employee_id,
    SUM(CASE WHEN e.event_class = 'voluntary' AND e.term_date > p.p6 AND e.term_date <= p.t THEN 1 ELSE 0 END) AS six_month_voluntary_events,
    SUM(CASE WHEN e.event_class = 'voluntary' AND e.term_date > p.p1 AND e.term_date <= p.t THEN 1 ELSE 0 END) AS current_interval_voluntary_events
  FROM events AS e CROSS JOIN parameters AS p
  GROUP BY 1
),
index_teams AS (
  SELECT s.manager_employee_id, s.size_band
  FROM team_sizes AS s
  INNER JOIN recent_events AS e ON e.manager_employee_id = s.manager_employee_id
  WHERE e.six_month_voluntary_events = 1 AND e.current_interval_voluntary_events = 1
),
control_teams AS (
  SELECT s.manager_employee_id, s.size_band
  FROM team_sizes AS s
  LEFT JOIN recent_events AS e ON e.manager_employee_id = s.manager_employee_id
  WHERE COALESCE(e.six_month_voluntary_events, 0) = 0
),
roster_raw AS (
  SELECT 'exposed' AS comparison_group, i.manager_employee_id, i.size_band, a.employee_id
  FROM index_teams AS i INNER JOIN active_index AS a ON a.manager_employee_id = i.manager_employee_id
  UNION ALL
  SELECT 'reference_standardized', c.manager_employee_id, c.size_band, a.employee_id
  FROM control_teams AS c INNER JOIN active_index AS a ON a.manager_employee_id = c.manager_employee_id
),
reference_band_counts AS (
  SELECT size_band, SUM(CASE WHEN comparison_group = 'reference_standardized' THEN 1 ELSE 0 END) AS reference_initial_n
  FROM roster_raw GROUP BY 1
),
roster AS (
  SELECT r.comparison_group, r.manager_employee_id, r.size_band, r.employee_id
  FROM roster_raw AS r INNER JOIN reference_band_counts AS b ON b.size_band = r.size_band
  WHERE b.reference_initial_n >= 30
),
follow_steps AS (
  SELECT 1 AS follow_month, t AS interval_start, f1 AS interval_end FROM parameters
  UNION ALL SELECT 2, f1, f2 FROM parameters
  UNION ALL SELECT 3, f2, f3 FROM parameters
  UNION ALL SELECT 4, f3, f4 FROM parameters
  UNION ALL SELECT 5, f4, f5 FROM parameters
  UNION ALL SELECT 6, f5, f6 FROM parameters
),
follow_active AS (
  SELECT CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date, w.employee_id, w.manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN parameters AS p
  WHERE CAST(w.fis_mo_end_dt AS DATE) IN (p.f1, p.f2, p.f3, p.f4, p.f5, p.f6)
    AND w.worker_type = 'Employee' AND w.employee_type = 'Regular' AND w.active_status = 1
    AND w.manager_employee_id IS NOT NULL
  GROUP BY 1, 2, 3
),
follow_status AS (
  SELECT r.comparison_group, r.manager_employee_id, r.size_band, r.employee_id, s.follow_month,
    MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_event,
    MAX(CASE WHEN n.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS nonvoluntary_event,
    MAX(CASE WHEN a.employee_id IS NOT NULL AND a.manager_employee_id = r.manager_employee_id THEN 1 ELSE 0 END) AS retained_manager
  FROM roster AS r CROSS JOIN follow_steps AS s
  LEFT JOIN events AS v ON v.employee_id = r.employee_id AND v.manager_employee_id = r.manager_employee_id
    AND v.event_class = 'voluntary' AND v.term_date > s.interval_start AND v.term_date <= s.interval_end
  LEFT JOIN events AS n ON n.employee_id = r.employee_id AND n.event_class = 'nonvoluntary'
    AND n.term_date > s.interval_start AND n.term_date <= s.interval_end
  LEFT JOIN follow_active AS a ON a.employee_id = r.employee_id AND a.snapshot_date = s.interval_end
  GROUP BY 1, 2, 3, 4, 5
),
event_censor AS (
  SELECT comparison_group, manager_employee_id, size_band, employee_id,
    MIN(CASE WHEN voluntary_event = 1 THEN follow_month END) AS event_month,
    MIN(CASE WHEN voluntary_event = 0 AND (nonvoluntary_event = 1 OR retained_manager = 0) THEN follow_month END) AS censor_month
  FROM follow_status
  GROUP BY 1, 2, 3, 4
),
interval_metrics AS (
  SELECT e.comparison_group, e.size_band, s.follow_month, COUNT(*) AS initial_roster_n,
    SUM(CASE WHEN (e.event_month IS NULL OR e.event_month >= s.follow_month)
              AND (e.censor_month IS NULL OR e.censor_month >= s.follow_month) THEN 1 ELSE 0 END) AS at_risk_n,
    SUM(CASE WHEN e.event_month = s.follow_month AND (e.censor_month IS NULL OR e.event_month <= e.censor_month) THEN 1 ELSE 0 END) AS voluntary_events_in_interval,
    SUM(CASE WHEN e.censor_month = s.follow_month AND (e.event_month IS NULL OR e.event_month <> e.censor_month) THEN 1 ELSE 0 END) AS censored_in_interval
  FROM event_censor AS e CROSS JOIN follow_steps AS s
  GROUP BY 1, 2, 3
),
stratum_curves AS (
  SELECT comparison_group, size_band, follow_month, initial_roster_n, at_risk_n,
    voluntary_events_in_interval, censored_in_interval,
    100.0 * voluntary_events_in_interval::DECIMAL(18,10) / NULLIF(at_risk_n, 0) AS interval_hazard_percent
  FROM interval_metrics
),
valid_bands AS (
  SELECT size_band FROM stratum_curves GROUP BY 1
  HAVING MIN(CASE WHEN comparison_group = 'reference_standardized' THEN at_risk_n END) >= 30
),
scope_curves AS (
  SELECT 'all_teams' AS scope, c.comparison_group, c.size_band, c.follow_month, c.initial_roster_n, c.at_risk_n, c.voluntary_events_in_interval, c.censored_in_interval, c.interval_hazard_percent
  FROM stratum_curves AS c INNER JOIN valid_bands AS b ON b.size_band = c.size_band
  UNION ALL
  SELECT 'teams_6_plus', c.comparison_group, c.size_band, c.follow_month, c.initial_roster_n, c.at_risk_n, c.voluntary_events_in_interval, c.censored_in_interval, c.interval_hazard_percent
  FROM stratum_curves AS c INNER JOIN valid_bands AS b ON b.size_band = c.size_band
  WHERE c.size_band <> '1–5'
),
weights AS (
  SELECT scope, size_band, initial_roster_n::DECIMAL(18,10) / SUM(initial_roster_n) OVER (PARTITION BY scope) AS exposed_weight
  FROM scope_curves WHERE comparison_group = 'exposed' AND follow_month = 1
),
series AS (
  SELECT c.scope, c.comparison_group, c.follow_month,
    ROUND(SUM(c.interval_hazard_percent * w.exposed_weight), 6) AS standardized_hazard_percent,
    SUM(c.initial_roster_n) AS initial_roster_n, SUM(c.at_risk_n) AS at_risk_n,
    SUM(c.voluntary_events_in_interval) AS voluntary_events_in_interval,
    SUM(c.censored_in_interval) AS censored_in_interval, COUNT(*) AS included_bands
  FROM scope_curves AS c INNER JOIN weights AS w ON w.scope = c.scope AND w.size_band = c.size_band
  GROUP BY 1, 2, 3
  HAVING SUM(c.at_risk_n) >= 30
)
SELECT 'series' AS row_type, scope, comparison_group, follow_month, standardized_hazard_percent,
  initial_roster_n, at_risk_n, voluntary_events_in_interval, censored_in_interval, included_bands,
  CAST(NULL AS VARCHAR(128)) AS metric, CAST(NULL AS DECIMAL(18,4)) AS metric_value
FROM series
UNION ALL
SELECT 'audit', CAST(NULL AS VARCHAR(32)), CAST(NULL AS VARCHAR(32)), CAST(NULL AS INTEGER), CAST(NULL AS DECIMAL(18,6)),
  CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
  'index_team_episodes', COUNT(*)::DECIMAL(18,4) FROM index_teams
UNION ALL
SELECT 'audit', CAST(NULL AS VARCHAR(32)), CAST(NULL AS VARCHAR(32)), CAST(NULL AS INTEGER), CAST(NULL AS DECIMAL(18,6)),
  CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
  'series_points', COUNT(*)::DECIMAL(18,4) FROM series
ORDER BY row_type, scope, comparison_group, follow_month, metric;
