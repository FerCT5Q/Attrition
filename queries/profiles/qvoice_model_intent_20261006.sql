-- Cobertura descriptiva del concepto en workforce previo; no acredita fecha predictiva.
SELECT snapshot_date, survey_year AS fiscal_year, eligible_count AS eligible_employees,
       primary_available_count AS observable_employees
FROM qvoice_variable_audit ORDER BY snapshot_date;
