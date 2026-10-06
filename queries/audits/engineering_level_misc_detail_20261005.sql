/*
  Aclaracion del slide 5 de la v9, modo presentation, sin cambio de scores.
  Concepto: etiqueta almacenada Misc en level_grouped (grouped_mapping).
  Uso: describir la categoria llamada 'otros' en la presentacion.
  Poblacion: Employee/Regular activos, no RF360, Engineering en cada foto.
  Ventanas: historia del modelo jul-2021 a jul-2026 y foto 2026-07-26.
  Grain interno: empleado-foto, salida: resumen de poblacion y categorias.
  Hipotesis: Misc tiene niveles detallados identificables y puede aparecer
  en la historia aunque no exista en la ultima foto de la v9.
  Regla descriptiva: solo atribuir un nivel detallado a Misc cuando ambos
  campos coincidan en la misma fila y haya >=30 empleados distintos.
  No interpreta el nombre de la categoria como definicion oficial.
  Conteos de Misc entre 1 y 29 se suprimen. Los detalles solo devuelven
  banda 30+ para evitar revelar remanentes por diferencia.
  Este cruce describe los valores observados. No valida el mapping oficial
  ni cambia la definicion, consistencia o score de la variable.
*/
WITH periods AS (
  SELECT 'historia_v9'::VARCHAR(32) AS period_label,
         DATE '2021-07-01' AS period_start, DATE '2026-07-26' AS period_end
  UNION ALL
  SELECT 'foto_v9'::VARCHAR(32), DATE '2026-07-26', DATE '2026-07-26'
), base AS (
  SELECT DISTINCT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    COALESCE(NULLIF(TRIM(level_grouped), ''), '(unknown)') AS level_label,
    COALESCE(NULLIF(TRIM(job_level_primary_position), ''), '(unknown)') AS detailed_level
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2021-07-01' AND DATE '2026-07-26'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND is_rf360_yes_no = 0
    AND TRIM(eng_or_noneng) = 'Engineering'
), scoped AS (
  SELECT p.period_label, p.period_start, p.period_end,
         b.employee_id, b.snapshot_date, b.level_label, b.detailed_level
  FROM periods p
  JOIN base b ON b.snapshot_date BETWEEN p.period_start AND p.period_end
), summary AS (
  SELECT period_label, period_start, period_end,
         COUNT(DISTINCT employee_id) AS eligible_employees,
         COUNT(DISTINCT snapshot_date) AS snapshots,
         COUNT(DISTINCT CASE WHEN level_label = 'Misc' THEN employee_id END) AS misc_employees,
         MIN(CASE WHEN level_label = 'Misc' THEN snapshot_date END) AS first_misc_date,
         MAX(CASE WHEN level_label = 'Misc' THEN snapshot_date END) AS last_misc_date
  FROM scoped
  GROUP BY 1, 2, 3
), details AS (
  SELECT period_label, period_start, period_end, detailed_level,
         COUNT(DISTINCT employee_id) AS detail_employees,
         MIN(snapshot_date) AS first_seen,
         MAX(snapshot_date) AS last_seen
  FROM scoped
  WHERE level_label = 'Misc'
  GROUP BY 1, 2, 3, 4
  HAVING COUNT(DISTINCT employee_id) >= 30
)
SELECT 'summary'::VARCHAR(32) AS result_type, period_label, period_start, period_end,
       'Misc'::VARCHAR(256) AS level_label, NULL::VARCHAR(256) AS detailed_level,
       eligible_employees, snapshots,
       CASE WHEN misc_employees = 0 OR misc_employees >= 30 THEN misc_employees END AS misc_employee_count,
       CASE WHEN misc_employees = 0 THEN '0'
            WHEN misc_employees >= 30 THEN '30+'
            ELSE '1-29 (suprimido)' END::VARCHAR(64) AS cohort_band,
       CASE WHEN misc_employees >= 30 THEN first_misc_date END AS first_seen,
       CASE WHEN misc_employees >= 30 THEN last_misc_date END AS last_seen
FROM summary
WHERE eligible_employees >= 30
UNION ALL
SELECT 'detail'::VARCHAR(32), period_label, period_start, period_end,
       'Misc'::VARCHAR(256), detailed_level,
       NULL::BIGINT, NULL::BIGINT, NULL::BIGINT,
       '30+'::VARCHAR(64), first_seen, last_seen
FROM details
ORDER BY period_label, result_type, detailed_level;
