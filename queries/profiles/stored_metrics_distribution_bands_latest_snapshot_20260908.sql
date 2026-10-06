-- Pregunta: ¿cómo se distribuyen los valores almacenados de compa_ratio y
-- prior_qc_work_years en el último snapshot de empleados regulares activos?
-- Población: worker_type='Employee', employee_type='Regular', active_status=1.
-- Grain: empleado-snapshot; los conteos usan empleados distintos.
-- Regla de publicación: cada banda visible debe tener n >= 30. Las colas de
-- baja frecuencia se incluyen en la banda superior, no se muestran aisladas.
-- Alcance: distribución del valor almacenado. No valida fórmula, lineage,
-- unidad, elegibilidad upstream ni significado de negocio de las métricas.

WITH latest_snapshot AS (
  SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
base AS (
  SELECT
    employee_id,
    compa_ratio,
    prior_qc_work_years
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND CAST(fis_mo_end_dt AS DATE) = (SELECT snapshot_date FROM latest_snapshot)
),
controls AS (
  SELECT COUNT(DISTINCT employee_id) AS eligible_employees
  FROM base
),
bands AS (
  SELECT
    'compa_ratio' AS metric,
    CASE
      WHEN compa_ratio <= 0 THEN 1
      WHEN compa_ratio < 0.8 THEN 2
      WHEN compa_ratio < 0.9 THEN 3
      WHEN compa_ratio < 1.0 THEN 4
      WHEN compa_ratio < 1.1 THEN 5
      WHEN compa_ratio < 1.25 THEN 6
      ELSE 7
    END AS band_order,
    CASE
      WHEN compa_ratio <= 0 THEN '≤ 0'
      WHEN compa_ratio < 0.8 THEN '> 0–< 0.8'
      WHEN compa_ratio < 0.9 THEN '0.8–< 0.9'
      WHEN compa_ratio < 1.0 THEN '0.9–< 1.0'
      WHEN compa_ratio < 1.1 THEN '1.0–< 1.1'
      WHEN compa_ratio < 1.25 THEN '1.1–< 1.25'
      ELSE '≥ 1.25'
    END AS band_label,
    employee_id
  FROM base
  WHERE compa_ratio IS NOT NULL

  UNION ALL

  SELECT
    'prior_qc_work_years' AS metric,
    CASE
      WHEN prior_qc_work_years = 0 THEN 1
      WHEN prior_qc_work_years < 1 THEN 2
      WHEN prior_qc_work_years < 3 THEN 3
      WHEN prior_qc_work_years < 5 THEN 4
      WHEN prior_qc_work_years < 10 THEN 5
      WHEN prior_qc_work_years < 15 THEN 6
      WHEN prior_qc_work_years < 25 THEN 7
      ELSE 8
    END AS band_order,
    CASE
      WHEN prior_qc_work_years = 0 THEN '0 años'
      WHEN prior_qc_work_years < 1 THEN '> 0–< 1 año'
      WHEN prior_qc_work_years < 3 THEN '1–< 3 años'
      WHEN prior_qc_work_years < 5 THEN '3–< 5 años'
      WHEN prior_qc_work_years < 10 THEN '5–< 10 años'
      WHEN prior_qc_work_years < 15 THEN '10–< 15 años'
      WHEN prior_qc_work_years < 25 THEN '15–< 25 años'
      ELSE '≥ 25 años'
    END AS band_label,
    employee_id
  FROM base
  WHERE prior_qc_work_years IS NOT NULL
),
aggregated AS (
  SELECT
    metric,
    band_order,
    band_label,
    COUNT(DISTINCT employee_id) AS employees
  FROM bands
  GROUP BY 1, 2, 3
)
SELECT
  (SELECT snapshot_date FROM latest_snapshot) AS snapshot_date,
  controls.eligible_employees,
  aggregated.metric,
  aggregated.band_order,
  aggregated.band_label,
  aggregated.employees,
  ROUND(100.0 * aggregated.employees / NULLIF(controls.eligible_employees, 0), 2) AS population_pct
FROM aggregated
CROSS JOIN controls
WHERE aggregated.employees >= 30
ORDER BY metric, band_order;
