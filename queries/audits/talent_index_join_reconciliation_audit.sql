-- Talent index: reconciliacion agregada del join empleado-snapshot.
--
-- Claim:
--   Cuantificar el join desde empleados regulares activos a Talent index usando una
--   regla tecnica conservadora: ultimo registro con fecha tecnica <= snapshot. Cuando
--   varios ciclos comparten fecha se usa cycle_number descendente como desempate y se
--   cuantifica cuantas filas requieren esa regla.
--
-- Population:
--   Empleados regulares activos por snapshot mensual.
--
-- Acceptance rule stated before execution for Join=2:
--   Cada empleado-snapshot elegible debe producir exactamente un match temporal, sin
--   unmatched, duplicados ni multi-match, y el desempate/fecha debe estar gobernado.
--   Si hay cobertura parcial o empates que requieren una regla no oficial, Join queda
--   como maximo en 1 aunque la transformacion tecnica sea determinista.

WITH eligible AS (
  SELECT
    CAST(employee_id AS BIGINT) AS employee_id,
    fis_mo_end_dt AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY 1, 2
),
raw_talent AS (
  SELECT
    CAST(empl_id AS BIGINT) AS employee_id,
    cycle_number,
    COALESCE(last_modified_date, airflow_execution_date) AS availability_date,
    talent_index
  FROM hrda.master_talent_index
  WHERE empl_id IS NOT NULL
    AND cycle_number IS NOT NULL
),
exact_keys AS (
  SELECT
    employee_id,
    cycle_number,
    availability_date,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT talent_index) AS distinct_index_values,
    MIN(talent_index) AS min_talent_index
  FROM raw_talent
  GROUP BY 1, 2, 3
),
canonical_cycle_version AS (
  SELECT
    employee_id,
    cycle_number,
    availability_date,
    source_rows,
    distinct_index_values,
    CASE WHEN distinct_index_values = 1 THEN min_talent_index ELSE NULL END
      AS talent_index
  FROM exact_keys
  WHERE availability_date IS NOT NULL
),
ranked_availability AS (
  SELECT
    employee_id,
    cycle_number,
    availability_date,
    talent_index,
    COUNT(*) OVER (
      PARTITION BY employee_id, availability_date
    ) AS source_versions_at_availability,
    ROW_NUMBER() OVER (
      PARTITION BY employee_id, availability_date
      ORDER BY cycle_number DESC
    ) AS availability_rank
  FROM canonical_cycle_version
),
selected_availability AS (
  SELECT
    employee_id,
    availability_date,
    talent_index,
    source_versions_at_availability
  FROM ranked_availability
  WHERE availability_rank = 1
),
talent_intervals AS (
  SELECT
    employee_id,
    availability_date,
    LEAD(availability_date) OVER (
      PARTITION BY employee_id
      ORDER BY availability_date
    ) AS next_availability_date,
    talent_index,
    source_versions_at_availability
  FROM selected_availability
),
joined AS (
  SELECT
    e.employee_id,
    e.snapshot_date,
    t.availability_date,
    t.talent_index,
    t.source_versions_at_availability
  FROM eligible e
  LEFT JOIN talent_intervals t
    ON t.employee_id = e.employee_id
   AND e.snapshot_date >= t.availability_date
   AND (
     t.next_availability_date IS NULL
     OR e.snapshot_date < t.next_availability_date
   )
),
eligible_people AS (
  SELECT DISTINCT employee_id FROM eligible
),
identity_metrics AS (
  SELECT
    COUNT(*) AS eligible_employees,
    COUNT(CASE WHEN r.employee_id IS NOT NULL THEN 1 END)
      AS identity_matched_employees,
    COUNT(CASE WHEN r.employee_id IS NULL THEN 1 END)
      AS identity_unmatched_employees
  FROM eligible_people e
  LEFT JOIN (
    SELECT DISTINCT employee_id FROM raw_talent
  ) r
    ON r.employee_id = e.employee_id
),
source_metrics AS (
  SELECT
    COALESCE(SUM(CASE WHEN source_rows > 1 THEN source_rows - 1 ELSE 0 END), 0)
      AS duplicate_count,
    COALESCE(SUM(CASE WHEN distinct_index_values > 1 THEN 1 ELSE 0 END), 0)
      AS conflicting_source_key_groups,
    COALESCE(SUM(CASE WHEN availability_date IS NULL THEN source_rows ELSE 0 END), 0)
      AS source_rows_without_technical_date
  FROM exact_keys
)
SELECT
  'Talent index' AS variable_name,
  COUNT(*) AS eligible_count,
  COUNT(CASE WHEN availability_date IS NOT NULL THEN 1 END) AS matched_count,
  COUNT(CASE WHEN availability_date IS NULL THEN 1 END) AS unmatched_count,
  COUNT(CASE WHEN talent_index IS NOT NULL THEN 1 END) AS observable_count,
  source_metrics.duplicate_count,
  COUNT(CASE WHEN source_versions_at_availability > 1 THEN 1 END)
    AS multi_match_count,
  source_metrics.conflicting_source_key_groups,
  source_metrics.source_rows_without_technical_date,
  identity_metrics.eligible_employees,
  identity_metrics.identity_matched_employees,
  identity_metrics.identity_unmatched_employees,
  ROUND(
    100.0 * COUNT(CASE WHEN availability_date IS NOT NULL THEN 1 END)
    / NULLIF(COUNT(*), 0),
    4
  ) AS temporal_match_percent,
  ROUND(
    100.0 * COUNT(CASE WHEN talent_index IS NOT NULL THEN 1 END)
    / NULLIF(COUNT(*), 0),
    4
  ) AS observable_percent
FROM joined
CROSS JOIN identity_metrics
CROSS JOIN source_metrics
GROUP BY
  source_metrics.duplicate_count,
  source_metrics.conflicting_source_key_groups,
  source_metrics.source_rows_without_technical_date,
  identity_metrics.eligible_employees,
  identity_metrics.identity_matched_employees,
  identity_metrics.identity_unmatched_employees;
