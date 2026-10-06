-- Entrega: presentation. Sólo agregados; sin identificadores en la salida.
-- Propósito: validar los valores codificados de worker_type, employee_type y
-- active_status en el snapshot mensual más reciente antes de medir headcount.
WITH latest_snapshot AS (
    SELECT MAX(fis_mo_end_dt) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
),
snapshot_population AS (
    SELECT
        d.worker_type,
        d.employee_type,
        d.active_status,
        d.employee_id
    FROM hrda.post_hire_monthly_worker_dtls AS d
    INNER JOIN latest_snapshot AS l
        ON d.fis_mo_end_dt = l.snapshot_date
)
SELECT
    worker_type,
    employee_type,
    active_status,
    COUNT(*) AS worker_month_rows,
    COUNT(DISTINCT employee_id) AS distinct_employees
FROM snapshot_population
GROUP BY 1, 2, 3
ORDER BY distinct_employees DESC, worker_type, employee_type, active_status;
