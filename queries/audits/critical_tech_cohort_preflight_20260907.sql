/*
  Preflight agregado para descubrimiento de cohortes en Critical Tech.

  Objetivo:
    Confirmar que el snapshot mensual puede convertirse en una base de
    employee-snapshot sin inflar la exposición y revisar la observabilidad de
    las dimensiones candidatas antes de calcular tasas de attrition.

  Población:
    worker_type='Employee', employee_type='Regular', active_status=1, con
    job_family normalizado coincidente con hrda.critical_tech.

  Ventana:
    Sólo snapshots cuyo horizonte de seis meses termina en 2026-09-07. Se
    excluyen snapshots posteriores a la fecha de conocimiento.

  Privacidad:
    employee_id sólo se usa dentro de COUNT/GROUP BY internos. No se devuelven
    filas de empleados ni valores de identidad.
*/
WITH params AS (
  SELECT DATE '2026-09-07' AS knowledge_boundary
),
critical_map AS (
  SELECT
    TRIM(LOWER(extended_job_family)) AS family_key
  FROM hrda.critical_tech
  WHERE extended_job_family IS NOT NULL
    AND TRIM(extended_job_family) <> ''
  GROUP BY 1
),
scoped_rows AS (
  SELECT
    CAST(p.fis_mo_end_dt AS DATE) AS snapshot_date,
    p.employee_id,
    p.job_family,
    p.job_family_group,
    p.level_grouped,
    p.management_level,
    p.region,
    p.labor_market,
    p.work_arrangement,
    p.original_hire_date,
    p.manager_change,
    p.manager_change_date,
    p.is_promo,
    p.promotion_date,
    p.is_transferred,
    p.transfer_date
  FROM hrda.post_hire_monthly_worker_dtls p
  CROSS JOIN params x
  INNER JOIN critical_map c
    ON TRIM(LOWER(p.job_family)) = c.family_key
  WHERE p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
    AND p.fis_mo_end_dt IS NOT NULL
    AND CAST(p.fis_mo_end_dt AS DATE) <= x.knowledge_boundary
    AND CAST(DATEADD(month, 6, CAST(p.fis_mo_end_dt AS DATE)) AS DATE)
        <= x.knowledge_boundary
),
per_snapshot AS (
  SELECT
    snapshot_date,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT employee_id) AS distinct_employees,
    COUNT(*) - COUNT(DISTINCT employee_id) AS duplicate_rows,
    COUNT(DISTINCT NULLIF(TRIM(job_family), '')) AS job_family_values,
    COUNT(DISTINCT NULLIF(TRIM(job_family_group), '')) AS job_family_group_values,
    COUNT(DISTINCT NULLIF(TRIM(level_grouped), '')) AS level_grouped_values,
    COUNT(DISTINCT NULLIF(TRIM(management_level), '')) AS management_level_values,
    COUNT(DISTINCT NULLIF(TRIM(region), '')) AS region_values,
    COUNT(DISTINCT NULLIF(TRIM(labor_market), '')) AS labor_market_values,
    COUNT(DISTINCT NULLIF(TRIM(work_arrangement), '')) AS work_arrangement_values,
    COUNT(CASE WHEN original_hire_date IS NOT NULL THEN 1 END) AS tenure_observable_rows,
    COUNT(CASE WHEN manager_change IS NOT NULL THEN 1 END) AS manager_change_observable_rows,
    COUNT(CASE WHEN is_promo IS NOT NULL THEN 1 END) AS promotion_observable_rows,
    COUNT(CASE WHEN is_transferred IS NOT NULL THEN 1 END) AS transfer_observable_rows
  FROM scoped_rows
  GROUP BY 1
),
conflict_counts AS (
  SELECT
    COUNT(CASE WHEN family_values > 1 THEN 1 END) AS employee_date_family_conflicts,
    COUNT(CASE WHEN level_values > 1 THEN 1 END) AS employee_date_level_conflicts,
    COUNT(CASE WHEN region_values > 1 THEN 1 END) AS employee_date_region_conflicts,
    COUNT(CASE WHEN work_values > 1 THEN 1 END) AS employee_date_work_arrangement_conflicts
  FROM (
    SELECT
      snapshot_date,
      employee_id,
      COUNT(DISTINCT NULLIF(TRIM(job_family), '')) AS family_values,
      COUNT(DISTINCT NULLIF(TRIM(level_grouped), '')) AS level_values,
      COUNT(DISTINCT NULLIF(TRIM(region), '')) AS region_values,
      COUNT(DISTINCT NULLIF(TRIM(work_arrangement), '')) AS work_values
    FROM scoped_rows
    GROUP BY 1, 2
  ) q
),
summary AS (
  SELECT
    COUNT(*) AS complete_snapshot_months,
    MIN(snapshot_date) AS first_snapshot,
    MAX(snapshot_date) AS last_snapshot,
    SUM(source_rows) AS source_rows,
    SUM(distinct_employees) AS employee_snapshot_rows,
    SUM(duplicate_rows) AS duplicate_rows,
    MIN(100.0 * tenure_observable_rows / NULLIF(distinct_employees, 0))
      AS minimum_tenure_coverage_percent,
    MIN(100.0 * manager_change_observable_rows / NULLIF(distinct_employees, 0))
      AS minimum_manager_change_coverage_percent,
    MIN(100.0 * promotion_observable_rows / NULLIF(distinct_employees, 0))
      AS minimum_promotion_coverage_percent,
    MIN(100.0 * transfer_observable_rows / NULLIF(distinct_employees, 0))
      AS minimum_transfer_coverage_percent
  FROM per_snapshot
)
SELECT
  s.complete_snapshot_months,
  s.first_snapshot,
  s.last_snapshot,
  s.source_rows,
  s.employee_snapshot_rows,
  s.duplicate_rows,
  ROUND(s.minimum_tenure_coverage_percent, 4) AS minimum_tenure_coverage_percent,
  ROUND(s.minimum_manager_change_coverage_percent, 4)
    AS minimum_manager_change_coverage_percent,
  ROUND(s.minimum_promotion_coverage_percent, 4)
    AS minimum_promotion_coverage_percent,
  ROUND(s.minimum_transfer_coverage_percent, 4)
    AS minimum_transfer_coverage_percent,
  c.employee_date_family_conflicts,
  c.employee_date_level_conflicts,
  c.employee_date_region_conflicts,
  c.employee_date_work_arrangement_conflicts,
  CASE
    WHEN s.complete_snapshot_months >= 24
     AND s.duplicate_rows = 0
     AND c.employee_date_family_conflicts = 0
    THEN 'pass'
    ELSE 'review'
  END AS preflight_outcome
FROM summary s
CROSS JOIN conflict_counts c;
