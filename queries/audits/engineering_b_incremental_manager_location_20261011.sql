/* Auditoría agregada: contrato en config/engineering_b_incremental_inputs_20261011.json. */
/* B incremental: entradas adicionales. Sólo bandas y categorías en RAM bajo
   autorización 20261001; nunca se devuelven importes, IDs ni domicilios. */
WITH params AS (
  SELECT DATE '2020-07-26' AS period_start,
         DATE '2026-09-07' AS period_end
),
workforce AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id,
         MAX(TRIM(eng_or_noneng)) AS engineering,
         MAX(manager_employee_id) AS manager_id,
         MAX(NULLIF(UPPER(TRIM(job_family)),'')) AS job_family,
         MAX(NULLIF(UPPER(TRIM(job_family_group)),'')) AS job_family_group,
         MAX(NULLIF(UPPER(TRIM(country)),'')) AS country,
         MAX(NULLIF(UPPER(TRIM(city)),'')) AS city,
         MAX(NULLIF(UPPER(TRIM(office_site)),'')) AS office_site,
         MAX(NULLIF(UPPER(TRIM(compensation_grade)),'')) AS grade,
         MAX(CAST(time_in_job_profile_start_date AS DATE)) AS job_start,
         MAX(CAST(service_date AS DATE)) AS episode_start,
         MAX(fte_annual_base_pay) AS pay,
         MAX(NULLIF(UPPER(TRIM(fte_annual_base_pay_currency_code)),'')) AS currency,
         COUNT(*) AS source_rows,
         COUNT(DISTINCT COALESCE(UPPER(TRIM(job_family)),'<NULL>')) AS family_variants,
         COUNT(DISTINCT COALESCE(UPPER(TRIM(job_family_group)),'<NULL>')) AS group_variants,
         COUNT(DISTINCT COALESCE(UPPER(TRIM(country)),'<NULL>')) AS country_variants,
         COUNT(DISTINCT COALESCE(UPPER(TRIM(city)),'<NULL>')) AS city_variants,
         COUNT(DISTINCT COALESCE(UPPER(TRIM(office_site)),'<NULL>')) AS site_variants,
         COUNT(DISTINCT COALESCE(UPPER(TRIM(compensation_grade)),'<NULL>')) AS grade_variants,
         COUNT(DISTINCT COALESCE(CAST(manager_employee_id AS VARCHAR),'<NULL>')) AS manager_variants,
         COUNT(DISTINCT COALESCE(CAST(time_in_job_profile_start_date AS VARCHAR),'<NULL>')) AS job_start_variants,
         COUNT(DISTINCT COALESCE(CAST(service_date AS VARCHAR),'<NULL>')) AS episode_variants,
         COUNT(DISTINCT COALESCE(CAST(fte_annual_base_pay AS VARCHAR),'<NULL>')) AS pay_variants,
         COUNT(DISTINCT COALESCE(UPPER(TRIM(fte_annual_base_pay_currency_code)),'<NULL>')) AS currency_variants
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN (SELECT period_start FROM params) AND (SELECT period_end FROM params)
    AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
    AND is_rf360_yes_no=0 AND employee_id IS NOT NULL
  GROUP BY 1,2
),
population AS (
  SELECT snapshot_date, employee_id, engineering, manager_id,
         job_family, job_family_group, country, city, office_site, grade,
         job_start, episode_start, pay, currency, source_rows,
         family_variants, group_variants, country_variants, city_variants,
         site_variants, grade_variants, manager_variants, job_start_variants,
         episode_variants, pay_variants, currency_variants
  FROM workforce WHERE engineering='Engineering'
),
complete_pay AS (
  SELECT snapshot_date, employee_id, manager_id, country, grade, currency, pay
  FROM workforce
  WHERE manager_id IS NOT NULL AND manager_id<>employee_id
    AND country IS NOT NULL AND grade IS NOT NULL AND currency IS NOT NULL
    AND pay>0 AND pay_variants=1 AND currency_variants=1 AND grade_variants=1
    AND country_variants=1 AND manager_variants=1 AND source_rows=1
),
peer_stats AS (
  SELECT snapshot_date, manager_id, country, grade, currency,
         COUNT(*) AS peer_n, MIN(pay) AS min_pay, MAX(pay) AS max_pay
  FROM complete_pay GROUP BY 1,2,3,4,5
),
peer_ranks AS (
  SELECT snapshot_date, employee_id, manager_id, country, grade, currency,
         RANK() OVER(PARTITION BY snapshot_date,manager_id,country,grade,currency ORDER BY pay) AS first_rank,
         COUNT(*) OVER(PARTITION BY snapshot_date,manager_id,country,grade,currency,pay) AS tie_n
  FROM complete_pay
),
pay_position AS (
  SELECT r.snapshot_date, r.employee_id, s.peer_n,
         (r.first_rank-1.0+(r.tie_n-1.0)/2.0)/NULLIF(s.peer_n-1.0,0) AS relative_position
  FROM peer_ranks r JOIN peer_stats s
    ON s.snapshot_date=r.snapshot_date AND s.manager_id=r.manager_id
    AND s.country=r.country AND s.grade=r.grade AND s.currency=r.currency
),
manager_spread AS (
  SELECT snapshot_date, manager_id, COUNT(*) AS comparable_groups,
         SUM(CASE WHEN max_pay/min_pay>=1.10 THEN 1 ELSE 0 END) AS flagged_groups
  FROM peer_stats WHERE peer_n>=2 GROUP BY 1,2
),
encoded AS (
  SELECT p.snapshot_date, p.employee_id,
         COALESCE(p.job_family,'(unknown)') AS job_family_detail,
         COALESCE(p.job_family_group,'(unknown)') AS job_family_group,
         COALESCE(p.country,'(unknown)') AS work_country,
         CASE WHEN p.country IS NOT NULL AND p.office_site IS NOT NULL
              THEN p.country||' | '||p.office_site ELSE '(unknown)' END AS work_site,
         COALESCE(p.grade,'(unknown)') AS compensation_grade_detail,
         CASE WHEN p.job_start IS NULL OR p.episode_start IS NULL
                    OR p.job_start>p.snapshot_date OR p.episode_start>p.snapshot_date THEN '(unknown)'
              WHEN DATEDIFF(month,GREATEST(p.job_start,p.episode_start),p.snapshot_date)<12 THEN '<1 year'
              WHEN DATEDIFF(month,GREATEST(p.job_start,p.episode_start),p.snapshot_date)<24 THEN '1-2 years'
              WHEN DATEDIFF(month,GREATEST(p.job_start,p.episode_start),p.snapshot_date)<36 THEN '2-3 years'
              WHEN DATEDIFF(month,GREATEST(p.job_start,p.episode_start),p.snapshot_date)<60 THEN '3-5 years'
              ELSE '5+ years' END AS time_in_job_profile_band,
         CASE WHEN p.manager_id IS NULL OR m.employee_id IS NULL OR m.source_rows<>1
                    OR p.manager_variants<>1 OR m.country_variants<>1 OR m.site_variants<>1
                    OR m.city_variants<>1 OR p.country IS NULL OR m.country IS NULL THEN '(unknown)'
              WHEN p.country<>m.country THEN 'different country'
              WHEN p.office_site IS NOT NULL AND m.office_site IS NOT NULL
                    AND p.office_site=m.office_site THEN 'same recorded site'
              WHEN p.city IS NOT NULL AND m.city IS NOT NULL AND p.city=m.city THEN 'same recorded city'
              ELSE 'same country' END AS manager_location_relation,
         CASE WHEN r.peer_n IS NULL OR r.peer_n<5 THEN '(no comparable group)'
              WHEN r.relative_position<0.25 THEN 'lower quarter'
              WHEN r.relative_position>0.75 THEN 'upper quarter'
              ELSE 'middle half' END AS within_team_pay_position,
         CASE WHEN s.comparable_groups IS NULL THEN '(no comparable group)'
              WHEN s.flagged_groups=0 THEN 'none'
              WHEN s.flagged_groups=s.comparable_groups THEN 'all'
              ELSE 'some' END AS manager_pay_spread_band
  FROM population p
  LEFT JOIN workforce m ON m.snapshot_date=p.snapshot_date AND m.employee_id=p.manager_id
  LEFT JOIN pay_position r ON r.snapshot_date=p.snapshot_date AND r.employee_id=p.employee_id
  LEFT JOIN manager_spread s ON s.snapshot_date=p.snapshot_date AND s.manager_id=p.manager_id
)
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
GROUP BY 1 HAVING COUNT(DISTINCT p.employee_id)>=30 ORDER BY 1;
