/*
  Pregunta: ¿la reasignación masiva de job_family del 2026-09-01 cambia el
  segmento (seg) que usa el modelo de Critical Tech para las mismas personas?

  Tipo semántico: grouped_mapping (job_family -> hrda.critical_tech.seg).
  Población: worker_type='Employee', employee_type='Regular', active_status=1,
  presentes en los snapshots mensuales 2026-08-23 y 2026-09-27.
  Grain: empleado; sólo se devuelven conteos agregados por par de segmentos.
  Regla de aceptación: seg es estable para el modelo si >=99% de las personas
  presentes en ambos snapshots conserva el mismo seg (incluido "fuera de
  Critical Tech"). Si no, seg histórico no es comparable con el futuro.
  Modo: presentation. Pares con <30 personas se agregan en una fila residual.
*/
WITH critical_map AS (
  SELECT
    TRIM(LOWER(extended_job_family)) AS family_key,
    MAX(NULLIF(TRIM(seg), '')) AS seg
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
  GROUP BY 1
),
snap AS (
  SELECT
    CAST(p.fis_mo_end_dt AS DATE) AS snapshot_date,
    p.employee_id,
    TRIM(LOWER(p.job_family)) AS family_key,
    COALESCE(m.seg, '(fuera de Critical Tech)') AS seg
  FROM hrda.post_hire_monthly_worker_dtls p
  LEFT JOIN critical_map m
    ON TRIM(LOWER(p.job_family)) = m.family_key
  WHERE CAST(p.fis_mo_end_dt AS DATE) IN (DATE '2026-08-23', DATE '2026-09-27')
    AND p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
),
paired AS (
  SELECT
    a.employee_id,
    a.seg AS seg_before,
    b.seg AS seg_after,
    CASE WHEN a.family_key = b.family_key THEN 0 ELSE 1 END AS family_changed
  FROM snap a
  INNER JOIN snap b
    ON a.employee_id = b.employee_id
   AND a.snapshot_date = DATE '2026-08-23'
   AND b.snapshot_date = DATE '2026-09-27'
),
pairs AS (
  SELECT
    seg_before,
    seg_after,
    COUNT(DISTINCT employee_id) AS employees,
    SUM(family_changed) AS employees_family_changed
  FROM paired
  GROUP BY 1, 2
)
SELECT
  CASE WHEN employees >= 30 THEN seg_before ELSE '(pares <30 agrupados)' END AS seg_before,
  CASE WHEN employees >= 30 THEN seg_after ELSE '(pares <30 agrupados)' END AS seg_after,
  SUM(employees) AS employees,
  SUM(employees_family_changed) AS employees_family_changed
FROM pairs
GROUP BY 1, 2
ORDER BY 3 DESC;
