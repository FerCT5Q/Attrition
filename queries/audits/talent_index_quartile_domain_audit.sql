-- Talent index: follow-up del dominio numerico de talent_quartile.
--
-- Revision trigger:
--   La auditoria estructural encontro filas fuera del rango hipotetico 1..4.
--
-- Acceptance / interpretation rule stated before execution:
--   Si outside_expected_domain_rows > 0, el rango 1..4 no puede tratarse como
--   dominio completo sin documentar los valores sentinel o categorias adicionales.
--   Esta columna es contextual y no demuestra la formula de talent_index.

SELECT
  'Talent index' AS variable_name,
  COUNT(CASE WHEN talent_quartile IS NOT NULL THEN 1 END)
    AS populated_quartile_rows,
  COUNT(DISTINCT talent_quartile) AS distinct_quartile_values,
  MIN(talent_quartile) AS minimum_quartile_value,
  MAX(talent_quartile) AS maximum_quartile_value,
  COUNT(CASE WHEN talent_quartile < 1 THEN 1 END) AS below_one_rows,
  COUNT(CASE WHEN talent_quartile > 4 THEN 1 END) AS above_four_rows,
  COUNT(CASE
    WHEN talent_quartile IS NOT NULL
     AND talent_quartile NOT BETWEEN 1 AND 4
    THEN 1
  END) AS outside_expected_domain_rows,
  COUNT(CASE
    WHEN talent_quartile IS NOT NULL
     AND talent_quartile NOT BETWEEN 1 AND 4
     AND talent_index IS NULL
    THEN 1
  END) AS outside_domain_with_null_index_rows,
  COUNT(CASE
    WHEN talent_quartile IS NOT NULL
     AND talent_quartile NOT BETWEEN 1 AND 4
     AND talent_index IS NOT NULL
    THEN 1
  END) AS outside_domain_with_populated_index_rows
FROM hrda.master_talent_index;
