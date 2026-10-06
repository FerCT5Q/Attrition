-- Cobertura agregada del composite binario de todos los items disponibles.
SELECT
    snapshot_date,
    fiscal_year,
    eligible_employees,
    observable_employees,
    event_employees,
    item_count,
    min_items_required,
    invalid_count,
    notes
FROM qvoice_excel_coverage_aggregate
WHERE variable_name = 'Average of all Qvoice items'
ORDER BY snapshot_date;
