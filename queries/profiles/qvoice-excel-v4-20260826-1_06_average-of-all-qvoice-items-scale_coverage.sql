-- Cobertura agregada del composite ordinal 1-5 de todos los items disponibles.
SELECT snapshot_date, fiscal_year, eligible_employees, observable_employees,
       event_employees, notes
FROM qvoice_excel_coverage_aggregate
WHERE variable_name = 'Average of all Qvoice items-scale'
ORDER BY snapshot_date;
