/*
  Pregunta: ¿los flags de evento (is_promo, manager_change) existen desde el
  inicio de la tabla y con volumen estable mes a mes, para reconstruir
  "meses desde la última promoción" y "cambios de manager en 12 meses" con
  fotos <= t? ¿El hueco de promociones en 2026 es real o de carga?
  Población: Employee/Regular activos sin RF360 (todas las funciones, para
  la historia previa a la marca eng_or_noneng) y Engineering por separado.
  Regla de aceptación: flags presentes en todos los meses con volumen > 0 en
  cada año; un mes sin registros se trata como ruptura de fuente.
  Sólo conteos agregados.
*/
SELECT
  DATE_TRUNC('quarter', CAST(fis_mo_end_dt AS DATE))::DATE AS trimestre,
  COUNT(DISTINCT CAST(fis_mo_end_dt AS DATE)) AS fotos,
  COUNT(*) AS filas,
  SUM(CASE WHEN TRIM(eng_or_noneng) = 'Engineering' THEN 1 ELSE 0 END) AS filas_eng,
  SUM(CASE WHEN eng_or_noneng IS NULL THEN 1 ELSE 0 END) AS eng_nulo,
  SUM(CASE WHEN is_promo = 1 THEN 1 ELSE 0 END) AS promo,
  SUM(CASE WHEN is_promo = 1 AND TRIM(eng_or_noneng) = 'Engineering' THEN 1 ELSE 0 END) AS promo_eng,
  SUM(CASE WHEN manager_change = 1 THEN 1 ELSE 0 END) AS cambio_manager,
  SUM(CASE WHEN manager_change = 1 AND TRIM(eng_or_noneng) = 'Engineering' THEN 1 ELSE 0 END) AS cambio_manager_eng,
  SUM(CASE WHEN manager_employee_id IS NULL THEN 1 ELSE 0 END) AS sin_manager
FROM hrda.post_hire_monthly_worker_dtls
WHERE worker_type = 'Employee' AND employee_type = 'Regular'
  AND active_status = 1 AND COALESCE(is_rf360_yes_no, 0) = 0
GROUP BY 1
ORDER BY 1
