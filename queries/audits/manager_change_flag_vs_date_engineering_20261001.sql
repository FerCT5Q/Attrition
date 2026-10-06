/*
  Pregunta: ¿manager_change_12m del frame base (yes/no/unknown) refleja los
  cambios de manager de los últimos 12 meses, o el flag manager_change sólo
  marca el mes del cambio y la regla clasifica como 'unknown' a quien no cambió?
  Población: ingenieros Regular activos sin RF360, foto 2026-07-26.
  Regla de aceptación: si la mayoría de 'unknown' tiene manager_change=0 con
  fecha nula, la categoría no es "sin dato" sino "sin cambio este mes", y la
  variable debe reconstruirse contando cambios entre fotos.
  Sólo conteos agregados.
*/
WITH foto AS (
  SELECT employee_id, manager_change, manager_change_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) = DATE '2026-07-26'
    AND worker_type = 'Employee' AND employee_type = 'Regular'
    AND active_status = 1 AND is_rf360_yes_no = 0
    AND TRIM(eng_or_noneng) = 'Engineering'
),
hist AS (
  SELECT employee_id, COUNT(DISTINCT manager_change_date) AS cambios_12m
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) > DATE '2025-07-26'
    AND CAST(fis_mo_end_dt AS DATE) <= DATE '2026-07-26'
    AND manager_change = 1
    AND manager_change_date > DATE '2025-07-26'
    AND manager_change_date <= DATE '2026-07-26'
  GROUP BY 1
)
SELECT
  COALESCE(CAST(f.manager_change AS VARCHAR), 'nulo') AS flag_mes,
  CASE WHEN f.manager_change_date IS NULL THEN 'fecha nula'
       WHEN f.manager_change_date > DATE '2025-07-26' THEN 'fecha <=12m'
       ELSE 'fecha >12m' END AS fecha,
  CASE WHEN COALESCE(h.cambios_12m, 0) = 0 THEN '0'
       WHEN h.cambios_12m = 1 THEN '1' ELSE '2+' END AS cambios_12m_entre_fotos,
  COUNT(DISTINCT f.employee_id) AS personas
FROM foto f LEFT JOIN hist h ON h.employee_id = f.employee_id
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
