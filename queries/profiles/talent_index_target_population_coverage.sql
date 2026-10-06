-- Talent index: cobertura mensual sobre la poblacion objetivo del modelo.
--
-- La fecha tecnica se usa conservadoramente como limite de conocimiento. Los ciclos
-- sin fecha se excluyen. Si varios ciclos comparten fecha para un empleado, se elige
-- cycle_number descendente; el audit de join cuantifica cuantas filas requieren ese
-- desempate. Esta regla no se presenta como fecha oficial de publicacion.

WITH eligible AS (
  SELECT
    CAST(employee_id AS BIGINT) AS employee_id,
    fis_mo_end_dt AS snapshot_date,
    MAX(CAST(fiscal_year AS VARCHAR)) AS fiscal_year
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND employee_id IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY 1, 2
),
exact_keys AS (
  SELECT
    CAST(empl_id AS BIGINT) AS employee_id,
    cycle_number,
    COALESCE(last_modified_date, airflow_execution_date) AS availability_date,
    COUNT(DISTINCT talent_index) AS distinct_index_values,
    MIN(talent_index) AS min_talent_index
  FROM hrda.master_talent_index
  WHERE empl_id IS NOT NULL
    AND cycle_number IS NOT NULL
  GROUP BY 1, 2, 3
),
ranked_availability AS (
  SELECT
    employee_id,
    cycle_number,
    availability_date,
    CASE WHEN distinct_index_values = 1 THEN min_talent_index ELSE NULL END
      AS talent_index,
    ROW_NUMBER() OVER (
      PARTITION BY employee_id, availability_date
      ORDER BY cycle_number DESC
    ) AS availability_rank
  FROM exact_keys
  WHERE availability_date IS NOT NULL
),
selected_availability AS (
  SELECT
    employee_id,
    availability_date,
    talent_index
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
    talent_index
  FROM selected_availability
),
joined AS (
  SELECT
    e.snapshot_date,
    e.fiscal_year,
    e.employee_id,
    t.talent_index
  FROM eligible e
  LEFT JOIN talent_intervals t
    ON t.employee_id = e.employee_id
   AND e.snapshot_date >= t.availability_date
   AND (
     t.next_availability_date IS NULL
     OR e.snapshot_date < t.next_availability_date
   )
)
SELECT
  snapshot_date,
  MAX(fiscal_year) AS fiscal_year,
  COUNT(*) AS eligible_employees,
  COUNT(CASE WHEN talent_index IS NOT NULL THEN 1 END) AS observable_employees,
  CAST(NULL AS BIGINT) AS event_employees,
  CAST('As-of tecnico conservador, no equivale a fecha oficial de publicacion.' AS VARCHAR(160))
    AS notes
FROM joined
GROUP BY 1
ORDER BY 1;
