/*
  V7 annual attrition trend for the comp-ratio slide.

  Claim: the two series compare one-year voluntary-exit incidence after each
  active non-RF360 Critical Tech employee snapshot. The compa-ratio band is measured at the
  snapshot; term dates strictly after that snapshot are the outcome.

  Population: worker_type='Employee', employee_type='Regular', active_status=1,
  is_rf360_yes_no=0, exact current Critical Tech catalogue match, seg <> 'Other Eng'.
  Outcome: strict term_type='VOLUNTARY' in (snapshot_date, snapshot_date + 12 months].
  History: the 24 latest monthly snapshots with complete 12-month follow-up.
  Privacy: output is aggregate-only. Each emitted point has at least 30
  employee-snapshot exposures and 30 voluntary outcomes.

  Acceptance rule: each emitted point must have a complete annual window,
  positive denominator, 0 <= rate <= 100, and meet the publication threshold.
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
    MAX(w.compa_ratio) AS compa_ratio
  FROM hrda.post_hire_monthly_worker_dtls AS w
  INNER JOIN eligible_snapshot_dates AS d
    ON CAST(w.fis_mo_end_dt AS DATE) = d.snapshot_date
  INNER JOIN critical_tech_catalog AS c
    ON c.normalized_job_family = LOWER(TRIM(w.job_family))
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.is_rf360_yes_no = 0
  GROUP BY 1, 2
),
voluntary_events AS (
  SELECT employee_id, CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(256))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
  GROUP BY 1, 2
),
targets AS (
  SELECT
    s.snapshot_date,
    s.employee_id,
    CASE WHEN s.compa_ratio IS NOT NULL AND s.compa_ratio < 0.8
      THEN '<0.8 (incl. 0)' ELSE '>=0.8' END AS group_label,
    MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
  FROM snapshot_rows AS s
  LEFT JOIN voluntary_events AS v
    ON v.employee_id = s.employee_id
   AND v.term_date > s.snapshot_date
   AND v.term_date <= DATEADD(month, 12, s.snapshot_date)
  GROUP BY 1, 2, 3
),
monthly AS (
  SELECT
    snapshot_date,
    group_label,
    COUNT(*) AS employee_snapshot_count,
    SUM(voluntary_attrition_target) AS voluntary_exits,
    100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0) AS attrition_rate_percent
  FROM targets
  GROUP BY 1, 2
)
SELECT
  snapshot_date,
  group_label,
  employee_snapshot_count,
  voluntary_exits,
  ROUND(attrition_rate_percent, 4) AS attrition_rate_percent
FROM monthly
WHERE employee_snapshot_count >= 30
  AND voluntary_exits >= 30
ORDER BY snapshot_date, group_label
