/*
  Estudio descriptivo de salidas secuenciales de equipo.

  Propósito (presentation): comparar la incidencia acumulada retrospectiva de
  salida Voluntary entre quienes permanecen en un equipo después de una salida
  inicial única y equipos de referencia sin salida reciente. No estima un
  efecto causal, no prueba contagio y no publica personas, managers ni equipos.

  Población: worker_type='Employee', employee_type='Regular', active_status=1
  en el snapshot índice; manager_employee_id sólo se usa dentro de joins.

  Episodio índice: exactamente una salida Voluntary distinta del equipo durante
  los seis intervalos mensuales (t-6, t], y esa salida ocurre en el intervalo
  inmediatamente anterior a t. La salida se atribuye al último manager único
  observado en o antes de term_date.

  Seguimiento: seis snapshots posteriores. Se cuenta una salida Voluntary de
  un integrante del roster únicamente si el evento conserva el manager índice.
  Se censura al cambio de manager observado, a una salida no Voluntary o a una
  pérdida de observación. Las curvas son 1 - supervivencia Kaplan–Meier.

  Referencia: sin salida Voluntary en (t-6, t], mismo snapshot y banda de
  tamaño 1–5 / 6–10 / 11–20 / 21+. La referencia se estandariza con la
  distribución de snapshot × banda de tamaño de la cohorte expuesta.

  Privacidad: el resultado final es estrictamente agregado. Sólo publica
  estratos y puntos con al menos 30 integrantes inicialmente y en riesgo.
*/
WITH raw_history AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND fis_mo_end_dt IS NOT NULL
),
history_manager_by_snapshot AS (
  SELECT
    snapshot_date,
    employee_id,
    COUNT(DISTINCT manager_employee_id) AS manager_value_count,
    CASE WHEN COUNT(DISTINCT manager_employee_id) = 1
      THEN MAX(manager_employee_id) END AS manager_employee_id
  FROM raw_history
  WHERE manager_employee_id IS NOT NULL
  GROUP BY 1, 2
),
raw_active AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    manager_employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
active_employee_snapshot AS (
  SELECT
    snapshot_date,
    employee_id,
    COUNT(DISTINCT manager_employee_id) AS manager_value_count,
    CASE WHEN COUNT(DISTINCT manager_employee_id) = 1
      THEN MAX(manager_employee_id) END AS manager_employee_id
  FROM raw_active
  WHERE manager_employee_id IS NOT NULL
  GROUP BY 1, 2
),
snapshot_calendar_base AS (
  SELECT DISTINCT snapshot_date
  FROM active_employee_snapshot
),
snapshot_calendar_lag_lead AS (
  SELECT
    snapshot_date,
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
  SELECT snapshot_date, p1, p2, p3, p4, p5, p6, f1, f2, f3, f4, f5, f6
  FROM snapshot_calendar_lag_lead
  CROSS JOIN (
    SELECT MAX(snapshot_date) AS latest_snapshot_date
    FROM snapshot_calendar_base
  ) AS bounds
  WHERE p6 IS NOT NULL
    AND f6 IS NOT NULL
    AND snapshot_date >= DATEADD(month, -29, bounds.latest_snapshot_date)
    AND DATEDIFF(day, p6, p5) BETWEEN 20 AND 45
    AND DATEDIFF(day, p5, p4) BETWEEN 20 AND 45
    AND DATEDIFF(day, p4, p3) BETWEEN 20 AND 45
    AND DATEDIFF(day, p3, p2) BETWEEN 20 AND 45
    AND DATEDIFF(day, p2, p1) BETWEEN 20 AND 45
    AND DATEDIFF(day, p1, snapshot_date) BETWEEN 20 AND 45
    AND DATEDIFF(day, snapshot_date, f1) BETWEEN 20 AND 45
    AND DATEDIFF(day, f1, f2) BETWEEN 20 AND 45
    AND DATEDIFF(day, f2, f3) BETWEEN 20 AND 45
    AND DATEDIFF(day, f3, f4) BETWEEN 20 AND 45
    AND DATEDIFF(day, f4, f5) BETWEEN 20 AND 45
    AND DATEDIFF(day, f5, f6) BETWEEN 20 AND 45
),
termination_raw AS (
  SELECT
    employee_id,
    CAST(term_date AS DATE) AS term_date,
    UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) AS normalized_term_type
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND term_date IS NOT NULL
),
termination_events AS (
  SELECT
    employee_id,
    term_date,
    MAX(CASE WHEN normalized_term_type = 'VOLUNTARY' THEN 1 ELSE 0 END) AS has_voluntary_type,
    MAX(CASE WHEN normalized_term_type IS NOT NULL
                  AND normalized_term_type <> 'VOLUNTARY' THEN 1 ELSE 0 END) AS has_nonvoluntary_type,
    COUNT(DISTINCT normalized_term_type) AS nonnull_term_type_count
  FROM termination_raw
  GROUP BY 1, 2
),
classified_termination_events AS (
  SELECT
    employee_id,
    term_date,
    CASE
      WHEN has_voluntary_type = 1 AND has_nonvoluntary_type = 0 THEN 'voluntary'
      WHEN has_voluntary_type = 0 AND has_nonvoluntary_type = 1 THEN 'nonvoluntary'
      ELSE 'ambiguous_or_unknown'
    END AS event_class,
    CASE WHEN has_voluntary_type = 1 AND has_nonvoluntary_type = 1 THEN 1 ELSE 0 END AS term_type_conflict
  FROM termination_events
),
event_manager_candidates AS (
  SELECT
    e.employee_id,
    e.term_date,
    e.event_class,
    e.term_type_conflict,
    h.manager_employee_id,
    ROW_NUMBER() OVER (
      PARTITION BY e.employee_id, e.term_date
      ORDER BY h.snapshot_date DESC
    ) AS manager_rank
  FROM classified_termination_events AS e
  LEFT JOIN history_manager_by_snapshot AS h
    ON h.employee_id = e.employee_id
   AND h.snapshot_date <= e.term_date
),
termination_events_with_manager AS (
  SELECT
    employee_id,
    term_date,
    event_class,
    term_type_conflict,
    manager_employee_id
  FROM event_manager_candidates
  WHERE manager_rank = 1
),
voluntary_events AS (
  SELECT employee_id, term_date, manager_employee_id
  FROM termination_events_with_manager
  WHERE event_class = 'voluntary'
    AND manager_employee_id IS NOT NULL
),
nonvoluntary_events AS (
  SELECT employee_id, term_date
  FROM termination_events_with_manager
  WHERE event_class = 'nonvoluntary'
),
team_snapshot_sizes AS (
  SELECT
    snapshot_date,
    manager_employee_id,
    COUNT(*) AS team_size,
    CASE
      WHEN COUNT(*) BETWEEN 1 AND 5 THEN '1–5'
      WHEN COUNT(*) BETWEEN 6 AND 10 THEN '6–10'
      WHEN COUNT(*) BETWEEN 11 AND 20 THEN '11–20'
      ELSE '21+'
    END AS size_band
  FROM active_employee_snapshot
  WHERE manager_employee_id IS NOT NULL
  GROUP BY 1, 2
),
team_voluntary_window AS (
  SELECT
    c.snapshot_date,
    v.manager_employee_id,
    COUNT(*) AS six_month_voluntary_events,
    SUM(CASE WHEN v.term_date > c.p1 THEN 1 ELSE 0 END) AS current_interval_voluntary_events
  FROM complete_calendars AS c
  INNER JOIN voluntary_events AS v
    ON v.term_date > c.p6
   AND v.term_date <= c.snapshot_date
  GROUP BY 1, 2
),
index_teams AS (
  SELECT
    c.snapshot_date,
    s.manager_employee_id,
    s.team_size,
    s.size_band
  FROM complete_calendars AS c
  INNER JOIN team_snapshot_sizes AS s
    ON s.snapshot_date = c.snapshot_date
  INNER JOIN team_voluntary_window AS w
    ON w.snapshot_date = s.snapshot_date
   AND w.manager_employee_id = s.manager_employee_id
  WHERE w.six_month_voluntary_events = 1
    AND w.current_interval_voluntary_events = 1
),
control_teams AS (
  SELECT
    c.snapshot_date,
    s.manager_employee_id,
    s.team_size,
    s.size_band
  FROM complete_calendars AS c
  INNER JOIN team_snapshot_sizes AS s
    ON s.snapshot_date = c.snapshot_date
  LEFT JOIN team_voluntary_window AS w
    ON w.snapshot_date = s.snapshot_date
   AND w.manager_employee_id = s.manager_employee_id
  WHERE COALESCE(w.six_month_voluntary_events, 0) = 0
),
index_team_scopes AS (
  SELECT 'all_teams' AS scope, snapshot_date, manager_employee_id, team_size, size_band
  FROM index_teams
  UNION ALL
  SELECT 'teams_6_plus', snapshot_date, manager_employee_id, team_size, size_band
  FROM index_teams
  WHERE team_size >= 6
),
control_team_scopes AS (
  SELECT 'all_teams' AS scope, snapshot_date, manager_employee_id, team_size, size_band
  FROM control_teams
  UNION ALL
  SELECT 'teams_6_plus', snapshot_date, manager_employee_id, team_size, size_band
  FROM control_teams
  WHERE team_size >= 6
),
exposed_roster_raw AS (
  SELECT
    x.scope,
    'exposed' AS comparison_group,
    x.snapshot_date,
    x.manager_employee_id,
    x.size_band,
    a.employee_id
  FROM index_team_scopes AS x
  INNER JOIN active_employee_snapshot AS a
    ON a.snapshot_date = x.snapshot_date
   AND a.manager_employee_id = x.manager_employee_id
),
reference_roster_raw AS (
  SELECT
    x.scope,
    'reference_standardized' AS comparison_group,
    x.snapshot_date,
    x.manager_employee_id,
    x.size_band,
    a.employee_id
  FROM control_team_scopes AS x
  INNER JOIN active_employee_snapshot AS a
    ON a.snapshot_date = x.snapshot_date
   AND a.manager_employee_id = x.manager_employee_id
),
initial_stratum_counts AS (
  SELECT
    scope,
    snapshot_date,
    size_band,
    SUM(CASE WHEN comparison_group = 'exposed' THEN 1 ELSE 0 END) AS exposed_initial_n,
    SUM(CASE WHEN comparison_group = 'reference_standardized' THEN 1 ELSE 0 END) AS reference_initial_n
  FROM (
    SELECT scope, comparison_group, snapshot_date, manager_employee_id, size_band, employee_id
    FROM exposed_roster_raw
    UNION ALL
    SELECT scope, comparison_group, snapshot_date, manager_employee_id, size_band, employee_id
    FROM reference_roster_raw
  ) AS combined
  GROUP BY 1, 2, 3
),
initial_publicable_strata AS (
  SELECT scope, snapshot_date, size_band
  FROM initial_stratum_counts
  WHERE reference_initial_n >= 30
),
roster AS (
  SELECT r.scope, r.comparison_group, r.snapshot_date, r.manager_employee_id,
    r.size_band, r.employee_id
  FROM (
    SELECT scope, comparison_group, snapshot_date, manager_employee_id, size_band, employee_id
    FROM exposed_roster_raw
    UNION ALL
    SELECT scope, comparison_group, snapshot_date, manager_employee_id, size_band, employee_id
    FROM reference_roster_raw
  ) AS r
  INNER JOIN initial_publicable_strata AS p
    ON p.scope = r.scope
   AND p.snapshot_date = r.snapshot_date
   AND p.size_band = r.size_band
),
follow_steps AS (
  SELECT snapshot_date, 1 AS follow_month, snapshot_date AS interval_start, f1 AS interval_end FROM complete_calendars
  UNION ALL SELECT snapshot_date, 2, f1, f2 FROM complete_calendars
  UNION ALL SELECT snapshot_date, 3, f2, f3 FROM complete_calendars
  UNION ALL SELECT snapshot_date, 4, f3, f4 FROM complete_calendars
  UNION ALL SELECT snapshot_date, 5, f4, f5 FROM complete_calendars
  UNION ALL SELECT snapshot_date, 6, f5, f6 FROM complete_calendars
),
follow_status AS (
  SELECT
    r.scope,
    r.comparison_group,
    r.snapshot_date,
    r.manager_employee_id,
    r.size_band,
    r.employee_id,
    f.follow_month,
    MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_event_with_index_manager,
    MAX(CASE WHEN n.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS nonvoluntary_event,
    MAX(CASE WHEN a.employee_id IS NOT NULL
                  AND a.manager_employee_id = r.manager_employee_id THEN 1 ELSE 0 END) AS retained_index_manager_at_end
  FROM roster AS r
  INNER JOIN follow_steps AS f
    ON f.snapshot_date = r.snapshot_date
  LEFT JOIN voluntary_events AS v
    ON v.employee_id = r.employee_id
   AND v.manager_employee_id = r.manager_employee_id
   AND v.term_date > f.interval_start
   AND v.term_date <= f.interval_end
  LEFT JOIN nonvoluntary_events AS n
    ON n.employee_id = r.employee_id
   AND n.term_date > f.interval_start
   AND n.term_date <= f.interval_end
  LEFT JOIN active_employee_snapshot AS a
    ON a.employee_id = r.employee_id
   AND a.snapshot_date = f.interval_end
  GROUP BY 1, 2, 3, 4, 5, 6, 7
),
roster_event_censor AS (
  SELECT
    scope,
    comparison_group,
    snapshot_date,
    manager_employee_id,
    size_band,
    employee_id,
    MIN(CASE WHEN voluntary_event_with_index_manager = 1 THEN follow_month END) AS event_month,
    MIN(CASE
      WHEN voluntary_event_with_index_manager = 0
       AND (nonvoluntary_event = 1 OR retained_index_manager_at_end = 0)
      THEN follow_month END) AS censor_month
  FROM follow_status
  GROUP BY 1, 2, 3, 4, 5, 6
),
stratum_interval_metrics AS (
  SELECT
    r.scope,
    r.comparison_group,
    r.snapshot_date,
    r.size_band,
    f.follow_month,
    COUNT(*) AS initial_roster_n,
    SUM(CASE
      WHEN (r.event_month IS NULL OR r.event_month >= f.follow_month)
       AND (r.censor_month IS NULL OR r.censor_month >= f.follow_month)
      THEN 1 ELSE 0 END) AS at_risk_n,
    SUM(CASE
      WHEN r.event_month = f.follow_month
       AND (r.censor_month IS NULL OR r.event_month <= r.censor_month)
      THEN 1 ELSE 0 END) AS voluntary_events_in_interval,
    SUM(CASE
      WHEN r.censor_month = f.follow_month
       AND (r.event_month IS NULL OR r.event_month <> r.censor_month)
      THEN 1 ELSE 0 END) AS censored_in_interval
  FROM roster_event_censor AS r
  INNER JOIN follow_steps AS f
    ON f.snapshot_date = r.snapshot_date
  GROUP BY 1, 2, 3, 4, 5
),
stratum_curves AS (
  SELECT
    scope,
    comparison_group,
    snapshot_date,
    size_band,
    follow_month,
    initial_roster_n,
    at_risk_n,
    voluntary_events_in_interval,
    censored_in_interval,
    CASE
      WHEN SUM(CASE
        WHEN at_risk_n > 0 AND voluntary_events_in_interval >= at_risk_n THEN 1
        ELSE 0 END) OVER (
          PARTITION BY scope, comparison_group, snapshot_date, size_band
          ORDER BY follow_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) > 0 THEN 100.0
      ELSE 100.0 * (1.0 - EXP(SUM(
        LN(CASE
          WHEN at_risk_n > 0
            THEN GREATEST((at_risk_n - voluntary_events_in_interval)::DECIMAL(18,10)
                           / at_risk_n::DECIMAL(18,10), 0.0000000001)
          ELSE 1.0
        END)
      ) OVER (
        PARTITION BY scope, comparison_group, snapshot_date, size_band
        ORDER BY follow_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      )))
    END AS cumulative_incidence_percent
  FROM stratum_interval_metrics
),
risk_publicable_strata AS (
  SELECT scope, snapshot_date, size_band
  FROM stratum_curves
  GROUP BY 1, 2, 3
  HAVING MIN(CASE WHEN comparison_group = 'reference_standardized' THEN at_risk_n END) >= 30
     AND COUNT(DISTINCT comparison_group) = 2
),
publication_strata AS (
  SELECT p.scope, p.snapshot_date, p.size_band
  FROM initial_publicable_strata AS p
  INNER JOIN risk_publicable_strata AS r
    ON r.scope = p.scope
   AND r.snapshot_date = p.snapshot_date
   AND r.size_band = p.size_band
),
stratum_weights AS (
  SELECT
    c.scope,
    c.snapshot_date,
    c.size_band,
    c.initial_roster_n::DECIMAL(18,10)
      / SUM(c.initial_roster_n) OVER (PARTITION BY c.scope) AS exposed_weight
  FROM stratum_curves AS c
  INNER JOIN publication_strata AS p
    ON p.scope = c.scope
   AND p.snapshot_date = c.snapshot_date
   AND p.size_band = c.size_band
  WHERE c.comparison_group = 'exposed'
    AND c.follow_month = 1
),
series_output AS (
  SELECT
    c.scope,
    c.comparison_group,
    c.follow_month,
    ROUND(SUM(c.cumulative_incidence_percent * w.exposed_weight), 4) AS cumulative_incidence_percent,
    SUM(c.initial_roster_n) AS initial_roster_n,
    SUM(c.at_risk_n) AS at_risk_n,
    SUM(c.voluntary_events_in_interval) AS voluntary_events_in_interval,
    SUM(c.censored_in_interval) AS censored_in_interval,
    COUNT(DISTINCT c.snapshot_date || '|' || c.size_band) AS included_strata,
    MIN(c.at_risk_n) AS minimum_stratum_at_risk_n
  FROM stratum_curves AS c
  INNER JOIN stratum_weights AS w
    ON w.scope = c.scope
   AND w.snapshot_date = c.snapshot_date
   AND w.size_band = c.size_band
  GROUP BY 1, 2, 3
),
episode_counts AS (
  SELECT scope, COUNT(*) AS index_team_episodes
  FROM index_team_scopes
  GROUP BY 1
),
control_episode_counts AS (
  SELECT scope, COUNT(*) AS reference_team_episodes
  FROM control_team_scopes
  GROUP BY 1
),
suppression_counts AS (
  SELECT
    checked.scope,
    COUNT(*) AS candidate_strata,
    SUM(CASE WHEN checked.initial_ok = 0 THEN 1 ELSE 0 END) AS initial_suppressed_strata,
    SUM(CASE WHEN checked.initial_ok = 1 AND checked.risk_ok = 0 THEN 1 ELSE 0 END) AS risk_suppressed_strata,
    SUM(CASE WHEN checked.initial_ok = 1 AND checked.risk_ok = 1 THEN 1 ELSE 0 END) AS published_strata
  FROM (
    SELECT
      candidate.scope,
      candidate.snapshot_date,
      candidate.size_band,
      CASE WHEN initial_check.scope IS NOT NULL THEN 1 ELSE 0 END AS initial_ok,
      CASE WHEN risk_check.scope IS NOT NULL THEN 1 ELSE 0 END AS risk_ok
    FROM (
      SELECT scope, snapshot_date, size_band FROM initial_stratum_counts
    ) AS candidate
    LEFT JOIN initial_publicable_strata AS initial_check
      ON initial_check.scope = candidate.scope
     AND initial_check.snapshot_date = candidate.snapshot_date
     AND initial_check.size_band = candidate.size_band
    LEFT JOIN risk_publicable_strata AS risk_check
      ON risk_check.scope = candidate.scope
     AND risk_check.snapshot_date = candidate.snapshot_date
     AND risk_check.size_band = candidate.size_band
  ) AS checked
  GROUP BY 1
),
audit_numeric AS (
  SELECT 'calendar_complete_snapshots' AS metric, COUNT(*)::DECIMAL(18,4) AS metric_value FROM complete_calendars
  UNION ALL SELECT 'active_employee_snapshot_manager_conflicts', COUNT(*)::DECIMAL(18,4) FROM active_employee_snapshot WHERE manager_value_count > 1
  UNION ALL SELECT 'history_manager_snapshot_conflicts', COUNT(*)::DECIMAL(18,4) FROM history_manager_by_snapshot WHERE manager_value_count > 1
  UNION ALL SELECT 'term_type_conflicts', SUM(term_type_conflict)::DECIMAL(18,4) FROM classified_termination_events
  UNION ALL SELECT 'voluntary_events_without_unique_prior_manager', COUNT(*)::DECIMAL(18,4)
    FROM termination_events_with_manager WHERE event_class = 'voluntary' AND manager_employee_id IS NULL
  UNION ALL SELECT 'index_team_window_rule_violations', COUNT(*)::DECIMAL(18,4)
    FROM index_teams AS i LEFT JOIN team_voluntary_window AS w
      ON w.snapshot_date = i.snapshot_date AND w.manager_employee_id = i.manager_employee_id
    WHERE w.six_month_voluntary_events <> 1 OR w.current_interval_voluntary_events <> 1
  UNION ALL SELECT 'series_points', COUNT(*)::DECIMAL(18,4) FROM series_output
  UNION ALL SELECT 'series_points_outside_0_100', COUNT(*)::DECIMAL(18,4)
    FROM series_output WHERE cumulative_incidence_percent < 0 OR cumulative_incidence_percent > 100
  UNION ALL SELECT 'series_points_under_minimum_risk_n', COUNT(*)::DECIMAL(18,4)
    FROM series_output WHERE at_risk_n < 30
),
scope_audit AS (
  SELECT scope, 'index_team_episodes' AS metric, index_team_episodes::DECIMAL(18,4) AS metric_value FROM episode_counts
  UNION ALL SELECT scope, 'reference_team_episodes', reference_team_episodes::DECIMAL(18,4) FROM control_episode_counts
  UNION ALL SELECT scope, 'candidate_strata', candidate_strata::DECIMAL(18,4) FROM suppression_counts
  UNION ALL SELECT scope, 'initial_suppressed_strata', initial_suppressed_strata::DECIMAL(18,4) FROM suppression_counts
  UNION ALL SELECT scope, 'risk_suppressed_strata', risk_suppressed_strata::DECIMAL(18,4) FROM suppression_counts
  UNION ALL SELECT scope, 'published_strata', published_strata::DECIMAL(18,4) FROM suppression_counts
)
SELECT
  'series' AS row_type,
  scope,
  comparison_group,
  follow_month,
  cumulative_incidence_percent,
  initial_roster_n,
  at_risk_n,
  voluntary_events_in_interval,
  censored_in_interval,
  included_strata,
  minimum_stratum_at_risk_n,
  CAST(NULL AS VARCHAR(128)) AS metric,
  CAST(NULL AS DECIMAL(18,4)) AS metric_value
FROM series_output
UNION ALL
SELECT
  'audit',
  CAST(NULL AS VARCHAR(32)),
  CAST(NULL AS VARCHAR(32)),
  CAST(NULL AS INTEGER),
  CAST(NULL AS DECIMAL(18,4)),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  metric,
  metric_value
FROM audit_numeric
UNION ALL
SELECT
  'scope_audit',
  scope,
  CAST(NULL AS VARCHAR(32)),
  CAST(NULL AS INTEGER),
  CAST(NULL AS DECIMAL(18,4)),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  CAST(NULL AS BIGINT),
  metric,
  metric_value
FROM scope_audit
ORDER BY row_type, scope, comparison_group, follow_month, metric;
