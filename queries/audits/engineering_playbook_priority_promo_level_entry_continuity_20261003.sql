/*
  Continuidad de promociones y de levelentrydate alrededor del cambio de
  fuente de 2022-10 (2026-10-03). Engineering, Employee/Regular activos, sin
  RF360. Sólo agregados.

  Preguntas:
  1) ¿Desde qué año hay promociones registradas (is_promo) con volumen estable?
  2) ¿levelentrydate antes de 2022-10 coincide con el valor después del cambio
     para la misma persona (2022-09-25 vs 2022-10-23)?
  Regla: se usa el historial de promociones desde el primer año con tasa
  anual >= 5% de la población; levelentrydate previo se acepta si coincide
  en >= 90% de las personas con valor en ambas fotos.
*/
WITH promo_year AS (
  SELECT EXTRACT(year FROM CAST(fis_mo_end_dt AS DATE)) AS yr,
         COUNT(DISTINCT employee_id) AS people,
         COUNT(DISTINCT CASE WHEN is_promo = 1 THEN employee_id END) AS promoted
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) >= DATE '2018-01-01'
    AND worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1
    AND is_rf360_yes_no = 0 AND TRIM(eng_or_noneng) = 'Engineering' AND employee_id IS NOT NULL
  GROUP BY 1
),
le AS (
  SELECT employee_id,
         MAX(CASE WHEN CAST(fis_mo_end_dt AS DATE) = DATE '2022-09-25' THEN CAST(levelentrydate AS DATE) END) AS le_before,
         MAX(CASE WHEN CAST(fis_mo_end_dt AS DATE) = DATE '2022-10-23' THEN CAST(levelentrydate AS DATE) END) AS le_after
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) IN (DATE '2022-09-25', DATE '2022-10-23')
    AND worker_type = 'Employee' AND employee_type = 'Regular' AND active_status = 1
    AND is_rf360_yes_no = 0 AND TRIM(eng_or_noneng) = 'Engineering' AND employee_id IS NOT NULL
  GROUP BY 1
)
SELECT 'promo_' || CAST(yr AS VARCHAR) AS metric, people AS n, promoted AS value,
       ROUND(100.0 * promoted / people, 1) AS pct
FROM promo_year
UNION ALL
SELECT 'level_entry_both_present', COUNT(*),
       SUM(CASE WHEN le_before = le_after THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN le_before = le_after THEN 1 ELSE 0 END) / COUNT(*), 1)
FROM le WHERE le_before IS NOT NULL AND le_after IS NOT NULL
UNION ALL
SELECT 'level_entry_missing_before_present_after', COUNT(*), NULL, NULL
FROM le WHERE le_before IS NULL AND le_after IS NOT NULL
ORDER BY 1
