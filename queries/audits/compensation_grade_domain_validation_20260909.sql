/*
  Validación agregada del dominio de compensation_grade para el artefacto
  internal_analysis. No devuelve filas de empleados ni valores de compensación.
  Población: empleados regulares activos en el último snapshot disponible;
  grain de los conteos: empleado distinto por grado observado.
*/
WITH latest_snapshot AS (
    SELECT MAX(fis_mo_end_dt) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt IS NOT NULL
),
employee_grades AS (
    SELECT DISTINCT
        employee_id,
        NULLIF(TRIM(compensation_grade), '') AS grade_label
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt = (SELECT snapshot_date FROM latest_snapshot)
),
grade_counts AS (
    SELECT
        grade_label,
        COUNT(DISTINCT employee_id) AS employee_count
    FROM employee_grades
    WHERE grade_label IS NOT NULL
    GROUP BY grade_label
),
ranked_grades AS (
    SELECT
        grade_label,
        employee_count,
        ROW_NUMBER() OVER (ORDER BY employee_count DESC, grade_label) AS grade_rank
    FROM grade_counts
),
summary AS (
    SELECT
        COUNT(*) AS observed_grade_count,
        SUM(CASE WHEN employee_count >= 30 THEN 1 ELSE 0 END) AS public_grade_count,
        SUM(CASE WHEN employee_count < 30 THEN 1 ELSE 0 END) AS suppressed_small_grade_count,
        SUM(CASE WHEN employee_count >= 30 THEN employee_count ELSE 0 END) AS public_grade_employee_count,
        SUM(CASE WHEN employee_count < 30 THEN employee_count ELSE 0 END) AS small_grade_employee_count,
        MAX(CASE WHEN UPPER(grade_label) = 'M' THEN 1 ELSE 0 END) AS m_present,
        MAX(CASE WHEN UPPER(grade_label) = 'M' AND employee_count >= 30 THEN 1 ELSE 0 END) AS m_publicable,
        SUM(CASE WHEN UPPER(grade_label) LIKE 'M%' THEN 1 ELSE 0 END) AS m_family_grade_count,
        SUM(CASE WHEN UPPER(grade_label) LIKE 'M%' THEN employee_count ELSE 0 END) AS m_family_employee_count,
        (SELECT COUNT(DISTINCT employee_id) FROM employee_grades) AS eligible_employee_count
    FROM grade_counts
)
SELECT
    'grade' AS row_type,
    grade_label,
    employee_count,
    CAST(NULL AS INTEGER) AS observed_grade_count,
    CAST(NULL AS INTEGER) AS public_grade_count,
    CAST(NULL AS INTEGER) AS suppressed_small_grade_count,
    CAST(NULL AS INTEGER) AS public_grade_employee_count,
    CAST(NULL AS INTEGER) AS small_grade_employee_count,
    CAST(NULL AS INTEGER) AS m_present,
    CAST(NULL AS INTEGER) AS m_publicable,
    CAST(NULL AS INTEGER) AS m_family_grade_count,
    CAST(NULL AS INTEGER) AS m_family_employee_count,
    CAST(NULL AS INTEGER) AS eligible_employee_count
FROM ranked_grades
WHERE employee_count >= 30

UNION ALL

SELECT
    'summary' AS row_type,
    CAST(NULL AS VARCHAR) AS grade_label,
    eligible_employee_count AS employee_count,
    observed_grade_count,
    public_grade_count,
    suppressed_small_grade_count,
    public_grade_employee_count,
    small_grade_employee_count,
    m_present,
    m_publicable,
    m_family_grade_count,
    m_family_employee_count,
    eligible_employee_count
FROM summary
ORDER BY row_type DESC, employee_count DESC, grade_label;
