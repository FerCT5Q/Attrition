/*
  Vista anual YTD de movimientos IOS por business_process_reason.

  Propósito: alimentar el slide 5 de la presentación V7 con cohortes de
  empleados regulares activos y attrition Voluntary observado después del
  primer evento IOS de cada motivo. El resultado es agregado; employee_id se
  utiliza únicamente dentro de joins, deduplicaciones y COUNT(DISTINCT).

  Ventana comparable: enero al último snapshot de agosto de cada año calendario
  2024, 2025 y 2026. No usa eventos posteriores al cutoff correspondiente.
  El outcome no es un follow-up completo de 12 meses: es una salida Voluntary
  después del evento y hasta el cutoff de agosto del mismo año.

  Modo de entrega V7: internal_analysis autorizado para el requester y Julia.
  Se conservan todos los conteos y tasas agregadas, incluso cuando n < 30.
  No se devuelve ninguna fila de empleado ni identificador.
*/
WITH critical_tech_catalog AS (
  SELECT LOWER(TRIM(extended_job_family)) AS normalized_job_family
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
  GROUP BY 1
  HAVING COUNT(DISTINCT NULLIF(TRIM(seg), '')) = 1
     AND MAX(NULLIF(TRIM(seg), '')) <> 'Other Eng'
),
august_cutoffs AS (
  SELECT
    EXTRACT(YEAR FROM fis_mo_end_dt)::int AS calendar_year,
    MAX(fis_mo_end_dt::date) AS cutoff_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE EXTRACT(YEAR FROM fis_mo_end_dt) BETWEEN 2024 AND 2026
    AND EXTRACT(MONTH FROM fis_mo_end_dt) = 8
  GROUP BY 1
),
monthly_workforce AS (
  SELECT
    fis_mo_end_dt::date AS snapshot_date,
    COUNT(DISTINCT employee_id) AS active_regular_employees
  FROM hrda.post_hire_monthly_worker_dtls w
  INNER JOIN critical_tech_catalog c
    ON c.normalized_job_family = LOWER(TRIM(w.job_family))
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.is_rf360_yes_no = 0
  GROUP BY 1
),
ytd_workforce AS (
  SELECT
    c.calendar_year,
    c.cutoff_date,
    COUNT(DISTINCT m.snapshot_date) AS observed_monthly_snapshots,
    AVG(m.active_regular_employees) AS average_active_regular_employees
  FROM august_cutoffs c
  JOIN monthly_workforce m
    ON m.snapshot_date >= DATE_TRUNC('year', c.cutoff_date)::date
   AND m.snapshot_date <= c.cutoff_date
  GROUP BY 1, 2
),
raw_ios_events AS (
  SELECT DISTINCT
    c.calendar_year,
    c.cutoff_date,
    t.employee_id,
    t.effective_date::date AS effective_date,
    TRIM(t.business_process_reason) AS reason_value
  FROM august_cutoffs c
  JOIN hrda.workers_ios_transfers t
    ON t.effective_date::date >= DATE_TRUNC('year', c.cutoff_date)::date
   AND t.effective_date::date <= c.cutoff_date
  WHERE t.employee_id IS NOT NULL
    AND t.effective_date IS NOT NULL
    AND NULLIF(TRIM(t.business_process_reason), '') IS NOT NULL
),
active_regular_candidates AS (
  SELECT
    e.calendar_year,
    e.cutoff_date,
    e.employee_id,
    e.effective_date,
    e.reason_value,
    w.fis_mo_end_dt::date AS snapshot_date
  FROM raw_ios_events e
  JOIN hrda.post_hire_monthly_worker_dtls w
    ON w.employee_id = e.employee_id
   AND w.worker_type = 'Employee'
   AND w.employee_type = 'Regular'
   AND w.active_status = 1
   AND w.is_rf360_yes_no = 0
  JOIN critical_tech_catalog c
    ON c.normalized_job_family = LOWER(TRIM(w.job_family))
   AND w.fis_mo_end_dt::date <= e.effective_date
   AND w.fis_mo_end_dt::date >= DATEADD(day, -45, e.effective_date)
),
eligible_ios_events AS (
  SELECT calendar_year, cutoff_date, employee_id, effective_date, reason_value
  FROM (
    SELECT
      calendar_year,
      cutoff_date,
      employee_id,
      effective_date,
      reason_value,
      ROW_NUMBER() OVER (
        PARTITION BY calendar_year, employee_id, effective_date, reason_value
        ORDER BY snapshot_date DESC
      ) AS snapshot_rank
    FROM active_regular_candidates
  ) ranked
  WHERE snapshot_rank = 1
),
reason_cohorts AS (
  SELECT
    calendar_year,
    cutoff_date,
    reason_value AS group_label,
    employee_id,
    MIN(effective_date) AS index_event_date
  FROM eligible_ios_events
  GROUP BY 1, 2, 3, 4
),
total_cohorts AS (
  SELECT
    calendar_year,
    cutoff_date,
    'All eligible IOS movements' AS group_label,
    employee_id,
    MIN(effective_date) AS index_event_date
  FROM eligible_ios_events
  GROUP BY 1, 2, 3, 4
),
cohorts AS (
  SELECT calendar_year, cutoff_date, group_label, employee_id, index_event_date
  FROM total_cohorts
  UNION ALL
  SELECT calendar_year, cutoff_date, group_label, employee_id, index_event_date
  FROM reason_cohorts
),
voluntary_terms AS (
  SELECT DISTINCT employeeid, term_date::date AS term_date
  FROM hrda.all_terminations
  WHERE term_date IS NOT NULL
    AND term_date::date <= (SELECT MAX(cutoff_date) FROM august_cutoffs)
    AND NULLIF(TRIM(term_type), '') = 'Voluntary'
),
aggregates AS (
  SELECT
    c.calendar_year,
    c.group_label,
    COUNT(DISTINCT c.employee_id) AS cohort_employees,
    COUNT(DISTINCT CASE WHEN t.employeeid IS NOT NULL THEN c.employee_id END)
      AS voluntary_exit_employees,
    ROUND(
      100.0 * COUNT(DISTINCT CASE WHEN t.employeeid IS NOT NULL THEN c.employee_id END)
      / NULLIF(COUNT(DISTINCT c.employee_id), 0),
      1
    ) AS post_event_voluntary_attrition_percent
  FROM cohorts c
  LEFT JOIN voluntary_terms t
    ON t.employeeid = c.employee_id
   AND t.term_date > c.index_event_date
   AND t.term_date <= c.cutoff_date
  GROUP BY 1, 2
),
group_order AS (
  SELECT 0 AS display_order, 'All eligible IOS movements' AS group_label
  UNION ALL SELECT 1, 'Transfer > Transfer > Reorg Department and/or Manager Change'
  UNION ALL SELECT 2, 'Transfer > Transfer > Lateral IOS'
  UNION ALL SELECT 3, 'Transfer > Transfer > Country-to-Country Location Change'
  UNION ALL SELECT 4, 'Promotion > Transfer > Promo IOS'
  UNION ALL SELECT 5, 'Transfer > Transfer > Immigration Parking'
  UNION ALL SELECT 6, 'Demotion > Transfer > Downlevel IOS'
),
published AS (
  SELECT
    c.calendar_year,
    c.cutoff_date,
    g.display_order,
    g.group_label,
    w.observed_monthly_snapshots,
    w.average_active_regular_employees,
    COALESCE(a.cohort_employees, 0) AS cohort_employees,
    a.post_event_voluntary_attrition_percent
  FROM august_cutoffs c
  JOIN ytd_workforce w
    ON w.calendar_year = c.calendar_year
  CROSS JOIN group_order g
  LEFT JOIN aggregates a
    ON a.calendar_year = c.calendar_year
   AND a.group_label = g.group_label
)
SELECT
  calendar_year,
  cutoff_date,
  observed_monthly_snapshots,
  ROUND(average_active_regular_employees, 0) AS ytd_average_scoped_critical_tech_workforce,
  group_label,
  cohort_employees AS cohort_n,
  ROUND(
    100.0 * cohort_employees / average_active_regular_employees,
    1
  ) AS workforce_share_percent,
  post_event_voluntary_attrition_percent AS post_event_voluntary_attrition_percent,
  CASE
    WHEN cohort_employees >= 30 THEN 'publish'
    ELSE 'internal_analysis_exception'
  END AS publication_status
FROM published
ORDER BY calendar_year, display_order;
