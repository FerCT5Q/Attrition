/*
  Jan-2026 QVoice structured items: attrition voluntaria YTD por respuesta.

  La población se fija en el snapshot activo Regular anterior a la wave.
  El outcome no incluye el día de la respuesta y termina en el último
  snapshot observado. Sólo se devuelven agregados por item y valor 0/1.
*/
WITH source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
),
parameters AS (
  SELECT
    DATE '2026-01-07' AS survey_launch_date,
    DATE '2025-12-28' AS baseline_snapshot,
    latest_snapshot_date
  FROM source_bounds
),
qvoice_source AS (
  SELECT
    q.emp_id,
    COUNT(*) AS qvoice_row_count,
    COUNT(DISTINCT q.intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm) AS intent_see_myself_value_count,
    MIN(q.intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm) AS intent_see_myself_value,
    COUNT(DISTINCT q.intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job) AS intent_rarely_look_value_count,
    MIN(q.intent_to_stay_kpi_item_2_rarely_think_about_looking_for_new_job) AS intent_rarely_look_value,
    COUNT(DISTINCT q.growth_and_development_item_1_career_goals_can_be_met) AS career_goals_value_count,
    MIN(q.growth_and_development_item_1_career_goals_can_be_met) AS career_goals_value
  FROM hrda.qvoice_survey_data AS q
  CROSS JOIN parameters AS p
  WHERE q.survey_launch_date = p.survey_launch_date
    AND q.emp_id IS NOT NULL
  GROUP BY 1
),
baseline AS (
  SELECT
    w.employee_id,
    COUNT(*) AS baseline_row_count
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN parameters AS p
  WHERE CAST(w.fis_mo_end_dt AS DATE) = p.baseline_snapshot
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
  GROUP BY 1
),
voluntary_events AS (
  SELECT
    w.employee_id,
    COUNT(DISTINCT CAST(w.term_date AS DATE)) AS event_date_count
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN parameters AS p
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > p.survey_launch_date
    AND CAST(w.term_date AS DATE) <= p.latest_snapshot_date
  GROUP BY 1
),
eligible AS (
  SELECT
    q.emp_id,
    q.qvoice_row_count,
    q.intent_see_myself_value_count,
    q.intent_see_myself_value,
    q.intent_rarely_look_value_count,
    q.intent_rarely_look_value,
    q.career_goals_value_count,
    q.career_goals_value,
    b.baseline_row_count,
    CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END AS voluntary_attrition_target
  FROM qvoice_source AS q
  INNER JOIN baseline AS b
    ON b.employee_id = q.emp_id
  LEFT JOIN voluntary_events AS v
    ON v.employee_id = q.emp_id
),
item_values AS (
  SELECT
    'intent_see_myself' AS metric,
    intent_see_myself_value AS response_value,
    voluntary_attrition_target
  FROM eligible
  WHERE qvoice_row_count = 1
    AND baseline_row_count = 1
    AND intent_see_myself_value_count = 1
    AND intent_see_myself_value IN (0, 1)

  UNION ALL

  SELECT
    'intent_rarely_look' AS metric,
    intent_rarely_look_value AS response_value,
    voluntary_attrition_target
  FROM eligible
  WHERE qvoice_row_count = 1
    AND baseline_row_count = 1
    AND intent_rarely_look_value_count = 1
    AND intent_rarely_look_value IN (0, 1)

  UNION ALL

  SELECT
    'career_goals' AS metric,
    career_goals_value AS response_value,
    voluntary_attrition_target
  FROM eligible
  WHERE qvoice_row_count = 1
    AND baseline_row_count = 1
    AND career_goals_value_count = 1
    AND career_goals_value IN (0, 1)
),
item_metrics AS (
  SELECT
    metric,
    response_value,
    COUNT(*) AS eligible_employee_count,
    SUM(voluntary_attrition_target) AS voluntary_exit_count,
    ROUND(
      100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0),
      4
    ) AS ytd_voluntary_attrition_rate_percent
  FROM item_values
  GROUP BY 1, 2
),
quality_metrics AS (
  SELECT
    'latest_snapshot_date' AS metric,
    CAST(NULL AS INTEGER) AS response_value,
    CAST(NULL AS BIGINT) AS eligible_employee_count,
    CAST(NULL AS BIGINT) AS voluntary_exit_count,
    CAST(NULL AS DECIMAL(18, 4)) AS ytd_voluntary_attrition_rate_percent,
    CAST(p.latest_snapshot_date AS VARCHAR(32)) AS metric_value
  FROM parameters AS p

  UNION ALL

  SELECT
    'qvoice_distinct_employee_count', CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 4)),
    CAST(COUNT(*) AS VARCHAR(32))
  FROM qvoice_source

  UNION ALL

  SELECT
    'qvoice_duplicate_employee_count', CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 4)),
    CAST(SUM(CASE WHEN qvoice_row_count > 1 THEN 1 ELSE 0 END) AS VARCHAR(32))
  FROM qvoice_source

  UNION ALL

  SELECT
    'baseline_duplicate_employee_count', CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 4)),
    CAST(SUM(CASE WHEN baseline_row_count > 1 THEN 1 ELSE 0 END) AS VARCHAR(32))
  FROM baseline

  UNION ALL

  SELECT
    'matched_qvoice_employee_count', CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 4)),
    CAST(COUNT(*) AS VARCHAR(32))
  FROM eligible

  UNION ALL

  SELECT
    'unmatched_qvoice_employee_count', CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 4)),
    CAST((SELECT COUNT(*) FROM qvoice_source) - (SELECT COUNT(*) FROM eligible) AS VARCHAR(32))
)
SELECT
  'quality_metric' AS result_type,
  metric,
  response_value,
  eligible_employee_count,
  voluntary_exit_count,
  ytd_voluntary_attrition_rate_percent,
  metric_value
FROM quality_metrics

UNION ALL

SELECT
  'item_response' AS result_type,
  metric,
  response_value,
  eligible_employee_count,
  voluntary_exit_count,
  ytd_voluntary_attrition_rate_percent,
  CAST(NULL AS VARCHAR(32)) AS metric_value
FROM item_metrics
ORDER BY 1, 2, 3;
