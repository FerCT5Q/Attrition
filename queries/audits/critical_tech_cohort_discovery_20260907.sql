/*
  Descubrimiento de cohortes agregadas para Critical Tech.

  Pregunta:
    ¿Qué combinaciones interpretables de rol, nivel, tenure, geografía,
    work arrangement y eventos recientes muestran una tasa de attrition
    voluntario a seis meses superior al baseline de Critical Tech?

  Población:
    worker_type='Employee', employee_type='Regular', active_status=1, con
    job_family normalizado coincidente con el catálogo vigente
    hrda.critical_tech.

  Grain:
    Una exposición employee-snapshot mensual. El target vale 1 si existe un
    evento Voluntary estrictamente después del snapshot y hasta seis meses
    después.

  Fecha de conocimiento:
    2026-09-07. Sólo se usan snapshots cuyo horizonte completo de seis meses
    termina en esa fecha. El catálogo vigente se usa como filtro exploratorio;
    la membership histórica del archive aún requiere reconciliación.

  Reglas de publicación:
    - Al menos 30 employee-snapshots y 30 empleados distintos por cohorte.
    - Al menos 30 targets positivos antes de publicar tasa y lift.
    - Se reportan combinaciones con lift calculado, pero "prioritaria" exige
      lift >= 1.25, al menos 100 empleados y estabilidad en dos periodos.
    - Los periodos internos con menos de 30 eventos nunca se devuelven.

  Privacidad:
    employee_id sólo se usa dentro de joins y COUNT(DISTINCT). No se devuelve
    ningún identificador, nombre, atributo protegido, texto libre o importe.
*/
WITH params AS (
  SELECT DATE '2026-09-07' AS knowledge_boundary
),
critical_map AS (
  SELECT
    TRIM(LOWER(extended_job_family)) AS family_key,
    MAX(NULLIF(TRIM(seg), '')) AS seg
  FROM hrda.critical_tech
  WHERE extended_job_family IS NOT NULL
    AND TRIM(extended_job_family) <> ''
  GROUP BY 1
),
raw_scope AS (
  SELECT
    CAST(p.fis_mo_end_dt AS DATE) AS snapshot_date,
    p.employee_id,
    COALESCE(NULLIF(TRIM(p.job_family), ''), '(unknown)') AS job_family,
    COALESCE(NULLIF(TRIM(p.job_family_group), ''), '(unknown)') AS job_family_group,
    COALESCE(NULLIF(TRIM(p.level_grouped), ''), '(unknown)') AS level_grouped,
    COALESCE(NULLIF(TRIM(p.management_level), ''), '(unknown)') AS management_level,
    COALESCE(NULLIF(TRIM(p.region), ''), '(unknown)') AS region,
    COALESCE(NULLIF(TRIM(p.labor_market), ''), '(unknown)') AS labor_market,
    CASE
      WHEN UPPER(TRIM(CAST(p.work_arrangement AS VARCHAR(256)))) LIKE 'INTERIM MODIFIED%'
        THEN '(restricted work arrangement)'
      ELSE COALESCE(NULLIF(TRIM(p.work_arrangement), ''), '(unknown)')
    END AS work_arrangement,
    p.original_hire_date,
    p.manager_change,
    p.manager_change_date,
    p.is_promo,
    p.promotion_date,
    p.is_transferred,
    p.transfer_date,
    c.seg
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
key_quality AS (
  SELECT
    snapshot_date,
    employee_id,
    COUNT(DISTINCT job_family) AS family_values,
    COUNT(DISTINCT level_grouped) AS level_values,
    COUNT(DISTINCT region) AS region_values,
    COUNT(DISTINCT work_arrangement) AS work_arrangement_values
  FROM raw_scope
  GROUP BY 1, 2
),
base_snapshots AS (
  SELECT DISTINCT
    r.snapshot_date,
    r.employee_id,
    r.job_family,
    r.job_family_group,
    r.level_grouped,
    r.management_level,
    r.region,
    r.labor_market,
    r.work_arrangement,
    r.original_hire_date,
    r.manager_change,
    r.manager_change_date,
    r.is_promo,
    r.promotion_date,
    r.is_transferred,
    r.transfer_date,
    r.seg
  FROM raw_scope r
  INNER JOIN key_quality q
    ON q.snapshot_date = r.snapshot_date
   AND q.employee_id = r.employee_id
   AND q.family_values <= 1
   AND q.level_values <= 1
   AND q.region_values <= 1
   AND q.work_arrangement_values <= 1
),
voluntary_events AS (
  SELECT
    employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  CROSS JOIN params x
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
    AND CAST(term_date AS DATE) <= x.knowledge_boundary
  GROUP BY 1, 2
),
target_flags AS (
  SELECT
    b.snapshot_date,
    b.employee_id,
    MAX(
      CASE
        WHEN v.employee_id IS NOT NULL THEN 1
        ELSE 0
      END
    ) AS voluntary_attrition_6m
  FROM base_snapshots b
  LEFT JOIN voluntary_events v
    ON v.employee_id = b.employee_id
   AND v.term_date > b.snapshot_date
   AND v.term_date <= CAST(DATEADD(month, 6, b.snapshot_date) AS DATE)
  GROUP BY 1, 2
),
labeled AS (
  SELECT
    b.snapshot_date,
    b.employee_id,
    b.job_family,
    b.job_family_group,
    b.level_grouped,
    b.management_level,
    b.region,
    b.labor_market,
    b.work_arrangement,
    b.original_hire_date,
    b.manager_change,
    b.manager_change_date,
    b.is_promo,
    b.promotion_date,
    b.is_transferred,
    b.transfer_date,
    b.seg,
    t.voluntary_attrition_6m,
    CASE
      WHEN b.original_hire_date IS NULL
        OR b.original_hire_date > b.snapshot_date
        THEN '(unknown)'
      WHEN DATEDIFF(month, b.original_hire_date, b.snapshot_date) < 12
        THEN '<1 year'
      WHEN DATEDIFF(month, b.original_hire_date, b.snapshot_date) < 36
        THEN '1-3 years'
      WHEN DATEDIFF(month, b.original_hire_date, b.snapshot_date) < 84
        THEN '3-7 years'
      ELSE '7+ years'
    END AS company_tenure_band,
    CASE
      WHEN b.manager_change = 1
       AND b.manager_change_date IS NOT NULL
       AND b.manager_change_date > CAST(DATEADD(month, -12, b.snapshot_date) AS DATE)
       AND b.manager_change_date <= b.snapshot_date
        THEN 'manager change: yes'
      WHEN b.manager_change IS NULL OR b.manager_change_date IS NULL
        THEN 'manager change: unknown'
      ELSE 'manager change: no'
    END AS manager_change_12m,
    CASE
      WHEN b.is_promo = 1
       AND b.promotion_date IS NOT NULL
       AND b.promotion_date > CAST(DATEADD(month, -12, b.snapshot_date) AS DATE)
       AND b.promotion_date <= b.snapshot_date
        THEN 'promotion: yes'
      WHEN b.is_promo IS NULL OR b.promotion_date IS NULL
        THEN 'promotion: unknown'
      ELSE 'promotion: no'
    END AS promotion_12m,
    CASE
      WHEN b.is_transferred = 1
       AND b.transfer_date IS NOT NULL
       AND b.transfer_date > CAST(DATEADD(month, -12, b.snapshot_date) AS DATE)
       AND b.transfer_date <= b.snapshot_date
        THEN 'transfer: yes'
      WHEN b.is_transferred IS NULL OR b.transfer_date IS NULL
        THEN 'transfer: unknown'
      ELSE 'transfer: no'
    END AS transfer_12m
  FROM base_snapshots b
  INNER JOIN target_flags t
    ON t.snapshot_date = b.snapshot_date
   AND t.employee_id = b.employee_id
),
cohort_rows AS (
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'segment' AS cohort_axis, seg AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'job_family' AS cohort_axis, job_family AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'job_family_group' AS cohort_axis, job_family_group AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'level_grouped' AS cohort_axis, level_grouped AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'management_level' AS cohort_axis, management_level AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'company_tenure_band' AS cohort_axis, company_tenure_band AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'region' AS cohort_axis, region AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'labor_market' AS cohort_axis, labor_market AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'work_arrangement' AS cohort_axis, work_arrangement AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'manager_change_12m' AS cohort_axis, manager_change_12m AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'promotion_12m' AS cohort_axis, promotion_12m AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'transfer_12m' AS cohort_axis, transfer_12m AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'segment_x_level' AS cohort_axis,
         seg || ' | level=' || level_grouped AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'segment_x_tenure' AS cohort_axis,
         seg || ' | tenure=' || company_tenure_band AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'segment_x_work_arrangement' AS cohort_axis,
         seg || ' | work=' || work_arrangement AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'segment_x_manager_change' AS cohort_axis,
         seg || ' | ' || manager_change_12m AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'segment_x_promotion' AS cohort_axis,
         seg || ' | ' || promotion_12m AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'segment_x_transfer' AS cohort_axis,
         seg || ' | ' || transfer_12m AS cohort_value
  FROM labeled
  UNION ALL
  SELECT snapshot_date, employee_id, voluntary_attrition_6m,
         'job_family_x_level' AS cohort_axis,
         job_family || ' | level=' || level_grouped AS cohort_value
  FROM labeled
),
overall AS (
  SELECT
    COUNT(*) AS all_snapshot_rows,
    COUNT(DISTINCT employee_id) AS all_distinct_employees,
    SUM(voluntary_attrition_6m) AS all_positive_rows,
    100.0 * SUM(voluntary_attrition_6m) / NULLIF(COUNT(*), 0)
      AS all_rate_percent
  FROM labeled
),
cohort_summary AS (
  SELECT
    cohort_axis,
    cohort_value,
    COUNT(*) AS snapshot_rows,
    COUNT(DISTINCT employee_id) AS distinct_employees,
    SUM(voluntary_attrition_6m) AS positive_target_rows,
    MIN(snapshot_date) AS first_snapshot,
    MAX(snapshot_date) AS last_snapshot,
    100.0 * SUM(voluntary_attrition_6m) / NULLIF(COUNT(*), 0)
      AS target_rate_percent
  FROM cohort_rows
  GROUP BY 1, 2
),
period_summary AS (
  SELECT
    cohort_axis,
    cohort_value,
    CASE WHEN snapshot_date < DATE '2025-01-01' THEN 'early' ELSE 'late' END
      AS period_label,
    COUNT(*) AS period_snapshot_rows,
    SUM(voluntary_attrition_6m) AS period_positive_rows,
    100.0 * SUM(voluntary_attrition_6m) / NULLIF(COUNT(*), 0)
      AS period_rate_percent
  FROM cohort_rows
  GROUP BY 1, 2, 3
),
stability AS (
  SELECT
    cohort_axis,
    cohort_value,
    COUNT(*) AS periods_observed,
    SUM(CASE WHEN period_positive_rows >= 30 THEN 1 ELSE 0 END)
      AS periods_with_30_positive,
    MIN(CASE WHEN period_positive_rows >= 30 THEN period_rate_percent END)
      AS minimum_reportable_period_rate,
    MAX(CASE WHEN period_positive_rows >= 30 THEN period_rate_percent END)
      AS maximum_reportable_period_rate
  FROM period_summary
  GROUP BY 1, 2
),
scored AS (
  SELECT
    c.cohort_axis,
    c.cohort_value,
    c.snapshot_rows,
    c.distinct_employees,
    CASE WHEN c.positive_target_rows >= 30 THEN c.positive_target_rows END
      AS positive_target_rows,
    CASE WHEN c.positive_target_rows >= 30
         THEN ROUND(c.target_rate_percent, 4) END AS target_rate_percent,
    ROUND(o.all_rate_percent, 4) AS critical_tech_rate_percent,
    CASE WHEN c.positive_target_rows >= 30
         THEN ROUND(c.target_rate_percent / NULLIF(o.all_rate_percent, 0), 4) END
      AS lift_vs_critical_tech,
    c.first_snapshot,
    c.last_snapshot,
    s.periods_observed,
    s.periods_with_30_positive,
    CASE WHEN s.periods_with_30_positive >= 2
         THEN ROUND(s.maximum_reportable_period_rate - s.minimum_reportable_period_rate, 4)
    END AS reportable_period_rate_range_pp,
    CASE
      WHEN LOWER(c.cohort_value) LIKE '%unknown%'
        THEN 'review_data_quality'
      WHEN c.positive_target_rows < 30 THEN 'suppressed_for_privacy'
      WHEN s.periods_with_30_positive >= 2
       AND s.maximum_reportable_period_rate - s.minimum_reportable_period_rate <= 5
        THEN 'consistent_screen'
      ELSE 'review_temporal_stability'
    END AS stability_status,
    CASE
      WHEN LOWER(c.cohort_value) LIKE '%unknown%' THEN 'review_data_quality'
      WHEN c.positive_target_rows >= 30
       AND c.distinct_employees >= 100
       AND c.target_rate_percent / NULLIF(o.all_rate_percent, 0) >= 1.25
       AND s.periods_with_30_positive >= 2
       AND s.maximum_reportable_period_rate - s.minimum_reportable_period_rate <= 5
        THEN 'prioritaria_para_validacion'
      WHEN c.positive_target_rows >= 30
       AND c.target_rate_percent / NULLIF(o.all_rate_percent, 0) >= 1.25
        THEN 'hipotesis_accionable'
      ELSE 'referencia'
    END AS priority_status
  FROM cohort_summary c
  CROSS JOIN overall o
  INNER JOIN stability s
    ON s.cohort_axis = c.cohort_axis
   AND s.cohort_value = c.cohort_value
  WHERE c.snapshot_rows >= 30
    AND c.distinct_employees >= 30
)
SELECT
  cohort_axis,
  cohort_value,
  snapshot_rows,
  distinct_employees,
  positive_target_rows,
  target_rate_percent,
  critical_tech_rate_percent,
  lift_vs_critical_tech,
  first_snapshot,
  last_snapshot,
  periods_observed,
  periods_with_30_positive,
  reportable_period_rate_range_pp,
  stability_status,
  priority_status
FROM scored
WHERE positive_target_rows IS NOT NULL
ORDER BY
  CASE WHEN priority_status = 'prioritaria_para_validacion' THEN 1
       WHEN priority_status = 'hipotesis_accionable' THEN 2
       ELSE 3 END,
  lift_vs_critical_tech DESC NULLS LAST,
  positive_target_rows DESC,
  distinct_employees DESC,
  cohort_axis,
  cohort_value;
