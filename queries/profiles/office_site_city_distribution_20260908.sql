-- Distribución congelada para la lámina "Office site and city".
-- Entregable: presentación agregada; no devuelve filas ni identificadores.
-- Población: worker_type='Employee', employee_type='Regular', active_status=1.
-- Snapshot: 2026-08-23. Grain: empleado-snapshot.
-- Regla de publicación: top 20 pares completos con n >= 30; la cola de
-- pares completos fuera del top 20 y los faltantes se publican sólo si n >= 30.

WITH base AS (
  SELECT
    employee_id,
    NULLIF(TRIM(CAST(office_site AS VARCHAR(512))), '') AS office_site,
    NULLIF(TRIM(CAST(city AS VARCHAR(512))), '') AS city
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt = DATE '2026-08-23'
),
eligible AS (
  SELECT COUNT(DISTINCT employee_id) AS eligible_employees
  FROM base
),
pair_counts AS (
  SELECT
    office_site,
    city,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM base
  WHERE office_site IS NOT NULL
    AND city IS NOT NULL
  GROUP BY office_site, city
),
ranked_pairs AS (
  SELECT
    office_site,
    city,
    employee_count,
    ROW_NUMBER() OVER (ORDER BY employee_count DESC, office_site, city) AS pair_rank
  FROM pair_counts
  WHERE employee_count >= 30
),
summary AS (
  SELECT
    COUNT(DISTINCT CASE WHEN office_site IS NOT NULL AND city IS NOT NULL THEN employee_id END) AS pair_population_employees,
    COUNT(DISTINCT CASE WHEN office_site IS NULL OR city IS NULL THEN employee_id END) AS missing_pair_employees,
    COUNT(DISTINCT CASE WHEN office_site IS NOT NULL AND city IS NOT NULL THEN office_site || '|' || city END) AS distinct_complete_pairs
  FROM base
),
top_totals AS (
  SELECT
    COALESCE(SUM(employee_count), 0) AS top_20_employee_count,
    COUNT(*) AS top_20_pair_count
  FROM ranked_pairs
  WHERE pair_rank <= 20
),
display_rows AS (
  SELECT
    'top_pair' AS row_type,
    pair_rank AS display_order,
    office_site || ' · ' || city AS display_label,
    office_site,
    city,
    employee_count,
    '2026-08-23' AS snapshot_date
  FROM ranked_pairs
  WHERE pair_rank <= 20
  UNION ALL
  SELECT
    'other_pairs',
    21,
    'Other site-city pairs',
    CAST(NULL AS VARCHAR(512)),
    CAST(NULL AS VARCHAR(512)),
    s.pair_population_employees - t.top_20_employee_count,
    '2026-08-23'
  FROM summary s
  CROSS JOIN top_totals t
  WHERE s.pair_population_employees - t.top_20_employee_count >= 30
  UNION ALL
  SELECT
    'missing_pair',
    22,
    'No office-site/city pair',
    CAST(NULL AS VARCHAR(512)),
    CAST(NULL AS VARCHAR(512)),
    missing_pair_employees,
    '2026-08-23'
  FROM summary
  WHERE missing_pair_employees >= 30
)
SELECT
  d.row_type,
  d.display_order,
  d.display_label,
  d.office_site,
  d.city,
  d.employee_count,
  d.snapshot_date,
  e.eligible_employees,
  s.pair_population_employees,
  s.missing_pair_employees,
  s.distinct_complete_pairs,
  t.top_20_pair_count,
  t.top_20_employee_count,
  CASE WHEN e.eligible_employees > 0
    THEN d.employee_count::DECIMAL(18,6) / e.eligible_employees
    ELSE 0 END AS share_of_eligible
FROM display_rows d
CROSS JOIN eligible e
CROSS JOIN summary s
CROSS JOIN top_totals t
ORDER BY d.display_order, d.display_label;
