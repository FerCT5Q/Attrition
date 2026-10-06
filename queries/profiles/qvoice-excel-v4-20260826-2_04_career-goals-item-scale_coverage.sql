-- Cobertura agregada del item ordinal 1-5 de career goals.
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
WHERE variable_name = 'Career goals item-scale'
ORDER BY snapshot_date;
