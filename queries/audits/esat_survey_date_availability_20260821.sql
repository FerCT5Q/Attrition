SELECT
  COUNT(*) AS row_count,
  MIN(last_modified_date) AS min_last_modified_date,
  MAX(last_modified_date) AS max_last_modified_date,
  MIN(airflow_execution_date) AS min_airflow_execution_date,
  MAX(airflow_execution_date) AS max_airflow_execution_date
FROM hrda.esat
