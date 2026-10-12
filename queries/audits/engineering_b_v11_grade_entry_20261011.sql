/* Entrada observada al grado en el episodio actual. Fechas y confirmación
   de promoción conocidas en cada foto. No usa compensation_grade_old. */
WITH targets AS (
 SELECT fis_mo_end_dt::DATE AS snapshot_date,employee_id
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE fis_mo_end_dt::DATE BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
 AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
 AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
 GROUP BY 1,2
),
history AS (
 SELECT w.fis_mo_end_dt::DATE AS snapshot_date,w.employee_id,
        MAX(NULLIF(UPPER(TRIM(w.compensation_grade)),'')) AS grade,
        MAX(w.max_hire_rehire_date::DATE) AS episode,
        MAX(w.is_promo) AS promo_flag,MAX(w.promotion_date::DATE) AS promo_date,
        COUNT(*) AS n,
        COUNT(DISTINCT COALESCE(UPPER(TRIM(w.compensation_grade)),'<NULL>')) AS grade_variants,
        COUNT(DISTINCT COALESCE(w.max_hire_rehire_date::VARCHAR,'<NULL>')) AS episode_variants,
        COUNT(DISTINCT COALESCE(w.is_promo::VARCHAR,'<NULL>')||'|'||COALESCE(w.promotion_date::VARCHAR,'<NULL>')) AS promo_variants
 FROM hrda.post_hire_monthly_worker_dtls w
 JOIN (SELECT DISTINCT employee_id FROM targets) p ON p.employee_id=w.employee_id
 WHERE w.fis_mo_end_dt::DATE<=DATE '2026-09-07'
 GROUP BY 1,2
),
timeline AS (
 SELECT snapshot_date,employee_id,grade,episode,promo_flag,promo_date,n,
        grade_variants,episode_variants,promo_variants,
        LAG(snapshot_date) OVER(PARTITION BY employee_id ORDER BY snapshot_date) AS previous_date,
        LAG(grade) OVER(PARTITION BY employee_id ORDER BY snapshot_date) AS previous_grade,
        LAG(episode) OVER(PARTITION BY employee_id ORDER BY snapshot_date) AS previous_episode
 FROM history
),
running AS (
 SELECT snapshot_date,employee_id,grade,episode,n,grade_variants,episode_variants,promo_variants,
        previous_date,previous_grade,previous_episode,
        MAX(CASE WHEN grade IS NOT NULL AND previous_grade IS NOT NULL AND grade<>previous_grade
                  AND episode=previous_episode AND previous_date>=episode
                  AND DATEDIFF(day,previous_date,snapshot_date)<=45
                  AND n=1 AND grade_variants=1 AND episode_variants=1 THEN snapshot_date END)
          OVER(PARTITION BY employee_id,episode,grade ORDER BY snapshot_date ROWS UNBOUNDED PRECEDING) AS last_entry,
        MAX(CASE WHEN previous_date IS NULL OR previous_grade IS NULL OR grade IS NULL
                  OR previous_episode<>episode OR DATEDIFF(day,previous_date,snapshot_date)>45
                  OR n<>1 OR grade_variants<>1 OR episode_variants<>1 THEN snapshot_date END)
          OVER(PARTITION BY employee_id,episode ORDER BY snapshot_date ROWS UNBOUNDED PRECEDING) AS last_break
 FROM timeline
),
promotions AS (
 SELECT employee_id,grade,episode,promo_date,MIN(snapshot_date) AS known_date
 FROM history
 WHERE promo_flag=1 AND promo_date IS NOT NULL AND promo_date<=snapshot_date
 AND promo_date>=episode AND n=1 AND grade_variants=1 AND episode_variants=1 AND promo_variants=1
 GROUP BY 1,2,3,4
),
linked AS (
 SELECT r.snapshot_date,r.employee_id,r.grade,r.episode,r.n,
        r.grade_variants,r.episode_variants,r.promo_variants,
        CASE WHEN r.last_entry>=r.last_break AND r.episode<=r.snapshot_date THEN r.last_entry END AS entry_date,
        e.previous_date AS before_entry_date,e.previous_episode AS before_entry_episode,
        e.previous_grade AS before_entry_grade,
        MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS confirmed_promotion,
        MAX(v.known_date) AS promotion_known_date,MAX(v.promo_date) AS confirmation_effective_date
 FROM running r JOIN targets t ON t.snapshot_date=r.snapshot_date AND t.employee_id=r.employee_id
 LEFT JOIN timeline e ON e.employee_id=r.employee_id AND e.snapshot_date=r.last_entry
 LEFT JOIN promotions v ON v.employee_id=r.employee_id AND v.grade=r.grade AND v.episode=r.episode
 AND v.promo_date>e.previous_date AND v.promo_date<=r.last_entry AND v.known_date<=r.snapshot_date
 GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12
),
encoded AS (
 SELECT snapshot_date,employee_id,grade,episode,n,grade_variants,episode_variants,promo_variants,
        entry_date,before_entry_date,before_entry_episode,before_entry_grade,
        confirmed_promotion,promotion_known_date,confirmation_effective_date,
        CASE WHEN entry_date IS NULL THEN '(historia no confirmada)'
             WHEN confirmed_promotion=1 THEN 'promotion confirmed'
             ELSE 'observed change without registered promotion' END AS current_grade_entry_path,
        CASE WHEN entry_date IS NULL THEN '(historia no confirmada)'
             WHEN DATEDIFF(month,entry_date,snapshot_date)<12 THEN '<1 year'
             WHEN DATEDIFF(month,entry_date,snapshot_date)<24 THEN '1-2 years'
             WHEN DATEDIFF(month,entry_date,snapshot_date)<36 THEN '2-3 years'
             WHEN DATEDIFF(month,entry_date,snapshot_date)<60 THEN '3-5 years'
             ELSE '5+ years' END AS time_since_grade_entry_band,
        CASE WHEN grade ~ '^[A-Z][0-9]+$' THEN LEFT(grade,1) ELSE '(unknown)' END AS pay_track_detail
 FROM linked
)

, checked AS (
 SELECT snapshot_date,employee_id,n,grade_variants,episode_variants,promo_variants,
 entry_date,before_entry_date,before_entry_episode,before_entry_grade,grade,episode,
 confirmed_promotion,promotion_known_date,confirmation_effective_date,
 current_grade_entry_path,time_since_grade_entry_band,pay_track_detail,
 CASE WHEN entry_date IS NULL THEN '(historia no confirmada)'
      WHEN (EXTRACT(year FROM snapshot_date)*12+EXTRACT(month FROM snapshot_date))-
           (EXTRACT(year FROM entry_date)*12+EXTRACT(month FROM entry_date))<12 THEN '<1 year'
      WHEN (EXTRACT(year FROM snapshot_date)*12+EXTRACT(month FROM snapshot_date))-
           (EXTRACT(year FROM entry_date)*12+EXTRACT(month FROM entry_date))<24 THEN '1-2 years'
      WHEN (EXTRACT(year FROM snapshot_date)*12+EXTRACT(month FROM snapshot_date))-
           (EXTRACT(year FROM entry_date)*12+EXTRACT(month FROM entry_date))<36 THEN '2-3 years'
      WHEN (EXTRACT(year FROM snapshot_date)*12+EXTRACT(month FROM snapshot_date))-
           (EXTRACT(year FROM entry_date)*12+EXTRACT(month FROM entry_date))<60 THEN '3-5 years'
      ELSE '5+ years' END AS independent_band
 FROM encoded
)
SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT employee_id) AS employee_count,
 SUM(CASE WHEN n<>1 THEN 1 ELSE 0 END) AS duplicate_keys,
 SUM(CASE WHEN grade_variants<>1 OR episode_variants<>1 OR promo_variants<>1 THEN 1 ELSE 0 END) AS contradictory_cells,
 SUM(CASE WHEN entry_date IS NOT NULL THEN 1 ELSE 0 END) AS observable_entry_rows,
 SUM(CASE WHEN current_grade_entry_path='promotion confirmed' THEN 1 ELSE 0 END) AS promotion_confirmed_rows,
 SUM(CASE WHEN entry_date>snapshot_date OR entry_date<episode OR before_entry_date<episode
               OR (entry_date IS NOT NULL AND (before_entry_episode<>episode OR before_entry_grade=grade OR DATEDIFF(day,before_entry_date,entry_date)>45)) THEN 1 ELSE 0 END) AS entry_rule_violations,
 SUM(CASE WHEN promotion_known_date>snapshot_date OR confirmation_effective_date>entry_date THEN 1 ELSE 0 END) AS promotion_future_violations,
 SUM(CASE WHEN independent_band<>time_since_grade_entry_band THEN 1 ELSE 0 END) AS band_recalculation_mismatches,
 SUM(CASE WHEN pay_track_detail<>'(unknown)' AND (LEFT(grade,1)<>pay_track_detail OR NOT(grade ~ '^[A-Z][0-9]+$')) THEN 1 ELSE 0 END) AS track_rule_violations,
 COUNT(DISTINCT pay_track_detail) AS track_categories
FROM checked GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1;
