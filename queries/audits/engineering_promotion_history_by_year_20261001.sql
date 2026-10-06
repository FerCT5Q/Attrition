/*
  Pregunta: ¿is_promo/promotion_date marcan sólo el mes de la promoción y
  existen en toda la historia, de modo que "meses desde la última promoción"
  se pueda reconstruir con las fotos <= t?
  Población: Engineering, Regular activos sin RF360.
  Regla de aceptación: promociones registradas en todos los años 2018-2026
  con volumen comparable (sin años en cero) y promotion_date <= foto.
  Sólo conteos agregados.
*/
SELECT
  EXTRACT(year FROM CAST(fis_mo_end_dt AS DATE)) AS anio,
  COUNT(DISTINCT CAST(fis_mo_end_dt AS DATE)) AS fotos,
  COUNT(*) AS filas,
  SUM(CASE WHEN is_promo = 1 THEN 1 ELSE 0 END) AS filas_promo,
  SUM(CASE WHEN is_promo = 1 AND promotion_date IS NOT NULL THEN 1 ELSE 0 END) AS promo_con_fecha,
  SUM(CASE WHEN promotion_date > CAST(fis_mo_end_dt AS DATE) THEN 1 ELSE 0 END) AS fecha_futura,
  SUM(CASE WHEN promotion_date IS NOT NULL AND promotion_date <= DATEADD(month, -2, CAST(fis_mo_end_dt AS DATE)) THEN 1 ELSE 0 END) AS fecha_mas_de_2m_antes,
  SUM(CASE WHEN levelentrydate > CAST(fis_mo_end_dt AS DATE) THEN 1 ELSE 0 END) AS levelentry_futura,
  SUM(CASE WHEN manager_employee_id IS NULL THEN 1 ELSE 0 END) AS sin_manager
FROM hrda.post_hire_monthly_worker_dtls
WHERE worker_type = 'Employee' AND employee_type = 'Regular'
  AND active_status = 1 AND is_rf360_yes_no = 0
  AND TRIM(eng_or_noneng) = 'Engineering'
  AND CAST(fis_mo_end_dt AS DATE) >= DATE '2017-01-01'
GROUP BY 1
ORDER BY 1
