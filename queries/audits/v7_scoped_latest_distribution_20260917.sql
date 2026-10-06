/*
  Current distributions for V7 after the approved population restriction.
  The source is one active employee snapshot at the latest available month.
  It returns aggregate counts only; no employee identifiers leave the query.

  Population: Employee + Regular + active_status=1 + is_rf360_yes_no=0,
  exact current Critical Tech catalogue match, excluding seg='Other Eng'.
*/
WITH critical_tech_catalog AS (
  SELECT LOWER(TRIM(extended_job_family)) AS normalized_job_family
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
  GROUP BY 1
  HAVING COUNT(DISTINCT NULLIF(TRIM(seg), '')) = 1
     AND MAX(NULLIF(TRIM(seg), '')) <> 'Other Eng'
),
latest_snapshot AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
),
scoped_snapshot AS (
  SELECT
    w.employee_id,
    MAX(NULLIF(TRIM(w.country), '')) AS country,
    MAX(NULLIF(TRIM(w.office_site), '')) AS office_site,
    MAX(NULLIF(TRIM(w.city), '')) AS city,
    MAX(NULLIF(TRIM(w.job_family), '')) AS job_family,
    MAX(NULLIF(TRIM(w.region), '')) AS region,
    MAX(NULLIF(TRIM(w.labor_market), '')) AS labor_market,
    MAX(NULLIF(TRIM(w.gender), '')) AS gender,
    MAX(NULLIF(TRIM(w.work_arrangement), '')) AS work_arrangement,
    MAX(NULLIF(TRIM(w.eng_or_noneng), '')) AS eng_or_noneng,
    MAX(COALESCE(w.is_rehire, 0)) AS is_rehire,
    MAX(w.prior_qc_work_years) AS prior_qc_work_years,
    MAX(NULLIF(TRIM(w.level_grouped), '')) AS level_grouped,
    MAX(NULLIF(TRIM(w.management_level), '')) AS management_level,
    MAX(NULLIF(TRIM(w.job_level_primary_position), '')) AS job_level_primary_position,
    MAX(NULLIF(TRIM(w.compensation_grade), '')) AS compensation_grade,
    MAX(w.compa_ratio) AS compa_ratio,
    MAX(CAST(w.max_hire_rehire_date AS DATE)) AS max_hire_rehire_date,
    MAX(CAST(w.promotion_date AS DATE)) AS promotion_date,
    MAX(COALESCE(w.manager_change, 0)) AS manager_change,
    MAX(COALESCE(w.is_transferred, 0)) AS is_transferred,
    MAX(COALESCE(w.location_change, 0)) AS location_change,
    MAX(COALESCE(w.job_family_change, 0)) AS job_family_change,
    MAX(COALESCE(w.cost_center_change, 0)) AS cost_center_change
  FROM hrda.post_hire_monthly_worker_dtls AS w
  INNER JOIN latest_snapshot AS d
    ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
  INNER JOIN critical_tech_catalog AS c
    ON c.normalized_job_family = LOWER(TRIM(w.job_family))
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.is_rf360_yes_no = 0
  GROUP BY w.employee_id
),
unpivoted AS (
  SELECT 'country' AS metric, COALESCE(country, 'Unknown') AS category FROM scoped_snapshot
  UNION ALL SELECT 'office_site', COALESCE(office_site, 'Unknown') FROM scoped_snapshot
  UNION ALL SELECT 'office_site_city', CASE WHEN office_site IS NULL OR city IS NULL THEN 'Unknown' ELSE office_site || ' · ' || city END FROM scoped_snapshot
  UNION ALL SELECT 'job_family', COALESCE(job_family, 'Unknown') FROM scoped_snapshot
  UNION ALL SELECT 'region', COALESCE(region, 'Unknown') FROM scoped_snapshot
  UNION ALL SELECT 'region_country_split', CASE WHEN country IN ('India', 'United States of America', 'China') THEN country ELSE COALESCE(region, 'Unknown') END FROM scoped_snapshot
  UNION ALL SELECT 'labor_market', COALESCE(labor_market, 'Unknown') FROM scoped_snapshot
  UNION ALL SELECT 'gender', CASE WHEN gender IS NULL THEN 'Unknown / other' WHEN UPPER(gender) LIKE 'F%' THEN 'Group A' WHEN UPPER(gender) LIKE 'M%' THEN 'Group B' ELSE 'Unknown / other' END FROM scoped_snapshot
  UNION ALL SELECT 'work_arrangement', CASE WHEN work_arrangement IS NULL THEN 'Unknown' WHEN UPPER(work_arrangement) SIMILAR TO '%(MEDICAL|CAREGIV|LOA)%' THEN 'Restricted arrangement categories' ELSE work_arrangement END FROM scoped_snapshot
  UNION ALL SELECT 'work_arrangement_binary', CASE WHEN UPPER(work_arrangement) = 'ONSITE' THEN 'Onsite (1)' ELSE 'Other stored values (0)' END FROM scoped_snapshot
  UNION ALL SELECT 'engineering', COALESCE(eng_or_noneng, 'Unknown') FROM scoped_snapshot
  UNION ALL SELECT 'rehire', CASE WHEN is_rehire = 1 THEN 'Rehire (1)' ELSE 'Not rehire (0)' END FROM scoped_snapshot
  UNION ALL SELECT 'prior_experience_years', CASE WHEN prior_qc_work_years IS NULL THEN 'Unknown' WHEN prior_qc_work_years < 1 THEN '0 years' WHEN prior_qc_work_years >= 20 THEN '20+ years' ELSE CAST(FLOOR(prior_qc_work_years) AS VARCHAR(32)) || ' years' END FROM scoped_snapshot
  UNION ALL SELECT 'level_grouped', COALESCE(level_grouped, 'Unknown') FROM scoped_snapshot
  UNION ALL SELECT 'management_level', COALESCE(management_level, 'Unknown') FROM scoped_snapshot
  UNION ALL SELECT 'job_level', COALESCE(job_level_primary_position, 'Unknown') FROM scoped_snapshot
  UNION ALL SELECT 'compensation_grade', COALESCE(compensation_grade, 'Unknown') FROM scoped_snapshot
  UNION ALL SELECT 'comp_ratio_band', CASE WHEN compa_ratio IS NULL THEN 'Unknown' WHEN compa_ratio < 0.8 THEN '<0.8 (incl. 0)' WHEN compa_ratio < 0.9 THEN '0.8–<0.9' WHEN compa_ratio < 1.0 THEN '0.9–<1.0' WHEN compa_ratio < 1.1 THEN '1.0–<1.1' WHEN compa_ratio < 1.25 THEN '1.1–<1.25' ELSE '≥1.25' END FROM scoped_snapshot
  UNION ALL SELECT 'company_tenure', CASE WHEN max_hire_rehire_date IS NULL THEN 'Unknown' WHEN DATEDIFF(day, max_hire_rehire_date, (SELECT snapshot_date FROM latest_snapshot)) < 365 THEN '<1 year' WHEN DATEDIFF(day, max_hire_rehire_date, (SELECT snapshot_date FROM latest_snapshot)) < 730 THEN '1–<2 years' WHEN DATEDIFF(day, max_hire_rehire_date, (SELECT snapshot_date FROM latest_snapshot)) < 1825 THEN '2–<5 years' WHEN DATEDIFF(day, max_hire_rehire_date, (SELECT snapshot_date FROM latest_snapshot)) < 3650 THEN '5–<10 years' ELSE '10+ years' END FROM scoped_snapshot
  UNION ALL SELECT 'time_since_promotion', CASE WHEN promotion_date IS NULL THEN 'No recorded promotion' WHEN DATEDIFF(day, promotion_date, (SELECT snapshot_date FROM latest_snapshot)) < 365 THEN '<1 year' WHEN DATEDIFF(day, promotion_date, (SELECT snapshot_date FROM latest_snapshot)) < 730 THEN '1–<2 years' WHEN DATEDIFF(day, promotion_date, (SELECT snapshot_date FROM latest_snapshot)) < 1825 THEN '2–<5 years' ELSE '5+ years' END FROM scoped_snapshot
  UNION ALL SELECT 'manager_change', CASE WHEN manager_change = 1 THEN 'Manager change (1)' ELSE 'No manager change (0)' END FROM scoped_snapshot
  UNION ALL SELECT 'transfer_event', CASE WHEN is_transferred = 1 THEN 'Transfer (1)' ELSE 'No transfer (0)' END FROM scoped_snapshot
  UNION ALL SELECT 'major_inflection_proxy', CASE WHEN manager_change = 1 OR is_transferred = 1 OR location_change = 1 OR job_family_change = 1 OR cost_center_change = 1 THEN '1+ proxy movement' ELSE 'No proxy movement' END FROM scoped_snapshot
),
counts AS (
  SELECT metric, category, COUNT(*) AS employee_count
  FROM unpivoted
  GROUP BY 1, 2
),
totals AS (
  SELECT metric, SUM(employee_count) AS scoped_employee_count
  FROM counts
  GROUP BY 1
)
SELECT
  (SELECT snapshot_date FROM latest_snapshot) AS snapshot_date,
  c.metric,
  c.category,
  c.employee_count,
  t.scoped_employee_count,
  ROUND(100.0 * c.employee_count / NULLIF(t.scoped_employee_count, 0), 4) AS workforce_share_percent
FROM counts AS c
INNER JOIN totals AS t
  ON t.metric = c.metric
WHERE c.employee_count >= 30
ORDER BY c.metric, c.employee_count DESC, c.category;
