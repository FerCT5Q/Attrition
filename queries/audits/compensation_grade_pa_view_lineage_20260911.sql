-- Propósito: revisar el lineage declarado de vistas relacionadas con
-- aplicaciones y requisiciones. No consulta valores de candidatos.
-- Modo de entrega: presentation; definición de metadatos.

SELECT
  table_schema,
  table_name,
  view_definition
FROM information_schema.views
WHERE table_schema = 'hrda'
  AND table_name IN (
    'job_applications_vw',
    'applications_vw',
    'requisitions_vw'
  );
