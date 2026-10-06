-- Resumen de dominio de Compensation grade con corte temporal y privacidad.
-- No devuelve categorias ni identificadores; solo conteos agregados.
WITH grade_stats AS (
    SELECT
        NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') AS normalized_grade,
        COUNT(DISTINCT employee_id) AS distinct_employees
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt <= '2026-08-25'
      AND NULLIF(TRIM(CAST(compensation_grade AS VARCHAR)), '') IS NOT NULL
    GROUP BY 1
)
SELECT
    COUNT(*) AS distinct_nonblank_grades,
    SUM(CASE WHEN distinct_employees >= 30 THEN 1 ELSE 0 END) AS shareable_grades,
    SUM(CASE WHEN distinct_employees < 30 THEN 1 ELSE 0 END) AS suppressed_grades
FROM grade_stats;
