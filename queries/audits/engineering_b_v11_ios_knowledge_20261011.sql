/* IOS: antes de modelar los seis motivos, comprobar trazabilidad temporal.
   Sólo agregados de eventos ligados a alguna foto de la población objetivo. */
WITH population AS (
 SELECT DISTINCT employee_id FROM hrda.post_hire_monthly_worker_dtls
 WHERE fis_mo_end_dt::DATE BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
 AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
 AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
), events AS (
 SELECT t.employee_id,t.effective_date,TRIM(t.business_process_reason) AS reason,
        COUNT(*) AS n,MIN(t.date_initiated) AS initiated,
        MIN(t.last_modified_date) AS modified,MIN(t.airflow_execution_date) AS loaded,
        COUNT(DISTINCT COALESCE(t.date_initiated::VARCHAR,'<NULL>')) AS initiation_variants
 FROM hrda.workers_ios_transfers t JOIN population p ON p.employee_id=t.employee_id
 WHERE t.effective_date<=DATE '2026-09-07'
 GROUP BY 1,2,3
)
SELECT EXTRACT(year FROM effective_date)::INTEGER AS effective_year,
 COUNT(*) AS distinct_events,COUNT(DISTINCT employee_id) AS employee_count,
 SUM(n) AS source_rows,MIN(effective_date) AS first_effective_date,
 MIN(initiated) AS first_initiated_date,MAX(initiated) AS last_initiated_date,
 MIN(modified) AS first_modified_date,MAX(modified) AS last_modified_date,
 MIN(loaded) AS first_loaded_date,MAX(loaded) AS last_loaded_date,
 SUM(CASE WHEN initiated IS NULL THEN 1 ELSE 0 END) AS missing_initiated,
 SUM(CASE WHEN initiated>effective_date THEN 1 ELSE 0 END) AS initiated_after_effective,
 SUM(CASE WHEN loaded>effective_date THEN 1 ELSE 0 END) AS loaded_after_effective,
 SUM(CASE WHEN modified>effective_date THEN 1 ELSE 0 END) AS modified_after_effective,
 SUM(CASE WHEN GREATEST(effective_date,modified,loaded)<=DATE '2026-02-28' THEN 1 ELSE 0 END) AS events_known_by_mature_cutoff,
 SUM(CASE WHEN initiation_variants>1 THEN 1 ELSE 0 END) AS conflicting_initiation,
 SUM(CASE WHEN reason IN (
 'Transfer > Transfer > Reorg Department and/or Manager Change',
 'Transfer > Transfer > Lateral IOS',
 'Transfer > Transfer > Country-to-Country Location Change',
 'Promotion > Transfer > Promo IOS',
 'Transfer > Transfer > Immigration Parking',
 'Demotion > Transfer > Downlevel IOS') THEN 1 ELSE 0 END) AS v11_reason_events
FROM events GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1;
