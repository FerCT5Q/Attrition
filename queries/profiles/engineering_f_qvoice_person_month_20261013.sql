/* C y control B: sólo memoria, autorización 20261001. Salt efímero.
   Se conserva la última foto sin etiquetas. Salidas como features sólo tras su primera foto registrada.
   No QVoice, IDs publicables, compensación exacta ni caché de filas. */
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
    MAX(CAST(p.service_date AS DATE)) AS service_date,
    MAX(CAST(p.levelentrydate AS DATE)) AS level_entry_date,
    MAX(p.prior_qc_work_years) AS prior_years,
    MAX(p.worker_supervisory_organization_level_from_top) AS layers,
    MAX(NULLIF(TRIM(p.work_arrangement), '')) AS work_arrangement,
    MAX(p.reg_non_intern_dir_reports) AS dir_reports,
    MAX(NULLIF(TRIM(p.region), '')) AS region,
    MAX(NULLIF(UPPER(TRIM(p.country)), '')) AS work_country,
    MAX(NULLIF(UPPER(TRIM(p.city)), '')) AS work_city_raw,
    MAX(p.compa_ratio) AS cr,
    MAX(NULLIF(TRIM(p.compensation_grade), '')) AS grade,
    MAX(CASE WHEN NULLIF(TRIM(p.acquisition), '') IS NOT NULL THEN 1 ELSE 0 END) AS acquisition_recorded
  FROM snapshot_calendar c
  INNER JOIN hrda.post_hire_monthly_worker_dtls p
    ON CAST(p.fis_mo_end_dt AS DATE) = c.snapshot_date
  WHERE c.snapshot_date >= (SELECT period_start FROM params)
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
    h.is_transferred,
    CAST(h.transfer_date AS DATE) AS transfer_date,
    h.is_promo,
    CAST(h.promotion_date AS DATE) AS promotion_date,
    h.manager_change,
    CAST(h.manager_change_date AS DATE) AS manager_change_date
  FROM hrda.post_hire_monthly_worker_dtls h
  WHERE h.worker_type = 'Employee'
    AND h.employee_type = 'Regular'
    AND CAST(h.fis_mo_end_dt AS DATE) > DATEADD(month, -12, (SELECT period_start FROM params))
    AND CAST(h.fis_mo_end_dt AS DATE) <= (SELECT period_end FROM params)
    AND (h.is_promo = 1 OR h.manager_change = 1 OR h.is_transferred = 1)
    AND h.employee_id IN (SELECT employee_id FROM pop)
),
promo_history AS (
  SELECT DISTINCT
    h.employee_id,
    CAST(h.fis_mo_end_dt AS DATE) AS row_date,
    CAST(h.promotion_date AS DATE) AS promotion_date
  FROM hrda.post_hire_monthly_worker_dtls h
  WHERE h.worker_type = 'Employee'
    AND h.employee_type = 'Regular'
    AND h.is_promo = 1
    AND h.promotion_date IS NOT NULL
    AND CAST(h.fis_mo_end_dt AS DATE) <= (SELECT period_end FROM params)
    AND h.employee_id IN (SELECT employee_id FROM pop)
),
last_promo AS (
  SELECT p.snapshot_date, p.employee_id, MAX(h.promotion_date) AS last_promotion_date
  FROM pop p
  INNER JOIN promo_history h
    ON h.employee_id = p.employee_id
   AND h.row_date <= p.snapshot_date
   AND h.promotion_date <= p.snapshot_date
   AND (p.service_date IS NULL OR h.promotion_date >= p.service_date)
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
transfer_events AS (
  SELECT p.snapshot_date, p.employee_id, 1 AS transfer_12m
  FROM pop p INNER JOIN history h ON h.employee_id = p.employee_id
   AND h.is_transferred = 1 AND h.row_date <= p.snapshot_date
   AND h.transfer_date > DATEADD(month, -12, p.snapshot_date)
   AND h.transfer_date <= p.snapshot_date
   AND (p.service_date IS NULL OR h.transfer_date >= p.service_date)
  GROUP BY 1, 2
),
voluntary_events AS (
  SELECT employee_id, CAST(term_date AS DATE) AS term_date, MIN(CAST(fis_mo_end_dt AS DATE)) AS known_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(term_type::VARCHAR), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
    AND CAST(term_date AS DATE) <= (SELECT knowledge_boundary FROM params)
  GROUP BY 1, 2
),
recent_exits AS (
  SELECT employee_id, term_date, known_date
  FROM voluntary_events
  WHERE term_date > DATEADD(month, -12, (SELECT period_start FROM params))
    AND term_date <= (SELECT period_end FROM params)
),
exit_manager AS (
  SELECT employee_id, term_date, manager_id, known_date
  FROM (
    SELECT
      e.employee_id,
      e.term_date, e.known_date,
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
   AND x.known_date <= p.snapshot_date
  GROUP BY 1, 2
),
leaver_snapshot AS (
  -- Última foto dentro de los 45 días previos a la salida del manager.
  SELECT e.employee_id AS leaver_id, e.term_date, MIN(e.known_date) AS known_date, MAX(c.snapshot_date) AS ref_snapshot
  FROM recent_exits e
  INNER JOIN snapshot_calendar c
    ON c.snapshot_date < e.term_date
   AND c.snapshot_date >= DATEADD(day, -45, e.term_date)
  WHERE e.term_date > DATEADD(month, -6, (SELECT period_start FROM params))
  GROUP BY 1, 2
),
leaving_managers AS (
  SELECT s.leaver_id, s.term_date, s.ref_snapshot, MIN(s.known_date) AS known_date
  FROM leaver_snapshot s
  INNER JOIN hrda.post_hire_monthly_worker_dtls m
    ON m.employee_id = s.leaver_id
   AND CAST(m.fis_mo_end_dt AS DATE) = s.ref_snapshot
  GROUP BY 1, 2, 3
  HAVING MAX(m.reg_non_intern_dir_reports) > 0
),
left_reports AS (
  SELECT DISTINCT r.employee_id, l.term_date, l.known_date
  FROM leaving_managers l
  INNER JOIN hrda.post_hire_monthly_worker_dtls r
    ON r.manager_employee_id = l.leaver_id
   AND CAST(r.fis_mo_end_dt AS DATE) = l.ref_snapshot
   AND r.employee_id <> l.leaver_id
  WHERE r.employee_id IN (SELECT employee_id FROM pop)
),
manager_left AS (
  SELECT p.snapshot_date, p.employee_id, 1 AS manager_left
  FROM pop p
  INNER JOIN left_reports r
    ON r.employee_id = p.employee_id
   AND r.term_date > DATEADD(month, -6, p.snapshot_date)
   AND r.term_date <= p.snapshot_date
   AND r.known_date <= p.snapshot_date
  GROUP BY 1, 2
),
ios AS (
  SELECT
    p.snapshot_date,
    p.employee_id,
    MAX(CASE WHEN TRIM(t.business_process_reason) NOT LIKE '%Reorg Department and/or Manager Change%' THEN 1 ELSE 0 END) AS other_move,
    COUNT(*) AS moves
  FROM pop p
  INNER JOIN hrda.workers_ios_transfers t
    ON t.employee_id = p.employee_id
   AND t.effective_date > DATEADD(month, -12, p.snapshot_date)
   AND t.effective_date <= p.snapshot_date
   AND NULLIF(TRIM(t.business_process_reason), '') IS NOT NULL
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
),
features AS (
  SELECT
    p.snapshot_date,
    p.next_snapshot_date,
    p.employee_id,
    p.manager_id,
    p.level_grouped,
    p.original_hire_date,
    p.service_date,
    p.prior_years,
    p.layers,
    p.work_arrangement,
    p.dir_reports, p.region, p.work_country, p.work_city_raw,
    p.cr, p.grade, p.acquisition_recorded,
    COALESCE(tr.transfer_12m, 0) AS transfer_12m,
    CASE WHEN p.original_hire_date IS NULL OR p.original_hire_date > p.snapshot_date THEN NULL
         ELSE DATEDIFF(month, p.original_hire_date, p.snapshot_date) END AS tenure_months,
    CASE WHEN lp.last_promotion_date IS NOT NULL THEN DATEDIFF(month, lp.last_promotion_date, p.snapshot_date) END AS promo_months,
    CASE WHEN p.service_date IS NOT NULL AND p.service_date <= p.snapshot_date
         THEN DATEDIFF(month, p.service_date, p.snapshot_date) END AS hire_months,
    CASE WHEN p.level_entry_date IS NOT NULL AND p.level_entry_date <= p.snapshot_date
         THEN DATEDIFF(month, GREATEST(p.level_entry_date, COALESCE(p.service_date, p.level_entry_date)), p.snapshot_date) END AS level_months,
    COALESCE(mm.changes, 0) AS mgr_changes,
    te.exits AS team_exit_count,
    COALESCE(ml.manager_left, 0) AS manager_left,
    i.moves AS ios_moves,
    i.other_move AS ios_other
  FROM pop p
  LEFT JOIN transfer_events tr ON tr.snapshot_date = p.snapshot_date AND tr.employee_id = p.employee_id
  LEFT JOIN last_promo lp ON lp.snapshot_date = p.snapshot_date AND lp.employee_id = p.employee_id
  LEFT JOIN manager_moves mm ON mm.snapshot_date = p.snapshot_date AND mm.employee_id = p.employee_id
  LEFT JOIN team_exits te ON te.snapshot_date = p.snapshot_date AND te.employee_id = p.employee_id
  LEFT JOIN manager_left ml ON ml.snapshot_date = p.snapshot_date AND ml.employee_id = p.employee_id
  LEFT JOIN ios i ON i.snapshot_date = p.snapshot_date AND i.employee_id = p.employee_id
)
SELECT
  f.snapshot_date,
  MD5(CAST(f.employee_id AS VARCHAR) || '__RUN_SALT__') AS person_key,
  f.next_snapshot_date AS label_end,
  CASE WHEN f.service_date IS NOT NULL AND f.service_date <= DATE '2024-01-01'
       AND NOT EXISTS (
         SELECT 1 FROM hrda.post_hire_monthly_worker_dtls episode
         WHERE episode.employee_id = f.employee_id
           AND CAST(episode.term_date AS DATE) >= DATE '2024-01-01'
           AND CAST(episode.term_date AS DATE) <= f.snapshot_date
           AND CAST(episode.fis_mo_end_dt AS DATE) <= f.snapshot_date
       ) THEN 1 ELSE 0 END AS same_episode_2024,
  CASE WHEN f.service_date IS NOT NULL AND f.service_date <= DATE '2025-01-01'
       AND NOT EXISTS (
         SELECT 1 FROM hrda.post_hire_monthly_worker_dtls episode
         WHERE episode.employee_id = f.employee_id
           AND CAST(episode.term_date AS DATE) >= DATE '2025-01-01'
           AND CAST(episode.term_date AS DATE) <= f.snapshot_date
           AND CAST(episode.fis_mo_end_dt AS DATE) <= f.snapshot_date
       ) THEN 1 ELSE 0 END AS same_episode_2025,
  CASE WHEN f.service_date IS NOT NULL AND f.service_date <= DATE '2026-01-07'
       AND NOT EXISTS (
         SELECT 1 FROM hrda.post_hire_monthly_worker_dtls episode
         WHERE episode.employee_id = f.employee_id
           AND CAST(episode.term_date AS DATE) >= DATE '2026-01-07'
           AND CAST(episode.term_date AS DATE) <= f.snapshot_date
           AND CAST(episode.fis_mo_end_dt AS DATE) <= f.snapshot_date
       ) THEN 1 ELSE 0 END AS same_episode_2026,
  COALESCE(f.level_grouped, '(unknown)') AS level_grouped,
  CASE
    WHEN f.tenure_months IS NULL THEN '(unknown)'
    WHEN f.tenure_months < 12 THEN '<1 year'
    WHEN f.tenure_months < 36 THEN '1-3 years'
    WHEN f.tenure_months < 84 THEN '3-7 years'
    ELSE '7+ years'
  END AS company_tenure_band,
  CASE
    WHEN f.tenure_months IS NULL THEN '(unknown)'
    WHEN f.tenure_months < 12 THEN '<1 year'
    WHEN f.tenure_months < 36 THEN '1-3 years'
    WHEN f.tenure_months < 60 THEN '3-5 years'
    ELSE '5+ years'
  END AS tenure_julia_band,
  CASE
    WHEN f.tenure_months IS NULL THEN '(unknown)'
    WHEN f.tenure_months < 12 THEN '<1 year'
    WHEN f.tenure_months < 24 THEN '1-2 years'
    WHEN f.tenure_months < 36 THEN '2-3 years'
    WHEN f.tenure_months < 60 THEN '3-5 years'
    WHEN f.tenure_months < 120 THEN '5-10 years'
    ELSE '10+ years'
  END AS tenure_playbook_band,
  CASE
    WHEN f.mgr_changes = 0 THEN '0'
    WHEN f.mgr_changes = 1 THEN '1'
    ELSE '2+'
  END AS manager_changes_12m,
  CASE
    WHEN f.manager_id IS NULL THEN '(unknown)'
    WHEN COALESCE(f.team_exit_count, 0) = 0 THEN '0'
    WHEN f.team_exit_count = 1 THEN '1'
    ELSE '2+'
  END AS team_exits_12m,
  CASE
    WHEN f.dir_reports IS NULL THEN '(unknown)'
    WHEN f.dir_reports = 0 THEN '0'
    WHEN f.dir_reports <= 5 THEN '1-5'
    ELSE '6+'
  END AS direct_reports_band,
  CASE
    WHEN f.prior_years IS NULL OR f.prior_years < 0 THEN '(unknown)'
    WHEN f.prior_years < 1 THEN '<1 year'
    WHEN f.prior_years < 3 THEN '1-3 years'
    WHEN f.prior_years < 5 THEN '3-5 years'
    WHEN f.prior_years < 10 THEN '5-10 years'
    ELSE '10+ years'
  END AS prior_experience_band,
  CASE
    WHEN f.service_date IS NULL OR f.original_hire_date IS NULL OR f.service_date > f.snapshot_date THEN '(unknown)'
    WHEN f.service_date > f.original_hire_date THEN 'yes'
    ELSE 'no'
  END AS rehire,
  CASE
    WHEN f.promo_months IS NOT NULL AND f.promo_months < 12 THEN 'promo <1 year'
    WHEN f.promo_months IS NOT NULL AND f.promo_months < 24 THEN 'promo 1-2 years'
    WHEN f.promo_months IS NOT NULL AND f.promo_months < 36 THEN 'promo 2-3 years'
    WHEN f.promo_months IS NOT NULL THEN 'promo 3+ years'
    WHEN f.hire_months IS NULL THEN '(unknown)'
    WHEN f.service_date < DATE '2020-08-01' THEN 'sin promo en historial'
    WHEN f.hire_months < 12 THEN 'sin promo, contratado <1 year'
    WHEN f.hire_months < 36 THEN 'sin promo, contratado 1-3 years'
    ELSE 'sin promo, contratado 3+ years'
  END AS time_since_promotion_band,
  CASE
    WHEN f.snapshot_date < DATE '2022-10-23' THEN '(antes de la fuente)'
    WHEN f.level_months IS NULL THEN '(unknown)'
    WHEN f.level_months < 12 THEN '<1 year'
    WHEN f.level_months < 24 THEN '1-2 years'
    WHEN f.level_months < 36 THEN '2-3 years'
    WHEN f.level_months < 60 THEN '3-5 years'
    ELSE '5+ years'
  END AS time_at_level_band,
  CASE WHEN f.manager_left = 1 THEN 'yes' ELSE 'no' END AS manager_left_6m,
  CASE
    WHEN f.snapshot_date < DATE '2023-10-22' THEN '(antes de la fuente)'
    WHEN f.ios_moves IS NULL THEN 'none'
    WHEN f.ios_other = 1 THEN 'lateral u otro'
    ELSE 'reorg'
  END AS ios_12m,
  CASE
    WHEN f.snapshot_date < DATE '2023-03-26' THEN '(antes de la fuente)'
    WHEN f.layers IS NULL THEN '(unknown)'
    WHEN f.layers <= 6 THEN '<=6'
    WHEN f.layers >= 10 THEN '10+'
    ELSE CAST(f.layers AS VARCHAR)
  END AS layers_band,
  CASE
    WHEN f.snapshot_date < DATE '2024-08-25' THEN '(antes de la fuente)'
    WHEN f.work_arrangement = 'Onsite' THEN 'Onsite'
    WHEN UPPER(f.work_arrangement) LIKE '%MEDICAL%' OR UPPER(f.work_arrangement) LIKE '%CAREGIV%' OR UPPER(f.work_arrangement) LIKE '%LOA%' THEN 'otro o desconocido'
    WHEN f.work_arrangement LIKE 'Offsite%' THEN 'Offsite'
    WHEN f.work_arrangement LIKE 'Interim Modified%' THEN 'Interim Modified'
    ELSE 'otro o desconocido'
  END AS work_arrangement_group,
  COALESCE(f.region, '(unknown)') AS region,
  CASE WHEN f.work_country IS NOT NULL AND f.work_city_raw IS NOT NULL
       THEN f.work_country || ' | ' || f.work_city_raw
       ELSE '(unknown)' END AS work_city,
  CASE WHEN f.cr IS NULL OR f.cr <= 0 THEN '(unknown)'
       WHEN f.cr < 0.8 THEN '<0.8' WHEN f.cr < 0.9 THEN '0.8-0.9'
       WHEN f.cr < 1.0 THEN '0.9-1.0' WHEN f.cr < 1.1 THEN '1.0-1.1'
       WHEN f.cr < 1.2 THEN '1.1-1.2' ELSE '1.2+' END AS comp_ratio_band,
  CASE WHEN f.grade LIKE 'R%' THEN 'R' WHEN f.grade LIKE 'T%' THEN 'T'
       WHEN f.grade IS NULL THEN '(unknown)' ELSE 'other' END AS grade_family,
  CASE WHEN f.acquisition_recorded = 1 THEN 'registrada' ELSE 'sin registro' END AS acquisition_recorded,
  CASE WHEN f.snapshot_date < DATE '2023-10-23' THEN '(historia no confirmada)'
       WHEN f.transfer_12m = 1 THEN 'yes' ELSE 'no' END AS transfer_12m,
  CASE
    WHEN f.next_snapshot_date IS NULL OR f.next_snapshot_date > (SELECT knowledge_boundary FROM params) THEN NULL
    ELSE COALESCE(l.hit_next, 0)
  END AS y_next,
  CASE
    WHEN DATEADD(month, 6, f.snapshot_date) > (SELECT knowledge_boundary FROM params) THEN NULL
    ELSE COALESCE(l.hit_6m, 0)
  END AS y_6m
FROM features f
LEFT JOIN labels l ON l.snapshot_date = f.snapshot_date AND l.employee_id = f.employee_id
