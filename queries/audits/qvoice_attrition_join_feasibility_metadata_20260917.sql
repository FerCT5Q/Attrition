-- Preflight de metadatos para evaluar si las respuestas QVoice pueden
-- vincularse de forma temporal con attrition posterior.
--
-- Claim: la fuente estructurada de QVoice conserva una llave de empleado y
-- una fecha de wave, y la fuente HRDA conserva las columnas necesarias para
-- construir una cohorte activa antes de la wave y observar una salida
-- Voluntary posterior. Este preflight no calcula cohortes ni attrition.
--
-- Regla de aceptación: qvoice_survey_data debe exponer una llave de empleado
-- y fecha de wave; post_hire_monthly_worker_dtls debe exponer llave, fecha de
-- snapshot, filtros de población y columnas de terminación. La resolución de
-- duplicados y el join empleado-fecha se validan después, por variable/wave.
SELECT
  table_schema,
  table_name,
  column_name,
  data_type,
  ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND (
    (table_name = 'qvoice_survey_data' AND LOWER(column_name) IN (
      'employee_id', 'employeeid', 'emp_id', 'survey_launch_date', 'recorded_date', 'response_type', 'region'
    ))
    OR
    (table_name = 'post_hire_monthly_worker_dtls' AND LOWER(column_name) IN (
      'employee_id', 'fis_mo_end_dt', 'worker_type', 'employee_type', 'active_status', 'term_date', 'term_type'
    ))
  )
ORDER BY table_name, ordinal_position;
