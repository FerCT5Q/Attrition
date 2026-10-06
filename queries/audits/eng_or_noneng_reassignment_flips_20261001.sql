/*
  Pregunta: ¿la reasignación de job family del 2026-09-01 cambió eng_or_noneng
  de las mismas personas? Regla de aceptación: >=99% conserva el valor.
  Población: Employee, Regular, activos, sin RF360, en 2026-08-23 y 2026-09-27.
  Sólo conteos agregados por par de valores.
*/
WITH f AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS foto, employee_id,
         COALESCE(NULLIF(TRIM(eng_or_noneng), ''), '(nulo)') AS valor
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) IN (DATE '2026-08-23', DATE '2026-09-27')
    AND worker_type = 'Employee' AND employee_type = 'Regular'
    AND active_status = 1 AND is_rf360_yes_no = 0
)
SELECT a.valor AS valor_ago, b.valor AS valor_sep, COUNT(DISTINCT a.employee_id) AS personas
FROM f a JOIN f b ON a.employee_id = b.employee_id
 AND a.foto = DATE '2026-08-23' AND b.foto = DATE '2026-09-27'
GROUP BY 1, 2 ORDER BY 3 DESC;
