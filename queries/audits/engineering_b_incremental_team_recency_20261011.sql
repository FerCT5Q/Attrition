/* Modelo D - auditoría agregada de salidas voluntarias del equipo y recencia.
   Regla: 3m <= 6m <= 12m; la banda coincide con la última salida elegible;
   eventos futuros o conocidos tarde quedan excluidos. */
WITH params AS (
  SELECT DATE '2020-07-26' AS period_start, DATE '2026-09-07' AS period_end
),
population AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id,
         MAX(manager_employee_id) AS manager_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN (SELECT period_start FROM params) AND (SELECT period_end FROM params)
    AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
    AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
  GROUP BY 1,2
),
voluntary_events AS (
  SELECT employee_id,CAST(term_date AS DATE) AS term_date,
         MIN(CAST(fis_mo_end_dt AS DATE)) AS known_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type='Employee' AND employee_type='Regular'
    AND UPPER(NULLIF(TRIM(term_type::VARCHAR),''))='VOLUNTARY' AND term_date IS NOT NULL
    AND CAST(term_date AS DATE)<=(SELECT period_end FROM params)
  GROUP BY 1,2
),
exit_manager AS (
  SELECT employee_id,term_date,known_date,manager_id
  FROM (
    SELECT e.employee_id,e.term_date,e.known_date,w.manager_employee_id AS manager_id,
           ROW_NUMBER() OVER(PARTITION BY e.employee_id,e.term_date ORDER BY CAST(w.fis_mo_end_dt AS DATE) DESC) AS rn
    FROM voluntary_events e
    JOIN hrda.post_hire_monthly_worker_dtls w ON w.employee_id=e.employee_id
      AND CAST(w.fis_mo_end_dt AS DATE)<e.term_date
      AND CAST(w.fis_mo_end_dt AS DATE)>=DATEADD(month,-3,e.term_date)
      AND w.active_status=1 AND w.manager_employee_id IS NOT NULL
  ) z WHERE rn=1
),
counts AS (
  SELECT p.snapshot_date,p.employee_id,p.manager_id,
    COUNT(DISTINCT CASE WHEN x.term_date>DATEADD(month,-3,p.snapshot_date)
                         AND x.term_date<=p.snapshot_date AND x.known_date<=p.snapshot_date
                        THEN x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR END) AS n3,
    COUNT(DISTINCT CASE WHEN x.term_date>DATEADD(month,-6,p.snapshot_date)
                         AND x.term_date<=p.snapshot_date AND x.known_date<=p.snapshot_date
                        THEN x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR END) AS n6,
    COUNT(DISTINCT CASE WHEN x.term_date>DATEADD(month,-12,p.snapshot_date)
                         AND x.term_date<=p.snapshot_date AND x.known_date<=p.snapshot_date
                        THEN x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR END) AS n12,
    MAX(CASE WHEN x.term_date<=p.snapshot_date AND x.known_date<=p.snapshot_date THEN x.term_date END) AS last_exit,
    COUNT(DISTINCT CASE WHEN x.term_date>p.snapshot_date THEN x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR END) AS future_events,
    COUNT(DISTINCT CASE WHEN x.term_date<=p.snapshot_date AND x.known_date>p.snapshot_date
                        THEN x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR END) AS late_known
  FROM population p LEFT JOIN exit_manager x ON x.manager_id=p.manager_id AND x.employee_id<>p.employee_id
    AND x.term_date>DATEADD(month,-12,p.snapshot_date)
  GROUP BY 1,2,3
),
checked AS (
  SELECT snapshot_date,employee_id,manager_id,n3,n6,n12,last_exit,future_events,late_known,
         CASE WHEN manager_id IS NULL THEN '(unknown)'
                 WHEN last_exit IS NULL THEN 'none in 12m'
                 WHEN last_exit>DATEADD(month,-3,snapshot_date) THEN '<3m'
                 WHEN last_exit>DATEADD(month,-6,snapshot_date) THEN '3-6m'
                 ELSE '6-12m' END AS recency_band
  FROM counts
)
SELECT COUNT(*) AS person_snapshots,COUNT(DISTINCT snapshot_date) AS snapshots,
       SUM(CASE WHEN n3>n6 OR n6>n12 THEN 1 ELSE 0 END) AS monotonicity_violations,
       SUM(CASE WHEN (n12=0 AND last_exit IS NOT NULL) OR (n12>0 AND last_exit IS NULL) THEN 1 ELSE 0 END) AS last_event_consistency_violations,
       SUM(CASE WHEN recency_band='<3m' AND n3=0 THEN 1 WHEN recency_band='3-6m' AND (n6=0 OR n3>0) THEN 1
                WHEN recency_band='6-12m' AND (n12=0 OR n6>0) THEN 1 WHEN recency_band='none in 12m' AND n12>0 THEN 1 ELSE 0 END) AS band_consistency_violations,
       SUM(future_events) AS future_events_excluded,SUM(late_known) AS late_known_events_excluded,
       SUM(CASE WHEN n12>0 THEN 1 ELSE 0 END) AS covered_person_snapshots,
       ROUND(100.0*SUM(CASE WHEN n12>0 THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0),4) AS covered_percent,
       MAX(n3) AS maximum_3m,MAX(n6) AS maximum_6m,MAX(n12) AS maximum_12m
FROM checked;
