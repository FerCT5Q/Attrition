-- Auditoria longitudinal agregada de mapping, dominio y cambios de componentes.
SELECT
    variable_name,
    snapshot_date,
    eligible_count,
    invalid_count,
    anomaly_count,
    unexplained_change_count,
    expected_component_count,
    available_component_count,
    complete_component_count,
    partial_component_count,
    missing_component_count,
    component_mapping_status,
    item_count,
    item_set_change_count,
    standard_deviation_zero_count
FROM qvoice_excel_consistency_aggregate
WHERE variable_name = :variable_name
ORDER BY snapshot_date;
