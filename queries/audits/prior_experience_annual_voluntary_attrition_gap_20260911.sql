/*
  Follow-up audit for unresolved Voluntary event attribution.
  Aggregate-only; no employee identifiers or event rows are returned.
  Purpose: distinguish left-censoring/no prior snapshot, invalid prior values,
  and ambiguous employee-snapshot values before deciding publication wording.
*/
WITH
parameters AS (
  SELECT DATE '2026-09-11' AS cutoff_date
),
raw_calendar AS (
  SELECT
    CAST(fis_mo_beg_dt AS DATE) AS period_begin,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(fiscal_year AS INTEGER) AS fiscal_year,
    CAST(fiscal_month AS INTEGER) AS fiscal_month,
    MOD(CAST(fiscal_month AS INTEGER), 100) AS fiscal_month_of_year
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) <= (SELECT cutoff_date FROM parameters)
  GROUP BY 1, 2, 3, 4, 5
),
calendar_by_year AS (
  SELECT
    fiscal_year,
    COUNT(DISTINCT snapshot_date) AS snapshot_count,
    COUNT(DISTINCT fiscal_month_of_year) AS fiscal_month_count,
    MIN(fiscal_month_of_year) AS min_fiscal_month,
    MAX(fiscal_month_of_year) AS max_fiscal_month,
    MAX(snapshot_date) AS last_snapshot_date
  FROM raw_calendar
  GROUP BY 1
),
selected_years AS (
  SELECT fiscal_year
  FROM calendar_by_year
  WHERE snapshot_count = 12
    AND fiscal_month_count = 12
    AND min_fiscal_month = 1
    AND max_fiscal_month = 12
  ORDER BY fiscal_year DESC
  LIMIT 5
),
selected_periods AS (
  SELECT
    c.period_begin,
    c.snapshot_date,
    c.fiscal_year,
    c.fiscal_month
  FROM raw_calendar AS c
  INNER JOIN selected_years AS y USING (fiscal_year)
),
all_source_rows AS (
  SELECT
    worker.employee_id,
    CAST(worker.fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(worker.term_date AS DATE) AS term_date,
    CAST(worker.prior_qc_work_years AS DECIMAL(18,6)) AS prior_qc_work_years,
    worker.worker_type,
    worker.employee_type,
    worker.active_status,
    UPPER(NULLIF(TRIM(CAST(worker.term_type AS VARCHAR(256))), '')) AS normalized_term_type
  FROM hrda.post_hire_monthly_worker_dtls AS worker
  CROSS JOIN parameters
  WHERE worker.fis_mo_end_dt IS NOT NULL
    AND CAST(worker.fis_mo_end_dt AS DATE) <= parameters.cutoff_date
),
voluntary_events AS (
  SELECT
    a.employee_id,
    a.term_date,
    p.fiscal_year
  FROM all_source_rows AS a
  INNER JOIN selected_periods AS p
    ON a.term_date >= p.period_begin
   AND a.term_date <= p.snapshot_date
  WHERE a.worker_type = 'Employee'
    AND a.employee_type = 'Regular'
    AND a.normalized_term_type = 'VOLUNTARY'
    AND a.term_date IS NOT NULL
  GROUP BY 1, 2, 3
),
prior_snapshot_summary AS (
  SELECT
    e.employee_id,
    e.term_date,
    e.fiscal_year,
    COUNT(DISTINCT CASE
      WHEN h.worker_type = 'Employee'
       AND h.employee_type = 'Regular'
       AND h.active_status = 1
       AND h.snapshot_date < e.term_date
      THEN h.snapshot_date END) AS active_prior_snapshot_count,
    COUNT(DISTINCT CASE
      WHEN h.worker_type = 'Employee'
       AND h.employee_type = 'Regular'
       AND h.active_status = 1
       AND h.snapshot_date < e.term_date
       AND h.prior_qc_work_years IS NOT NULL
       AND h.prior_qc_work_years >= 0
      THEN h.snapshot_date END) AS valid_prior_snapshot_count,
    COUNT(DISTINCT CASE
      WHEN h.worker_type = 'Employee'
       AND h.employee_type = 'Regular'
       AND h.active_status = 1
       AND h.snapshot_date < e.term_date
       AND h.prior_qc_work_years < 0
      THEN h.snapshot_date END) AS negative_prior_snapshot_count,
    COUNT(DISTINCT CASE
      WHEN h.worker_type = 'Employee'
       AND h.employee_type = 'Regular'
       AND h.active_status = 1
       AND h.snapshot_date < e.term_date
       AND h.prior_qc_work_years IS NULL
      THEN h.snapshot_date END) AS null_prior_snapshot_count
  FROM voluntary_events AS e
  LEFT JOIN all_source_rows AS h
    ON h.employee_id = e.employee_id
  GROUP BY 1, 2, 3
),
unresolved_reasons AS (
  SELECT
    fiscal_year,
    CASE
      WHEN active_prior_snapshot_count = 0 THEN 'Sin snapshot activo previo'
      WHEN valid_prior_snapshot_count = 0 AND negative_prior_snapshot_count > 0 THEN 'Sólo snapshots previos con valor negativo'
      WHEN valid_prior_snapshot_count = 0 AND null_prior_snapshot_count > 0 THEN 'Sólo snapshots previos con valor nulo'
      WHEN valid_prior_snapshot_count = 0 THEN 'Snapshot previo sin banda válida'
      ELSE 'Revisión adicional'
    END AS unresolved_reason,
    COUNT(*) AS voluntary_events
  FROM prior_snapshot_summary
  WHERE valid_prior_snapshot_count = 0
  GROUP BY 1, 2
),
domain_by_year AS (
  SELECT
    p.fiscal_year,
    COUNT(DISTINCT CASE WHEN a.worker_type = 'Employee' AND a.employee_type = 'Regular' AND a.active_status = 1 THEN a.employee_id || '|' || CAST(a.snapshot_date AS VARCHAR(32)) END) AS active_employee_snapshots,
    COUNT(DISTINCT CASE WHEN a.worker_type = 'Employee' AND a.employee_type = 'Regular' AND a.active_status = 1 AND a.prior_qc_work_years IS NULL THEN a.employee_id || '|' || CAST(a.snapshot_date AS VARCHAR(32)) END) AS null_active_snapshots,
    COUNT(DISTINCT CASE WHEN a.worker_type = 'Employee' AND a.employee_type = 'Regular' AND a.active_status = 1 AND a.prior_qc_work_years < 0 THEN a.employee_id || '|' || CAST(a.snapshot_date AS VARCHAR(32)) END) AS negative_active_snapshots
  FROM all_source_rows AS a
  INNER JOIN selected_periods AS p ON p.snapshot_date = a.snapshot_date
  GROUP BY 1
)
SELECT
  'unresolved_reason' AS row_type,
  fiscal_year,
  unresolved_reason AS metric,
  voluntary_events,
  CAST(NULL AS BIGINT) AS active_employee_snapshots,
  CAST(NULL AS BIGINT) AS null_active_snapshots,
  CAST(NULL AS BIGINT) AS negative_active_snapshots
FROM unresolved_reasons

UNION ALL

SELECT
  'domain_by_year' AS row_type,
  fiscal_year,
  'active_snapshots' AS metric,
  CAST(NULL AS BIGINT) AS voluntary_events,
  active_employee_snapshots,
  null_active_snapshots,
  negative_active_snapshots
FROM domain_by_year
ORDER BY row_type, fiscal_year, metric;
