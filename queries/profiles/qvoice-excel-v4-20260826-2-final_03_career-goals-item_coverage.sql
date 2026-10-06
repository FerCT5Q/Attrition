-- Cobertura agregada del item binario de career goals.
SELECT
    snapshot_date,
    fiscal_year,
    eligible_employees,
    observable_employees,
    event_employees,
    item_count,
    invalid_count,
    notes
FROM qvoice_excel_coverage_aggregate
WHERE variable_name = 'Career goals item'
ORDER BY snapshot_date;
