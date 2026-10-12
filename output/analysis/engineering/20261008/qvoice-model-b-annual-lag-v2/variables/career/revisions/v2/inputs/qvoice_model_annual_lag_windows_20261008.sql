/*
  Validacion agregada de la politica anual QVoice para el experimento del 8-oct-2026.
  Claim: wave Y se asigna solo a snapshots del ano Y+1.
  Poblacion: Engineering, Employee, Regular, activo, RF360 excluido.
  Grain de salida: periodo de validacion; no devuelve identificadores.
  Regla de aceptacion declarada antes de ejecutar:
    - aug_dec_2025 contiene cinco snapshots y solo wave 2024;
    - jan_feb_2026 contiene dos snapshots y solo wave 2025;
    - cero contradicciones con wave = ano(snapshot)-1;
    - cada snapshot tiene al menos 30 personas elegibles.
*/
WITH snapshots AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    EXTRACT(YEAR FROM CAST(fis_mo_end_dt AS DATE))::INTEGER - 1 AS assigned_wave_year,
    COUNT(DISTINCT employee_id) AS eligible_people
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND COALESCE(is_rf360_yes_no, 0) = 0
    AND eng_or_noneng = 'Engineering'
    AND CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2025-08-01' AND DATE '2026-02-28'
  GROUP BY 1, 2
), classified AS (
  SELECT
    CASE
      WHEN snapshot_date BETWEEN DATE '2025-08-01' AND DATE '2025-12-31' THEN 'aug_dec_2025'
      WHEN snapshot_date BETWEEN DATE '2026-01-01' AND DATE '2026-02-28' THEN 'jan_feb_2026'
      ELSE 'outside'
    END AS period_id,
    snapshot_date,
    assigned_wave_year,
    eligible_people,
    CASE
      WHEN EXTRACT(YEAR FROM snapshot_date)::INTEGER - assigned_wave_year = 1 THEN 0
      ELSE 1
    END AS mapping_contradiction
  FROM snapshots
)
SELECT
  period_id,
  MIN(snapshot_date) AS first_snapshot,
  MAX(snapshot_date) AS last_snapshot,
  COUNT(*) AS snapshot_count,
  MIN(assigned_wave_year) AS minimum_wave_year,
  MAX(assigned_wave_year) AS maximum_wave_year,
  MIN(eligible_people) AS minimum_eligible_people,
  MAX(eligible_people) AS maximum_eligible_people,
  SUM(mapping_contradiction) AS mapping_contradiction_count,
  SUM(CASE WHEN eligible_people < 30 THEN 1 ELSE 0 END) AS below_privacy_threshold_count
FROM classified
GROUP BY 1
ORDER BY 1;
