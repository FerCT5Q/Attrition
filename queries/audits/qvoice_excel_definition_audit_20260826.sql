-- Auditoria agregada del calculo KPI, dominio y completitud por wave.
-- Un KPI puede usar componentes disponibles, pero las respuestas parciales
-- deben quedar separadas de las respuestas con todos los componentes.
SELECT
    variable_name,
    snapshot_date,
    eligible_count,
    populated_count,
    distinct_count,
    invalid_count,
    expected_component_count,
    available_component_count,
    complete_component_count,
    partial_component_count,
    missing_component_count,
    component_header_coverage_percent,
    component_response_coverage_percent,
    full_kpi_response_percent,
    component_mapping_status,
    item_count,
    min_items_required
FROM qvoice_excel_definition_aggregate
WHERE variable_name = :variable_name
ORDER BY snapshot_date;
