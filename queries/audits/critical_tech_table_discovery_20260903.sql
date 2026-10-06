-- Pregunta: ¿Cuantos objetos tabulares del esquema hrda contienen "critical" en su nombre?
-- Regla de aceptacion: exactamente dos filas para afirmar que existen dos tablas.
SELECT
  table_name,
  table_type
FROM information_schema.tables
WHERE table_schema = 'hrda'
  AND table_name ILIKE '%critical%'
ORDER BY table_name;
