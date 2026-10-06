-- Talent Index: auditoria agregada de variacion de term_reason sin publicar categorias.
--
-- Claim:
--   Distinguir si term_reason parece una senal categorial real y variable o un unico
--   marcador constante dentro de cada ciclo historico.
--
-- Population:
--   Registros de hrda.master_talent_index con term_reason no nulo/no vacio.
--
-- Grain:
--   Un agregado por cycle_number. Las categorias concretas nunca salen del query.
--
-- Interpretation rule stated before execution:
--   * distinct_reason_values = 1 y top_reason_percent = 100 puede corresponder a un
--     marcador constante; no confirma contenido del outcome.
--   * distinct_reason_values > 1 demuestra que el campo contiene variacion categorial.
--     Si ademas aparece en registros posteriores a term_date, constituye un indicio
--     fuerte de enriquecimiento post-outcome de la tabla, aunque no prueba que forme
--     parte de la formula de talent_index.

WITH reason_counts AS (
  SELECT
    cycle_number,
    CAST(term_reason AS VARCHAR) AS internal_reason,
    COUNT(*) AS reason_rows
  FROM hrda.master_talent_index
  WHERE cycle_number IS NOT NULL
    AND NULLIF(TRIM(CAST(term_reason AS VARCHAR)), '') IS NOT NULL
  GROUP BY 1, 2
),
ranked_reasons AS (
  SELECT
    cycle_number,
    reason_rows,
    ROW_NUMBER() OVER (
      PARTITION BY cycle_number
      ORDER BY reason_rows DESC
    ) AS reason_rank
  FROM reason_counts
),
cycle_summary AS (
  SELECT
    cycle_number,
    SUM(reason_rows) AS populated_reason_rows,
    COUNT(*) AS distinct_reason_values,
    MAX(CASE WHEN reason_rank = 1 THEN reason_rows ELSE 0 END) AS top_reason_rows
  FROM ranked_reasons
  GROUP BY 1
  HAVING SUM(reason_rows) >= 30
)
SELECT
  cycle_number,
  populated_reason_rows,
  distinct_reason_values,
  top_reason_rows,
  ROUND(
    100.0 * top_reason_rows / NULLIF(populated_reason_rows, 0),
    4
  ) AS top_reason_percent
FROM cycle_summary
ORDER BY cycle_number;
