"""Materializa SQL agregado de las hipótesis explícitas de B incremental."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def build():
    source = ROOT / 'queries/profiles/engineering_b_incremental_pending_person_month_20261011.sql'
    if '--v2-team-pay' in sys.argv:
        corrected = source.read_text(encoding='utf-8').replace('COUNT(*) AS peer_n','COUNT(DISTINCT employee_id) AS peer_n').replace('COUNT(*) AS comparable_groups','COUNT(min_pay) AS comparable_groups')
        target = source.with_name(source.stem+'_v2.sql')
        audit = ROOT / 'queries/audits/engineering_b_incremental_team_pay_20261011.sql'
        audit_target = audit.with_name(audit.stem+'_v2.sql')
        if target.exists() or audit_target.exists():
            raise RuntimeError('La revisión de compensación ya existe.')
        target.write_text(corrected,encoding='utf-8')
        corrected_audit = audit.read_text(encoding='utf-8').replace('COUNT(*) AS peer_n','COUNT(DISTINCT employee_id) AS peer_n').replace('COUNT(*) AS comparable_groups','COUNT(min_pay) AS comparable_groups')
        audit_target.write_text(corrected_audit,encoding='utf-8')
        print('SQL v2: conteo explícito de integrantes y conteo de grupos con importe no nulo; contrastado con recálculo independiente.')
        return
    prefix = source.read_text(encoding='utf-8').split('-- MODEL_OUTPUT')[0].rstrip()
    prefix = prefix.replace('__PERIOD_START__', '2020-07-26').replace('__PERIOD_END__', '2026-09-07')
    queries = {
        'work_location': """
SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT employee_id) AS employee_count,
 COUNT(DISTINCT snapshot_date) AS snapshots,
 SUM(CASE WHEN source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_keys,
 SUM(CASE WHEN country_variants<>1 OR site_variants<>1 OR city_variants<>1 THEN 1 ELSE 0 END) AS contradictory_cells,
 SUM(CASE WHEN country IS NOT NULL THEN 1 ELSE 0 END) AS country_populated,
 SUM(CASE WHEN country IS NOT NULL AND office_site IS NOT NULL THEN 1 ELSE 0 END) AS site_populated,
 COUNT(DISTINCT country) AS country_categories,
 COUNT(DISTINCT country||' | '||office_site) AS site_categories
FROM population GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1
""",
        'grade_detail': """
SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT employee_id) AS employee_count,
 COUNT(DISTINCT snapshot_date) AS snapshots,
 SUM(CASE WHEN source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_keys,
 SUM(CASE WHEN grade_variants<>1 THEN 1 ELSE 0 END) AS contradictory_cells,
 SUM(CASE WHEN grade IS NOT NULL THEN 1 ELSE 0 END) AS grade_populated,
 COUNT(DISTINCT grade) AS grade_categories
FROM population GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1
""",
        'job_profile_time': """,
recalculated AS (
 SELECT p.snapshot_date,p.employee_id,p.job_start,p.episode_start,p.source_rows,
        p.job_start_variants,p.episode_variants,e.time_in_job_profile_band,
        CASE WHEN p.job_start IS NULL OR p.episode_start IS NULL
                   OR p.job_start>p.snapshot_date OR p.episode_start>p.snapshot_date THEN '(unknown)'
             WHEN GREATEST(p.job_start,p.episode_start)>DATEADD(month,-12,DATE_TRUNC('month',p.snapshot_date)) THEN '<1 year'
             WHEN GREATEST(p.job_start,p.episode_start)>DATEADD(month,-24,DATE_TRUNC('month',p.snapshot_date)) THEN '1-2 years'
             WHEN GREATEST(p.job_start,p.episode_start)>DATEADD(month,-36,DATE_TRUNC('month',p.snapshot_date)) THEN '2-3 years'
             WHEN GREATEST(p.job_start,p.episode_start)>DATEADD(month,-60,DATE_TRUNC('month',p.snapshot_date)) THEN '3-5 years'
             ELSE '5+ years' END AS independent_band
 FROM population p JOIN encoded e ON e.snapshot_date=p.snapshot_date AND e.employee_id=p.employee_id
)
SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT employee_id) AS employee_count,
 SUM(CASE WHEN source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_keys,
 SUM(CASE WHEN job_start_variants<>1 OR episode_variants<>1 THEN 1 ELSE 0 END) AS contradictory_cells,
 SUM(CASE WHEN job_start IS NOT NULL THEN 1 ELSE 0 END) AS source_date_present,
 SUM(CASE WHEN job_start>snapshot_date OR episode_start>snapshot_date THEN 1 ELSE 0 END) AS future_dates_excluded,
 SUM(CASE WHEN time_in_job_profile_band<>'(unknown)' THEN 1 ELSE 0 END) AS observable_rows,
 MIN(CASE WHEN time_in_job_profile_band<>'(unknown)' THEN snapshot_date END) AS first_observed_date,
 SUM(CASE WHEN (job_start IS NULL OR episode_start IS NULL OR job_start>snapshot_date OR episode_start>snapshot_date)
               AND time_in_job_profile_band<>'(unknown)' THEN 1 ELSE 0 END) AS invalid_dates_encoded_as_known,
 SUM(CASE WHEN independent_band<>time_in_job_profile_band THEN 1 ELSE 0 END) AS band_recalculation_mismatches
FROM recalculated GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1
""",
        'manager_location': """
SELECT EXTRACT(year FROM p.snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT p.employee_id) AS employee_count,
 SUM(CASE WHEN p.source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_keys,
 SUM(CASE WHEN p.manager_variants<>1 OR p.country_variants<>1 OR p.site_variants<>1 OR p.city_variants<>1 THEN 1 ELSE 0 END) AS contradictory_cells,
 SUM(CASE WHEN m.source_rows>1 OR m.country_variants>1 OR m.site_variants>1 OR m.city_variants>1 THEN 1 ELSE 0 END) AS ambiguous_manager_keys,
 SUM(CASE WHEN m.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_rows,
 SUM(CASE WHEN m.employee_id IS NULL THEN 1 ELSE 0 END) AS unmatched_rows,
 SUM(CASE WHEN e.manager_location_relation='(unknown)' THEN 1 ELSE 0 END) AS relation_unknown,
 SUM(CASE WHEN e.manager_location_relation='same recorded site' AND NOT(p.country=m.country AND p.office_site=m.office_site)
          THEN 1 WHEN e.manager_location_relation='same recorded city' AND NOT(p.country=m.country AND p.city=m.city)
          THEN 1 WHEN e.manager_location_relation='different country' AND p.country=m.country THEN 1
          WHEN m.employee_id IS NULL AND e.manager_location_relation<>'(unknown)' THEN 1 ELSE 0 END) AS relation_violations,
 COUNT(*)-COUNT(DISTINCT p.employee_id::VARCHAR||'|'||p.snapshot_date::VARCHAR) AS join_count_difference
FROM population p LEFT JOIN workforce m ON m.snapshot_date=p.snapshot_date AND m.employee_id=p.manager_id
JOIN encoded e ON e.snapshot_date=p.snapshot_date AND e.employee_id=p.employee_id
GROUP BY 1 HAVING COUNT(DISTINCT p.employee_id)>=30 ORDER BY 1
""",
        'team_pay': """,
rank_check AS (
 SELECT c.snapshot_date,c.manager_id,c.country,c.grade,c.currency,
        COUNT(*) AS n,AVG(r.relative_position) AS mean_rank
 FROM complete_pay c JOIN pay_position r ON r.snapshot_date=c.snapshot_date AND r.employee_id=c.employee_id
 WHERE r.peer_n>=5 GROUP BY 1,2,3,4,5
),
rank_year AS (
 SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
        SUM(CASE WHEN ABS(mean_rank-0.5)>0.0000001 THEN 1 ELSE 0 END) AS rank_midpoint_violations
 FROM rank_check GROUP BY 1
),
annual AS (
 SELECT EXTRACT(year FROM p.snapshot_date)::INTEGER AS year,
 COUNT(*) AS person_snapshots,COUNT(DISTINCT p.employee_id) AS employee_count,
 SUM(CASE WHEN p.source_rows<>1 THEN 1 ELSE 0 END) AS duplicate_keys,
 SUM(CASE WHEN p.pay_variants<>1 OR p.currency_variants<>1 OR p.grade_variants<>1
               OR p.country_variants<>1 OR p.manager_variants<>1 THEN 1 ELSE 0 END) AS contradictory_cells,
 SUM(CASE WHEN r.peer_n>=5 THEN 1 ELSE 0 END) AS comparable_position_rows,
 SUM(CASE WHEN s.comparable_groups>0 THEN 1 ELSE 0 END) AS comparable_spread_rows,
 SUM(CASE WHEN r.relative_position<0 OR r.relative_position>1 THEN 1 ELSE 0 END) AS rank_bound_violations,
 SUM(CASE WHEN s.flagged_groups<0 OR s.flagged_groups>s.comparable_groups THEN 1 ELSE 0 END) AS spread_violations,
 SUM(CASE WHEN COALESCE(r.peer_n,0)<5 AND e.within_team_pay_position<>'(no comparable group)' THEN 1 ELSE 0 END) AS small_group_position_violations
 FROM population p LEFT JOIN pay_position r ON r.snapshot_date=p.snapshot_date AND r.employee_id=p.employee_id
 LEFT JOIN manager_spread s ON s.snapshot_date=p.snapshot_date AND s.manager_id=p.manager_id
 JOIN encoded e ON e.snapshot_date=p.snapshot_date AND e.employee_id=p.employee_id
 GROUP BY 1
)
SELECT a.year,a.person_snapshots,a.employee_count,a.duplicate_keys,a.contradictory_cells,
 a.comparable_position_rows,a.comparable_spread_rows,a.rank_bound_violations,
 a.spread_violations,a.small_group_position_violations,COALESCE(r.rank_midpoint_violations,0) AS rank_midpoint_violations
FROM annual a LEFT JOIN rank_year r ON r.year=a.year WHERE a.employee_count>=30 ORDER BY a.year
"""
    }
    # Recalcular DATEDIFF(month) por números de mes, no por días ni aniversarios.
    q = queries['job_profile_time']
    for months in (12, 24, 36, 60):
        old = f"GREATEST(p.job_start,p.episode_start)>DATEADD(month,-{months},DATE_TRUNC('month',p.snapshot_date))"
        new = f"(EXTRACT(year FROM p.snapshot_date)*12+EXTRACT(month FROM p.snapshot_date))-(EXTRACT(year FROM GREATEST(p.job_start,p.episode_start))*12+EXTRACT(month FROM GREATEST(p.job_start,p.episode_start)))<{months}"
        q = q.replace(old, new)
    queries['job_profile_time'] = q
    for name, ending in queries.items():
        target = ROOT / f'queries/audits/engineering_b_incremental_{name}_20261011.sql'
        if target.exists():
            raise RuntimeError('No sobrescribir consultas ya materializadas.')
        target.write_text('/* Auditoría agregada: contrato en config/engineering_b_incremental_inputs_20261011.json. */\n'
                          + prefix + '\n' + ending.strip() + ';\n', encoding='utf-8')
    print(f'{len(queries)} consultas agregadas materializadas.')


if __name__ == '__main__':
    build()
