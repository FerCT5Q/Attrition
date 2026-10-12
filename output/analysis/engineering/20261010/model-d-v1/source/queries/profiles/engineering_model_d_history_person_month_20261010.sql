/* Modelo D: señales históricas adicionales. Sólo se usan filas en RAM bajo la
   autorización 20261001. Salt efímero; la consulta no persiste identificadores. */
WITH params AS (
  SELECT DATE '__PERIOD_START__' AS period_start,
         DATE '__PERIOD_END__' AS period_end,
         DATE '2026-09-07' AS knowledge_boundary
),
calendar AS (
  SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) BETWEEN (SELECT period_start FROM params)
                                         AND (SELECT period_end FROM params)
),
population AS (
  SELECT c.snapshot_date, p.employee_id,
         MAX(p.manager_employee_id) AS manager_id
  FROM calendar c
  JOIN hrda.post_hire_monthly_worker_dtls p
    ON CAST(p.fis_mo_end_dt AS DATE) = c.snapshot_date
  WHERE p.worker_type = 'Employee' AND p.employee_type = 'Regular'
    AND p.active_status = 1 AND p.is_rf360_yes_no = 0
    AND TRIM(p.eng_or_noneng) = 'Engineering' AND p.employee_id IS NOT NULL
  GROUP BY 1, 2
),
manager_events AS (
  SELECT employee_id, CAST(manager_change_date AS DATE) AS event_date,
         MIN(CAST(fis_mo_end_dt AS DATE)) AS known_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee' AND employee_type = 'Regular'
    AND manager_change = 1 AND manager_change_date IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) <= (SELECT knowledge_boundary FROM params)
  GROUP BY 1, 2
),
manager_counts AS (
  SELECT p.snapshot_date, p.employee_id,
    COUNT(DISTINCT CASE WHEN e.event_date > DATEADD(month,-3,p.snapshot_date)
                         THEN e.event_date END) AS changes_3m,
    COUNT(DISTINCT CASE WHEN e.event_date > DATEADD(month,-6,p.snapshot_date)
                         THEN e.event_date END) AS changes_6m
  FROM population p
  LEFT JOIN manager_events e ON e.employee_id = p.employee_id
    AND e.event_date > DATEADD(month,-6,p.snapshot_date)
    AND e.event_date <= p.snapshot_date AND e.known_date <= p.snapshot_date
  GROUP BY 1, 2
),
voluntary_events AS (
  SELECT employee_id, CAST(term_date AS DATE) AS term_date,
         MIN(CAST(fis_mo_end_dt AS DATE)) AS known_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee' AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(term_type::VARCHAR),'')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
    AND CAST(term_date AS DATE) <= (SELECT knowledge_boundary FROM params)
  GROUP BY 1, 2
),
exit_manager AS (
  SELECT employee_id, term_date, known_date, manager_id
  FROM (
    SELECT e.employee_id, e.term_date, e.known_date,
           w.manager_employee_id AS manager_id,
           ROW_NUMBER() OVER (PARTITION BY e.employee_id,e.term_date
             ORDER BY CAST(w.fis_mo_end_dt AS DATE) DESC) AS rn
    FROM voluntary_events e
    JOIN hrda.post_hire_monthly_worker_dtls w ON w.employee_id=e.employee_id
      AND CAST(w.fis_mo_end_dt AS DATE) < e.term_date
      AND CAST(w.fis_mo_end_dt AS DATE) >= DATEADD(month,-3,e.term_date)
      AND w.active_status=1 AND w.manager_employee_id IS NOT NULL
  ) ranked WHERE rn=1
),
team_events AS (
  SELECT p.snapshot_date,p.employee_id,
    COUNT(DISTINCT CASE WHEN x.term_date > DATEADD(month,-3,p.snapshot_date)
                         THEN x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR END) AS exits_3m,
    COUNT(DISTINCT CASE WHEN x.term_date > DATEADD(month,-6,p.snapshot_date)
                         THEN x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR END) AS exits_6m,
    COUNT(DISTINCT x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR) AS exits_12m,
    MAX(x.term_date) AS last_exit_date
  FROM population p LEFT JOIN exit_manager x ON x.manager_id=p.manager_id
    AND x.employee_id<>p.employee_id
    AND x.term_date>DATEADD(month,-12,p.snapshot_date)
    AND x.term_date<=p.snapshot_date AND x.known_date<=p.snapshot_date
  GROUP BY 1,2
),
workforce_month AS (
  SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS row_date, employee_id,
         manager_employee_id AS manager_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type='Employee' AND employee_type='Regular'
    AND active_status=1 AND is_rf360_yes_no=0
    AND employee_id IS NOT NULL AND manager_employee_id IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) > DATEADD(month,-12,(SELECT period_start FROM params))
    AND CAST(fis_mo_end_dt AS DATE) <= (SELECT period_end FROM params)
),
team_context AS (
  SELECT p.snapshot_date,p.employee_id,
    COUNT(DISTINCT CASE WHEN w.row_date=p.snapshot_date THEN w.employee_id END) AS current_span,
    COUNT(DISTINCT w.employee_id::VARCHAR||'|'||w.row_date::VARCHAR) AS exposure_person_months
  FROM population p LEFT JOIN workforce_month w ON w.manager_id=p.manager_id
    AND w.row_date>DATEADD(month,-12,p.snapshot_date) AND w.row_date<=p.snapshot_date
  GROUP BY 1,2
)
SELECT p.snapshot_date,
       MD5(CAST(p.employee_id AS VARCHAR)||'__RUN_SALT__') AS person_key,
       CASE WHEN COALESCE(m.changes_3m,0)=0 THEN '0'
            WHEN m.changes_3m=1 THEN '1' ELSE '2+' END AS manager_changes_3m,
       CASE WHEN COALESCE(m.changes_6m,0)=0 THEN '0'
            WHEN m.changes_6m=1 THEN '1' ELSE '2+' END AS manager_changes_6m,
       CASE WHEN COALESCE(t.exits_3m,0)=0 THEN '0'
            WHEN t.exits_3m=1 THEN '1' ELSE '2+' END AS team_exits_3m,
       CASE WHEN COALESCE(t.exits_6m,0)=0 THEN '0'
            WHEN t.exits_6m=1 THEN '1' ELSE '2+' END AS team_exits_6m,
       CASE WHEN p.manager_id IS NULL THEN '(unknown)'
            WHEN t.last_exit_date IS NULL THEN 'none in 12m'
            WHEN t.last_exit_date>DATEADD(month,-3,p.snapshot_date) THEN '<3m'
            WHEN t.last_exit_date>DATEADD(month,-6,p.snapshot_date) THEN '3-6m'
            ELSE '6-12m' END AS team_exit_recency_12m,
       CASE WHEN p.manager_id IS NULL OR c.current_span IS NULL THEN '(unknown)'
            WHEN c.current_span<=4 THEN '1-4' WHEN c.current_span<=9 THEN '5-9'
            WHEN c.current_span<=14 THEN '10-14' WHEN c.current_span<=19 THEN '15-19'
            WHEN c.current_span<=29 THEN '20-29' ELSE '30+' END AS manager_team_size_band,
       CASE WHEN p.manager_id IS NULL OR COALESCE(c.exposure_person_months,0)=0 THEN '(unknown)'
            WHEN COALESCE(t.exits_12m,0)=0 THEN '0'
            WHEN 100.0*t.exits_12m/c.exposure_person_months<0.5 THEN '>0-<0.5'
            WHEN 100.0*t.exits_12m/c.exposure_person_months<1.0 THEN '0.5-<1'
            ELSE '1+' END AS team_exit_intensity_12m
FROM population p
LEFT JOIN manager_counts m ON m.snapshot_date=p.snapshot_date AND m.employee_id=p.employee_id
LEFT JOIN team_events t ON t.snapshot_date=p.snapshot_date AND t.employee_id=p.employee_id
LEFT JOIN team_context c ON c.snapshot_date=p.snapshot_date AND c.employee_id=p.employee_id

