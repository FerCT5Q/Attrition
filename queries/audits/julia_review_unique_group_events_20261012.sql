/* presentation: salida persona-fecha distinta, por grupo/foto. Regla: >=30 personas/eventos; supresión complementaria. */
/* C, B y BU L3: sÃ³lo memoria, autorizaciÃ³n 20261001. Salt efÃ­mero.
   Se conserva la Ãºltima foto sin etiquetas. Salidas como features sÃ³lo tras su primera foto registrada.
   No QVoice, IDs publicables, compensaciÃ³n exacta ni cachÃ© de filas. */
WITH params AS (
  SELECT
    DATE '2025-08-01' AS period_start,
    DATE '2026-02-28' AS period_end,
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
    MAX(NULLIF(TRIM(d.ude_bu_reporting_l3), '')) AS bu_l3,
    MAX(p.compa_ratio) AS cr,
    MAX(NULLIF(TRIM(p.compensation_grade), '')) AS grade,
    MAX(CASE WHEN NULLIF(TRIM(p.acquisition), '') IS NOT NULL THEN 1 ELSE 0 END) AS acquisition_recorded
  FROM snapshot_calendar c
  INNER JOIN hrda.post_hire_monthly_worker_dtls p
    ON CAST(p.fis_mo_end_dt AS DATE) = c.snapshot_date
  LEFT JOIN hrda.d_department d
    ON CAST(d.nk_dept_id AS VARCHAR) = NULLIF(TRIM(p.cost_centerid), '')
   AND CAST(d.edw_effective_dt AS DATE) <= c.snapshot_date
   AND (
        d.edw_end_dt IS NULL
        OR c.snapshot_date < CAST(d.edw_end_dt AS DATE)
   )
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
  -- Ãšltima foto dentro de los 45 dÃ­as previos a la salida del manager.
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
    p.dir_reports, p.region, p.work_country, p.work_city_raw, p.bu_l3,
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
), grouped AS (
 SELECT f.employee_id,f.snapshot_date,
 CASE WHEN f.tenure_months IS NULL THEN 'sin dato'
 WHEN f.tenure_months<12 THEN '<1 año' WHEN f.tenure_months<24 THEN '1-2 años'
 WHEN f.tenure_months<36 THEN '2-3 años' WHEN f.tenure_months<60 THEN '3-5 años'
 WHEN f.tenure_months<120 THEN '5-10 años' ELSE '10+ años' END
 || ' · ' || CASE WHEN f.manager_id IS NULL THEN 'sin dato'
 WHEN COALESCE(f.team_exit_count,0)=0 THEN 'sin salidas' ELSE 'con salidas' END
 || ' · ' || CASE WHEN SPLIT_PART(f.level_grouped,' - ',1) IN ('1','2','3') THEN 'alto'
 WHEN SPLIT_PART(f.level_grouped,' - ',1) IN ('5','6') THEN 'medio'
 WHEN SPLIT_PART(f.level_grouped,' - ',1) IN ('7','8') THEN 'entrada' ELSE 'otro' END AS parent
 FROM features f
), counts AS (
 SELECT g.snapshot_date,g.parent,COUNT(DISTINCT g.employee_id) AS people,
 COUNT(DISTINCT CASE WHEN v.term_date IS NOT NULL THEN g.employee_id END) AS event_exposures,
 COUNT(DISTINCT CASE WHEN v.term_date IS NOT NULL THEN g.employee_id::VARCHAR || '|' || v.term_date::VARCHAR END) AS unique_exit_events
 FROM grouped g LEFT JOIN voluntary_events v ON v.employee_id=g.employee_id
 AND v.term_date>g.snapshot_date AND v.term_date<=DATEADD(month,6,g.snapshot_date)
 GROUP BY 1,2
), flags AS (
 SELECT snapshot_date,parent,people,event_exposures,unique_exit_events,
 CASE WHEN people<30 OR event_exposures<30 THEN 1 ELSE 0 END AS hidden
 FROM counts
), complement AS (
 SELECT snapshot_date,parent,people,event_exposures,unique_exit_events,hidden,
 SUM(hidden) OVER(PARTITION BY snapshot_date) AS hidden_cells,
 ROW_NUMBER() OVER(PARTITION BY snapshot_date,hidden ORDER BY event_exposures,parent) AS safety_order
 FROM flags
)
SELECT snapshot_date,parent,people,event_exposures,unique_exit_events
FROM complement WHERE hidden=0 AND NOT(hidden_cells=1 AND safety_order=1)
ORDER BY snapshot_date,parent
