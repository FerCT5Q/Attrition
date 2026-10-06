/*
  Dominio almacenado de Region al snapshot 2026-08-23.

  Pregunta: ¿qué categorías exactas almacena HRDA para Region en la población
  de empleados regulares activos que alimenta la lámina?

  Población: worker_type='Employee', employee_type='Regular', active_status=1.
  Grain: empleado-snapshot distinto. Entrega presentation; n >= 30.
*/
SELECT
  region,
  COUNT(DISTINCT employee_id) AS employee_count
FROM hrda.post_hire_monthly_worker_dtls
WHERE fis_mo_end_dt::date = DATE '2026-08-23'
  AND worker_type = 'Employee'
  AND employee_type = 'Regular'
  AND active_status = 1
GROUP BY region
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY employee_count DESC, region;
