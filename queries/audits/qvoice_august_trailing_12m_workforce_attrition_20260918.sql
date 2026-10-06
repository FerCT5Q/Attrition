/*
  Slide 18 QVoice: attrition voluntario retrospectivo uniforme por año.

  Claim
  -----
  Para cada encuesta QVoice de 2023 a 2026, el slide muestra el attrition
  voluntario de toda la fuerza laboral regular no-RF360 durante los 12 meses
  que terminan en el último snapshot mensual de agosto del mismo año.

  Definición
  ----------
  - Ventana: (corte de agosto - 12 meses, corte de agosto].
  - Denominador: promedio de headcount activo regular no-RF360 en los últimos
    12 snapshots mensuales disponibles hasta ese corte de agosto.
  - Numerador: empleados distintos que tuvieron al menos una terminación con
    term_type exactamente VOLUNTARY en la ventana y que aparecen activos en
    alguno de esos snapshots mensuales.
  - Tasa: 100 * salidas voluntarias / headcount mensual promedio.

  Es una comparación descriptiva de tendencia para poner junto a las menciones
  de QVoice. No atribuye las salidas a los comentarios ni mide attrition de
  participantes individuales de QVoice.

  Grano: un corte de agosto por año. Sólo resultados agregados.

  Regla de aceptación
  -------------------
  Deben regresar exactamente cuatro años (2023-2026), cada uno con 12
  snapshots mensuales, al menos 30 empleados activos promedio y cero
  duplicados de employee_id dentro de cada snapshot después de la
  deduplicación. La etiqueta VOLUNTARY se valida en el audit complementario.
*/
WITH august_cutoffs AS (
  SELECT
    CAST(fiscal_year AS INTEGER) AS cutoff_year,
    MAX(CAST(fis_mo_end_dt AS DATE)) AS august_cutoff_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fiscal_year BETWEEN 2023 AND 2026
    AND fis_mo_end_dt IS NOT NULL
    AND EXTRACT(MONTH FROM CAST(fis_mo_end_dt AS DATE)) = 8
  GROUP BY 1
),
candidate_snapshot_dates AS (
  SELECT
    c.cutoff_year,
    c.august_cutoff_date,
    CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
    ROW_NUMBER() OVER (
      PARTITION BY c.cutoff_year
      ORDER BY CAST(w.fis_mo_end_dt AS DATE) DESC
    ) AS recency_rank
  FROM august_cutoffs AS c
  INNER JOIN hrda.post_hire_monthly_worker_dtls AS w
    ON CAST(w.fis_mo_end_dt AS DATE) <= c.august_cutoff_date
   AND CAST(w.fis_mo_end_dt AS DATE) > DATEADD(month, -12, c.august_cutoff_date)
  WHERE w.fis_mo_end_dt IS NOT NULL
  GROUP BY 1, 2, 3
),
trailing_monthly_dates AS (
  SELECT cutoff_year, august_cutoff_date, snapshot_date
  FROM candidate_snapshot_dates
  WHERE recency_rank <= 12
),
active_employee_snapshot_rows AS (
  SELECT
    d.cutoff_year,
    d.august_cutoff_date,
    d.snapshot_date,
    w.employee_id,
    COUNT(*) AS source_row_count
  FROM trailing_monthly_dates AS d
  INNER JOIN hrda.post_hire_monthly_worker_dtls AS w
    ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND COALESCE(w.is_rf360_yes_no, 0) = 0
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2, 3, 4
),
monthly_headcount AS (
  SELECT
    cutoff_year,
    august_cutoff_date,
    snapshot_date,
    COUNT(*) AS active_regular_employee_count,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_count
  FROM active_employee_snapshot_rows
  GROUP BY 1, 2, 3
),
window_population AS (
  SELECT
    cutoff_year,
    august_cutoff_date,
    COUNT(DISTINCT employee_id) AS distinct_active_employee_count_in_window
  FROM active_employee_snapshot_rows
  GROUP BY 1, 2
),
voluntary_events AS (
  SELECT DISTINCT
    employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND COALESCE(is_rf360_yes_no, 0) = 0
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
    AND employee_id IS NOT NULL
),
voluntary_exit_counts AS (
  SELECT
    c.cutoff_year,
    c.august_cutoff_date,
    COUNT(DISTINCT e.employee_id) AS voluntary_exit_count
  FROM august_cutoffs AS c
  INNER JOIN window_population AS p
    ON p.cutoff_year = c.cutoff_year
  INNER JOIN active_employee_snapshot_rows AS s
    ON s.cutoff_year = c.cutoff_year
  INNER JOIN voluntary_events AS e
    ON e.employee_id = s.employee_id
   AND e.term_date > DATEADD(month, -12, c.august_cutoff_date)
   AND e.term_date <= c.august_cutoff_date
  GROUP BY 1, 2
),
headcount_summary AS (
  SELECT
    cutoff_year,
    august_cutoff_date,
    MIN(snapshot_date) AS first_snapshot_date,
    MAX(snapshot_date) AS last_snapshot_date,
    COUNT(*) AS monthly_snapshot_count,
    MIN(active_regular_employee_count) AS minimum_monthly_headcount,
    MAX(active_regular_employee_count) AS maximum_monthly_headcount,
    AVG(active_regular_employee_count) AS average_monthly_headcount,
    SUM(duplicate_employee_count) AS duplicate_employee_count
  FROM monthly_headcount
  GROUP BY 1, 2
)
SELECT
  h.cutoff_year,
  h.august_cutoff_date,
  DATEADD(month, -12, h.august_cutoff_date) AS window_start_date,
  h.first_snapshot_date,
  h.last_snapshot_date,
  h.monthly_snapshot_count,
  h.minimum_monthly_headcount,
  h.maximum_monthly_headcount,
  ROUND(h.average_monthly_headcount, 2) AS average_monthly_headcount,
  h.duplicate_employee_count,
  p.distinct_active_employee_count_in_window,
  COALESCE(v.voluntary_exit_count, 0) AS voluntary_exit_count,
  ROUND(
    100.0 * COALESCE(v.voluntary_exit_count, 0)
      / NULLIF(h.average_monthly_headcount, 0),
    2
  ) AS trailing_12m_voluntary_attrition_percent
FROM headcount_summary AS h
INNER JOIN window_population AS p
  ON p.cutoff_year = h.cutoff_year
LEFT JOIN voluntary_exit_counts AS v
  ON v.cutoff_year = h.cutoff_year
ORDER BY h.cutoff_year;
