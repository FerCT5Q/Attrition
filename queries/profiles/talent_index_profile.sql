SELECT
  CAST(last_modified_date AS DATE) AS snapshot_date,
  CAST(MAX(cycle_number) AS VARCHAR(32)) AS fiscal_year,
  COUNT(DISTINCT empl_id) AS eligible_employees,
  COUNT(DISTINCT CASE
    WHEN talent_index IS NOT NULL THEN empl_id
  END) AS observable_employees,
  CAST(NULL AS BIGINT) AS event_employees,
  'Coverage is source-internal by talent cycle and the composite includes leakage fields.' AS notes
FROM hrda.master_talent_index
WHERE last_modified_date IS NOT NULL
  AND empl_id IS NOT NULL
GROUP BY last_modified_date
HAVING COUNT(DISTINCT empl_id) >= 30
ORDER BY snapshot_date
