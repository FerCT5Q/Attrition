/*
  Valida el puente entre application_date y el calendario fiscal para la
  distribución descriptiva de solicitudes por solicitante-año fiscal.

  Claim: cada evento candidato de hrda.job_applications_vw se asigna a un
  único año fiscal. Tipo semántico: input de feature derivada. Modo de reporte:
  presentation; sólo se devuelven métricas agregadas.

  Regla de aceptación: unmapped_event_keys = 0 y multi_mapped_event_keys = 0.
  Esta validación prueba la asignación temporal, no la equivalencia de negocio
  de la vista ni la definición de una feature mensual.
*/
WITH fiscal_calendar AS (
  SELECT
    CAST(fiscal_year AS VARCHAR(32)) AS fiscal_year,
    MIN(CAST(fis_mo_beg_dt AS DATE)) AS fiscal_year_start,
    MAX(CAST(fis_mo_end_dt AS DATE)) AS fiscal_year_end
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fiscal_year IS NOT NULL
    AND fis_mo_beg_dt IS NOT NULL
    AND fis_mo_end_dt IS NOT NULL
  GROUP BY 1
),
source_event_keys AS (
  SELECT
    employee_id,
    req_id,
    CAST(application_date AS DATE) AS application_date
  FROM hrda.job_applications_vw
  WHERE cand_applied = 1
    AND employee_id IS NOT NULL
    AND req_id IS NOT NULL
    AND application_date IS NOT NULL
  GROUP BY 1, 2, 3
),
event_fiscal_mapping AS (
  SELECT
    e.employee_id,
    e.req_id,
    e.application_date,
    COUNT(c.fiscal_year) AS fiscal_year_matches
  FROM source_event_keys AS e
  LEFT JOIN fiscal_calendar AS c
    ON e.application_date BETWEEN c.fiscal_year_start AND c.fiscal_year_end
  GROUP BY 1, 2, 3
),
calendar_summary AS (
  SELECT
    COUNT(*) AS fiscal_years_in_calendar,
    MIN(fiscal_year_start) AS calendar_first_date,
    MAX(fiscal_year_end) AS calendar_last_date
  FROM fiscal_calendar
)
SELECT
  COUNT(*) AS source_event_keys,
  MIN(application_date) AS source_first_application_date,
  MAX(application_date) AS source_last_application_date,
  SUM(CASE WHEN fiscal_year_matches = 1 THEN 1 ELSE 0 END) AS exactly_mapped_event_keys,
  SUM(CASE WHEN fiscal_year_matches = 0 THEN 1 ELSE 0 END) AS unmapped_event_keys,
  SUM(CASE WHEN fiscal_year_matches > 1 THEN 1 ELSE 0 END) AS multi_mapped_event_keys,
  c.fiscal_years_in_calendar,
  c.calendar_first_date,
  c.calendar_last_date
FROM event_fiscal_mapping
CROSS JOIN calendar_summary AS c
GROUP BY 7, 8, 9;
