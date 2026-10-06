-- Tamaño agregado de las etiquetas históricas de office_site dentro de India.
-- No devuelve etiquetas de baja frecuencia ni filas de empleados.

WITH site_counts AS (
  SELECT
    NULLIF(TRIM(CAST(office_site AS VARCHAR(512))), '') AS office_site,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND UPPER(NULLIF(TRIM(CAST(country AS VARCHAR(512))), '')) = 'INDIA'
    AND NULLIF(TRIM(CAST(office_site AS VARCHAR(512))), '') IS NOT NULL
  GROUP BY 1
)
SELECT
  COUNT(*) AS distinct_office_site_labels,
  SUM(CASE WHEN employee_count >= 30 THEN 1 ELSE 0 END) AS labels_with_at_least_30_employees,
  SUM(CASE WHEN employee_count < 30 THEN 1 ELSE 0 END) AS labels_below_30_employees,
  MAX(employee_count) AS largest_label_employee_count
FROM site_counts;
