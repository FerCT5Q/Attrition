-- Valores históricos agregados de office_site dentro de India.
-- Entregable: internal_analysis. No devuelve filas ni identificadores.
-- Población: worker_type='Employee', employee_type='Regular', active_status=1.
-- Regla: cada etiqueta visible debe representar al menos 30 empleados distintos.

WITH india_history AS (
  SELECT
    employee_id,
    fis_mo_end_dt,
    NULLIF(TRIM(CAST(office_site AS VARCHAR(512))), '') AS office_site,
    NULLIF(TRIM(CAST(city AS VARCHAR(512))), '') AS city
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND UPPER(NULLIF(TRIM(CAST(country AS VARCHAR(512))), '')) = 'INDIA'
    AND NULLIF(TRIM(CAST(office_site AS VARCHAR(512))), '') IS NOT NULL
)
SELECT
  office_site AS value_label,
  COUNT(DISTINCT employee_id) AS employee_count,
  COUNT(*) AS employee_snapshot_rows,
  COUNT(DISTINCT fis_mo_end_dt) AS snapshots_observed,
  MIN(fis_mo_end_dt) AS first_snapshot,
  MAX(fis_mo_end_dt) AS last_snapshot,
  COUNT(DISTINCT city) AS city_count
FROM india_history
GROUP BY office_site
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY employee_count DESC, value_label
LIMIT 100;
