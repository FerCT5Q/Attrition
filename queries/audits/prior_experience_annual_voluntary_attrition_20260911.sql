/*
  Propósito: calcular una vista descriptiva anual de salida Voluntary por
  bandas de prior_qc_work_years para el deck activo.

  Deliverable mode: internal_analysis.
  Población de denominador: worker_type='Employee', employee_type='Regular',
  active_status=1.
  Corte fijo para reproducibilidad: 2026-09-11. Se excluyen snapshots futuros.
  Tasa = eventos Voluntary atribuidos a la última banda válida previa a
  term_date / promedio mensual de headcount activo de la banda * 100.

  La consulta devuelve únicamente métricas agregadas. No devuelve IDs ni filas
  de empleados. El field prior_qc_work_years se trata como stored/precomputed
  metric: la consulta valida la agrupación y la atribución temporal, no prueba
  su fórmula de negocio ni su lineage.

  Reglas de publicación:
    - cinco fiscal_year más recientes con 12 snapshots únicos, sufijo de fiscal_month 01..12
      y todas las fechas <= 2026-09-11;
    - siete bandas mutuamente excluyentes para valores válidos >= 0;
    - cada celda publicada requiere 12 meses, annual_distinct_employees >= 30
      y min_monthly_headcount >= 30;
    - sólo term_type normalizado exactamente igual a VOLUNTARY y term_date no nulo;
    - cada evento debe reconciliar a exactamente una última banda válida previa.
*/
WITH
parameters AS (
  SELECT DATE '2026-09-11' AS cutoff_date
),
raw_calendar AS (
  SELECT
    CAST(fis_mo_beg_dt AS DATE) AS period_begin,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS INTEGER) AS fiscal_year,
    CAST(fiscal_month AS INTEGER) AS fiscal_month,
    MOD(CAST(fiscal_month AS INTEGER), 100) AS fiscal_month_of_year
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) <= (SELECT cutoff_date FROM parameters)
  GROUP BY 1, 2, 3, 4
),
calendar_by_year AS (
  SELECT
    fiscal_year,
    COUNT(DISTINCT snapshot_date) AS snapshot_count,
    COUNT(DISTINCT fiscal_month_of_year) AS fiscal_month_count,
    MIN(fiscal_month_of_year) AS min_fiscal_month,
    MAX(fiscal_month_of_year) AS max_fiscal_month,
    MIN(period_begin) AS first_period_begin,
    MAX(snapshot_date) AS last_snapshot_date
  FROM raw_calendar
  GROUP BY 1
),
complete_year_candidates AS (
  SELECT fiscal_year
  FROM calendar_by_year
  WHERE snapshot_count = 12
    AND fiscal_month_count = 12
    AND min_fiscal_month = 1
    AND max_fiscal_month = 12
    AND last_snapshot_date <= (SELECT cutoff_date FROM parameters)
),
selected_years AS (
  SELECT fiscal_year
  FROM complete_year_candidates
  ORDER BY fiscal_year DESC
  LIMIT 5
),
selected_periods AS (
  SELECT
    c.period_begin,
    c.snapshot_date,
    c.fiscal_year,
    c.fiscal_month,
    c.fiscal_month_of_year
  FROM raw_calendar AS c
  INNER JOIN selected_years AS y USING (fiscal_year)
),
selected_period_counts AS (
  SELECT
    COUNT(*) AS selected_period_count,
    COUNT(DISTINCT snapshot_date) AS selected_snapshot_count,
    COUNT(DISTINCT fiscal_year) AS selected_fiscal_year_count,
    MIN(snapshot_date) AS first_selected_snapshot,
    MAX(snapshot_date) AS last_selected_snapshot,
    SUM(CASE WHEN snapshot_date > (SELECT cutoff_date FROM parameters) THEN 1 ELSE 0 END) AS future_selected_periods
  FROM selected_periods
),
bands AS (
  SELECT '0' AS band, 1 AS band_order
  UNION ALL SELECT '>0–<1', 2
  UNION ALL SELECT '1–<3', 3
  UNION ALL SELECT '3–<5', 4
  UNION ALL SELECT '5–<10', 5
  UNION ALL SELECT '10–<15', 6
  UNION ALL SELECT '15+', 7
),
all_source_rows AS (
  SELECT
    worker.employee_id,
    CAST(worker.fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(worker.fiscal_year AS INTEGER) AS fiscal_year,
    CAST(worker.fiscal_month AS INTEGER) AS fiscal_month,
    CAST(worker.prior_qc_work_years AS DECIMAL(18,6)) AS prior_qc_work_years,
    worker.worker_type,
    worker.employee_type,
    worker.active_status,
    worker.term_date,
    UPPER(NULLIF(TRIM(CAST(worker.term_type AS VARCHAR(256))), '')) AS normalized_term_type
  FROM hrda.post_hire_monthly_worker_dtls AS worker
  CROSS JOIN parameters
  WHERE worker.fis_mo_end_dt IS NOT NULL
    AND CAST(worker.fis_mo_end_dt AS DATE) <= parameters.cutoff_date
),
employee_snapshot_quality AS (
  SELECT
    snapshot_date,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT employee_id) AS distinct_employees,
    SUM(CASE WHEN prior_qc_work_years IS NULL THEN 1 ELSE 0 END) AS null_value_rows,
    SUM(CASE WHEN prior_qc_work_years < 0 THEN 1 ELSE 0 END) AS negative_value_rows
  FROM all_source_rows
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
  GROUP BY 1
),
history_band_rows AS (
  SELECT
    employee_id,
    snapshot_date,
    CASE
      WHEN prior_qc_work_years = 0 THEN '0'
      WHEN prior_qc_work_years > 0 AND prior_qc_work_years < 1 THEN '>0–<1'
      WHEN prior_qc_work_years >= 1 AND prior_qc_work_years < 3 THEN '1–<3'
      WHEN prior_qc_work_years >= 3 AND prior_qc_work_years < 5 THEN '3–<5'
      WHEN prior_qc_work_years >= 5 AND prior_qc_work_years < 10 THEN '5–<10'
      WHEN prior_qc_work_years >= 10 AND prior_qc_work_years < 15 THEN '10–<15'
      WHEN prior_qc_work_years >= 15 THEN '15+'
      ELSE NULL
    END AS band
  FROM all_source_rows
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND prior_qc_work_years IS NOT NULL
    AND prior_qc_work_years >= 0
),
history_band_snapshot AS (
  SELECT
    employee_id,
    snapshot_date,
    COUNT(DISTINCT band) AS distinct_band_count,
    COUNT(*) AS source_rows,
    MIN(band) AS band
  FROM history_band_rows
  GROUP BY 1, 2
),
valid_history_band AS (
  SELECT employee_id, snapshot_date, band
  FROM history_band_snapshot
  WHERE distinct_band_count = 1
),
selected_active_snapshots AS (
  SELECT
    a.employee_id,
    a.snapshot_date,
    a.fiscal_year,
    a.fiscal_month,
    h.band
  FROM all_source_rows AS a
  INNER JOIN selected_periods AS p
    ON p.snapshot_date = a.snapshot_date
   AND p.fiscal_year = a.fiscal_year
   AND p.fiscal_month = a.fiscal_month
  INNER JOIN valid_history_band AS h
    ON h.employee_id = a.employee_id
   AND h.snapshot_date = a.snapshot_date
  WHERE a.worker_type = 'Employee'
    AND a.employee_type = 'Regular'
    AND a.active_status = 1
),
monthly_band_counts AS (
  SELECT
    fiscal_year,
    fiscal_month,
    snapshot_date,
    band,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT employee_id) AS monthly_headcount
  FROM selected_active_snapshots
  GROUP BY 1, 2, 3, 4
),
band_month_grid AS (
  SELECT
    p.fiscal_year,
    p.fiscal_month,
    p.snapshot_date,
    b.band,
    b.band_order,
    COALESCE(m.monthly_headcount, 0) AS monthly_headcount,
    COALESCE(m.source_rows, 0) AS source_rows
  FROM selected_periods AS p
  CROSS JOIN bands AS b
  LEFT JOIN monthly_band_counts AS m
    ON m.fiscal_year = p.fiscal_year
   AND m.fiscal_month = p.fiscal_month
   AND m.snapshot_date = p.snapshot_date
   AND m.band = b.band
),
annual_band_exposure AS (
  SELECT
    fiscal_year,
    band,
    MAX(band_order) AS band_order,
    COUNT(DISTINCT snapshot_date) AS months_checked,
    COUNT(DISTINCT CASE WHEN monthly_headcount > 0 THEN snapshot_date END) AS months_with_headcount,
    MIN(monthly_headcount) AS min_monthly_headcount,
    MAX(monthly_headcount) AS max_monthly_headcount,
    AVG(monthly_headcount::DECIMAL(18,6)) AS average_monthly_headcount,
    SUM(source_rows) AS source_rows,
    COUNT(DISTINCT CASE WHEN monthly_headcount > 0 THEN NULL END) AS unused_metric
  FROM band_month_grid
  GROUP BY 1, 2
),
annual_distinct_population AS (
  SELECT
    fiscal_year,
    band,
    COUNT(DISTINCT employee_id) AS annual_distinct_employees
  FROM selected_active_snapshots
  GROUP BY 1, 2
),
voluntary_event_candidates AS (
  SELECT
    a.employee_id,
    CAST(a.term_date AS DATE) AS term_date,
    p.fiscal_year,
    COUNT(*) AS source_rows
  FROM all_source_rows AS a
  INNER JOIN selected_periods AS p
    ON CAST(a.term_date AS DATE) >= p.period_begin
   AND CAST(a.term_date AS DATE) <= p.snapshot_date
  WHERE a.worker_type = 'Employee'
    AND a.employee_type = 'Regular'
    AND a.normalized_term_type = 'VOLUNTARY'
    AND a.term_date IS NOT NULL
  GROUP BY 1, 2, 3
),
voluntary_events AS (
  SELECT employee_id, term_date, fiscal_year
  FROM voluntary_event_candidates
),
event_band_candidates AS (
  SELECT
    e.employee_id,
    e.term_date,
    e.fiscal_year,
    h.band,
    h.snapshot_date,
    ROW_NUMBER() OVER (
      PARTITION BY e.employee_id, e.term_date, e.fiscal_year
      ORDER BY h.snapshot_date DESC
    ) AS band_snapshot_rank
  FROM voluntary_events AS e
  LEFT JOIN valid_history_band AS h
    ON h.employee_id = e.employee_id
   AND h.snapshot_date < e.term_date
),
attributed_events AS (
  SELECT employee_id, term_date, fiscal_year, band, snapshot_date
  FROM event_band_candidates
  WHERE band_snapshot_rank = 1
    AND band IS NOT NULL
),
annual_exit_counts AS (
  SELECT
    fiscal_year,
    band,
    COUNT(*) AS voluntary_exit_events
  FROM attributed_events
  GROUP BY 1, 2
),
annual_total_events AS (
  SELECT fiscal_year, COUNT(*) AS total_voluntary_events
  FROM voluntary_events
  GROUP BY 1
),
annual_attributed_events AS (
  SELECT fiscal_year, COUNT(*) AS attributed_voluntary_events
  FROM attributed_events
  GROUP BY 1
),
annual_metrics AS (
  SELECT
    e.fiscal_year,
    e.band,
    e.band_order,
    e.months_checked,
    e.months_with_headcount,
    e.min_monthly_headcount,
    e.max_monthly_headcount,
    e.average_monthly_headcount,
    COALESCE(d.annual_distinct_employees, 0) AS annual_distinct_employees,
    COALESCE(x.voluntary_exit_events, 0) AS voluntary_exit_events,
    COALESCE(t.total_voluntary_events, 0) AS total_voluntary_events,
    COALESCE(a.attributed_voluntary_events, 0) AS attributed_voluntary_events,
    CASE
      WHEN e.months_checked = 12
       AND e.months_with_headcount = 12
       AND COALESCE(d.annual_distinct_employees, 0) >= 30
       AND e.min_monthly_headcount >= 30
      THEN 1 ELSE 0
    END AS privacy_eligible,
    CASE
      WHEN e.average_monthly_headcount > 0
      THEN ROUND(100.0 * COALESCE(x.voluntary_exit_events, 0) / e.average_monthly_headcount, 4)
      ELSE NULL
    END AS annual_voluntary_attrition_percent
  FROM annual_band_exposure AS e
  LEFT JOIN annual_distinct_population AS d
    ON d.fiscal_year = e.fiscal_year AND d.band = e.band
  LEFT JOIN annual_exit_counts AS x
    ON x.fiscal_year = e.fiscal_year AND x.band = e.band
  LEFT JOIN annual_total_events AS t
    ON t.fiscal_year = e.fiscal_year
  LEFT JOIN annual_attributed_events AS a
    ON a.fiscal_year = e.fiscal_year
),
annual_reconciliation AS (
  SELECT
    y.fiscal_year,
    COALESCE(t.total_voluntary_events, 0) AS total_voluntary_events,
    COALESCE(a.attributed_voluntary_events, 0) AS attributed_voluntary_events,
    COALESCE(t.total_voluntary_events, 0) - COALESCE(a.attributed_voluntary_events, 0) AS unattributed_voluntary_events,
    COALESCE(SUM(m.voluntary_exit_events), 0) AS sum_of_band_events,
    COALESCE(SUM(CASE WHEN m.privacy_eligible = 1 THEN m.voluntary_exit_events ELSE 0 END), 0) AS sum_of_published_band_events
  FROM selected_years AS y
  LEFT JOIN annual_total_events AS t USING (fiscal_year)
  LEFT JOIN annual_attributed_events AS a USING (fiscal_year)
  LEFT JOIN annual_metrics AS m USING (fiscal_year)
  GROUP BY 1, 2, 3, 4
),
source_domain AS (
  SELECT
    COUNT(DISTINCT CASE WHEN a.term_date IS NOT NULL THEN a.employee_id || '|' || CAST(a.term_date AS VARCHAR(32)) END) AS dated_termination_events,
    COUNT(DISTINCT CASE WHEN a.term_date IS NULL THEN a.employee_id END) AS employees_with_missing_term_date,
    COUNT(DISTINCT CASE WHEN a.term_date IS NOT NULL AND a.normalized_term_type = 'VOLUNTARY' THEN a.employee_id || '|' || CAST(a.term_date AS VARCHAR(32)) END) AS voluntary_events,
    COUNT(DISTINCT CASE WHEN a.term_date IS NOT NULL AND a.normalized_term_type = 'INVOLUNTARY' THEN a.employee_id || '|' || CAST(a.term_date AS VARCHAR(32)) END) AS involuntary_events,
    COUNT(DISTINCT CASE WHEN a.term_date IS NOT NULL AND a.normalized_term_type = 'VOLUNTARY EXCEPTION' THEN a.employee_id || '|' || CAST(a.term_date AS VARCHAR(32)) END) AS voluntary_exception_events,
    COUNT(DISTINCT CASE WHEN a.term_date IS NOT NULL AND COALESCE(a.normalized_term_type, '') NOT IN ('VOLUNTARY', 'INVOLUNTARY', 'VOLUNTARY EXCEPTION') THEN a.employee_id || '|' || CAST(a.term_date AS VARCHAR(32)) END) AS other_or_missing_type_events
  FROM all_source_rows AS a
  INNER JOIN selected_periods AS p
    ON CAST(a.term_date AS DATE) >= p.period_begin
   AND CAST(a.term_date AS DATE) <= p.snapshot_date
  WHERE a.worker_type = 'Employee'
    AND a.employee_type = 'Regular'
),
quality_summary AS (
  SELECT
    COUNT(*) AS all_employee_snapshot_dates_checked,
    SUM(CASE WHEN distinct_employees < source_rows THEN 1 ELSE 0 END) AS dates_with_duplicate_employee_rows,
    SUM(negative_value_rows) AS negative_value_rows,
    SUM(null_value_rows) AS null_value_rows
  FROM employee_snapshot_quality
  WHERE snapshot_date IN (SELECT snapshot_date FROM selected_periods)
)
SELECT
  'calendar' AS row_type,
  CAST(c.fiscal_year AS VARCHAR(32)) AS band_or_metric,
  c.fiscal_year,
  CAST(NULL AS INTEGER) AS fiscal_month,
  c.snapshot_count,
  c.fiscal_month_count,
  c.min_fiscal_month,
  c.max_fiscal_month,
  c.first_period_begin,
  c.last_snapshot_date,
  CAST(NULL AS INTEGER) AS months_checked,
  CAST(NULL AS INTEGER) AS months_with_headcount,
  CAST(NULL AS BIGINT) AS min_monthly_headcount,
  CAST(NULL AS BIGINT) AS max_monthly_headcount,
  CAST(NULL AS DECIMAL(18,6)) AS average_monthly_headcount,
  CAST(NULL AS BIGINT) AS annual_distinct_employees,
  CAST(NULL AS BIGINT) AS voluntary_exit_events,
  CAST(NULL AS BIGINT) AS total_voluntary_events,
  CAST(NULL AS BIGINT) AS attributed_voluntary_events,
  CAST(NULL AS BIGINT) AS unattributed_voluntary_events,
  CAST(NULL AS BIGINT) AS sum_of_band_events,
  CAST(NULL AS BIGINT) AS sum_of_published_band_events,
  CAST(NULL AS DECIMAL(18,4)) AS annual_voluntary_attrition_percent,
  CAST(NULL AS INTEGER) AS privacy_eligible,
  CAST(NULL AS BIGINT) AS dated_termination_events,
  CAST(NULL AS BIGINT) AS employees_with_missing_term_date,
  CAST(NULL AS BIGINT) AS voluntary_events,
  CAST(NULL AS BIGINT) AS involuntary_events,
  CAST(NULL AS BIGINT) AS voluntary_exception_events,
  CAST(NULL AS BIGINT) AS other_or_missing_type_events,
  CAST(NULL AS BIGINT) AS all_employee_snapshot_dates_checked,
  CAST(NULL AS BIGINT) AS dates_with_duplicate_employee_rows,
  CAST(NULL AS BIGINT) AS negative_value_rows,
  CAST(NULL AS BIGINT) AS null_value_rows,
  CAST(NULL AS BIGINT) AS selected_period_count,
  CAST(NULL AS BIGINT) AS selected_snapshot_count,
  CAST(NULL AS BIGINT) AS selected_fiscal_year_count,
  CAST(NULL AS DATE) AS first_selected_snapshot,
  CAST(NULL AS DATE) AS last_selected_snapshot,
  CAST(NULL AS BIGINT) AS future_selected_periods
FROM calendar_by_year AS c
WHERE c.fiscal_year IN (SELECT fiscal_year FROM selected_years)

UNION ALL

SELECT
  'band_year' AS row_type,
  m.band AS band_or_metric,
  m.fiscal_year,
  CAST(NULL AS INTEGER) AS fiscal_month,
  CAST(NULL AS BIGINT) AS snapshot_count,
  CAST(NULL AS BIGINT) AS fiscal_month_count,
  CAST(NULL AS INTEGER) AS min_fiscal_month,
  CAST(NULL AS INTEGER) AS max_fiscal_month,
  CAST(NULL AS DATE) AS first_period_begin,
  CAST(NULL AS DATE) AS last_snapshot_date,
  m.months_checked,
  m.months_with_headcount,
  m.min_monthly_headcount,
  m.max_monthly_headcount,
  m.average_monthly_headcount,
  m.annual_distinct_employees,
  m.voluntary_exit_events,
  m.total_voluntary_events,
  m.attributed_voluntary_events,
  CAST(NULL AS BIGINT) AS unattributed_voluntary_events,
  CAST(NULL AS BIGINT) AS sum_of_band_events,
  CAST(NULL AS BIGINT) AS sum_of_published_band_events,
  m.annual_voluntary_attrition_percent,
  m.privacy_eligible,
  CAST(NULL AS BIGINT) AS dated_termination_events,
  CAST(NULL AS BIGINT) AS employees_with_missing_term_date,
  CAST(NULL AS BIGINT) AS voluntary_events,
  CAST(NULL AS BIGINT) AS involuntary_events,
  CAST(NULL AS BIGINT) AS voluntary_exception_events,
  CAST(NULL AS BIGINT) AS other_or_missing_type_events,
  CAST(NULL AS BIGINT) AS all_employee_snapshot_dates_checked,
  CAST(NULL AS BIGINT) AS dates_with_duplicate_employee_rows,
  CAST(NULL AS BIGINT) AS negative_value_rows,
  CAST(NULL AS BIGINT) AS null_value_rows,
  CAST(NULL AS BIGINT) AS selected_period_count,
  CAST(NULL AS BIGINT) AS selected_snapshot_count,
  CAST(NULL AS BIGINT) AS selected_fiscal_year_count,
  CAST(NULL AS DATE) AS first_selected_snapshot,
  CAST(NULL AS DATE) AS last_selected_snapshot,
  CAST(NULL AS BIGINT) AS future_selected_periods
FROM annual_metrics AS m

UNION ALL

SELECT
  'reconciliation' AS row_type,
  CAST(r.fiscal_year AS VARCHAR(32)) AS band_or_metric,
  r.fiscal_year,
  CAST(NULL AS INTEGER) AS fiscal_month,
  CAST(NULL AS BIGINT) AS snapshot_count,
  CAST(NULL AS BIGINT) AS fiscal_month_count,
  CAST(NULL AS INTEGER) AS min_fiscal_month,
  CAST(NULL AS INTEGER) AS max_fiscal_month,
  CAST(NULL AS DATE) AS first_period_begin,
  CAST(NULL AS DATE) AS last_snapshot_date,
  CAST(NULL AS INTEGER) AS months_checked,
  CAST(NULL AS INTEGER) AS months_with_headcount,
  CAST(NULL AS BIGINT) AS min_monthly_headcount,
  CAST(NULL AS BIGINT) AS max_monthly_headcount,
  CAST(NULL AS DECIMAL(18,6)) AS average_monthly_headcount,
  CAST(NULL AS BIGINT) AS annual_distinct_employees,
  CAST(NULL AS BIGINT) AS voluntary_exit_events,
  r.total_voluntary_events,
  r.attributed_voluntary_events,
  r.unattributed_voluntary_events,
  r.sum_of_band_events,
  r.sum_of_published_band_events,
  CAST(NULL AS DECIMAL(18,4)) AS annual_voluntary_attrition_percent,
  CAST(NULL AS INTEGER) AS privacy_eligible,
  CAST(NULL AS BIGINT) AS dated_termination_events,
  CAST(NULL AS BIGINT) AS employees_with_missing_term_date,
  CAST(NULL AS BIGINT) AS voluntary_events,
  CAST(NULL AS BIGINT) AS involuntary_events,
  CAST(NULL AS BIGINT) AS voluntary_exception_events,
  CAST(NULL AS BIGINT) AS other_or_missing_type_events,
  CAST(NULL AS BIGINT) AS all_employee_snapshot_dates_checked,
  CAST(NULL AS BIGINT) AS dates_with_duplicate_employee_rows,
  CAST(NULL AS BIGINT) AS negative_value_rows,
  CAST(NULL AS BIGINT) AS null_value_rows,
  CAST(NULL AS BIGINT) AS selected_period_count,
  CAST(NULL AS BIGINT) AS selected_snapshot_count,
  CAST(NULL AS BIGINT) AS selected_fiscal_year_count,
  CAST(NULL AS DATE) AS first_selected_snapshot,
  CAST(NULL AS DATE) AS last_selected_snapshot,
  CAST(NULL AS BIGINT) AS future_selected_periods
FROM annual_reconciliation AS r

UNION ALL

SELECT
  'source_domain' AS row_type,
  'selected_years' AS band_or_metric,
  CAST(NULL AS INTEGER) AS fiscal_year,
  CAST(NULL AS INTEGER) AS fiscal_month,
  CAST(NULL AS BIGINT) AS snapshot_count,
  CAST(NULL AS BIGINT) AS fiscal_month_count,
  CAST(NULL AS INTEGER) AS min_fiscal_month,
  CAST(NULL AS INTEGER) AS max_fiscal_month,
  CAST(NULL AS DATE) AS first_period_begin,
  CAST(NULL AS DATE) AS last_snapshot_date,
  CAST(NULL AS INTEGER) AS months_checked,
  CAST(NULL AS INTEGER) AS months_with_headcount,
  CAST(NULL AS BIGINT) AS min_monthly_headcount,
  CAST(NULL AS BIGINT) AS max_monthly_headcount,
  CAST(NULL AS DECIMAL(18,6)) AS average_monthly_headcount,
  CAST(NULL AS BIGINT) AS annual_distinct_employees,
  CAST(NULL AS BIGINT) AS voluntary_exit_events,
  CAST(NULL AS BIGINT) AS total_voluntary_events,
  CAST(NULL AS BIGINT) AS attributed_voluntary_events,
  CAST(NULL AS BIGINT) AS unattributed_voluntary_events,
  CAST(NULL AS BIGINT) AS sum_of_band_events,
  CAST(NULL AS BIGINT) AS sum_of_published_band_events,
  CAST(NULL AS DECIMAL(18,4)) AS annual_voluntary_attrition_percent,
  CAST(NULL AS INTEGER) AS privacy_eligible,
  d.dated_termination_events,
  d.employees_with_missing_term_date,
  d.voluntary_events,
  d.involuntary_events,
  d.voluntary_exception_events,
  d.other_or_missing_type_events,
  q.all_employee_snapshot_dates_checked,
  q.dates_with_duplicate_employee_rows,
  q.negative_value_rows,
  q.null_value_rows,
  p.selected_period_count,
  p.selected_snapshot_count,
  p.selected_fiscal_year_count,
  p.first_selected_snapshot,
  p.last_selected_snapshot,
  p.future_selected_periods
FROM source_domain AS d
CROSS JOIN quality_summary AS q
CROSS JOIN selected_period_counts AS p
ORDER BY row_type, fiscal_year, band_or_metric;
