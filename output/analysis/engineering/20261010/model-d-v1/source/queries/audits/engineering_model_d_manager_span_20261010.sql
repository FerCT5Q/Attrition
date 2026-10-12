/* Modelo D - auditoría agregada del span reconstruido del manager actual.
   La comparación con reg_non_intern_dir_reports es diagnóstica porque el campo
   almacenado puede representar un contrato distinto. */
WITH params AS (
  SELECT DATE '2025-01-01' AS period_start, DATE '2026-09-07' AS period_end
),
population AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date,employee_id,
         MAX(manager_employee_id) AS manager_id,
         MAX(reg_non_intern_dir_reports) AS stored_direct_reports
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN (SELECT period_start FROM params) AND (SELECT period_end FROM params)
    AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
    AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
  GROUP BY 1,2
),
workforce AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date,employee_id,manager_employee_id AS manager_id
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN (SELECT period_start FROM params) AND (SELECT period_end FROM params)
    AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
    AND is_rf360_yes_no=0 AND employee_id IS NOT NULL AND manager_employee_id IS NOT NULL
  GROUP BY 1,2,3
),
span AS (
  SELECT p.snapshot_date,p.employee_id,p.manager_id,p.stored_direct_reports,
         COUNT(DISTINCT w.employee_id) AS reconstructed_span
  FROM population p LEFT JOIN workforce w ON w.snapshot_date=p.snapshot_date AND w.manager_id=p.manager_id
  GROUP BY 1,2,3,4
)
SELECT COUNT(*) AS person_snapshots,COUNT(DISTINCT snapshot_date) AS snapshots,
       SUM(CASE WHEN manager_id IS NOT NULL THEN 1 ELSE 0 END) AS manager_known_rows,
       SUM(CASE WHEN manager_id IS NOT NULL AND reconstructed_span>0 THEN 1 ELSE 0 END) AS reconstructed_rows,
       SUM(CASE WHEN reconstructed_span<0 THEN 1 ELSE 0 END) AS negative_span_violations,
       SUM(CASE WHEN stored_direct_reports IS NOT NULL THEN 1 ELSE 0 END) AS stored_field_rows,
       SUM(CASE WHEN stored_direct_reports IS NOT NULL AND ABS(reconstructed_span-stored_direct_reports)<0.000001 THEN 1 ELSE 0 END) AS exact_matches,
       ROUND(AVG(CASE WHEN stored_direct_reports IS NOT NULL THEN ABS(reconstructed_span-stored_direct_reports) END),4) AS mean_absolute_difference,
       SUM(CASE WHEN reconstructed_span BETWEEN 1 AND 4 THEN 1 ELSE 0 END) AS band_1_4,
       SUM(CASE WHEN reconstructed_span BETWEEN 5 AND 9 THEN 1 ELSE 0 END) AS band_5_9,
       SUM(CASE WHEN reconstructed_span BETWEEN 10 AND 14 THEN 1 ELSE 0 END) AS band_10_14,
       SUM(CASE WHEN reconstructed_span BETWEEN 15 AND 19 THEN 1 ELSE 0 END) AS band_15_19,
       SUM(CASE WHEN reconstructed_span BETWEEN 20 AND 29 THEN 1 ELSE 0 END) AS band_20_29,
       SUM(CASE WHEN reconstructed_span>=30 THEN 1 ELSE 0 END) AS band_30_plus,
       MAX(reconstructed_span) AS maximum_reconstructed_span
FROM span;
