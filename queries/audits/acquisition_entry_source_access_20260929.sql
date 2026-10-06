-- Preflight de fuente para el assessment v4 de Ingreso por adquisición.
-- No consulta datos de empleados; verifica sólo metadata de la fuente principal.
WITH required_columns AS (
    SELECT 'Ingreso por adquisición' AS variable_name, 'hrda' AS table_schema,
           'post_hire_monthly_worker_dtls' AS table_name, 'employee_id' AS column_name
    UNION ALL SELECT 'Ingreso por adquisición', 'hrda', 'post_hire_monthly_worker_dtls', 'fis_mo_end_dt'
    UNION ALL SELECT 'Ingreso por adquisición', 'hrda', 'post_hire_monthly_worker_dtls', 'acquisition'
    UNION ALL SELECT 'Ingreso por adquisición', 'hrda', 'post_hire_monthly_worker_dtls', 'worker_type'
    UNION ALL SELECT 'Ingreso por adquisición', 'hrda', 'post_hire_monthly_worker_dtls', 'employee_type'
    UNION ALL SELECT 'Ingreso por adquisición', 'hrda', 'post_hire_monthly_worker_dtls', 'active_status'
)
SELECT
    required_columns.variable_name,
    COUNT(*) AS required_items,
    SUM(CASE WHEN information_schema.columns.column_name IS NOT NULL THEN 1 ELSE 0 END) AS found_items,
    SUM(CASE WHEN information_schema.columns.column_name IS NULL THEN 1 ELSE 0 END) AS missing_items
FROM required_columns
LEFT JOIN information_schema.columns
  ON information_schema.columns.table_schema = required_columns.table_schema
 AND information_schema.columns.table_name = required_columns.table_name
 AND information_schema.columns.column_name = required_columns.column_name
GROUP BY required_columns.variable_name;
