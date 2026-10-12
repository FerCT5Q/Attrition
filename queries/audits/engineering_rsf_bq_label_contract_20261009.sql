/* Modo presentation. Recalculo agregado del limite de registro de etiquetas.
   Engineering; Employee; Regular; activo; sin RF360. Sin identidad en salida. */
WITH population AS (
  SELECT employee_id, CAST(fis_mo_end_dt AS DATE) AS snapshot_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee' AND employee_type = 'Regular'
    AND active_status = 1 AND is_rf360_yes_no = 0
    AND TRIM(eng_or_noneng) = 'Engineering' AND employee_id IS NOT NULL
    AND CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2025-08-24' AND DATE '2026-02-22'
  GROUP BY 1, 2
), events AS (
  SELECT employee_id, CAST(term_date AS DATE) AS term_date,
         MIN(CAST(fis_mo_end_dt AS DATE)) AS first_recorded_snapshot
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee' AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(term_type::VARCHAR), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL AND CAST(term_date AS DATE) <= DATE '2026-09-07'
  GROUP BY 1, 2
), labels AS (
  SELECT p.employee_id, p.snapshot_date,
         MAX(CASE WHEN e.term_date IS NOT NULL THEN 1 ELSE 0 END) AS common_label,
         MAX(CASE WHEN e.first_recorded_snapshot <= DATE '2026-09-07' THEN 1 ELSE 0 END) AS legacy_label
  FROM population p
  LEFT JOIN events e ON e.employee_id = p.employee_id
    AND e.term_date > p.snapshot_date
    AND e.term_date <= DATEADD(month, 6, p.snapshot_date)
  GROUP BY 1, 2
)
SELECT COUNT(*) AS comparable_rows,
       SUM(CASE WHEN common_label = legacy_label THEN 1 ELSE 0 END) AS matched_rows,
       SUM(CASE WHEN common_label = 1 AND legacy_label = 0 THEN 1 ELSE 0 END) AS common_positive_legacy_negative,
       SUM(CASE WHEN common_label = 0 AND legacy_label = 1 THEN 1 ELSE 0 END) AS common_negative_legacy_positive
FROM labels
