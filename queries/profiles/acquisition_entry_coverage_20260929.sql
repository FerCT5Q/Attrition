-- Cobertura histórica del campo acquisition para el assessment v4.
-- Modo de entrega: presentation. Devuelve sólo agregados por snapshot.
WITH monthly_coverage AS (
    SELECT
        fis_mo_end_dt AS snapshot_date,
        fiscal_year,
        COUNT(DISTINCT employee_id) AS eligible_employees,
        COUNT(DISTINCT CASE
            WHEN NULLIF(TRIM(acquisition), '') IS NOT NULL THEN employee_id
        END) AS observable_employees
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
      AND fis_mo_end_dt <= DATE '2026-08-23'
    GROUP BY fis_mo_end_dt, fiscal_year
)
SELECT
    snapshot_date,
    fiscal_year,
    eligible_employees,
    observable_employees,
    'Cobertura de acquisition no vacío, un vacío no se interpreta como ausencia de adquisición.' AS notes
FROM monthly_coverage
ORDER BY snapshot_date;
