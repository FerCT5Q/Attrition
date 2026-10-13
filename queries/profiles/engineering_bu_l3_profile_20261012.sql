/*
  Perfil agregado de BU L3 en la población de modelado.
  Modo: presentation. Sólo se muestran buckets con al menos 30 personas.
  No se devuelven empleados, identificadores ni valores individuales.
*/
WITH employee_snapshot AS (
  SELECT
    CAST(p.fis_mo_end_dt AS DATE) AS snapshot_date,
    p.employee_id,
    MAX(NULLIF(TRIM(p.cost_centerid), '')) AS cost_centerid
  FROM hrda.post_hire_monthly_worker_dtls p
  WHERE CAST(p.fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
    AND p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
    AND p.is_rf360_yes_no = 0
    AND TRIM(p.eng_or_noneng) = 'Engineering'
    AND p.employee_id IS NOT NULL
  GROUP BY 1, 2
),
joined AS (
  SELECT
    e.snapshot_date,
    e.employee_id,
    COALESCE(MAX(NULLIF(TRIM(d.ude_bu_reporting_l3), '')), '(unknown)') AS bu_l3
  FROM employee_snapshot e
  LEFT JOIN hrda.d_department d
    ON CAST(d.nk_dept_id AS VARCHAR) = e.cost_centerid
   AND CAST(d.edw_effective_dt AS DATE) <= e.snapshot_date
   AND (
        d.edw_end_dt IS NULL
        OR e.snapshot_date < CAST(d.edw_end_dt AS DATE)
   )
  GROUP BY 1, 2
)
SELECT
  snapshot_date,
  bu_l3,
  COUNT(*) AS employee_snapshot_rows,
  COUNT(DISTINCT employee_id) AS distinct_employees
FROM joined
GROUP BY 1, 2
HAVING COUNT(DISTINCT employee_id) >= 30
ORDER BY snapshot_date, employee_snapshot_rows DESC, bu_l3;
