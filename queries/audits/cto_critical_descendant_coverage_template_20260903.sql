-- Pregunta: ¿Todos los empleados activos regulares bajo las dos raices CTO
-- pertenecen al mapeo actual de Critical Tech?
-- Raices: sustituir los dos placeholders solo durante la ejecucion; no persistir IDs.
-- Poblacion: employee_type='Regular', worker_type='Employee', active_status=1.
-- Grain: empleado en el ultimo snapshot mensual disponible.
-- Regla de aceptacion: las dos raices tienen reportes directos, no hay miembros
-- duplicados ni multiples managers, y cto_noncritical_employee_count = 0.
WITH RECURSIVE
latest_snapshot AS (
  SELECT MAX(fis_mo_end_dt) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
),
provided_roots AS (
  SELECT CAST('{{LEADER_EMPLOYEE_ID_1}}' AS VARCHAR(64)) AS root_employee_id
  UNION ALL
  SELECT CAST('{{LEADER_EMPLOYEE_ID_2}}' AS VARCHAR(64)) AS root_employee_id
),
worker_snapshot AS (
  SELECT
    CAST(employee_id AS VARCHAR(64)) AS employee_id,
    CAST(MIN(manager_employee_id) AS VARCHAR(64)) AS manager_employee_id,
    MIN(job_family) AS job_family,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT manager_employee_id) AS manager_variants
  FROM hrda.post_hire_monthly_worker_dtls AS m
  CROSS JOIN latest_snapshot AS l
  WHERE m.fis_mo_end_dt = l.snapshot_date
    AND m.worker_type = 'Employee'
    AND m.employee_type = 'Regular'
    AND m.active_status = 1
  GROUP BY 1
),
critical_mapping AS (
  SELECT
    UPPER(TRIM(extended_job_family)) AS normalized_job_family,
    COUNT(*) AS mapping_rows
  FROM hrda.critical_tech
  WHERE NULLIF(TRIM(extended_job_family), '') IS NOT NULL
  GROUP BY 1
),
critical_snapshot AS (
  SELECT w.employee_id
  FROM worker_snapshot AS w
  INNER JOIN critical_mapping AS c
    ON c.normalized_job_family = UPPER(TRIM(w.job_family))
),
static_stats AS (
  SELECT
    (SELECT snapshot_date FROM latest_snapshot) AS snapshot_date,
    (SELECT COUNT(*) FROM provided_roots) AS provided_root_count,
    (SELECT COUNT(DISTINCT manager_employee_id)
     FROM worker_snapshot
     WHERE manager_employee_id IN (SELECT root_employee_id FROM provided_roots)) AS roots_with_direct_reports,
    (SELECT COUNT(*)
     FROM provided_roots AS r
     INNER JOIN worker_snapshot AS w
       ON w.employee_id = r.root_employee_id) AS roots_present_in_employee_snapshot,
    (SELECT COUNT(*) FROM worker_snapshot) AS active_regular_employee_count,
    (SELECT COUNT(*) FROM critical_snapshot) AS critical_employee_count,
    (SELECT COUNT(*) FROM worker_snapshot WHERE source_rows > 1) AS duplicate_source_employee_count,
    (SELECT COUNT(*) FROM worker_snapshot WHERE manager_variants > 1) AS multi_manager_employee_count,
    (SELECT COUNT(*) FROM critical_mapping WHERE mapping_rows > 1) AS duplicate_critical_mapping_value_count
),
hierarchy (
  root_employee_id,
  employee_id,
  manager_employee_id,
  job_family,
  depth,
  path
) AS (
  SELECT
    r.root_employee_id,
    w.employee_id,
    w.manager_employee_id,
    w.job_family,
    1 AS depth,
    CAST('|' || w.employee_id || '|' AS VARCHAR(65535)) AS path
  FROM provided_roots AS r
  INNER JOIN worker_snapshot AS w
    ON w.manager_employee_id = r.root_employee_id

  UNION ALL

  SELECT
    h.root_employee_id,
    w.employee_id,
    w.manager_employee_id,
    w.job_family,
    h.depth + 1 AS depth,
    CAST(h.path || w.employee_id || '|' AS VARCHAR(65535)) AS path
  FROM hierarchy AS h
  INNER JOIN worker_snapshot AS w
    ON w.manager_employee_id = h.employee_id
  WHERE h.depth < 30
    AND POSITION('|' || w.employee_id || '|' IN h.path) = 0
)
SELECT
  s.snapshot_date,
  s.provided_root_count,
  s.roots_with_direct_reports,
  s.roots_present_in_employee_snapshot,
  s.active_regular_employee_count,
  s.critical_employee_count,
  h.cto_employee_count,
  h.cto_critical_employee_count,
  h.cto_employee_count - h.cto_critical_employee_count AS cto_noncritical_employee_count,
  s.critical_employee_count - h.cto_critical_employee_count AS critical_noncto_employee_count,
  h.duplicate_cto_membership_count,
  h.maximum_cto_depth,
  h.depth_limit_employee_count,
  s.duplicate_source_employee_count,
  s.multi_manager_employee_count,
  s.duplicate_critical_mapping_value_count
FROM static_stats AS s
CROSS JOIN (
  SELECT
    COUNT(*) AS cto_employee_count,
    SUM(CASE WHEN c.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS cto_critical_employee_count,
    SUM(CASE WHEN m.root_membership_count > 1 THEN 1 ELSE 0 END) AS duplicate_cto_membership_count,
    MAX(m.maximum_depth) AS maximum_cto_depth,
    SUM(CASE WHEN m.maximum_depth = 30 THEN 1 ELSE 0 END) AS depth_limit_employee_count
  FROM (
    SELECT
      employee_id,
      COUNT(DISTINCT root_employee_id) AS root_membership_count,
      MAX(depth) AS maximum_depth
    FROM hierarchy
    GROUP BY 1
  ) AS m
  LEFT JOIN critical_snapshot AS c
    ON c.employee_id = m.employee_id
) AS h;
