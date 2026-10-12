-- Metadata únicamente: posibles fuentes históricas o fechas de negocio de Talent index.
SELECT table_name,column_name,data_type
FROM information_schema.columns
WHERE table_schema='hrda' AND LOWER(table_name) LIKE '%talent%'
ORDER BY table_name,ordinal_position
