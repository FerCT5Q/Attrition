-- Question: does hrda.job_applications_vw contain a material volume of usable
-- candidate application events after the historical hrda.applications cut-off?
-- Semantic type: profile of a proposed input source for the derived feature
-- "Applied to a job"; it is not yet a confirmation of business semantics.
-- Reporting mode: presentation (aggregate-only).
-- Population: all rows dated 2024-01-01 through 2026-12-31 in the candidate
-- source. The qualified-event subset additionally requires cand_applied = 1
-- and non-null employee_id, req_id, and application_date.
-- Grain: source row for completeness metrics; deduplicated
-- employee_id + application_date + req_id for qualified-event metrics.
-- Acceptance rule: diagnostic. A source supports further validation when
-- qualified unique event keys continue beyond 2025 and the key inputs are not
-- systematically absent. It still needs lineage, scope, and snapshot-join
-- validation before the feature can be defined or scored.
WITH base AS (
  SELECT
    application_date,
    cand_applied,
    employee_id,
    req_id
  FROM hrda.job_applications_vw
  WHERE application_date BETWEEN DATE '2024-01-01' AND DATE '2026-12-31'
),
row_profile AS (
  SELECT
    EXTRACT(YEAR FROM application_date)::INTEGER AS calendar_year,
    COUNT(*) AS source_rows,
    SUM(CASE WHEN cand_applied = 1 THEN 1 ELSE 0 END) AS cand_applied_rows,
    SUM(CASE WHEN cand_applied = 1 AND employee_id IS NOT NULL THEN 1 ELSE 0 END) AS cand_applied_with_employee_rows,
    SUM(CASE WHEN cand_applied = 1 AND req_id IS NOT NULL THEN 1 ELSE 0 END) AS cand_applied_with_req_rows,
    SUM(CASE WHEN cand_applied = 1 AND employee_id IS NOT NULL AND req_id IS NOT NULL THEN 1 ELSE 0 END) AS fully_keyed_cand_applied_rows,
    COUNT(DISTINCT CASE WHEN cand_applied = 1 AND employee_id IS NOT NULL THEN employee_id END) AS distinct_employees_with_cand_applied
  FROM base
  GROUP BY 1
),
qualified_event_keys AS (
  SELECT
    EXTRACT(YEAR FROM application_date)::INTEGER AS calendar_year,
    employee_id,
    application_date,
    TRIM(req_id) AS req_id
  FROM base
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
  GROUP BY 1, 2, 3, 4
),
key_profile AS (
  SELECT
    calendar_year,
    COUNT(*) AS qualified_unique_event_keys,
    COUNT(DISTINCT employee_id) AS qualified_distinct_employees,
    COUNT(DISTINCT req_id) AS qualified_distinct_requisitions
  FROM qualified_event_keys
  GROUP BY 1
)
SELECT
  row_profile.calendar_year,
  row_profile.source_rows,
  row_profile.cand_applied_rows,
  row_profile.cand_applied_with_employee_rows,
  row_profile.cand_applied_with_req_rows,
  row_profile.fully_keyed_cand_applied_rows,
  row_profile.distinct_employees_with_cand_applied,
  key_profile.qualified_unique_event_keys,
  key_profile.qualified_distinct_employees,
  key_profile.qualified_distinct_requisitions,
  ROUND(100.0 * row_profile.fully_keyed_cand_applied_rows / NULLIF(row_profile.cand_applied_rows, 0), 4) AS fully_keyed_rate_percent
FROM row_profile
LEFT JOIN key_profile
  ON key_profile.calendar_year = row_profile.calendar_year
ORDER BY row_profile.calendar_year;
