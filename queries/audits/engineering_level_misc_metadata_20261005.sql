-- Modo: presentation. Metadata de la aclaracion de Misc en la v9.
-- Regla: deben existir los nueve campos antes de consultar agregados.
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN (
    'employee_id', 'fis_mo_end_dt', 'worker_type', 'employee_type',
    'active_status', 'is_rf360_yes_no', 'eng_or_noneng',
    'level_grouped', 'job_level_primary_position'
  )
ORDER BY column_name;
