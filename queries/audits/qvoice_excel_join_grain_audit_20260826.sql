-- Auditoria agregada del grain interno empleado-wave en Excel.
-- La reconciliacion con workforce mensual queda fuera de esta fuente local.
SELECT
    variable_name,
    snapshot_date,
    eligible_count,
    matched_count,
    unmatched_count,
    duplicate_count,
    expected_component_count,
    available_component_count,
    complete_component_count,
    partial_component_count,
    missing_component_count
FROM qvoice_excel_join_aggregate
WHERE variable_name = :variable_name
ORDER BY snapshot_date;
