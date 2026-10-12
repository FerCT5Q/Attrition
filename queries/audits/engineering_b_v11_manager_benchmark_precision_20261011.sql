/* Contexto histórico del manager del V11. Datos de cada intervalo y eventos
   conocidos en la foto objetivo. Identidades sólo como llaves dentro de SQL. */
WITH dates AS (
 SELECT fis_mo_end_dt::DATE AS snapshot_date FROM hrda.post_hire_monthly_worker_dtls
 WHERE fis_mo_end_dt::DATE<=DATE '2026-08-23' GROUP BY 1
), calendar AS (
 SELECT snapshot_date,ROW_NUMBER() OVER(ORDER BY snapshot_date) AS seq,
 LEAD(snapshot_date) OVER(ORDER BY snapshot_date) AS interval_end FROM dates
), targets AS (
 SELECT snapshot_date,seq FROM calendar
 WHERE snapshot_date BETWEEN DATE '2026-08-23' AND DATE '2026-08-23'
), raw_workforce AS (
 SELECT w.fis_mo_end_dt::DATE AS snapshot_date,w.employee_id,w.manager_employee_id::BIGINT AS manager_id,
 COALESCE(NULLIF(TRIM(w.region),''),'(unknown)') AS region,
 COALESCE(NULLIF(TRIM(w.job_family),''),'(unknown)') AS family,
 COALESCE(NULLIF(TRIM(w.job_level_primary_position),''),'(unknown)') AS level,
 COALESCE(CASE WHEN w.max_hire_rehire_date<=w.fis_mo_end_dt THEN w.max_hire_rehire_date END,
          CASE WHEN w.service_date<=w.fis_mo_end_dt THEN w.service_date END,
          CASE WHEN w.original_hire_date<=w.fis_mo_end_dt THEN w.original_hire_date END)::DATE AS episode,
 TRIM(w.eng_or_noneng) AS engineering
 FROM hrda.post_hire_monthly_worker_dtls w
 WHERE w.fis_mo_end_dt::DATE BETWEEN DATEADD(month,-21,DATE '2026-08-23') AND DATE '2026-08-23'
 AND w.worker_type='Employee' AND w.employee_type='Regular' AND w.active_status=1
 AND w.is_rf360_yes_no=0 AND w.employee_id IS NOT NULL
), workforce AS (
 SELECT snapshot_date,employee_id,MAX(manager_id) AS manager_id,
 MAX(region) AS region,MAX(family) AS family,MAX(level) AS level,MAX(episode) AS episode,
 MAX(engineering) AS engineering,COUNT(*) AS n,
 COUNT(DISTINCT COALESCE(manager_id::VARCHAR,'<NULL>')||'|'||region||'|'||family||'|'||level||'|'||COALESCE(episode::VARCHAR,'<NULL>')) AS variants
 FROM raw_workforce GROUP BY 1,2
), exposure AS (
 SELECT w.snapshot_date,c.seq,c.interval_end,w.employee_id,w.manager_id,
 w.region||'|'||w.family||'|'||w.level||'|'||
 CASE WHEN w.episode IS NULL THEN '(unknown)'
 WHEN DATEDIFF(month,w.episode,w.snapshot_date)<12 THEN '<1'
 WHEN DATEDIFF(month,w.episode,w.snapshot_date)<24 THEN '1-2'
 WHEN DATEDIFF(month,w.episode,w.snapshot_date)<60 THEN '2-5' ELSE '5+' END AS stratum
 FROM workforce w JOIN calendar c ON c.snapshot_date=w.snapshot_date
 WHERE w.manager_id IS NOT NULL AND w.manager_id<>w.employee_id AND w.n=1 AND w.variants=1
), event_sources AS (
 SELECT employee_id,term_date::DATE AS term_date,
 MIN(CASE WHEN UPPER(TRIM(term_type))='VOLUNTARY' AND term_date<=fis_mo_end_dt THEN fis_mo_end_dt::DATE END) AS known_date,
 MIN(CASE WHEN NULLIF(TRIM(term_type),'') IS NOT NULL AND UPPER(TRIM(term_type))<>'VOLUNTARY'
          AND term_date<=fis_mo_end_dt THEN fis_mo_end_dt::DATE END) AS conflicting_known_date
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE fis_mo_end_dt::DATE BETWEEN DATEADD(month,-21,DATE '2026-08-23') AND DATE '2026-08-23'
 AND term_date::DATE>DATEADD(month,-21,DATE '2026-08-23') AND term_date::DATE<=DATE '2026-08-23'
 AND employee_id IS NOT NULL GROUP BY 1,2
), attributions AS (
 SELECT e.employee_id,e.term_date,e.known_date,e.conflicting_known_date,
 x.seq,x.manager_id,x.stratum
 FROM event_sources e JOIN calendar c ON e.term_date>c.snapshot_date AND e.term_date<=c.interval_end
 JOIN exposure x ON x.seq=c.seq AND x.employee_id=e.employee_id
 WHERE e.known_date IS NOT NULL
), known_events AS (
 SELECT t.snapshot_date,t.seq AS target_seq,a.employee_id,a.term_date,a.known_date,
 a.seq,a.manager_id,a.stratum
 FROM targets t JOIN attributions a ON a.seq>=t.seq-18 AND a.seq<t.seq AND a.known_date<=t.snapshot_date
 AND (a.conflicting_known_date IS NULL OR a.conflicting_known_date>t.snapshot_date)
), team_intervals AS (
 SELECT seq,manager_id,COUNT(DISTINCT employee_id) AS exposure_n FROM exposure GROUP BY 1,2
), manager_strata AS (
 SELECT seq,manager_id,stratum,COUNT(DISTINCT employee_id) AS exposure_n FROM exposure GROUP BY 1,2,3
), strata AS (
 SELECT seq,stratum,COUNT(DISTINCT employee_id) AS exposure_n FROM exposure GROUP BY 1,2
), current_managers AS (
 SELECT t.snapshot_date,t.seq,w.manager_id,COUNT(DISTINCT w.employee_id) AS current_reports
 FROM targets t JOIN workforce w ON w.snapshot_date=t.snapshot_date
 WHERE w.manager_id IS NOT NULL AND w.manager_id<>w.employee_id AND w.n=1 AND w.variants=1 GROUP BY 1,2,3
), history AS (
 SELECT c.snapshot_date,c.seq,c.manager_id,
 COUNT(h.seq) AS intervals18,MIN(h.seq) AS first18,MAX(h.seq) AS last18,
 SUM(h.exposure_n) AS exposure18,
 SUM(CASE WHEN h.seq>=c.seq-6 THEN 1 ELSE 0 END) AS intervals6,
 SUM(CASE WHEN h.seq>=c.seq-6 THEN h.exposure_n ELSE 0 END) AS exposure6
 FROM current_managers c LEFT JOIN team_intervals h ON h.manager_id=c.manager_id AND h.seq>=c.seq-18 AND h.seq<c.seq
 GROUP BY 1,2,3
), observed AS (
 SELECT snapshot_date,manager_id,COUNT(*) AS exits18,
 SUM(CASE WHEN seq>=target_seq-6 THEN 1 ELSE 0 END) AS exits6,
 MAX(known_date) AS latest_known_date
 FROM known_events GROUP BY 1,2
), stratum_events AS (
 SELECT snapshot_date,seq,stratum,COUNT(*) AS exits
 FROM known_events WHERE seq>=target_seq-6 GROUP BY 1,2,3
), interval_strata AS (
 SELECT t.snapshot_date,s.seq,s.stratum,s.exposure_n,COALESCE(e.exits,0) AS exits
 FROM targets t JOIN strata s ON s.seq>=t.seq-6 AND s.seq<t.seq
 LEFT JOIN stratum_events e ON e.snapshot_date=t.snapshot_date AND e.seq=s.seq AND e.stratum=s.stratum
), global_intervals AS (
 SELECT snapshot_date,seq,SUM(exposure_n) AS exposure_n,SUM(exits) AS exits,
 SUM(exits)::DOUBLE PRECISION/NULLIF(SUM(exposure_n),0) AS rate
 FROM interval_strata GROUP BY 1,2
), rates AS (
 SELECT s.snapshot_date,s.seq,s.stratum,
 CASE WHEN s.exposure_n>=30 THEN s.exits::DOUBLE PRECISION/s.exposure_n ELSE g.rate END AS rate
 FROM interval_strata s JOIN global_intervals g ON g.snapshot_date=s.snapshot_date AND g.seq=s.seq
), expected AS (
 SELECT r.snapshot_date,m.manager_id,SUM(m.exposure_n*r.rate) AS expected6
 FROM rates r JOIN manager_strata m ON m.seq=r.seq AND m.stratum=r.stratum GROUP BY 1,2
), prior AS (
 SELECT snapshot_date,SUM(exits)::DOUBLE PRECISION/NULLIF(SUM(exposure_n),0) AS rate,
 COUNT(*) AS intervals FROM global_intervals GROUP BY 1
), values6 AS (
 SELECT h.snapshot_date,h.seq,h.manager_id,h.intervals18,h.first18,h.last18,h.exposure18,h.intervals6,h.exposure6,
 COALESCE(o.exits18,0) AS exits18,COALESCE(o.exits6,0) AS exits6,o.latest_known_date,
 e.expected6,p.rate AS prior_rate,p.intervals AS global_intervals6,
 CASE WHEN h.seq>=(SELECT seq FROM calendar WHERE snapshot_date=DATE '2022-10-23')+6 THEN 1 ELSE 0 END AS feed_complete6,
 CASE WHEN h.seq>=(SELECT seq FROM calendar WHERE snapshot_date=DATE '2022-10-23')+18 THEN 1 ELSE 0 END AS feed_complete18,
 CASE WHEN h.seq>=(SELECT seq FROM calendar WHERE snapshot_date=DATE '2022-10-23')+6 AND h.exposure6>0 AND p.intervals=6 AND p.rate>0 AND e.expected6 IS NOT NULL
 THEN (COALESCE(o.exits6,0)+60*p.rate)/(e.expected6+60*p.rate) END AS oe6,
 CASE WHEN h.seq>=(SELECT seq FROM calendar WHERE snapshot_date=DATE '2022-10-23')+18 AND h.intervals18=18 AND h.first18=h.seq-18 AND h.last18=h.seq-1
 AND h.exposure18/18.0>=4 AND COALESCE(o.exits18,0)>=2 AND h.exposure18>0 THEN 1 ELSE 0 END AS eligible18,
 CASE WHEN h.exposure18>0 THEN COALESCE(o.exits18,0)::DOUBLE PRECISION/h.exposure18*6 END AS rate18
 FROM history h LEFT JOIN observed o ON o.snapshot_date=h.snapshot_date AND o.manager_id=h.manager_id
 LEFT JOIN expected e ON e.snapshot_date=h.snapshot_date AND e.manager_id=h.manager_id
 LEFT JOIN prior p ON p.snapshot_date=h.snapshot_date
), benchmarks AS (
 SELECT snapshot_date,SUM(exits18)::DOUBLE PRECISION/NULLIF(SUM(exposure18),0)*6 AS benchmark,
 SUM(rate18*(exposure18/18.0))/NULLIF(SUM(exposure18/18.0),0) AS independent_benchmark
 FROM values6 WHERE eligible18=1 GROUP BY 1
)
SELECT v.snapshot_date,COUNT(*) AS eligible_managers,
 SUM(v.exposure18) AS exposure18,SUM(v.exits18) AS exits18,
 MAX(b.benchmark) AS benchmark,MAX(b.independent_benchmark) AS independent_decimal_weights,
 SUM(v.rate18*v.exposure18)/SUM(v.exposure18) AS independent_exposure_weights,
 SUM(v.rate18*(v.exposure18::DOUBLE PRECISION/18))/SUM(v.exposure18::DOUBLE PRECISION/18) AS independent_float_weights,
 MAX(ABS(v.exposure18/18.0-v.exposure18::DOUBLE PRECISION/18)) AS maximum_weight_rounding_difference
FROM values6 v JOIN benchmarks b ON b.snapshot_date=v.snapshot_date
WHERE v.eligible18=1 GROUP BY 1 HAVING COUNT(*)>=30;
