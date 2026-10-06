/*
  Pregunta: ¿eng_or_noneng sirve como población estable del modelo (todos los
  ingenieros) a lo largo del tiempo, incluida la reasignación de job family del
  2026-09-01?
  Población: Employee, Regular, active_status=1, is_rf360_yes_no=0, por foto
  mensual desde 2020-07-26. Sólo conteos agregados por foto y valor.
  Regla de aceptación: valores consistentes (sin nulos relevantes) y sin salto
  >5% en el conteo Eng entre 2026-08-23 y 2026-09-27.
*/
SELECT
  CAST(fis_mo_end_dt AS DATE) AS foto,
  COALESCE(NULLIF(TRIM(eng_or_noneng), ''), '(nulo)') AS valor,
  COUNT(DISTINCT employee_id) AS personas
FROM hrda.post_hire_monthly_worker_dtls
WHERE CAST(fis_mo_end_dt AS DATE) >= DATE '2020-07-26'
  AND worker_type = 'Employee'
  AND employee_type = 'Regular'
  AND active_status = 1
  AND is_rf360_yes_no = 0
GROUP BY 1, 2
ORDER BY 1, 2;
