-- Aggregate-only coverage check for a deliberately conservative candidate
-- mapping of work_arrangement:
--   ONSITE                  -> In office
--   labels explicitly containing REMOTE -> Remote
--   every other label / blank -> Unclassified
-- No source label is disclosed by this query.
--
-- Acceptance rule for coverage only: at least 95% of all eligible active
-- Regular Employee snapshots must be explicitly classified in each of the
-- latest three monthly snapshots. Passing this rule does not prove the
-- business definition, handling of exceptions, or approval of the mapping.

WITH dated_snapshots AS (
  SELECT
    snapshot_date,
    ROW_NUMBER() OVER (ORDER BY snapshot_date DESC) AS snapshot_rank
  FROM (
    SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt IS NOT NULL
  ) dates
),
latest_three AS (
  SELECT snapshot_date
  FROM dated_snapshots
  WHERE snapshot_rank <= 3
),
base AS (
  SELECT
    CAST(w.fis_mo_end_dt AS DATE) AS snapshot_date,
    w.employee_id,
    REGEXP_REPLACE(
      UPPER(NULLIF(TRIM(CAST(w.work_arrangement AS VARCHAR(256))), '')),
      '^[A-Z0-9]+\\.\\s*', ''
    ) AS canonical_category
  FROM hrda.post_hire_monthly_worker_dtls w
  JOIN latest_three l
    ON CAST(w.fis_mo_end_dt AS DATE) = l.snapshot_date
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
),
classified AS (
  SELECT
    snapshot_date,
    employee_id,
    canonical_category,
    CASE
      WHEN canonical_category = 'ONSITE' THEN 'in_office'
      WHEN canonical_category LIKE '%REMOTE%' THEN 'remote'
      ELSE NULL
    END AS conservative_work_mode
  FROM base
)
SELECT
  snapshot_date,
  COUNT(DISTINCT employee_id) AS eligible_employees,
  COUNT(DISTINCT CASE WHEN canonical_category IS NOT NULL THEN employee_id END)
    AS populated_work_arrangement_employees,
  COUNT(DISTINCT CASE WHEN conservative_work_mode IS NOT NULL THEN employee_id END)
    AS explicitly_classified_employees,
  COUNT(DISTINCT CASE WHEN conservative_work_mode = 'in_office' THEN employee_id END)
    AS in_office_employees,
  COUNT(DISTINCT CASE WHEN conservative_work_mode = 'remote' THEN employee_id END)
    AS remote_employees,
  COUNT(DISTINCT CASE
    WHEN canonical_category IS NOT NULL AND conservative_work_mode IS NULL
    THEN employee_id END) AS populated_but_unclassified_employees,
  COUNT(DISTINCT CASE WHEN canonical_category IS NULL THEN employee_id END)
    AS missing_work_arrangement_employees,
  ROUND(
    100.0 * COUNT(DISTINCT CASE WHEN conservative_work_mode IS NOT NULL THEN employee_id END)
      / NULLIF(COUNT(DISTINCT employee_id), 0),
    4
  ) AS explicit_classification_percent_of_eligible,
  ROUND(
    100.0 * COUNT(DISTINCT CASE WHEN conservative_work_mode IS NOT NULL THEN employee_id END)
      / NULLIF(COUNT(DISTINCT CASE WHEN canonical_category IS NOT NULL THEN employee_id END), 0),
    4
  ) AS explicit_classification_percent_of_populated
FROM classified
GROUP BY snapshot_date
ORDER BY snapshot_date;
