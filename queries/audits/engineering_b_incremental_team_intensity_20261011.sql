/* Modelo D - auditoría agregada de intensidad de salidas por 100 personas-mes.
   Regla: denominador positivo cuando hay manager; numerador no negativo y no
   mayor que la exposición; ningún evento futuro o conocido tarde entra. */
WITH params AS (
  SELECT DATE '2020-07-26' AS period_start, DATE '2026-09-07' AS period_end
),
population AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date,employee_id,MAX(manager_employee_id) AS manager_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN (SELECT period_start FROM params) AND (SELECT period_end FROM params)
    AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
    AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
  GROUP BY 1,2
),
workforce AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS row_date,employee_id,manager_employee_id AS manager_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE)>DATEADD(month,-12,(SELECT period_start FROM params))
    AND CAST(fis_mo_end_dt AS DATE)<=(SELECT period_end FROM params)
    AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
    AND is_rf360_yes_no=0 AND employee_id IS NOT NULL AND manager_employee_id IS NOT NULL
  GROUP BY 1,2,3
),
voluntary_events AS (
  SELECT employee_id,CAST(term_date AS DATE) AS term_date,MIN(CAST(fis_mo_end_dt AS DATE)) AS known_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type='Employee' AND employee_type='Regular'
    AND UPPER(NULLIF(TRIM(term_type::VARCHAR),''))='VOLUNTARY' AND term_date IS NOT NULL
    AND CAST(term_date AS DATE)<=(SELECT period_end FROM params)
  GROUP BY 1,2
),
exit_manager AS (
  SELECT employee_id,term_date,known_date,manager_id FROM (
    SELECT e.employee_id,e.term_date,e.known_date,w.manager_employee_id AS manager_id,
           ROW_NUMBER() OVER(PARTITION BY e.employee_id,e.term_date ORDER BY CAST(w.fis_mo_end_dt AS DATE) DESC) AS rn
    FROM voluntary_events e JOIN hrda.post_hire_monthly_worker_dtls w ON w.employee_id=e.employee_id
      AND CAST(w.fis_mo_end_dt AS DATE)<e.term_date AND CAST(w.fis_mo_end_dt AS DATE)>=DATEADD(month,-3,e.term_date)
      AND w.active_status=1 AND w.manager_employee_id IS NOT NULL
  ) z WHERE rn=1
),
exposure AS (
  SELECT p.snapshot_date,p.employee_id,p.manager_id,
         COUNT(DISTINCT w.employee_id::VARCHAR||'|'||w.row_date::VARCHAR) AS person_months
  FROM population p LEFT JOIN workforce w ON w.manager_id=p.manager_id
    AND w.row_date>DATEADD(month,-12,p.snapshot_date) AND w.row_date<=p.snapshot_date
  GROUP BY 1,2,3
),
events AS (
  SELECT p.snapshot_date,p.employee_id,
    COUNT(DISTINCT CASE WHEN x.term_date<=p.snapshot_date AND x.known_date<=p.snapshot_date
                        THEN x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR END) AS exits12,
    COUNT(DISTINCT CASE WHEN x.term_date>p.snapshot_date THEN x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR END) AS future_events,
    COUNT(DISTINCT CASE WHEN x.term_date<=p.snapshot_date AND x.known_date>p.snapshot_date
                        THEN x.employee_id::VARCHAR||'|'||x.term_date::VARCHAR END) AS late_known
  FROM population p LEFT JOIN exit_manager x ON x.manager_id=p.manager_id AND x.employee_id<>p.employee_id
    AND x.term_date>DATEADD(month,-12,p.snapshot_date)
  GROUP BY 1,2
),
checked AS (
  SELECT x.snapshot_date,x.employee_id,x.manager_id,x.person_months,
         e.exits12,e.future_events,e.late_known,
         CASE WHEN x.manager_id IS NULL OR x.person_months=0 THEN '(unknown)'
              WHEN e.exits12=0 THEN '0'
              WHEN 100.0*e.exits12/x.person_months<0.5 THEN '>0-<0.5'
              WHEN 100.0*e.exits12/x.person_months<1.0 THEN '0.5-<1' ELSE '1+' END AS band
  FROM exposure x JOIN events e ON e.snapshot_date=x.snapshot_date AND e.employee_id=x.employee_id
)
SELECT COUNT(*) AS person_snapshots,COUNT(DISTINCT snapshot_date) AS snapshots,
       SUM(CASE WHEN manager_id IS NOT NULL AND person_months<=0 THEN 1 ELSE 0 END) AS nonpositive_denominator_violations,
       SUM(CASE WHEN exits12<0 OR exits12>person_months THEN 1 ELSE 0 END) AS numerator_exposure_violations,
       SUM(future_events) AS future_events_excluded,SUM(late_known) AS late_known_events_excluded,
       SUM(CASE WHEN band='0' THEN 1 ELSE 0 END) AS band_0,
       SUM(CASE WHEN band='>0-<0.5' THEN 1 ELSE 0 END) AS band_gt0_lt05,
       SUM(CASE WHEN band='0.5-<1' THEN 1 ELSE 0 END) AS band_05_lt1,
       SUM(CASE WHEN band='1+' THEN 1 ELSE 0 END) AS band_1_plus,
       SUM(CASE WHEN band='(unknown)' THEN 1 ELSE 0 END) AS band_unknown,
       MAX(person_months) AS maximum_person_months,
       ROUND(MAX(CASE WHEN person_months>0 THEN 100.0*exits12/person_months END),4) AS maximum_rate_per_100_person_months
FROM checked;
