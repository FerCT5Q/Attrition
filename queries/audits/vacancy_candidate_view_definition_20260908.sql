/* Definición metadata de la vista current de requisiciones. */
SELECT
    table_schema,
    table_name,
    view_definition
FROM information_schema.views
WHERE table_schema = 'hrda'
  AND table_name IN ('requisitions_vw', 'pre_hire_flat_and_wide_summary_mvw');
