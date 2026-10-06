-- Talent index: cobertura en el último snapshot laboral disponible.
--
-- Esta consulta no usa last_modified_date, airflow_execution_date ni otro timestamp
-- técnico. Para medir recuperación actual, selecciona el mayor cycle_number de cada
-- empleado después de colapsar la llave empleado-ciclo. Esa selección no demuestra
-- vigencia oficial ni puede trasladarse a snapshots históricos.

WITH latest_snapshot AS (
  SELECT MAX(fis_mo_end_dt) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
),
eligible AS (
  SELECT
    CAST(w.employee_id AS BIGINT) AS employee_id,
    w.fis_mo_end_dt AS snapshot_date,
    MAX(CAST(w.fiscal_year AS VARCHAR)) AS fiscal_year
  FROM hrda.post_hire_monthly_worker_dtls w
  CROSS JOIN latest_snapshot s
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
    AND w.fis_mo_end_dt = s.snapshot_date
  GROUP BY 1, 2
),
employee_cycle AS (
  SELECT
    CAST(empl_id AS BIGINT) AS employee_id,
    cycle_number,
    COUNT(*) AS source_rows,
    COUNT(talent_index) AS populated_index_rows,
    COUNT(DISTINCT talent_index) AS distinct_index_values,
    MIN(talent_index) AS min_talent_index
  FROM hrda.master_talent_index
  WHERE empl_id IS NOT NULL
    AND cycle_number IS NOT NULL
  GROUP BY 1, 2
),
ranked_cycles AS (
  SELECT
    employee_id,
    cycle_number,
    source_rows,
    populated_index_rows,
    distinct_index_values,
    CASE
      WHEN distinct_index_values = 1
       AND populated_index_rows = source_rows
      THEN min_talent_index
      ELSE NULL
    END AS talent_index,
    ROW_NUMBER() OVER (
      PARTITION BY employee_id
      ORDER BY cycle_number DESC NULLS LAST
    ) AS cycle_rank
  FROM employee_cycle
),
selected_cycle AS (
  SELECT
    employee_id,
    cycle_number,
    talent_index
  FROM ranked_cycles
  WHERE cycle_rank = 1
),
joined AS (
  SELECT
    e.snapshot_date,
    e.fiscal_year,
    e.employee_id,
    s.talent_index
  FROM eligible e
  LEFT JOIN selected_cycle s
    ON s.employee_id = e.employee_id
)
SELECT
  snapshot_date,
  MAX(fiscal_year) AS fiscal_year,
  COUNT(*) AS eligible_employees,
  COUNT(CASE WHEN talent_index IS NOT NULL THEN 1 END) AS observable_employees,
  CAST(NULL AS BIGINT) AS event_employees,
  CAST(
    'Estado actual: mayor cycle_number por empleado; sin fecha efectiva histórica.'
    AS VARCHAR(160)
  ) AS notes
FROM joined
GROUP BY 1
ORDER BY 1;
