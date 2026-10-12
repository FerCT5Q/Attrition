/* Metadata focalizada: ciclo/fechas de talento y timestamps de aplicaciones. */
SELECT table_schema,table_name,column_name,data_type
FROM information_schema.columns
WHERE table_schema='hrda' AND
 (table_name IN ('master_talent_index','job_applications_vw')
  OR (table_name='post_hire_monthly_worker_dtls' AND column_name='max_hire_rehire_date'))
ORDER BY table_name,column_name;
