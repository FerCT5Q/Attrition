-- Validación agregada de viabilidad: QVoice Jan-2026 con attrition voluntario
-- posterior para los items estructurados de Intent to Stay y Career Goals.
--
-- Concepto: cada respuesta QVoice se asigna al empleado activo regular del
-- snapshot inmediatamente anterior a la wave. La llave se usa sólo en CTEs y
-- joins; la salida contiene métricas agregadas y tasas por valor 0/1.
--
-- Target: al menos una terminación con term_type estrictamente VOLUNTARY y
-- term_date en (2026-01-07, 2026-07-07]. Los nulos no se convierten en 0.
--
-- Regla de aceptación: el seguimiento de seis meses debe estar disponible;
-- el snapshot workforce y la fuente QVoice deben ser únicos por empleado;
-- los valores publicados deben ser 0/1 y cada bucket debe tener n >= 30.
WITH source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
),
wave AS (
  SELECT DATE '2026-01-07' AS survey_launch_date
),
baseline_choice AS (
  SELECT
    wave.survey_launch_date,
    MAX(CAST(w.fis_mo_end_dt AS DATE)) AS baseline_snapshot
  FROM wave
  CROSS JOIN hrda.post_hire_monthly_worker_dtls AS w
  WHERE CAST(w.fis_mo_end_dt AS DATE) <= wave.survey_launch_date
  GROUP BY wave.survey_launch_date
),
qvoice_source AS (
  SELECT
    q.emp_id,
    COUNT(*) AS qvoice_source_row_count,
    COUNT(DISTINCT q.intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm) AS intent_value_count,
    MIN(q.intent_to_stay_kpi_item_1_see_myself_working_at_qualcomm) AS intent_value,
    COUNT(DISTINCT q.growth_and_development_item_1_career_goals_can_be_met) AS career_value_count,
    MIN(q.growth_and_development_item_1_career_goals_can_be_met) AS career_value
  FROM hrda.qvoice_survey_data AS q
  CROSS JOIN wave
  WHERE q.survey_launch_date = wave.survey_launch_date
    AND q.emp_id IS NOT NULL
  GROUP BY 1
),
workforce_snapshot AS (
  SELECT
    w.employee_id,
    COUNT(*) AS workforce_source_row_count
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN baseline_choice AS b
  WHERE w.fis_mo_end_dt = b.baseline_snapshot
    AND w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
  GROUP BY 1
),
voluntary_events AS (
  SELECT
    w.employee_id,
    COUNT(DISTINCT CAST(w.term_date AS DATE)) AS voluntary_event_date_count
  FROM hrda.post_hire_monthly_worker_dtls AS w
  CROSS JOIN wave
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.employee_id IS NOT NULL
    AND UPPER(NULLIF(TRIM(CAST(w.term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND CAST(w.term_date AS DATE) > wave.survey_launch_date
    AND CAST(w.term_date AS DATE) <= DATEADD(month, 6, wave.survey_launch_date)
  GROUP BY 1
),
eligible_qvoice AS (
  SELECT
    q.emp_id,
    q.qvoice_source_row_count,
    q.intent_value_count,
    q.intent_value,
    q.career_value_count,
    q.career_value,
    w.workforce_source_row_count,
    CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END AS voluntary_attrition_target
  FROM qvoice_source AS q
  INNER JOIN workforce_snapshot AS w
    ON w.employee_id = q.emp_id
  LEFT JOIN voluntary_events AS v
    ON v.employee_id = q.emp_id
),
item_values AS (
  SELECT
    CAST('Intent to Stay' AS VARCHAR(64)) AS item,
    intent_value AS response_value,
    voluntary_attrition_target
  FROM eligible_qvoice
  WHERE qvoice_source_row_count = 1
    AND workforce_source_row_count = 1
    AND intent_value_count = 1
    AND intent_value IN (0, 1)

  UNION ALL

  SELECT
    CAST('Career Goals' AS VARCHAR(64)) AS item,
    career_value AS response_value,
    voluntary_attrition_target
  FROM eligible_qvoice
  WHERE qvoice_source_row_count = 1
    AND workforce_source_row_count = 1
    AND career_value_count = 1
    AND career_value IN (0, 1)
),
item_metrics AS (
  SELECT
    item,
    response_value,
    COUNT(*) AS eligible_employee_count,
    SUM(voluntary_attrition_target) AS voluntary_exit_count,
    100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0) AS voluntary_attrition_rate_percent
  FROM item_values
  GROUP BY 1, 2
),
validation_metrics AS (
  SELECT 'latest_snapshot_date' AS metric, CAST(NULL AS VARCHAR(64)) AS item, CAST(NULL AS INTEGER) AS response_value, CAST(NULL AS BIGINT) AS eligible_employee_count, CAST(NULL AS BIGINT) AS voluntary_exit_count, CAST(NULL AS DECIMAL(18, 8)) AS voluntary_attrition_rate_percent, CAST(source_bounds.latest_snapshot_date AS VARCHAR(32)) AS metric_value
  FROM source_bounds
  UNION ALL SELECT 'six_month_followup_complete', CAST(NULL AS VARCHAR(64)), CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST(CASE WHEN source_bounds.latest_snapshot_date >= DATEADD(month, 6, wave.survey_launch_date) THEN 1 ELSE 0 END AS VARCHAR(32)) FROM source_bounds CROSS JOIN wave
  UNION ALL SELECT 'qvoice_distinct_employee_count', CAST(NULL AS VARCHAR(64)), CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST(COUNT(*) AS VARCHAR(32)) FROM qvoice_source
  UNION ALL SELECT 'qvoice_duplicate_employee_count', CAST(NULL AS VARCHAR(64)), CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST(SUM(CASE WHEN qvoice_source_row_count > 1 THEN 1 ELSE 0 END) AS VARCHAR(32)) FROM qvoice_source
  UNION ALL SELECT 'workforce_distinct_employee_count', CAST(NULL AS VARCHAR(64)), CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST(COUNT(*) AS VARCHAR(32)) FROM workforce_snapshot
  UNION ALL SELECT 'workforce_duplicate_employee_count', CAST(NULL AS VARCHAR(64)), CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST(SUM(CASE WHEN workforce_source_row_count > 1 THEN 1 ELSE 0 END) AS VARCHAR(32)) FROM workforce_snapshot
  UNION ALL SELECT 'matched_qvoice_employee_count', CAST(NULL AS VARCHAR(64)), CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST(COUNT(*) AS VARCHAR(32)) FROM eligible_qvoice
  UNION ALL SELECT 'unmatched_qvoice_employee_count', CAST(NULL AS VARCHAR(64)), CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST((SELECT COUNT(*) FROM qvoice_source) - (SELECT COUNT(*) FROM eligible_qvoice) AS VARCHAR(32))
  UNION ALL SELECT 'qvoice_conflicting_item_response_count', CAST(NULL AS VARCHAR(64)), CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST(SUM(CASE WHEN intent_value_count > 1 OR career_value_count > 1 THEN 1 ELSE 0 END) AS VARCHAR(32)) FROM eligible_qvoice
  UNION ALL SELECT 'multiple_voluntary_event_date_count', CAST(NULL AS VARCHAR(64)), CAST(NULL AS INTEGER), CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18, 8)), CAST(COUNT(*) AS VARCHAR(32)) FROM voluntary_events WHERE voluntary_event_date_count > 1
)
SELECT
  CAST('metric' AS VARCHAR(16)) AS result_type,
  metric,
  item,
  response_value,
  eligible_employee_count,
  voluntary_exit_count,
  voluntary_attrition_rate_percent,
  metric_value
FROM validation_metrics

UNION ALL

SELECT
  CAST('item_response' AS VARCHAR(16)) AS result_type,
  CAST(NULL AS VARCHAR(64)) AS metric,
  item,
  response_value,
  eligible_employee_count,
  voluntary_exit_count,
  voluntary_attrition_rate_percent,
  CAST(NULL AS VARCHAR(32)) AS metric_value
FROM item_metrics
WHERE eligible_employee_count >= 30
ORDER BY 1, 2, 3, 4;
