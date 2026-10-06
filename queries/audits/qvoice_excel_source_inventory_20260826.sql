-- Auditoria agregada del diccionario KPI y disponibilidad de componentes.
-- El extractor local congela el resultado en aggregate-results JSON; este SQL
-- documenta el contrato y no devuelve columnas de empleados.
SELECT
    variable_name,
    kpi_name,
    expected_component_count,
    available_component_count,
    workbooks_checked,
    usable_form_workbooks,
    observations_checked,
    missing_items
FROM qvoice_excel_source_inventory_aggregate
ORDER BY variable_name;
