-- Cobertura agregada del z-score binario por region-wave.
SELECT
    snapshot_date,
    fiscal_year,
    eligible_employees,
    observable_employees,
    event_employees,
    item_count,
    min_items_required,
    regions_checked,
    standard_deviation_zero_count,
    notes
FROM qvoice_excel_coverage_aggregate
WHERE variable_name = 'Standardized / normalized within region'
ORDER BY snapshot_date;
