WITH base AS (
  SELECT
    fis_mo_end_dt::date AS snapshot_date,
    fiscal_year,
    employee_id,
    CASE WHEN is_transferred IS NULL THEN 0 ELSE 1 END AS flag_observable,
    CASE WHEN is_transferred > 0 THEN 1 ELSE 0 END AS stored_transfer_flag,
    transfer_date::date AS transfer_date,
    CASE WHEN is_transferred > 0 AND transfer_date IS NULL THEN 1 ELSE 0 END AS flag_without_date,
    CASE WHEN transfer_date IS NOT NULL AND COALESCE(is_transferred, 0) <= 0 THEN 1 ELSE 0 END AS date_without_flag,
    CASE WHEN transfer_date::date > fis_mo_end_dt::date THEN 1 ELSE 0 END AS future_transfer_date,
    CASE
      WHEN is_transferred > 0
       AND transfer_date::date BETWEEN DATEADD(year, -1, fis_mo_end_dt::date) AND fis_mo_end_dt::date
      THEN 1 ELSE 0
    END AS same_row_flag_in_window
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
recent_snapshots AS (
  SELECT snapshot_date
  FROM (
    SELECT DISTINCT snapshot_date
    FROM base
    ORDER BY snapshot_date DESC
    LIMIT 3
  ) s
),
latest_snapshot AS (
  SELECT MAX(snapshot_date) AS snapshot_date
  FROM base
),
key_counts AS (
  SELECT
    snapshot_date,
    employee_id,
    COUNT(*) AS row_count
  FROM base
  GROUP BY 1, 2
),
key_agg AS (
  SELECT
    SUM(CASE WHEN row_count > 1 THEN 1 ELSE 0 END) AS duplicate_key_count,
    SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END) AS duplicate_extra_rows
  FROM key_counts
),
transfer_events AS (
  SELECT DISTINCT
    employee_id,
    transfer_date
  FROM base
  WHERE stored_transfer_flag = 1
    AND transfer_date IS NOT NULL
    AND future_transfer_date = 0
),
base_recalc AS (
  SELECT
    b.snapshot_date,
    b.fiscal_year,
    b.employee_id,
    b.flag_observable,
    b.stored_transfer_flag,
    b.flag_without_date,
    b.date_without_flag,
    b.future_transfer_date,
    b.same_row_flag_in_window,
    CASE WHEN COUNT(e.transfer_date) > 0 THEN 1 ELSE 0 END AS recalculated_past_year_flag,
    COUNT(DISTINCT e.transfer_date) AS transfer_events_in_window
  FROM base b
  LEFT JOIN transfer_events e
    ON b.employee_id = e.employee_id
   AND e.transfer_date BETWEEN DATEADD(year, -1, b.snapshot_date) AND b.snapshot_date
  GROUP BY
    b.snapshot_date,
    b.fiscal_year,
    b.employee_id,
    b.flag_observable,
    b.stored_transfer_flag,
    b.flag_without_date,
    b.date_without_flag,
    b.future_transfer_date,
    b.same_row_flag_in_window
),
scoped AS (
  SELECT 'full_history' AS scope, *
  FROM base_recalc
  UNION ALL
  SELECT 'recent_3_snapshots' AS scope, br.*
  FROM base_recalc br
  JOIN recent_snapshots r
    ON br.snapshot_date = r.snapshot_date
  UNION ALL
  SELECT 'latest_snapshot' AS scope, br.*
  FROM base_recalc br
  JOIN latest_snapshot l
    ON br.snapshot_date = l.snapshot_date
),
summary AS (
  SELECT
    'summary' AS section,
    scope,
    COUNT(*) AS eligible_rows,
    SUM(flag_observable) AS observable_rows,
    SUM(stored_transfer_flag) AS stored_transfer_flag_rows,
    SUM(recalculated_past_year_flag) AS recalculated_past_year_rows,
    SUM(CASE WHEN stored_transfer_flag = recalculated_past_year_flag THEN 1 ELSE 0 END) AS matched_rows,
    SUM(CASE WHEN stored_transfer_flag <> recalculated_past_year_flag THEN 1 ELSE 0 END) AS mismatch_rows,
    SUM(CASE WHEN stored_transfer_flag = 1 AND recalculated_past_year_flag = 0 THEN 1 ELSE 0 END) AS stored_yes_calc_no_rows,
    SUM(CASE WHEN stored_transfer_flag = 0 AND recalculated_past_year_flag = 1 THEN 1 ELSE 0 END) AS stored_no_calc_yes_rows,
    SUM(flag_without_date) AS flag_without_date_rows,
    SUM(date_without_flag) AS date_without_flag_rows,
    SUM(future_transfer_date) AS future_transfer_date_rows,
    SUM(CASE WHEN stored_transfer_flag = 1 AND same_row_flag_in_window = 0 THEN 1 ELSE 0 END) AS stored_flag_same_row_outside_window_rows,
    ROUND(100.0 * SUM(flag_observable) / NULLIF(COUNT(*), 0), 4) AS observable_percent,
    ROUND(100.0 * SUM(CASE WHEN stored_transfer_flag = recalculated_past_year_flag THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(100.0 * SUM(stored_transfer_flag) / NULLIF(COUNT(*), 0), 4) AS stored_event_percent,
    ROUND(100.0 * SUM(recalculated_past_year_flag) / NULLIF(COUNT(*), 0), 4) AS recalculated_event_percent
  FROM scoped
  GROUP BY 1, 2
),
fiscal_year_summary AS (
  SELECT
    'fiscal_year_summary' AS section,
    'fy_' || fiscal_year::varchar AS scope,
    COUNT(*) AS eligible_rows,
    SUM(flag_observable) AS observable_rows,
    SUM(stored_transfer_flag) AS stored_transfer_flag_rows,
    SUM(recalculated_past_year_flag) AS recalculated_past_year_rows,
    SUM(CASE WHEN stored_transfer_flag = recalculated_past_year_flag THEN 1 ELSE 0 END) AS matched_rows,
    SUM(CASE WHEN stored_transfer_flag <> recalculated_past_year_flag THEN 1 ELSE 0 END) AS mismatch_rows,
    SUM(CASE WHEN stored_transfer_flag = 1 AND recalculated_past_year_flag = 0 THEN 1 ELSE 0 END) AS stored_yes_calc_no_rows,
    SUM(CASE WHEN stored_transfer_flag = 0 AND recalculated_past_year_flag = 1 THEN 1 ELSE 0 END) AS stored_no_calc_yes_rows,
    SUM(flag_without_date) AS flag_without_date_rows,
    SUM(date_without_flag) AS date_without_flag_rows,
    SUM(future_transfer_date) AS future_transfer_date_rows,
    SUM(CASE WHEN stored_transfer_flag = 1 AND same_row_flag_in_window = 0 THEN 1 ELSE 0 END) AS stored_flag_same_row_outside_window_rows,
    ROUND(100.0 * SUM(flag_observable) / NULLIF(COUNT(*), 0), 4) AS observable_percent,
    ROUND(100.0 * SUM(CASE WHEN stored_transfer_flag = recalculated_past_year_flag THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) AS match_rate_percent,
    ROUND(100.0 * SUM(stored_transfer_flag) / NULLIF(COUNT(*), 0), 4) AS stored_event_percent,
    ROUND(100.0 * SUM(recalculated_past_year_flag) / NULLIF(COUNT(*), 0), 4) AS recalculated_event_percent
  FROM base_recalc
  GROUP BY 1, 2
),
event_source_summary AS (
  SELECT
    'event_source_summary' AS section,
    'all' AS scope,
    COUNT(*) AS eligible_rows,
    NULL::BIGINT AS observable_rows,
    NULL::BIGINT AS stored_transfer_flag_rows,
    NULL::BIGINT AS recalculated_past_year_rows,
    NULL::BIGINT AS matched_rows,
    NULL::BIGINT AS mismatch_rows,
    NULL::BIGINT AS stored_yes_calc_no_rows,
    NULL::BIGINT AS stored_no_calc_yes_rows,
    NULL::BIGINT AS flag_without_date_rows,
    NULL::BIGINT AS date_without_flag_rows,
    NULL::BIGINT AS future_transfer_date_rows,
    NULL::BIGINT AS stored_flag_same_row_outside_window_rows,
    NULL::DECIMAL(18,4) AS observable_percent,
    NULL::DECIMAL(18,4) AS match_rate_percent,
    NULL::DECIMAL(18,4) AS stored_event_percent,
    NULL::DECIMAL(18,4) AS recalculated_event_percent
  FROM transfer_events
)
SELECT
  section,
  scope,
  eligible_rows,
  observable_rows,
  stored_transfer_flag_rows,
  recalculated_past_year_rows,
  matched_rows,
  mismatch_rows,
  stored_yes_calc_no_rows,
  stored_no_calc_yes_rows,
  flag_without_date_rows,
  date_without_flag_rows,
  future_transfer_date_rows,
  stored_flag_same_row_outside_window_rows,
  observable_percent,
  match_rate_percent,
  stored_event_percent,
  recalculated_event_percent,
  CASE WHEN section = 'summary' AND scope = 'full_history' THEN (SELECT duplicate_key_count FROM key_agg) END AS duplicate_key_count,
  CASE WHEN section = 'summary' AND scope = 'full_history' THEN (SELECT duplicate_extra_rows FROM key_agg) END AS duplicate_extra_rows
FROM summary
UNION ALL
SELECT
  section,
  scope,
  eligible_rows,
  observable_rows,
  stored_transfer_flag_rows,
  recalculated_past_year_rows,
  matched_rows,
  mismatch_rows,
  stored_yes_calc_no_rows,
  stored_no_calc_yes_rows,
  flag_without_date_rows,
  date_without_flag_rows,
  future_transfer_date_rows,
  stored_flag_same_row_outside_window_rows,
  observable_percent,
  match_rate_percent,
  stored_event_percent,
  recalculated_event_percent,
  NULL::BIGINT AS duplicate_key_count,
  NULL::BIGINT AS duplicate_extra_rows
FROM fiscal_year_summary
UNION ALL
SELECT
  section,
  scope,
  eligible_rows,
  observable_rows,
  stored_transfer_flag_rows,
  recalculated_past_year_rows,
  matched_rows,
  mismatch_rows,
  stored_yes_calc_no_rows,
  stored_no_calc_yes_rows,
  flag_without_date_rows,
  date_without_flag_rows,
  future_transfer_date_rows,
  stored_flag_same_row_outside_window_rows,
  observable_percent,
  match_rate_percent,
  stored_event_percent,
  recalculated_event_percent,
  NULL::BIGINT AS duplicate_key_count,
  NULL::BIGINT AS duplicate_extra_rows
FROM event_source_summary
ORDER BY section, scope
