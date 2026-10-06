-- Talent index: disponibilidad agregada para una futura reconciliacion de formula.
--
-- Claim:
--   Cuantificar si el valor almacenado y sus componentes candidatos estan presentes
--   en el mismo grain empleado-ciclo. Esta consulta no descubre ni confirma la
--   formula; Definition=2 sigue requiriendo lineage autoritativo y reconciliacion.
--
-- Acceptance / interpretation rule stated before execution:
--   La fuente debe contener valores del indice y filas comparables con componentes.
--   Aun si pasa, esta prueba solo demuestra factibilidad de reconciliacion, no la
--   definicion del indice.

SELECT
  'Talent index' AS variable_name,
  COUNT(*) AS source_rows,
  COUNT(DISTINCT empl_id) AS source_employees,
  COUNT(DISTINCT cycle_number) AS cycles_checked,
  COUNT(CASE WHEN talent_index IS NOT NULL THEN 1 END)
    AS populated_talent_index_rows,
  COUNT(DISTINCT talent_index) AS distinct_talent_index_values,
  COUNT(CASE
    WHEN talent_index IS NOT NULL
     AND perf IS NOT NULL
     AND stock IS NOT NULL
     AND bonus IS NOT NULL
     AND promo_index IS NOT NULL
    THEN 1
  END) AS rows_with_all_candidate_components,
  COUNT(CASE
    WHEN talent_index IS NOT NULL
     AND (
       perf IS NULL OR stock IS NULL OR bonus IS NULL OR promo_index IS NULL
     )
    THEN 1
  END) AS populated_index_rows_missing_candidate_components,
  COUNT(CASE WHEN talent_quartile IS NOT NULL THEN 1 END)
    AS populated_talent_quartile_rows,
  COUNT(CASE WHEN ar_eligibility IS NOT NULL THEN 1 END)
    AS populated_eligibility_rows
FROM hrda.master_talent_index;
