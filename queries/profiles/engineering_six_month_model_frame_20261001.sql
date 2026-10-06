/*
  Población del modelo (2026-10-01): Employee, Regular, active_status=1,
  is_rf360_yes_no=0 y eng_or_noneng='Engineering' en cada foto. Sustituye el
  match con hrda.critical_tech: job_family se reasignó el 2026-09-01 y
  eng_or_noneng no cambió (queries/audits/eng_or_noneng_reassignment_flips_20261001.sql).
  La columna seg queda constante ('Engineering') por compatibilidad.
*/
/*
  Frame agregado para el benchmark directo a seis meses y la evaluación del
  riesgo acumulado del hazard mensual.

  El runner reemplaza __PERIOD_START__ y __PERIOD_END__. La salida es una
  celda agregada; employee_id se usa sólo internamente para deduplicar.
  Voluntary Exception queda fuera del target primario hasta confirmación de
  negocio.
*/
WITH params AS (
  SELECT
    DATE '__PERIOD_START__' AS period_start,
    DATE '__PERIOD_END__' AS period_end,
    DATE '2026-09-07' AS knowledge_boundary
),
snapshot_dates AS (
  SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE)
      <= (SELECT knowledge_boundary FROM params)
),
raw_scope AS (
  SELECT
    d.snapshot_date,
    p.employee_id,
    p.level_grouped,
    p.original_hire_date,
    p.manager_change,
    p.manager_change_date,
    'Engineering' AS seg
  FROM snapshot_dates d
  INNER JOIN hrda.post_hire_monthly_worker_dtls p
    ON CAST(p.fis_mo_end_dt AS DATE) = d.snapshot_date
  WHERE d.snapshot_date >= (SELECT period_start FROM params)
    AND d.snapshot_date <= (SELECT period_end FROM params)
    AND DATEADD(month, 6, d.snapshot_date)
      <= (SELECT knowledge_boundary FROM params)
    AND p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
    AND p.is_rf360_yes_no = 0
    AND TRIM(p.eng_or_noneng) = 'Engineering'
),
base_snapshots AS (
  SELECT DISTINCT
    snapshot_date,
    employee_id,
    COALESCE(NULLIF(TRIM(level_grouped), ''), '(unknown)')
      AS level_grouped,
    CASE
      WHEN original_hire_date IS NULL OR original_hire_date > snapshot_date
        THEN '(unknown)'
      WHEN DATEDIFF(month, original_hire_date, snapshot_date) < 12
        THEN '<1 year'
      WHEN DATEDIFF(month, original_hire_date, snapshot_date) < 36
        THEN '1-3 years'
      WHEN DATEDIFF(month, original_hire_date, snapshot_date) < 84
        THEN '3-7 years'
      ELSE '7+ years'
    END AS company_tenure_band,
    CASE
      WHEN manager_change = 1
       AND manager_change_date IS NOT NULL
       AND manager_change_date > DATEADD(month, -12, snapshot_date)
       AND manager_change_date <= snapshot_date
        THEN 'yes'
      WHEN manager_change IS NULL OR manager_change_date IS NULL
        THEN 'unknown'
      ELSE 'no'
    END AS manager_change_12m,
    COALESCE(NULLIF(TRIM(seg), ''), '(unknown)') AS seg
  FROM raw_scope
),
voluntary_events AS (
  SELECT
    employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(term_type::VARCHAR), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
    AND CAST(term_date AS DATE)
      <= (SELECT knowledge_boundary FROM params)
  GROUP BY 1, 2
),
labeled AS (
  SELECT
    b.snapshot_date,
    b.employee_id,
    b.level_grouped,
    b.company_tenure_band,
    b.manager_change_12m,
    b.seg,
    MAX(
      CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END
    ) AS voluntary_attrition_6m
  FROM base_snapshots b
  LEFT JOIN voluntary_events v
    ON v.employee_id = b.employee_id
   AND v.term_date > b.snapshot_date
   AND v.term_date <= DATEADD(month, 6, b.snapshot_date)
  GROUP BY 1, 2, 3, 4, 5, 6
)
SELECT
  snapshot_date,
  seg,
  level_grouped,
  company_tenure_band,
  manager_change_12m,
  COUNT(*) AS exposure_count,
  COUNT(DISTINCT employee_id) AS distinct_employee_count,
  SUM(voluntary_attrition_6m) AS event_count
FROM labeled
GROUP BY 1, 2, 3, 4, 5
ORDER BY 1, 2, 3, 4, 5;
