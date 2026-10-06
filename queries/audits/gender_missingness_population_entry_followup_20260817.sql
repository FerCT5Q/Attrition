-- Gender: composición temporal agregada del bloque de missingness de FY2026.
--
-- Pregunta: las llaves faltantes durante los cinco snapshots existían en el
-- snapshot previo, o entraron a la población durante el bloque? Esta consulta
-- no devuelve employee_id ni valores/códigos de gender.
--
-- Regla de interpretación declarada antes de ejecutar:
-- - Si la mayoría no estaba presente antes y vuelve poblada después, la brecha
--   se describe como una cohorte de entrada con atributo pendiente de carga.
-- - Si estaba presente antes, se describe como regresión temporal de población
--   existente. Ninguno de los dos resultados identifica por sí solo la causa
--   raíz operacional.

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
      WHEN snapshot_date = CAST('2025-11-23' AS DATE) THEN 1 ELSE 0
    END) AS present_before_block,
    MAX(CASE
      WHEN snapshot_date = CAST('2025-11-23' AS DATE)
       AND has_observed_value = 1
      THEN 1 ELSE 0
    END) AS observed_before_block,
    MAX(CASE
      WHEN snapshot_date = CAST('2026-05-24' AS DATE) THEN 1 ELSE 0
    END) AS present_after_block,
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
  END) = 5
)
SELECT
  COUNT(*) AS employees_missing_all_five_months,
  SUM(present_before_block) AS present_before_block,
  SUM(observed_before_block) AS observed_before_block,
  SUM(CASE
    WHEN present_before_block = 1 AND observed_before_block = 0
    THEN 1 ELSE 0
  END) AS present_but_missing_before_block,
  SUM(present_after_block) AS present_after_block,
  SUM(observed_after_block) AS observed_after_block,
  SUM(CASE
    WHEN present_before_block = 0
     AND observed_after_block = 1
    THEN 1 ELSE 0
  END) AS entered_after_prior_snapshot_and_observed_after_block
FROM affected_employee
HAVING COUNT(*) >= 30;
