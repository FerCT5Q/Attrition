-- Metadata del concepto postal; no valores de domicilio ni registros personales.
SELECT column_name,data_type
FROM information_schema.columns
WHERE table_schema='hrda' AND table_name='post_hire_monthly_worker_dtls'
  AND (column_name LIKE '%home%' OR column_name LIKE '%address%'
       OR column_name LIKE '%postal%' OR column_name LIKE '%country%' OR column_name LIKE '%zip%')
ORDER BY column_name
