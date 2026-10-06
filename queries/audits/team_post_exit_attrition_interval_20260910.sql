/*
  Un intervalo del estudio de salidas secuenciales.
  Cambiar únicamente params.follow_month (1 a 6) para obtener un hazard
  estandarizado agregado. El generador ejecuta las seis variantes y compone
  1 - producto(1 - hazard) como incidencia acumulada Kaplan–Meier.
  Esta consulta no devuelve estratos, empleados, managers ni identificadores.
*/
WITH params AS (
  SELECT 1::INTEGER AS follow_month
),
source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
),
raw_history AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id, manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  CROSS JOIN source_bounds AS bounds
  WHERE worker_type = 'Employee' AND employee_type = 'Regular'
    AND fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) >= DATEADD(month, -37, bounds.latest_snapshot_date)
    AND employee_id IN (
      SELECT DISTINCT t.employeeid
      FROM hrda.all_terminations AS t
      CROSS JOIN source_bounds AS term_bounds
      WHERE t.term_date >= DATEADD(month, -36, term_bounds.latest_snapshot_date)
        AND t.term_date <= term_bounds.latest_snapshot_date
    )
),
history_manager_by_snapshot AS (
  SELECT snapshot_date, employee_id,
    COUNT(DISTINCT manager_employee_id) AS manager_value_count,
    CASE WHEN COUNT(DISTINCT manager_employee_id) = 1 THEN MAX(manager_employee_id) END AS manager_employee_id
  FROM raw_history
  WHERE manager_employee_id IS NOT NULL
  GROUP BY 1, 2
),
raw_active AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id, manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  CROSS JOIN source_bounds AS bounds
  WHERE worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) >= DATEADD(month, -37, bounds.latest_snapshot_date)
),
active_employee_snapshot AS (
  SELECT snapshot_date, employee_id,
    COUNT(DISTINCT manager_employee_id) AS manager_value_count,
    CASE WHEN COUNT(DISTINCT manager_employee_id) = 1 THEN MAX(manager_employee_id) END AS manager_employee_id
  FROM raw_active
  WHERE manager_employee_id IS NOT NULL
  GROUP BY 1, 2
),
snapshot_calendar_base AS (
  SELECT DISTINCT snapshot_date FROM active_employee_snapshot
),
snapshot_calendar_lag_lead AS (
  SELECT snapshot_date,
    LAG(snapshot_date, 1) OVER (ORDER BY snapshot_date) AS p1,
    LAG(snapshot_date, 2) OVER (ORDER BY snapshot_date) AS p2,
    LAG(snapshot_date, 3) OVER (ORDER BY snapshot_date) AS p3,
    LAG(snapshot_date, 4) OVER (ORDER BY snapshot_date) AS p4,
    LAG(snapshot_date, 5) OVER (ORDER BY snapshot_date) AS p5,
    LAG(snapshot_date, 6) OVER (ORDER BY snapshot_date) AS p6,
    LEAD(snapshot_date, 1) OVER (ORDER BY snapshot_date) AS f1,
    LEAD(snapshot_date, 2) OVER (ORDER BY snapshot_date) AS f2,
    LEAD(snapshot_date, 3) OVER (ORDER BY snapshot_date) AS f3,
    LEAD(snapshot_date, 4) OVER (ORDER BY snapshot_date) AS f4,
    LEAD(snapshot_date, 5) OVER (ORDER BY snapshot_date) AS f5,
    LEAD(snapshot_date, 6) OVER (ORDER BY snapshot_date) AS f6
  FROM snapshot_calendar_base
),
complete_calendars AS (
  SELECT c.snapshot_date, c.p1, c.p2, c.p3, c.p4, c.p5, c.p6, c.f1, c.f2, c.f3, c.f4, c.f5, c.f6
  FROM snapshot_calendar_lag_lead AS c
  CROSS JOIN source_bounds AS bounds
  WHERE c.p6 IS NOT NULL AND c.f6 IS NOT NULL
    AND c.snapshot_date >= DATEADD(month, -29, bounds.latest_snapshot_date)
    AND DATEDIFF(day, c.p6, c.p5) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.p5, c.p4) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.p4, c.p3) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.p3, c.p2) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.p2, c.p1) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.p1, c.snapshot_date) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.snapshot_date, c.f1) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.f1, c.f2) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.f2, c.f3) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.f3, c.f4) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.f4, c.f5) BETWEEN 20 AND 45
    AND DATEDIFF(day, c.f5, c.f6) BETWEEN 20 AND 45
),
termination_raw AS (
  SELECT employee_id, CAST(term_date AS DATE) AS term_date,
    UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) AS normalized_term_type
  FROM hrda.post_hire_monthly_worker_dtls
  CROSS JOIN source_bounds AS bounds
  WHERE worker_type = 'Employee' AND employee_type = 'Regular' AND term_date IS NOT NULL
    AND CAST(term_date AS DATE) >= DATEADD(month, -36, bounds.latest_snapshot_date)
),
monthly_termination_keys AS (
  SELECT employee_id, term_date, normalized_term_type
  FROM termination_raw
  GROUP BY 1, 2, 3
),
all_termination_keys AS (
  SELECT employeeid AS employee_id, term_date,
    UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) AS normalized_term_type
  FROM hrda.all_terminations
  CROSS JOIN source_bounds AS bounds
  WHERE term_date IS NOT NULL
    AND term_date >= DATEADD(month, -36, bounds.latest_snapshot_date)
    AND term_date <= bounds.latest_snapshot_date
  GROUP BY 1, 2, 3
),
reconciled_termination_keys AS (
  SELECT m.employee_id, m.term_date, m.normalized_term_type
  FROM monthly_termination_keys AS m
  INNER JOIN all_termination_keys AS a
    ON a.employee_id = m.employee_id
   AND a.term_date = m.term_date
   AND COALESCE(a.normalized_term_type, '__NULL__') = COALESCE(m.normalized_term_type, '__NULL__')
),
termination_events AS (
  SELECT employee_id, term_date,
    MAX(CASE WHEN normalized_term_type = 'VOLUNTARY' THEN 1 ELSE 0 END) AS has_voluntary_type,
    MAX(CASE WHEN normalized_term_type IS NOT NULL AND normalized_term_type <> 'VOLUNTARY' THEN 1 ELSE 0 END) AS has_nonvoluntary_type
  FROM reconciled_termination_keys
  GROUP BY 1, 2
),
classified_termination_events AS (
  SELECT employee_id, term_date,
    CASE WHEN has_voluntary_type = 1 AND has_nonvoluntary_type = 0 THEN 'voluntary'
         WHEN has_voluntary_type = 0 AND has_nonvoluntary_type = 1 THEN 'nonvoluntary'
         ELSE 'ambiguous_or_unknown' END AS event_class,
    CASE WHEN has_voluntary_type = 1 AND has_nonvoluntary_type = 1 THEN 1 ELSE 0 END AS term_type_conflict
  FROM termination_events
),
event_manager_candidates AS (
  SELECT e.employee_id, e.term_date, e.event_class, e.term_type_conflict, h.manager_employee_id,
    ROW_NUMBER() OVER (PARTITION BY e.employee_id, e.term_date ORDER BY h.snapshot_date DESC) AS manager_rank
  FROM classified_termination_events AS e
  LEFT JOIN history_manager_by_snapshot AS h
    ON h.employee_id = e.employee_id AND h.snapshot_date <= e.term_date
),
termination_events_with_manager AS (
  SELECT employee_id, term_date, event_class, term_type_conflict, manager_employee_id
  FROM event_manager_candidates
  WHERE manager_rank = 1
),
voluntary_events AS (
  SELECT employee_id, term_date, manager_employee_id
  FROM termination_events_with_manager
  WHERE event_class = 'voluntary' AND manager_employee_id IS NOT NULL
),
nonvoluntary_events AS (
  SELECT employee_id, term_date
  FROM termination_events_with_manager
  WHERE event_class = 'nonvoluntary'
),
team_snapshot_sizes AS (
  SELECT snapshot_date, manager_employee_id, COUNT(*) AS team_size,
    CASE WHEN COUNT(*) BETWEEN 1 AND 5 THEN '1–5'
         WHEN COUNT(*) BETWEEN 6 AND 10 THEN '6–10'
         WHEN COUNT(*) BETWEEN 11 AND 20 THEN '11–20' ELSE '21+' END AS size_band
  FROM active_employee_snapshot
  WHERE manager_employee_id IS NOT NULL
  GROUP BY 1, 2
),
team_voluntary_window AS (
  SELECT c.snapshot_date, v.manager_employee_id,
    COUNT(*) AS six_month_voluntary_events,
    SUM(CASE WHEN v.term_date > c.p1 THEN 1 ELSE 0 END) AS current_interval_voluntary_events
  FROM complete_calendars AS c
  INNER JOIN voluntary_events AS v ON v.term_date > c.p6 AND v.term_date <= c.snapshot_date
  GROUP BY 1, 2
),
index_teams AS (
  SELECT c.snapshot_date, s.manager_employee_id, s.size_band
  FROM complete_calendars AS c
  INNER JOIN team_snapshot_sizes AS s ON s.snapshot_date = c.snapshot_date
  INNER JOIN team_voluntary_window AS w ON w.snapshot_date = s.snapshot_date AND w.manager_employee_id = s.manager_employee_id
  WHERE w.six_month_voluntary_events = 1 AND w.current_interval_voluntary_events = 1
),
control_teams AS (
  SELECT c.snapshot_date, s.manager_employee_id, s.size_band
  FROM complete_calendars AS c
  INNER JOIN team_snapshot_sizes AS s ON s.snapshot_date = c.snapshot_date
  LEFT JOIN team_voluntary_window AS w ON w.snapshot_date = s.snapshot_date AND w.manager_employee_id = s.manager_employee_id
  WHERE COALESCE(w.six_month_voluntary_events, 0) = 0
),
exposed_roster AS (
  SELECT 'exposed' AS comparison_group, i.snapshot_date, i.manager_employee_id, i.size_band, a.employee_id
  FROM index_teams AS i
  INNER JOIN active_employee_snapshot AS a ON a.snapshot_date = i.snapshot_date AND a.manager_employee_id = i.manager_employee_id
),
reference_roster AS (
  SELECT 'reference_standardized' AS comparison_group, c.snapshot_date, c.manager_employee_id, c.size_band, a.employee_id
  FROM control_teams AS c
  INNER JOIN active_employee_snapshot AS a ON a.snapshot_date = c.snapshot_date AND a.manager_employee_id = c.manager_employee_id
),
initial_strata AS (
  SELECT snapshot_date, size_band,
    SUM(CASE WHEN comparison_group = 'exposed' THEN 1 ELSE 0 END) AS exposed_initial_n,
    SUM(CASE WHEN comparison_group = 'reference_standardized' THEN 1 ELSE 0 END) AS reference_initial_n
  FROM (
    SELECT comparison_group, snapshot_date, manager_employee_id, size_band, employee_id FROM exposed_roster
    UNION ALL
    SELECT comparison_group, snapshot_date, manager_employee_id, size_band, employee_id FROM reference_roster
  ) AS combined
  GROUP BY 1, 2
),
roster AS (
  SELECT r.comparison_group, r.snapshot_date, r.manager_employee_id, r.size_band, r.employee_id
  FROM (
    SELECT comparison_group, snapshot_date, manager_employee_id, size_band, employee_id FROM exposed_roster
    UNION ALL
    SELECT comparison_group, snapshot_date, manager_employee_id, size_band, employee_id FROM reference_roster
  ) AS r
  INNER JOIN initial_strata AS s ON s.snapshot_date = r.snapshot_date AND s.size_band = r.size_band
  WHERE s.reference_initial_n >= 30
),
follow_target AS (
  SELECT r.comparison_group, r.snapshot_date, r.manager_employee_id, r.size_band, r.employee_id,
    p.follow_month,
    CASE p.follow_month WHEN 1 THEN c.snapshot_date WHEN 2 THEN c.f1 WHEN 3 THEN c.f2
      WHEN 4 THEN c.f3 WHEN 5 THEN c.f4 WHEN 6 THEN c.f5 END AS interval_start,
    CASE p.follow_month WHEN 1 THEN c.f1 WHEN 2 THEN c.f2 WHEN 3 THEN c.f3
      WHEN 4 THEN c.f4 WHEN 5 THEN c.f5 WHEN 6 THEN c.f6 END AS interval_end,
    c.f1, c.f2, c.f3, c.f4, c.f5, c.f6
  FROM roster AS r
  INNER JOIN complete_calendars AS c ON c.snapshot_date = r.snapshot_date
  CROSS JOIN params AS p
),
follow_flags AS (
  SELECT t.comparison_group, t.snapshot_date, t.size_band, t.employee_id, t.manager_employee_id AS index_manager_employee_id, t.follow_month,
    CASE WHEN
      (t.follow_month < 2 OR (a1.employee_id IS NOT NULL AND a1.manager_employee_id = t.manager_employee_id))
      AND (t.follow_month < 3 OR (a2.employee_id IS NOT NULL AND a2.manager_employee_id = t.manager_employee_id))
      AND (t.follow_month < 4 OR (a3.employee_id IS NOT NULL AND a3.manager_employee_id = t.manager_employee_id))
      AND (t.follow_month < 5 OR (a4.employee_id IS NOT NULL AND a4.manager_employee_id = t.manager_employee_id))
      AND (t.follow_month < 6 OR (a5.employee_id IS NOT NULL AND a5.manager_employee_id = t.manager_employee_id))
      AND prior_v.employee_id IS NULL AND prior_n.employee_id IS NULL
    THEN 1 ELSE 0 END AS at_risk,
    CASE WHEN current_v.employee_id IS NOT NULL THEN 1 ELSE 0 END AS voluntary_event,
    CASE WHEN current_n.employee_id IS NOT NULL THEN 1 ELSE 0 END AS nonvoluntary_event,
    CASE t.follow_month WHEN 1 THEN a1.manager_employee_id WHEN 2 THEN a2.manager_employee_id
      WHEN 3 THEN a3.manager_employee_id WHEN 4 THEN a4.manager_employee_id
      WHEN 5 THEN a5.manager_employee_id WHEN 6 THEN a6.manager_employee_id END AS manager_at_interval_end
  FROM follow_target AS t
  LEFT JOIN active_employee_snapshot AS a1 ON a1.employee_id = t.employee_id AND a1.snapshot_date = t.f1
  LEFT JOIN active_employee_snapshot AS a2 ON t.follow_month >= 2 AND a2.employee_id = t.employee_id AND a2.snapshot_date = t.f2
  LEFT JOIN active_employee_snapshot AS a3 ON t.follow_month >= 3 AND a3.employee_id = t.employee_id AND a3.snapshot_date = t.f3
  LEFT JOIN active_employee_snapshot AS a4 ON t.follow_month >= 4 AND a4.employee_id = t.employee_id AND a4.snapshot_date = t.f4
  LEFT JOIN active_employee_snapshot AS a5 ON t.follow_month >= 5 AND a5.employee_id = t.employee_id AND a5.snapshot_date = t.f5
  LEFT JOIN active_employee_snapshot AS a6 ON t.follow_month >= 6 AND a6.employee_id = t.employee_id AND a6.snapshot_date = t.f6
  LEFT JOIN voluntary_events AS prior_v ON prior_v.employee_id = t.employee_id
    AND prior_v.manager_employee_id = t.manager_employee_id
    AND prior_v.term_date > t.snapshot_date AND prior_v.term_date <= t.interval_start
  LEFT JOIN nonvoluntary_events AS prior_n ON prior_n.employee_id = t.employee_id
    AND prior_n.term_date > t.snapshot_date AND prior_n.term_date <= t.interval_start
  LEFT JOIN voluntary_events AS current_v ON current_v.employee_id = t.employee_id
    AND current_v.manager_employee_id = t.manager_employee_id
    AND current_v.term_date > t.interval_start AND current_v.term_date <= t.interval_end
  LEFT JOIN nonvoluntary_events AS current_n ON current_n.employee_id = t.employee_id
    AND current_n.term_date > t.interval_start AND current_n.term_date <= t.interval_end
),
interval_strata AS (
  SELECT f.comparison_group, f.snapshot_date, f.size_band, f.follow_month,
    COUNT(*) AS initial_roster_n,
    SUM(f.at_risk) AS at_risk_n,
    SUM(CASE WHEN f.at_risk = 1 AND f.voluntary_event = 1 THEN 1 ELSE 0 END) AS voluntary_events_in_interval,
    SUM(CASE WHEN f.at_risk = 1 AND f.voluntary_event = 0
              AND (f.nonvoluntary_event = 1 OR f.manager_at_interval_end IS NULL
                   OR f.manager_at_interval_end <> f.index_manager_employee_id) THEN 1 ELSE 0 END) AS censored_in_interval
  FROM follow_flags AS f
  GROUP BY 1, 2, 3, 4
),
scoped_strata AS (
  SELECT 'all_teams' AS scope, comparison_group, snapshot_date, size_band, follow_month,
    initial_roster_n, at_risk_n, voluntary_events_in_interval, censored_in_interval
  FROM interval_strata
  UNION ALL
  SELECT 'teams_6_plus', comparison_group, snapshot_date, size_band, follow_month,
    initial_roster_n, at_risk_n, voluntary_events_in_interval, censored_in_interval
  FROM interval_strata
  WHERE size_band <> '1–5'
),
stratum_pivot AS (
  SELECT scope, snapshot_date, size_band, MAX(follow_month) AS follow_month,
    MAX(CASE WHEN comparison_group = 'exposed' THEN initial_roster_n END) AS exposed_initial_n,
    MAX(CASE WHEN comparison_group = 'reference_standardized' THEN initial_roster_n END) AS reference_initial_n,
    MAX(CASE WHEN comparison_group = 'reference_standardized' THEN at_risk_n END) AS reference_at_risk_n
  FROM scoped_strata
  GROUP BY 1, 2, 3
),
qualified_strata AS (
  SELECT scope, snapshot_date, size_band, follow_month, exposed_initial_n
  FROM stratum_pivot
  WHERE reference_initial_n >= 30 AND reference_at_risk_n >= 30
),
stratum_weights AS (
  SELECT scope, snapshot_date, size_band, follow_month,
    exposed_initial_n::DECIMAL(18,10) / SUM(exposed_initial_n) OVER (PARTITION BY scope) AS exposed_weight
  FROM qualified_strata
),
interval_output AS (
  SELECT s.scope, s.comparison_group, s.follow_month,
    ROUND(100.0 * SUM(w.exposed_weight * s.voluntary_events_in_interval::DECIMAL(18,10)
      / NULLIF(s.at_risk_n, 0)), 6) AS standardized_hazard_percent,
    SUM(s.initial_roster_n) AS initial_roster_n,
    SUM(s.at_risk_n) AS at_risk_n,
    SUM(s.voluntary_events_in_interval) AS voluntary_events_in_interval,
    SUM(s.censored_in_interval) AS censored_in_interval,
    COUNT(*) AS included_strata
  FROM scoped_strata AS s
  INNER JOIN stratum_weights AS w ON w.scope = s.scope AND w.snapshot_date = s.snapshot_date
    AND w.size_band = s.size_band AND w.follow_month = s.follow_month
  GROUP BY 1, 2, 3
  HAVING SUM(s.at_risk_n) >= 30
),
scope_audit AS (
  SELECT x.scope, 'candidate_strata' AS metric, COUNT(*)::DECIMAL(18,4) AS metric_value
  FROM (SELECT 'all_teams' AS scope, snapshot_date, size_band FROM initial_strata
        UNION ALL SELECT 'teams_6_plus', snapshot_date, size_band FROM initial_strata WHERE size_band <> '1–5') AS x
  GROUP BY 1
  UNION ALL
  SELECT scope, 'included_strata', COUNT(*)::DECIMAL(18,4) FROM qualified_strata GROUP BY 1
  UNION ALL
  SELECT x.scope, 'suppressed_strata', (COUNT(*) - COALESCE(q.included_strata, 0))::DECIMAL(18,4)
  FROM (SELECT 'all_teams' AS scope, snapshot_date, size_band FROM initial_strata
        UNION ALL SELECT 'teams_6_plus', snapshot_date, size_band FROM initial_strata WHERE size_band <> '1–5') AS x
  LEFT JOIN (SELECT scope, COUNT(*) AS included_strata FROM qualified_strata GROUP BY 1) AS q ON q.scope = x.scope
  GROUP BY 1, q.included_strata
),
audit_numeric AS (
  SELECT 'calendar_complete_snapshots' AS metric, COUNT(*)::DECIMAL(18,4) AS metric_value FROM complete_calendars
  UNION ALL SELECT 'term_type_conflicts', SUM(term_type_conflict)::DECIMAL(18,4) FROM classified_termination_events
  UNION ALL SELECT 'voluntary_events_without_unique_prior_manager', COUNT(*)::DECIMAL(18,4)
    FROM termination_events_with_manager WHERE event_class = 'voluntary' AND manager_employee_id IS NULL
  UNION ALL SELECT 'index_team_window_rule_violations', COUNT(*)::DECIMAL(18,4)
    FROM index_teams AS i LEFT JOIN team_voluntary_window AS w
      ON w.snapshot_date = i.snapshot_date AND w.manager_employee_id = i.manager_employee_id
    WHERE w.six_month_voluntary_events <> 1 OR w.current_interval_voluntary_events <> 1
  UNION ALL SELECT 'series_points', COUNT(*)::DECIMAL(18,4) FROM interval_output
  UNION ALL SELECT 'series_points_under_n_30', COUNT(*)::DECIMAL(18,4) FROM interval_output WHERE at_risk_n < 30
  UNION ALL SELECT 'hazards_outside_0_100', COUNT(*)::DECIMAL(18,4)
    FROM interval_output WHERE standardized_hazard_percent < 0 OR standardized_hazard_percent > 100
)
SELECT 'interval' AS row_type, scope, comparison_group, follow_month,
  standardized_hazard_percent AS metric_percent, initial_roster_n, at_risk_n,
  voluntary_events_in_interval, censored_in_interval, included_strata,
  CAST(NULL AS VARCHAR(128)) AS metric, CAST(NULL AS DECIMAL(18,4)) AS metric_value
FROM interval_output
UNION ALL
SELECT 'audit', CAST(NULL AS VARCHAR(32)), CAST(NULL AS VARCHAR(32)), CAST(NULL AS INTEGER),
  CAST(NULL AS DECIMAL(18,6)), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), metric, metric_value
FROM audit_numeric
UNION ALL
SELECT 'scope_audit', scope, CAST(NULL AS VARCHAR(32)), CAST(NULL AS INTEGER),
  CAST(NULL AS DECIMAL(18,6)), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), metric, metric_value
FROM scope_audit
ORDER BY row_type, scope, comparison_group, follow_month, metric;
