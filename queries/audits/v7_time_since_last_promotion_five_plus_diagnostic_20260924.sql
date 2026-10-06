/*
  Presentation-safe aggregate diagnosis for the V7 Time since last promotion
  slide.  It tests whether the non-estimable 5+ recorded-promotion band is
  caused by the event-level RF360 filter or is inherent to the valid-event
  reconstruction at the fixed 2025-08-24 baseline.

  Acceptance rule before interpretation:
  - Compare latest valid promotion with and without the historical event-row
    RF360 filter. If removing that filter materially changes 5+ membership,
    investigate the historical RF360 rule before publishing the visual.
  - Separately quantify the safe (n>=30) 5+ no-recorded-promotion episode
    population, distinguishing the strict aligned proxy from left-censored and
    role/episode-misaligned cases.
  - Never return an exact aggregate below the presentation minimum of 30.
*/
WITH parameters AS (
    SELECT DATE '2025-08-24' AS baseline_snapshot_date
),
baseline AS (
    SELECT
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.max_hire_rehire_date AS DATE)) AS episode_start_date,
        MAX(w.time_in_role) AS time_in_role_years
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN parameters AS p
    WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_snapshot_date
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND COALESCE(w.is_rf360_yes_no, 0) = 0
      AND w.employee_id IS NOT NULL
    GROUP BY 1
),
observed_history AS (
    SELECT MIN(CAST(fis_mo_end_dt AS DATE)) AS observed_history_start_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
history AS (
    SELECT
        CAST(w.employee_id AS BIGINT) AS employee_id,
        CAST(w.fis_mo_end_dt AS DATE) AS event_snapshot_date,
        CAST(w.promotion_date AS DATE) AS promotion_date,
        w.is_promo,
        COALESCE(w.is_rf360_yes_no, 0) AS event_is_rf360
    FROM hrda.post_hire_monthly_worker_dtls AS w
    INNER JOIN baseline AS b
      ON b.employee_id = CAST(w.employee_id AS BIGINT)
    CROSS JOIN parameters AS p
    WHERE w.fis_mo_end_dt IS NOT NULL
      AND CAST(w.fis_mo_end_dt AS DATE) <= p.baseline_snapshot_date
),
valid_events AS (
    SELECT DISTINCT
        employee_id,
        promotion_date,
        event_is_rf360
    FROM history AS h
    CROSS JOIN parameters AS p
    WHERE h.is_promo = 1
      AND h.promotion_date IS NOT NULL
      AND h.promotion_date <= h.event_snapshot_date
      AND h.promotion_date <= p.baseline_snapshot_date
),
latest AS (
    SELECT
        b.employee_id,
        b.episode_start_date,
        b.time_in_role_years,
        MAX(CASE WHEN e.promotion_date >= b.episode_start_date AND e.event_is_rf360 = 0 THEN e.promotion_date END) AS latest_nonrf_event_promotion_date,
        MAX(CASE WHEN e.promotion_date >= b.episode_start_date THEN e.promotion_date END) AS latest_all_event_rows_promotion_date
    FROM baseline AS b
    LEFT JOIN valid_events AS e
      ON e.employee_id = b.employee_id
    GROUP BY 1, 2, 3
),
classified AS (
    SELECT
        l.employee_id,
        l.episode_start_date,
        l.time_in_role_years,
        l.latest_nonrf_event_promotion_date,
        l.latest_all_event_rows_promotion_date,
        CASE
            WHEN l.latest_nonrf_event_promotion_date IS NOT NULL
             AND DATEADD(year, 5, l.latest_nonrf_event_promotion_date) <= p.baseline_snapshot_date
                THEN 1 ELSE 0
        END AS recorded_five_plus_nonrf_event,
        CASE
            WHEN l.latest_all_event_rows_promotion_date IS NOT NULL
             AND DATEADD(year, 5, l.latest_all_event_rows_promotion_date) <= p.baseline_snapshot_date
                THEN 1 ELSE 0
        END AS recorded_five_plus_all_event_rows,
        CASE
            WHEN COALESCE(CAST(l.latest_nonrf_event_promotion_date AS VARCHAR(32)), '<NULL>')
               <> COALESCE(CAST(l.latest_all_event_rows_promotion_date AS VARCHAR(32)), '<NULL>')
                THEN 1 ELSE 0
        END AS latest_event_changes_when_historical_rf360_filter_is_removed,
        CASE
            WHEN l.latest_nonrf_event_promotion_date IS NULL
             AND l.episode_start_date >= h.observed_history_start_date
             AND DATEADD(year, 5, l.episode_start_date) <= p.baseline_snapshot_date
             AND l.time_in_role_years IS NOT NULL
             AND l.time_in_role_years >= 0
             AND ROUND(l.time_in_role_years, 1) = ROUND(DATEDIFF(day, l.episode_start_date, p.baseline_snapshot_date) / 365.2425, 1)
                THEN 1 ELSE 0
        END AS no_recorded_promotion_aligned_proxy_five_plus,
        CASE
            WHEN l.latest_nonrf_event_promotion_date IS NULL
             AND l.episode_start_date < h.observed_history_start_date
             AND DATEADD(year, 5, l.episode_start_date) <= p.baseline_snapshot_date
                THEN 1 ELSE 0
        END AS no_recorded_promotion_left_censored_five_plus,
        CASE
            WHEN l.latest_nonrf_event_promotion_date IS NULL
             AND l.episode_start_date >= h.observed_history_start_date
             AND DATEADD(year, 5, l.episode_start_date) <= p.baseline_snapshot_date
             AND l.time_in_role_years IS NOT NULL
             AND l.time_in_role_years >= 0
             AND ROUND(l.time_in_role_years, 1) <> ROUND(DATEDIFF(day, l.episode_start_date, p.baseline_snapshot_date) / 365.2425, 1)
                THEN 1 ELSE 0
        END AS no_recorded_promotion_role_episode_misaligned_five_plus
    FROM latest AS l
    CROSS JOIN observed_history AS h
    CROSS JOIN parameters AS p
),
metrics AS (
    SELECT 'baseline_non_rf360_count' AS metric, COUNT(*)::BIGINT AS raw_count FROM classified
    UNION ALL SELECT 'recorded_promotion_five_plus_with_event_rf360_filter', SUM(recorded_five_plus_nonrf_event)::BIGINT FROM classified
    UNION ALL SELECT 'recorded_promotion_five_plus_without_event_rf360_filter', SUM(recorded_five_plus_all_event_rows)::BIGINT FROM classified
    UNION ALL SELECT 'latest_promotion_changes_when_event_rf360_filter_removed', SUM(latest_event_changes_when_historical_rf360_filter_is_removed)::BIGINT FROM classified
    UNION ALL SELECT 'no_recorded_promotion_aligned_proxy_five_plus', SUM(no_recorded_promotion_aligned_proxy_five_plus)::BIGINT FROM classified
    UNION ALL SELECT 'no_recorded_promotion_left_censored_five_plus', SUM(no_recorded_promotion_left_censored_five_plus)::BIGINT FROM classified
    UNION ALL SELECT 'no_recorded_promotion_role_episode_misaligned_five_plus', SUM(no_recorded_promotion_role_episode_misaligned_five_plus)::BIGINT FROM classified
)
SELECT
    metric,
    CASE
        WHEN raw_count >= 30 THEN CAST(raw_count AS VARCHAR(32))
        ELSE 'below_presentation_minimum'
    END AS presentation_value,
    CASE WHEN raw_count >= 30 THEN 'publishable_aggregate' ELSE 'suppressed_small_cohort' END AS publication_status
FROM metrics
ORDER BY metric;
