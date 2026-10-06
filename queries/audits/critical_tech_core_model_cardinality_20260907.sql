/*
  Cardinalidad del frame agregado del champion v1.

  La especificación v1 ajusta el hazard con contexto Critical Tech, nivel,
  tenure y cambio reciente de manager. Promotion y transfer se conservan para
  análisis de sensibilidad/cohortes, pero no se incluyen en el primer frame
  multivariable para evitar celdas demasiado dispersas.

  Salida exclusivamente agregada por snapshot.
*/
WITH params AS (
  SELECT DATE '2026-09-07' AS knowledge_boundary
),
critical_map AS (
  SELECT
    TRIM(LOWER(extended_job_family)) AS family_key,
    MAX(NULLIF(TRIM(seg), '')) AS seg
  FROM hrda.critical_tech
  WHERE extended_job_family IS NOT NULL
    AND TRIM(extended_job_family) <> ''
  GROUP BY 1
),
snapshot_calendar AS (
  SELECT
    snapshot_date,
    LEAD(snapshot_date) OVER (ORDER BY snapshot_date) AS next_snapshot_date
  FROM (
    SELECT DISTINCT CAST(fis_mo_end_dt AS DATE) AS snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
      AND CAST(fis_mo_end_dt AS DATE) <= (SELECT knowledge_boundary FROM params)
  ) dates
),
raw_scope AS (
  SELECT
    c.snapshot_date,
    c.next_snapshot_date,
    p.employee_id,
    p.level_grouped,
    p.original_hire_date,
    p.manager_change,
    p.manager_change_date,
    m.seg
  FROM snapshot_calendar c
  INNER JOIN hrda.post_hire_monthly_worker_dtls p
    ON CAST(p.fis_mo_end_dt AS DATE) = c.snapshot_date
  INNER JOIN critical_map m
    ON TRIM(LOWER(p.job_family)) = m.family_key
  WHERE c.next_snapshot_date IS NOT NULL
    AND c.next_snapshot_date <= (SELECT knowledge_boundary FROM params)
    AND p.worker_type = 'Employee'
    AND p.employee_type = 'Regular'
    AND p.active_status = 1
),
base_snapshots AS (
  SELECT DISTINCT
    snapshot_date,
    next_snapshot_date,
    employee_id,
    COALESCE(NULLIF(TRIM(level_grouped), ''), '(unknown)') AS level_grouped,
    CASE
      WHEN original_hire_date IS NULL OR original_hire_date > snapshot_date
        THEN '(unknown)'
      WHEN DATEDIFF(month, original_hire_date, snapshot_date) < 12
        THEN '<1 year'
      WHEN DATEDIFF(month, original_hire_date, snapshot_date) < 36
        THEN '1-3 years'
      WHEN DATEDIFF(month, original_hire_date, snapshot_date) < 84
        THEN '3-7 years'
      ELSE '7+ years'
    END AS company_tenure_band,
    CASE
      WHEN manager_change = 1
       AND manager_change_date IS NOT NULL
       AND manager_change_date > DATEADD(month, -12, snapshot_date)
       AND manager_change_date <= snapshot_date
        THEN 'yes'
      WHEN manager_change IS NULL OR manager_change_date IS NULL
        THEN 'unknown'
      ELSE 'no'
    END AS manager_change_12m,
    seg
  FROM raw_scope
),
voluntary_events AS (
  SELECT employee_id, CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(term_type::VARCHAR), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
    AND CAST(term_date AS DATE) <= (SELECT knowledge_boundary FROM params)
  GROUP BY 1, 2
),
labeled AS (
  SELECT
    b.snapshot_date,
    b.employee_id,
    b.level_grouped,
    b.company_tenure_band,
    b.manager_change_12m,
    b.seg,
    MAX(CASE WHEN v.employee_id IS NOT NULL THEN 1 ELSE 0 END)
      AS voluntary_next_snapshot
  FROM base_snapshots b
  LEFT JOIN voluntary_events v
    ON v.employee_id = b.employee_id
   AND v.term_date > b.snapshot_date
   AND v.term_date <= b.next_snapshot_date
  GROUP BY 1,2,3,4,5,6
),
cells AS (
  SELECT
    snapshot_date,
    seg,
    level_grouped,
    company_tenure_band,
    manager_change_12m,
    COUNT(*) AS exposure_count,
    SUM(voluntary_next_snapshot) AS event_count
  FROM labeled
  GROUP BY 1,2,3,4,5
)
SELECT
  snapshot_date,
  COUNT(*) AS core_feature_cell_count,
  SUM(exposure_count) AS exposure_count,
  SUM(event_count) AS event_count,
  MAX(exposure_count) AS max_cell_exposure
FROM cells
GROUP BY 1
ORDER BY 1;
