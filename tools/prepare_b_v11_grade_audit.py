"""SQL agregado de entrada al grado: reconciliación de reglas y bandas."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'queries/profiles/engineering_b_v11_grade_entry_person_month_20261011.sql'
target=ROOT/'queries/audits/engineering_b_v11_grade_entry_20261011.sql'
if target.exists():
    raise RuntimeError('La auditoría ya existe.')
prefix=source.read_text(encoding='utf-8').split('-- MODEL_OUTPUT')[0]
prefix=prefix.replace('__PERIOD_START__','2020-07-26').replace('__PERIOD_END__','2026-09-07')
suffix="""
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
"""
target.write_text(prefix+suffix,encoding='utf-8')
print('Auditoría de entrada al grado preparada.')
