-- Talent index: contexto agregado de enriquecimiento posterior a terminacion.
--
-- Claim:
--   Medir si la tabla contiene versiones tecnicas posteriores a la ultima terminacion
--   conocida y si esas versiones contienen term_reason o cambios del indice.
--
-- Interpretation rule stated before execution:
--   Un resultado positivo demuestra enriquecimiento post-outcome de la tabla y obliga
--   a filtrar por fecha de conocimiento. No demuestra que term_reason forme parte de
--   la formula de talent_index.

WITH employee_term_summary AS (
  SELECT
    CAST(employee_id AS BIGINT) AS employee_id,
    MAX(term_date) AS latest_term_date,
    MAX(CASE
      WHEN COALESCE(is_rehire, 0) = 1 OR rehire_date IS NOT NULL THEN 1
      ELSE 0
    END) AS ever_rehire
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND employee_id IS NOT NULL
  GROUP BY 1
),
talent_version AS (
  SELECT
    CAST(empl_id AS BIGINT) AS employee_id,
    cycle_number,
    last_modified_date,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT talent_index) AS distinct_index_values,
    MIN(talent_index) AS min_talent_index,
    MAX(CASE
      WHEN NULLIF(TRIM(CAST(term_reason AS VARCHAR)), '') IS NOT NULL THEN 1
      ELSE 0
    END) AS term_reason_present
  FROM hrda.master_talent_index
  WHERE empl_id IS NOT NULL
    AND last_modified_date IS NOT NULL
  GROUP BY 1, 2, 3
),
sequenced AS (
  SELECT
    employee_id,
    cycle_number,
    last_modified_date,
    source_rows,
    distinct_index_values,
    CASE WHEN distinct_index_values = 1 THEN min_talent_index ELSE NULL END
      AS comparable_index,
    term_reason_present,
    LAG(CASE WHEN distinct_index_values = 1 THEN min_talent_index ELSE NULL END)
      OVER (
        PARTITION BY employee_id
        ORDER BY last_modified_date, cycle_number
      ) AS previous_index,
    LAG(last_modified_date) OVER (
      PARTITION BY employee_id
      ORDER BY last_modified_date, cycle_number
    ) AS previous_modified_date
  FROM talent_version
),
eligible AS (
  SELECT
    s.employee_id,
    s.cycle_number,
    s.last_modified_date,
    s.source_rows,
    s.distinct_index_values,
    s.comparable_index,
    s.term_reason_present,
    s.previous_index,
    s.previous_modified_date,
    t.latest_term_date
  FROM sequenced s
  INNER JOIN employee_term_summary t
    ON t.employee_id = s.employee_id
  WHERE t.latest_term_date IS NOT NULL
    AND t.ever_rehire = 0
)
SELECT
  'Talent index' AS variable_name,
  COUNT(*) AS matched_versions,
  COUNT(DISTINCT employee_id) AS matched_terminated_employees,
  COUNT(DISTINCT CASE
    WHEN last_modified_date > latest_term_date THEN employee_id
  END) AS post_term_employees,
  ROUND(
    100.0 * COUNT(DISTINCT CASE
      WHEN last_modified_date > latest_term_date THEN employee_id
    END) / NULLIF(COUNT(DISTINCT employee_id), 0),
    4
  ) AS post_term_employee_percent,
  SUM(CASE
    WHEN last_modified_date > latest_term_date
     AND term_reason_present = 1 THEN 1
    ELSE 0
  END) AS post_term_versions_with_term_reason,
  COUNT(DISTINCT CASE
    WHEN previous_modified_date <= latest_term_date
     AND last_modified_date > latest_term_date
     AND previous_index IS NOT NULL
     AND comparable_index IS NOT NULL
     AND comparable_index <> previous_index
    THEN employee_id
  END) AS cross_term_changed_employees,
  SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END) AS duplicate_key_versions,
  SUM(CASE WHEN distinct_index_values > 1 THEN 1 ELSE 0 END)
    AS conflicting_index_versions
FROM eligible
HAVING COUNT(DISTINCT employee_id) >= 30;
