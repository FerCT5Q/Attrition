-- Auditoría agregada de sensibilidad del umbral de Above-average team turnover.
--
-- Deliverable mode: presentation. No se publican IDs, nombres, tasas de
-- managers ni rankings. La distribución se resume con percentiles agregados;
-- los conteos se publican sólo cuando cumplen n >= 30.
--
-- Se conserva exactamente la derivación v4: 18 intervalos cerrados,
-- manager al inicio del intervalo, term_type exactamente Voluntary,
-- exposición de empleados regulares activos con manager y elegibilidad
-- promedio de equipo >=4 y >=2 salidas. Se comparan 1.2x, 1.3x y 1.4x.
--
-- Significancia operativa (no inferencia causal): límite inferior unilateral
-- aproximado de 95% para una proporción binomial de salidas por employee-month,
-- expresado a seis meses, comparado con el benchmark del mismo snapshot. Es
-- una aproximación conservadora para screening; no corrige dependencia entre
-- meses ni la incertidumbre de estimar el benchmark.
WITH closure_dates AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  GROUP BY 1
), closure_sequence AS (
  SELECT snapshot_date,
    ROW_NUMBER() OVER (ORDER BY snapshot_date) AS closure_sequence
  FROM closure_dates
), bounds AS (
  SELECT MAX(closure_sequence) AS max_sequence
  FROM closure_sequence
), evaluation_snapshots AS (
  SELECT c.snapshot_date, c.closure_sequence
  FROM closure_sequence AS c
  CROSS JOIN bounds AS b
  WHERE c.closure_sequence > 18
    AND c.closure_sequence >= b.max_sequence - 5
), scope_bounds AS (
  SELECT MIN(closure_sequence) - 18 AS first_required_sequence,
    MAX(closure_sequence) AS last_required_sequence
  FROM evaluation_snapshots
), base_exposure_raw AS (
  SELECT c.snapshot_date, c.closure_sequence, w.employee_id,
    w.manager_employee_id
  FROM closure_sequence AS c
  CROSS JOIN scope_bounds AS b
  INNER JOIN hrda.post_hire_monthly_worker_dtls AS w
    ON CAST(w.fis_mo_end_dt AS DATE) = c.snapshot_date
  WHERE c.closure_sequence BETWEEN b.first_required_sequence
                              AND b.last_required_sequence
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.manager_employee_id IS NOT NULL
), base_exposure AS (
  SELECT snapshot_date, closure_sequence, employee_id, manager_employee_id
  FROM (
    SELECT b.snapshot_date, b.closure_sequence, b.employee_id,
      b.manager_employee_id,
      ROW_NUMBER() OVER (
        PARTITION BY b.closure_sequence, b.employee_id
        ORDER BY b.manager_employee_id
      ) AS row_rank
    FROM base_exposure_raw AS b
  ) AS deduplicated
  WHERE row_rank = 1
), intervals AS (
  SELECT s.closure_sequence AS interval_start_sequence,
    s.snapshot_date AS interval_start,
    n.snapshot_date AS interval_end
  FROM closure_sequence AS s
  CROSS JOIN scope_bounds AS b
  INNER JOIN closure_sequence AS n
    ON n.closure_sequence = s.closure_sequence + 1
  WHERE s.closure_sequence BETWEEN b.first_required_sequence
                              AND b.last_required_sequence - 1
), voluntary_events AS (
  SELECT w.employee_id, CAST(w.term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN scope_bounds AS b
  INNER JOIN closure_sequence AS first_closure
    ON first_closure.closure_sequence = b.first_required_sequence
  INNER JOIN closure_sequence AS last_closure
    ON last_closure.closure_sequence = b.last_required_sequence
  WHERE CAST(w.term_date AS DATE) > first_closure.snapshot_date
    AND CAST(w.term_date AS DATE) <= last_closure.snapshot_date
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
  GROUP BY 1, 2
), event_attribution AS (
  SELECT i.interval_start_sequence, x.manager_employee_id,
    v.employee_id, v.term_date
  FROM intervals AS i
  INNER JOIN voluntary_events AS v
    ON v.term_date > i.interval_start
   AND v.term_date <= i.interval_end
  INNER JOIN base_exposure AS x
    ON x.closure_sequence = i.interval_start_sequence
   AND x.employee_id = v.employee_id
), manager_interval AS (
  SELECT x.closure_sequence, x.manager_employee_id,
    COUNT(*)::BIGINT AS team_size,
    COALESCE(e.voluntary_exit_count, 0)::BIGINT AS voluntary_exit_count
  FROM base_exposure AS x
  LEFT JOIN (
    SELECT interval_start_sequence, manager_employee_id,
      COUNT(*)::BIGINT AS voluntary_exit_count
    FROM event_attribution
    GROUP BY 1, 2
  ) AS e
    ON e.interval_start_sequence = x.closure_sequence
   AND e.manager_employee_id = x.manager_employee_id
  GROUP BY 1, 2, 4
), manager_rolling AS (
  SELECT m.closure_sequence, m.manager_employee_id,
    COUNT(*) OVER (
      PARTITION BY m.manager_employee_id
      ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    )::BIGINT AS observed_interval_count,
    MIN(m.closure_sequence) OVER (
      PARTITION BY m.manager_employee_id
      ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    )::BIGINT AS first_history_sequence,
    MAX(m.closure_sequence) OVER (
      PARTITION BY m.manager_employee_id
      ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    )::BIGINT AS last_history_sequence,
    SUM(m.team_size) OVER (
      PARTITION BY m.manager_employee_id
      ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    )::BIGINT AS historical_exposure,
    AVG(m.team_size::DECIMAL(20,6)) OVER (
      PARTITION BY m.manager_employee_id
      ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    ) AS average_team_size,
    SUM(m.voluntary_exit_count) OVER (
      PARTITION BY m.manager_employee_id
      ORDER BY m.closure_sequence
      ROWS BETWEEN 18 PRECEDING AND 1 PRECEDING
    )::BIGINT AS voluntary_exit_count
  FROM manager_interval AS m
), manager_context AS (
  SELECT e.snapshot_date AS evaluation_date, e.closure_sequence,
    r.manager_employee_id, r.observed_interval_count,
    r.first_history_sequence, r.last_history_sequence,
    r.historical_exposure, r.average_team_size,
    r.voluntary_exit_count,
    CASE WHEN r.observed_interval_count = 18
           AND r.last_history_sequence - r.first_history_sequence = 17
           AND r.average_team_size >= 4
           AND r.voluntary_exit_count >= 2
           AND r.historical_exposure > 0
         THEN 1 ELSE 0 END AS manager_eligible,
    CASE WHEN r.historical_exposure > 0
         THEN r.voluntary_exit_count::DECIMAL(30,12)
              / r.historical_exposure * 6 END AS six_month_rate
  FROM evaluation_snapshots AS e
  INNER JOIN manager_rolling AS r
    ON r.closure_sequence = e.closure_sequence
), benchmarks AS (
  SELECT closure_sequence,
    SUM(voluntary_exit_count)::DECIMAL(30,12)
      / NULLIF(SUM(historical_exposure), 0) * 6
      AS weighted_benchmark_six_month_rate
  FROM manager_context
  WHERE manager_eligible = 1
  GROUP BY 1
), current_report_counts AS (
  SELECT e.closure_sequence, x.manager_employee_id,
    COUNT(*)::BIGINT AS current_report_count
  FROM evaluation_snapshots AS e
  INNER JOIN base_exposure AS x
    ON x.closure_sequence = e.closure_sequence
  GROUP BY 1, 2
), manager_scored AS (
  SELECT c.evaluation_date, c.closure_sequence,
    c.manager_employee_id, c.historical_exposure,
    c.voluntary_exit_count, c.manager_eligible, c.six_month_rate,
    b.weighted_benchmark_six_month_rate,
    COALESCE(r.current_report_count, 0)::BIGINT AS current_report_count,
    CASE WHEN c.manager_eligible = 1
           AND b.weighted_benchmark_six_month_rate > 0
         THEN c.six_month_rate / b.weighted_benchmark_six_month_rate
    END AS rate_ratio,
    -- One-sided 95% Wilson lower bound for the monthly exit proportion,
    -- converted to an equivalent six-month rate. z=1.6448536269.
    CASE WHEN c.manager_eligible = 1 AND c.historical_exposure > 0 THEN
      6 * (
        (
          (c.voluntary_exit_count::DECIMAL(30,12)
             / c.historical_exposure)
          + (1.64485362695147 * 1.64485362695147)
             / (2 * c.historical_exposure)
          - 1.64485362695147 * SQRT(
              GREATEST(
                (
                  (c.voluntary_exit_count::DECIMAL(30,12)
                     / c.historical_exposure)
                  * (1 - c.voluntary_exit_count::DECIMAL(30,12)
                       / c.historical_exposure)
                  / c.historical_exposure
                )
                + (1.64485362695147 * 1.64485362695147)
                  / (4 * c.historical_exposure * c.historical_exposure),
                0
              )
            )
        )
        / (
          1 + (1.64485362695147 * 1.64485362695147)
                / c.historical_exposure
        )
      )
    END AS lower95_six_month_rate
  FROM manager_context AS c
  LEFT JOIN benchmarks AS b
    ON b.closure_sequence = c.closure_sequence
  LEFT JOIN current_report_counts AS r
    ON r.closure_sequence = c.closure_sequence
   AND r.manager_employee_id = c.manager_employee_id
), thresholds AS (
  SELECT 1.2::DECIMAL(4,2) AS threshold_multiplier
  UNION ALL SELECT 1.3::DECIMAL(4,2)
  UNION ALL SELECT 1.4::DECIMAL(4,2)
), threshold_snapshot AS (
  SELECT m.evaluation_date AS snapshot_date,
    t.threshold_multiplier,
    COUNT(CASE WHEN m.manager_eligible = 1 THEN 1 END)::BIGINT
      AS eligible_manager_count_raw,
    SUM(CASE WHEN m.manager_eligible = 1 THEN m.current_report_count ELSE 0 END)::BIGINT
      AS eligible_report_count_raw,
    SUM(CASE WHEN m.manager_eligible = 1
                  AND m.rate_ratio >= t.threshold_multiplier
             THEN 1 ELSE 0 END)::BIGINT AS flagged_manager_count_raw,
    SUM(CASE WHEN m.manager_eligible = 1
                  AND m.rate_ratio >= t.threshold_multiplier
             THEN m.current_report_count ELSE 0 END)::BIGINT
      AS flagged_report_count_raw,
    SUM(CASE WHEN m.manager_eligible = 1
                  AND m.lower95_six_month_rate
                        > m.weighted_benchmark_six_month_rate
             THEN 1 ELSE 0 END)::BIGINT AS significant_manager_count_raw,
    SUM(CASE WHEN m.manager_eligible = 1
                  AND m.lower95_six_month_rate
                        > m.weighted_benchmark_six_month_rate
             THEN m.current_report_count ELSE 0 END)::BIGINT
      AS significant_report_count_raw,
    SUM(CASE WHEN m.manager_eligible = 1
                  AND m.rate_ratio >= t.threshold_multiplier
                  AND m.lower95_six_month_rate
                        > m.weighted_benchmark_six_month_rate
             THEN 1 ELSE 0 END)::BIGINT
      AS flagged_and_significant_manager_count_raw,
    SUM(CASE WHEN m.manager_eligible = 1
                  AND m.rate_ratio >= t.threshold_multiplier
                  AND m.lower95_six_month_rate
                        > m.weighted_benchmark_six_month_rate
             THEN m.current_report_count ELSE 0 END)::BIGINT
      AS flagged_and_significant_report_count_raw,
    MAX(m.weighted_benchmark_six_month_rate) AS benchmark_six_month_rate
  FROM manager_scored AS m
  CROSS JOIN thresholds AS t
  GROUP BY 1, 2
), latest_snapshot AS (
  SELECT MAX(snapshot_date) AS snapshot_date
  FROM evaluation_snapshots
), latest_rate_distribution AS (
  SELECT m.evaluation_date AS snapshot_date,
    COUNT(*)::BIGINT AS eligible_manager_count_raw,
    MAX(m.weighted_benchmark_six_month_rate) AS benchmark_six_month_rate,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY m.rate_ratio)
      AS ratio_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY m.rate_ratio)
      AS ratio_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY m.rate_ratio)
      AS ratio_p75,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY m.rate_ratio)
      AS ratio_p90,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.rate_ratio)
      AS ratio_p95
  FROM manager_scored AS m
  INNER JOIN latest_snapshot AS l
    ON l.snapshot_date = m.evaluation_date
  WHERE m.manager_eligible = 1
  GROUP BY 1
), threshold_stability AS (
  SELECT threshold_multiplier,
    COUNT(*)::BIGINT AS snapshots_checked,
    AVG(flagged_report_count_raw::DECIMAL(30,6)) AS avg_flagged_report_count_raw,
    MIN(flagged_report_count_raw)::BIGINT AS min_flagged_report_count_raw,
    MAX(flagged_report_count_raw)::BIGINT AS max_flagged_report_count_raw,
    AVG(
      CASE WHEN eligible_report_count_raw > 0
           THEN flagged_report_count_raw::DECIMAL(30,12)
                / eligible_report_count_raw * 100
      END
    ) AS avg_flagged_report_share_percent,
    MIN(
      CASE WHEN eligible_report_count_raw > 0
           THEN flagged_report_count_raw::DECIMAL(30,12)
                / eligible_report_count_raw * 100
      END
    ) AS min_flagged_report_share_percent,
    MAX(
      CASE WHEN eligible_report_count_raw > 0
           THEN flagged_report_count_raw::DECIMAL(30,12)
                / eligible_report_count_raw * 100
      END
    ) AS max_flagged_report_share_percent,
    SUM(CASE WHEN flagged_report_count_raw >= 30 THEN 1 ELSE 0 END)::BIGINT
      AS snapshots_with_reportable_flagged_count
  FROM threshold_snapshot
  GROUP BY 1
), published AS (
  SELECT 'rate_distribution'::VARCHAR(32) AS row_type,
    d.snapshot_date, NULL::DECIMAL(4,2) AS threshold_multiplier,
    CASE WHEN d.eligible_manager_count_raw >= 30
         THEN d.eligible_manager_count_raw END::BIGINT
      AS eligible_manager_count,
    NULL::BIGINT AS eligible_report_count,
    NULL::BIGINT AS flagged_manager_count,
    NULL::BIGINT AS flagged_report_count,
    NULL::BIGINT AS significant_manager_count,
    NULL::BIGINT AS significant_report_count,
    NULL::BIGINT AS flagged_and_significant_manager_count,
    NULL::BIGINT AS flagged_and_significant_report_count,
    d.benchmark_six_month_rate,
    d.ratio_p25, d.ratio_p50, d.ratio_p75, d.ratio_p90, d.ratio_p95,
    NULL::DECIMAL(30,12) AS avg_flagged_report_share_percent,
    NULL::DECIMAL(30,12) AS min_flagged_report_share_percent,
    NULL::DECIMAL(30,12) AS max_flagged_report_share_percent,
    NULL::DECIMAL(30,12) AS avg_flagged_report_count,
    NULL::BIGINT AS min_flagged_report_count,
    NULL::BIGINT AS max_flagged_report_count,
    NULL::BIGINT AS snapshots_checked,
    NULL::BIGINT AS snapshots_with_reportable_flagged_count,
    'Percentiles de la tasa del manager / benchmark entre managers elegibles. No son tasas individuales.'::VARCHAR(256)
      AS interpretation
  FROM latest_rate_distribution AS d
  UNION ALL
  SELECT 'threshold_snapshot'::VARCHAR(32),
    s.snapshot_date, s.threshold_multiplier,
    CASE WHEN s.eligible_manager_count_raw >= 30
         THEN s.eligible_manager_count_raw END::BIGINT,
    CASE WHEN s.eligible_report_count_raw >= 30
         THEN s.eligible_report_count_raw END::BIGINT,
    CASE WHEN s.flagged_manager_count_raw >= 30
         THEN s.flagged_manager_count_raw END::BIGINT,
    CASE WHEN s.flagged_report_count_raw >= 30
         THEN s.flagged_report_count_raw END::BIGINT,
    CASE WHEN s.significant_manager_count_raw >= 30
         THEN s.significant_manager_count_raw END::BIGINT,
    CASE WHEN s.significant_report_count_raw >= 30
         THEN s.significant_report_count_raw END::BIGINT,
    CASE WHEN s.flagged_and_significant_manager_count_raw >= 30
         THEN s.flagged_and_significant_manager_count_raw END::BIGINT,
    CASE WHEN s.flagged_and_significant_report_count_raw >= 30
         THEN s.flagged_and_significant_report_count_raw END::BIGINT,
    s.benchmark_six_month_rate,
    NULL::DECIMAL(30,12), NULL::DECIMAL(30,12), NULL::DECIMAL(30,12),
    NULL::DECIMAL(30,12), NULL::DECIMAL(30,12),
    CASE WHEN s.eligible_report_count_raw > 0
         THEN s.flagged_report_count_raw::DECIMAL(30,12)
              / s.eligible_report_count_raw * 100 END,
    NULL::DECIMAL(30,12), NULL::DECIMAL(30,12), NULL::DECIMAL(30,12),
    NULL::BIGINT, NULL::BIGINT, NULL::BIGINT, NULL::BIGINT,
    'Conteos individuales se suprimen cuando el bucket queda debajo de n=30. La tasa de reportes usa sólo reportes con manager elegible.'::VARCHAR(256)
  FROM threshold_snapshot AS s
  UNION ALL
  SELECT 'threshold_stability'::VARCHAR(32),
    NULL::DATE, s.threshold_multiplier,
    NULL::BIGINT, NULL::BIGINT, NULL::BIGINT, NULL::BIGINT,
    NULL::BIGINT, NULL::BIGINT, NULL::BIGINT, NULL::BIGINT,
    NULL::DECIMAL(30,12),
    NULL::DECIMAL(30,12), NULL::DECIMAL(30,12), NULL::DECIMAL(30,12),
    NULL::DECIMAL(30,12), NULL::DECIMAL(30,12),
    s.avg_flagged_report_share_percent,
    CASE WHEN s.min_flagged_report_count_raw >= 30
         THEN s.min_flagged_report_share_percent END,
    CASE WHEN s.min_flagged_report_count_raw >= 30
         THEN s.max_flagged_report_share_percent END,
    CASE WHEN s.avg_flagged_report_count_raw >= 30
         THEN s.avg_flagged_report_count_raw END,
    CASE WHEN s.min_flagged_report_count_raw >= 30
         THEN s.min_flagged_report_count_raw END,
    CASE WHEN s.min_flagged_report_count_raw >= 30
         THEN s.max_flagged_report_count_raw END,
    s.snapshots_checked,
    s.snapshots_with_reportable_flagged_count,
    'Estabilidad agregada en los seis snapshots históricos. El límite inferior 95% es un screening aproximado, no una prueba causal.'::VARCHAR(256)
  FROM threshold_stability AS s
)
SELECT row_type, snapshot_date, threshold_multiplier,
  eligible_manager_count, eligible_report_count,
  flagged_manager_count, flagged_report_count,
  significant_manager_count, significant_report_count,
  flagged_and_significant_manager_count,
  flagged_and_significant_report_count,
  benchmark_six_month_rate,
  ratio_p25, ratio_p50, ratio_p75, ratio_p90, ratio_p95,
  avg_flagged_report_share_percent,
  min_flagged_report_share_percent,
  max_flagged_report_share_percent,
  avg_flagged_report_count,
  min_flagged_report_count,
  max_flagged_report_count,
  snapshots_checked,
  snapshots_with_reportable_flagged_count,
  interpretation
FROM published
ORDER BY CASE row_type
           WHEN 'rate_distribution' THEN 1
           WHEN 'threshold_snapshot' THEN 2
           ELSE 3
         END,
         snapshot_date,
         threshold_multiplier;
