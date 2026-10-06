-- Propósito: buscar lineage técnico alternativo cuando
-- information_schema.views.view_definition es NULL.
-- Modo de entrega: presentation; sólo definición de vistas.
SELECT
    schemaname,
    viewname,
    definition
FROM pg_catalog.pg_views
WHERE schemaname = 'hrda'
  AND viewname IN ('job_applications_vw', 'applications_vw', 'requisitions_vw');
