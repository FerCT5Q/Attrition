/* Reconciliar personas con salida y eventos únicos en horizontes superpuestos.
   Aceptación: eventos únicos = personas con evento para poder usar ambos rótulos;
   si difieren se conserva sólo «personas con evento» en fichas, sin asumir una salida/persona. */
WITH periods AS (
 SELECT 'aug_dec_2025' AS period, DATE '2025-08-01' AS start_date, DATE '2025-12-31' AS end_date
 UNION ALL SELECT 'jan_feb_2026', DATE '2026-01-01', DATE '2026-02-28'
), pop AS (
 SELECT DISTINCT p.period, h.employee_id, CAST(h.fis_mo_end_dt AS DATE) AS snapshot_date
 FROM periods p JOIN hrda.post_hire_monthly_worker_dtls h
 ON CAST(h.fis_mo_end_dt AS DATE) BETWEEN p.start_date AND p.end_date
 WHERE h.worker_type='Employee' AND h.employee_type='Regular' AND h.active_status=1
 AND h.is_rf360_yes_no=0 AND TRIM(h.eng_or_noneng)='Engineering' AND h.employee_id IS NOT NULL
), terms AS (
 SELECT DISTINCT employee_id, CAST(term_date AS DATE) AS term_date
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE worker_type='Employee' AND employee_type='Regular'
 AND UPPER(NULLIF(TRIM(term_type::VARCHAR),''))='VOLUNTARY'
 AND term_date IS NOT NULL AND CAST(term_date AS DATE)<=DATE '2026-09-07'
), hits AS (
 SELECT DISTINCT p.period,p.employee_id,p.snapshot_date,t.term_date
 FROM pop p JOIN terms t ON t.employee_id=p.employee_id
 AND t.term_date>p.snapshot_date AND t.term_date<=DATEADD(month,6,p.snapshot_date)
), events AS (
 SELECT DISTINCT period,employee_id,term_date FROM hits
), exposures AS (
 SELECT DISTINCT period,employee_id,snapshot_date FROM hits
), event_counts AS (
 SELECT period,COUNT(*) AS unique_exit_events,COUNT(DISTINCT employee_id) AS distinct_people_with_event
 FROM events GROUP BY 1
), exposure_counts AS (
 SELECT period,COUNT(*) AS event_exposures FROM exposures GROUP BY 1
)
SELECT e.period,e.unique_exit_events,e.distinct_people_with_event,x.event_exposures
FROM event_counts e JOIN exposure_counts x ON x.period=e.period
WHERE e.distinct_people_with_event>=30
ORDER BY e.period
