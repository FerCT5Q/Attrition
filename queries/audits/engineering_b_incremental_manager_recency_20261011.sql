/* Modelo D - auditoría agregada de cambios de manager 3/6/12 meses.
   Regla: una fila por persona-foto; 3m <= 6m <= 12m; ningún evento futuro
   ni conocido después de la foto puede entrar. No devuelve identificadores. */
WITH params AS (
  SELECT DATE '2020-07-26' AS period_start, DATE '2026-09-07' AS period_end
),
population AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN (SELECT period_start FROM params) AND (SELECT period_end FROM params)
    AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
    AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
  GROUP BY 1,2
),
events AS (
  SELECT employee_id, CAST(manager_change_date AS DATE) AS event_date,
         MIN(CAST(fis_mo_end_dt AS DATE)) AS known_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type='Employee' AND employee_type='Regular'
    AND manager_change=1 AND manager_change_date IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) <= (SELECT period_end FROM params)
  GROUP BY 1,2
),
counts AS (
  SELECT p.snapshot_date,p.employee_id,
    COUNT(DISTINCT CASE WHEN e.event_date>DATEADD(month,-3,p.snapshot_date)
                         AND e.event_date<=p.snapshot_date AND e.known_date<=p.snapshot_date THEN e.event_date END) AS n3,
    COUNT(DISTINCT CASE WHEN e.event_date>DATEADD(month,-6,p.snapshot_date)
                         AND e.event_date<=p.snapshot_date AND e.known_date<=p.snapshot_date THEN e.event_date END) AS n6,
    COUNT(DISTINCT CASE WHEN e.event_date>DATEADD(month,-12,p.snapshot_date)
                         AND e.event_date<=p.snapshot_date AND e.known_date<=p.snapshot_date THEN e.event_date END) AS n12,
    COUNT(DISTINCT CASE WHEN e.event_date>p.snapshot_date THEN e.event_date END) AS future_events_available_in_source,
    COUNT(DISTINCT CASE WHEN e.event_date<=p.snapshot_date AND e.known_date>p.snapshot_date THEN e.event_date END) AS late_known_events_excluded
  FROM population p
  LEFT JOIN events e ON e.employee_id=p.employee_id
    AND e.event_date>DATEADD(month,-12,p.snapshot_date)
  GROUP BY 1,2
)
SELECT COUNT(*) AS person_snapshots,
       COUNT(DISTINCT snapshot_date) AS snapshots,
       SUM(CASE WHEN n3>n6 OR n6>n12 THEN 1 ELSE 0 END) AS monotonicity_violations,
       SUM(CASE WHEN n3<0 OR n6<0 OR n12<0 THEN 1 ELSE 0 END) AS negative_count_violations,
       SUM(future_events_available_in_source) AS future_events_excluded,
       SUM(late_known_events_excluded) AS late_known_events_excluded,
       SUM(CASE WHEN n12>0 THEN 1 ELSE 0 END) AS covered_person_snapshots,
       ROUND(100.0*SUM(CASE WHEN n12>0 THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),4) AS covered_percent,
       MAX(n3) AS maximum_3m, MAX(n6) AS maximum_6m, MAX(n12) AS maximum_12m
FROM counts;
