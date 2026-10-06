-- Cobertura agregada de Engagement binario, calculado desde Q1, Q2 y Q3.
SELECT
    snapshot_date,
    fiscal_year,
    eligible_employees,
    observable_employees,
    event_employees,
    expected_component_count,
    available_component_count,
    complete_component_count,
    partial_component_count,
    missing_component_count,
    component_header_coverage_percent,
    component_response_coverage_percent,
    full_kpi_response_percent,
    component_mapping_status,
    notes
FROM qvoice_excel_coverage_aggregate
WHERE variable_name = 'Engagement items'
ORDER BY snapshot_date;
