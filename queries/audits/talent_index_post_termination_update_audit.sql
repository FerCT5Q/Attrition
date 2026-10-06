-- Talent Index: auditoria agregada de posibles actualizaciones posteriores a la terminacion.
--
-- Claim:
--   Identificar si hrda.master_talent_index contiene versiones de empleados regulares
--   modificadas despues de su ultima terminacion conocida y, entre ellas, si el valor
--   de talent_index cambio o el registro ya contiene term_reason.
--
-- Population:
--   Registros de Talent Index con empleado y last_modified_date, unidos internamente
--   a empleados regulares con term_date. Se excluyen empleados con evidencia de rehire
--   para reducir falsos positivos entre episodios laborales.
--
-- Grain:
--   Una version agregada por empleado, cycle_number y last_modified_date. Los IDs se
--   usan solo dentro del calculo y nunca se publican.
--
-- Acceptance / interpretation rule stated before execution:
--   * Sin indicio observable: post_term_employees = 0,
--     cross_term_changed_employees = 0 y
--     post_term_versions_with_term_reason = 0.
--   * Indicio de riesgo: existe al menos un registro posterior a la terminacion.
--   * Indicio fuerte de actualizacion post-outcome: existe al menos un cambio de
--     talent_index que cruza la fecha de terminacion, o un registro posterior contiene
--     term_reason.
--   Esta auditoria no demuestra que term_reason participe en la formula; eso requiere
--   lineage autoritativo o recalculo independiente del target talent_index.

WITH employee_term_summary AS (
  SELECT
    CAST(employee_id AS BIGINT) AS employee_id,
    MAX(term_date) AS latest_term_date,
    MAX(
      CASE
        WHEN COALESCE(is_rehire, 0) = 1 OR rehire_date IS NOT NULL THEN 1
        ELSE 0
      END
    ) AS ever_rehire
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
    MAX(talent_index) AS max_talent_index,
    MAX(
      CASE
        WHEN NULLIF(TRIM(CAST(term_reason AS VARCHAR)), '') IS NOT NULL THEN 1
        ELSE 0
      END
    ) AS term_reason_present
  FROM hrda.master_talent_index
  WHERE empl_id IS NOT NULL
    AND last_modified_date IS NOT NULL
  GROUP BY 1, 2, 3
),
normalized_version AS (
  SELECT
    employee_id,
    cycle_number,
    last_modified_date,
    source_rows,
    distinct_index_values,
    CASE
      WHEN distinct_index_values = 1 THEN min_talent_index
      ELSE NULL
    END AS comparable_index,
    term_reason_present
  FROM talent_version
),
sequenced_version AS (
  SELECT
    employee_id,
    cycle_number,
    last_modified_date,
    source_rows,
    distinct_index_values,
    comparable_index,
    term_reason_present,
    LAG(comparable_index) OVER (
      PARTITION BY employee_id
      ORDER BY last_modified_date, cycle_number
    ) AS previous_index,
    LAG(last_modified_date) OVER (
      PARTITION BY employee_id
      ORDER BY last_modified_date, cycle_number
    ) AS previous_modified_date
  FROM normalized_version
),
eligible_versions AS (
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
  FROM sequenced_version s
  INNER JOIN employee_term_summary t
    ON t.employee_id = s.employee_id
  WHERE t.latest_term_date IS NOT NULL
    AND t.ever_rehire = 0
),
cycle_metrics AS (
  SELECT
    CAST('cycle' AS VARCHAR(16)) AS result_scope,
    cycle_number,
    last_modified_date,
    COUNT(*) AS matched_versions,
    COUNT(DISTINCT employee_id) AS matched_terminated_employees,
    SUM(CASE WHEN last_modified_date > latest_term_date THEN 1 ELSE 0 END)
      AS post_term_versions,
    COUNT(DISTINCT CASE
      WHEN last_modified_date > latest_term_date THEN employee_id
      ELSE NULL
    END) AS post_term_employees,
    SUM(CASE
      WHEN last_modified_date > latest_term_date
       AND term_reason_present = 1 THEN 1
      ELSE 0
    END) AS post_term_versions_with_term_reason,
    SUM(CASE
      WHEN last_modified_date > latest_term_date
       AND previous_index IS NOT NULL
       AND comparable_index IS NOT NULL
       AND comparable_index <> previous_index THEN 1
      ELSE 0
    END) AS post_term_changed_versions,
    COUNT(DISTINCT CASE
      WHEN last_modified_date > latest_term_date
       AND previous_index IS NOT NULL
       AND comparable_index IS NOT NULL
       AND comparable_index <> previous_index THEN employee_id
      ELSE NULL
    END) AS post_term_changed_employees,
    SUM(CASE
      WHEN previous_modified_date <= latest_term_date
       AND last_modified_date > latest_term_date
       AND previous_index IS NOT NULL
       AND comparable_index IS NOT NULL
       AND comparable_index <> previous_index THEN 1
      ELSE 0
    END) AS cross_term_changed_versions,
    COUNT(DISTINCT CASE
      WHEN previous_modified_date <= latest_term_date
       AND last_modified_date > latest_term_date
       AND previous_index IS NOT NULL
       AND comparable_index IS NOT NULL
       AND comparable_index <> previous_index THEN employee_id
      ELSE NULL
    END) AS cross_term_changed_employees,
    SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END) AS duplicate_key_versions,
    SUM(CASE WHEN distinct_index_values > 1 THEN 1 ELSE 0 END)
      AS conflicting_index_versions
  FROM eligible_versions
  GROUP BY 1, 2, 3
  HAVING COUNT(DISTINCT employee_id) >= 30
     AND COUNT(DISTINCT CASE
       WHEN last_modified_date > latest_term_date THEN employee_id
       ELSE NULL
     END) >= 30
),
overall_metrics AS (
  SELECT
    CAST('overall' AS VARCHAR(16)) AS result_scope,
    CAST(NULL AS INTEGER) AS cycle_number,
    CAST(NULL AS DATE) AS last_modified_date,
    COUNT(*) AS matched_versions,
    COUNT(DISTINCT employee_id) AS matched_terminated_employees,
    SUM(CASE WHEN last_modified_date > latest_term_date THEN 1 ELSE 0 END)
      AS post_term_versions,
    COUNT(DISTINCT CASE
      WHEN last_modified_date > latest_term_date THEN employee_id
      ELSE NULL
    END) AS post_term_employees,
    SUM(CASE
      WHEN last_modified_date > latest_term_date
       AND term_reason_present = 1 THEN 1
      ELSE 0
    END) AS post_term_versions_with_term_reason,
    SUM(CASE
      WHEN last_modified_date > latest_term_date
       AND previous_index IS NOT NULL
       AND comparable_index IS NOT NULL
       AND comparable_index <> previous_index THEN 1
      ELSE 0
    END) AS post_term_changed_versions,
    COUNT(DISTINCT CASE
      WHEN last_modified_date > latest_term_date
       AND previous_index IS NOT NULL
       AND comparable_index IS NOT NULL
       AND comparable_index <> previous_index THEN employee_id
      ELSE NULL
    END) AS post_term_changed_employees,
    SUM(CASE
      WHEN previous_modified_date <= latest_term_date
       AND last_modified_date > latest_term_date
       AND previous_index IS NOT NULL
       AND comparable_index IS NOT NULL
       AND comparable_index <> previous_index THEN 1
      ELSE 0
    END) AS cross_term_changed_versions,
    COUNT(DISTINCT CASE
      WHEN previous_modified_date <= latest_term_date
       AND last_modified_date > latest_term_date
       AND previous_index IS NOT NULL
       AND comparable_index IS NOT NULL
       AND comparable_index <> previous_index THEN employee_id
      ELSE NULL
    END) AS cross_term_changed_employees,
    SUM(CASE WHEN source_rows > 1 THEN 1 ELSE 0 END) AS duplicate_key_versions,
    SUM(CASE WHEN distinct_index_values > 1 THEN 1 ELSE 0 END)
      AS conflicting_index_versions
  FROM eligible_versions
  HAVING COUNT(DISTINCT employee_id) >= 30
),
combined AS (
  SELECT
    result_scope,
    cycle_number,
    last_modified_date,
    matched_versions,
    matched_terminated_employees,
    post_term_versions,
    post_term_employees,
    post_term_versions_with_term_reason,
    post_term_changed_versions,
    post_term_changed_employees,
    cross_term_changed_versions,
    cross_term_changed_employees,
    duplicate_key_versions,
    conflicting_index_versions
  FROM cycle_metrics
  UNION ALL
  SELECT
    result_scope,
    cycle_number,
    last_modified_date,
    matched_versions,
    matched_terminated_employees,
    post_term_versions,
    post_term_employees,
    post_term_versions_with_term_reason,
    post_term_changed_versions,
    post_term_changed_employees,
    cross_term_changed_versions,
    cross_term_changed_employees,
    duplicate_key_versions,
    conflicting_index_versions
  FROM overall_metrics
)
SELECT
  result_scope,
  cycle_number,
  last_modified_date,
  matched_versions,
  matched_terminated_employees,
  post_term_versions,
  post_term_employees,
  ROUND(
    100.0 * post_term_employees / NULLIF(matched_terminated_employees, 0),
    4
  ) AS post_term_employee_percent,
  post_term_versions_with_term_reason,
  post_term_changed_versions,
  post_term_changed_employees,
  cross_term_changed_versions,
  cross_term_changed_employees,
  duplicate_key_versions,
  conflicting_index_versions
FROM combined
ORDER BY
  CASE WHEN result_scope = 'overall' THEN 1 ELSE 0 END,
  last_modified_date,
  cycle_number;
