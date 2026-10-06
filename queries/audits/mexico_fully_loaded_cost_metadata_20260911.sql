-- Propósito: revisar la estructura completa de los catálogos internos de
-- fully loaded cost y distinguir salario de costo total; sólo metadatos.
-- Modo de entrega: presentation.
SELECT
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name IN ('fully_loaded_cost', 'flc_20251006')
ORDER BY table_name, ordinal_position;
