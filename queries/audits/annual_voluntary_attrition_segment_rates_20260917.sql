/*
  V7 distribution deck: annual voluntary attrition after the prediction snapshot.

  Purpose
  -------
  Return aggregate, privacy-safe segment rates for the visual categories that
  have a direct or bounded time-safe representation in HRDA.  The result is
  descriptive evidence for the presentation deck; it is not an employee-level
  prediction, a model score, or causal evidence.

  Outcome contract
  ----------------
  Population: active non-RF360 Critical Tech Employees at each monthly snapshot
      worker_type = 'Employee'
      employee_type = 'Regular'
      active_status = 1
      is_rf360_yes_no = 0
      exact current Critical Tech catalogue match; seg <> 'Other Eng'
  Target: at least one strict term_type = 'VOLUNTARY' event in
      (snapshot_date, snapshot_date + 12 months].
  Excluded: Voluntary Exception, null / ambiguous term types, involuntary
      terminations, and any event on or before the snapshot.
  History: the latest 24 monthly snapshots whose full 12-month follow-up is
      observable in the source.
  Privacy: results are aggregate only. Every emitted category has at least 30
      distinct employees and at least 30 employee-snapshot exposures.

  Acceptance rule for this display query
  --------------------------------------
  Every emitted category must reconcile to a distinct-employee aggregate,
  remain above the publication threshold, and use only information present in
  the employee snapshot.  Categories whose semantic definition, source or
  time-safe join is not established are intentionally absent and must render as
  "Attrition not estimable" in V7.
*/
WITH critical_tech_catalog AS (
  SELECT LOWER(TRIM(extended_job_family)) AS normalized_job_family
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
  GROUP BY 1
  HAVING COUNT(DISTINCT NULLIF(TRIM(seg), '')) = 1
     AND MAX(NULLIF(TRIM(seg), '')) <> 'Other Eng'
),
source_bounds AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
),
eligible_snapshot_dates AS (
  SELECT snapshot_date
  FROM (
    SELECT
      CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
      ROW_NUMBER() OVER (ORDER BY CAST(fis_mo_end_dt AS DATE) DESC) AS recency_rank
    FROM hrda.post_hire_monthly_worker_dtls
    CROSS JOIN source_bounds
    WHERE fis_mo_end_dt IS NOT NULL
      AND CAST(fis_mo_end_dt AS DATE) <= DATEADD(month, -12, latest_snapshot_date)
    GROUP BY 1
  ) dated
  WHERE recency_rank <= 24
),
snapshot_rows AS (
  SELECT
    CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
    w.employee_id,
    MAX(NULLIF(TRIM(CAST(w.country AS VARCHAR(256))), '')) AS country,
    MAX(NULLIF(TRIM(CAST(w.office_site AS VARCHAR(256))), '')) AS office_site,
    MAX(NULLIF(TRIM(CAST(w.city AS VARCHAR(256))), '')) AS city,
    MAX(NULLIF(TRIM(CAST(w.job_family_group AS VARCHAR(256))), '')) AS job_family_group,
    MAX(NULLIF(TRIM(CAST(w.job_family AS VARCHAR(256))), '')) AS job_family,
    MAX(NULLIF(TRIM(CAST(w.region AS VARCHAR(256))), '')) AS region,
    MAX(NULLIF(TRIM(CAST(w.labor_market AS VARCHAR(256))), '')) AS labor_market,
    MAX(NULLIF(TRIM(CAST(w.gender AS VARCHAR(256))), '')) AS gender,
    MAX(NULLIF(TRIM(CAST(w.work_arrangement AS VARCHAR(256))), '')) AS work_arrangement,
    MAX(NULLIF(TRIM(CAST(w.eng_or_noneng AS VARCHAR(256))), '')) AS eng_or_noneng,
    MAX(COALESCE(w.is_rehire, 0)) AS is_rehire,
    MAX(w.prior_qc_work_years) AS prior_qc_work_years,
    MAX(NULLIF(TRIM(CAST(w.level_grouped AS VARCHAR(256))), '')) AS level_grouped,
    MAX(NULLIF(TRIM(CAST(w.management_level AS VARCHAR(256))), '')) AS management_level,
    MAX(NULLIF(TRIM(CAST(w.job_level_primary_position AS VARCHAR(256))), '')) AS job_level_primary_position,
    MAX(NULLIF(TRIM(CAST(w.compensation_grade AS VARCHAR(256))), '')) AS compensation_grade,
    MAX(w.compa_ratio) AS compa_ratio,
    MAX(CAST(w.max_hire_rehire_date AS DATE)) AS max_hire_rehire_date,
    MAX(CAST(w.promotion_date AS DATE)) AS promotion_date,
    MAX(COALESCE(w.manager_change, 0)) AS manager_change,
    MAX(COALESCE(w.is_transferred, 0)) AS is_transferred,
    MAX(COALESCE(w.location_change, 0)) AS location_change,
    MAX(COALESCE(w.job_family_change, 0)) AS job_family_change,
    MAX(COALESCE(w.cost_center_change, 0)) AS cost_center_change
  FROM hrda.post_hire_monthly_worker_dtls w
  INNER JOIN eligible_snapshot_dates d
    ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
  INNER JOIN critical_tech_catalog c
    ON c.normalized_job_family = LOWER(TRIM(w.job_family))
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.is_rf360_yes_no = 0
  GROUP BY 1, 2
),
voluntary_events AS (
  SELECT
    employee_id,
    CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
  GROUP BY 1, 2
),
target_flags AS (
  SELECT
    s.snapshot_date,
    s.employee_id,
    s.country,
    s.office_site,
    s.city,
    s.job_family_group,
    s.job_family,
    s.region,
    s.labor_market,
    s.gender,
    s.work_arrangement,
    s.eng_or_noneng,
    s.is_rehire,
    s.prior_qc_work_years,
    s.level_grouped,
    s.management_level,
    s.job_level_primary_position,
    s.compensation_grade,
    s.compa_ratio,
    s.max_hire_rehire_date,
    s.promotion_date,
    s.manager_change,
    s.is_transferred,
    s.location_change,
    s.job_family_change,
    s.cost_center_change,
    MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
  FROM snapshot_rows s
  LEFT JOIN voluntary_events v
    ON v.employee_id = s.employee_id
   AND v.term_date > s.snapshot_date
   AND v.term_date <= DATEADD(month, 12, s.snapshot_date)
  GROUP BY
    s.snapshot_date, s.employee_id, s.country, s.office_site, s.city,
    s.job_family_group, s.job_family, s.region, s.labor_market, s.gender,
    s.work_arrangement, s.eng_or_noneng, s.is_rehire, s.prior_qc_work_years,
    s.level_grouped, s.management_level, s.job_level_primary_position,
    s.compensation_grade, s.compa_ratio, s.max_hire_rehire_date, s.promotion_date,
    s.manager_change, s.is_transferred, s.location_change, s.job_family_change,
    s.cost_center_change
),
category_rows AS (
  SELECT 'country' AS metric, COALESCE(country, 'Sin país') AS category, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'office_site', COALESCE(office_site, 'Sin office site'), snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'office_site_city', CASE WHEN office_site IS NULL OR city IS NULL THEN 'Sin par office site · ciudad' ELSE office_site || ' · ' || city END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'job_family_group', COALESCE(job_family_group, 'Sin job family group'), snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'job_family', COALESCE(job_family, 'Sin job family'), snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'region', COALESCE(region, 'Sin región'), snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'region_country_split', CASE
    WHEN UPPER(country) IN ('UNITED STATES OF AMERICA', 'UNITED STATES', 'USA', 'U.S.A.') THEN 'United States'
    WHEN UPPER(region) = 'AMERICAS' THEN 'Americas excluding U.S.'
    WHEN UPPER(country) = 'CHINA' THEN 'China'
    WHEN UPPER(region) = 'APAC' THEN 'APAC excluding China'
    WHEN region IS NULL THEN 'Sin región'
    ELSE region END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'labor_market', COALESCE(labor_market, 'Sin Labor Market'), snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'gender', CASE
    WHEN UPPER(gender) = 'F' THEN 'Category A'
    WHEN UPPER(gender) = 'M' THEN 'Category B'
    ELSE 'Unknown / other' END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'work_arrangement', CASE
    WHEN UPPER(COALESCE(work_arrangement, '')) LIKE '%MEDICAL%'
      OR UPPER(COALESCE(work_arrangement, '')) LIKE '%CAREGIV%'
      OR UPPER(COALESCE(work_arrangement, '')) LIKE '%LOA%'
    THEN 'Restricted arrangement categories'
    ELSE COALESCE(work_arrangement, 'Sin modalidad') END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'work_arrangement_binary', CASE WHEN UPPER(work_arrangement) = 'ONSITE' THEN 'Onsite (1)' ELSE 'Other stored values (0)' END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'engineering', COALESCE(eng_or_noneng, 'Sin clasificación'), snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'rehire', CASE WHEN is_rehire = 1 THEN 'Rehire (1)' ELSE 'Not rehire (0)' END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'prior_experience_years', CASE
    WHEN prior_qc_work_years IS NULL THEN 'Sin valor'
    WHEN prior_qc_work_years < 1 THEN '<1'
    WHEN prior_qc_work_years >= 32 THEN '32+'
    ELSE CAST(FLOOR(prior_qc_work_years) AS VARCHAR(32)) END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'level_grouped', COALESCE(level_grouped, 'Sin level'), snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'management_level', COALESCE(management_level, 'Sin management level'), snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'job_level', COALESCE(job_level_primary_position, 'Sin job level'), snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'compensation_grade', COALESCE(compensation_grade, 'Sin compensation grade'), snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'comp_ratio_band', CASE
    WHEN compa_ratio IS NULL THEN 'Sin valor'
    WHEN compa_ratio <= 0 THEN '≤ 0'
    WHEN compa_ratio < 0.8 THEN '> 0–< 0.8'
    WHEN compa_ratio < 0.9 THEN '0.8–< 0.9'
    WHEN compa_ratio < 1.0 THEN '0.9–< 1.0'
    WHEN compa_ratio < 1.1 THEN '1.0–< 1.1'
    WHEN compa_ratio < 1.25 THEN '1.1–< 1.25'
    ELSE '≥ 1.25' END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'company_tenure', CASE
    WHEN max_hire_rehire_date IS NULL THEN 'Sin fecha de hire/rehire'
    WHEN DATEDIFF(month, max_hire_rehire_date, snapshot_date) < 12 THEN '<1 año'
    WHEN DATEDIFF(month, max_hire_rehire_date, snapshot_date) < 24 THEN '1–<2 años'
    WHEN DATEDIFF(month, max_hire_rehire_date, snapshot_date) < 48 THEN '2–<4 años'
    WHEN DATEDIFF(month, max_hire_rehire_date, snapshot_date) < 72 THEN '4–<6 años'
    WHEN DATEDIFF(month, max_hire_rehire_date, snapshot_date) < 120 THEN '6–<10 años'
    ELSE '10+ años' END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'time_since_promotion', CASE
    WHEN promotion_date IS NULL THEN 'Sin promoción registrada'
    WHEN promotion_date > snapshot_date THEN 'Fecha futura / no usable'
    WHEN DATEDIFF(month, promotion_date, snapshot_date) < 12 THEN '<1 año'
    WHEN DATEDIFF(month, promotion_date, snapshot_date) < 24 THEN '1–<2 años'
    WHEN DATEDIFF(month, promotion_date, snapshot_date) < 48 THEN '2–<4 años'
    WHEN DATEDIFF(month, promotion_date, snapshot_date) < 60 THEN '4–<5 años'
    ELSE '5+ años' END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'manager_change', CASE WHEN manager_change = 1 THEN 'Manager change (1)' ELSE 'No manager change (0)' END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'transfer_event', CASE WHEN is_transferred = 1 THEN 'Transfer (1)' ELSE 'No transfer (0)' END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
  UNION ALL SELECT 'major_inflection_proxy', CASE WHEN manager_change = 1 OR is_transferred = 1 OR location_change = 1 OR job_family_change = 1 OR cost_center_change = 1 THEN '1+ proxy movement' ELSE 'No proxy movement' END, snapshot_date, employee_id, voluntary_attrition_target FROM target_flags
),
metric_baselines AS (
  SELECT
    metric,
    COUNT(*) AS baseline_employee_snapshots,
    SUM(voluntary_attrition_target) AS baseline_voluntary_exits,
    100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0) AS baseline_rate_percent
  FROM category_rows
  GROUP BY 1
),
category_metrics AS (
  SELECT
    metric,
    category,
    MIN(snapshot_date) AS first_snapshot_date,
    MAX(snapshot_date) AS last_snapshot_date,
    COUNT(DISTINCT employee_id) AS employee_count,
    COUNT(*) AS employee_snapshot_count,
    SUM(voluntary_attrition_target) AS voluntary_exits,
    100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0) AS attrition_rate_percent
  FROM category_rows
  GROUP BY 1, 2
)
SELECT
  c.metric,
  c.category,
  c.first_snapshot_date,
  c.last_snapshot_date,
  c.employee_count,
  c.employee_snapshot_count,
  c.voluntary_exits,
  ROUND(c.attrition_rate_percent, 4) AS attrition_rate_percent,
  b.baseline_employee_snapshots,
  b.baseline_voluntary_exits,
  ROUND(b.baseline_rate_percent, 4) AS baseline_rate_percent,
  ROUND(c.attrition_rate_percent / NULLIF(b.baseline_rate_percent, 0), 4) AS lift_vs_baseline
FROM category_metrics c
INNER JOIN metric_baselines b
  ON b.metric = c.metric
WHERE c.employee_count >= 30
  AND c.employee_snapshot_count >= 30
  AND c.voluntary_exits >= 30
ORDER BY c.metric, c.attrition_rate_percent DESC, c.category
