/*
  Frame persona-mes para la selección de variables por bloques (2026-10-01).

  Uso: sólo en memoria, bajo
  config/attrition_model_in_memory_training_authorization_20261001.json.
  El runner reemplaza __PERIOD_START__ y __PERIOD_END__ y lee el resultado
  en lotes; no se escribe a disco. La salida NO contiene employee_id,
  manager_employee_id ni compa_ratio: los IDs se usan sólo en joins y la
  compensación sale únicamente en bandas.

  Población: Employee, Regular, active_status=1, is_rf360_yes_no=0,
  eng_or_noneng='Engineering' en la foto t.

  Etiquetas:
    y_next: salida VOLUNTARY en (t, siguiente foto]; NULL si la siguiente foto
            supera la frontera de conocimiento.
    y_6m:   salida VOLUNTARY en (t, t+6 meses]; NULL si t+6m supera la frontera.

  Variables (todas con información <= t):
    level_grouped, company_tenure_band (base del modelo vigente).
    promo_12m: is_promo=1 con promotion_date en (t-12m, t] en una foto <= t
      (queries/audits/engineering_promotion_history_by_year_20261001.sql).
    manager_changes_12m: fechas distintas de manager_change_date con
      manager_change=1 en (t-12m, t] observadas en fotos <= t (0/1/2+)
      (queries/audits/manager_change_flag_vs_date_engineering_20261001.sql).
    team_exits_12m: salidas voluntarias en (t-12m, t] de personas cuyo
      manager en su última foto previa a la salida es el manager actual (0/1/2+).
    direct_reports_band: reg_non_intern_dir_reports en t (0/1-5/6+).
    region: región en t.
    comp_ratio_band: bandas de compa_ratio en t.
    grade_family: primera letra de compensation_grade en t.
  Historia: la tabla empieza en 2020-07; las ventanas de 12 meses sólo están
  completas desde 2021-07, por eso el runner pide fotos >= 2021-07-25.
*/
WITH params AS (
  SELECT
    DATE '__PERIOD_START__' AS period_start,
    DATE '__PERIOD_END__' AS period_end,
    DATE '2026-09-07' AS knowledge_boundary
),
snapshot_calendar AS (
  SELECT
    snapshot_date,
    LEAD(snapshot_date) OVER (ORDER BY snapshot_date) AS next_snapshot_date
  FROM (
    SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
      AND CAST(fis_mo_end_dt AS DATE) <= (SELECT knowledge_boundary FROM params)
  ) dates
),
pop AS (
  SELECT
    c.snapshot_date,
    c.next_snapshot_date,
    p.employee_id,
    MAX(p.manager_employee_id) AS manager_id,
    MAX(NULLIF(TRIM(p.level_grouped), '')) AS level_grouped,
    MAX(CAST(p.original_hire_date AS DATE)) AS original_hire_date,
    MAX(p.compa_ratio) AS cr,
    MAX(NULLIF(TRIM(p.compensation_grade), '')) AS grade,
    MAX(NULLIF(TRIM(p.region), '')) AS region,
    MAX(p.reg_non_intern_dir_reports) AS dir_reports
  FROM snapshot_calendar c
  INNER JOIN hrda.post_hire_monthly_worker_dtls p
    ON CAST(p.fis_mo_end_dt AS DATE) = c.snapshot_date
  WHERE c.next_snapshot_date IS NOT NULL
    AND c.snapshot_date >= (SELECT period_start FROM params)
    AND c.snapshot_date <= (SELECT period_end FROM params)
    AND p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
    AND p.is_rf360_yes_no = 0
    AND TRIM(p.eng_or_noneng) = 'Engineering'
    AND p.employee_id IS NOT NULL
  GROUP BY 1, 2, 3
),
history AS (
  SELECT
    h.employee_id,
    CAST(h.fis_mo_end_dt AS DATE) AS row_date,
    h.is_promo,
    CAST(h.promotion_date AS DATE) AS promotion_date,
    h.manager_change,
    CAST(h.manager_change_date AS DATE) AS manager_change_date
  FROM hrda.post_hire_monthly_worker_dtls h
  WHERE h.worker_type = 'Employee'
    AND h.employee_type = 'Regular'
    AND CAST(h.fis_mo_end_dt AS DATE) > DATEADD(month, -12, (SELECT period_start FROM params))
    AND CAST(h.fis_mo_end_dt AS DATE) <= (SELECT period_end FROM params)
    AND (h.is_promo = 1 OR h.manager_change = 1)
    AND h.employee_id IN (SELECT employee_id FROM pop)
),
promo AS (
  SELECT p.snapshot_date, p.employee_id, COUNT(DISTINCT h.promotion_date) AS promotions
  FROM pop p
  INNER JOIN history h
    ON h.employee_id = p.employee_id
   AND h.is_promo = 1
   AND h.row_date <= p.snapshot_date
   AND h.promotion_date > DATEADD(month, -12, p.snapshot_date)
   AND h.promotion_date <= p.snapshot_date
  GROUP BY 1, 2
),
manager_moves AS (
  SELECT p.snapshot_date, p.employee_id, COUNT(DISTINCT h.manager_change_date) AS changes
  FROM pop p
  INNER JOIN history h
    ON h.employee_id = p.employee_id
   AND h.manager_change = 1
   AND h.row_date <= p.snapshot_date
   AND h.manager_change_date > DATEADD(month, -12, p.snapshot_date)
   AND h.manager_change_date <= p.snapshot_date
  GROUP BY 1, 2
),
voluntary_events AS (
  SELECT employee_id, CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(term_type::VARCHAR), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
    AND CAST(term_date AS DATE) <= (SELECT knowledge_boundary FROM params)
  GROUP BY 1, 2
),
recent_exits AS (
  SELECT employee_id, term_date
  FROM voluntary_events
  WHERE term_date > DATEADD(month, -12, (SELECT period_start FROM params))
    AND term_date <= (SELECT period_end FROM params)
),
exit_manager AS (
  SELECT employee_id, term_date, manager_id
  FROM (
    SELECT
      e.employee_id,
      e.term_date,
      w.manager_employee_id AS manager_id,
      ROW_NUMBER() OVER (
        PARTITION BY e.employee_id, e.term_date
        ORDER BY CAST(w.fis_mo_end_dt AS DATE) DESC
      ) AS rn
    FROM recent_exits e
    INNER JOIN hrda.post_hire_monthly_worker_dtls w
      ON w.employee_id = e.employee_id
     AND CAST(w.fis_mo_end_dt AS DATE) < e.term_date
     AND CAST(w.fis_mo_end_dt AS DATE) >= DATEADD(month, -3, e.term_date)
     AND w.active_status = 1
     AND w.manager_employee_id IS NOT NULL
  ) ranked
  WHERE rn = 1
),
team_exits AS (
  SELECT p.snapshot_date, p.employee_id, COUNT(*) AS exits
  FROM pop p
  INNER JOIN exit_manager x
    ON x.manager_id = p.manager_id
   AND x.employee_id <> p.employee_id
   AND x.term_date > DATEADD(month, -12, p.snapshot_date)
   AND x.term_date <= p.snapshot_date
  GROUP BY 1, 2
),
labels AS (
  SELECT
    p.snapshot_date,
    p.employee_id,
    MAX(CASE WHEN v.term_date <= p.next_snapshot_date THEN 1 ELSE 0 END) AS hit_next,
    MAX(CASE WHEN v.term_date <= DATEADD(month, 6, p.snapshot_date) THEN 1 ELSE 0 END) AS hit_6m
  FROM pop p
  INNER JOIN voluntary_events v
    ON v.employee_id = p.employee_id
   AND v.term_date > p.snapshot_date
   AND v.term_date <= DATEADD(month, 6, p.snapshot_date)
  GROUP BY 1, 2
)
SELECT
  p.snapshot_date,
  COALESCE(p.level_grouped, '(unknown)') AS level_grouped,
  CASE
    WHEN p.original_hire_date IS NULL OR p.original_hire_date > p.snapshot_date THEN '(unknown)'
    WHEN DATEDIFF(month, p.original_hire_date, p.snapshot_date) < 12 THEN '<1 year'
    WHEN DATEDIFF(month, p.original_hire_date, p.snapshot_date) < 36 THEN '1-3 years'
    WHEN DATEDIFF(month, p.original_hire_date, p.snapshot_date) < 84 THEN '3-7 years'
    ELSE '7+ years'
  END AS company_tenure_band,
  CASE WHEN COALESCE(pr.promotions, 0) > 0 THEN 'yes' ELSE 'no' END AS promo_12m,
  CASE
    WHEN COALESCE(mm.changes, 0) = 0 THEN '0'
    WHEN mm.changes = 1 THEN '1'
    ELSE '2+'
  END AS manager_changes_12m,
  CASE
    WHEN p.manager_id IS NULL THEN '(unknown)'
    WHEN COALESCE(te.exits, 0) = 0 THEN '0'
    WHEN te.exits = 1 THEN '1'
    ELSE '2+'
  END AS team_exits_12m,
  CASE
    WHEN p.dir_reports IS NULL THEN '(unknown)'
    WHEN p.dir_reports = 0 THEN '0'
    WHEN p.dir_reports <= 5 THEN '1-5'
    ELSE '6+'
  END AS direct_reports_band,
  COALESCE(p.region, '(unknown)') AS region,
  CASE
    WHEN p.cr IS NULL OR p.cr <= 0 THEN '(unknown)'
    WHEN p.cr < 0.8 THEN '<0.8'
    WHEN p.cr < 0.9 THEN '0.8-0.9'
    WHEN p.cr < 1.0 THEN '0.9-1.0'
    WHEN p.cr < 1.1 THEN '1.0-1.1'
    WHEN p.cr < 1.2 THEN '1.1-1.2'
    ELSE '1.2+'
  END AS comp_ratio_band,
  CASE
    WHEN p.grade LIKE 'R%' THEN 'R'
    WHEN p.grade LIKE 'T%' THEN 'T'
    WHEN p.grade IS NULL THEN '(unknown)'
    ELSE 'other'
  END AS grade_family,
  CASE
    WHEN p.next_snapshot_date > (SELECT knowledge_boundary FROM params) THEN NULL
    ELSE COALESCE(l.hit_next, 0)
  END AS y_next,
  CASE
    WHEN DATEADD(month, 6, p.snapshot_date) > (SELECT knowledge_boundary FROM params) THEN NULL
    ELSE COALESCE(l.hit_6m, 0)
  END AS y_6m
FROM pop p
LEFT JOIN promo pr ON pr.snapshot_date = p.snapshot_date AND pr.employee_id = p.employee_id
LEFT JOIN manager_moves mm ON mm.snapshot_date = p.snapshot_date AND mm.employee_id = p.employee_id
LEFT JOIN team_exits te ON te.snapshot_date = p.snapshot_date AND te.employee_id = p.employee_id
LEFT JOIN labels l ON l.snapshot_date = p.snapshot_date AND l.employee_id = p.employee_id
