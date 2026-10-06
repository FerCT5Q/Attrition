-- Aggregate-only transition audit for work_arrangement.
--
-- A category change between adjacent monthly snapshots is temporally supported
-- when either the current start date or prior end date lies in the interval
-- (prior_snapshot, current_snapshot]. The rule tests date alignment; it does
-- not establish the business meaning of a category or its mapping to Remote,
-- Hybrid, or In office.

WITH base AS (
  SELECT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    UPPER(NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), ''))
      AS normalized_work_arrangement,
    CAST(work_arrangement_start_date AS DATE) AS work_arrangement_start_date,
    CAST(work_arrangement_end_date AS DATE) AS work_arrangement_end_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
    AND NULLIF(TRIM(CAST(work_arrangement AS VARCHAR(256))), '') IS NOT NULL
),
sequenced AS (
  SELECT
    employee_id,
    snapshot_date,
    normalized_work_arrangement,
    work_arrangement_start_date,
    work_arrangement_end_date,
    LAG(snapshot_date) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS prior_snapshot_date,
    LAG(normalized_work_arrangement) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS prior_work_arrangement,
    LAG(work_arrangement_end_date) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS prior_work_arrangement_end_date
  FROM base
),
adjacent AS (
  SELECT
    employee_id,
    snapshot_date,
    normalized_work_arrangement,
    work_arrangement_start_date,
    work_arrangement_end_date,
    prior_snapshot_date,
    prior_work_arrangement,
    prior_work_arrangement_end_date
  FROM sequenced
  WHERE prior_snapshot_date IS NOT NULL
    AND DATEDIFF(day, prior_snapshot_date, snapshot_date) BETWEEN 20 AND 45
)
SELECT
  COUNT(*) AS adjacent_populated_snapshot_pairs,
  SUM(CASE
    WHEN normalized_work_arrangement <> prior_work_arrangement THEN 1 ELSE 0
  END) AS category_change_pairs,
  SUM(CASE
    WHEN normalized_work_arrangement <> prior_work_arrangement
     AND work_arrangement_start_date > prior_snapshot_date
     AND work_arrangement_start_date <= snapshot_date
    THEN 1 ELSE 0
  END) AS changes_with_current_start_in_interval,
  SUM(CASE
    WHEN normalized_work_arrangement <> prior_work_arrangement
     AND prior_work_arrangement_end_date > prior_snapshot_date
     AND prior_work_arrangement_end_date <= snapshot_date
    THEN 1 ELSE 0
  END) AS changes_with_prior_end_in_interval,
  SUM(CASE
    WHEN normalized_work_arrangement <> prior_work_arrangement
     AND (
       (work_arrangement_start_date > prior_snapshot_date
        AND work_arrangement_start_date <= snapshot_date)
       OR (prior_work_arrangement_end_date > prior_snapshot_date
        AND prior_work_arrangement_end_date <= snapshot_date)
     )
    THEN 1 ELSE 0
  END) AS changes_with_boundary_evidence,
  SUM(CASE
    WHEN normalized_work_arrangement <> prior_work_arrangement
     AND CASE
       WHEN work_arrangement_start_date > prior_snapshot_date
        AND work_arrangement_start_date <= snapshot_date
       THEN 1 ELSE 0
     END = 0
     AND CASE
       WHEN prior_work_arrangement_end_date > prior_snapshot_date
        AND prior_work_arrangement_end_date <= snapshot_date
       THEN 1 ELSE 0
     END = 0
    THEN 1 ELSE 0
  END) AS changes_without_boundary_evidence
FROM adjacent;
