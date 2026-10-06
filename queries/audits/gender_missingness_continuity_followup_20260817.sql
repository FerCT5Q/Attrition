-- Gender: continuidad agregada de la brecha de missingness de FY2026.
--
-- Pregunta: ¿los cinco snapshots con missingness elevado afectan de forma
-- sostenida a las mismas llaves empleado-snapshot o son ausencias mensuales
-- no relacionadas? No devuelve employee_id ni códigos de gender.
--
-- Población y grain: Employee / Regular / active_status=1; empleado-snapshot.
-- Bloque investigado: 2025-12-28 a 2026-04-26, precedido por 2025-11-23 y
-- seguido por 2026-05-24.
--
-- Regla de interpretación declarada antes de ejecutar:
-- si la mayor parte de las llaves faltantes aparece en cuatro o cinco meses y
-- vuelve a estar poblada en los límites, el patrón apoya una hipótesis de
-- brecha temporal de carga/formato. No identifica por sí solo la causa raíz.

WITH source_rows AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    CASE
      WHEN NULLIF(TRIM(CAST(gender AS VARCHAR(256))), '') IS NOT NULL
      THEN 1 ELSE 0
    END AS has_observed_row
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IN (
      CAST('2025-11-23' AS DATE),
      CAST('2025-12-28' AS DATE),
      CAST('2026-01-25' AS DATE),
      CAST('2026-02-22' AS DATE),
      CAST('2026-03-29' AS DATE),
      CAST('2026-04-26' AS DATE),
      CAST('2026-05-24' AS DATE)
    )
),
employee_snapshot AS (
  SELECT
    snapshot_date,
    employee_id,
    MAX(has_observed_row) AS has_observed_value
  FROM source_rows
  GROUP BY 1, 2
),
affected_employee AS (
  SELECT
    employee_id,
    SUM(CASE
      WHEN snapshot_date BETWEEN CAST('2025-12-28' AS DATE)
        AND CAST('2026-04-26' AS DATE)
       AND has_observed_value = 0
      THEN 1 ELSE 0
    END) AS missing_months_in_block,
    MAX(CASE
      WHEN snapshot_date = CAST('2025-11-23' AS DATE)
       AND has_observed_value = 1
      THEN 1 ELSE 0
    END) AS observed_before_block,
    MAX(CASE
      WHEN snapshot_date = CAST('2026-05-24' AS DATE)
       AND has_observed_value = 1
      THEN 1 ELSE 0
    END) AS observed_after_block
  FROM employee_snapshot
  GROUP BY 1
  HAVING SUM(CASE
    WHEN snapshot_date BETWEEN CAST('2025-12-28' AS DATE)
      AND CAST('2026-04-26' AS DATE)
     AND has_observed_value = 0
    THEN 1 ELSE 0
  END) > 0
)
SELECT
  missing_months_in_block,
  COUNT(*) AS affected_employees,
  SUM(observed_before_block) AS observed_before_block,
  SUM(observed_after_block) AS observed_after_block,
  SUM(CASE
    WHEN observed_before_block = 1 AND observed_after_block = 1
    THEN 1 ELSE 0
  END) AS observed_on_both_boundaries
FROM affected_employee
GROUP BY 1
HAVING COUNT(*) >= 30
ORDER BY missing_months_in_block;
