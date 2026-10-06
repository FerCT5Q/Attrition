-- Gender: seguimiento mensual de missingness al grain empleado-snapshot.
--
-- Claim: La brecha observada en el gráfico histórico proviene de valores
-- ausentes después de TRIM(), no de la exposición de categorías protegidas.
-- Población: worker_type='Employee', employee_type='Regular', active_status=1.
-- Grain: un empleado por cierre de snapshot mensual; employee_id se usa sólo
-- dentro de los CTEs y nunca se devuelve.
-- Privacidad: esta consulta no devuelve valores ni etiquetas de gender.
--
-- Reglas de aceptación declaradas antes de ejecutar:
-- 1. Cada mes debe mantener missingness <= 5%; de lo contrario la calidad
--    reciente requiere investigación adicional.
-- 2. La causa se clasifica como NULL, blanco/espacios, ambos o no clasificada
--    al grain empleado-snapshot, sin publicar códigos de gender.
-- 3. Las llaves duplicadas se cuentan por separado; no se interpretan como
--    personas faltantes.

WITH source_rows AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS VARCHAR(20)) AS fiscal_year,
    employee_id,
    CASE
      WHEN NULLIF(TRIM(CAST(gender AS VARCHAR(256))), '') IS NOT NULL
      THEN 1 ELSE 0
    END AS has_observed_row,
    CASE WHEN gender IS NULL THEN 1 ELSE 0 END AS has_null_row,
    CASE
      WHEN gender IS NOT NULL
       AND TRIM(CAST(gender AS VARCHAR(256))) = ''
      THEN 1 ELSE 0
    END AS has_blank_row
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
employee_snapshot AS (
  SELECT
    snapshot_date,
    fiscal_year,
    employee_id,
    MAX(has_observed_row) AS has_observed_value,
    MAX(has_null_row) AS has_null_value,
    MAX(has_blank_row) AS has_blank_value,
    COUNT(*) AS source_rows_in_key
  FROM source_rows
  GROUP BY 1, 2, 3
),
monthly AS (
  SELECT
    snapshot_date,
    fiscal_year,
    COUNT(*) AS eligible_employee_snapshots,
    SUM(CASE WHEN has_observed_value = 1 THEN 1 ELSE 0 END)
      AS populated_employee_snapshots,
    SUM(CASE WHEN has_observed_value = 0 THEN 1 ELSE 0 END)
      AS missing_employee_snapshots,
    SUM(CASE
      WHEN has_observed_value = 0
       AND has_null_value = 1
       AND has_blank_value = 0
      THEN 1 ELSE 0
    END) AS null_only_missing_employee_snapshots,
    SUM(CASE
      WHEN has_observed_value = 0
       AND has_null_value = 0
       AND has_blank_value = 1
      THEN 1 ELSE 0
    END) AS blank_only_missing_employee_snapshots,
    SUM(CASE
      WHEN has_observed_value = 0
       AND has_null_value = 1
       AND has_blank_value = 1
      THEN 1 ELSE 0
    END) AS null_and_blank_missing_employee_snapshots,
    SUM(CASE
      WHEN has_observed_value = 0
       AND has_null_value = 0
       AND has_blank_value = 0
      THEN 1 ELSE 0
    END) AS unclassified_missing_employee_snapshots,
    SUM(CASE WHEN source_rows_in_key > 1 THEN 1 ELSE 0 END)
      AS duplicate_employee_snapshot_keys,
    ROUND(
      100.0 * SUM(CASE WHEN has_observed_value = 0 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
      6
    ) AS missing_percent
  FROM employee_snapshot
  GROUP BY 1, 2
)
SELECT
  snapshot_date,
  fiscal_year,
  eligible_employee_snapshots,
  populated_employee_snapshots,
  missing_employee_snapshots,
  null_only_missing_employee_snapshots,
  blank_only_missing_employee_snapshots,
  null_and_blank_missing_employee_snapshots,
  unclassified_missing_employee_snapshots,
  duplicate_employee_snapshot_keys,
  missing_percent,
  CASE WHEN missing_percent <= 5 THEN 1 ELSE 0 END AS missingness_rule_pass
FROM monthly
WHERE eligible_employee_snapshots >= 30
ORDER BY snapshot_date;
