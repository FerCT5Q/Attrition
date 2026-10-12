/* Contexto histórico del manager del V11. Datos de cada intervalo y eventos
   conocidos en la foto objetivo. Identidades sólo como llaves dentro de SQL. */
WITH dates AS (
 SELECT fis_mo_end_dt::DATE AS snapshot_date FROM hrda.post_hire_monthly_worker_dtls
 WHERE fis_mo_end_dt::DATE<=DATE '2026-09-07' GROUP BY 1
), calendar AS (
 SELECT snapshot_date,ROW_NUMBER() OVER(ORDER BY snapshot_date) AS seq,
 LEAD(snapshot_date) OVER(ORDER BY snapshot_date) AS interval_end FROM dates
), targets AS (
 SELECT snapshot_date,seq FROM calendar
 WHERE snapshot_date BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
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
 WHERE w.fis_mo_end_dt::DATE BETWEEN DATEADD(month,-21,DATE '2020-07-26') AND DATE '2026-09-07'
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
 WHERE fis_mo_end_dt::DATE BETWEEN DATEADD(month,-21,DATE '2020-07-26') AND DATE '2026-09-07'
 AND term_date::DATE>DATEADD(month,-21,DATE '2020-07-26') AND term_date::DATE<=DATE '2026-09-07'
 AND employee_id IS NOT NULL GROUP BY 1,2
)
SELECT COUNT(*) AS event_keys,COUNT(DISTINCT employee_id) AS employee_count,
 MIN(known_date) AS first_known_voluntary_date,MAX(known_date) AS last_known_voluntary_date,
 MIN(CASE WHEN known_date IS NOT NULL THEN term_date END) AS first_effective_voluntary_date,
 SUM(CASE WHEN known_date<DATE '2022-01-01' THEN 1 ELSE 0 END) AS known_before_2022,
 SUM(CASE WHEN known_date IS NOT NULL AND known_date>DATEADD(day,45,term_date) THEN 1 ELSE 0 END) AS recorded_over_45_days_after_event,
 SUM(CASE WHEN known_date IS NOT NULL AND conflicting_known_date IS NOT NULL THEN 1 ELSE 0 END) AS conflicting_type_events
FROM event_sources HAVING COUNT(DISTINCT employee_id)>=30;
