-- Metadatos de tablas candidatas a mapping de Compensation grade.
-- No devuelve filas de empleados ni valores de compensacion.
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('compgrade_benefitsusd_mapping', 'annual_review_report')
ORDER BY table_name, ordinal_position;
