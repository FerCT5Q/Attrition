SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND LOWER(column_name) = 'business_process_reason'
ORDER BY table_name, ordinal_position
