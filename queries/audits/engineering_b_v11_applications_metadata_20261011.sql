-- Metadata de las dos fuentes, sin filas ni llaves de personas.
SELECT table_name,column_name,data_type
FROM information_schema.columns
WHERE table_schema='hrda' AND table_name IN ('applications','job_applications_vw')
  AND (column_name LIKE '%date%' OR column_name LIKE '%time%' OR column_name LIKE '%snapshot%'
       OR column_name LIKE '%employee%' OR column_name LIKE '%candidate%' OR column_name LIKE '%req%'
       OR column_name LIKE '%applied%' OR column_name LIKE '%internal%' OR column_name LIKE '%type%')
ORDER BY table_name,column_name
